"""
Pipeline Validation Benchmark Tests
=====================================

Comprehensive test suite for the pipeline validation benchmark engine.
Uses deterministic synthetic datasets (Bangalore/Delhi region towers)
to verify metric accuracy, edge cases, and reproducibility.
"""

import pytest

from scientific.pipeline.benchmarks import (
    BenchmarkMetrics,
    CoordinateAccuracyResult,
    calculate_kalman_improvement_factor,
    calculate_tower_resolution_rate,
    calculate_unknown_tower_pct_by_operator,
    calculate_validation_pass_rate,
    evaluate_coordinate_accuracy,
    run_pipeline_benchmarks,
)


# ---------------------------------------------------------------------------
# Synthetic Test Datasets — Deterministic, Hardcoded
# ---------------------------------------------------------------------------

# Reference towers (known ground truth) — Bangalore region
REFERENCE_TOWERS = [
    {"tower_id": "BLR-001", "latitude": 12.9716, "longitude": 77.5946},
    {"tower_id": "BLR-002", "latitude": 12.9352, "longitude": 77.6245},
    {"tower_id": "BLR-003", "latitude": 12.9698, "longitude": 77.7500},
    {"tower_id": "BLR-004", "latitude": 13.0358, "longitude": 77.5970},
    {"tower_id": "BLR-005", "latitude": 12.9141, "longitude": 77.6411},
]

# Computed towers (pipeline output) — slight offsets from reference
COMPUTED_TOWERS = [
    {"tower_id": "BLR-001", "latitude": 12.9720, "longitude": 77.5950},  # ~55m offset
    {"tower_id": "BLR-002", "latitude": 12.9360, "longitude": 77.6240},  # ~102m offset
    {"tower_id": "BLR-003", "latitude": 12.9700, "longitude": 77.7510},  # ~111m offset
    {"tower_id": "BLR-004", "latitude": 13.0400, "longitude": 77.6000},  # ~553m offset
    {"tower_id": "BLR-005", "latitude": 12.9141, "longitude": 77.6411},  # 0m (exact)
]

# Tower resolution data — mixed resolution methods and operators
TOWER_DATA = [
    {"tower_id": "T-001", "resolution_method": "exact", "operator": "Airtel"},
    {"tower_id": "T-002", "resolution_method": "exact", "operator": "Airtel"},
    {"tower_id": "T-003", "resolution_method": "prefix_lac", "operator": "Jio"},
    {"tower_id": "T-004", "resolution_method": "prefix_mnc", "operator": "Jio"},
    {"tower_id": "T-005", "resolution_method": "unresolved", "operator": "BSNL"},
    {"tower_id": "T-006", "resolution_method": "exact", "operator": "BSNL"},
    {"tower_id": "T-007", "resolution_method": "unresolved", "operator": "Vi"},
    {"tower_id": "T-008", "resolution_method": "unresolved", "operator": "Vi"},
    {"tower_id": "T-009", "resolution_method": "prefix_mcc", "operator": "Airtel"},
    {"tower_id": "T-010", "resolution_method": "exact", "operator": "Jio"},
]


# ---------------------------------------------------------------------------
# Test: Coordinate Accuracy Evaluation
# ---------------------------------------------------------------------------


