import json
from pathlib import Path
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.measurement import Measurement as MeasurementORM
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.case_repository import CaseRepository
from app.shared.validation import (
    ValidationError,
    decode_case_code,
)
from scientific.models.scenario_config import ScenarioConfig, SimulationParameters
from scientific.simulation.measurement_generator import generate_scenario_measurements


class MeasurementService:
    """Service class for Measurement operations and simulation generation."""

    @staticmethod
    def generate_measurements(
        db: Session,
        case_code: str,
        params: SimulationParameters,
    ) -> List[MeasurementORM]:
        """Generate synthetic measurements for a case using Chaitanya's simulation engine."""
        # 1. Decode case code
        case_id = decode_case_code(case_code)

        # 2. Retrieve the case
        case = CaseRepository.get(db, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # 3. Check scenario association
        if not case.scenario_id:
            raise ValidationError(
                "case",
                "Case must have an associated scenario to generate measurements.",
                status_code=400,
            )

        # 4. Load the scenario configs from JSON dataset
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

        # 5. Search for the scenario config that matches our scenario_id
        target_config_dict = None
        for cfg_dict in configs_list:
            sc_id_str = cfg_dict.get("scenario_id", "")
            try:
                # e.g., SCN-CFG-001 -> 1
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

        # 6. Parse into ScenarioConfig and override simulation parameters
        try:
            config = ScenarioConfig(**target_config_dict)
            config.simulation = params
        except Exception as e:
            raise ValidationError(
                "simulation_parameters",
                f"Failed to validate scenario config or simulation parameters: {str(e)}",
                status_code=400,
            )

        # 7. Call Chaitanya's engine to generate measurements
        try:
            scientific_measurements = generate_scenario_measurements(config)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate measurements: {str(e)}",
            )

        # 8. Delete existing measurements for this case (to allow regeneration/overwriting)
        existing_measurements = MeasurementRepository.get_by_case(db, case_id)
        for m in existing_measurements:
            db.delete(m)
        db.commit()

        # 9. Translate to ORM models and save
        db_measurements = []
        for s_meas in scientific_measurements:
            db_m = MeasurementORM(
                case_id=case.id,
                scenario_id=case.scenario_id,
                measurement_code=s_meas.measurement_id,
                timestamp=s_meas.timestamp,
                rssi_dbm=s_meas.rssi_dbm,
                latitude=s_meas.latitude,
                longitude=s_meas.longitude,
                timing_advance=s_meas.timing_advance,
                uncertainty_m=s_meas.uncertainty_m,
            )
            db_measurements.append(db_m)

        # Save to DB
        saved_measurements = MeasurementRepository.batch_create(db, db_measurements)
        return saved_measurements
