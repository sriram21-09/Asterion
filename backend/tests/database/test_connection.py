from sqlalchemy import text
from app.database.engine import engine


def test_database_connection():
    """Verify that we can successfully connect to the SQLite database and run a simple query."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1
