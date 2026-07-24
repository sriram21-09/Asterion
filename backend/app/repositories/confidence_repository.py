from app.models.confidence_result import ConfidenceResult
from sqlalchemy.orm import Session


class ConfidenceRepository:
    """Repository for ConfidenceResult database operations.

    # ponytail: static methods to avoid instantiation/dependency boilerplate
    """

    @staticmethod
    def create(db: Session, result: ConfidenceResult) -> ConfidenceResult:
        """Persist a single confidence result."""
        db.add(result)
        db.commit()
        db.refresh(result)
        return result

    @staticmethod
    def bulk_create(
        db: Session, results: list[ConfidenceResult]
    ) -> list[ConfidenceResult]:
        """Persist a list of confidence results in one commit."""
        db.add_all(results)
        db.commit()
        for r in results:
            db.refresh(r)
        return results

    @staticmethod
    def get_by_case(db: Session, case_id: int) -> list[ConfidenceResult]:
        """Retrieve all confidence results for a case, ordered by creation time."""
        return (
            db.query(ConfidenceResult)
            .filter(ConfidenceResult.case_id == case_id)
            .order_by(ConfidenceResult.created_at.desc())
            .all()
        )

    @staticmethod
    def get_latest_by_case(db: Session, case_id: int) -> ConfidenceResult | None:
        """Retrieve the most recent confidence result for a case."""
        return (
            db.query(ConfidenceResult)
            .filter(ConfidenceResult.case_id == case_id)
            .order_by(ConfidenceResult.created_at.desc())
            .first()
        )

    @staticmethod
    def delete_by_case(db: Session, case_id: int) -> int:
        """Delete all confidence results for a case. Returns count deleted."""
        count = (
            db.query(ConfidenceResult)
            .filter(ConfidenceResult.case_id == case_id)
            .delete(synchronize_session="fetch")
        )
        db.commit()
        return count
