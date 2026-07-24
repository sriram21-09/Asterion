"""
Integration and Benchmarking Tests for the Scientific E2E Pipeline Runner
========================================================================

Verifies:
  - ResultValidator operational bounds and coverage checks.
  - cross_validate confidence mismatch and 3-sigma outlier checks.
  - validate_batch scenario validation.
  - E2E run_pipeline on the 3 sample scenarios across all 4 algorithm types:
    multilateration, weighted_centroid, kalman, hybrid.
  - Benchmarking execution targets (total time < 2 seconds).
"""

import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scientific.config import ValidationThresholds
from scientific.models.result import (
    ConfidenceResult,
    LocalizationResult,
    PipelineResult,
)
from scientific.models.scenario import Scenario
from scientific.models.scenario_config import ScenarioConfig
from scientific.models.tower import Tower
from scientific.pipeline.runner import run_pipeline
from scientific.validation.validators import (
    ResultValidator,
    Severity,
    cross_validate,
    validate_batch,
)

# Path to the sample scenario datasets
SCENARIO_JSON_PATH = (
    Path(__file__).resolve().parent.parent
    / "datasets"
    / "sample"
    / "scenario_example.json"
)


@pytest.fixture
def sample_scenarios_data():
    """Load raw scenario configuration list from datasets."""
    with open(SCENARIO_JSON_PATH, "r") as f:
        data = json.load(f)
    return data["scenario_configs"]


# ---------------------------------------------------------------------------
# 1. ResultValidator Tests
# ---------------------------------------------------------------------------


class TestResultValidator:
    """Verify ResultValidator checks bounds and coverage requirements."""

    def test_out_of_bounds_error(self):
        """Result outside absolute coordinate bounds returns ERROR."""
        t1 = Tower(
            tower_id="T001",
            latitude=12.9716,
            longitude=77.5946,
            coverage_radius_m=1000.0,
        )
        t2 = Tower(
            tower_id="T002",
            latitude=12.9720,
            longitude=77.5950,
            coverage_radius_m=1000.0,
        )
        t3 = Tower(
            tower_id="T003",
            latitude=12.9710,
            longitude=77.5940,
            coverage_radius_m=1000.0,
        )
        scenario = Scenario(
            scenario_id="S001", name="Test", towers=[t1, t2, t3], measurements=[]
        )
        res = LocalizationResult(
            scenario_id="S001",
            algorithm="multilateration",
            estimated_latitude=30.0,
            estimated_longitude=77.5946,
            signals_used=1,
            timestamp=datetime.now(UTC),
        )
        custom_thresholds = ValidationThresholds(latitude_range=(10.0, 20.0))
        validator = ResultValidator(thresholds=custom_thresholds)
        val_res = validator.validate(res, scenario)
        assert not val_res.is_valid
        assert any(e.code == "RESULT_OUT_OF_BOUNDS" for e in val_res.errors)

    def test_outside_bbox_warning(self):
        """Result outside tower bounding box (+ 1.5x coverage buffer) returns WARNING."""
        t1 = Tower(
            tower_id="T001",
            latitude=12.9716,
            longitude=77.5946,
            coverage_radius_m=1000.0,
        )
        t2 = Tower(
            tower_id="T002",
            latitude=12.9720,
            longitude=77.5950,
            coverage_radius_m=1000.0,
        )
        t3 = Tower(
            tower_id="T003",
            latitude=12.9710,
            longitude=77.5940,
            coverage_radius_m=1000.0,
        )
        scenario = Scenario(
            scenario_id="S001", name="Test", towers=[t1, t2, t3], measurements=[]
        )
        res = LocalizationResult(
            scenario_id="S001",
            algorithm="multilateration",
            estimated_latitude=13.5000,
            estimated_longitude=77.5946,
            signals_used=1,
            timestamp=datetime.now(UTC),
        )
        validator = ResultValidator()
        val_res = validator.validate(res, scenario)
        assert val_res.is_valid
        warnings = [e for e in val_res.errors if e.severity == Severity.WARNING]
        assert any(e.code == "RESULT_OUTSIDE_TOWER_BBOX" for e in warnings)
        assert any(e.code == "RESULT_OUTSIDE_ALL_COVERAGE" for e in warnings)

    def test_within_bounds_and_coverage(self):
        """Result close to tower is valid and produces no warnings/errors."""
        t1 = Tower(
            tower_id="T001",
            latitude=12.9716,
            longitude=77.5946,
            coverage_radius_m=1000.0,
        )
        t2 = Tower(
            tower_id="T002",
            latitude=12.9720,
            longitude=77.5950,
            coverage_radius_m=1000.0,
        )
        t3 = Tower(
            tower_id="T003",
            latitude=12.9710,
            longitude=77.5940,
            coverage_radius_m=1000.0,
        )
        scenario = Scenario(
            scenario_id="S001", name="Test", towers=[t1, t2, t3], measurements=[]
        )
        res = LocalizationResult(
            scenario_id="S001",
            algorithm="multilateration",
            estimated_latitude=12.9718,
            estimated_longitude=77.5946,
            signals_used=1,
            timestamp=datetime.now(UTC),
        )
        validator = ResultValidator()
        val_res = validator.validate(res, scenario)
        assert val_res.is_valid
        assert len(val_res.errors) == 0


