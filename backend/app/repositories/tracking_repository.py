from app.models.tracking_result import TrackingResult
from sqlalchemy.orm import Session


class TrackingRepository:
    """Repository for TrackingResult database operations.

    # ponytail: static methods to avoid instantiation/dependency boilerplate
    """

    @staticmethod
    def create(db: Session, result: TrackingResult) -> TrackingResult:
        """Persist a single tracking result."""
        db.add(result)
        db.commit()
        db.refresh(result)
        return result

    @staticmethod
    def bulk_create(db: Session, results: list[TrackingResult]) -> list[TrackingResult]:
        """Persist a list of tracking results in one commit."""
        db.add_all(results)
        db.commit()
        for r in results:
            db.refresh(r)
        return results

    @staticmethod
    def get_by_case(db: Session, case_id: int) -> list[TrackingResult]:
        """Retrieve all tracking results for a case, ordered by step_number."""
        return (
            db.query(TrackingResult)
            .filter(TrackingResult.case_id == case_id)
            .order_by(TrackingResult.step_number.asc())
            .all()
        )

    @staticmethod
    def get_latest_by_case(db: Session, case_id: int) -> TrackingResult | None:
        """Retrieve the last step in the most recent tracking run for a case."""
        return (
            db.query(TrackingResult)
            .filter(TrackingResult.case_id == case_id)
            .order_by(TrackingResult.created_at.desc())
            .first()
        )

    @staticmethod
    def delete_by_case(db: Session, case_id: int) -> int:
        """Delete all tracking results for a case. Returns count deleted."""
        count = (
            db.query(TrackingResult)
            .filter(TrackingResult.case_id == case_id)
            .delete(synchronize_session="fetch")
        )
        db.commit()
        return count
