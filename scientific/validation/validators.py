"""
Scientific Validation Interfaces & Validators
===============================================

Defines expected interfaces and concrete validators for the core scientific
data models: Measurement, Tower, and Scenario.

Interface Contracts
--------------------
Each validator protocol specifies the contract that any conforming
implementation must satisfy. This enables:

- Swapping validation strategies without changing pipeline code
- Mocking validators in tests
- Layering validation (quick → deep → physics-based)

Concrete Validators
--------------------
Ready-to-use validators that enforce domain constraints beyond what
Pydantic field-level validation covers:

- **MeasurementValidator**: Cross-field consistency (lat/lon pairing,
  RSSI plausibility given timing advance, timestamp sanity).
- **TowerValidator**: Physics-aware checks (frequency band validity,
  transmit power range, height realism).
- **ScenarioValidator**: Structural integrity (tower uniqueness,
  measurement–tower referential consistency, minimum coverage).

Usage::

    >>> from scientific.validation.validators import ScenarioValidator
    >>> validator = ScenarioValidator()
    >>> result = validator.validate(some_scenario)
    >>> if not result.is_valid:
    ...     for err in result.errors:
    ...         print(f"[{err.severity}] {err.field}: {err.message}")
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Protocol, TypeVar, Dict

from scientific.models.measurement import Measurement
from scientific.models.scenario import Scenario
from scientific.models.scenario_config import ScenarioConfig
from scientific.models.tower import Tower
from scientific.models.result import LocalizationResult, ConfidenceResult
from scientific.config import (
    ValidationThresholds,
    DEFAULT_VALIDATION_THRESHOLDS,
    get_environment_config,
)
from scientific.constants import TA_RESOLUTION_M, haversine_distance_m

# ---------------------------------------------------------------------------
# Validation result types
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    """Severity level for a validation finding."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationError:
    """A single validation finding.

    Attributes:
        field: Dot-separated path to the offending field (e.g. ``"towers[0].latitude"``).
        message: Human-readable description of the issue.
        severity: How serious the finding is.
        code: Machine-readable error code for programmatic handling.
    """

    field: str
    message: str
    severity: Severity = Severity.ERROR
    code: Optional[str] = None


