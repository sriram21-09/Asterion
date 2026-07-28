from app.core.config import settings
from app.database.session import get_db
from app.schemas.dashboard import DashboardSummary
from app.schemas.response import APIResponse
from app.services.dashboard_service import DashboardService
from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/health",
    summary="Dashboard router health check",
    description="Returns the health status of the dashboard component.",
)
def health_check():
    return {
        "status": "healthy",
        "service": "dashboard-api",
        "version": settings.app_version,
    }


@router.get(
    "/{case_id}/summary",
    response_model=APIResponse[DashboardSummary],
    summary="Retrieve case dashboard summary aggregations",
    description="Returns case-wide summary aggregations including CDR record counts, tower stats, movement metrics, localization, confidence, and pipeline health status.",
)
def get_case_summary(case_id: int, db: Session = Depends(get_db)):
    result = DashboardService.get_case_summary(db, case_id=case_id)
    return APIResponse(success=True, data=result)


@router.get(
    "/{case_id}/heatmap",
    response_model=APIResponse[dict[str, Any]],
    summary="Retrieve heatmap data for a case",
    description="Returns GeoJSON-compatible heatmap data points based on movement events, taking configurable weights for density, dwell time, confidence, and transitions.",
)
def get_heatmap(
    case_id: int,
    w1: float | None = Query(None, description="Weight for Density"),
    w2: float | None = Query(None, description="Weight for Dwell Time"),
    w3: float | None = Query(None, description="Weight for Confidence"),
    w4: float | None = Query(None, description="Weight for Transitions"),
    db: Session = Depends(get_db)
):
    result = DashboardService.get_heatmap(db, case_id=case_id, w1=w1, w2=w2, w3=w3, w4=w4)
    return APIResponse(success=True, data=result)
