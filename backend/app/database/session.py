from typing import Generator
from sqlalchemy.orm import sessionmaker, Session
from app.database.engine import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a typed SQLAlchemy Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