@dataclass
class ValidationResult:
    """Aggregated result of running one or more validation checks.

    Attributes:
        errors: List of validation findings (errors, warnings, info).
        is_valid: ``True`` if there are no ``ERROR``-severity findings.
    """

    errors: List[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no ERROR-severity findings exist."""
        return not any(e.severity == Severity.ERROR for e in self.errors)

    @property
    def warnings(self) -> List[ValidationError]:
        """Return only WARNING-severity findings."""
        return [e for e in self.errors if e.severity == Severity.WARNING]

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Merge another result into this one, combining all findings."""
        self.errors.extend(other.errors)
        return self


# ---------------------------------------------------------------------------
# Protocol interfaces (structural typing)
# ---------------------------------------------------------------------------

T = TypeVar("T")


class Validator(Protocol[T]):
    """Protocol that all scientific validators must satisfy.

    Implementing classes must provide a ``validate`` method that accepts
    an instance of the target model and returns a :class:`ValidationResult`.

    Expected Interfaces
    --------------------

    **Measurement objects** must expose:
        - ``measurement_id: str``   — unique measurement identifier
        - ``tower_id: str``         — reference to the source tower
        - ``timestamp: datetime``   — when the measurement was taken
        - ``rssi_dbm: float``       — RSSI in dBm, range [-150, 0]
        - ``latitude: float | None``  — optional measurement-point latitude
        - ``longitude: float | None`` — optional measurement-point longitude
        - ``timing_advance: float | None`` — optional GSM TA value
        - ``uncertainty_m: float | None``  — optional uncertainty in meters

    **Tower objects** must expose:
        - ``tower_id: str``           — unique tower identifier
        - ``latitude: float``         — WGS84 latitude [-90, 90]
        - ``longitude: float``        — WGS84 longitude [-180, 180]
        - ``antenna_height_m: float`` — antenna height > 0 meters
        - ``frequency_mhz: float``    — operating frequency > 0 MHz
        - ``transmit_power_dbm: float`` — EIRP in dBm
        - ``sector: str | None``      — optional sector identifier
        - ``coverage_radius_m: float`` — coverage radius > 0 meters

    **Scenario objects** must expose:
        - ``scenario_id: str``                  — unique scenario identifier
        - ``name: str``                         — human-readable name
        - ``description: str | None``           — optional description
        - ``towers: list[Tower]``               — ≥ 3 towers
        - ``measurements: list[Measurement]``   — associated measurements
        - --noise_level_dbm: float``            -- background noise floor
        - ``environment_type: str``             — one of: urban, suburban, rural, highway
        - ``expected_device_lat: float | None`` — optional ground-truth latitude
        - ``expected_device_lon: float | None`` — optional ground-truth longitude
    """

    def validate(self, obj: T) -> ValidationResult:
        """Validate *obj* and return a :class:`ValidationResult`."""
        ...  # pragma: no cover


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Common cellular frequency bands (MHz) — used for plausibility checks
CELLULAR_BANDS_MHZ = [
    700,
    800,
    850,
    900,  # Low-band
    1700,
    1800,
    1900,
    2100,  # Mid-band
    2300,
    2500,
    2600,  # Upper mid-band
    3500,
    3700,  # C-band (5G)
    26000,
    28000,
    39000,  # mmWave (5G)
]


# ---------------------------------------------------------------------------
# Concrete validators
# ---------------------------------------------------------------------------


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
                        "be omitted. Got latitude={}, longitude={}.".format(
                            measurement.latitude, measurement.longitude
                        )
                    ),
                    code="MEAS_PARTIAL_COORDS",
                )
            )
        elif has_lat and has_lon:
            lat_min, lat_max = self.thresholds.latitude_range
            lon_min, lon_max = self.thresholds.longitude_range
            # Note: We do ge/le check
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
            now = datetime.now(timezone.utc)
            ts = measurement.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
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
        if tower.antenna_height_m is not None:
            if not (
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


class ScenarioValidator:
    """Validates a complete :class:`Scenario` instance.

    Checks performed:
        1. Required fields presence.
        2. All tower IDs must be unique within the scenario.
        3. Every measurement must reference a tower that exists in the
           scenario's tower list.
        4. Unique measurement IDs and duplicate record checks (same tower + timestamp).
        5. If ground-truth coordinates are provided, both lat and lon
           must be present, and must fall within expected operational areas.
        6. At least one measurement should exist for each tower
           (warning if a tower has zero coverage).
        7. Physics consistency cross-checks between Timing Advance distance and RSSI decay models.
        8. All embedded towers and measurements pass their own
           validators (deep validation).

    Parameters:
        deep: If ``True`` (default), also runs :class:`TowerValidator`
              and :class:`MeasurementValidator` on each embedded object.
    """

    def __init__(
        self,
        *,
        deep: bool = True,
        thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
    ) -> None:
        self._deep = deep
        self.thresholds = thresholds
        self._tower_validator = TowerValidator(thresholds=thresholds)
        self._measurement_validator = MeasurementValidator(thresholds=thresholds)

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Run all scenario validation checks."""
        result = ValidationResult()

        # --- 1. Missing scenario values ---
        if not scenario.scenario_id or scenario.scenario_id.strip() == "":
            result.errors.append(
                ValidationError(
                    field="scenario_id",
                    message="Scenario ID must be provided and cannot be empty.",
                    code="SCENARIO_MISSING_ID",
                )
            )
        if not scenario.name or scenario.name.strip() == "":
            result.errors.append(
                ValidationError(
                    field="name",
                    message="Scenario name must be provided and cannot be empty.",
                    code="SCENARIO_MISSING_NAME",
                )
            )
        if scenario.towers is None or len(scenario.towers) < 3:
            result.errors.append(
                ValidationError(
                    field="towers",
                    message=(
                        f"At least 3 towers are required for localization. "
                        f"Got {len(scenario.towers) if scenario.towers else 0}."
                    ),
                    code="SCENARIO_INSUFFICIENT_TOWERS",
                )
            )

        # --- 2. Unique tower IDs ---
        tower_ids = (
            [t.tower_id for t in scenario.towers if t.tower_id]
            if scenario.towers
            else []
        )
        seen_towers: set[str] = set()
        for idx, tid in enumerate(tower_ids):
            if tid in seen_towers:
                result.errors.append(
                    ValidationError(
                        field=f"towers[{idx}].tower_id",
                        message=f"Duplicate tower_id '{tid}' in scenario.",
                        code="SCENARIO_DUPLICATE_TOWER",
                    )
                )
            seen_towers.add(tid)

        # --- 3. Measurement → Tower referential integrity & duplicates ---
        tower_id_set = set(tower_ids)
        seen_meas_ids: set[str] = set()
        seen_meas_records: set[tuple[str, datetime]] = set()

        measurements = scenario.measurements or []
        for idx, m in enumerate(measurements):
            # Check unique measurement IDs
            if m.measurement_id:
                if m.measurement_id in seen_meas_ids:
                    result.errors.append(
                        ValidationError(
                            field=f"measurements[{idx}].measurement_id",
                            message=f"Duplicate measurement_id '{m.measurement_id}' in scenario.",
                            code="SCENARIO_DUPLICATE_MEASUREMENT",
                        )
                    )
                seen_meas_ids.add(m.measurement_id)

            # Referential integrity
            if m.tower_id not in tower_id_set:
                result.errors.append(
                    ValidationError(
                        field=f"measurements[{idx}].tower_id",
                        message=(
                            f"Measurement '{m.measurement_id}' references tower "
                            f"'{m.tower_id}' which is not defined in this scenario."
                        ),
                        code="SCENARIO_ORPHAN_MEASUREMENT",
                    )
                )

            # Check duplicate timestamps (same tower, same timestamp)
            if m.tower_id and m.timestamp:
                record_key = (m.tower_id, m.timestamp)
                if record_key in seen_meas_records:
                    result.errors.append(
                        ValidationError(
                            field=f"measurements[{idx}].timestamp",
                            message=(
                                f"Duplicate measurement record found for tower '{m.tower_id}' "
                                f"at timestamp {m.timestamp.isoformat()}."
                            ),
                            code="SCENARIO_DUPLICATE_RECORD",
                        )
                    )
                seen_meas_records.add(record_key)

        # --- 4. Ground-truth coordinate pairing & bounds checking ---
        has_gt_lat = scenario.expected_device_lat is not None
        has_gt_lon = scenario.expected_device_lon is not None
        if has_gt_lat != has_gt_lon:
            result.errors.append(
                ValidationError(
                    field="expected_device_lat/expected_device_lon",
                    message=(
                        "Ground-truth coordinates must both be provided or both "
                        "be omitted."
                    ),
                    code="SCENARIO_PARTIAL_GROUND_TRUTH",
                )
            )
        elif has_gt_lat and has_gt_lon:
            lat_min, lat_max = self.thresholds.latitude_range
            lon_min, lon_max = self.thresholds.longitude_range
            if not (lat_min <= scenario.expected_device_lat <= lat_max) or not (
                lon_min <= scenario.expected_device_lon <= lon_max
            ):
                result.errors.append(
                    ValidationError(
                        field="expected_device_lat/expected_device_lon",
                        message=(
                            f"Ground-truth coordinates ({scenario.expected_device_lat}, {scenario.expected_device_lon}) "
                            f"are outside the expected operational area. "
                            f"Allowed range: Latitude {self.thresholds.latitude_range}, Longitude {self.thresholds.longitude_range}."
                        ),
                        code="SCENARIO_COORDS_OUT_OF_BOUNDS",
                    )
                )

        # --- 5. Tower coverage (every tower should have ≥1 measurement) ---
        if scenario.measurements:
            referenced_towers = {
                m.tower_id for m in scenario.measurements if m.tower_id
            }
            uncovered = tower_id_set - referenced_towers
            for tid in uncovered:
                result.errors.append(
                    ValidationError(
                        field="towers/measurements",
                        message=(
                            f"Tower '{tid}' has no measurements in this scenario. "
                            "It will not contribute to localization."
                        ),
                        severity=Severity.WARNING,
                        code="SCENARIO_UNCOVERED_TOWER",
                    )
                )

        # --- 6. Physics-based TA vs RSSI decay model cross-check ---
        if scenario.towers and scenario.measurements:
            env_cfg = get_environment_config(scenario.environment_type)
            exponent = env_cfg.path_loss_exponent
            ref_loss = env_cfg.reference_loss_db
            ref_dist = env_cfg.reference_distance_m
            sigma = env_cfg.shadow_fading_std_db

            tower_map = {t.tower_id: t for t in scenario.towers if t.tower_id}

            for idx, m in enumerate(scenario.measurements):
                if m.timing_advance is not None and m.rssi_dbm is not None:
                    tower = tower_map.get(m.tower_id)
                    if tower is not None and tower.transmit_power_dbm is not None:
                        ta = m.timing_advance
                        # Compute distance interval implied by TA
                        d_min = max(ref_dist, (ta - 0.5) * TA_RESOLUTION_M)
                        d_max = max(ref_dist, (ta + 0.5) * TA_RESOLUTION_M)

                        # Compute path loss at the limits
                        loss_min = ref_loss + 10.0 * exponent * math.log10(
                            d_min / ref_dist
                        )
                        loss_max = ref_loss + 10.0 * exponent * math.log10(
                            d_max / ref_dist
                        )

                        expected_rssi_max = tower.transmit_power_dbm - loss_min
                        expected_rssi_min = tower.transmit_power_dbm - loss_max

                        # Define upper and lower bounds with standard deviation margins
                        rssi_upper_bound = expected_rssi_max + 3.0 * sigma
                        rssi_lower_bound = expected_rssi_min - 4.0 * sigma

                        # Check for wild mismatch
                        if m.rssi_dbm > rssi_upper_bound:
                            result.errors.append(
                                ValidationError(
                                    field=f"measurements[{idx}].timing_advance",
                                    message=(
                                        f"Physics Mismatch: Measurement '{m.measurement_id}' has RSSI of {m.rssi_dbm} dBm, "
                                        f"which is physically too strong for the Timing Advance of {ta} "
                                        f"(implied distance range: {d_min:.1f}m - {d_max:.1f}m, expected RSSI range: "
                                        f"{expected_rssi_min:.1f} to {expected_rssi_max:.1f} dBm with shadow fading std {sigma} dB)."
                                    ),
                                    severity=Severity.WARNING,
                                    code="SCENARIO_TA_RSSI_PHYSICS_MISMATCH",
                                )
                            )
                        elif m.rssi_dbm < rssi_lower_bound:
                            result.errors.append(
                                ValidationError(
                                    field=f"measurements[{idx}].timing_advance",
                                    message=(
                                        f"Physics Mismatch: Measurement '{m.measurement_id}' has RSSI of {m.rssi_dbm} dBm, "
                                        f"which is physically too weak for the Timing Advance of {ta} "
                                        f"(implied distance range: {d_min:.1f}m - {d_max:.1f}m, expected RSSI range: "
                                        f"{expected_rssi_min:.1f} to {expected_rssi_max:.1f} dBm with shadow fading std {sigma} dB)."
                                    ),
                                    severity=Severity.WARNING,
                                    code="SCENARIO_TA_RSSI_PHYSICS_MISMATCH",
                                )
                            )

        # --- 7. Deep validation of embedded objects ---
        if self._deep:
            if scenario.towers:
                for idx, tower in enumerate(scenario.towers):
                    sub = self._tower_validator.validate(tower)
                    for err in sub.errors:
                        result.errors.append(
                            ValidationError(
                                field=f"towers[{idx}].{err.field}",
                                message=err.message,
                                severity=err.severity,
                                code=err.code,
                            )
                        )

            if scenario.measurements:
                for idx, meas in enumerate(scenario.measurements):
                    sub = self._measurement_validator.validate(meas)
                    for err in sub.errors:
                        result.errors.append(
                            ValidationError(
                                field=f"measurements[{idx}].{err.field}",
                                message=err.message,
                                severity=err.severity,
                                code=err.code,
                            )
                        )

        return result


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def validate_measurement(
    measurement: Measurement,
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> ValidationResult:
    """Shortcut: validate a single Measurement."""
    return MeasurementValidator(thresholds).validate(measurement)


def validate_tower(
    tower: Tower,
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> ValidationResult:
    """Shortcut: validate a single Tower."""
    return TowerValidator(thresholds).validate(tower)


def validate_scenario(
    scenario: Scenario,
    *,
    deep: bool = True,
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> ValidationResult:
    """Shortcut: validate a complete Scenario (optionally with deep checks)."""
    return ScenarioValidator(deep=deep, thresholds=thresholds).validate(scenario)


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
        max_coverage = max((t.coverage_radius_m for t in towers), default=5000.0)
        from scientific.constants import METERS_PER_DEGREE_LAT

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
    """Compare localization result error against confidence estimation parameters.

    Warns if there is a mismatch (e.g., high actual error with 'high' confidence).
    """
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


def validate_batch(
    scenarios: List[Scenario],
    *,
    deep: bool = True,
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> Dict[str, ValidationResult]:
    """Validate a batch of Scenario objects, returning a mapping of scenario_id to ValidationResult."""
    validator = ScenarioValidator(deep=deep, thresholds=thresholds)
    return {s.scenario_id: validator.validate(s) for s in scenarios}
