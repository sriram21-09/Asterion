"""
RSSI Signal Generator
=====================

Simulates received signal strength (RSSI) using a log-distance path-loss model.
"""

from __future__ import annotations

import math
from typing import Optional
from scientific.constants import haversine_distance_m


def calculate_path_loss(
    distance_m: float,
    path_loss_exponent: float,
    reference_loss_db: float,
    reference_distance_m: float = 1.0,
) -> float:
    """Calculate path loss using log-distance model."""
    # ponytail: clamp distance to reference distance to avoid division by zero or negative loss
    effective_dist = max(distance_m, reference_distance_m)
    return reference_loss_db + 10.0 * path_loss_exponent * math.log10(effective_dist / reference_distance_m)


def generate_rssi(
    distance_m: float,
    transmit_power_dbm: float,
    coverage_radius_m: float,
    path_loss_exponent: float,
    reference_loss_db: float,
    reference_distance_m: float = 1.0,
) -> Optional[float]:
    """Generate clean received signal strength (RSSI) in dBm.

    Returns None if the distance exceeds the coverage radius.
    """
    if distance_m > coverage_radius_m:
        return None
    pl = calculate_path_loss(
        distance_m,
        path_loss_exponent,
        reference_loss_db,
        reference_distance_m,
    )
    return transmit_power_dbm - pl
