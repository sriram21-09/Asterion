"""
Confidence Service
===================

Orchestrates the confidence analysis pipeline:
  DB localization + measurements → scientific confidence engine → persisted result.
"""

import json
import time
from pathlib import Path

from app.models.confidence_result import ConfidenceResult as ConfidenceResultORM
from app.repositories.case_repository import CaseRepository
from app.repositories.confidence_repository import ConfidenceRepository
from app.repositories.localization_repository import LocalizationRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.shared.validation import ValidationError, decode_case_code
from fastapi import HTTPException
from sqlalchemy.orm import Session

from scientific.models.measurement import Measurement as ScientificMeasurement
from scientific.models.scenario_config import ScenarioConfig
from scientific.models.tower import Tower as ScientificTower
from scientific.pipeline.confidence import compute_confidence


class ConfidenceService:
    """Service that bridges DB data → scientific confidence engine → persisted results."""

    @staticmethod
    def run_confidence(
        db: Session,
        case_code: str,
    ) -> dict:
        """Run confidence analysis for a case.

        1. Decode case_code → load case + scenario
        2. Load scenario config from dataset JSON
        3. Retrieve stored measurements and latest localization result
        4. Convert DB models → scientific Tower/Measurement models
        5. Call compute_confidence() from the scientific pipeline
        6. Persist as ConfidenceResult ORM row
        7. Return structured response dict

        Returns:
            Dictionary with confidence_score, confidence_level, error ellipse
            parameters, gdop, method, and computation_time_ms.
        """
        overall_start = time.perf_counter()

        # 1. Decode case code and load case
        case_id = decode_case_code(case_code)
        case = CaseRepository.get(db, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if not case.scenario_id:
            raise ValidationError(
                "case",
                "Case must have an associated scenario to run confidence analysis.",
                status_code=400,
            )

        # 2. Load scenario config from dataset JSON
        config = ConfidenceService._load_scenario_config(case.scenario_id)

        # 3. Retrieve stored measurements
        db_measurements = MeasurementRepository.get_by_case(db, case_id)
        if not db_measurements:
            raise ValidationError(
                "measurements",
                "No measurements found for this case. Generate measurements first.",
                status_code=400,
            )

        # Get latest localization result (if available) for linking
        latest_loc = LocalizationRepository.get_latest_by_case(db, case_id)

        # Use the localization estimate if available; otherwise use ground truth
        if latest_loc:
            est_lat = latest_loc.estimated_latitude
            est_lon = latest_loc.estimated_longitude
        elif config.expected_device_lat and config.expected_device_lon:
            est_lat = config.expected_device_lat
            est_lon = config.expected_device_lon
        else:
            raise ValidationError(
                "localization",
                "No localization result or ground-truth coordinates available.",
                status_code=400,
            )

        # 4. Convert DB models → scientific models
        scientific_towers, scientific_measurements = (
            ConfidenceService._convert_to_scientific(config, db_measurements)
        )

        # 5. Call the confidence engine
        scenario_id_str = config.scenario_id
        confidence_result = compute_confidence(
            scenario_id=scenario_id_str,
            estimated_latitude=est_lat,
            estimated_longitude=est_lon,
            towers=scientific_towers,
            measurements=scientific_measurements,
        )

        # 6. Persist result
        db_result = ConfidenceResultORM(
            case_id=case_id,
            localization_result_id=latest_loc.id if latest_loc else None,
            confidence_score=confidence_result.confidence_score,
            confidence_level=confidence_result.confidence_level,
            error_ellipse_semi_major_m=confidence_result.error_ellipse_semi_major_m,
            error_ellipse_semi_minor_m=confidence_result.error_ellipse_semi_minor_m,
            error_ellipse_orientation_deg=confidence_result.error_ellipse_orientation_deg,
            gdop=confidence_result.gdop,
            method=confidence_result.method,
        )
        ConfidenceRepository.create(db, db_result)

        # 7. Build response
        overall_ms = (time.perf_counter() - overall_start) * 1000.0

        return {
            "case_code": case_code.upper(),
            "confidence_score": round(confidence_result.confidence_score, 4),
            "confidence_level": confidence_result.confidence_level,
            "error_ellipse_semi_major_m": (
                round(confidence_result.error_ellipse_semi_major_m, 2)
                if confidence_result.error_ellipse_semi_major_m is not None
                else None
            ),
            "error_ellipse_semi_minor_m": (
                round(confidence_result.error_ellipse_semi_minor_m, 2)
                if confidence_result.error_ellipse_semi_minor_m is not None
                else None
            ),
            "error_ellipse_orientation_deg": (
                round(confidence_result.error_ellipse_orientation_deg, 2)
                if confidence_result.error_ellipse_orientation_deg is not None
                else None
            ),
            "gdop": (
                round(confidence_result.gdop, 4)
                if confidence_result.gdop is not None
                else None
            ),
            "method": confidence_result.method,
            "computation_time_ms": round(overall_ms, 2),
        }

    @staticmethod
    def _load_scenario_config(scenario_id: int) -> ScenarioConfig:
        """Load and parse scenario config from the dataset JSON."""
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
                detail=f"Failed to read scenario dataset: {e!s}",
            )

        for cfg_dict in configs_list:
            sc_id_str = cfg_dict.get("scenario_id", "")
            try:
                cfg_id_int = int(sc_id_str.split("-")[-1])
            except (ValueError, IndexError):
                continue
            if cfg_id_int == scenario_id:
                try:
                    return ScenarioConfig(**cfg_dict)
                except Exception as e:
                    raise ValidationError(
                        "scenario_config",
                        f"Failed to parse scenario config: {e!s}",
                        status_code=400,
                    )

        raise ValidationError(
            "scenario_id",
            f"Scenario config mapping to scenario ID {scenario_id} not found in dataset.",
            status_code=400,
        )

    @staticmethod
    def _convert_to_scientific(config, db_measurements):
        """Convert DB ORM measurement records + scenario config → scientific models."""
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

        scientific_measurements: list[ScientificMeasurement] = []
        for m in db_measurements:
            # Map measurement back to tower_id using measurement_code pattern
            parts = m.measurement_code.split("-")
            tower_id = None
            for part in parts:
                if part.startswith("T") and part[1:].isdigit():
                    tower_id = part
                    break

            if tower_id is None:
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

        return scientific_towers, scientific_measurements
