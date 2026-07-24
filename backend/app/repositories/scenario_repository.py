from app.models.scenario import Scenario
from sqlalchemy.orm import Session


class ScenarioRepository:
    """Repository for Scenario database operations.

    # ponytail: static methods to avoid instantiation/dependency boilerplates
    """

    @staticmethod
    def get(db: Session, scenario_id: int) -> Scenario | None:
        return db.query(Scenario).filter(Scenario.id == scenario_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Scenario | None:
        return db.query(Scenario).filter(Scenario.name == name).first()

    @staticmethod
    def get_multi(db: Session, skip: int = 0, limit: int = 100) -> list[Scenario]:
        return db.query(Scenario).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, *, name: str, description: str | None = None) -> Scenario:
        db_obj = Scenario(name=name, description=description)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, scenario_id: int) -> Scenario | None:
        db_obj = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        if db_obj:
            db.delete(db_obj)
            db.commit()
        return db_obj
