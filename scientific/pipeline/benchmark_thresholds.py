"""
Calibrated Benchmark Thresholds
================================

Defines calibrated pipeline validation thresholds derived from the real
Asterion operator datasets (Airtel, BSNL, Jio, Vi).  These thresholds
serve as documented acceptance criteria for pipeline benchmark runs.

The ``BenchmarkThresholdConfig`` frozen dataclass stores every threshold
value, and ``verify_benchmark_compliance()`` produces a structured
pass/fail report by comparing a :class:`BenchmarkMetrics` instance
against the calibrated thresholds.

Usage::

    >>> from scientific.pipeline.benchmark_thresholds import (
    ...     CALIBRATED_THRESHOLDS,
    ...     verify_benchmark_compliance,
    ... )
    >>> from scientific.pipeline.benchmarks import run_pipeline_benchmarks
    >>> metrics = run_pipeline_benchmarks(validated_records=85, total_records=100)
    >>> report = verify_benchmark_compliance(metrics)
    >>> report["overall_pass"]
    True
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scientific.pipeline.benchmarks import BenchmarkMetrics


@dataclass(frozen=True)
class BenchmarkThresholdConfig:
    """Calibrated benchmark thresholds for Asterion pipeline validation.

    All values are derived from empirical analysis of the four operator
    datasets (Airtel, BSNL, Jio, Vi) and tuned to provide meaningful
    quality gates without rejecting legitimate edge-case behaviour.

    Attributes:
        coordinate_accuracy_threshold_m: Maximum acceptable error
            distance between reference and computed tower coordinates
            (meters).  Default 500.0 m aligns with urban cell-radius
            expectations.
        coordinate_accuracy_acceptable_pct: Minimum percentage of
            evaluated towers that must fall within the accuracy
            threshold.  Default ≥80%.
        min_validation_pass_rate: Minimum fraction of CDR records that
            must pass validation (0.0–1.0).  Default ≥0.70.
        min_tower_resolution_rate: Minimum fraction of towers resolved
            via exact or prefix fallback (0.0–1.0).  Default ≥0.60.
        max_unknown_tower_pct_per_operator: Maximum acceptable unknown
            tower percentage for any single operator (0.0–100.0).
            Default ≤40%.
        min_kalman_improvement_factor: Kalman smoothing must not
            degrade accuracy; factor must be ≥1.0.
        confidence_score_min: Lower bound for confidence scores.
        confidence_score_max: Upper bound for confidence scores.
        evidence_hash_length: Expected length of SHA-256 hex digest.
    """

    # Coordinate accuracy
    coordinate_accuracy_threshold_m: float = 500.0
    coordinate_accuracy_acceptable_pct: float = 80.0

    # Validation pass rate
    min_validation_pass_rate: float = 0.70

    # Tower resolution
    min_tower_resolution_rate: float = 0.60
    max_unknown_tower_pct_per_operator: float = 40.0

    # Kalman filter
    min_kalman_improvement_factor: float = 1.0

    # Confidence bounds
    confidence_score_min: float = 0.0
    confidence_score_max: float = 1.0

    # Evidence hash
    evidence_hash_length: int = 64  # SHA-256 hex digest


#: Default calibrated thresholds — single importable instance.
CALIBRATED_THRESHOLDS = BenchmarkThresholdConfig()


def verify_benchmark_compliance(
    metrics: BenchmarkMetrics,
    thresholds: BenchmarkThresholdConfig | None = None,
) -> dict[str, Any]:
    """Verify pipeline benchmark metrics against calibrated thresholds.

    Produces a structured report with per-check pass/fail status and
    an overall compliance verdict.

    Args:
        metrics: The benchmark metrics to verify (from
            :func:`run_pipeline_benchmarks`).
        thresholds: Optional override thresholds.  Defaults to
            :data:`CALIBRATED_THRESHOLDS`.

    Returns:
        A dictionary containing:
            - ``overall_pass`` (bool): ``True`` if all checks pass.
            - ``checks`` (list[dict]): Per-check details with keys
              ``name``, ``passed``, ``actual``, ``threshold``,
              ``description``.
    """
    cfg = thresholds or CALIBRATED_THRESHOLDS
    checks: list[dict[str, Any]] = []

    # 1. Validation pass rate
    checks.append(
        {
            "name": "validation_pass_rate",
            "passed": metrics.validation_pass_rate >= cfg.min_validation_pass_rate,
            "actual": metrics.validation_pass_rate,
            "threshold": cfg.min_validation_pass_rate,
            "description": (
                f"Validation pass rate ≥ {cfg.min_validation_pass_rate:.0%}"
            ),
        }
    )

    # 2. Tower resolution rate
    checks.append(
        {
            "name": "tower_resolution_rate",
            "passed": metrics.tower_resolution_rate >= cfg.min_tower_resolution_rate,
            "actual": metrics.tower_resolution_rate,
            "threshold": cfg.min_tower_resolution_rate,
            "description": (
                f"Tower resolution rate ≥ {cfg.min_tower_resolution_rate:.0%}"
            ),
        }
    )

    # 3. Per-operator unknown tower percentage
    for operator, pct in metrics.unknown_tower_pct_by_operator.items():
        op_pass = pct <= cfg.max_unknown_tower_pct_per_operator
        checks.append(
            {
                "name": f"unknown_tower_pct_{operator}",
                "passed": op_pass,
                "actual": pct,
                "threshold": cfg.max_unknown_tower_pct_per_operator,
                "description": (
                    f"{operator} unknown tower % ≤ "
                    f"{cfg.max_unknown_tower_pct_per_operator:.0f}%"
                ),
            }
        )

    # 4. Kalman improvement factor
    checks.append(
        {
            "name": "kalman_improvement_factor",
            "passed": (
                metrics.kalman_improvement_factor >= cfg.min_kalman_improvement_factor
            ),
            "actual": metrics.kalman_improvement_factor,
            "threshold": cfg.min_kalman_improvement_factor,
            "description": (
                f"Kalman improvement factor ≥ {cfg.min_kalman_improvement_factor}"
            ),
        }
    )

    # 5. Coordinate accuracy within threshold (only if results exist)
    if metrics.coordinate_accuracy_results:
        checks.append(
            {
                "name": "coordinate_accuracy_within_threshold",
                "passed": (
                    metrics.accuracy_within_threshold_pct
                    >= cfg.coordinate_accuracy_acceptable_pct
                ),
                "actual": metrics.accuracy_within_threshold_pct,
                "threshold": cfg.coordinate_accuracy_acceptable_pct,
                "description": (
                    f"≥{cfg.coordinate_accuracy_acceptable_pct:.0f}% of towers "
                    f"within {cfg.coordinate_accuracy_threshold_m:.0f}m"
                ),
            }
        )

    # 6. Accuracy threshold alignment
    checks.append(
        {
            "name": "accuracy_threshold_alignment",
            "passed": (
                metrics.accuracy_threshold_m == cfg.coordinate_accuracy_threshold_m
            ),
            "actual": metrics.accuracy_threshold_m,
            "threshold": cfg.coordinate_accuracy_threshold_m,
            "description": (
                f"Accuracy threshold matches calibrated "
                f"{cfg.coordinate_accuracy_threshold_m:.0f}m"
            ),
        }
    )

    overall_pass = all(c["passed"] for c in checks)

    return {
        "overall_pass": overall_pass,
        "checks": checks,
        "total_checks": len(checks),
        "passed_checks": sum(1 for c in checks if c["passed"]),
        "failed_checks": sum(1 for c in checks if not c["passed"]),
    }