class TestCoordinateAccuracy:
    """Tests for evaluate_coordinate_accuracy()."""

    def test_basic_accuracy_evaluation(self):
        """Per-tower error distances are computed correctly."""
        results = evaluate_coordinate_accuracy(
            REFERENCE_TOWERS, COMPUTED_TOWERS, threshold_m=500.0,
        )

        assert len(results) == 5

        # All results are CoordinateAccuracyResult instances
        for r in results:
            assert isinstance(r, CoordinateAccuracyResult)
            assert r.error_distance_m >= 0.0

    def test_exact_match_zero_error(self):
        """Identical reference and computed coordinates yield zero error."""
        results = evaluate_coordinate_accuracy(
            REFERENCE_TOWERS, COMPUTED_TOWERS, threshold_m=500.0,
        )

        # BLR-005 has identical coordinates
        blr005 = next(r for r in results if r.tower_id == "BLR-005")
        assert blr005.error_distance_m == 0.0
        assert blr005.is_within_threshold is True

    def test_threshold_pass_fail(self):
        """Towers above threshold are correctly flagged."""
        results = evaluate_coordinate_accuracy(
            REFERENCE_TOWERS, COMPUTED_TOWERS, threshold_m=500.0,
        )

        # BLR-004 has ~553m offset → should exceed 500m threshold
        blr004 = next(r for r in results if r.tower_id == "BLR-004")
        assert blr004.error_distance_m > 500.0
        assert blr004.is_within_threshold is False

        # BLR-001 has ~55m offset → within threshold
        blr001 = next(r for r in results if r.tower_id == "BLR-001")
        assert blr001.error_distance_m < 500.0
        assert blr001.is_within_threshold is True

    def test_unmatched_towers_skipped(self):
        """Reference towers without a computed match are skipped."""
        ref = [{"tower_id": "MISSING-001", "latitude": 12.0, "longitude": 77.0}]
        results = evaluate_coordinate_accuracy(ref, COMPUTED_TOWERS, threshold_m=500.0)
        assert len(results) == 0

    def test_empty_inputs(self):
        """Empty reference or computed lists return empty results."""
        assert evaluate_coordinate_accuracy([], COMPUTED_TOWERS) == []
        assert evaluate_coordinate_accuracy(REFERENCE_TOWERS, []) == []
        assert evaluate_coordinate_accuracy([], []) == []

    def test_custom_threshold(self):
        """Custom threshold changes pass/fail classification."""
        # With tight 50m threshold, fewer towers pass
        results_tight = evaluate_coordinate_accuracy(
            REFERENCE_TOWERS, COMPUTED_TOWERS, threshold_m=50.0,
        )
        passed_tight = sum(1 for r in results_tight if r.is_within_threshold)

        # With loose 1000m threshold, more towers pass
        results_loose = evaluate_coordinate_accuracy(
            REFERENCE_TOWERS, COMPUTED_TOWERS, threshold_m=1000.0,
        )
        passed_loose = sum(1 for r in results_loose if r.is_within_threshold)

        assert passed_loose >= passed_tight

    def test_error_distances_positive(self):
        """All computed error distances are non-negative."""
        results = evaluate_coordinate_accuracy(
            REFERENCE_TOWERS, COMPUTED_TOWERS, threshold_m=500.0,
        )
        for r in results:
            assert r.error_distance_m >= 0.0

    def test_reference_and_computed_coords_preserved(self):
        """Original reference and computed coords are stored in results."""
        results = evaluate_coordinate_accuracy(
            REFERENCE_TOWERS, COMPUTED_TOWERS, threshold_m=500.0,
        )
        blr001 = next(r for r in results if r.tower_id == "BLR-001")
        assert blr001.reference_latitude == 12.9716
        assert blr001.reference_longitude == 77.5946
        assert blr001.computed_latitude == 12.9720
        assert blr001.computed_longitude == 77.5950


# ---------------------------------------------------------------------------
# Test: Validation Pass Rate
# ---------------------------------------------------------------------------


