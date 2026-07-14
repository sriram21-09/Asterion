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
)
def generate_simulation(
    params: SimulationParameters,
    case_code: str = Query(..., description="The unique Case Code (e.g. CASE-001)"),
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
                scenario_code=encode_scenario_code(m.scenario_id) if m.scenario_id else None,
                timestamp=m.timestamp,
                rssi_dbm=m.rssi_dbm,
                latitude=m.latitude,
                longitude=m.longitude,
                timing_advance=m.timing_advance,
                uncertainty_m=m.uncertainty_m,
            )
        )

    return APIResponse(success=True, data=data)
