import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    """Application settings with dynamic environment variable resolution."""

    app_name: str = Field(default_factory=lambda: os.getenv("APP_NAME", "Asterion"))
    app_version: str = Field(default_factory=lambda: os.getenv("APP_VERSION", "0.2.0"))
    api_prefix: str = Field(default_factory=lambda: os.getenv("API_PREFIX", "/api/v1"))
    database_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./asterion.db")
    )
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    debug: bool = Field(
        default_factory=lambda: os.getenv("DEBUG", "False").lower()
        in ("true", "1", "yes")
    )

    @property
    def cors_origins(self) -> list[str]:
        raw = os.getenv("CORS_ORIGINS", "*")
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings()
