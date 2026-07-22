"""
Scientific Validation Module
==============================

Input validation and data quality components for the scientific engine:

- RSSI range validation (-150 dBm to 0 dBm)
- Coordinate bounds checking (WGS84 lat/lon)
- Measurement consistency checks (timestamps, tower IDs)
- Scenario completeness validation (minimum tower count)
- Data format validators for pipeline inputs
- CDR record validation and duplicate detection

Exports:
    MeasurementValidator: Single-measurement domain validation.
    TowerValidator: Single-tower physics-aware validation.
    ScenarioValidator: Full-scenario structural + deep validation.
    CDRRecordValidator: Single CDR record domain validation.
    ValidationResult: Aggregated validation findings.
    ValidationError: A single validation finding.
    Severity: Error / Warning / Info classification.
    validate_measurement: Convenience shortcut.
    validate_tower: Convenience shortcut.
    validate_scenario: Convenience shortcut.
    validate_cdr_batch: Convenience shortcut for CDR batch validation.
"""

from scientific.validation.validators import (
    MeasurementValidator,
    ScenarioValidator,
    Severity,
    TowerValidator,
    ValidationError,
    ValidationResult,
    validate_measurement,
    validate_scenario,
    validate_tower,
    ResultValidator,
    cross_validate,
    validate_batch,
    CDRRecordValidator,
    validate_cdr_batch,
)

__all__ = [
    "MeasurementValidator",
    "TowerValidator",
    "ScenarioValidator",
    "ValidationResult",
    "ValidationError",
    "Severity",
    "validate_measurement",
    "validate_tower",
    "validate_scenario",
    "ResultValidator",
    "cross_validate",
    "validate_batch",
    "CDRRecordValidator",
    "validate_cdr_batch",
]

