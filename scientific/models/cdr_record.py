"""
CDR Record Data Model
=====================

Defines the scientific schema for a cellular Call Detail Record (CDR).
CDRs are imported from operator-specific CSV files, normalized, and validated.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class CDRRecord(BaseModel):
    """Schema for a normalized Call Detail Record (CDR).

    Attributes:
        id: Optional unique database identifier.
        import_job_id: Optional ID linking to the import job.
        case_id: Optional ID linking to the investigation case.
        operator: Operator name (e.g. airtel, bsnl, jio, vi).
        target_number: Phone number of the observed subscriber (A-party).
        b_party_number: Phone number of the other party (B-party).
        call_type: Call type (e.g., IN, OUT, SMT, SMS).
        service_type: Service type (e.g., Voice, SMS).
        timestamp: Timestamp when the event occurred.
        duration: Call duration in seconds.
        latitude: Latitude of the start location (WGS84).
        longitude: Longitude of the start location (WGS84).
        first_cgi: Cell Global ID of the start cell.
        first_bts_location: String description/address of the start BTS.
        last_latitude: Latitude of the end location (WGS84).
        last_longitude: Longitude of the end location (WGS84).
        last_cgi: Cell Global ID of the end cell.
        last_bts_location: String description/address of the end BTS.
        imei: Mobile equipment identifier.
        imsi: Subscriber identification card ID.
        smsc_number: SMS center identifier.
        roaming_network: Operator/Circle identifier when roaming.
        raw_data: Optional dictionary containing raw CSV parsing information.
    """

    id: Optional[int] = Field(
        default=None,
        description="Unique database identifier",
    )
    import_job_id: Optional[int] = Field(
        default=None,
        description="Identifier of the import job",
    )
    case_id: Optional[int] = Field(
        default=None,
        description="Identifier of the associated investigation case",
    )
    operator: str = Field(
        ...,
        min_length=1,
        description="Cellular operator name (e.g. airtel, bsnl, jio, vi)",
        examples=["airtel"],
    )
    target_number: Optional[str] = Field(
        default=None,
        description="Phone number of the observed subscriber",
        examples=["9714499703"],
    )
    b_party_number: Optional[str] = Field(
        default=None,
        description="Phone number of the second party",
        examples=["8128778750"],
    )
    call_type: Optional[str] = Field(
        default=None,
        description="Type of connection/event (e.g., IN, OUT, SMT)",
    )
    service_type: Optional[str] = Field(
        default=None,
        description="Service type (e.g., Voice, SMS)",
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Event timestamp",
    )
    duration: Optional[int] = Field(
        default=0,
        description="Call duration in seconds",
    )
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Start point latitude (WGS84), if known",
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Start point longitude (WGS84), if known",
    )
    first_cgi: Optional[str] = Field(
        default=None,
        description="Start Cell Global Identifier",
    )
    first_bts_location: Optional[str] = Field(
        default=None,
        description="Start BTS location description",
    )
    last_latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="End point latitude (WGS84), if known",
    )
    last_longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="End point longitude (WGS84), if known",
    )
    last_cgi: Optional[str] = Field(
        default=None,
        description="End Cell Global Identifier",
    )
    last_bts_location: Optional[str] = Field(
        default=None,
        description="End BTS location description",
    )
    imei: Optional[str] = Field(
        default=None,
        description="International Mobile Equipment Identity",
    )
    imsi: Optional[str] = Field(
        default=None,
        description="International Mobile Subscriber Identity",
    )
    smsc_number: Optional[str] = Field(
        default=None,
        description="SMS center number",
    )
    roaming_network: Optional[str] = Field(
        default=None,
        description="Roaming network identifier",
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw CSV record data",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "operator": "airtel",
                    "target_number": "9714499703",
                    "b_party_number": "8128778750",
                    "call_type": "OUT",
                    "timestamp": "2026-07-07T10:30:00Z",
                    "duration": 41,
                    "latitude": 21.29327,
                    "longitude": 72.88987,
                }
            ]
        }
    }
