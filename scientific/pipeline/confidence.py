"""
Confidence Estimation Engine
============================

Computes Dilution of Precision (GDOP) and error ellipse parameters
(semi-major, semi-minor, and orientation) from tower geometries and
measurement covariance.
"""

import math

import numpy as np

from scientific.config import DEFAULT_VALIDATION_THRESHOLDS, ValidationThresholds
from scientific.constants import METERS_PER_DEGREE_LAT
from scientific.models.measurement import Measurement
from scientific.models.result import ConfidenceResult
from scientific.models.tower import Tower


def compute_confidence(
    scenario_id: str,
    estimated_latitude: float,
    estimated_longitude: float,
    towers: list[Tower],
    measurements: list[Measurement],
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> ConfidenceResult:
    """Calculate the confidence score, level, and error ellipse parameters for an estimate.

    Args:
        scenario_id: Identifier of the source scenario.
        estimated_latitude: Estimated latitude of the device (WGS84).
        estimated_longitude: Estimated longitude of the device (WGS84).
        towers: List of tower configurations in the scenario.
        measurements: List of signal measurements.
        thresholds: Validation thresholds for mapping GDOP to confidence levels.

    Returns:
        A ConfidenceResult containing GDOP, error ellipse details, and confidence levels.
    """
    # 1. Filter to active towers that have measurements associated with them
    used_tower_ids = {m.tower_id for m in measurements if m.tower_id}
    tower_map = {t.tower_id: t for t in towers}
    active_towers = [tower_map[tid] for tid in used_tower_ids if tid in tower_map]

    # Handle insufficient towers (need at least 2 towers for a 2D position estimation geometry)
    if len(active_towers) < 2:
        return ConfidenceResult(
            scenario_id=scenario_id,
            confidence_score=0.0,
            confidence_level="low",
            error_ellipse_semi_major_m=None,
            error_ellipse_semi_minor_m=None,
            error_ellipse_orientation_deg=None,
            gdop=None,
            method="gdop",
        )

    # 2. Project tower coordinates relative to the estimated position
    # Origin (0,0) is at (estimated_longitude, estimated_latitude)
    lat_ref_rad = math.radians(estimated_latitude)
    meters_per_deg_lat = METERS_PER_DEGREE_LAT
    meters_per_deg_lon = METERS_PER_DEGREE_LAT * math.cos(lat_ref_rad)

    tower_xs = []
    tower_ys = []
    distances = []

    for tower in active_towers:
        dx_m = (tower.longitude - estimated_longitude) * meters_per_deg_lon
        dy_m = (tower.latitude - estimated_latitude) * meters_per_deg_lat
        dist = math.sqrt(dx_m**2 + dy_m**2)

        tower_xs.append(dx_m)
        tower_ys.append(dy_m)
        distances.append(dist)

    # 3. Build the geometry matrix H
    # Each row is a unit vector from the estimated position to the tower
    H = np.zeros((len(active_towers), 2))
    for i, (x_i, y_i, d_i) in enumerate(zip(tower_xs, tower_ys, distances)):
        # Clamp distance to avoid division by zero
        ref_d = max(d_i, 1e-9)
        H[i, 0] = x_i / ref_d
        H[i, 1] = y_i / ref_d

    # Compute H^T * H
    H_T_H = H.T @ H

    # Check determinant for near-singular layouts
    det = H_T_H[0, 0] * H_T_H[1, 1] - H_T_H[0, 1] * H_T_H[1, 0]

    if abs(det) < 1e-6:
        # Near-singular geometry (e.g. collinear towers)
        return ConfidenceResult(
            scenario_id=scenario_id,
            confidence_score=0.0,
            confidence_level="low",
            error_ellipse_semi_major_m=None,
            error_ellipse_semi_minor_m=None,
            error_ellipse_orientation_deg=None,
            gdop=None,
            method="gdop",
        )

    # Invert H^T * H to obtain the geometric covariance factor matrix
    try:
        C = np.linalg.inv(H_T_H)
    except np.linalg.LinAlgError:
        C = np.linalg.pinv(H_T_H)

    # 4. Compute GDOP
    # GDOP = sqrt(trace(C))
    trace_val = C[0, 0] + C[1, 1]
    gdop = math.sqrt(max(0.0, trace_val))

    # Clamp GDOP to avoid infinity
    if math.isnan(gdop) or math.isinf(gdop):
        return ConfidenceResult(
            scenario_id=scenario_id,
            confidence_score=0.0,
            confidence_level="low",
            error_ellipse_semi_major_m=None,
            error_ellipse_semi_minor_m=None,
            error_ellipse_orientation_deg=None,
            gdop=None,
            method="gdop",
        )

    # Map GDOP to confidence score (continuous score between 0.0 and 1.0)
    # Using an exponential decay mapping starting from GDOP = 1.0
    confidence_score = math.exp(-0.15 * (gdop - 1.0))
    confidence_score = max(0.0, min(1.0, confidence_score))

    # Map GDOP to confidence level based on ValidationThresholds
    if gdop <= thresholds.gdop_excellent:
        confidence_level = "high"
    elif gdop <= thresholds.gdop_good:
        confidence_level = "medium"
    else:
        confidence_level = "low"

    # 5. Compute Error Ellipse Parameters
    # Get range measurement standard deviation (sigma) from measurements' uncertainty_m
    valid_uncertainties = [
        m.uncertainty_m
        for m in measurements
        if m.uncertainty_m is not None and m.uncertainty_m > 0
    ]
    if valid_uncertainties:
        sigma = sum(valid_uncertainties) / len(valid_uncertainties)
    else:
        sigma = 50.0  # Default fallback range error standard deviation in meters

    # Covariance matrix of position error: Sigma = sigma^2 * C
    Sigma = (sigma**2) * C

    # Compute eigenvalues of Sigma to get semi-major and semi-minor axes
    # For 2x2 matrix: [[a, b], [b, c]], eigenvalues are (a+c +/- sqrt((a-c)^2 + 4b^2)) / 2
    a, b = Sigma[0, 0], Sigma[0, 1]
    c = Sigma[1, 1]

    discriminant = math.sqrt((a - c) ** 2 + 4 * b**2)
    lambda_1 = (a + c + discriminant) / 2.0
    lambda_2 = (a + c - discriminant) / 2.0

    # Ensure non-negative values for square roots
    semi_major = math.sqrt(max(0.0, lambda_1))
    semi_minor = math.sqrt(max(0.0, lambda_2))

    # Compute orientation angle (degrees clockwise from North)
    # Angle relative to East (Cartesian x-axis):
    # phi = 0.5 * atan2(2 * Sigma_xy, Sigma_xx - Sigma_yy)
    phi = 0.5 * math.atan2(2 * b, a - c)

    # Convert Cartesian angle (East is 0, North is 90) to Clockwise from North (North is 0, East is 90):
    # theta = 90 - degrees(phi)
    orientation = (90.0 - math.degrees(phi)) % 360.0

    return ConfidenceResult(
        scenario_id=scenario_id,
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        error_ellipse_semi_major_m=semi_major,
        error_ellipse_semi_minor_m=semi_minor,
        error_ellipse_orientation_deg=orientation,
        gdop=gdop,
        method="gdop",
    )
