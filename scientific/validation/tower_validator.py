"""
Tower Validator
===============
"""

from __future__ import annotations

from scientific.config import DEFAULT_VALIDATION_THRESHOLDS, ValidationThresholds
from scientific.models.tower import Tower
from scientific.validation.types import (
    CELLULAR_BANDS_MHZ,
    Severity,
    ValidationError,
    ValidationResult,
)


class TowerValidator:
    """Validates a single :class:`Tower` instance.

    Checks performed:
        1. Required fields presence.
        2. Coordinates must fall within the expected operational area.
        3. Frequency should be near a known cellular band (warning).
        4. Transmit power should be within a realistic range (warning).
        5. Antenna height should be within a plausible range (warning).
        6. Coverage radius should not exceed a plausible maximum (warning).
    """

    def __init__(
        self, thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS
    ) -> None:
        self.thresholds = thresholds

    def validate(self, tower: Tower) -> ValidationResult:
        """Run all tower validation checks."""
        result = ValidationResult()

        # --- 1. Missing values check ---
        if not tower.tower_id or tower.tower_id.strip() == "":
            result.errors.append(
                ValidationError(
                    field="tower_id",
                    message="Tower ID must be provided.",
                    code="TOWER_MISSING_ID",
                )
            )
        if tower.latitude is None or tower.longitude is None:
            result.errors.append(
                ValidationError(
                    field="latitude/longitude",
                    message="Tower coordinates must be provided.",
                    code="TOWER_MISSING_COORDS",
                )
            )
        if tower.antenna_height_m is None:
            result.errors.append(
                ValidationError(
                    field="antenna_height_m",
                    message="Antenna height must be provided.",
                    code="TOWER_MISSING_HEIGHT",
                )
            )
        if tower.frequency_mhz is None:
            result.errors.append(
                ValidationError(
                    field="frequency_mhz",
                    message="Operating frequency must be provided.",
                    code="TOWER_MISSING_FREQUENCY",
                )
            )
        if tower.transmit_power_dbm is None:
            result.errors.append(
                ValidationError(
                    field="transmit_power_dbm",
                    message="Transmit power must be provided.",
                    code="TOWER_MISSING_TX_POWER",
                )
            )
        if tower.coverage_radius_m is None:
            result.errors.append(
                ValidationError(
                    field="coverage_radius_m",
                    message="Coverage radius must be provided.",
                    code="TOWER_MISSING_RADIUS",
                )
            )

        # --- 2. Coordinate operational bounds check ---
        if tower.latitude is not None and tower.longitude is not None:
            lat_min, lat_max = self.thresholds.latitude_range
            lon_min, lon_max = self.thresholds.longitude_range
            if not (lat_min <= tower.latitude <= lat_max) or not (
                lon_min <= tower.longitude <= lon_max
            ):
                result.errors.append(
                    ValidationError(
                        field="latitude/longitude",
                        message=(
                            f"Tower coordinates ({tower.latitude}, {tower.longitude}) "
                            f"are outside the expected operational area. "
                            f"Allowed range: Latitude {self.thresholds.latitude_range}, Longitude {self.thresholds.longitude_range}."
                        ),
                        code="TOWER_COORDS_OUT_OF_BOUNDS",
                    )
                )

        # --- 3. Frequency band plausibility ---
        if tower.frequency_mhz is not None:
            near_known_band = any(
                abs(tower.frequency_mhz - band) <= self.thresholds.band_tolerance_mhz
                for band in CELLULAR_BANDS_MHZ
            )
            if not near_known_band:
                result.errors.append(
                    ValidationError(
                        field="frequency_mhz",
                        message=(
                            f"Frequency {tower.frequency_mhz} MHz is not near any "
                            "standard cellular band. This may indicate a data entry "
                            "error."
                        ),
                        severity=Severity.WARNING,
                        code="TOWER_UNUSUAL_FREQ",
                    )
                )

        # --- 4. Transmit power range ---
        if tower.transmit_power_dbm is not None:
            if not (
                self.thresholds.min_tx_power_dbm
                <= tower.transmit_power_dbm
                <= self.thresholds.max_tx_power_dbm
            ):
                result.errors.append(
                    ValidationError(
                        field="transmit_power_dbm",
                        message=(
                            f"Transmit power {tower.transmit_power_dbm} dBm is outside "
                            f"the typical range [{self.thresholds.min_tx_power_dbm}, {self.thresholds.max_tx_power_dbm}] dBm."
                        ),
                        severity=Severity.WARNING,
                        code="TOWER_TX_POWER_RANGE",
                    )
                )

        # --- 5. Antenna height plausibility ---
        if tower.antenna_height_m is not None and not (
            self.thresholds.min_antenna_height_m
            <= tower.antenna_height_m
            <= self.thresholds.max_antenna_height_m
        ):
            result.errors.append(
                ValidationError(
                    field="antenna_height_m",
                    message=(
                        f"Antenna height {tower.antenna_height_m} m is outside "
                        f"the plausible range [{self.thresholds.min_antenna_height_m}, "
                        f"{self.thresholds.max_antenna_height_m}] m."
                    ),
                    severity=Severity.WARNING,
                    code="TOWER_HEIGHT_RANGE",
                )
            )

        # --- 6. Coverage radius ---
        if tower.coverage_radius_m is not None:
            if tower.coverage_radius_m > self.thresholds.max_coverage_radius_m:
                result.errors.append(
                    ValidationError(
                        field="coverage_radius_m",
                        message=(
                            f"Coverage radius {tower.coverage_radius_m} m exceeds the "
                            f"plausible maximum of {self.thresholds.max_coverage_radius_m} m."
                        ),
                        severity=Severity.WARNING,
                        code="TOWER_COVERAGE_EXTREME",
                    )
                )

        return result
