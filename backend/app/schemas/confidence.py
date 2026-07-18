from typing import Optional
from pydantic import BaseModel, ConfigDict


class ConfidenceRunResponse(BaseModel):
    """Response schema for a confidence analysis run."""

    model_config = ConfigDict(from_attributes=True)

    case_code: str
    confidence_score: float
    confidence_level: str
    error_ellipse_semi_major_m: Optional[float] = None
    error_ellipse_semi_minor_m: Optional[float] = None
    error_ellipse_orientation_deg: Optional[float] = None
    gdop: Optional[float] = None
    method: str
    computation_time_ms: float
