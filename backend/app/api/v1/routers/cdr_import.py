from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.import_job import ImportJob
from app.models.cdr_record import CDRRecord
from app.schemas.import_job import CDRRecordResponse, CDRUploadResponse, ImportJobResponse
from app.schemas.response import APIResponse
from app.services.import_service import CDRImportService

router = APIRouter(prefix="/import", tags=["import"])


@router.post(
    "/upload",
    response_model=APIResponse[CDRUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a CDR CSV file",
    description="Upload a raw CDR file (Airtel, BSNL, etc.), auto-detect or specify operator, and parse into unified CDR records.",
)
async def upload_cdr_file(
    file: UploadFile = File(...),
    case_id: Optional[int] = Form(None),
    operator: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    filename = file.filename or "unknown.csv"
    if not filename.lower().endswith(".csv") and not filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and TXT files are supported for CDR import.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    service = CDRImportService()
    result = service.process_upload(
        file_name=filename,
        file_bytes=content,
        case_id=case_id,
        operator=operator,
        db=db,
    )


    upload_resp = CDRUploadResponse(
        job=ImportJobResponse.model_validate(result["job"]),
        summary=result["summary"],
    )

    return APIResponse(success=True, data=upload_resp)


@router.get(
    "/jobs/{job_id}",
    response_model=APIResponse[ImportJobResponse],
    summary="Get import job by ID",
    description="Retrieve status and metadata for a specific import job.",
)
def get_import_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job with ID {job_id} not found.",
        )
    return APIResponse(success=True, data=ImportJobResponse.model_validate(job))


@router.get(
    "/jobs/{job_id}/records",
    response_model=APIResponse[List[CDRRecordResponse]],
    summary="Get parsed records for an import job",
    description="Retrieve parsed CDR records associated with an import job.",
)
def get_import_job_records(
    job_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job with ID {job_id} not found.",
        )

    records = (
        db.query(CDRRecord)
        .filter(CDRRecord.import_job_id == job_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    res_records = [CDRRecordResponse.model_validate(r) for r in records]
    return APIResponse(success=True, data=res_records)
