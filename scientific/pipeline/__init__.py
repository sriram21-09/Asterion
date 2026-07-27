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
from scientific.pipeline.confidence import compute_confidence
from scientific.pipeline.evidence import compute_evidence_hash, synthesize_evidence
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
    "InputQualityScore",
    "InvestigationSummaryGenerator",
    "KalmanTracker",
    "MovementEvent",
    "MovementSummary",
    "PROHIBITED_TERMS",
    "calculate_bearing_deg",
    "calculate_distance_m",
    "calculate_evidence_hash",
    "calculate_grid_density",
    "calculate_neighbor_density",
    "calculate_radius_density",
    "calculate_speed_kmh",
    "classify_velocity",
    "compute_confidence",
    "compute_evidence_hash",
    "compute_input_quality_scores",
    "detect_handover",
    "flag_impossible_velocity",
    "generate_device_overview",
    "generate_movement_summary",
    "generate_timeline_summary",
    "generate_tower_summary",
    "normalize_densities",
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

