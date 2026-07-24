from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MovementEventResponse(BaseModel):
    """A single reconstructed movement event."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "sequence_number": 1,
                "event_type": "handover",
                "timestamp": "2026-07-19T13:59:00Z",
                "latitude": 12.9721,
                "longitude": 77.5951,
                "from_cgi": "404-45-1234-5678",
                "to_cgi": "404-45-1234-5679",
                "speed_kmh": 25.4,
                "heading_deg": 45.0,
                "distance_from_prev_m": 120.5,
                "dwell_time_seconds": 30.0,
                "confidence": 0.95,
            }
        },
    )

    sequence_number: int = Field(
        ..., description="Sequential index of this event in the movement path", ge=1
    )
    event_type: str = Field(
        ...,
        description="Type of movement event (e.g. location_update, handover, call_start, call_end, sms, data_session)",
    )
    timestamp: Optional[datetime] = Field(
        None, description="Timestamp of the event in ISO format"
    )
    latitude: Optional[float] = Field(
        None,
        description="Best estimate latitude coordinate (WGS84)",
        ge=-90.0,
        le=90.0,
    )
    longitude: Optional[float] = Field(
        None,
        description="Best estimate longitude coordinate (WGS84)",
        ge=-180.0,
        le=180.0,
    )
    from_cgi: Optional[str] = Field(
        None, description="Source Cell Global Identifier for handovers"
    )
    to_cgi: Optional[str] = Field(
        None, description="Target Cell Global Identifier for handovers"
    )
    speed_kmh: Optional[float] = Field(
        None, description="Estimated speed at this event in km/h", ge=0.0
    )
    heading_deg: Optional[float] = Field(
        None,
        description="Estimated bearing heading in degrees (0-360)",
        ge=0.0,
        le=360.0,
    )
    distance_from_prev_m: Optional[float] = Field(
        None, description="Distance from previous event in meters", ge=0.0
    )
    dwell_time_seconds: Optional[float] = Field(
        None, description="Time spent at this location prior to moving", ge=0.0
    )
    confidence: Optional[float] = Field(
        None, description="Confidence score [0.0 - 1.0]", ge=0.0, le=1.0
    )


class MovementReconstructionResponse(BaseModel):
    """Response payload for movement sequence reconstruction."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "case_code": "CASE-001",
                "total_events": 5,
                "events": [
                    {
                        "sequence_number": 1,
                        "event_type": "call_start",
                        "timestamp": "2026-07-19T13:59:00Z",
                        "latitude": 12.9721,
                        "longitude": 77.5951,
                        "from_cgi": None,
                        "to_cgi": None,
                        "speed_kmh": 0.0,
                        "heading_deg": None,
                        "distance_from_prev_m": 0.0,
                        "dwell_time_seconds": 0.0,
                        "confidence": 0.95,
                    }
                ],
                "handover_count": 1,
                "total_distance_km": 1.25,
                "time_span_hours": 0.5,
                "computation_time_ms": 12.4,
            }
        },
    )

    case_code: str = Field(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    )
    total_events: int = Field(
        ..., description="Total number of discrete movement events generated", ge=0
    )
    events: List[MovementEventResponse] = Field(
        ..., description="Chronologically ordered array of movement events"
    )
    handover_count: int = Field(
        ..., description="Total number of handover events detected", ge=0
    )
    total_distance_km: float = Field(
        ...,
        description="Total distance traversed across all events in kilometers",
        ge=0.0,
    )
    time_span_hours: float = Field(
        ..., description="Time duration between first and last event in hours", ge=0.0
    )
    computation_time_ms: float = Field(
        ..., description="Execution time of movement reconstruction in milliseconds"
    )
