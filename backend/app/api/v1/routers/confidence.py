"""
Confidence Router
==================

Provides the endpoint for running confidence analysis on a case.

Endpoints:
  - ``POST /confidence/run`` — run confidence analysis and return GDOP/error ellipse
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.schemas.confidence import ConfidenceRunResponse
from app.services.confidence_service import ConfidenceService

router = APIRouter(prefix="/confidence", tags=["confidence"])


@router.post(
    "/run",
    response_model=APIResponse[ConfidenceRunResponse],
    status_code=status.HTTP_200_OK,
    summary="Run confidence analysis on a case",
    description=(
        "Execute the confidence analysis pipeline using GDOP and error "
        "ellipse computation over stored measurements and localization "
        "results for the given case. Returns confidence score, level, "
        "GDOP, and error ellipse parameters."
    ),
    responses={
        400: {
            "model": APIResponse,
            "description": "Insufficient signal measurements (minimum 3 distinct towers required) to perform confidence analysis",
        },
        404: {"model": APIResponse, "description": "Case or measurements not found"},
        422: {
            "model": APIResponse,
            "description": "Validation error in query parameters",
        },
    },
)
def run_confidence(
    case_code: str = Query(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    ),
    db: Session = Depends(get_db),
):
    result = ConfidenceService.run_confidence(db=db, case_code=case_code)

    response_data = ConfidenceRunResponse(
        case_code=result["case_code"],
        confidence_score=result["confidence_score"],
        confidence_level=result["confidence_level"],
        error_ellipse_semi_major_m=result["error_ellipse_semi_major_m"],
        error_ellipse_semi_minor_m=result["error_ellipse_semi_minor_m"],
        error_ellipse_orientation_deg=result["error_ellipse_orientation_deg"],
        gdop=result["gdop"],
        method=result["method"],
        computation_time_ms=result["computation_time_ms"],
    )

    return APIResponse(success=True, data=response_data)