class TestValidationPassRate:
    """Tests for calculate_validation_pass_rate()."""

    def test_normal_ratio(self):
        """Standard validated/total calculation."""
        rate = calculate_validation_pass_rate(85, 100)
        assert rate == pytest.approx(0.85, abs=1e-6)

    def test_all_validated(self):
        """All records validated → rate = 1.0."""
        rate = calculate_validation_pass_rate(200, 200)
        assert rate == pytest.approx(1.0, abs=1e-6)

    def test_none_validated(self):
        """No records validated → rate = 0.0."""
        rate = calculate_validation_pass_rate(0, 100)
        assert rate == pytest.approx(0.0, abs=1e-6)

    def test_zero_total_guard(self):
        """Zero total records → rate = 0.0 (no division by zero)."""
        rate = calculate_validation_pass_rate(0, 0)
        assert rate == 0.0

    def test_negative_total_guard(self):
        """Negative total records → rate = 0.0."""
        rate = calculate_validation_pass_rate(5, -1)
        assert rate == 0.0

    def test_fractional_rate(self):
        """Non-round validation ratio is precise to 6 decimal places."""
        rate = calculate_validation_pass_rate(1, 3)
        assert rate == pytest.approx(1 / 3, abs=1e-6)


# ---------------------------------------------------------------------------
# Test: Tower Resolution Rate
# ---------------------------------------------------------------------------


class TestTowerResolutionRate:
    """Tests for calculate_tower_resolution_rate()."""

    def test_mixed_resolution_methods(self):
        """Known + Estimated towers counted correctly."""
        rate = calculate_tower_resolution_rate(TOWER_DATA)
        # 4 exact + 2 prefix_lac/mnc + 1 prefix_mcc = 7 resolved out of 10
        assert rate == pytest.approx(7 / 10, abs=1e-6)

    def test_all_exact(self):
        """All towers exactly resolved → rate = 1.0."""
        data = [
            {"tower_id": "T-1", "resolution_method": "exact"},
            {"tower_id": "T-2", "resolution_method": "exact"},
        ]
        assert calculate_tower_resolution_rate(data) == pytest.approx(1.0, abs=1e-6)

    def test_all_unresolved(self):
        """All towers unresolved → rate = 0.0."""
        data = [
            {"tower_id": "T-1", "resolution_method": "unresolved"},
            {"tower_id": "T-2", "resolution_method": "unresolved"},
        ]
        assert calculate_tower_resolution_rate(data) == pytest.approx(0.0, abs=1e-6)

    def test_empty_tower_list(self):
        """Empty tower list → rate = 0.0."""
        assert calculate_tower_resolution_rate([]) == 0.0

    def test_prefix_methods_counted_as_estimated(self):
        """prefix_lac, prefix_mnc, prefix_mcc all count as resolved."""
        data = [
            {"tower_id": "T-1", "resolution_method": "prefix_lac"},
            {"tower_id": "T-2", "resolution_method": "prefix_mnc"},
            {"tower_id": "T-3", "resolution_method": "prefix_mcc"},
        ]
        assert calculate_tower_resolution_rate(data) == pytest.approx(1.0, abs=1e-6)

    def test_missing_resolution_method_treated_as_unknown(self):
        """Missing resolution_method key defaults to unresolved."""
        data = [
            {"tower_id": "T-1"},
            {"tower_id": "T-2", "resolution_method": "exact"},
        ]
        assert calculate_tower_resolution_rate(data) == pytest.approx(0.5, abs=1e-6)


# ---------------------------------------------------------------------------
# Test: Unknown Tower Percentage by Operator
# ---------------------------------------------------------------------------


