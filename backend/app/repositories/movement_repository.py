<<<<<<< HEAD
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.movement_event import MovementEvent
=======
from app.models.movement_event import MovementEvent
from sqlalchemy.orm import Session
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468


class MovementRepository:
    """Repository for MovementEvent database operations.

    # ponytail: static methods to avoid instantiation/dependency boilerplate
    """

    @staticmethod
    def create(db: Session, event: MovementEvent) -> MovementEvent:
        """Persist a single movement event."""
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
<<<<<<< HEAD
    def bulk_create(db: Session, events: List[MovementEvent]) -> List[MovementEvent]:
=======
    def bulk_create(db: Session, events: list[MovementEvent]) -> list[MovementEvent]:
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
        """Persist a list of movement events in one commit."""
        db.add_all(events)
        db.commit()
        for e in events:
            db.refresh(e)
        return events

    @staticmethod
<<<<<<< HEAD
    def get_by_case(db: Session, case_id: int) -> List[MovementEvent]:
=======
    def get_by_case(db: Session, case_id: int) -> list[MovementEvent]:
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
        """Retrieve all movement events for a case, ordered by sequence_number."""
        return (
            db.query(MovementEvent)
            .filter(MovementEvent.case_id == case_id)
            .order_by(MovementEvent.sequence_number.asc())
            .all()
        )

    @staticmethod
    def get_by_case_and_type(
        db: Session, case_id: int, event_type: str
<<<<<<< HEAD
    ) -> List[MovementEvent]:
=======
    ) -> list[MovementEvent]:
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
        """Retrieve movement events for a case filtered by event_type."""
        return (
            db.query(MovementEvent)
            .filter(
                MovementEvent.case_id == case_id,
                MovementEvent.event_type == event_type,
            )
            .order_by(MovementEvent.sequence_number.asc())
            .all()
        )

    @staticmethod
    def delete_by_case(db: Session, case_id: int) -> int:
        """Delete all movement events for a case. Returns count deleted."""
        count = (
            db.query(MovementEvent)
            .filter(MovementEvent.case_id == case_id)
            .delete(synchronize_session="fetch")
        )
        db.commit()
        return count
