from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.services.provenance_service import ProvenanceService

router = APIRouter(tags=["provenance"])


@router.get(
    "/cases/{case_id}/provenance",
    response_model=APIResponse[dict[str, Any]],
    summary="Retrieve case measurement provenance audit snapshot",
    description="Returns exact count breakdown, status, percentages, and scientific integrity declarations for measurement provenance.",
)
def get_case_provenance(case_id: int, db: Session = Depends(get_db)):
    result = ProvenanceService.get_case_provenance(db, case_id=case_id)
    return APIResponse(success=True, data=result)


@router.get(
    "/dashboard/{case_id}/provenance",
    response_model=APIResponse[dict[str, Any]],
    summary="Retrieve dashboard measurement provenance audit snapshot",
    description="Alias endpoint for dashboard measurement provenance snapshot.",
)
def get_dashboard_provenance(case_id: int, db: Session = Depends(get_db)):
    result = ProvenanceService.get_case_provenance(db, case_id=case_id)
    return APIResponse(success=True, data=result)
