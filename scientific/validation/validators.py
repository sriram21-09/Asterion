"""
Scientific Validation Interfaces & Validators (Facade)
======================================================

Provides modularized validators and re-exports all interfaces, data models,
and validator classes for 100% backwards compatibility across the project.
"""

from __future__ import annotations

from scientific.validation.cdr_validator import (
    CDRDataQualityScore,
    CDRRecordValidator,
    CDRValidationReport,
    CDRValidationService,
    validate_cdr_batch,
)
from scientific.validation.measurement_validator import MeasurementValidator
from scientific.validation.result_validator import ResultValidator, cross_validate
from scientific.validation.scenario_validator import (
    ScenarioValidator,
    validate_batch,
    validate_measurement,
    validate_scenario,
    validate_tower,
)
from scientific.validation.tower_validator import TowerValidator
from scientific.validation.types import (
    CELLULAR_BANDS_MHZ,
    Severity,
    ValidationError,
    ValidationResult,
    Validator,
)

__all__ = [
    "Severity",
    "ValidationError",
    "ValidationResult",
    "Validator",
    "CELLULAR_BANDS_MHZ",
    "MeasurementValidator",
    "TowerValidator",
    "ScenarioValidator",
    "ResultValidator",
    "cross_validate",
    "validate_measurement",
    "validate_tower",
    "validate_scenario",
    "validate_batch",
    "CDRRecordValidator",
    "validate_cdr_batch",
    "CDRDataQualityScore",
    "CDRValidationReport",
    "CDRValidationService",
]
