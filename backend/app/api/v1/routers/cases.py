from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.case import CaseCreate, CaseResponse
from app.services.case_service import CaseService
from typing import List, Optional

router = APIRouter(
    prefix="/cases",
    tags=["cases"]
)

@router.post(
    "/",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case",
    description="Validate inputs and create a new localization investigation case."
)
def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db)
):
    return CaseService.create_case(db, case_in)

@router.get(
    "/",
    response_model=List[CaseResponse],
    summary="Retrieve all cases",
    description="Retrieve a paginated list of cases."
)
def list_cases(
    page: Optional[int] = Query(None, description="Page number starting from 1"),
    page_size: Optional[int] = Query(None, description="Number of items per page"),
    db: Session = Depends(get_db)
):
    return CaseService.list_cases(db, page=page, page_size=page_size)

@router.get(
    "/health",
    summary="Case router health check",
    description="Returns the health status of the cases component."
)
def health_check():
    return {
        "status": "healthy",
        "service": "cases-api",
        "version": "1.0.0"
    }

@router.get(
    "/{id}",
    response_model=CaseResponse,
    summary="Retrieve a case by ID",
    description="Get details of a single investigation case."
)
def get_case(
    id: int,
    db: Session = Depends(get_db)
):
    return CaseService.get_case(db, case_id=id)

@router.delete(
    "/{id}",
    response_model=CaseResponse,
    summary="Delete a case by ID",
    description="Remove a case and return the deleted object."
)
def delete_case(
    id: int,
    db: Session = Depends(get_db)
):
    return CaseService.delete_case(db, case_id=id)
