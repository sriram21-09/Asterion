"""
Scientific Pipeline Module
============================

Orchestrator and solvers for the localization estimation pipeline.

Exports:
    solve_weighted_centroid: Signal-strength-weighted centroid fallback.
    solve_multilateration: NLLS multilateration using scipy.
"""

from scientific.pipeline.multilateration import solve_multilateration
from scientific.pipeline.weighted_centroid import solve_weighted_centroid

__all__ = [
    "solve_weighted_centroid",
    "solve_multilateration",
]
