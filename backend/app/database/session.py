from collections.abc import Generator

from app.database.engine import engine
from sqlalchemy.orm import Session, sessionmaker

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a typed SQLAlchemy Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
