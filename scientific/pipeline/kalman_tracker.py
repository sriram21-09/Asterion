"""
2D Constant-Velocity Kalman Filter Tracker
==========================================

Implements a linear Kalman filter for smoothing sequential geodetic coordinates
(latitude and longitude) using a constant-velocity motion model.
"""

import math
import time
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np

from scientific.constants import METERS_PER_DEGREE_LAT, haversine_distance_m
from scientific.logger import get_logger
from scientific.models.result import LocalizationResult

logger = get_logger(__name__)


class KalmanTracker:
    """A linear 2D Kalman Filter tracker for Constant-Velocity state estimation.

    State Vector (x):
        [latitude (deg), longitude (deg), velocity_lat (deg/s), velocity_lon (deg/s)]^T

    Measurement Vector (z):
        [latitude (deg), longitude (deg)]^T
    """

    def __init__(
        self,
        process_noise_acc: float = 0.5,
        default_measurement_noise_m: float = 50.0,
    ):
        """Initialize the Kalman filter tracker.

        Args:
            process_noise_acc: Standard deviation of acceleration process noise (m/s^2).
            default_measurement_noise_m: Fallback measurement noise standard deviation (meters).
        """
        self.process_noise_acc = process_noise_acc
        self.default_measurement_noise_m = default_measurement_noise_m

        self.x: Optional[np.ndarray] = None  # State vector: shape (4,)
        self.P: Optional[np.ndarray] = None  # Covariance matrix: shape (4, 4)

    def initialize(self, lat: float, lon: float, error_m: Optional[float] = None):
        """Initialize the tracker state and covariance.

        Args:
            lat: Starting latitude in degrees.
            lon: Starting longitude in degrees.
            error_m: Initial measurement error in meters.
        """
        lat_ref_rad = math.radians(lat)
        cos_lat = max(1e-2, math.cos(lat_ref_rad))

        # Initial measurement error in degrees
        err_m = max(1.0, error_m if error_m is not None else self.default_measurement_noise_m)
        sig_lat = err_m / METERS_PER_DEGREE_LAT
        sig_lon = err_m / (METERS_PER_DEGREE_LAT * cos_lat)

        # Initial velocity uncertainty (assumed around 10 m/s standard deviation)
        vel_err_m_s = 10.0
        sig_v_lat = vel_err_m_s / METERS_PER_DEGREE_LAT
        sig_v_lon = vel_err_m_s / (METERS_PER_DEGREE_LAT * cos_lat)

        self.x = np.array([lat, lon, 0.0, 0.0], dtype=float)
        self.P = np.diag([
            sig_lat**2,
            sig_lon**2,
            sig_v_lat**2,
            sig_v_lon**2,
        ])

    def predict(self, dt: float):
        """Perform the state and covariance prediction step.

        Args:
            dt: Time delta in seconds.
        """
        if self.x is None or self.P is None:
            raise RuntimeError("Tracker must be initialized before calling predict.")

        if dt <= 0.0:
            return  # No time elapsed, skip prediction

        # 1. State transition matrix (F)
        F = np.array([
            [1.0, 0.0, dt,   0.0],
            [0.0, 1.0, 0.0,  dt],
            [0.0, 0.0, 1.0,  0.0],
            [0.0, 0.0, 0.0,  1.0]
        ], dtype=float)

        # 2. Process noise covariance (Q)
        lat_ref_rad = math.radians(self.x[0])
        cos_lat = max(1e-2, math.cos(lat_ref_rad))

        # Acceleration noise components converted to degrees/sec^2
        q_acc_lat = self.process_noise_acc / METERS_PER_DEGREE_LAT
        q_acc_lon = self.process_noise_acc / (METERS_PER_DEGREE_LAT * cos_lat)

        w_lat = q_acc_lat**2
        w_lon = q_acc_lon**2

        # Discrete process noise covariance formulation for constant acceleration noise
        Q = np.array([
            [(dt**3 / 3.0) * w_lat, 0.0,                   (dt**2 / 2.0) * w_lat, 0.0],
            [0.0,                   (dt**3 / 3.0) * w_lon, 0.0,                   (dt**2 / 2.0) * w_lon],
            [(dt**2 / 2.0) * w_lat, 0.0,                   dt * w_lat,             0.0],
            [0.0,                   (dt**2 / 2.0) * w_lon, 0.0,                   dt * w_lon]
        ], dtype=float)

        # 3. Predict state and covariance
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q

    def update(self, lat: float, lon: float, error_m: Optional[float] = None):
        """Perform the measurement update step.

        Args:
            lat: Measured latitude in degrees.
            lon: Measured longitude in degrees.
            error_m: Measurement error in meters.
        """
        if self.x is None or self.P is None:
            raise RuntimeError("Tracker must be initialized before calling update.")

        # 1. Measurement vector (z)
        z = np.array([lat, lon], dtype=float)

        # 2. Measurement model matrix (H)
        H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ], dtype=float)

        # 3. Measurement noise covariance (R)
        lat_ref_rad = math.radians(self.x[0])
        cos_lat = max(1e-2, math.cos(lat_ref_rad))

        err_m = max(1.0, error_m if error_m is not None else self.default_measurement_noise_m)
        r_lat = err_m / METERS_PER_DEGREE_LAT
        r_lon = err_m / (METERS_PER_DEGREE_LAT * cos_lat)

        R = np.diag([r_lat**2, r_lon**2])

        # 4. Innovation (y) and innovation covariance (S)
        y = z - H @ self.x
        S = H @ self.P @ H.T + R

        # 5. Kalman gain (K)
        K = self.P @ H.T @ np.linalg.inv(S)

        # 6. Update state and covariance (Joseph stabilized form)
        self.x = self.x + K @ y

        I = np.eye(4, dtype=float)
        ImKH = I - K @ H
        self.P = ImKH @ self.P @ ImKH.T + K @ R @ K.T


