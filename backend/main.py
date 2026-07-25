import sys
from pathlib import Path

# Ensure root and backend directories are in sys.path for local and nested imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.api.v1.routers.cases import router as cases_router
from app.api.v1.routers.cdr_import import router as import_router
from app.api.v1.routers.confidence import router as confidence_router
from app.api.v1.routers.dashboard import router as dashboard_router
from app.api.v1.routers.evidence import router as evidence_router
from app.api.v1.routers.localization import router as localization_router
from app.api.v1.routers.measurements import router as measurements_router
from app.api.v1.routers.movement import router as movement_router
from app.api.v1.routers.scenarios import router as scenarios_router
from app.api.v1.routers.simulation import router as simulation_router
from app.api.v1.routers.towers import router as towers_router
from app.api.v1.routers.tracking import router as tracking_router
from app.core.config import settings
from app.exceptions.handlers import register_exception_handlers
from app.middleware.logging import LoggingMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.app_name,
    description="Explainable Telecom Localization & Investigation Support Platform Backend",
    version=settings.app_version,
    debug=settings.debug,
)

# Register logging/timing middleware
app.add_middleware(LoggingMiddleware)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global exception handlers
register_exception_handlers(app)

app.include_router(scenarios_router, prefix=settings.api_prefix)
app.include_router(cases_router, prefix=settings.api_prefix)
app.include_router(simulation_router, prefix=settings.api_prefix)
app.include_router(measurements_router, prefix=settings.api_prefix)
app.include_router(localization_router, prefix=settings.api_prefix)
app.include_router(tracking_router, prefix=settings.api_prefix)
app.include_router(confidence_router, prefix=settings.api_prefix)
app.include_router(evidence_router, prefix=settings.api_prefix)
app.include_router(import_router, prefix=settings.api_prefix)
app.include_router(towers_router, prefix=settings.api_prefix)
app.include_router(movement_router, prefix=settings.api_prefix)
app.include_router(dashboard_router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.get(f"{settings.api_prefix}/health")
async def health():
    return {
        "status": "healthy",
        "service": "asterion-api",
        "version": settings.app_version,
    }