class TestUnknownTowerPctByOperator:
    """Tests for calculate_unknown_tower_pct_by_operator()."""

    def test_multi_operator_grouping(self):
        """Per-operator unknown percentages are correctly computed."""
        result = calculate_unknown_tower_pct_by_operator(TOWER_DATA)

        # Airtel: 3 towers, 0 unresolved → 0%
        assert result["Airtel"] == pytest.approx(0.0, abs=0.01)

        # Jio: 3 towers, 0 unresolved → 0%
        assert result["Jio"] == pytest.approx(0.0, abs=0.01)

        # BSNL: 2 towers, 1 unresolved → 50%
        assert result["BSNL"] == pytest.approx(50.0, abs=0.01)

        # Vi: 2 towers, 2 unresolved → 100%
        assert result["Vi"] == pytest.approx(100.0, abs=0.01)

    def test_operator_with_zero_unknown(self):
        """Operator with all resolved towers → 0.0%."""
        data = [
            {"tower_id": "T-1", "resolution_method": "exact", "operator": "TestOp"},
            {"tower_id": "T-2", "resolution_method": "prefix_lac", "operator": "TestOp"},
        ]
        result = calculate_unknown_tower_pct_by_operator(data)
        assert result["TestOp"] == 0.0

    def test_operator_with_all_unknown(self):
        """Operator with all unresolved towers → 100.0%."""
        data = [
            {"tower_id": "T-1", "resolution_method": "unresolved", "operator": "BadOp"},
            {"tower_id": "T-2", "resolution_method": "unresolved", "operator": "BadOp"},
        ]
        result = calculate_unknown_tower_pct_by_operator(data)
        assert result["BadOp"] == 100.0

    def test_empty_tower_list(self):
        """Empty tower list returns empty dict."""
        assert calculate_unknown_tower_pct_by_operator([]) == {}

    def test_missing_operator_defaults_to_unknown(self):
        """Missing operator key defaults to 'Unknown'."""
        data = [
            {"tower_id": "T-1", "resolution_method": "unresolved"},
        ]
        result = calculate_unknown_tower_pct_by_operator(data)
        assert "Unknown" in result
        assert result["Unknown"] == 100.0


# ---------------------------------------------------------------------------
# Test: Kalman Improvement Factor
# ---------------------------------------------------------------------------


class TestKalmanImprovementFactor:
    """Tests for calculate_kalman_improvement_factor()."""

    def test_improvement_detected(self):
        """Factor > 1.0 when smoothed errors are smaller than raw."""
        raw = [100.0, 200.0, 150.0, 250.0, 180.0]
        smoothed = [50.0, 80.0, 60.0, 90.0, 70.0]

        factor = calculate_kalman_improvement_factor(raw, smoothed)

        # mean(raw) = 176.0, mean(smoothed) = 70.0 → factor ≈ 2.514
        assert factor > 1.0
        assert factor == pytest.approx(176.0 / 70.0, abs=1e-4)

    def test_no_improvement_clamped(self):
        """Factor clamped to 1.0 when smoothed is worse than raw."""
        raw = [50.0, 60.0, 40.0]
        smoothed = [100.0, 120.0, 90.0]

        factor = calculate_kalman_improvement_factor(raw, smoothed)
        assert factor == 1.0

    def test_equal_errors(self):
        """Equal raw and smoothed errors → factor = 1.0."""
        raw = [100.0, 200.0]
        smoothed = [100.0, 200.0]

        factor = calculate_kalman_improvement_factor(raw, smoothed)
        assert factor == 1.0

    def test_empty_raw_errors(self):
        """Empty raw errors → factor = 1.0."""
        factor = calculate_kalman_improvement_factor([], [50.0, 60.0])
        assert factor == 1.0

    def test_empty_smoothed_errors(self):
        """Empty smoothed errors → factor = 1.0."""
        factor = calculate_kalman_improvement_factor([100.0, 200.0], [])
        assert factor == 1.0

    def test_both_empty(self):
        """Both empty → factor = 1.0."""
        factor = calculate_kalman_improvement_factor([], [])
        assert factor == 1.0

    def test_zero_smoothed_mean_guard(self):
        """Zero smoothed mean → factor = 1.0 (no division by zero)."""
        factor = calculate_kalman_improvement_factor([100.0], [0.0])
        assert factor == 1.0

    def test_single_element_lists(self):
        """Single-element lists work correctly."""
        factor = calculate_kalman_improvement_factor([200.0], [100.0])
        assert factor == pytest.approx(2.0, abs=1e-6)

    def test_large_improvement(self):
        """Very large improvement factor is not artificially capped."""
        raw = [1000.0, 2000.0, 1500.0]
        smoothed = [10.0, 20.0, 15.0]

        factor = calculate_kalman_improvement_factor(raw, smoothed)
        assert factor == pytest.approx(100.0, abs=1e-4)


