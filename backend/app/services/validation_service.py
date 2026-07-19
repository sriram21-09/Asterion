"""
Measurement Validation Service
================================

Stateless validation logic for measurement batches.

Each measurement is checked against domain-specific business rules:
  - RSSI within [-150, 0] dBm
  - Coordinates within WGS84 bounds
  - Timestamp is a parseable ISO 8601 string and not in the future
  - Optional fields are non-negative where applicable (timing advance, uncertainty)

This service is deliberately **stateless** — it does not touch the database.
It applies the same constraints found in ``app.shared.validation`` but
returns a structured result rather than raising on first failure.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from app.schemas.validation import (
    MeasurementInput,
    ValidationErrorItem,
    ValidateMeasurementsResponse,
    Severity,
)

from scientific.models.measurement import Measurement as SciMeasurement
from scientific.validation.validators import MeasurementValidator
from scientific.validation.validators import Severity as SciSeverity

# ── Constants (same as app.shared.validation) ─────────────────────────────

LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0
RSSI_MIN, RSSI_MAX = -150.0, 0.0


def _validate_single(
    m: MeasurementInput,
    index: int,
) -> List[ValidationErrorItem]:
    """Run all checks against a single measurement.

    Returns a (possibly empty) list of errors / warnings.
    """
    issues: List[ValidationErrorItem] = []

    # ── Basic constraints & format validation ─────────────────────────
    # 1. measurement_id non-empty
    if not m.measurement_id or not m.measurement_id.strip():
        issues.append(
            ValidationErrorItem(
                field="measurement_id",
                message="Measurement ID must not be empty.",
                severity=Severity.ERROR,
                measurement_index=index,
            )
        )

    # 2. tower_id non-empty
    if not m.tower_id or not m.tower_id.strip():
        issues.append(
            ValidationErrorItem(
                field="tower_id",
                message="Tower ID must not be empty.",
                severity=Severity.ERROR,
                measurement_index=index,
            )
        )

    # 3. RSSI range [-150, 0] dBm
    if not (RSSI_MIN <= m.rssi_dbm <= RSSI_MAX):
        issues.append(
            ValidationErrorItem(
                field="rssi_dbm",
                message=f"RSSI must be between {RSSI_MIN} and {RSSI_MAX} dBm. Got {m.rssi_dbm}.",
                severity=Severity.ERROR,
                measurement_index=index,
            )
        )

    # 4. Latitude WGS84 range
    if m.latitude is not None and not (LAT_MIN <= m.latitude <= LAT_MAX):
        issues.append(
            ValidationErrorItem(
                field="latitude",
                message=f"Latitude must be between {LAT_MIN} and {LAT_MAX}. Got {m.latitude}.",
                severity=Severity.ERROR,
                measurement_index=index,
            )
        )

    # 5. Longitude WGS84 range
    if m.longitude is not None and not (LON_MIN <= m.longitude <= LON_MAX):
        issues.append(
            ValidationErrorItem(
                field="longitude",
                message=f"Longitude must be between {LON_MIN} and {LON_MAX}. Got {m.longitude}.",
                severity=Severity.ERROR,
                measurement_index=index,
            )
        )

    # 6. Lat/lon parity (both or neither)
    has_lat = m.latitude is not None
    has_lon = m.longitude is not None
    if has_lat != has_lon:
        issues.append(
            ValidationErrorItem(
                field="latitude/longitude",
                message="Latitude and longitude must both be provided or both be omitted.",
                severity=Severity.ERROR,
                measurement_index=index,
            )
        )

    # 7. Timing advance (non-negative if provided)
    if m.timing_advance is not None and m.timing_advance < 0:
        issues.append(
            ValidationErrorItem(
                field="timing_advance",
                message=f"Timing advance must be ≥ 0. Got {m.timing_advance}.",
                severity=Severity.WARNING,
                measurement_index=index,
            )
        )

    # 8. Uncertainty (positive if provided)
    if m.uncertainty_m is not None and m.uncertainty_m < 0:
        issues.append(
            ValidationErrorItem(
                field="uncertainty_m",
                message=f"Uncertainty must be ≥ 0 metres. Got {m.uncertainty_m}.",
                severity=Severity.WARNING,
                measurement_index=index,
            )
        )

    # 9. Timestamp parseable
    dt = None
    try:
        dt = datetime.fromisoformat(m.timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        issues.append(
            ValidationErrorItem(
                field="timestamp",
                message=f"Could not parse timestamp '{m.timestamp}' as ISO 8601.",
                severity=Severity.ERROR,
                measurement_index=index,
            )
        )

    # ── Scientific Domain Rules (only if basic layout/format is valid) ──
    has_errors = any(issue.severity == Severity.ERROR for issue in issues)

    if not has_errors and dt is not None:
        try:
            sci_m = SciMeasurement(
                measurement_id=m.measurement_id,
                tower_id=m.tower_id,
                timestamp=dt,
                rssi_dbm=m.rssi_dbm,
                latitude=m.latitude,
                longitude=m.longitude,
                timing_advance=m.timing_advance,
                uncertainty_m=m.uncertainty_m,
            )
            validator = MeasurementValidator()
            result = validator.validate(sci_m)
            for err in result.errors:
                sev = (
                    Severity.ERROR
                    if err.severity == SciSeverity.ERROR
                    else Severity.WARNING
                )
                issues.append(
                    ValidationErrorItem(
                        field=err.field,
                        message=err.message,
                        severity=sev,
                        measurement_index=index,
                    )
                )
        except Exception as e:
            issues.append(
                ValidationErrorItem(
                    field="measurement",
                    message=f"Scientific validator error: {str(e)}",
                    severity=Severity.ERROR,
                    measurement_index=index,
                )
            )

    return issues


def validate_measurements_batch(
    measurements: List[MeasurementInput],
) -> ValidateMeasurementsResponse:
    """Validate a full batch and return aggregated results."""
    all_errors: List[ValidationErrorItem] = []
    rejected_indices: set[int] = set()

    for idx, m in enumerate(measurements):
        issues = _validate_single(m, idx)
        all_errors.extend(issues)
        # A measurement is "rejected" if it has at least one error-level issue
        if any(i.severity == Severity.ERROR for i in issues):
            rejected_indices.add(idx)

    total = len(measurements)
    rejected = len(rejected_indices)
    warning_count = sum(1 for e in all_errors if e.severity == Severity.WARNING)

    return ValidateMeasurementsResponse(
        is_valid=(rejected == 0),
        valid_count=total - rejected,
        rejected_count=rejected,
        warning_count=warning_count,
        errors=all_errors,
    )
