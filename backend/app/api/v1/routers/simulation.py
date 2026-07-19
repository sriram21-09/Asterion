from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.schemas.measurement import MeasurementResponse
from app.services.measurement_service import MeasurementService
from app.shared.validation import encode_case_code, encode_scenario_code
from scientific.models.scenario_config import SimulationParameters

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post(
    "/generate",
    response_model=APIResponse[List[MeasurementResponse]],
    status_code=status.HTTP_200_OK,
    summary="Generate simulation measurements",
    description="Generate synthetic signal strength measurements for a case's scenario using the simulation engine.",
    responses={
        400: {
            "model": APIResponse,
            "description": "Case does not have an associated scenario, or simulation parameters are invalid",
        },
        404: {"model": APIResponse, "description": "Case not found"},
        422: {
            "model": APIResponse,
            "description": "Validation error in query parameters or payload",
        },
    },
)
def generate_simulation(
    params: SimulationParameters,
    case_code: str = Query(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    ),
    db: Session = Depends(get_db),
):
    saved_measurements = MeasurementService.generate_measurements(
        db=db,
        case_code=case_code,
        params=params,
    )

    # Translate ORM models to response models with human-readable code IDs
    data = []
    for m in saved_measurements:
        data.append(
            MeasurementResponse(
                measurement_code=m.measurement_code,
                case_code=encode_case_code(m.case_id),
                scenario_code=(
                    encode_scenario_code(m.scenario_id) if m.scenario_id else None
                ),
                timestamp=m.timestamp,
                rssi_dbm=m.rssi_dbm,
                latitude=m.latitude,
                longitude=m.longitude,
                timing_advance=m.timing_advance,
                uncertainty_m=m.uncertainty_m,
            )
        )

    return APIResponse(success=True, data=data)


@router.get(
    "/measurements",
    response_model=APIResponse[List[MeasurementResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get measurements for a case",
    description="Retrieve stored measurements for the given case.",
    responses={
        404: {"model": APIResponse, "description": "Case not found"},
        422: {
            "model": APIResponse,
            "description": "Validation error in query parameters",
        },
    },
)
def get_measurements(
    case_code: str = Query(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    ),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException
    from app.shared.validation import decode_case_code
    from app.repositories.measurement_repository import MeasurementRepository
    from app.repositories.case_repository import CaseRepository

    case_id = decode_case_code(case_code)
    case = CaseRepository.get(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    measurements = MeasurementRepository.get_by_case(db, case_id)

    data = []
    for m in measurements:
        data.append(
            MeasurementResponse(
                measurement_code=m.measurement_code,
                case_code=encode_case_code(m.case_id),
                scenario_code=(
                    encode_scenario_code(m.scenario_id) if m.scenario_id else None
                ),
                timestamp=m.timestamp,
                rssi_dbm=m.rssi_dbm,
                latitude=m.latitude,
                longitude=m.longitude,
                timing_advance=m.timing_advance,
                uncertainty_m=m.uncertainty_m,
            )
        )

    return APIResponse(success=True, data=data)
