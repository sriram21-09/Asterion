"""Global Search API router.

GET /api/v1/search?q=... — unified search across CDR records, towers, and cases.
"""

from app.database.session import get_db
from app.schemas.response import APIResponse
from app.schemas.search import PaginatedSearchResponse
from app.services.search_service import SearchService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/search", tags=["Global Search"])


@router.get(
    "",
    response_model=APIResponse[PaginatedSearchResponse],
    summary="Global Search",
    description=(
        "Search across CDR records (IMEI, IMSI, MSISDN, Cell ID), "
        "towers (Tower ID/CGI), and cases (title, description). "
        "Results include a type discriminator field for each match."
    ),
)
def global_search(
    q: str = Query(
        ...,
        min_length=1,
        description="Search query string (IMEI, IMSI, MSISDN, Cell ID, Tower ID, or case keyword)",
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """Perform a global search across all entity types.

    Returns matching CDR records, towers, and cases with pagination support.
    Empty or whitespace-only queries return HTTP 400.
    """
    # Strip and validate query
    query = q.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must not be empty or whitespace-only.",
        )

    result = SearchService.search(db, query=query, limit=limit, offset=offset)
    return APIResponse(success=True, data=result)
