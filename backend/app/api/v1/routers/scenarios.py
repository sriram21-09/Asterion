from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.scenario import ScenarioCreate, ScenarioResponse
from app.services.scenario_service import ScenarioService
from typing import List, Optional

router = APIRouter(
    prefix="/scenarios",
    tags=["scenarios"]
)

@router.post(
    "/",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scenario",
    description="Validate inputs and create a new localization scenario."
)
def create_scenario(
    scenario_in: ScenarioCreate,
    db: Session = Depends(get_db)
):
    return ScenarioService.create_scenario(db, scenario_in)

@router.get(
    "/",
    response_model=List[ScenarioResponse],
    summary="Retrieve all scenarios",
    description="Retrieve a paginated list of scenarios."
)
def list_scenarios(
    page: Optional[int] = Query(None, description="Page number starting from 1"),
    page_size: Optional[int] = Query(None, description="Number of items per page"),
    db: Session = Depends(get_db)
):
    return ScenarioService.list_scenarios(db, page=page, page_size=page_size)

@router.get(
    "/{id}",
    response_model=ScenarioResponse,
    summary="Retrieve a scenario by ID",
    description="Get details of a single scenario."
)
def get_scenario(
    id: int,
    db: Session = Depends(get_db)
):
    return ScenarioService.get_scenario(db, scenario_id=id)

@router.delete(
    "/{id}",
    response_model=ScenarioResponse,
    summary="Delete a scenario by ID",
    description="Remove a scenario and return the deleted object."
)
def delete_scenario(
    id: int,
    db: Session = Depends(get_db)
):
    return ScenarioService.delete_scenario(db, scenario_id=id)
