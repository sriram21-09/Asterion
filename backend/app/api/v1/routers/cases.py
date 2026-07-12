from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.case import CaseCreate, CaseResponse
from app.schemas.response import APIResponse
from app.services.case_service import CaseService
from app.core.config import settings
from typing import List, Optional

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post(
    "/",
    response_model=APIResponse[CaseResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case",
    description="Validate inputs and create a new localization investigation case.",
)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    result = CaseService.create_case(db, case_in)
    return APIResponse(success=True, data=result)


@router.get(
    "/",
    response_model=APIResponse[List[CaseResponse]],
    summary="Retrieve all cases",
    description="Retrieve a paginated list of cases.",
)
def list_cases(
    page: Optional[int] = Query(None, description="Page number starting from 1"),
    page_size: Optional[int] = Query(None, description="Number of items per page"),
    db: Session = Depends(get_db),
):
    result = CaseService.list_cases(db, page=page, page_size=page_size)
    return APIResponse(success=True, data=result)


@router.get(
    "/health",
    summary="Case router health check",
    description="Returns the health status of the cases component.",
)
def health_check():
    return {"status": "healthy", "service": "cases-api", "version": settings.app_version}


@router.get(
    "/{id}",
    response_model=APIResponse[CaseResponse],
    summary="Retrieve a case by ID",
    description="Get details of a single investigation case.",
)
def get_case(id: int, db: Session = Depends(get_db)):
    result = CaseService.get_case(db, case_id=id)
    return APIResponse(success=True, data=result)


@router.delete(
    "/{id}",
    response_model=APIResponse[CaseResponse],
    summary="Delete a case by ID",
    description="Remove a case and return the deleted object.",
)
def delete_case(id: int, db: Session = Depends(get_db)):
    result = CaseService.delete_case(db, case_id=id)
    return APIResponse(success=True, data=result)
