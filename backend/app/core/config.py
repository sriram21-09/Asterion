import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Asterion")
    app_version: str = os.getenv("APP_VERSION", "0.2.0")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./asterion.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]


settings = Settings()
