from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.services.system_service import SystemService

router = APIRouter(prefix="/system", tags=["system"])


@router.post(
    "/database/reset",
    response_model=APIResponse[dict[str, Any]],
    summary="Reset and purge complete database",
    description="Deletes all case records, imported CDRs, measurements, localization results, and evidence while keeping table schemas intact.",
)
def reset_database(db: Session = Depends(get_db)):
    try:
        result = SystemService.reset_database(db)
        return APIResponse(success=True, data=result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post(
    "/database/seed",
    response_model=APIResponse[dict[str, Any]],
    summary="Seed demonstration data",
    description="Seeds default scenarios, cases, measurements, and movement events into the database for demonstration purposes.",
)
def seed_database(db: Session = Depends(get_db)):
    try:
        result = SystemService.seed_database(db)
        return APIResponse(success=True, data=result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
