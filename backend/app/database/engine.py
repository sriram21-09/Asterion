from app.core.config import settings
from sqlalchemy import create_engine

DATABASE_URL = settings.database_url

# Configure connection args specifically for SQLite to support multithreading
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
