from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.scenario import ScenarioCreate, ScenarioResponse
from app.schemas.response import APIResponse
from app.services.scenario_service import ScenarioService
from typing import List, Optional

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post(
    "/",
    response_model=APIResponse[ScenarioResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scenario",
    description="Validate inputs and create a new localization scenario.",
)
def create_scenario(scenario_in: ScenarioCreate, db: Session = Depends(get_db)):
    result = ScenarioService.create_scenario(db, scenario_in)
    return APIResponse(success=True, data=result)


@router.get(
    "/",
    response_model=APIResponse[List[ScenarioResponse]],
    summary="Retrieve all scenarios",
    description="Retrieve a paginated list of scenarios.",
)
def list_scenarios(
    page: Optional[int] = Query(None, description="Page number starting from 1"),
    page_size: Optional[int] = Query(None, description="Number of items per page"),
    db: Session = Depends(get_db),
):
    result = ScenarioService.list_scenarios(db, page=page, page_size=page_size)
    return APIResponse(success=True, data=result)


@router.get(
    "/{id}",
    response_model=APIResponse[ScenarioResponse],
    summary="Retrieve a scenario by ID",
    description="Get details of a single scenario.",
)
def get_scenario(id: int, db: Session = Depends(get_db)):
    result = ScenarioService.get_scenario(db, scenario_id=id)
    return APIResponse(success=True, data=result)


@router.delete(
    "/{id}",
    response_model=APIResponse[ScenarioResponse],
    summary="Delete a scenario by ID",
    description="Remove a scenario and return the deleted object.",
)
def delete_scenario(id: int, db: Session = Depends(get_db)):
    result = ScenarioService.delete_scenario(db, scenario_id=id)
    return APIResponse(success=True, data=result)
