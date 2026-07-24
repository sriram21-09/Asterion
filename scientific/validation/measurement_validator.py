"""
Measurement Validator
=====================
"""

from __future__ import annotations

from datetime import UTC, datetime

from scientific.config import DEFAULT_VALIDATION_THRESHOLDS, ValidationThresholds
from scientific.models.measurement import Measurement
from scientific.validation.types import Severity, ValidationError, ValidationResult


class MeasurementValidator:
    """Validates a single :class:`Measurement` instance.

    Checks performed:
        1. Required fields presence (measurement_id, tower_id, timestamp, rssi_dbm).
        2. Latitude/longitude must be provided together or not at all.
        3. Coordinates must fall within the expected operational area.
        4. RSSI must be in absolute limits [-150, 0] dBm, and warning if outside
           plausible range [-120, -30] dBm.
        5. Timing advance and RSSI consistency (warning if TA > thresholds.ta_rssi_ta_threshold
           but RSSI is stronger than thresholds.ta_rssi_rssi_threshold_dbm).
        6. Timestamp must not be in the future.
        7. Timestamp should not be excessively old.
    """

    def __init__(
        self, thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS
    ) -> None:
        self.thresholds = thresholds

    def validate(self, measurement: Measurement) -> ValidationResult:
        """Run all measurement validation checks."""
        result = ValidationResult()

        # --- 1. Missing values check ---
        if not measurement.measurement_id or measurement.measurement_id.strip() == "":
            result.errors.append(
                ValidationError(
                    field="measurement_id",
                    message="Measurement ID must be provided and cannot be empty.",
                    code="MEAS_MISSING_ID",
                )
            )
        if not measurement.tower_id or measurement.tower_id.strip() == "":
            result.errors.append(
                ValidationError(
                    field="tower_id",
                    message="Tower ID must be provided and cannot be empty.",
                    code="MEAS_MISSING_TOWER_ID",
                )
            )
        if measurement.timestamp is None:
            result.errors.append(
                ValidationError(
                    field="timestamp",
                    message="Measurement timestamp must be provided.",
                    code="MEAS_MISSING_TIMESTAMP",
                )
            )
        if measurement.rssi_dbm is None:
            result.errors.append(
                ValidationError(
                    field="rssi_dbm",
                    message="RSSI value must be provided.",
                    code="MEAS_MISSING_RSSI",
                )
            )

        # --- 2. Lat/Lon pairing and spatial bounds verification ---
        has_lat = measurement.latitude is not None
        has_lon = measurement.longitude is not None
        if has_lat != has_lon:
            result.errors.append(
                ValidationError(
                    field="latitude/longitude",
                    message=(
                        "Latitude and longitude must both be provided or both "
                        f"be omitted. Got latitude={measurement.latitude}, longitude={measurement.longitude}."
                    ),
                    code="MEAS_PARTIAL_COORDS",
                )
            )
        elif has_lat and has_lon:
            lat_min, lat_max = self.thresholds.latitude_range
            lon_min, lon_max = self.thresholds.longitude_range
            if not (lat_min <= measurement.latitude <= lat_max) or not (
                lon_min <= measurement.longitude <= lon_max
            ):
                result.errors.append(
                    ValidationError(
                        field="latitude/longitude",
                        message=(
                            f"Coordinates ({measurement.latitude}, {measurement.longitude}) "
                            f"are outside the expected operational area. "
                            f"Allowed range: Latitude {self.thresholds.latitude_range}, Longitude {self.thresholds.longitude_range}."
                        ),
                        code="MEAS_COORDS_OUT_OF_BOUNDS",
                    )
                )

        # --- 3. RSSI plausibility and boundaries ---
        if measurement.rssi_dbm is not None:
            if (
                measurement.rssi_dbm > self.thresholds.rssi_max_dbm
                or measurement.rssi_dbm < self.thresholds.rssi_min_dbm
            ):
                result.errors.append(
                    ValidationError(
                        field="rssi_dbm",
                        message=(
                            f"RSSI value {measurement.rssi_dbm} dBm is out of the absolute "
                            f"allowed range [{self.thresholds.rssi_min_dbm}, {self.thresholds.rssi_max_dbm}] dBm."
                        ),
                        code="MEAS_RSSI_OUT_OF_BOUNDS",
                    )
                )
            elif measurement.rssi_dbm > self.thresholds.rssi_plausible_max_dbm:
                result.errors.append(
                    ValidationError(
                        field="rssi_dbm",
                        message=(
                            f"RSSI value {measurement.rssi_dbm} dBm is unusually "
                            "strong for cellular signals. Typical range is "
                            f"[{self.thresholds.rssi_plausible_min_dbm}, {self.thresholds.rssi_plausible_max_dbm}] dBm."
                        ),
                        severity=Severity.WARNING,
                        code="MEAS_RSSI_HIGH",
                    )
                )
            elif measurement.rssi_dbm < self.thresholds.rssi_plausible_min_dbm:
                result.errors.append(
                    ValidationError(
                        field="rssi_dbm",
                        message=(
                            f"RSSI value {measurement.rssi_dbm} dBm is extremely "
                            "weak. Signal may be below the noise floor."
                        ),
                        severity=Severity.WARNING,
                        code="MEAS_RSSI_LOW",
                    )
                )

        # --- 4. TA vs RSSI consistency ---
        if (
            measurement.timing_advance is not None
            and measurement.rssi_dbm is not None
            and measurement.timing_advance > self.thresholds.ta_rssi_ta_threshold
            and measurement.rssi_dbm > self.thresholds.ta_rssi_rssi_threshold_dbm
        ):
            result.errors.append(
                ValidationError(
                    field="timing_advance",
                    message=(
                        f"Timing advance ({measurement.timing_advance}) suggests "
                        f"the device is far from the tower, but RSSI "
                        f"({measurement.rssi_dbm} dBm) indicates a strong signal. "
                        "These values may be inconsistent."
                    ),
                    severity=Severity.WARNING,
                    code="MEAS_TA_RSSI_MISMATCH",
                )
            )

        # --- 5. Future timestamp ---
        if measurement.timestamp is not None:
            now = datetime.now(UTC)
            ts = measurement.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            if ts > now:
                result.errors.append(
                    ValidationError(
                        field="timestamp",
                        message=(
                            f"Measurement timestamp {measurement.timestamp.isoformat()} "
                            "is in the future."
                        ),
                        code="MEAS_FUTURE_TIMESTAMP",
                    )
                )

            # --- 6. Excessively old timestamp ---
            age_days = (now - ts).days
            if age_days > self.thresholds.max_measurement_age_days:
                result.errors.append(
                    ValidationError(
                        field="timestamp",
                        message=(
                            f"Measurement is {age_days} days old (> {self.thresholds.max_measurement_age_days} "
                            "days). Data may be stale."
                        ),
                        severity=Severity.WARNING,
                        code="MEAS_STALE",
                    )
                )

        return result
