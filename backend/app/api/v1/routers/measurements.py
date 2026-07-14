"""
Measurements Router
=====================

Provides endpoints for measurement-level operations that are independent
of the simulation generation flow (which lives in ``simulation.py``).

Current endpoints:
  - ``POST /measurements/validate`` — batch-validate a list of measurements
    against domain business rules and return structured results.
"""

from fastapi import APIRouter, status

from app.schemas.response import APIResponse
from app.schemas.validation import (
    ValidateMeasurementsRequest,
    ValidateMeasurementsResponse,
)
from app.services.validation_service import validate_measurements_batch

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
)
def validate_measurements(payload: ValidateMeasurementsRequest):
    result = validate_measurements_batch(payload.measurements)
    return APIResponse(success=True, data=result)
