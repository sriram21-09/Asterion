from app.core.config import settings
from sqlalchemy import create_engine

DATABASE_URL = settings.database_url

# Configure connection args specifically for SQLite to support multithreading
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if db_path != ":memory:":
            import os

            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args=connect_args)


def init_db():
    """Ensure database is up to date using Alembic migrations."""
    import logging
    from alembic.config import Config
    from alembic import command
    import os

    logger = logging.getLogger(__name__)

    try:
        # Assuming we are running from the backend directory
        alembic_ini_path = os.path.join(os.getcwd(), "alembic.ini")
        if not os.path.exists(alembic_ini_path):
            logger.warning(
                f"alembic.ini not found at {alembic_ini_path}. Skipping migrations."
            )
            return

        alembic_cfg = Config(alembic_ini_path)
        command.upgrade(alembic_cfg, "head")
        logger.info("Successfully ran database migrations.")
    except Exception as e:
        import sqlalchemy.exc

        if isinstance(
            e, sqlalchemy.exc.DatabaseError
        ) or "file is not a database" in str(e):
            logger.critical(
                "SQLite database is corrupted! Renaming to .corrupt and trying again..."
            )
            try:
                db_path = settings.database_url.replace("sqlite:///", "")
                if os.path.exists(db_path):
                    import shutil

                    shutil.move(db_path, f"{db_path}.corrupt")
                # Try one more time with a fresh database
                command.upgrade(alembic_cfg, "head")
                logger.info(
                    "Successfully recovered by creating a fresh database. Old database saved as .corrupt."
                )
            except Exception as recovery_error:
                logger.critical(f"Recovery failed: {recovery_error}")
                raise
        else:
            logger.error(f"Failed to run database migrations: {e}")
            raise
