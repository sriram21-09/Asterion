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
)
from scientific.pipeline.multilateration import solve_multilateration
from scientific.pipeline.runner import run_pipeline
from scientific.pipeline.weighted_centroid import solve_weighted_centroid

__all__ = [
    "CGIResolver",
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
    "detect_handover",
    "flag_impossible_velocity",
    "normalize_densities",
    "parse_cgi",
    "reconstruct_movement_events",
    "run_pipeline",
    "solve_multilateration",
    "solve_weighted_centroid",
    "synthesize_evidence",
    "track_positions",
]
