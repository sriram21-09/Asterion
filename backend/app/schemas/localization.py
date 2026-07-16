from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class LocalizationRunResponse(BaseModel):
    """Response schema for a localization run."""

    model_config = ConfigDict(from_attributes=True)

    case_code: str
    scenario_code: Optional[str] = None
    algorithm: str
    estimated_latitude: float
    estimated_longitude: float
    error_m: Optional[float] = None
    signals_used: int
    computation_time_ms: Optional[float] = None
    timestamp: datetime
