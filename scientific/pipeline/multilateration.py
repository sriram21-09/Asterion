"""
Multilateration Solver
======================

Implements the Non-Linear Least Squares (NLLS) multilateration algorithm using
scipy.optimize.least_squares.
"""

import math
import time
from datetime import UTC, datetime

import numpy as np
from scipy.optimize import least_squares

from scientific.constants import METERS_PER_DEGREE_LAT, haversine_distance_m
from scientific.logger import get_logger
from scientific.models.measurement import Measurement
from scientific.models.result import LocalizationResult
from scientific.models.scenario_config import PropagationDefaults, SimulationParameters
from scientific.models.tower import Tower
from scientific.pipeline.weighted_centroid import solve_weighted_centroid

logger = get_logger(__name__)


def solve_multilateration(
    scenario_id: str,
    towers: list[Tower],
    measurements: list[Measurement],
    propagation: PropagationDefaults,
    simulation: SimulationParameters,
    expected_device_lat: float | None = None,
    expected_device_lon: float | None = None,
) -> LocalizationResult:
    """Solve for the device position using Non-Linear Least Squares (NLLS).

    If the number of unique towers with measurements is less than 3, this falls
    back immediately to the weighted centroid solver.

    Args:
        scenario_id: Identifier of the source scenario.
        towers: List of tower configurations.
        measurements: List of signal measurements.
        propagation: Signal propagation defaults.
        simulation: Simulation and solver parameters.
        expected_device_lat: Ground-truth device latitude (for error calculation).
        expected_device_lon: Ground-truth device longitude (for error calculation).

    Returns:
        A LocalizationResult containing the estimated position.
    """
    start_time = time.perf_counter()

    # 1. Group measurements by tower_id and average RSSI
    tower_rssis = {}
    for m in measurements:
        tower_rssis.setdefault(m.tower_id, []).append(m.rssi_dbm)

    avg_tower_rssi = {
        tid: sum(rssi_list) / len(rssi_list) for tid, rssi_list in tower_rssis.items()
    }

    # 2. Map tower ID to tower configurations and filter available towers
    tower_map = {t.tower_id: t for t in towers}
    valid_towers_rssi = {
        tid: rssi for tid, rssi in avg_tower_rssi.items() if tid in tower_map
    }

    # 3. Check minimum towers constraint
    if len(valid_towers_rssi) < 3:
        logger.warning(
            f"Fewer than 3 unique towers with measurements ({len(valid_towers_rssi)}). "
            "Falling back to Weighted Centroid solver."
        )
        return solve_weighted_centroid(
            scenario_id=scenario_id,
            towers=towers,
            measurements=measurements,
            expected_device_lat=expected_device_lat,
            expected_device_lon=expected_device_lon,
        )

    # 4. Compute Weighted Centroid as the initial guess & coordinate reference origin
    wc_result = solve_weighted_centroid(
        scenario_id=scenario_id,
        towers=towers,
        measurements=measurements,
        expected_device_lat=expected_device_lat,
        expected_device_lon=expected_device_lon,
    )
    lat_ref = wc_result.estimated_latitude
    lon_ref = wc_result.estimated_longitude

    # 5. Project geodetic coordinates to local flat Cartesian plane (meters)
    lat_ref_rad = math.radians(lat_ref)
    meters_per_deg_lat = METERS_PER_DEGREE_LAT
    meters_per_deg_lon = METERS_PER_DEGREE_LAT * math.cos(lat_ref_rad)

    # 6. Convert RSSI to estimated distances (meters) using inverse path-loss model
    # d = d0 * 10^((tx_power - RSSI - L0) / (10 * n))
    est_distances = []
    tower_xs = []
    tower_ys = []

    for tid, rssi in valid_towers_rssi.items():
        tower = tower_map[tid]

        # Calculate estimated distance
        numerator = tower.transmit_power_dbm - rssi - propagation.reference_loss_db
        denominator = 10.0 * propagation.path_loss_exponent
        est_dist = propagation.reference_distance_m * (
            10.0 ** (numerator / denominator)
        )
        est_distances.append(est_dist)

        # Calculate Cartesian coordinates (relative to weighted centroid reference)
        x = (tower.longitude - lon_ref) * meters_per_deg_lon
        y = (tower.latitude - lat_ref) * meters_per_deg_lat
        tower_xs.append(x)
        tower_ys.append(y)

    # Convert lists to NumPy arrays
    tower_xs_arr = np.array(tower_xs)
    tower_ys_arr = np.array(tower_ys)
    est_distances_arr = np.array(est_distances)

    # 7. Formulate Least Squares solver
    # Initial guess in Cartesian coordinate system (0, 0)
    x0 = np.array([0.0, 0.0])

    def residuals(coords):
        x, y = coords
        # residual_i = model_distance_i - estimated_distance_i
        # Adding 1e-9 inside sqrt to ensure differentiability at zero
        model_distances = np.sqrt(
            (tower_xs_arr - x) ** 2 + (tower_ys_arr - y) ** 2 + 1e-9
        )
        return model_distances - est_distances_arr

    # Run solver
    try:
        res = least_squares(
            residuals,
            x0,
            method="lm",  # Levenberg-Marquardt optimizer
            max_nfev=simulation.max_iterations,
            xtol=simulation.convergence_threshold_m,
            ftol=1e-8,
        )

        if not res.success:
            logger.warning(
                "Least squares optimization failed to converge. Falling back to Weighted Centroid."
            )
            return wc_result

        # Extract optimal Cartesian coordinates
        x_opt, y_opt = res.x

        # 8. Convert optimized Cartesian coordinates back to geodetic lat/lon
        est_lat = lat_ref + (y_opt / meters_per_deg_lat)
        est_lon = lon_ref + (x_opt / meters_per_deg_lon)

    except Exception as e:
        logger.error(
            f"Error during NLLS multilateration optimization: {e}. Falling back to Weighted Centroid."
        )
        return wc_result

    end_time = time.perf_counter()
    computation_time_ms = (end_time - start_time) * 1000.0

    # Calculate error if ground truth is available
    error_m = None
    if expected_device_lat is not None and expected_device_lon is not None:
        error_m = haversine_distance_m(
            expected_device_lat, expected_device_lon, est_lat, est_lon
        )

    return LocalizationResult(
        scenario_id=scenario_id,
        algorithm="multilateration",
        estimated_latitude=est_lat,
        estimated_longitude=est_lon,
        error_m=error_m,
        computation_time_ms=computation_time_ms,
        signals_used=len(valid_towers_rssi),
        timestamp=datetime.now(UTC),
    )
