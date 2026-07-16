import json
import time
from pathlib import Path
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.localization_result import LocalizationResult as LocalizationResultORM
from app.repositories.localization_repository import LocalizationRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.case_repository import CaseRepository
from app.shared.validation import ValidationError, decode_case_code

from scientific.models.measurement import Measurement as ScientificMeasurement
from scientific.models.tower import Tower as ScientificTower
from scientific.models.result import LocalizationResult as ScientificResult
from scientific.models.scenario_config import (
    ScenarioConfig,
    PropagationDefaults,
    SimulationParameters,
)
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

        # 2. Load scenario config from JSON dataset
        dataset_path = (
            Path(__file__).resolve().parents[3]
            / "datasets"
            / "sample"
            / "scenario_example.json"
        )
        if not dataset_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Scenario dataset not found at {dataset_path}",
            )

        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            configs_list = data.get("scenario_configs", [])
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read scenario dataset: {str(e)}",
            )

        # Find matching scenario config
        target_config_dict = None
        for cfg_dict in configs_list:
            sc_id_str = cfg_dict.get("scenario_id", "")
            try:
                cfg_id_int = int(sc_id_str.split("-")[-1])
            except (ValueError, IndexError):
                continue
            if cfg_id_int == case.scenario_id:
                target_config_dict = cfg_dict
                break

        if not target_config_dict:
            raise ValidationError(
                "scenario_id",
                f"Scenario config mapping to scenario ID {case.scenario_id} not found in dataset.",
                status_code=400,
            )

        # Parse into ScenarioConfig
        try:
            config = ScenarioConfig(**target_config_dict)
        except Exception as e:
            raise ValidationError(
                "scenario_config",
                f"Failed to parse scenario config: {str(e)}",
                status_code=400,
            )

        # 3. Retrieve stored measurements for the case
        db_measurements = MeasurementRepository.get_by_case(db, case_id)
        if not db_measurements:
            raise ValidationError(
                "measurements",
                "No measurements found for this case. Generate measurements first.",
                status_code=400,
            )

        # 4. Convert DB measurements → scientific Measurement models
        scientific_measurements: List[ScientificMeasurement] = []
        for m in db_measurements:
            # Map measurement back to tower_id using measurement_code pattern
            # Measurement codes follow: MEAS-SCNXXX-TYYY-ZZZZ
            parts = m.measurement_code.split("-")
            tower_id = None
            for i, part in enumerate(parts):
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
                    rssi_dbm=m.rssi_dbm,
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
        scientific_towers: List[ScientificTower] = []
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

        # 6. Call the multilateration solver
        result: ScientificResult = solve_multilateration(
            scenario_id=config.scenario_id,
            towers=scientific_towers,
            measurements=scientific_measurements,
            propagation=config.propagation,
            simulation=config.simulation,
            expected_device_lat=config.expected_device_lat,
            expected_device_lon=config.expected_device_lon,
        )

        # 7. Persist result
        db_result = LocalizationResultORM(
            case_id=case_id,
            scenario_id=case.scenario_id,
            algorithm=result.algorithm,
            estimated_latitude=result.estimated_latitude,
            estimated_longitude=result.estimated_longitude,
            error_m=result.error_m,
            computation_time_ms=result.computation_time_ms,
            signals_used=result.signals_used,
        )
        LocalizationRepository.create(db, db_result)

        return result
