from sqlalchemy.orm import Session
from app.models.case import Case
from typing import List, Optional


class CaseRepository:
    """Repository for Case database operations.

    # ponytail: static methods to avoid instantiation/dependency boilerplates
    """

    @staticmethod
    def get(db: Session, case_id: int) -> Optional[Case]:
        return db.query(Case).filter(Case.id == case_id).first()

    @staticmethod
    def get_multi(db: Session, skip: int = 0, limit: int = 100) -> List[Case]:
        return db.query(Case).offset(skip).limit(limit).all()

    @staticmethod
    def create(
        db: Session,
        *,
        title: str,
        description: Optional[str] = None,
        scenario_id: Optional[int] = None,
    ) -> Case:
        db_obj = Case(title=title, description=description, scenario_id=scenario_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, case_id: int) -> Optional[Case]:
        db_obj = db.query(Case).filter(Case.id == case_id).first()
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj
