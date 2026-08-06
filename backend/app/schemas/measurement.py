from datetime import datetime
from pydantic import BaseModel, ConfigDict
from scientific.models.measurement import MeasurementSource


class MeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    measurement_code: str
    case_code: str
    scenario_code: str | None = None
    timestamp: datetime
    rssi_dbm: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    timing_advance: float | None = None
    uncertainty_m: float | None = None
    is_simulated: bool = False
    source: MeasurementSource = MeasurementSource.REAL
    tower_id: str | None = None
