from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.benchmark import BenchmarkResponse
from app.services.benchmark_service import BenchmarkService

router = APIRouter(prefix="/validation", tags=["Validation"])


@router.get(
    "/benchmark/{case_id}",
    response_model=BenchmarkResponse,
    summary="Get pipeline validation benchmark metrics",
    description="Calculates and returns benchmark metrics for a specific case.",
)
def get_benchmark(
    case_id: int = Path(..., description="The ID of the case to benchmark"),
    db: Session = Depends(get_db),
):
    """Retrieve benchmark metrics for a given case."""
    return BenchmarkService.calculate_benchmarks(case_id, db)