# ---------------------------------------------------------------------------
# Test: Determinism — Every metric must be identical across runs
# ---------------------------------------------------------------------------


class TestDeterminism:
    """Verify that all benchmark calculations are deterministic."""

    def test_coordinate_accuracy_deterministic(self):
        """evaluate_coordinate_accuracy returns identical results across 5 runs."""
        results = [
            evaluate_coordinate_accuracy(REFERENCE_TOWERS, COMPUTED_TOWERS, 500.0)
            for _ in range(5)
        ]
        for i in range(1, 5):
            assert len(results[i]) == len(results[0])
            for a, b in zip(results[0], results[i]):
                assert a.tower_id == b.tower_id
                assert a.error_distance_m == b.error_distance_m
                assert a.is_within_threshold == b.is_within_threshold

    def test_validation_pass_rate_deterministic(self):
        """calculate_validation_pass_rate returns identical results across 5 runs."""
        results = [calculate_validation_pass_rate(85, 100) for _ in range(5)]
        assert all(r == results[0] for r in results)

    def test_tower_resolution_rate_deterministic(self):
        """calculate_tower_resolution_rate returns identical results across 5 runs."""
        results = [calculate_tower_resolution_rate(TOWER_DATA) for _ in range(5)]
        assert all(r == results[0] for r in results)

    def test_unknown_pct_deterministic(self):
        """calculate_unknown_tower_pct_by_operator returns identical results across 5 runs."""
        results = [
            calculate_unknown_tower_pct_by_operator(TOWER_DATA)
            for _ in range(5)
        ]
        assert all(r == results[0] for r in results)

    def test_kalman_factor_deterministic(self):
        """calculate_kalman_improvement_factor returns identical results across 5 runs."""
        raw = [100.0, 200.0, 150.0]
        smoothed = [50.0, 80.0, 60.0]
        results = [
            calculate_kalman_improvement_factor(raw, smoothed)
            for _ in range(5)
        ]
        assert all(r == results[0] for r in results)

    def test_full_benchmarks_deterministic(self):
        """run_pipeline_benchmarks returns identical BenchmarkMetrics across 5 runs."""
        kwargs = dict(
            validated_records=85,
            total_records=100,
            tower_data=TOWER_DATA,
            reference_towers=REFERENCE_TOWERS,
            computed_towers=COMPUTED_TOWERS,
            raw_errors=[100.0, 200.0, 150.0],
            smoothed_errors=[50.0, 80.0, 60.0],
            accuracy_threshold_m=500.0,
        )
        results = [run_pipeline_benchmarks(**kwargs) for _ in range(5)]

        for i in range(1, 5):
            assert results[i].validation_pass_rate == results[0].validation_pass_rate
            assert results[i].tower_resolution_rate == results[0].tower_resolution_rate
            assert results[i].kalman_improvement_factor == results[0].kalman_improvement_factor
            assert results[i].mean_error_m == results[0].mean_error_m
            assert results[i].median_error_m == results[0].median_error_m
            assert results[i].max_error_m == results[0].max_error_m
            assert results[i].accuracy_within_threshold_pct == results[0].accuracy_within_threshold_pct


# ---------------------------------------------------------------------------
# Test: End-to-End Orchestrator
# ---------------------------------------------------------------------------


