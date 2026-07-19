from typing import List
from sqlalchemy.orm import Session
from app.models.measurement import Measurement


class MeasurementRepository:
    """Repository for Measurement database operations.

    # ponytail: static methods to avoid instantiation/dependency boilerplates
    """

    @staticmethod
    def get_by_case(db: Session, case_id: int) -> List[Measurement]:
        """Retrieve all measurements associated with a specific case."""
        return db.query(Measurement).filter(Measurement.case_id == case_id).all()

    @staticmethod
    def get_by_case_code(db: Session, case_code: str) -> List[Measurement]:
        """Retrieve all measurements associated with a specific case code."""
        from app.shared.validation import decode_case_code

        case_id = decode_case_code(case_code)
        return db.query(Measurement).filter(Measurement.case_id == case_id).all()

    @staticmethod
    def batch_create(db: Session, measurements: List[Measurement]) -> List[Measurement]:
        """Batch insert measurement ORM objects."""
        if not measurements:
            return []
        db.add_all(measurements)
        # ponytail: shift transaction commits (db.commit()) to the service layer to support multiple repositories in one ACID transaction boundary
        db.commit()
        for m in measurements:
            db.refresh(m)
        return measurements
