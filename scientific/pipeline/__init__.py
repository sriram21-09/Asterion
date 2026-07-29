"""
Scientific Pipeline Module
============================

Orchestrator and solvers for the localization estimation pipeline.

Exports:
    solve_weighted_centroid: Signal-strength-weighted centroid fallback.
    solve_multilateration: NLLS multilateration using scipy.
"""

from scientific.pipeline.benchmarks import (
    CGIResolver,
    calculate_grid_density,
    calculate_neighbor_density,
    calculate_radius_density,
    normalize_densities,
    parse_cgi,
)
from scientific.pipeline.case_comparison import (
    CaseComparisonResult,
    CellOverlapMetrics,
    SpatialCentroidComparison,
    SpeedTrendMetrics,
    calculate_cell_overlap,
    calculate_spatial_centroid_comparison,
    calculate_speed_trends,
    compare_cases,
)
from scientific.pipeline.confidence import compute_confidence
from scientific.pipeline.evidence import compute_evidence_hash, synthesize_evidence
from scientific.pipeline.heatmap import (
    HeatmapCellScore,
    HeatmapWeights,
    aggregate_grid_heatmap,
    calculate_cell_score,
    compute_heatmap,
    min_max_normalize,
    normalize_confidence,
    normalize_density,
    normalize_dwell_time,
    normalize_transitions,
)
from scientific.pipeline.kalman_tracker import KalmanTracker, track_positions
from scientific.pipeline.movement import (
    MovementEvent,
    MovementSummary,
    calculate_bearing_deg,
    calculate_distance_m,
    calculate_speed_kmh,
    classify_velocity,
    detect_handover,
    flag_impossible_velocity,
    reconstruct_movement_events,
    smooth_movement_path,
)
from scientific.pipeline.multilateration import solve_multilateration
from scientific.pipeline.runner import run_pipeline
from scientific.pipeline.summary_generator import (
    APPROVED_TERMS,
    PROHIBITED_TERMS,
    InvestigationSummaryGenerator,
    generate_device_overview,
    generate_movement_summary,
    generate_timeline_summary,
    generate_tower_summary,
    validate_neutral_terminology,
)
from scientific.pipeline.weighted_centroid import (
    InputQualityScore,
    compute_input_quality_scores,
    solve_weighted_centroid,
)

__all__ = [
    "APPROVED_TERMS",
    "CGIResolver",
    "CaseComparisonResult",
    "CellOverlapMetrics",
    "HeatmapCellScore",
    "HeatmapWeights",
    "InputQualityScore",
    "InvestigationSummaryGenerator",
    "KalmanTracker",
    "MovementEvent",
    "MovementSummary",
    "PROHIBITED_TERMS",
    "SpatialCentroidComparison",
    "SpeedTrendMetrics",
    "aggregate_grid_heatmap",
    "calculate_bearing_deg",
    "calculate_cell_overlap",
    "calculate_cell_score",
    "calculate_distance_m",
    "calculate_evidence_hash",
    "calculate_grid_density",
    "calculate_neighbor_density",
    "calculate_radius_density",
    "calculate_spatial_centroid_comparison",
    "calculate_speed_kmh",
    "calculate_speed_trends",
    "classify_velocity",
    "compare_cases",
    "compute_confidence",
    "compute_evidence_hash",
    "compute_heatmap",
    "compute_input_quality_scores",
    "detect_handover",
    "flag_impossible_velocity",
    "generate_device_overview",
    "generate_movement_summary",
    "generate_timeline_summary",
    "generate_tower_summary",
    "min_max_normalize",
    "normalize_confidence",
    "normalize_densities",
    "normalize_density",
    "normalize_dwell_time",
    "normalize_transitions",
    "parse_cgi",
    "reconstruct_movement_events",
    "run_pipeline",
    "smooth_movement_path",
    "solve_multilateration",
    "solve_weighted_centroid",
    "synthesize_evidence",
    "track_positions",
    "validate_neutral_terminology",
]
