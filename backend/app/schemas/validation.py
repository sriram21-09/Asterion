"""
Validation-specific request/response schemas.

Used by the ``POST /measurements/validate`` endpoint to return structured
validation results for a batch of measurements.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class MeasurementInput(BaseModel):
    """A single measurement submitted for validation.

    Mirrors the frontend ``Measurement`` type and the
    ``MeasurementResponse`` schema.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "measurement_id": "M001",
                "tower_id": "T001",
                "timestamp": "2026-07-19T13:59:55Z",
                "rssi_dbm": -72.5,
                "latitude": 12.9721,
                "longitude": 77.5951,
                "timing_advance": 2,
                "uncertainty_m": 50.0,
            }
        },
    )

    measurement_id: str = Field(
        ..., description="Unique measurement identifier", examples=["M001"]
    )
    tower_id: str = Field(
        ...,
        description="Unique tower identifier that recorded the signal",
        examples=["T001"],
    )
    timestamp: str = Field(
        ..., description="ISO 8601 string when the measurement was captured"
    )
    rssi_dbm: float = Field(
        ...,
        description="Received Signal Strength Indicator in dBm (typically negative)",
    )
    latitude: float | None = Field(
        None, description="Optional GPS latitude reported by device"
    )
    longitude: float | None = Field(
        None,
        description="Optional GPS longitude reported by device",
    )
    timing_advance: float | None = Field(
        None, description="Optional cellular Timing Advance value"
    )
    uncertainty_m: float | None = Field(
        None, description="Optional GPS accuracy uncertainty radius in meters"
    )


class ValidateMeasurementsRequest(BaseModel):
    """Payload for ``POST /measurements/validate``."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "measurements": [
                    {
                        "measurement_id": "M001",
                        "tower_id": "T001",
                        "timestamp": "2026-07-19T13:59:55Z",
                        "rssi_dbm": -72.5,
                        "latitude": 12.9721,
                        "longitude": 77.5951,
                        "timing_advance": 2,
                        "uncertainty_m": 50.0,
                    }
                ]
            }
        }
    )
    measurements: list[MeasurementInput] = Field(
        ..., description="Batch list of measurements to validate"
    )


class ValidationErrorItem(BaseModel):
    """A single structured validation error or warning."""

    field: str = Field(..., description="The model field where the violation occurred")
    message: str = Field(
        ..., description="Human-readable explanation of why validation failed"
    )
    severity: Severity = Field(
        ..., description="Violation severity level (error or warning)"
    )
    measurement_index: int = Field(
        ..., description="Zero-based index of the measurement in the input list", ge=0
    )


class ValidateMeasurementsResponse(BaseModel):
    """Response payload for ``POST /measurements/validate``."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": True,
                "valid_count": 1,
                "rejected_count": 0,
                "warning_count": 0,
                "errors": [],
            }
        }
    )
    is_valid: bool = Field(
        ..., description="True if no errors were generated (warnings are allowed)"
    )
    valid_count: int = Field(
        ..., description="Total measurements passing validation successfully", ge=0
    )
    rejected_count: int = Field(
        ..., description="Total measurements rejected due to validation errors", ge=0
    )
    warning_count: int = Field(
        ..., description="Total warnings generated across all measurements", ge=0
    )
    errors: list[ValidationErrorItem] = Field(
        ..., description="List of structured errors and warnings found"
    )
