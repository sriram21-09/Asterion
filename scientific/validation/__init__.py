"""
Scientific Validation Module
==============================

Input validation and data quality components for the scientific engine:

- RSSI range validation (-150 dBm to 0 dBm)
- Coordinate bounds checking (WGS84 lat/lon)
- Measurement consistency checks (timestamps, tower IDs)
- Scenario completeness validation (minimum tower count)
- Data format validators for pipeline inputs

Exports:
    MeasurementValidator: Single-measurement domain validation.
    TowerValidator: Single-tower physics-aware validation.
    ScenarioValidator: Full-scenario structural + deep validation.
    ValidationResult: Aggregated validation findings.
    ValidationError: A single validation finding.
    Severity: Error / Warning / Info classification.
    validate_measurement: Convenience shortcut.
    validate_tower: Convenience shortcut.
    validate_scenario: Convenience shortcut.
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
]
