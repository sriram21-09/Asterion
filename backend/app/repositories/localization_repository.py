from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.localization_result import LocalizationResult


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
    def get_by_case(db: Session, case_id: int) -> List[LocalizationResult]:
        """Retrieve all localization results for a specific case."""
        return (
            db.query(LocalizationResult)
            .filter(LocalizationResult.case_id == case_id)
            .order_by(LocalizationResult.created_at.desc())
            .all()
        )

    @staticmethod
    def get_latest_by_case(db: Session, case_id: int) -> Optional[LocalizationResult]:
        """Retrieve the most recent localization result for a case."""
        return (
            db.query(LocalizationResult)
            .filter(LocalizationResult.case_id == case_id)
            .order_by(LocalizationResult.created_at.desc())
            .first()
        )
