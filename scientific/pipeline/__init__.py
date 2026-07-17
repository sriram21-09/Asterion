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

__all__ = [
    "solve_weighted_centroid",
    "solve_multilateration",
    "KalmanTracker",
    "track_positions",
    "compute_confidence",
    "synthesize_evidence",
]
