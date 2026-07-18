from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class EvidenceSummary(BaseModel):
    """Summary statistics of measurement validation."""

    total_measurements: int
    accepted_measurements: int
    rejected_measurements: int
    towers_total: int
    towers_used_count: int


class EvidenceTower(BaseModel):
    """Per-tower measurement audit detail."""

    tower_id: str
    latitude: float
    longitude: float
    total_measurements: int
    accepted_measurements: int
    rejected_measurements: int
    status: str


class EvidenceRejectionError(BaseModel):
    """A single rejection error detail."""

    field: str
    message: str
    code: str
    severity: str


class EvidenceRejection(BaseModel):
    """Details of a rejected measurement."""

    measurement_id: Optional[str] = None
    tower_id: Optional[str] = None
    timestamp: Optional[str] = None
    errors: List[EvidenceRejectionError] = []


class EvidenceConfidence(BaseModel):
    """Confidence data included in evidence packet."""

    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None
    gdop: Optional[float] = None
    method: Optional[str] = None


class EvidenceResponse(BaseModel):
    """Full evidence audit packet response."""

    model_config = ConfigDict(from_attributes=True)

    case_code: str
    scenario_id: Optional[str] = None
    summary: EvidenceSummary
    towers: List[EvidenceTower]
    accepted_measurement_ids: List[str]
    rejections: List[EvidenceRejection]
    confidence: Optional[EvidenceConfidence] = None