def track_positions(
    results: List[LocalizationResult],
    expected_device_lat: Optional[float] = None,
    expected_device_lon: Optional[float] = None,
    process_noise_acc: float = 0.5,
    default_measurement_noise_m: float = 50.0,
) -> List[LocalizationResult]:
    """Smooth a sequence of localization results using the Kalman filter.

    Args:
        results: Chronological list of position estimates.
        expected_device_lat: Ground-truth latitude (for error calculation).
        expected_device_lon: Ground-truth longitude (for error calculation).
        process_noise_acc: Acceleration process noise standard deviation (m/s^2).
        default_measurement_noise_m: Fallback measurement noise standard deviation (meters).

    Returns:
        A list of smoothed LocalizationResult objects.
    """
    if not results:
        return []

    # Sort results chronologically by timestamp
    sorted_results = sorted(results, key=lambda r: r.timestamp)

    # Initialize tracker with first result
    first_res = sorted_results[0]
    tracker = KalmanTracker(
        process_noise_acc=process_noise_acc,
        default_measurement_noise_m=default_measurement_noise_m,
    )
    tracker.initialize(
        lat=first_res.estimated_latitude,
        lon=first_res.estimated_longitude,
        error_m=first_res.error_m,
    )

    smoothed_results: List[LocalizationResult] = []

    # Helper to create LocalizationResult
    def make_result(res_obj: LocalizationResult, x_state: np.ndarray, elapsed_ms: float) -> LocalizationResult:
        est_lat = float(x_state[0])
        est_lon = float(x_state[1])

        # Compute error if ground truth is available
        error_m = None
        if expected_device_lat is not None and expected_device_lon is not None:
            error_m = haversine_distance_m(expected_device_lat, expected_device_lon, est_lat, est_lon)

        # Compute velocities in meters per second (mps) for physical interpretation
        lat_rad = math.radians(est_lat)
        cos_lat = max(1e-2, math.cos(lat_rad))
        v_lat_mps = float(x_state[2] * METERS_PER_DEGREE_LAT)
        v_lon_mps = float(x_state[3] * METERS_PER_DEGREE_LAT * cos_lat)

        res = LocalizationResult(
            scenario_id=res_obj.scenario_id,
            algorithm="kalman",
            estimated_latitude=est_lat,
            estimated_longitude=est_lon,
            error_m=error_m,
            computation_time_ms=elapsed_ms,
            signals_used=res_obj.signals_used,
            timestamp=res_obj.timestamp,
        )

        # Attach velocity estimates as extra properties for database storage
        object.__setattr__(res, "velocity_lat", float(x_state[2]))
        object.__setattr__(res, "velocity_lon", float(x_state[3]))
        object.__setattr__(res, "velocity_lat_mps", v_lat_mps)
        object.__setattr__(res, "velocity_lon_mps", v_lon_mps)
        return res

    # The first result doesn't have a previous step to compute dt
    # We record it as a smoothed result with initial velocity zero
    smoothed_results.append(make_result(first_res, tracker.x, 0.0))

    # Process subsequent results
    for i in range(1, len(sorted_results)):
        res = sorted_results[i]
        start_time = time.perf_counter()

        dt = (res.timestamp - sorted_results[i - 1].timestamp).total_seconds()

        # Run Kalman prediction and update step
        tracker.predict(dt)
        tracker.update(lat=res.estimated_latitude, lon=res.estimated_longitude, error_m=res.error_m)

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000.0

        smoothed_results.append(make_result(res, tracker.x, elapsed_ms))

    return smoothed_results
