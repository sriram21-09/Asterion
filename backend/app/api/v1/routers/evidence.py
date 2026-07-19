"""
Evidence Router
================

Provides the endpoint for retrieving evidence audit packets for a case.

Endpoints:
  - ``GET /evidence/{case_code}`` — get evidence audit packet
"""

from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.schemas.evidence import (
    EvidenceResponse,
    EvidenceSummary,
    EvidenceTower,
    EvidenceRejection,
    EvidenceRejectionError,
    EvidenceConfidence,
)
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get(
    "/{case_code}",
    response_model=APIResponse[EvidenceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get evidence audit packet for a case",
    description=(
        "Retrieve a structured audit evidence packet for the given case. "
        "The packet includes measurement validation results, tower usage "
        "statistics, rejection details, and optionally confidence data."
    ),
    responses={
        400: {
            "model": APIResponse,
            "description": "Insufficient signal measurements to synthesize an evidence packet",
        },
        404: {"model": APIResponse, "description": "Case or measurements not found"},
        422: {
            "model": APIResponse,
            "description": "Validation error in path parameters",
        },
    },
)
def get_evidence(
    case_code: str = Path(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    ),
    db: Session = Depends(get_db),
):
    result = EvidenceService.get_evidence(db=db, case_code=case_code)

    # Convert nested dicts → Pydantic models
    summary = EvidenceSummary(**result["summary"])

    towers = [EvidenceTower(**t) for t in result["towers"]]

    rejections = []
    for r in result["rejections"]:
        errors = [EvidenceRejectionError(**e) for e in r.get("errors", [])]
        rejections.append(
            EvidenceRejection(
                measurement_id=r.get("measurement_id"),
                tower_id=r.get("tower_id"),
                timestamp=r.get("timestamp"),
                errors=errors,
            )
        )

    confidence = None
    if result.get("confidence"):
        confidence = EvidenceConfidence(**result["confidence"])

    response_data = EvidenceResponse(
        case_code=result["case_code"],
        scenario_id=result.get("scenario_id"),
        summary=summary,
        towers=towers,
        accepted_measurement_ids=result.get("accepted_measurement_ids", []),
        rejections=rejections,
        confidence=confidence,
    )

    return APIResponse(success=True, data=response_data)
