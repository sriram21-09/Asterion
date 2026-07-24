from app.models.movement_event import MovementEvent
from sqlalchemy.orm import Session


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
    def bulk_create(db: Session, events: list[MovementEvent]) -> list[MovementEvent]:
        """Persist a list of movement events in one commit."""
        db.add_all(events)
        db.commit()
        for e in events:
            db.refresh(e)
        return events

    @staticmethod
    def get_by_case(db: Session, case_id: int) -> list[MovementEvent]:
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
    ) -> list[MovementEvent]:
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
