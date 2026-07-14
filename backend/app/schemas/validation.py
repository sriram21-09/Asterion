"""
Validation-specific request/response schemas.

Used by the ``POST /measurements/validate`` endpoint to return structured
validation results for a batch of measurements.
"""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class MeasurementInput(BaseModel):
    """A single measurement submitted for validation.

    Mirrors the frontend ``Measurement`` type and the
    ``MeasurementResponse`` schema.
    """
    model_config = ConfigDict(from_attributes=True)

    measurement_id: str
    tower_id: str
    timestamp: str              # ISO 8601
    rssi_dbm: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timing_advance: Optional[float] = None
    uncertainty_m: Optional[float] = None


class ValidateMeasurementsRequest(BaseModel):
    """Payload for ``POST /measurements/validate``."""
    measurements: List[MeasurementInput]


class ValidationErrorItem(BaseModel):
    """A single structured validation error or warning."""
    field: str
    message: str
    severity: Severity
    measurement_index: int


class ValidateMeasurementsResponse(BaseModel):
    """Response payload for ``POST /measurements/validate``."""
    is_valid: bool
    valid_count: int
    rejected_count: int
    warning_count: int
    errors: List[ValidationErrorItem]
