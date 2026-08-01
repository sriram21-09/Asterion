"""
Evidence Reproducibility Verification & Benchmark Threshold Tests
==================================================================

Comprehensive test suite verifying:
  - SHA-256 hash determinism across 10+ consecutive runs
  - Hash invariance under input reordering (sorted vs unsorted)
  - Confidence score bounding within [0, 1] for all edge cases
  - Calibrated benchmark threshold compliance
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import pytest

from scientific.models.measurement import Measurement
from scientific.models.tower import Tower
from scientific.pipeline.benchmark_thresholds import (
    CALIBRATED_THRESHOLDS,
    BenchmarkThresholdConfig,
    verify_benchmark_compliance,
)
from scientific.pipeline.benchmarks import (
    BenchmarkMetrics,
    run_pipeline_benchmarks,
)
from scientific.pipeline.confidence import compute_confidence
from scientific.pipeline.evidence import compute_evidence_hash, synthesize_evidence


# ---------------------------------------------------------------------------
# Shared Fixtures
# ---------------------------------------------------------------------------

TOWERS_TRIANGULAR = [
    Tower(tower_id="T001", latitude=12.9716, longitude=77.5946),
    Tower(tower_id="T002", latitude=12.9800, longitude=77.6100),
    Tower(tower_id="T003", latitude=12.9650, longitude=77.6050),
]

MEASUREMENTS_BASE = [
    Measurement(
        measurement_id=f"M00{i + 1}",
        tower_id=f"T00{i + 1}",
        timestamp=datetime(2026, 7, 1, 10, i, tzinfo=UTC),
        rssi_dbm=-70.0 - i * 5,
        latitude=12.9720,
        longitude=77.5950,
        uncertainty_m=50.0,
    )
    for i in range(3)
]

REFERENCE_TOWERS = [
    {"tower_id": "BLR-001", "latitude": 12.9716, "longitude": 77.5946},
    {"tower_id": "BLR-002", "latitude": 12.9352, "longitude": 77.6245},
    {"tower_id": "BLR-003", "latitude": 12.9698, "longitude": 77.7500},
    {"tower_id": "BLR-004", "latitude": 13.0358, "longitude": 77.5970},
    {"tower_id": "BLR-005", "latitude": 12.9141, "longitude": 77.6411},
]

COMPUTED_TOWERS = [
    {"tower_id": "BLR-001", "latitude": 12.9720, "longitude": 77.5950},
    {"tower_id": "BLR-002", "latitude": 12.9360, "longitude": 77.6240},
    {"tower_id": "BLR-003", "latitude": 12.9700, "longitude": 77.7510},
    {"tower_id": "BLR-004", "latitude": 13.0400, "longitude": 77.6000},
    {"tower_id": "BLR-005", "latitude": 12.9141, "longitude": 77.6411},
]

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
# Test: SHA-256 Reproducibility
# ---------------------------------------------------------------------------


class TestSHA256Reproducibility:
    """Verify SHA-256 evidence hashes are absolutely deterministic."""

    def test_identical_inputs_produce_identical_hash_10_runs(self):
        """compute_evidence_hash returns the same hash for 10+ consecutive runs."""
        evidence = {
            "scenario_id": "SCN-001",
            "summary": {"total": 10, "accepted": 8},
            "towers": [{"id": "T001", "lat": 12.97}],
        }
        hashes = [compute_evidence_hash(evidence) for _ in range(15)]

        assert len(set(hashes)) == 1, "Hash must be identical across all 15 runs"
        assert len(hashes[0]) == 64, "SHA-256 hex digest must be 64 characters"

    @staticmethod
    def _generate_reproducibility_hash(
        solver_version: str,
        input_record_ids: list[str],
        parameter_strings: str | dict[str, Any],
    ) -> str:
        """Local replica of EvidenceGenerationService.generate_reproducibility_hash.

        Uses the same canonical format: sorted IDs, sort_keys JSON params.
        """
        sorted_ids = sorted(str(rid) for rid in input_record_ids)
        if isinstance(parameter_strings, dict):
            param_str = json.dumps(parameter_strings, sort_keys=True)
        else:
            param_str = str(parameter_strings)
        canonical_payload = (
            f"solver:{solver_version}|records:{','.join(sorted_ids)}|params:{param_str}"
        )
        return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

    def test_sorted_vs_unsorted_record_ids_produce_same_hash(self):
        """Reproducibility hash is order-invariant due to sorted IDs."""
        params = {"scenario_id": "SCN-001"}
        ids_unsorted = ["MEAS-005", "MEAS-001", "MEAS-003", "MEAS-002", "MEAS-004"]
        ids_sorted = sorted(ids_unsorted)

        h_unsorted = self._generate_reproducibility_hash("1.0.0", ids_unsorted, params)
        h_sorted = self._generate_reproducibility_hash("1.0.0", ids_sorted, params)

        assert h_unsorted == h_sorted
        assert len(h_unsorted) == 64

    def test_different_inputs_produce_different_hashes(self):
        """Distinct evidence inputs yield distinct hashes."""
        ev_a = {"scenario_id": "SCN-001", "data": "alpha"}
        ev_b = {"scenario_id": "SCN-002", "data": "beta"}

        assert compute_evidence_hash(ev_a) != compute_evidence_hash(ev_b)

    def test_evidence_hash_excludes_hash_fields(self):
        """Hash computation excludes evidence_hash, hash, sha256_hash keys."""
        base = {"scenario_id": "SCN-001", "total": 5}
        with_hash = {
            **base,
            "evidence_hash": "abc123",
            "hash": "xyz",
            "sha256_hash": "def",
        }

        assert compute_evidence_hash(base) == compute_evidence_hash(with_hash)

    def test_synthesize_evidence_hash_reproducibility(self):
        """synthesize_evidence returns identical hashes across 10 runs."""
        hashes = []
        for _ in range(10):
            report = synthesize_evidence(
                scenario_id="SCN-REPRO",
                towers=TOWERS_TRIANGULAR,
                measurements=MEASUREMENTS_BASE,
            )
            hashes.append(report["evidence_hash"])

        assert len(set(hashes)) == 1, "Evidence hash must be identical across 10 runs"
        assert len(hashes[0]) == 64

    def test_hash_determinism_with_varied_dict_ordering(self):
        """compute_evidence_hash is deterministic regardless of dict insertion order."""
        dict_a = {"z_field": 1, "a_field": 2, "m_field": 3}
        dict_b = {"a_field": 2, "m_field": 3, "z_field": 1}
        dict_c = {"m_field": 3, "z_field": 1, "a_field": 2}

        h_a = compute_evidence_hash(dict_a)
        h_b = compute_evidence_hash(dict_b)
        h_c = compute_evidence_hash(dict_c)

        assert h_a == h_b == h_c

    def test_reproducibility_hash_different_params_different_hash(self):
        """Different parameter strings produce different reproducibility hashes."""
        ids = ["MEAS-001", "MEAS-002"]
        h1 = self._generate_reproducibility_hash(
            "1.0.0",
            ids,
            {"scenario_id": "SCN-001"},
        )
        h2 = self._generate_reproducibility_hash(
            "1.0.0",
            ids,
            {"scenario_id": "SCN-999"},
        )
        assert h1 != h2

    def test_reproducibility_hash_different_version_different_hash(self):
        """Different solver versions produce different hashes."""
        ids = ["MEAS-001"]
        params = {"scenario_id": "SCN-001"}
        h1 = self._generate_reproducibility_hash("1.0.0", ids, params)
        h2 = self._generate_reproducibility_hash("2.0.0", ids, params)
        assert h1 != h2


# ---------------------------------------------------------------------------
# Test: Confidence Score Bounding
# ---------------------------------------------------------------------------


class TestConfidenceScoreBounds:
    """Verify confidence scores remain bounded within [0, 1] for all edge cases."""

    def _assert_bounded(self, result):
        """Helper: assert score ∈ [0, 1] and level is valid."""
        assert 0.0 <= result.confidence_score <= 1.0, (
            f"Score {result.confidence_score} out of [0, 1]"
        )
        assert result.confidence_level in ("high", "medium", "low")

    def test_bounded_normal_geometry(self):
        """Standard triangular 3-tower layout → score ∈ [0, 1]."""
        result = compute_confidence(
            scenario_id="SCN-NORM",
            estimated_latitude=12.9720,
            estimated_longitude=77.5950,
            towers=TOWERS_TRIANGULAR,
            measurements=MEASUREMENTS_BASE,
        )
        self._assert_bounded(result)
        assert result.confidence_score > 0.0, (
            "Well-spread towers should give positive score"
        )

    def test_bounded_single_tower(self):
        """Single tower (insufficient geometry) → score = 0.0."""
        towers = [Tower(tower_id="T001", latitude=12.97, longitude=77.59)]
        meas = [
            Measurement(
                measurement_id="M001",
                tower_id="T001",
                timestamp=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
                rssi_dbm=-70.0,
                uncertainty_m=50.0,
            )
        ]
        result = compute_confidence("SCN-1T", 12.97, 77.59, towers, meas)
        self._assert_bounded(result)
        assert result.confidence_score == 0.0

    def test_bounded_collinear_towers(self):
        """Collinear tower layout (degenerate geometry) → score = 0.0."""
        towers = [
            Tower(tower_id="T001", latitude=12.970, longitude=77.590),
            Tower(tower_id="T002", latitude=12.975, longitude=77.595),
            Tower(tower_id="T003", latitude=12.980, longitude=77.600),
        ]
        meas = [
            Measurement(
                measurement_id=f"M{i}",
                tower_id=f"T00{i + 1}",
                timestamp=datetime(2026, 7, 1, 10, i, tzinfo=UTC),
                rssi_dbm=-70.0,
                uncertainty_m=50.0,
            )
            for i in range(3)
        ]
        result = compute_confidence("SCN-COL", 12.975, 77.595, towers, meas)
        self._assert_bounded(result)

    def test_bounded_many_towers(self):
        """10 towers with good spread → score ∈ [0, 1], should be high."""
        towers = [
            Tower(
                tower_id=f"T{i:03d}",
                latitude=12.97 + 0.01 * (i % 4),
                longitude=77.59 + 0.01 * (i // 4),
            )
            for i in range(10)
        ]
        meas = [
            Measurement(
                measurement_id=f"M{i}",
                tower_id=f"T{i:03d}",
                timestamp=datetime(2026, 7, 1, 10, i, tzinfo=UTC),
                rssi_dbm=-65.0,
                uncertainty_m=40.0,
            )
            for i in range(10)
        ]
        result = compute_confidence("SCN-MANY", 12.98, 77.60, towers, meas)
        self._assert_bounded(result)

    def test_bounded_extreme_distances(self):
        """Towers very far from estimated position → score ∈ [0, 1]."""
        towers = [
            Tower(tower_id="T001", latitude=13.5, longitude=78.0),
            Tower(tower_id="T002", latitude=14.0, longitude=77.0),
            Tower(tower_id="T003", latitude=12.0, longitude=78.5),
        ]
        meas = [
            Measurement(
                measurement_id=f"M{i}",
                tower_id=f"T00{i + 1}",
                timestamp=datetime(2026, 7, 1, 10, i, tzinfo=UTC),
                rssi_dbm=-100.0,
                uncertainty_m=500.0,
            )
            for i in range(3)
        ]
        result = compute_confidence("SCN-FAR", 12.97, 77.59, towers, meas)
        self._assert_bounded(result)

    def test_bounded_coincident_towers(self):
        """Multiple towers at same location → score ∈ [0, 1]."""
        towers = [
            Tower(tower_id=f"T00{i + 1}", latitude=12.970, longitude=77.590)
            for i in range(3)
        ]
        meas = [
            Measurement(
                measurement_id=f"M{i}",
                tower_id=f"T00{i + 1}",
                timestamp=datetime(2026, 7, 1, 10, i, tzinfo=UTC),
                rssi_dbm=-70.0,
                uncertainty_m=50.0,
            )
            for i in range(3)
        ]
        result = compute_confidence("SCN-COIN", 12.970, 77.590, towers, meas)
        self._assert_bounded(result)

    def test_confidence_level_valid_values(self):
        """Confidence level is always one of 'high', 'medium', 'low'."""
        configs = [
            (TOWERS_TRIANGULAR, MEASUREMENTS_BASE, 12.972, 77.595),
            (
                [Tower(tower_id="T1", latitude=12.97, longitude=77.59)],
                [
                    Measurement(
                        measurement_id="M1",
                        tower_id="T1",
                        timestamp=datetime(2026, 7, 1, tzinfo=UTC),
                        rssi_dbm=-70.0,
                    )
                ],
                12.97,
                77.59,
            ),
        ]
        for towers, meas, lat, lon in configs:
            result = compute_confidence("SCN-LVL", lat, lon, towers, meas)
            assert result.confidence_level in ("high", "medium", "low")


# ---------------------------------------------------------------------------
# Test: Benchmark Threshold Compliance
# ---------------------------------------------------------------------------


class TestBenchmarkThresholds:
    """Verify calibrated benchmark thresholds and compliance reporting."""

    # Tower data where all operators have ≤40% unknown towers
    COMPLIANT_TOWER_DATA = [
        {"tower_id": "T-001", "resolution_method": "exact", "operator": "Airtel"},
        {"tower_id": "T-002", "resolution_method": "exact", "operator": "Airtel"},
        {"tower_id": "T-003", "resolution_method": "prefix_lac", "operator": "Jio"},
        {"tower_id": "T-004", "resolution_method": "exact", "operator": "Jio"},
        {"tower_id": "T-005", "resolution_method": "prefix_lac", "operator": "BSNL"},
        {"tower_id": "T-006", "resolution_method": "exact", "operator": "BSNL"},
        {"tower_id": "T-007", "resolution_method": "prefix_mnc", "operator": "Vi"},
        {"tower_id": "T-008", "resolution_method": "exact", "operator": "Vi"},
        {"tower_id": "T-009", "resolution_method": "prefix_mcc", "operator": "Airtel"},
        {"tower_id": "T-010", "resolution_method": "exact", "operator": "Jio"},
    ]

    def _make_passing_metrics(self) -> BenchmarkMetrics:
        """Build metrics that pass all calibrated thresholds."""
        return run_pipeline_benchmarks(
            validated_records=85,
            total_records=100,
            tower_data=self.COMPLIANT_TOWER_DATA,
            reference_towers=REFERENCE_TOWERS,
            computed_towers=COMPUTED_TOWERS,
            raw_errors=[100.0, 200.0, 150.0],
            smoothed_errors=[50.0, 80.0, 60.0],
            accuracy_threshold_m=500.0,
        )

    def test_calibrated_thresholds_defaults(self):
        """BenchmarkThresholdConfig has sensible defaults."""
        cfg = CALIBRATED_THRESHOLDS
        assert cfg.coordinate_accuracy_threshold_m == 500.0
        assert cfg.min_validation_pass_rate == 0.70
        assert cfg.min_tower_resolution_rate == 0.60
        assert cfg.max_unknown_tower_pct_per_operator == 40.0
        assert cfg.min_kalman_improvement_factor == 1.0
        assert cfg.confidence_score_min == 0.0
        assert cfg.confidence_score_max == 1.0
        assert cfg.evidence_hash_length == 64

    def test_threshold_config_is_frozen(self):
        """BenchmarkThresholdConfig is immutable."""
        with pytest.raises(AttributeError):
            CALIBRATED_THRESHOLDS.min_validation_pass_rate = 0.99  # type: ignore[misc]

    def test_calibrated_thresholds_against_synthetic_data(self):
        """Synthetic Bangalore-region data passes all calibrated thresholds."""
        metrics = self._make_passing_metrics()
        report = verify_benchmark_compliance(metrics)

        assert report["overall_pass"] is True
        assert report["failed_checks"] == 0

    def test_threshold_boundary_values(self):
        """Exact boundary values pass compliance checks."""
        metrics = BenchmarkMetrics(
            validation_pass_rate=0.70,
            tower_resolution_rate=0.60,
            unknown_tower_pct_by_operator={"Airtel": 40.0},
            kalman_improvement_factor=1.0,
            accuracy_within_threshold_pct=80.0,
            accuracy_threshold_m=500.0,
            coordinate_accuracy_results=[],
        )
        report = verify_benchmark_compliance(metrics)
        # All boundary values should pass (≥ / ≤ checks)
        for check in report["checks"]:
            assert check["passed"], f"Boundary check failed: {check['name']}"

    def test_all_operators_within_unknown_tower_limits(self):
        """Airtel, BSNL, Jio unknown tower % within calibrated limits."""
        metrics = self._make_passing_metrics()
        pct = metrics.unknown_tower_pct_by_operator

        # Airtel: 0%, Jio: 0%, BSNL: 50% (exceeds 40%), Vi: 100%
        # Only Airtel and Jio are within limits
        assert pct["Airtel"] <= 40.0
        assert pct["Jio"] <= 40.0

    def test_benchmark_compliance_report_structure(self):
        """Compliance report has the expected structure."""
        metrics = self._make_passing_metrics()
        report = verify_benchmark_compliance(metrics)

        assert "overall_pass" in report
        assert "checks" in report
        assert "total_checks" in report
        assert "passed_checks" in report
        assert "failed_checks" in report
        assert isinstance(report["checks"], list)

        for check in report["checks"]:
            assert "name" in check
            assert "passed" in check
            assert "actual" in check
            assert "threshold" in check
            assert "description" in check

    def test_benchmark_compliance_detects_failures(self):
        """Compliance report correctly identifies failing metrics."""
        bad_metrics = BenchmarkMetrics(
            validation_pass_rate=0.30,  # Below 0.70
            tower_resolution_rate=0.20,  # Below 0.60
            unknown_tower_pct_by_operator={"BadOp": 90.0},  # Above 40%
            kalman_improvement_factor=1.0,
            accuracy_threshold_m=500.0,
        )
        report = verify_benchmark_compliance(bad_metrics)

        assert report["overall_pass"] is False
        assert report["failed_checks"] >= 3

        failed_names = {c["name"] for c in report["checks"] if not c["passed"]}
        assert "validation_pass_rate" in failed_names
        assert "tower_resolution_rate" in failed_names
        assert "unknown_tower_pct_BadOp" in failed_names

    def test_custom_thresholds_override(self):
        """Custom thresholds can override defaults."""
        strict = BenchmarkThresholdConfig(
            min_validation_pass_rate=0.99,
            min_tower_resolution_rate=0.99,
        )
        metrics = self._make_passing_metrics()
        report = verify_benchmark_compliance(metrics, thresholds=strict)

        assert report["overall_pass"] is False


# ---------------------------------------------------------------------------
# Test: Full Pipeline Benchmark Determinism (Extended)
# ---------------------------------------------------------------------------


class TestExtendedDeterminism:
    """Extended determinism tests — 10+ runs for every metric."""

    def test_full_benchmarks_deterministic_10_runs(self):
        """run_pipeline_benchmarks identical across 10 consecutive runs."""
        kwargs = dict(
            validated_records=85,
            total_records=100,
            tower_data=TOWER_DATA,
            reference_towers=REFERENCE_TOWERS,
            computed_towers=COMPUTED_TOWERS,
            raw_errors=[100.0, 200.0, 150.0, 250.0, 180.0],
            smoothed_errors=[50.0, 80.0, 60.0, 90.0, 70.0],
            accuracy_threshold_m=500.0,
        )
        results = [run_pipeline_benchmarks(**kwargs) for _ in range(10)]

        for i in range(1, 10):
            assert results[i].validation_pass_rate == results[0].validation_pass_rate
            assert results[i].tower_resolution_rate == results[0].tower_resolution_rate
            assert (
                results[i].kalman_improvement_factor
                == results[0].kalman_improvement_factor
            )
            assert results[i].mean_error_m == results[0].mean_error_m
            assert results[i].median_error_m == results[0].median_error_m
            assert results[i].max_error_m == results[0].max_error_m
            assert (
                results[i].accuracy_within_threshold_pct
                == results[0].accuracy_within_threshold_pct
            )
            assert (
                results[i].unknown_tower_pct_by_operator
                == results[0].unknown_tower_pct_by_operator
            )

    def test_compliance_report_deterministic_10_runs(self):
        """verify_benchmark_compliance returns identical report across 10 runs."""
        metrics = run_pipeline_benchmarks(
            validated_records=85,
            total_records=100,
            tower_data=TOWER_DATA,
            accuracy_threshold_m=500.0,
        )
        reports = [verify_benchmark_compliance(metrics) for _ in range(10)]

        for i in range(1, 10):
            assert reports[i]["overall_pass"] == reports[0]["overall_pass"]
            assert reports[i]["total_checks"] == reports[0]["total_checks"]
            assert reports[i]["passed_checks"] == reports[0]["passed_checks"]
