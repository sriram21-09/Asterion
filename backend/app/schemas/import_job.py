from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CDRRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    first_bts_location: str | None = None
    last_latitude: float | None = None
    last_longitude: float | None = None
    last_cgi: str | None = None
    last_bts_location: str | None = None
    imei: str | None = None
    imsi: str | None = None
    smsc_number: str | None = None
    roaming_network: str | None = None
    created_at: datetime


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    operator: str
    status: str
    total_records: int
    parsed_records: int
    failed_records: int
    error_message: str | None = None
    case_id: int | None = None
    created_at: datetime
    updated_at: datetime


class CDRUploadResponse(BaseModel):
    job: ImportJobResponse
    summary: dict[str, Any]
