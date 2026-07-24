<<<<<<< HEAD
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.schemas.tower import (
    TowerCreate,
    TowerResponse,
    CGILookupRequest,
    CGILookupResponse,
)
from app.services.tower_service import TowerIntelligenceService
=======
from app.database.session import get_db
from app.schemas.response import APIResponse
from app.schemas.tower import (
    CGILookupRequest,
    CGILookupResponse,
    TowerCreate,
    TowerResponse,
)
from app.services.tower_service import TowerIntelligenceService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468

router = APIRouter(prefix="/towers", tags=["Tower Intelligence"])


@router.post(
    "/lookup",
    response_model=APIResponse[CGILookupResponse],
    summary="Resolve CGI Coordinates",
    description="Query CGI (MCC-MNC-LAC-CI) to resolve spatial coordinates and classify confidence level.",
)
def resolve_cgi_lookup(
    payload: CGILookupRequest,
    db: Session = Depends(get_db),
):
    cgi_str = payload.cgi
    if not cgi_str and (payload.mcc and payload.mnc and payload.lac and payload.ci):
        cgi_str = f"{payload.mcc}-{payload.mnc}-{payload.lac}-{payload.ci}"

    if not cgi_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'cgi' or complete ('mcc', 'mnc', 'lac', 'ci') must be provided.",
        )

    result = TowerIntelligenceService.resolve_cgi(db, cgi_str)
    return APIResponse(success=True, data=result)


@router.get(
    "",
<<<<<<< HEAD
    response_model=APIResponse[List[TowerResponse]],
=======
    response_model=APIResponse[list[TowerResponse]],
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
    summary="List Towers",
    description="Retrieve cell tower records with optional operator and confidence filters.",
)
def list_towers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
<<<<<<< HEAD
    operator: Optional[str] = Query(None, description="Filter by operator name"),
    confidence_category: Optional[str] = Query(
=======
    operator: str | None = Query(None, description="Filter by operator name"),
    confidence_category: str | None = Query(
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
        None, description="Filter by confidence category (Known, Estimated, Unknown)"
    ),
    db: Session = Depends(get_db),
):
    towers = TowerIntelligenceService.get_towers(
        db,
        skip=skip,
        limit=limit,
        operator=operator,
        confidence_category=confidence_category,
    )
    return APIResponse(success=True, data=towers)


@router.post(
    "",
    response_model=APIResponse[TowerResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Cell Tower",
    description="Create a new tower entry. Jio and Vi towers without coordinates are stored with null coordinates and confidence score 0.2.",
)
def register_tower(
    payload: TowerCreate,
    db: Session = Depends(get_db),
):
    db_tower = TowerIntelligenceService.register_tower(db, payload)
    return APIResponse(success=True, data=db_tower)
