"""
Unit Tests for Scientific Heatmap Engine
===========================================

Tests cover:
  - Min-Max normalization with zero-variance guard and edge cases.
  - Configurable weight handling and normalization.
  - Per-cell composite probability score S_j calculation.
  - Heatmap computation over pre-aggregated metrics.
  - Spatial grid aggregation for CDRs, measurements, and movement events.
  - Guaranteeing score values are strictly bounded in [0.0, 1.0].
"""

from datetime import datetime, timedelta, UTC
import pytest

from scientific.models.cdr_record import CDRRecord
from scientific.pipeline.heatmap import (
    HeatmapCellScore,
    HeatmapWeights,
    aggregate_grid_heatmap,
    calculate_cell_score,
    compute_heatmap,
    min_max_normalize,
    normalize_confidence,
    normalize_density,
    normalize_dwell_time,
    normalize_transitions,
)


class TestMinMaxNormalize:
    """Test min-max normalization functions and zero-variance guards."""

    def test_standard_normalization_list(self):
        vals = [10.0, 20.0, 30.0, 40.0, 50.0]
        norm = min_max_normalize(vals)
        assert norm == [0.0, 0.25, 0.5, 0.75, 1.0]

    def test_standard_normalization_dict(self):
        vals = {"a": 100.0, "b": 200.0, "c": 300.0}
        norm = min_max_normalize(vals)
        assert norm["a"] == 0.0
        assert norm["b"] == 0.5
        assert norm["c"] == 1.0

    def test_zero_variance_identical_positive(self):
        """All values identical and > 0 -> return 1.0 for all (guard division by zero)."""
        vals = [15.0, 15.0, 15.0]
        norm = min_max_normalize(vals)
        assert norm == [1.0, 1.0, 1.0]

        dict_vals = {"c1": 5.0, "c2": 5.0}
        norm_dict = min_max_normalize(dict_vals)
        assert norm_dict == {"c1": 1.0, "c2": 1.0}

    def test_zero_variance_identical_zeros(self):
        """All values 0.0 -> return 0.0 for all."""
        vals = [0.0, 0.0, 0.0]
        norm = min_max_normalize(vals)
        assert norm == [0.0, 0.0, 0.0]

        dict_vals = {"c1": 0.0, "c2": 0.0}
        norm_dict = min_max_normalize(dict_vals)
        assert norm_dict == {"c1": 0.0, "c2": 0.0}

    def test_single_element(self):
        """Single element input handles min=max without error."""
        assert min_max_normalize([42.0]) == [1.0]
        assert min_max_normalize([0.0]) == [0.0]
        assert min_max_normalize({"x": 10.0}) == {"x": 1.0}

    def test_empty_inputs(self):
        assert min_max_normalize([]) == []
        assert min_max_normalize({}) == {}

    def test_specific_normalizers(self):
        densities = {"c1": 10.0, "c2": 30.0}
        assert normalize_density(densities) == {"c1": 0.0, "c2": 1.0}

        dwells = {"c1": 5.0, "c2": 5.0}
        assert normalize_dwell_time(dwells) == {"c1": 1.0, "c2": 1.0}

        confs = {"c1": 0.6, "c2": 1.0}
        assert normalize_confidence(confs)["c1"] == pytest.approx(0.0)
        assert normalize_confidence(confs)["c2"] == pytest.approx(1.0)

        trans = {"c1": 0.0, "c2": 0.0}
        assert normalize_transitions(trans) == {"c1": 0.0, "c2": 0.0}


