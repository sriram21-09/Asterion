"""
Scientific Pipeline Module
============================

Orchestrator and solvers for the localization estimation pipeline.

Exports:
    solve_weighted_centroid: Signal-strength-weighted centroid fallback.
    solve_multilateration: NLLS multilateration using scipy.
"""

from scientific.pipeline.confidence import compute_confidence
from scientific.pipeline.evidence import synthesize_evidence
from scientific.pipeline.kalman_tracker import KalmanTracker, track_positions
from scientific.pipeline.multilateration import solve_multilateration
from scientific.pipeline.weighted_centroid import solve_weighted_centroid
from scientific.pipeline.runner import run_pipeline
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
)

__all__ = [
    "solve_weighted_centroid",
    "solve_multilateration",
    "KalmanTracker",
    "track_positions",
    "compute_confidence",
    "synthesize_evidence",
    "run_pipeline",
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
]
