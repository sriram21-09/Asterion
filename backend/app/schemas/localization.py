from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LocalizationRunResponse(BaseModel):
    """Response schema for a localization run."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "case_code": "CASE-001",
                "scenario_code": "SCN-001",
                "algorithm": "multilateration",
                "estimated_latitude": 12.9721,
                "estimated_longitude": 77.5951,
                "error_m": 8.5,
                "signals_used": 4,
                "computation_time_ms": 2.45,
                "timestamp": "2026-07-19T13:59:55Z",
            }
        },
    )

    case_code: str = Field(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    )
    scenario_code: str | None = Field(
        None, description="The unique Scenario Code if linked", examples=["SCN-001"]
    )
    algorithm: str = Field(
        ...,
        description="Localization algorithm used (e.g. multilateration, weighted_centroid)",
    )
    estimated_latitude: float = Field(
        ..., description="Estimated latitude coordinate (WGS84)", ge=-90.0, le=90.0
    )
    estimated_longitude: float = Field(
        ..., description="Estimated longitude coordinate (WGS84)", ge=-180.0, le=180.0
    )
    error_m: float | None = Field(
        None, description="Calculated circular error probability radius in meters"
    )
    signals_used: int = Field(
        ...,
        description="Number of distinct cellular tower signals used in the calculation",
        ge=1,
    )
    computation_time_ms: float | None = Field(
        None, description="Solver execution time in milliseconds"
    )
    timestamp: datetime = Field(
        ..., description="Timestamp when the localization estimation was computed"
    )
