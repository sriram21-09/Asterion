"""Pydantic schemas for the Global Search API."""

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class CDRSearchResult(BaseModel):
    """CDR record search result with type discriminator."""

    model_config = ConfigDict(from_attributes=True)

    result_type: Literal["cdr_record"] = "cdr_record"
    id: int
    import_job_id: int
    case_id: int | None = None
    operator: str
    target_number: str | None = None
    b_party_number: str | None = None
    call_type: str | None = None
    service_type: str | None = None
    timestamp: datetime | None = None
    duration: int | None = 0
    latitude: float | None = None
    longitude: float | None = None
    first_cgi: str | None = None
    last_cgi: str | None = None
    imei: str | None = None
    imsi: str | None = None


class TowerSearchResult(BaseModel):
    """Tower search result with type discriminator."""

    model_config = ConfigDict(from_attributes=True)

    result_type: Literal["tower"] = "tower"
    id: int
    tower_name: str
    cgi: str | None = None
    ci: str | None = None
    mcc: str | None = None
    mnc: str | None = None
    lac: str | None = None
    operator: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CaseSearchResult(BaseModel):
    """Case search result with type discriminator."""

    model_config = ConfigDict(from_attributes=True)

    result_type: Literal["case"] = "case"
    id: int
    title: str
    description: str | None = None
    status: str = "open"


SearchResultItem = Annotated[
    Union[CDRSearchResult, TowerSearchResult, CaseSearchResult],
    Field(discriminator="result_type"),
]


class PaginatedSearchResponse(BaseModel):
    """Paginated search response containing results from multiple entity types."""

    results: list[SearchResultItem]
    total: int
    limit: int
    offset: int
    query: str
