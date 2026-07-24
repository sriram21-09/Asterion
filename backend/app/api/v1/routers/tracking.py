"""
Tracking Router
================

Provides the endpoint for running the Kalman-smoothed tracking pipeline
against stored localization results for a case.

Endpoints:
  - ``POST /tracking/run`` — run tracking and return the smoothed path
"""

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.schemas.tracking import TrackingRunResponse, TrackingStepResponse
from app.services.tracking_service import TrackingService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.post(
    "/run",
    response_model=APIResponse[TrackingRunResponse],
    status_code=status.HTTP_200_OK,
    summary="Run tracking on a case",
    description=(
        "Execute the Kalman-smoothed tracking pipeline over stored "
        "localization results for the given case. Returns the array "
        "of smoothed track coordinates, velocities, headings, and "
        "overall path metrics."
    ),
    responses={
        400: {
            "model": APIResponse,
            "description": "Insufficient localization results (minimum 2 sequential results required) to construct a track",
        },
        404: {
            "model": APIResponse,
            "description": "Case or localization results not found",
        },
        422: {
            "model": APIResponse,
            "description": "Validation error in query parameters",
        },
    },
)
def run_tracking(
    case_code: str = Query(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    ),
    db: Session = Depends(get_db),
):
    result = TrackingService.run_tracking(db=db, case_code=case_code)

    # Convert dict path items into Pydantic models
    path_steps = [
        TrackingStepResponse(
            step_number=step["step_number"],
            latitude=step["latitude"],
            longitude=step["longitude"],
            velocity_kmh=step["velocity_kmh"],
            timestamp=step["timestamp"],
            heading_deg=step["heading_deg"],
        )
        for step in result["path"]
    ]

    response_data = TrackingRunResponse(
        case_code=result["case_code"],
        total_steps=result["total_steps"],
        path=path_steps,
        distance_km=result["distance_km"],
        avg_velocity_kmh=result["avg_velocity_kmh"],
        computation_time_ms=result["computation_time_ms"],
    )

    return APIResponse(success=True, data=response_data)
