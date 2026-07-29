from pydantic import BaseModel, Field


class CaseComparisonMetrics(BaseModel):
    case_id: int = Field(..., description="ID of the case")
    total_distance_m: float = Field(..., description="Total distance moved in meters")
    average_confidence: float = Field(..., description="Average confidence score")
    validation_pass_rate: float | None = Field(
        None, description="Validation pass rate percentage"
    )


class CaseComparisonResponse(BaseModel):
    cases: list[CaseComparisonMetrics] = Field(
        ..., description="Metrics for each compared case"
    )
    overlapping_towers: list[str] = Field(
        ..., description="List of CGIs (towers) overlapping between all compared cases"
    )
    max_distance_difference_m: float = Field(
        ...,
        description="Maximum absolute difference in total distance among the compared cases",
    )
