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

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Protocol, TypeVar

from scientific.models.measurement import Measurement
from scientific.models.scenario import Scenario
from scientific.models.tower import Tower

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
        - ``noise_level_dbm: float``            — background noise floor
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

# Tolerance for matching a known band (±50 MHz)
BAND_TOLERANCE_MHZ = 50.0

# Realistic transmit power range (dBm)
MIN_TX_POWER_DBM = 10.0
MAX_TX_POWER_DBM = 60.0

# Realistic antenna height range (meters)
MIN_ANTENNA_HEIGHT_M = 1.0
MAX_ANTENNA_HEIGHT_M = 300.0

# Maximum plausible coverage radius (meters)
MAX_COVERAGE_RADIUS_M = 50_000.0

# Maximum age for a "reasonable" measurement timestamp
MAX_MEASUREMENT_AGE_DAYS = 365 * 5  # 5 years


# ---------------------------------------------------------------------------
# Concrete validators
# ---------------------------------------------------------------------------


class MeasurementValidator:
    """Validates a single :class:`Measurement` instance.

    Checks performed:
        1. Latitude/longitude must be provided together or not at all.
        2. RSSI should be in a realistic range for cellular signals
           (warning if outside [-120, -30] dBm).
        3. Timing advance and RSSI consistency (warning if TA > 0
           but RSSI is very strong, which is physically unlikely).
        4. Timestamp must not be in the future.
        5. Timestamp should not be excessively old (> 5 years).
    """

    def validate(self, measurement: Measurement) -> ValidationResult:
        """Run all measurement validation checks."""
        result = ValidationResult()

        # --- 1. Lat/Lon pairing ---
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

        # --- 2. RSSI plausibility ---
        if measurement.rssi_dbm > -30.0:
            result.errors.append(
                ValidationError(
                    field="rssi_dbm",
                    message=(
                        f"RSSI value {measurement.rssi_dbm} dBm is unusually "
                        "strong for cellular signals. Typical range is "
                        "[-120, -30] dBm."
                    ),
                    severity=Severity.WARNING,
                    code="MEAS_RSSI_HIGH",
                )
            )
        elif measurement.rssi_dbm < -120.0:
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

        # --- 3. TA vs RSSI consistency ---
        if (
            measurement.timing_advance is not None
            and measurement.timing_advance > 10
            and measurement.rssi_dbm > -50.0
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

        # --- 4. Future timestamp ---
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

        # --- 5. Excessively old timestamp ---
        age_days = (now - ts).days
        if age_days > MAX_MEASUREMENT_AGE_DAYS:
            result.errors.append(
                ValidationError(
                    field="timestamp",
                    message=(
                        f"Measurement is {age_days} days old (> {MAX_MEASUREMENT_AGE_DAYS} "
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
        1. Frequency should be near a known cellular band (warning).
        2. Transmit power should be within a realistic range (warning).
        3. Antenna height should be within a plausible range (warning).
        4. Coverage radius should not exceed a plausible maximum (warning).
    """

    def validate(self, tower: Tower) -> ValidationResult:
        """Run all tower validation checks."""
        result = ValidationResult()

        # --- 1. Frequency band plausibility ---
        near_known_band = any(
            abs(tower.frequency_mhz - band) <= BAND_TOLERANCE_MHZ
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

        # --- 2. Transmit power range ---
        if not (MIN_TX_POWER_DBM <= tower.transmit_power_dbm <= MAX_TX_POWER_DBM):
            result.errors.append(
                ValidationError(
                    field="transmit_power_dbm",
                    message=(
                        f"Transmit power {tower.transmit_power_dbm} dBm is outside "
                        f"the typical range [{MIN_TX_POWER_DBM}, {MAX_TX_POWER_DBM}] dBm."
                    ),
                    severity=Severity.WARNING,
                    code="TOWER_TX_POWER_RANGE",
                )
            )

        # --- 3. Antenna height plausibility ---
        if not (MIN_ANTENNA_HEIGHT_M <= tower.antenna_height_m <= MAX_ANTENNA_HEIGHT_M):
            result.errors.append(
                ValidationError(
                    field="antenna_height_m",
                    message=(
                        f"Antenna height {tower.antenna_height_m} m is outside "
                        f"the plausible range [{MIN_ANTENNA_HEIGHT_M}, "
                        f"{MAX_ANTENNA_HEIGHT_M}] m."
                    ),
                    severity=Severity.WARNING,
                    code="TOWER_HEIGHT_RANGE",
                )
            )

        # --- 4. Coverage radius ---
        if tower.coverage_radius_m > MAX_COVERAGE_RADIUS_M:
            result.errors.append(
                ValidationError(
                    field="coverage_radius_m",
                    message=(
                        f"Coverage radius {tower.coverage_radius_m} m exceeds the "
                        f"plausible maximum of {MAX_COVERAGE_RADIUS_M} m."
                    ),
                    severity=Severity.WARNING,
                    code="TOWER_COVERAGE_EXTREME",
                )
            )

        return result


class ScenarioValidator:
    """Validates a complete :class:`Scenario` instance.

    Checks performed:
        1. All tower IDs must be unique within the scenario.
        2. Every measurement must reference a tower that exists in the
           scenario's tower list.
        3. If ground-truth coordinates are provided, both lat and lon
           must be present.
        4. At least one measurement should exist for each tower
           (warning if a tower has zero coverage).
        5. All embedded towers and measurements pass their own
           validators (deep validation).

    Parameters:
        deep: If ``True`` (default), also runs :class:`TowerValidator`
              and :class:`MeasurementValidator` on each embedded object.
    """

    def __init__(self, *, deep: bool = True) -> None:
        self._deep = deep
        self._tower_validator = TowerValidator()
        self._measurement_validator = MeasurementValidator()

    def validate(self, scenario: Scenario) -> ValidationResult:
        """Run all scenario validation checks."""
        result = ValidationResult()

        # --- 1. Unique tower IDs ---
        tower_ids = [t.tower_id for t in scenario.towers]
        seen: set[str] = set()
        for idx, tid in enumerate(tower_ids):
            if tid in seen:
                result.errors.append(
                    ValidationError(
                        field=f"towers[{idx}].tower_id",
                        message=f"Duplicate tower_id '{tid}' in scenario.",
                        code="SCENARIO_DUPLICATE_TOWER",
                    )
                )
            seen.add(tid)

        # --- 2. Measurement → Tower referential integrity ---
        tower_id_set = set(tower_ids)
        for idx, m in enumerate(scenario.measurements):
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

        # --- 3. Ground-truth coordinate pairing ---
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

        # --- 4. Tower coverage (every tower should have ≥1 measurement) ---
        if scenario.measurements:
            referenced_towers = {m.tower_id for m in scenario.measurements}
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

        # --- 5. Deep validation of embedded objects ---
        if self._deep:
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


def validate_measurement(measurement: Measurement) -> ValidationResult:
    """Shortcut: validate a single Measurement."""
    return MeasurementValidator().validate(measurement)


def validate_tower(tower: Tower) -> ValidationResult:
    """Shortcut: validate a single Tower."""
    return TowerValidator().validate(tower)


def validate_scenario(scenario: Scenario, *, deep: bool = True) -> ValidationResult:
    """Shortcut: validate a complete Scenario (optionally with deep checks)."""
    return ScenarioValidator(deep=deep).validate(scenario)