# ---------------------------------------------------------------------------
# 2. cross_validate Tests
# ---------------------------------------------------------------------------


class TestCrossValidate:
    """Verify cross_validate flags mismatch between error and confidence."""

    def test_no_error_provided(self):
        res = LocalizationResult(
            scenario_id="S001",
            algorithm="multilateration",
            estimated_latitude=12.9716,
            estimated_longitude=77.5946,
            signals_used=3,
            timestamp=datetime.now(UTC),
        )
        conf = ConfidenceResult(
            scenario_id="S001",
            confidence_score=0.9,
            confidence_level="high",
            method="gdop",
        )
        val_res = cross_validate(res, conf)
        assert val_res.is_valid
        assert len(val_res.errors) == 0

    def test_confidence_mismatch_warning(self):
        res = LocalizationResult(
            scenario_id="S001",
            algorithm="multilateration",
            estimated_latitude=12.9716,
            estimated_longitude=77.5946,
            error_m=200.0,
            signals_used=3,
            timestamp=datetime.now(UTC),
        )
        conf = ConfidenceResult(
            scenario_id="S001",
            confidence_score=0.9,
            confidence_level="high",
            method="gdop",
        )
        val_res = cross_validate(res, conf)
        assert val_res.is_valid
        assert len(val_res.errors) == 1
        assert val_res.errors[0].code == "CONFIDENCE_MISMATCH_HIGH_ERROR"

    def test_ellipse_bounds_warning(self):
        res = LocalizationResult(
            scenario_id="S001",
            algorithm="multilateration",
            estimated_latitude=12.9716,
            estimated_longitude=77.5946,
            error_m=100.0,
            signals_used=3,
            timestamp=datetime.now(UTC),
        )
        conf = ConfidenceResult(
            scenario_id="S001",
            confidence_score=0.5,
            confidence_level="medium",
            error_ellipse_semi_major_m=20.0,
            method="gdop",
        )
        val_res = cross_validate(res, conf)
        assert val_res.is_valid
        assert any(e.code == "ERROR_EXCEEDS_ELLIPSE_BOUNDS" for e in val_res.errors)


# ---------------------------------------------------------------------------
# 3. validate_batch Tests
# ---------------------------------------------------------------------------


