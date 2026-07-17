from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class TrackingStepResponse(BaseModel):
    """A single step in the smoothed tracking path."""

    model_config = ConfigDict(from_attributes=True)

    step_number: int
    latitude: float
    longitude: float
    velocity_kmh: float
    timestamp: Optional[datetime] = None
    heading_deg: Optional[float] = None


class TrackingRunResponse(BaseModel):
    """Full response from a tracking run."""

    model_config = ConfigDict(from_attributes=True)

    case_code: str
    total_steps: int
    path: List[TrackingStepResponse]
    distance_km: float
    avg_velocity_kmh: float
    computation_time_ms: float
