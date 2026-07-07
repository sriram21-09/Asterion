"""
Measurement Data Model
======================

Defines the schema for a single signal measurement captured from a cell tower.
Measurements are the primary input to localization algorithms — each record
represents one observed signal strength (RSSI) reading between a device and
a tower at a specific point in time.

RSSI (Received Signal Strength Indicator)
------------------------------------------
RSSI is measured in dBm and indicates the power level of a received radio
signal. In typical cellular environments:

    * **Strong signal:**  -50 dBm (very close to tower)
    * **Good signal:**    -70 dBm (normal indoor/urban)
    * **Weak signal:**    -90 dBm (cell edge)
    * **Very weak:**     -110 dBm (near loss of connectivity)
    * **No signal:**     -120 dBm or below

The valid range for this model is **-150.0 to 0.0 dBm** to accommodate
both standard cellular and low-power IoT measurements.

Required Fields
----------------
Every measurement **must** include:
    - ``measurement_id``: A unique identifier for the reading
    - ``tower_id``: Which tower produced the signal
    - ``timestamp``: When the measurement was taken (ISO 8601)
    - ``rssi_dbm``: The received signal strength in dBm

Optional Fields
----------------
    - ``latitude`` / ``longitude``: Known position of measurement point
    - ``timing_advance``: GSM Timing Advance (TA) value for distance estimation
    - ``uncertainty_m``: Measurement uncertainty in meters

Example RSSI Measurement
--------------------------
.. code-block:: json

    {
        "measurement_id": "M001",
        "tower_id": "T001",
        "timestamp": "2026-07-07T10:30:00Z",
        "rssi_dbm": -72.0,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "timing_advance": null,
        "uncertainty_m": 150.0
    }

Usage:
    >>> from scientific.models.measurement import Measurement
    >>> from datetime import datetime, timezone
    >>> m = Measurement(
    ...     measurement_id="M001",
    ...     tower_id="T001",
    ...     timestamp=datetime(2026, 7, 7, 10, 30, tzinfo=timezone.utc),
    ...     rssi_dbm=-72.0,
    ... )
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Measurement(BaseModel):
    """Schema for a single signal measurement from a cell tower.

    Attributes:
        measurement_id: Unique identifier for this measurement.
        tower_id: Identifier of the tower that produced the signal.
        timestamp: ISO 8601 timestamp of the measurement.
        rssi_dbm: Received Signal Strength Indicator in dBm (-150 to 0).
        latitude: Measurement point latitude, if known.
        longitude: Measurement point longitude, if known.
        timing_advance: GSM Timing Advance value for distance estimation.
        uncertainty_m: Measurement uncertainty in meters.
    """

    measurement_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for this measurement",
        examples=["M001"],
    )
    tower_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the tower that produced the signal",
        examples=["T001"],
    )
    timestamp: datetime = Field(
        ...,
        description="ISO 8601 timestamp of the measurement",
        examples=["2026-07-07T10:30:00Z"],
    )
    rssi_dbm: float = Field(
        ...,
        ge=-150.0,
        le=0.0,
        description="Received Signal Strength Indicator in dBm",
        examples=[-72.0],
    )
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Measurement point latitude (WGS84), if known",
        examples=[12.9716],
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Measurement point longitude (WGS84), if known",
        examples=[77.5946],
    )
    timing_advance: Optional[float] = Field(
        default=None,
        ge=0,
        description="GSM Timing Advance (TA) value for distance estimation",
    )
    uncertainty_m: Optional[float] = Field(
        default=None,
        ge=0,
        description="Measurement uncertainty in meters",
        examples=[150.0],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "measurement_id": "M001",
                    "tower_id": "T001",
                    "timestamp": "2026-07-07T10:30:00Z",
                    "rssi_dbm": -72.0,
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "timing_advance": None,
                    "uncertainty_m": 150.0,
                }
            ]
        }
    }
