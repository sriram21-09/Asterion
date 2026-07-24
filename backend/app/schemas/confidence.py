from pydantic import BaseModel, ConfigDict, Field


class ConfidenceRunResponse(BaseModel):
    """Response schema for a confidence analysis run."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "case_code": "CASE-001",
                "confidence_score": 0.85,
                "confidence_level": "high",
                "error_ellipse_semi_major_m": 45.2,
                "error_ellipse_semi_minor_m": 22.1,
                "error_ellipse_orientation_deg": 15.5,
                "gdop": 1.8,
                "method": "gdop_covariance",
                "computation_time_ms": 1.25,
            }
        },
    )

    case_code: str = Field(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    )
    confidence_score: float = Field(
        ...,
        description="Calculated confidence score between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )
    confidence_level: str = Field(
        ..., description="Qualitative confidence rating (low, medium, high)"
    )
    error_ellipse_semi_major_m: float | None = Field(
        None, description="Semi-major axis of the 95% error ellipse in meters"
    )
    error_ellipse_semi_minor_m: float | None = Field(
        None, description="Semi-minor axis of the 95% error ellipse in meters"
    )
    error_ellipse_orientation_deg: float | None = Field(
        None, description="Orientation angle of the error ellipse in degrees"
    )
    gdop: float | None = Field(
        None, description="Geometric Dilution of Precision (lower is better)"
    )
    method: str = Field(..., description="Method used for confidence evaluation")
    computation_time_ms: float = Field(
        ..., description="Solver execution time in milliseconds"
    )
