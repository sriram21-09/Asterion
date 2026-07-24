"""
Movement Router
===============

Provides the API endpoint for reconstructing chronological movement event sequences
and handover event classifications from CDR records and tracking data for a case.

Endpoints:
  - ``POST /movement/reconstruct`` — reconstruct movement path and handover events
"""

<<<<<<< HEAD
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.schemas.movement import MovementReconstructionResponse, MovementEventResponse
from app.services.movement_service import MovementReconstructionService

=======
from app.database.session import get_db
from app.schemas.movement import MovementEventResponse, MovementReconstructionResponse
from app.schemas.response import APIResponse
from app.services.movement_service import MovementReconstructionService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
router = APIRouter(prefix="/movement", tags=["movement"])


@router.post(
    "/reconstruct",
    response_model=APIResponse[MovementReconstructionResponse],
    status_code=status.HTTP_200_OK,
    summary="Reconstruct movement path for a case",
    description=(
        "Generate a chronological sequence of movement events from CDR records "
        "and Kalman-smoothed tracking data for the given case code. Classifies "
        "cell tower handover events and computes distance, velocity, heading, and dwell time."
    ),
    responses={
        400: {
            "model": APIResponse,
            "description": "No CDR records or tracking results found for the case",
        },
        404: {
            "model": APIResponse,
            "description": "Case not found",
        },
        422: {
            "model": APIResponse,
            "description": "Validation error in query parameters",
        },
    },
)
def reconstruct_movement(
    case_code: str = Query(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    ),
    db: Session = Depends(get_db),
):
<<<<<<< HEAD
    result = MovementReconstructionService.reconstruct_movements(db=db, case_code=case_code)
=======
    result = MovementReconstructionService.reconstruct_movements(
        db=db, case_code=case_code
    )
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468

    events_list = [
        MovementEventResponse(
            sequence_number=evt["sequence_number"],
            event_type=evt["event_type"],
            timestamp=evt["timestamp"],
            latitude=evt["latitude"],
            longitude=evt["longitude"],
            from_cgi=evt["from_cgi"],
            to_cgi=evt["to_cgi"],
            speed_kmh=evt["speed_kmh"],
            heading_deg=evt["heading_deg"],
            distance_from_prev_m=evt["distance_from_prev_m"],
            dwell_time_seconds=evt["dwell_time_seconds"],
            confidence=evt["confidence"],
        )
        for evt in result["events"]
    ]

    response_data = MovementReconstructionResponse(
        case_code=result["case_code"],
        total_events=result["total_events"],
        events=events_list,
        handover_count=result["handover_count"],
        total_distance_km=result["total_distance_km"],
        time_span_hours=result["time_span_hours"],
        computation_time_ms=result["computation_time_ms"],
    )

    return APIResponse(success=True, data=response_data)
