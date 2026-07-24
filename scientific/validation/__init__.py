"""
Scientific Validation Module
==============================

Input validation and data quality components for the scientific engine:

- RSSI range validation (-150 dBm to 0 dBm)
- Coordinate bounds checking (WGS84 lat/lon)
- Measurement consistency checks (timestamps, tower IDs)
- Scenario completeness validation (minimum tower count)
- Data format validators for pipeline inputs
- CDR record validation, duplicate detection, and batch quality scoring

Exports:
    MeasurementValidator: Single-measurement domain validation.
    TowerValidator: Single-tower physics-aware validation.
    ScenarioValidator: Full-scenario structural + deep validation.
    CDRRecordValidator: Single CDR record domain validation.
    CDRValidationService: Batch CDR orchestration + quality scoring.
    CDRValidationReport: Structured report from a batch validation run.
    CDRDataQualityScore: Quantitative quality score (0‒1) with grade.
    ValidationResult: Aggregated validation findings.
    ValidationError: A single validation finding.
    Severity: Error / Warning / Info classification.
    validate_measurement: Convenience shortcut.
    validate_tower: Convenience shortcut.
    validate_scenario: Convenience shortcut.
    validate_cdr_batch: Convenience shortcut for CDR batch validation.
"""

from scientific.validation.validators import (
    CDRDataQualityScore,
    CDRRecordValidator,
    CDRValidationReport,
    CDRValidationService,
    MeasurementValidator,
    ResultValidator,
    ScenarioValidator,
    Severity,
    TowerValidator,
    ValidationError,
    ValidationResult,
    cross_validate,
    validate_batch,
    validate_cdr_batch,
    validate_measurement,
    validate_scenario,
    validate_tower,
<<<<<<< HEAD
    ResultValidator,
    cross_validate,
    validate_batch,
    CDRRecordValidator,
    validate_cdr_batch,
    CDRValidationService,
    CDRValidationReport,
    CDRDataQualityScore,
=======
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
)

__all__ = [
    "CDRDataQualityScore",
    "CDRRecordValidator",
    "CDRValidationReport",
    "CDRValidationService",
    "MeasurementValidator",
    "ResultValidator",
    "ScenarioValidator",
    "Severity",
    "TowerValidator",
    "ValidationError",
    "ValidationResult",
    "cross_validate",
    "validate_batch",
<<<<<<< HEAD
    "CDRRecordValidator",
    "validate_cdr_batch",
    "CDRValidationService",
    "CDRValidationReport",
    "CDRDataQualityScore",
=======
    "validate_cdr_batch",
    "validate_measurement",
    "validate_scenario",
    "validate_tower",
>>>>>>> 563df9fcb5b395c6734dc2284f99456f989bf468
]

