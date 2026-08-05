import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    """Application settings with dynamic environment variable resolution."""

    app_name: str = Field(default_factory=lambda: os.getenv("APP_NAME", "Asterion"))
    app_version: str = Field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))
    api_prefix: str = Field(default_factory=lambda: os.getenv("API_PREFIX", "/api/v1"))
    database_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./asterion.db")
    )
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    debug: bool = Field(
        default_factory=lambda: (
            os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
        )
    )

    heatmap_weight_density: float = Field(
        default_factory=lambda: float(os.getenv("HEATMAP_WEIGHT_DENSITY", "1.0"))
    )
    heatmap_weight_dwell_time: float = Field(
        default_factory=lambda: float(os.getenv("HEATMAP_WEIGHT_DWELL_TIME", "1.0"))
    )
    heatmap_weight_confidence: float = Field(
        default_factory=lambda: float(os.getenv("HEATMAP_WEIGHT_CONFIDENCE", "1.0"))
    )
    heatmap_weight_transitions: float = Field(
        default_factory=lambda: float(os.getenv("HEATMAP_WEIGHT_TRANSITIONS", "1.0"))
    )

    benchmark_min_validation_pass_rate: float = Field(
        default_factory=lambda: float(
            os.getenv("BENCHMARK_MIN_VALIDATION_PASS_RATE", "90.0")
        )
    )
    benchmark_min_tower_resolution_rate: float = Field(
        default_factory=lambda: float(
            os.getenv("BENCHMARK_MIN_TOWER_RESOLUTION_RATE", "80.0")
        )
    )
    benchmark_max_unknown_tower_percentage: float = Field(
        default_factory=lambda: float(
            os.getenv("BENCHMARK_MAX_UNKNOWN_TOWER_PERCENTAGE", "20.0")
        )
    )
    benchmark_min_kalman_improvement_factor: float = Field(
        default_factory=lambda: float(
            os.getenv("BENCHMARK_MIN_KALMAN_IMPROVEMENT_FACTOR", "1.2")
        )
    )

    @property
    def cors_origins(self) -> list[str]:
        raw = os.getenv("CORS_ORIGINS", "*")
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings()
