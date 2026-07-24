from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TrackingStepResponse(BaseModel):
    """A single step in the smoothed tracking path."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "step_number": 1,
                "latitude": 12.9721,
                "longitude": 77.5951,
                "velocity_kmh": 12.5,
                "timestamp": "2026-07-19T13:59:00Z",
                "heading_deg": 45.0,
            }
        },
    )

    step_number: int = Field(
        ..., description="Sequential index of this position on the track", ge=0
    )
    latitude: float = Field(
        ...,
        description="Smoothed position latitude coordinate (WGS84)",
        ge=-90.0,
        le=90.0,
    )
    longitude: float = Field(
        ...,
        description="Smoothed position longitude coordinate (WGS84)",
        ge=-180.0,
        le=180.0,
    )
    velocity_kmh: float = Field(
        ..., description="Estimated instantaneous device velocity in km/h", ge=0.0
    )
    timestamp: datetime | None = Field(
        None, description="Timestamp of this step on the track"
    )
    heading_deg: float | None = Field(
        None,
        description="Estimated movement heading angle in degrees (0-360, North = 0)",
        ge=0.0,
        le=360.0,
    )


class TrackingRunResponse(BaseModel):
    """Full response from a tracking run."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "case_code": "CASE-001",
                "total_steps": 5,
                "path": [
                    {
                        "step_number": 0,
                        "latitude": 12.9721,
                        "longitude": 77.5951,
                        "velocity_kmh": 0.0,
                        "timestamp": "2026-07-19T13:59:00Z",
                        "heading_deg": 0.0,
                    },
                    {
                        "step_number": 1,
                        "latitude": 12.9725,
                        "longitude": 77.5955,
                        "velocity_kmh": 15.2,
                        "timestamp": "2026-07-19T13:59:10Z",
                        "heading_deg": 45.0,
                    },
                ],
                "distance_km": 0.062,
                "avg_velocity_kmh": 7.6,
                "computation_time_ms": 3.8,
            }
        },
    )

    case_code: str = Field(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    )
    total_steps: int = Field(
        ..., description="Total number of discrete steps in the generated track", ge=0
    )
    path: list[TrackingStepResponse] = Field(
        ..., description="Array of chronologically ordered track points"
    )
    distance_km: float = Field(
        ..., description="Total length of the track path in kilometers", ge=0.0
    )
    avg_velocity_kmh: float = Field(
        ...,
        description="Average velocity computed across the entire track path",
        ge=0.0,
    )
    computation_time_ms: float = Field(
        ..., description="Solver execution time in milliseconds"
    )
