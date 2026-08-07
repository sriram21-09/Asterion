from app.models.measurement import Measurement as MeasurementORM
from app.repositories.case_repository import CaseRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.shared.validation import (
    ValidationError,
    decode_case_code,
)
from fastapi import HTTPException
from sqlalchemy.orm import Session

from scientific.models.scenario_config import SimulationParameters
from scientific.simulation.measurement_generator import generate_scenario_measurements


class MeasurementService:
    """Service class for Measurement operations and simulation generation."""

    @staticmethod
    def generate_measurements(
        db: Session,
        case_code: str,
        params: SimulationParameters,
    ) -> list[MeasurementORM]:
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

        # 4. Load scenario config and override simulation parameters
        from app.services.scenario_config_helper import load_scenario_config

        config = load_scenario_config(db, case.scenario_id, case_id)
        config.simulation = params

        # 7. Call Chaitanya's engine to generate measurements
        try:
            scientific_measurements = generate_scenario_measurements(config)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate measurements: {e!s}",
            )

        # 8. Delete existing SIMULATED measurements for this case (preserving real CDR imported data)
        existing_simulated = (
            db.query(MeasurementORM)
            .filter(
                MeasurementORM.case_id == case_id,
                MeasurementORM.is_simulated,
            )
            .all()
        )
        for m in existing_simulated:
            db.delete(m)
        db.commit()

        # 9. Translate to ORM models and save
        db_measurements = []
        for s_meas in scientific_measurements:
            db_m = MeasurementORM(
                case_id=case.id,
                scenario_id=case.scenario_id,
                measurement_code=f"{case_code}-{s_meas.measurement_id}",
                timestamp=s_meas.timestamp,
                rssi_dbm=s_meas.rssi_dbm,
                tower_id=s_meas.tower_id,
                latitude=s_meas.latitude,
                longitude=s_meas.longitude,
                timing_advance=s_meas.timing_advance,
                uncertainty_m=s_meas.uncertainty_m,
                is_simulated=True,
                source="SIMULATED",
            )
            db_measurements.append(db_m)

        # Save to DB
        saved_measurements = MeasurementRepository.batch_create(db, db_measurements)
        return saved_measurements
