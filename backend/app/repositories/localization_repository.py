from app.models.localization_result import LocalizationResult
from sqlalchemy.orm import Session


class LocalizationRepository:
    """Repository for LocalizationResult database operations.

    # ponytail: static methods to avoid instantiation/dependency boilerplates
    """

    @staticmethod
    def create(db: Session, result: LocalizationResult) -> LocalizationResult:
        """Persist a single localization result."""
        db.add(result)
        db.commit()
        db.refresh(result)
        return result

    @staticmethod
    def bulk_create(db: Session, results: list[LocalizationResult]) -> list[LocalizationResult]:
        """Persist multiple localization results efficiently in a single transaction."""
        db.add_all(results)
        db.commit()
        for r in results:
            db.refresh(r)
        return results

    @staticmethod
    def get_by_case(db: Session, case_id: int) -> list[LocalizationResult]:
        """Retrieve all localization results for a specific case."""
        return (
            db.query(LocalizationResult)
            .filter(LocalizationResult.case_id == case_id)
            .order_by(LocalizationResult.created_at.desc())
            .all()
        )

    @staticmethod
    def get_latest_by_case(db: Session, case_id: int) -> LocalizationResult | None:
        """Retrieve the most recent localization result for a case."""
        return (
            db.query(LocalizationResult)
            .filter(LocalizationResult.case_id == case_id)
            .order_by(LocalizationResult.created_at.desc())
            .first()
        )
