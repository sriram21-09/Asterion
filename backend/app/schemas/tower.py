from datetime import datetime
<<<<<<< HEAD
from typing import Optional
=======

>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
from pydantic import BaseModel, ConfigDict, Field


class TowerBase(BaseModel):
    tower_name: str = Field(
        default="Tower", description="Name or designation of the tower"
    )
<<<<<<< HEAD
    cgi: Optional[str] = Field(
        default=None, description="Cell Global Identity (MCC-MNC-LAC-CI)"
    )
    mcc: Optional[str] = Field(default=None, description="Mobile Country Code")
    mnc: Optional[str] = Field(default=None, description="Mobile Network Code")
    lac: Optional[str] = Field(default=None, description="Location Area Code")
    ci: Optional[str] = Field(default=None, description="Cell Identifier")
    operator: Optional[str] = Field(
        default=None, description="Cellular Operator (Airtel, Jio, Vi, BSNL)"
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Latitude (null for Jio/Vi towers without coordinates)",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Longitude (null for Jio/Vi towers without coordinates)",
    )
    sector: Optional[str] = Field(default=None, description="Sector designation")


class TowerCreate(TowerBase):
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score (1.0 Known, 0.6 Estimated, 0.2 Unknown)",
    )
    confidence_category: Optional[str] = Field(
        default=None, description="Known, Estimated, or Unknown"
    )
    resolution_method: Optional[str] = Field(
=======
    cgi: str | None = Field(
        default=None, description="Cell Global Identity (MCC-MNC-LAC-CI)"
    )
    mcc: str | None = Field(default=None, description="Mobile Country Code")
    mnc: str | None = Field(default=None, description="Mobile Network Code")
    lac: str | None = Field(default=None, description="Location Area Code")
    ci: str | None = Field(default=None, description="Cell Identifier")
    operator: str | None = Field(
        default=None, description="Cellular Operator (Airtel, Jio, Vi, BSNL)"
    )
    latitude: float | None = Field(
        default=None,
        description="Latitude (null for Jio/Vi towers without coordinates)",
    )
    longitude: float | None = Field(
        default=None,
        description="Longitude (null for Jio/Vi towers without coordinates)",
    )
    sector: str | None = Field(default=None, description="Sector designation")


class TowerCreate(TowerBase):
    confidence: float | None = Field(
        default=None,
        description="Confidence score (1.0 Known, 0.6 Estimated, 0.2 Unknown)",
    )
    confidence_category: str | None = Field(
        default=None, description="Known, Estimated, or Unknown"
    )
    resolution_method: str | None = Field(
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
        default=None,
        description="exact, prefix_lac, prefix_mnc, prefix_mcc, or unresolved",
    )


class TowerUpdate(BaseModel):
<<<<<<< HEAD
    tower_name: Optional[str] = None
    cgi: Optional[str] = None
    mcc: Optional[str] = None
    mnc: Optional[str] = None
    lac: Optional[str] = None
    ci: Optional[str] = None
    operator: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sector: Optional[str] = None
    confidence: Optional[float] = None
    confidence_category: Optional[str] = None
    resolution_method: Optional[str] = None
=======
    tower_name: str | None = None
    cgi: str | None = None
    mcc: str | None = None
    mnc: str | None = None
    lac: str | None = None
    ci: str | None = None
    operator: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    sector: str | None = None
    confidence: float | None = None
    confidence_category: str | None = None
    resolution_method: str | None = None
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468


class TowerResponse(TowerBase):
    id: int
    confidence: float = 1.0
    confidence_category: str = "Known"
<<<<<<< HEAD
    resolution_method: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
=======
    resolution_method: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468

    model_config = ConfigDict(from_attributes=True)


class CGILookupRequest(BaseModel):
<<<<<<< HEAD
    cgi: Optional[str] = Field(
        default=None, description="Full CGI string e.g. 404-98-8331-23071"
    )
    mcc: Optional[str] = None
    mnc: Optional[str] = None
    lac: Optional[str] = None
    ci: Optional[str] = None


class CGILookupResponse(BaseModel):
    cgi: Optional[str] = None
    resolved_latitude: Optional[float] = None
    resolved_longitude: Optional[float] = None
=======
    cgi: str | None = Field(
        default=None, description="Full CGI string e.g. 404-98-8331-23071"
    )
    mcc: str | None = None
    mnc: str | None = None
    lac: str | None = None
    ci: str | None = None


class CGILookupResponse(BaseModel):
    cgi: str | None = None
    resolved_latitude: float | None = None
    resolved_longitude: float | None = None
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
    confidence: float = Field(
        ...,
        description="Confidence category weight: 1.0 (Known), 0.6 (Estimated), 0.2 (Unknown)",
    )
    confidence_category: str = Field(
        ..., description="Classification category: Known, Estimated, or Unknown"
    )
    resolution_method: str = Field(
        ..., description="exact, prefix_lac, prefix_mnc, prefix_mcc, or unresolved"
    )
    matched_towers_count: int = 0
<<<<<<< HEAD
    operator: Optional[str] = None
=======
    operator: str | None = None
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