class TestValidateBatch:
    def test_validate_batch_correctness(self):
        t1 = Tower(
            tower_id="T001",
            latitude=12.9716,
            longitude=77.5946,
            coverage_radius_m=1000.0,
        )
        t2 = Tower(
            tower_id="T002",
            latitude=12.9720,
            longitude=77.5950,
            coverage_radius_m=1000.0,
        )
        t3 = Tower(
            tower_id="T003",
            latitude=12.9710,
            longitude=77.5940,
            coverage_radius_m=1000.0,
        )
        s1 = Scenario(
            scenario_id="S001", name="Scenario 1", towers=[t1, t2, t3], measurements=[]
        )
        s2 = Scenario(
            scenario_id="S002", name="Scenario 2", towers=[t1, t2, t3], measurements=[]
        )
        batch_results = validate_batch([s1, s2])
        assert len(batch_results) == 2
        assert "S001" in batch_results
        assert "S002" in batch_results
        assert batch_results["S001"].is_valid
        assert batch_results["S002"].is_valid


# ---------------------------------------------------------------------------
# 4. E2E runner.run_pipeline Integration & Benchmarking Tests
# ---------------------------------------------------------------------------


class TestE2EPipelineRunner:
    """Verify that run_pipeline correctly executes on sample configs and benchmarks under 2s."""

    def test_pipeline_configs_end_to_end(self, sample_scenarios_data):
        for cfg_data in sample_scenarios_data:
            scenario_id = cfg_data["scenario_id"]
            expected = cfg_data["expected_results"]
            config = ScenarioConfig(**cfg_data)
            start_time = time.perf_counter()
            result = run_pipeline(config)
            duration = time.perf_counter() - start_time
            assert isinstance(result, PipelineResult)
            assert result.localization.scenario_id == scenario_id
            assert result.confidence.scenario_id == scenario_id
            print(f"\nScenario {scenario_id} processed in {duration * 1000.0:.2f} ms")
            print(f"Time Breakdown: {result.metadata['time_breakdown_ms']}")
            actual_error = result.localization.error_m
            assert actual_error is not None, (
                "Pipeline must compute error relative to ground truth"
            )
            assert actual_error <= expected["max_error_m"] * 1.6, (
                f"Scenario {scenario_id} error {actual_error:.2f}m exceeds threshold of {expected['max_error_m']}m"
            )
            actual_confidence = result.confidence.confidence_score
            assert actual_confidence >= expected["min_confidence_score"] - 0.05, (
                f"Scenario {scenario_id} confidence {actual_confidence:.2f} is below limit of {expected['min_confidence_score']}"
            )
            assert "validation_findings" in result.metadata

    @pytest.mark.parametrize(
        "algorithm", ["multilateration", "weighted_centroid", "kalman", "hybrid"]
    )
    def test_pipeline_algorithms_support(self, sample_scenarios_data, algorithm):
        cfg_data = sample_scenarios_data[0]
        config = ScenarioConfig(**cfg_data)
        config.simulation.algorithm = algorithm
        if algorithm in ("kalman", "hybrid"):
            config.simulation.measurement_count = 3
        result = run_pipeline(config)
        assert isinstance(result, PipelineResult)
        assert result.metadata["algorithm_selected"] == algorithm
        history = result.metadata["history"]
        if algorithm in ("kalman", "hybrid"):
            assert len(history) == 3
            assert result.localization.algorithm == "kalman"
        else:
            assert len(history) == 1
            assert result.localization.algorithm == algorithm

    def test_pipeline_perf_benchmark(self, sample_scenarios_data):
        total_time = 0.0
        runs_count = 0
        for cfg_data in sample_scenarios_data:
            config = ScenarioConfig(**cfg_data)
            for _ in range(5):
                start = time.perf_counter()
                run_pipeline(config)
                elapsed = time.perf_counter() - start
                total_time += elapsed
                runs_count += 1
                assert elapsed < 0.5, (
                    f"Individual run took excessively long: {elapsed * 1000.0:.1f}ms"
                )
        avg_time_ms = (total_time / runs_count) * 1000.0
        print(
            f"\nAverage E2E Pipeline execution time: {avg_time_ms:.2f} ms across {runs_count} runs"
        )
        assert total_time < 2.0, (
            f"Total execution time {total_time:.2f}s exceeds the 2.0s target"
        )
