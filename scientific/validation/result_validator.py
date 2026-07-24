"""
Result Validator & Cross Validation
===================================
"""

from __future__ import annotations

import math

from scientific.config import DEFAULT_VALIDATION_THRESHOLDS, ValidationThresholds
from scientific.constants import METERS_PER_DEGREE_LAT, haversine_distance_m
from scientific.models.result import ConfidenceResult, LocalizationResult
from scientific.models.scenario import Scenario
from scientific.models.scenario_config import ScenarioConfig
from scientific.validation.types import Severity, ValidationError, ValidationResult


class ResultValidator:
    """Validates a LocalizationResult against a Scenario or ScenarioConfig.

    Checks:
        1. Estimated position must be within scenario operational bounds.
        2. Estimated position is within coverage area of at least one tower (warning if outside all).
    """

    def __init__(
        self, thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS
    ) -> None:
        self.thresholds = thresholds

    def validate(
        self, result: LocalizationResult, scenario: Scenario | ScenarioConfig
    ) -> ValidationResult:
        validation_res = ValidationResult()

        lat = result.estimated_latitude
        lon = result.estimated_longitude

        lat_min, lat_max = self.thresholds.latitude_range
        lon_min, lon_max = self.thresholds.longitude_range

        if not (lat_min <= lat <= lat_max) or not (lon_min <= lon <= lon_max):
            validation_res.errors.append(
                ValidationError(
                    field="estimated_latitude/estimated_longitude",
                    message=f"Estimated coordinates ({lat}, {lon}) are outside operational ranges.",
                    severity=Severity.ERROR,
                    code="RESULT_OUT_OF_BOUNDS",
                )
            )
            return validation_res

        towers = []
        if hasattr(scenario, "towers") and scenario.towers:
            towers = scenario.towers
        elif hasattr(scenario, "tower_placements") and scenario.tower_placements:
            towers = scenario.tower_placements

        if not towers:
            validation_res.errors.append(
                ValidationError(
                    field="scenario.towers",
                    message="Scenario has no towers to validate result bounds against.",
                    severity=Severity.ERROR,
                    code="RESULT_NO_TOWERS",
                )
            )
            return validation_res

        # Compute bounding box of towers
        tower_lats = [t.latitude for t in towers]
        tower_lons = [t.longitude for t in towers]
        min_tower_lat, max_tower_lat = min(tower_lats), max(tower_lats)
        min_tower_lon, max_tower_lon = min(tower_lons), max(tower_lons)
        # Buffer distance in degrees (based on max coverage radius of the towers, or default 5000m)
        max_coverage = max(
            (
                t.coverage_radius_m
                for t in towers
                if getattr(t, "coverage_radius_m", None) is not None
            ),
            default=5000.0,
        )
        buffer_deg_lat = (max_coverage * 1.5) / METERS_PER_DEGREE_LAT
        lat_rad = math.radians((min_tower_lat + max_tower_lat) / 2.0)
        buffer_deg_lon = (max_coverage * 1.5) / (
            METERS_PER_DEGREE_LAT * max(0.1, math.cos(lat_rad))
        )

        if not (
            min_tower_lat - buffer_deg_lat <= lat <= max_tower_lat + buffer_deg_lat
        ) or not (
            min_tower_lon - buffer_deg_lon <= lon <= max_tower_lon + buffer_deg_lon
        ):
            validation_res.errors.append(
                ValidationError(
                    field="estimated_latitude/estimated_longitude",
                    message=(
                        f"Estimated position ({lat:.5f}, {lon:.5f}) is outside the scenario's "
                        f"tower bounding box with 1.5x coverage buffer."
                    ),
                    severity=Severity.WARNING,
                    code="RESULT_OUTSIDE_TOWER_BBOX",
                )
            )

        # Check if the estimated point is within the coverage area of at least one tower
        in_coverage = False
        for t in towers:
            dist = haversine_distance_m(lat, lon, t.latitude, t.longitude)
            if dist <= t.coverage_radius_m:
                in_coverage = True
                break

        if not in_coverage:
            validation_res.errors.append(
                ValidationError(
                    field="estimated_latitude/estimated_longitude",
                    message="Estimated position is outside the coverage radius of all towers.",
                    severity=Severity.WARNING,
                    code="RESULT_OUTSIDE_ALL_COVERAGE",
                )
            )

        return validation_res


def cross_validate(
    result: LocalizationResult,
    confidence: ConfidenceResult,
) -> ValidationResult:
    """Compare localization result error against confidence estimation parameters."""
    validation_res = ValidationResult()

    if result.error_m is None:
        return validation_res

    error = result.error_m
    level = confidence.confidence_level

    if level == "high" and error > 150.0:
        validation_res.errors.append(
            ValidationError(
                field="error_m",
                message=f"High error ({error:.1f}m) observed despite 'high' confidence level classification.",
                severity=Severity.WARNING,
                code="CONFIDENCE_MISMATCH_HIGH_ERROR",
            )
        )
    elif level == "medium" and error > 300.0:
        validation_res.errors.append(
            ValidationError(
                field="error_m",
                message=f"Moderate-high error ({error:.1f}m) observed for 'medium' confidence level classification.",
                severity=Severity.WARNING,
                code="CONFIDENCE_MISMATCH_MEDIUM_ERROR",
            )
        )

    if confidence.error_ellipse_semi_major_m is not None:
        limit = 3.0 * confidence.error_ellipse_semi_major_m
        if error > limit:
            validation_res.errors.append(
                ValidationError(
                    field="error_m",
                    message=(
                        f"Actual localization error ({error:.1f}m) exceeds the 3-sigma "
                        f"error ellipse bound ({limit:.1f}m)."
                    ),
                    severity=Severity.WARNING,
                    code="ERROR_EXCEEDS_ELLIPSE_BOUNDS",
                )
            )

    return validation_res
