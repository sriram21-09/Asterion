"""
Validation Types, Protocols, and Core Data Structures
=====================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, TypeVar


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
    code: str | None = None


@dataclass
class ValidationResult:
    """Aggregated result of running one or more validation checks.

    Attributes:
        errors: List of validation findings (errors, warnings, info).
        is_valid: ``True`` if there are no ``ERROR``-severity findings.
    """

    errors: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no ERROR-severity findings exist."""
        return not any(e.severity == Severity.ERROR for e in self.errors)

    @property
    def warnings(self) -> list[ValidationError]:
        """Return only WARNING-severity findings."""
        return [e for e in self.errors if e.severity == Severity.WARNING]

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Merge another result into this one, combining all findings."""
        self.errors.extend(other.errors)
        return self


T = TypeVar("T")


class Validator(Protocol[T]):
    """Protocol that all scientific validators must satisfy."""

    def validate(self, obj: T) -> ValidationResult:
        """Validate *obj* and return a :class:`ValidationResult`."""
        ...  # pragma: no cover


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