class TestHeatmapWeights:
    """Test HeatmapWeights dataclass and normalization."""

    def test_default_weights(self):
        hw = HeatmapWeights()
        assert hw.w1 == 0.35
        assert hw.w2 == 0.30
        assert hw.w3 == 0.20
        assert hw.w4 == 0.15
        assert sum([hw.w1, hw.w2, hw.w3, hw.w4]) == pytest.approx(1.0)

    def test_custom_weights_normalization(self):
        hw = HeatmapWeights(w_density=2.0, w_dwell_time=2.0, w_confidence=1.0, w_transitions=3.0)
        norm_hw = hw.normalized()
        assert norm_hw.w1 == pytest.approx(2.0 / 8.0)
        assert norm_hw.w2 == pytest.approx(2.0 / 8.0)
        assert norm_hw.w3 == pytest.approx(1.0 / 8.0)
        assert norm_hw.w4 == pytest.approx(3.0 / 8.0)
        assert sum([norm_hw.w1, norm_hw.w2, norm_hw.w3, norm_hw.w4]) == pytest.approx(1.0)

    def test_zero_weights_fallback(self):
        hw = HeatmapWeights(0.0, 0.0, 0.0, 0.0)
        norm_hw = hw.normalized()
        assert norm_hw.w1 == 0.25
        assert norm_hw.w2 == 0.25
        assert norm_hw.w3 == 0.25
        assert norm_hw.w4 == 0.25


class TestCellScoreCalculation:
    """Test per-cell score calculation S_j = w1·Norm(Density) + w2·Norm(Dwell) + w3·Norm(Conf) + w4·Norm(Trans)."""

    def test_max_score(self):
        score = calculate_cell_score(1.0, 1.0, 1.0, 1.0)
        assert score == pytest.approx(1.0)

    def test_min_score(self):
        score = calculate_cell_score(0.0, 0.0, 0.0, 0.0)
        assert score == pytest.approx(0.0)

    def test_partial_score(self):
        # Default weights: 0.35, 0.30, 0.20, 0.15
        score = calculate_cell_score(1.0, 0.0, 0.5, 0.0)
        expected = 0.35 * 1.0 + 0.30 * 0.0 + 0.20 * 0.5 + 0.15 * 0.0
        assert score == pytest.approx(expected)

    def test_custom_dict_weights(self):
        weights = {"w1": 0.5, "w2": 0.5, "w3": 0.0, "w4": 0.0}
        score = calculate_cell_score(1.0, 0.5, 1.0, 1.0, weights=weights)
        assert score == pytest.approx(0.75)

    def test_score_bounds(self):
        """Scores must always stay within [0.0, 1.0]."""
        score_high = calculate_cell_score(1.5, 1.2, 2.0, 1.0)
        assert 0.0 <= score_high <= 1.0

        score_low = calculate_cell_score(-0.5, -1.0, 0.0, 0.0)
        assert 0.0 <= score_low <= 1.0


class TestComputeHeatmap:
    """Test compute_heatmap on pre-aggregated cell metrics."""

    def test_compute_heatmap_basic(self):
        cells = [
            {"cell_id": "C1", "latitude": 21.1, "longitude": 72.8, "density": 10, "dwell_time": 100, "confidence": 1.0, "transitions": 1},
            {"cell_id": "C2", "latitude": 21.2, "longitude": 72.9, "density": 30, "dwell_time": 300, "confidence": 0.6, "transitions": 5},
        ]
        results = compute_heatmap(cells)
        assert len(results) == 2
        assert isinstance(results[0], HeatmapCellScore)

        c1 = results[0]
        c2 = results[1]

        # C1 density norm: 0.0, C2 density norm: 1.0
        assert c1.norm_density == pytest.approx(0.0)
        assert c2.norm_density == pytest.approx(1.0)

        # Higher metrics for C2 should yield higher composite score
        assert c2.score > c1.score
        assert 0.0 <= c1.score <= 1.0
        assert 0.0 <= c2.score <= 1.0

    def test_empty_heatmap(self):
        assert compute_heatmap([]) == []


