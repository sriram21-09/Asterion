from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    measurement_code: str
    case_code: str
    scenario_code: Optional[str] = None
    timestamp: datetime
    rssi_dbm: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timing_advance: Optional[float] = None
    uncertainty_m: Optional[float] = None
