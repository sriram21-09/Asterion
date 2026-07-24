"""
Localization Router
=====================

Provides the endpoint for running the multilateration localization pipeline
against stored measurements for a case.

Endpoints:
  - ``POST /localization/run`` — run localization and return computed coordinates
"""

from app.database.session import get_db
from app.schemas.localization import LocalizationRunResponse
from app.schemas.response import APIResponse
from app.services.localization_service import LocalizationService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/localization", tags=["localization"])


@router.post(
    "/run",
    response_model=APIResponse[LocalizationRunResponse],
    status_code=status.HTTP_200_OK,
    summary="Run localization on a case",
    description=(
        "Execute the NLLS multilateration solver against stored measurements "
        "for the given case. Returns computed coordinates, signal count, "
        "error metrics, and execution time."
    ),
    responses={
        400: {
            "model": APIResponse,
            "description": "Insufficient signal measurements (minimum 3 distinct towers required) to perform multilateration",
        },
        404: {"model": APIResponse, "description": "Case or measurements not found"},
        422: {
            "model": APIResponse,
            "description": "Validation error in query parameters",
        },
    },
)
def run_localization(
    case_code: str = Query(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    ),
    db: Session = Depends(get_db),
):
    result = LocalizationService.run_localization(db=db, case_code=case_code)

    response_data = LocalizationRunResponse(
        case_code=case_code.upper(),
        scenario_code=result.scenario_id if result.scenario_id else None,
        algorithm=result.algorithm,
        estimated_latitude=result.estimated_latitude,
        estimated_longitude=result.estimated_longitude,
        error_m=result.error_m,
        signals_used=result.signals_used,
        computation_time_ms=result.computation_time_ms,
        timestamp=result.timestamp,
    )

    return APIResponse(success=True, data=response_data)
