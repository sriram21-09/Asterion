from app.database.session import get_db
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.schemas.comparison import CaseComparisonResponse
from app.schemas.response import APIResponse
from app.services.case_service import CaseService
from app.services.comparison_service import ComparisonService
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

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
    response_model=APIResponse[list[CaseResponse]],
    summary="Retrieve all cases",
    description="Retrieve a paginated list of cases.",
)
def list_cases(
    page: int | None = Query(None, description="Page number starting from 1"),
    page_size: int | None = Query(None, description="Number of items per page"),
    db: Session = Depends(get_db),
):
    result = CaseService.list_cases(db, page=page, page_size=page_size)
    return APIResponse(success=True, data=result)


@router.get(
    "/compare",
    response_model=APIResponse[CaseComparisonResponse],
    summary="Compare cases",
    description="Compare multiple cases (overlapping towers, distance differences, confidence averages).",
)
def compare_cases(
    ids: str = Query(..., description="Comma-separated list of case IDs"),
    db: Session = Depends(get_db),
):
    case_ids = []
    for id_str in ids.split(","):
        try:
            case_ids.append(int(id_str.strip()))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid case ID: {id_str}")

    result = ComparisonService.compare_cases(db, case_ids)
    return APIResponse(success=True, data=result)


@router.get(
    "/{id}/provenance",
    response_model=APIResponse[dict],
    summary="Retrieve case measurement provenance audit snapshot",
    description="Returns exact count breakdown, status, percentages, and scientific integrity declarations for measurement provenance.",
)
def get_case_provenance_in_cases(id: int, db: Session = Depends(get_db)):
    from app.services.provenance_service import ProvenanceService

    result = ProvenanceService.get_case_provenance(db, case_id=id)
    return APIResponse(success=True, data=result)


@router.get(
    "/{id}",
    response_model=APIResponse[CaseResponse],
    summary="Retrieve a case by ID",
    description="Get details of a single investigation case.",
)
def get_case(id: int, db: Session = Depends(get_db)):
    result = CaseService.get_case(db, case_id=id)
    return APIResponse(success=True, data=result)


@router.patch(
    "/{id}",
    response_model=APIResponse[CaseResponse],
    summary="Update case status or attributes",
    description="Update status, scenario_id, or augmentation settings for a case.",
)
@router.put(
    "/{id}",
    response_model=APIResponse[CaseResponse],
    summary="Update case status or attributes",
    description="Update status, scenario_id, or augmentation settings for a case.",
)
def update_case_endpoint(id: int, update: CaseUpdate, db: Session = Depends(get_db)):
    result = CaseService.update_case(db, case_id=id, update_in=update)
    return APIResponse(success=True, data=CaseResponse.model_validate(result))


@router.put(
    "/{id}/scenario",
    response_model=APIResponse[CaseResponse],
    summary="Update case scenario",
    description="Assigns a scenario to an existing case.",
)
def update_case_scenario(id: int, update: CaseUpdate, db: Session = Depends(get_db)):
    result = CaseService.update_case(db, case_id=id, update_in=update)
    return APIResponse(success=True, data=CaseResponse.model_validate(result))


@router.delete(
    "/{id}",
    response_model=APIResponse[CaseResponse],
    summary="Delete a case by ID",
    description="Remove a case and return the deleted object.",
)
def delete_case(id: int, db: Session = Depends(get_db)):
    result = CaseService.delete_case(db, case_id=id)
    return APIResponse(success=True, data=result)
