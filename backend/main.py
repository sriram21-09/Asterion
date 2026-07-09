from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from app.api.v1.routers.scenarios import router as scenarios_router
from app.api.v1.routers.cases import router as cases_router
from app.exceptions.handlers import register_exception_handlers
from app.middleware.logging import LoggingMiddleware

app = FastAPI(
    title="Asterion API",
    description="Explainable Telecom Localization & Investigation Support Platform Backend",
    version="1.0.0"
)

# Register logging/timing middleware
app.add_middleware(LoggingMiddleware)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global exception handlers
register_exception_handlers(app)

app.include_router(scenarios_router, prefix="/api/v1")
app.include_router(cases_router, prefix="/api/v1")

class TowerSignal(BaseModel):
    tower_id: str
    latitude: float
    longitude: float
    signal_strength_dbm: float
    timestamp: float

class LocalizationRequest(BaseModel):
    signals: List[TowerSignal]
    algorithm: Optional[str] = "multilateration"

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Asterion API",
        "version": "1.0.0"
    }

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "service": "asterion-api",
        "version": "1.0.0"
    }

@app.post("/api/localize")
async def localize_device(payload: LocalizationRequest):
    if len(payload.signals) < 3:
        raise HTTPException(
            status_code=400,
            detail="At least 3 tower signals are required for multilateration."
        )
    # Simple centroid localization fallback for skeleton API
    total_weight = 0.0
    weighted_lat = 0.0
    weighted_lon = 0.0
    
    for signal in payload.signals:
        # Convert dbm to weight (stronger signal = higher weight)
        # Typical range: -110 (weak) to -50 (strong)
        weight = max(1.0, 120.0 + signal.signal_strength_dbm)
        weighted_lat += signal.latitude * weight
        weighted_lon += signal.longitude * weight
        total_weight += weight

    est_lat = weighted_lat / total_weight
    est_lon = weighted_lon / total_weight
    
    return {
        "estimated_latitude": est_lat,
        "estimated_longitude": est_lon,
        "confidence_score": 0.85,
        "signals_used": len(payload.signals),
        "algorithm_applied": payload.algorithm
    }