class TestRunPipelineBenchmarks:
    """Tests for run_pipeline_benchmarks()."""

    def test_full_benchmark_suite(self):
        """Orchestrator returns populated BenchmarkMetrics with all fields."""
        metrics = run_pipeline_benchmarks(
            validated_records=85,
            total_records=100,
            tower_data=TOWER_DATA,
            reference_towers=REFERENCE_TOWERS,
            computed_towers=COMPUTED_TOWERS,
            raw_errors=[100.0, 200.0, 150.0, 250.0, 180.0],
            smoothed_errors=[50.0, 80.0, 60.0, 90.0, 70.0],
            accuracy_threshold_m=500.0,
        )

        assert isinstance(metrics, BenchmarkMetrics)

        # Validation pass rate
        assert metrics.validation_pass_rate == pytest.approx(0.85, abs=1e-6)

        # Tower resolution rate (7/10 = 0.7)
        assert metrics.tower_resolution_rate == pytest.approx(0.7, abs=1e-6)

        # Kalman improvement factor > 1.0
        assert metrics.kalman_improvement_factor > 1.0

        # Coordinate accuracy results populated
        assert len(metrics.coordinate_accuracy_results) == 5

        # Aggregate accuracy stats are populated
        assert metrics.mean_error_m > 0.0
        assert metrics.median_error_m > 0.0
        assert metrics.max_error_m > 0.0

        # Accuracy threshold is preserved
        assert metrics.accuracy_threshold_m == 500.0

        # Within-threshold percentage is between 0 and 100
        assert 0.0 <= metrics.accuracy_within_threshold_pct <= 100.0

    def test_minimal_inputs(self):
        """Orchestrator handles minimal/empty inputs gracefully."""
        metrics = run_pipeline_benchmarks()

        assert metrics.validation_pass_rate == 0.0
        assert metrics.tower_resolution_rate == 0.0
        assert metrics.unknown_tower_pct_by_operator == {}
        assert metrics.kalman_improvement_factor == 1.0
        assert metrics.coordinate_accuracy_results == []
        assert metrics.mean_error_m == 0.0
        assert metrics.median_error_m == 0.0
        assert metrics.max_error_m == 0.0
        assert metrics.accuracy_within_threshold_pct == 0.0

    def test_unknown_pct_populated(self):
        """Per-operator unknown tower percentages are populated."""
        metrics = run_pipeline_benchmarks(
            tower_data=TOWER_DATA,
        )

        assert "Airtel" in metrics.unknown_tower_pct_by_operator
        assert "BSNL" in metrics.unknown_tower_pct_by_operator
        assert "Vi" in metrics.unknown_tower_pct_by_operator
        assert "Jio" in metrics.unknown_tower_pct_by_operator

    def test_custom_accuracy_threshold(self):
        """Custom threshold propagates to accuracy evaluation."""
        metrics_tight = run_pipeline_benchmarks(
            reference_towers=REFERENCE_TOWERS,
            computed_towers=COMPUTED_TOWERS,
            accuracy_threshold_m=50.0,
        )
        metrics_loose = run_pipeline_benchmarks(
            reference_towers=REFERENCE_TOWERS,
            computed_towers=COMPUTED_TOWERS,
            accuracy_threshold_m=1000.0,
        )

        assert metrics_tight.accuracy_threshold_m == 50.0
        assert metrics_loose.accuracy_threshold_m == 1000.0
        assert metrics_loose.accuracy_within_threshold_pct >= metrics_tight.accuracy_within_threshold_pct

    def test_benchmark_metrics_is_frozen(self):
        """BenchmarkMetrics instances are immutable (frozen dataclass)."""
        metrics = run_pipeline_benchmarks(
            validated_records=50,
            total_records=100,
        )
        with pytest.raises(AttributeError):
            metrics.validation_pass_rate = 0.99  # type: ignore[misc]

    def test_coordinate_accuracy_result_is_frozen(self):
        """CoordinateAccuracyResult instances are immutable (frozen dataclass)."""
        metrics = run_pipeline_benchmarks(
            reference_towers=REFERENCE_TOWERS,
            computed_towers=COMPUTED_TOWERS,
        )
        if metrics.coordinate_accuracy_results:
            with pytest.raises(AttributeError):
                metrics.coordinate_accuracy_results[0].error_distance_m = 0.0  # type: ignore[misc]
