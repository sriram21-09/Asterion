"""
Measurements Router
=====================

Provides endpoints for measurement-level operations that are independent
of the simulation generation flow (which lives in ``simulation.py``).

Current endpoints:
  - ``POST /measurements/validate`` — batch-validate a list of measurements
    against domain business rules and return structured results.
"""

from app.schemas.response import APIResponse, ErrorDetail
from app.schemas.validation import (
    ValidateMeasurementsRequest,
    ValidateMeasurementsResponse,
)
from app.services.validation_service import validate_measurements_batch
from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.post(
    "/validate",
    response_model=APIResponse[ValidateMeasurementsResponse],
    status_code=status.HTTP_200_OK,
    summary="Validate measurement data",
    description=(
        "Validate a batch of measurements against domain business rules "
        "(RSSI range, coordinate bounds, timestamp plausibility, etc.) "
        "and return structured validation results with per-field errors."
    ),
    responses={
        422: {
            "model": APIResponse[ValidateMeasurementsResponse],
            "description": "Validation failed: some measurements were rejected due to data anomalies",
        },
    },
)
def validate_measurements(payload: ValidateMeasurementsRequest):
    result = validate_measurements_batch(payload.measurements)
    if not result.is_valid:
        response_body = APIResponse(
            success=False,
            data=result,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=f"Validation failed: {result.rejected_count} measurements rejected.",
            ),
            detail=f"Validation failed: {result.rejected_count} measurements rejected.",
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(response_body),
        )
    return APIResponse(success=True, data=result)
