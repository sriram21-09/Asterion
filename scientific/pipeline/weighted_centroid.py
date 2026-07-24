"""
Weighted Centroid Solver
========================

Implements the signal-strength-weighted centroid algorithm for initial guess
generation and fallback localization.
"""

import time
from datetime import UTC, datetime

from scientific.constants import haversine_distance_m
from scientific.models.measurement import Measurement
from scientific.models.result import LocalizationResult
from scientific.models.tower import Tower


def solve_weighted_centroid(
    scenario_id: str,
    towers: list[Tower],
    measurements: list[Measurement],
    expected_device_lat: float | None = None,
    expected_device_lon: float | None = None,
) -> LocalizationResult:
    """Calculate the estimated position using the signal-strength weighted centroid.

    The weight for each tower is based on the average linear power of its received
    measurements:
        w_i = 10^(rssi_avg_i / 10)

    Args:
        scenario_id: Identifier of the source scenario.
        towers: List of tower configurations.
        measurements: List of signal measurements.
        expected_device_lat: Ground-truth device latitude (for error calculation).
        expected_device_lon: Ground-truth device longitude (for error calculation).

    Returns:
        A LocalizationResult containing the estimated position.
    """
    start_time = time.perf_counter()

    # 1. Group measurements by tower_id and compute average RSSI
    tower_rssis = {}
    for m in measurements:
        tower_rssis.setdefault(m.tower_id, []).append(m.rssi_dbm)

    # Compute average RSSI per unique tower
    avg_tower_rssi = {
        tid: sum(rssi_list) / len(rssi_list) for tid, rssi_list in tower_rssis.items()
    }

    # 2. Map tower ID to tower configurations
    tower_map = {t.tower_id: t for t in towers}

    total_weight = 0.0
    weighted_lat = 0.0
    weighted_lon = 0.0
    signals_used = 0

    for tid, avg_rssi in avg_tower_rssi.items():
        if tid in tower_map:
            tower = tower_map[tid]
            # w_i = 10^(rssi_i / 10.0)
            weight = 10.0 ** (avg_rssi / 10.0)
            weighted_lat += weight * tower.latitude
            weighted_lon += weight * tower.longitude
            total_weight += weight
            signals_used += 1

    # 3. Compute estimated coordinates
    if total_weight == 0.0:
        # Fallback to simple unweighted centroid of towers if no weights/measurements
        if towers:
            est_lat = sum(t.latitude for t in towers) / len(towers)
            est_lon = sum(t.longitude for t in towers) / len(towers)
        else:
            raise ValueError("No towers available to compute weighted centroid.")
    else:
        est_lat = weighted_lat / total_weight
        est_lon = weighted_lon / total_weight

    end_time = time.perf_counter()
    computation_time_ms = (end_time - start_time) * 1000.0

    # 4. Compute error if ground truth is provided
    error_m = None
    if expected_device_lat is not None and expected_device_lon is not None:
        error_m = haversine_distance_m(
            expected_device_lat, expected_device_lon, est_lat, est_lon
        )

    return LocalizationResult(
        scenario_id=scenario_id,
        algorithm="weighted_centroid",
        estimated_latitude=est_lat,
        estimated_longitude=est_lon,
        error_m=error_m,
        computation_time_ms=computation_time_ms,
        signals_used=max(1, signals_used),
        timestamp=datetime.now(UTC),
    )
