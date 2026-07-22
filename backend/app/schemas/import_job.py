from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict


class CDRRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    import_job_id: int
    case_id: Optional[int] = None
    operator: str
    target_number: Optional[str] = None
    b_party_number: Optional[str] = None
    call_type: Optional[str] = None
    service_type: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration: Optional[int] = 0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    first_cgi: Optional[str] = None
    first_bts_location: Optional[str] = None
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None
    last_cgi: Optional[str] = None
    last_bts_location: Optional[str] = None
    imei: Optional[str] = None
    imsi: Optional[str] = None
    smsc_number: Optional[str] = None
    roaming_network: Optional[str] = None
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
    error_message: Optional[str] = None
    case_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class CDRUploadResponse(BaseModel):
    job: ImportJobResponse
    summary: Dict[str, Any]
