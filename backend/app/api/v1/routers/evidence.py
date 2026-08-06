"""
Evidence Router
================

Provides endpoints for retrieving evidence audit packets and reproducibility reports for a case.

Endpoints:
  - ``GET /evidence/{case_id}`` — get evidence audit packet with reproducibility hash
  - ``GET /evidence/{case_id}/audit`` — get detailed audit trail report
"""

from app.database.session import get_db
from app.schemas.evidence import (
    EvidenceAuditResponse,
    EvidenceConfidence,
    EvidenceRejection,
    EvidenceRejectionError,
    EvidenceResponse,
    EvidenceSummary,
    EvidenceTower,
)
from app.schemas.response import APIResponse
from app.services.evidence_service import EvidenceGenerationService
from app.shared.validation import ValidationError
from fastapi import APIRouter, Depends, Path, status, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/evidence", tags=["evidence"])


def _parse_rejections(rejections_raw: list[dict]) -> list[EvidenceRejection]:
    rejections = []
    for r in rejections_raw:
        errors = [EvidenceRejectionError(**e) for e in r.get("errors", [])]
        rejections.append(
            EvidenceRejection(
                measurement_id=r.get("measurement_id"),
                tower_id=r.get("tower_id"),
                timestamp=r.get("timestamp"),
                errors=errors,
            )
        )
    return rejections


@router.get(
    "/{case_id}",
    response_model=APIResponse[EvidenceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get evidence audit packet for a case",
    description=(
        "Retrieve a structured audit evidence packet for the given case ID or case code. "
        "The packet includes measurement validation results, tower usage statistics, "
        "rejection details, confidence data, and a SHA-256 reproducibility hash."
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
    case_id: str = Path(
        ...,
        description="The Case ID or Case Code (e.g. 1 or CASE-001)",
        examples=["CASE-001"],
    ),
    db: Session = Depends(get_db),
):
    try:
        result = EvidenceGenerationService.get_evidence(db=db, case_id=case_id)
    except ValidationError as e:
        raise HTTPException(
            status_code=getattr(e, "status_code", 400), detail=e.message
        )

    summary = EvidenceSummary(**result["summary"])
    towers = [EvidenceTower(**t) for t in result["towers"]]
    rejections = _parse_rejections(result["rejections"])

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
        reproducibility_hash=result.get("reproducibility_hash"),
    )

    return APIResponse(success=True, data=response_data)


@router.get(
    "/{case_id}/audit",
    response_model=APIResponse[EvidenceAuditResponse],
    status_code=status.HTTP_200_OK,
    summary="Get evidence audit report with reproducibility hash for a case",
    description=(
        "Retrieve a detailed evidence audit report for the given case ID or case code. "
        "Includes SHA-256 reproducibility hash, solver version, input record IDs, "
        "parameter string, and full validation breakdown."
    ),
    responses={
        400: {
            "model": APIResponse,
            "description": "Invalid case or measurement state for audit generation",
        },
        404: {"model": APIResponse, "description": "Case or measurements not found"},
        422: {
            "model": APIResponse,
            "description": "Validation error in path parameters",
        },
    },
)
def get_evidence_audit(
    case_id: str = Path(
        ...,
        description="The Case ID or Case Code (e.g. 1 or CASE-001)",
        examples=["CASE-001"],
    ),
    db: Session = Depends(get_db),
):
    try:
        result = EvidenceGenerationService.get_audit(db=db, case_id=case_id)
    except ValidationError as e:
        raise HTTPException(
            status_code=getattr(e, "status_code", 400), detail=e.message
        )

    summary = EvidenceSummary(**result["summary"])
    towers = [EvidenceTower(**t) for t in result["towers"]]
    rejections = _parse_rejections(result["rejections"])

    confidence = None
    if result.get("confidence"):
        confidence = EvidenceConfidence(**result["confidence"])

    response_data = EvidenceAuditResponse(
        case_code=result["case_code"],
        reproducibility_hash=result["reproducibility_hash"],
        solver_version=result["solver_version"],
        input_record_ids=result["input_record_ids"],
        parameter_strings=result["parameter_strings"],
        summary=summary,
        towers=towers,
        rejections=rejections,
        confidence=confidence,
        audit_status=result.get("audit_status", "VERIFIED"),
        generated_at=result["generated_at"],
    )

    return APIResponse(success=True, data=response_data)
