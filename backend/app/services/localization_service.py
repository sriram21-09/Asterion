from app.models.localization_result import LocalizationResult as LocalizationResultORM
from app.repositories.case_repository import CaseRepository
from app.repositories.localization_repository import LocalizationRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.shared.validation import ValidationError, decode_case_code
from fastapi import HTTPException
from sqlalchemy.orm import Session

from scientific.models.measurement import Measurement as ScientificMeasurement
from scientific.models.result import LocalizationResult as ScientificResult
from scientific.models.tower import Tower as ScientificTower
from scientific.pipeline.multilateration import solve_multilateration


class LocalizationService:
    """Service that bridges DB data → scientific NLLS solver → persists results."""

    @staticmethod
    def run_localization(
        db: Session,
        case_code: str,
    ) -> ScientificResult:
        """Run multilateration localization against stored measurements for a case.

        1. Decode case_code → load case + scenario
        2. Load scenario config from JSON dataset
        3. Retrieve stored measurements for the case
        4. Convert DB models → scientific domain models
        5. Call solve_multilateration()
        6. Persist result as LocalizationResult ORM row
        7. Return the scientific LocalizationResult
        """
        # 1. Decode case code and load case
        case_id = decode_case_code(case_code)
        case = CaseRepository.get(db, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if not case.scenario_id:
            raise ValidationError(
                "case",
                "Case must have an associated scenario to run localization.",
                status_code=400,
            )

        # 2. Load scenario config (from dataset JSON or dynamically generated from DB data)
        from app.services.scenario_config_helper import load_scenario_config

        config = load_scenario_config(db, case.scenario_id, case_id)

        # 3. Retrieve stored measurements for the case
        db_measurements = MeasurementRepository.get_by_case(db, case_id)
        if not db_measurements:
            raise ValidationError(
                "measurements",
                "No measurements found for this case. Generate measurements first.",
                status_code=400,
            )

        # Scientific Integrity Check: If measurement augmentation is disabled for this case,
        # ensure no augmented/simulated measurements are forced and dataset contains valid signal values.
        aug_enabled = getattr(case, "enable_augmentation", True)
        if not aug_enabled:
            simulated_or_missing = [
                m for m in db_measurements if m.is_simulated or m.rssi_dbm is None
            ]
            if simulated_or_missing:
                raise ValidationError(
                    "measurements",
                    "Insufficient measurements: Measurement augmentation is disabled for this investigation "
                    "and the imported dataset lacks required signal parameters (RSSI/TA) for scientific localization. "
                    "Enable Measurement Augmentation in investigation options or Settings to proceed.",
                    status_code=400,
                )

        # 4. Convert DB measurements → scientific Measurement models
        scientific_measurements: list[ScientificMeasurement] = []
        for m in db_measurements:
            # Use stored tower_id first; fall back to parsing measurement_code
            tower_id = getattr(m, "tower_id", None)
            if not tower_id:
                parts = m.measurement_code.split("-")
                for part in parts:
                    if part.startswith("T") and part[1:].isdigit():
                        tower_id = part
                        break

            if tower_id is None:
                # Fallback: try to assign to towers round-robin based on index
                tower_placements = config.tower_placements
                if tower_placements:
                    idx = db_measurements.index(m) % len(tower_placements)
                    tower_id = tower_placements[idx].tower_id
                else:
                    continue

            scientific_measurements.append(
                ScientificMeasurement(
                    measurement_id=m.measurement_code,
                    tower_id=tower_id,
                    timestamp=m.timestamp,
                    rssi_dbm=m.rssi_dbm if m.rssi_dbm is not None else -80.0,
                    latitude=m.latitude,
                    longitude=m.longitude,
                    timing_advance=m.timing_advance,
                    uncertainty_m=m.uncertainty_m,
                )
            )

        if len(scientific_measurements) < 1:
            raise ValidationError(
                "measurements",
                "No valid measurements could be mapped to towers.",
                status_code=400,
            )

        # 5. Convert tower placements → scientific Tower models
        scientific_towers: list[ScientificTower] = []
        for tp in config.tower_placements:
            scientific_towers.append(
                ScientificTower(
                    tower_id=tp.tower_id,
                    latitude=tp.latitude,
                    longitude=tp.longitude,
                    antenna_height_m=tp.antenna_height_m,
                    frequency_mhz=tp.frequency_mhz,
                    transmit_power_dbm=tp.transmit_power_dbm,
                    coverage_radius_m=tp.coverage_radius_m,
                    sector=tp.sector,
                )
            )

        # Group measurements by timestamp
        from collections import defaultdict

        measurements_by_time = defaultdict(list)
        for m in scientific_measurements:
            measurements_by_time[m.timestamp].append(m)

        # Clear previous localization results for this case to avoid staled state
        db.query(LocalizationResultORM).filter(
            LocalizationResultORM.case_id == case_id
        ).delete()
        db.commit()

        # Run multilateration solver for each timestamp group
        results: list[ScientificResult] = []
        db_results: list[LocalizationResultORM] = []
        sorted_times = sorted(measurements_by_time.keys())
        for t in sorted_times:
            group = measurements_by_time[t]
            result: ScientificResult = solve_multilateration(
                scenario_id=config.scenario_id,
                towers=scientific_towers,
                measurements=group,
                propagation=config.propagation,
                simulation=config.simulation,
                expected_device_lat=config.expected_device_lat,
                expected_device_lon=config.expected_device_lon,
            )
            # Sync timestamp to the group timestamp
            result.timestamp = t
            results.append(result)
            db_result = LocalizationResultORM(
                case_id=case_id,
                scenario_id=case.scenario_id,
                algorithm=result.algorithm,
                estimated_latitude=result.estimated_latitude,
                estimated_longitude=result.estimated_longitude,
                error_m=result.error_m,
                computation_time_ms=result.computation_time_ms,
                signals_used=result.signals_used,
                created_at=t,
            )
            db_results.append(db_result)

        if db_results:
            LocalizationRepository.bulk_create(db, db_results)

        return results[-1]
