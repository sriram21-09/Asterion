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
from scientific.pipeline.evidence import synthesize_evidence
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
<<<<<<< HEAD
from scientific.pipeline.benchmarks import (
    parse_cgi,
    CGIResolver,
    calculate_radius_density,
    calculate_neighbor_density,
    calculate_grid_density,
    normalize_densities,
)
from scientific.pipeline.movement import (
    calculate_distance_m,
    calculate_speed_kmh,
    calculate_bearing_deg,
    detect_handover,
    classify_velocity,
    flag_impossible_velocity,
    reconstruct_movement_events,
    MovementEvent,
    MovementSummary,
=======
from scientific.pipeline.weighted_centroid import (
    InputQualityScore,
    compute_input_quality_scores,
    solve_weighted_centroid,
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
)

__all__ = [
    "CGIResolver",
    "InputQualityScore",
    "KalmanTracker",
    "MovementEvent",
    "MovementSummary",
    "calculate_bearing_deg",
    "calculate_distance_m",
    "calculate_grid_density",
    "calculate_neighbor_density",
    "calculate_radius_density",
    "calculate_speed_kmh",
    "classify_velocity",
    "compute_confidence",
    "compute_input_quality_scores",
    "detect_handover",
    "flag_impossible_velocity",
    "normalize_densities",
    "parse_cgi",
    "reconstruct_movement_events",
    "run_pipeline",
<<<<<<< HEAD
    "parse_cgi",
    "CGIResolver",
    "calculate_radius_density",
    "calculate_neighbor_density",
    "calculate_grid_density",
    "normalize_densities",
    "calculate_distance_m",
    "calculate_speed_kmh",
    "calculate_bearing_deg",
    "detect_handover",
    "classify_velocity",
    "flag_impossible_velocity",
    "reconstruct_movement_events",
    "MovementEvent",
    "MovementSummary",
=======
    "smooth_movement_path",
    "solve_multilateration",
    "solve_weighted_centroid",
    "synthesize_evidence",
    "track_positions",
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
]

