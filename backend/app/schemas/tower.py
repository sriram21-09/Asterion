from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TowerBase(BaseModel):
    tower_name: str = Field(
        default="Tower", description="Name or designation of the tower"
    )
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
        default=None,
        description="exact, prefix_lac, prefix_mnc, prefix_mcc, or unresolved",
    )


class TowerUpdate(BaseModel):
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


class TowerResponse(TowerBase):
    id: int
    confidence: float = 1.0
    confidence_category: str = "Known"
    resolution_method: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CGILookupRequest(BaseModel):
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
    operator: str | None = None