class TestSpatialGridAggregation:
    """Test aggregate_grid_heatmap spatial bucketing and intensity calculation."""

    def test_grid_aggregation_cdrs(self):
        base_time = datetime(2026, 7, 28, 10, 0, 0, tzinfo=UTC)
        records = [
            # 3 records near (21.29, 72.89)
            CDRRecord(
                operator="airtel",
                latitude=21.2930,
                longitude=72.8930,
                duration=30,
                timestamp=base_time,
                first_cgi="404-98-100-1",
            ),
            CDRRecord(
                operator="airtel",
                latitude=21.2932,
                longitude=72.8931,
                duration=60,
                timestamp=base_time + timedelta(minutes=5),
                first_cgi="404-98-100-1",
            ),
            CDRRecord(
                operator="airtel",
                latitude=21.2929,
                longitude=72.8929,
                duration=90,
                timestamp=base_time + timedelta(minutes=10),
                first_cgi="404-98-100-1",
            ),
            # 1 record far away at (21.50, 72.50)
            CDRRecord(
                operator="airtel",
                latitude=21.5000,
                longitude=72.5000,
                duration=10,
                timestamp=base_time + timedelta(minutes=30),
                first_cgi="404-98-200-1",
            ),
        ]

        heatmap = aggregate_grid_heatmap(records, grid_size_deg=0.01)
        assert len(heatmap) == 2

        # Order by score / location check
        hotspot = max(heatmap, key=lambda cell: cell.score)
        assert hotspot.raw_density == 3.0
        assert hotspot.raw_dwell_time == 180.0
        assert hotspot.norm_density == 1.0
        assert hotspot.norm_dwell_time == 1.0

    def test_grid_aggregation_transitions(self):
        base_time = datetime(2026, 7, 28, 10, 0, 0, tzinfo=UTC)
        # Sequence of records moving back and forth between two cells
        records = [
            {"latitude": 21.000, "longitude": 77.000, "timestamp": base_time, "duration": 10},
            {"latitude": 21.100, "longitude": 77.100, "timestamp": base_time + timedelta(minutes=1), "duration": 10},
            {"latitude": 21.000, "longitude": 77.000, "timestamp": base_time + timedelta(minutes=2), "duration": 10},
            {"latitude": 21.100, "longitude": 77.100, "timestamp": base_time + timedelta(minutes=3), "duration": 10},
        ]
        heatmap = aggregate_grid_heatmap(records, grid_size_deg=0.05)
        assert len(heatmap) == 2
        for cell in heatmap:
            assert cell.raw_transitions > 0.0

    def test_single_record_edge_case(self):
        """Single record input must be handled gracefully without division by zero."""
        record = CDRRecord(
            operator="bsnl",
            latitude=22.397,
            longitude=88.439,
            duration=45,
            timestamp=datetime(2026, 7, 28, 10, 0, tzinfo=UTC),
        )
        heatmap = aggregate_grid_heatmap([record])
        assert len(heatmap) == 1
        cell = heatmap[0]
        assert cell.raw_density == 1.0
        assert cell.raw_dwell_time == 45.0
        assert 0.0 <= cell.score <= 1.0

    def test_identical_location_records(self):
        """Multiple records at exact same coordinates handle zero-variance."""
        recs = [
            {"latitude": 20.0, "longitude": 70.0, "duration": 100, "confidence": 1.0},
            {"latitude": 20.0, "longitude": 70.0, "duration": 100, "confidence": 1.0},
        ]
        heatmap = aggregate_grid_heatmap(recs)
        assert len(heatmap) == 1
        cell = heatmap[0]
        assert cell.raw_density == 2.0
        # Norms: density=1.0, dwell=1.0, conf=1.0, trans=0.0 -> score = 0.35+0.30+0.20+0 = 0.85
        assert cell.score == pytest.approx(0.85)


    def test_invalid_records_ignored(self):
        records = [
            {"latitude": None, "longitude": None},
            {"latitude": 21.0, "longitude": 72.0},
        ]
        heatmap = aggregate_grid_heatmap(records)
        assert len(heatmap) == 1
        assert heatmap[0].raw_density == 1.0
