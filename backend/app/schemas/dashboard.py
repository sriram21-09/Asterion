from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CaseSummaryInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    status: str
    scenario_id: int | None = None
    created_at: datetime
    updated_at: datetime


class CDRSummary(BaseModel):
    total_records: int = 0
    total_measurements: int = 0
    operator_breakdown: dict[str, int] = Field(default_factory=dict)
    call_type_breakdown: dict[str, int] = Field(default_factory=dict)
    earliest_timestamp: datetime | None = None
    latest_timestamp: datetime | None = None
    target_numbers: list[str] = Field(default_factory=list)
    imeis: list[str] = Field(default_factory=list)
    imsis: list[str] = Field(default_factory=list)


class TowerSummary(BaseModel):
    total_towers: int = 0
    known_coords_count: int = 0
    estimated_coords_count: int = 0
    unknown_coords_count: int = 0


class MovementSummary(BaseModel):
    total_events: int = 0
    handover_events: int = 0
    total_distance_km: float = 0.0
    max_speed_kmh: float = 0.0
    avg_speed_kmh: float = 0.0


class LatestLocalization(BaseModel):
    id: int
    algorithm: str
    estimated_latitude: float
    estimated_longitude: float
    error_m: float | None = None
    computation_time_ms: float | None = None
    signals_used: int


class LocalizationSummary(BaseModel):
    total_results: int = 0
    latest_result: LatestLocalization | None = None


class LatestTrackingStep(BaseModel):
    step_number: int
    smoothed_latitude: float
    smoothed_longitude: float
    velocity_mps: float | None = None
    heading_deg: float | None = None
    algorithm: str
    timestamp: datetime | None = None


class TrackingSummary(BaseModel):
    total_steps: int = 0
    latest_step: LatestTrackingStep | None = None


class LatestConfidence(BaseModel):
    confidence_score: float
    confidence_level: str
    gdop: float | None = None
    method: str


class ConfidenceSummary(BaseModel):
    latest_result: LatestConfidence | None = None


class PipelineHealthStatus(BaseModel):
    imported: bool = False
    validated: bool = False
    towers_resolved: bool = False
    movement_reconstructed: bool = False
    localization_complete: bool = False
    confidence_generated: bool = False
    evidence_logged: bool = False
    report_ready: bool = False


class DashboardSummary(BaseModel):
    case: CaseSummaryInfo
    cdr: CDRSummary
    towers: TowerSummary
    movement: MovementSummary
    localization: LocalizationSummary
    tracking: TrackingSummary
    confidence: ConfidenceSummary
    pipeline_status: PipelineHealthStatus
