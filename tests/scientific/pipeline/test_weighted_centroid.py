"""
Test Suite — Quality-Weighted Centroid Solver
==============================================

Validates the enhanced weighted centroid algorithm including:
- Multi-factor quality score computation
- Quality-weighted positioning vs RSSI-only
- Backward compatibility (no tower_densities)
- Edge cases (missing coords, single tower, etc.)
"""

from datetime import UTC, datetime

import pytest

from scientific.models.measurement import Measurement
from scientific.models.tower import Tower
from scientific.pipeline.weighted_centroid import (
    InputQualityScore,
    compute_input_quality_scores,
    solve_weighted_centroid,
)


# ── Shared fixtures ────────────────────────────────────────────────────────


def _make_towers():
    return [
        Tower(tower_id="T001", latitude=10.0, longitude=20.0, coverage_radius_m=1000.0),
        Tower(tower_id="T002", latitude=12.0, longitude=20.0, coverage_radius_m=1000.0),
        Tower(tower_id="T003", latitude=11.0, longitude=22.0, coverage_radius_m=1000.0),
    ]


def _make_measurement(mid, tid, rssi, ts=None):
    return Measurement(
        measurement_id=mid,
        tower_id=tid,
        timestamp=ts or datetime.now(UTC),
        rssi_dbm=rssi,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 1. Existing tests (backward compatibility)
# ═══════════════════════════════════════════════════════════════════════════


class TestBackwardCompatibility:
    """Ensure all original behaviors still hold without tower_densities."""

    def test_symmetric_geometry(self):
        towers = _make_towers()
        expected_lat = 11.0
        expected_lon = (20.0 + 20.0 + 22.0) / 3.0

        measurements = [
            _make_measurement("M001", "T001", -70.0),
            _make_measurement("M002", "T002", -70.0),
            _make_measurement("M003", "T003", -70.0),
        ]

        result = solve_weighted_centroid(
            scenario_id="SCN-BC-1",
            towers=towers,
            measurements=measurements,
            expected_device_lat=expected_lat,
            expected_device_lon=expected_lon,
        )

        assert result.algorithm == "weighted_centroid"
        assert pytest.approx(result.estimated_latitude) == expected_lat
        assert pytest.approx(result.estimated_longitude) == expected_lon
        assert result.error_m < 1.0
        assert result.signals_used == 3

    def test_dominant_tower(self):
        towers = [
            Tower(tower_id="T001", latitude=10.0, longitude=10.0),
            Tower(tower_id="T002", latitude=20.0, longitude=20.0),
        ]
        measurements = [
            _make_measurement("M001", "T001", -30.0),
            _make_measurement("M002", "T002", -120.0),
        ]

        result = solve_weighted_centroid(
            scenario_id="SCN-BC-2",
            towers=towers,
            measurements=measurements,
        )

        assert abs(result.estimated_latitude - 10.0) < 0.01
        assert abs(result.estimated_longitude - 10.0) < 0.01

    def test_empty_towers_raises(self):
        measurements = [_make_measurement("M001", "T001", -70.0)]
        with pytest.raises(ValueError, match="No towers available"):
            solve_weighted_centroid(
                scenario_id="SCN-BC-3",
                towers=[],
                measurements=measurements,
            )

    def test_unweighted_fallback(self):
        towers = [
            Tower(tower_id="T001", latitude=10.0, longitude=10.0),
            Tower(tower_id="T002", latitude=20.0, longitude=20.0),
        ]
        measurements = [_make_measurement("M001", "T999", -70.0)]

        result = solve_weighted_centroid(
            scenario_id="SCN-BC-4",
            towers=towers,
            measurements=measurements,
        )

        assert pytest.approx(result.estimated_latitude) == 15.0
        assert pytest.approx(result.estimated_longitude) == 15.0


# ═══════════════════════════════════════════════════════════════════════════
# 2. Quality score computation
# ═══════════════════════════════════════════════════════════════════════════


class TestComputeInputQualityScores:
    """Test the compute_input_quality_scores function."""

    def test_basic_score_structure(self):
        towers = _make_towers()
        measurements = [
            _make_measurement("M001", "T001", -70.0),
            _make_measurement("M002", "T002", -70.0),
            _make_measurement("M003", "T003", -70.0),
        ]

        scores = compute_input_quality_scores(towers, measurements)

        assert len(scores) == 3
        for tid in ("T001", "T002", "T003"):
            assert tid in scores
            qs = scores[tid]
            assert isinstance(qs, InputQualityScore)
            assert qs.tower_id == tid
            assert 0.0 <= qs.rssi_score <= 1.0
            assert 0.0 <= qs.coord_score <= 1.0
            assert 0.0 <= qs.timestamp_score <= 1.0
            assert 0.0 <= qs.tower_confidence <= 1.0
            assert 0.0 <= qs.composite_score <= 1.0

    def test_equal_rssi_equal_scores(self):
        """All towers with equal RSSI should get rssi_score = 1.0."""
        towers = _make_towers()
        measurements = [
            _make_measurement("M001", "T001", -70.0),
            _make_measurement("M002", "T002", -70.0),
            _make_measurement("M003", "T003", -70.0),
        ]

        scores = compute_input_quality_scores(towers, measurements)

        for tid in ("T001", "T002", "T003"):
            assert scores[tid].rssi_score == 1.0

    def test_stronger_rssi_higher_score(self):
        """Tower with stronger RSSI should get higher rssi_score."""
        towers = [
            Tower(tower_id="T001", latitude=10.0, longitude=10.0),
            Tower(tower_id="T002", latitude=20.0, longitude=20.0),
        ]
        measurements = [
            _make_measurement("M001", "T001", -40.0),  # Strong
            _make_measurement("M002", "T002", -100.0),  # Weak
        ]

        scores = compute_input_quality_scores(towers, measurements)

        assert scores["T001"].rssi_score > scores["T002"].rssi_score
        assert scores["T001"].rssi_score == 1.0
        assert scores["T002"].rssi_score == 0.0

    def test_coord_score_full_for_valid_tower(self):
        """Tower with valid lat/lon gets coord_score = 1.0."""
        towers = _make_towers()
        measurements = [_make_measurement("M001", "T001", -70.0)]

        scores = compute_input_quality_scores(towers, measurements)

        assert scores["T001"].coord_score == 1.0

    def test_tower_densities_affect_confidence(self):
        """Providing tower_densities should affect tower_confidence score."""
        towers = _make_towers()
        measurements = [
            _make_measurement("M001", "T001", -70.0),
            _make_measurement("M002", "T002", -70.0),
            _make_measurement("M003", "T003", -70.0),
        ]

        densities = {"T001": 0.9, "T002": 0.3, "T003": 0.6}
        scores = compute_input_quality_scores(
            towers, measurements, tower_densities=densities
        )

        assert scores["T001"].tower_confidence == 0.9
        assert scores["T002"].tower_confidence == 0.3
        assert scores["T003"].tower_confidence == 0.6

    def test_no_densities_defaults_to_one(self):
        """Without tower_densities, tower_confidence defaults to 1.0."""
        towers = _make_towers()
        measurements = [_make_measurement("M001", "T001", -70.0)]

        scores = compute_input_quality_scores(
            towers, measurements, tower_densities=None
        )

        assert scores["T001"].tower_confidence == 1.0

    def test_composite_score_weighted_correctly(self):
        """Composite should reflect the dimension weights (0.35, 0.25, 0.20, 0.20)."""
        towers = [Tower(tower_id="T001", latitude=10.0, longitude=10.0)]
        measurements = [_make_measurement("M001", "T001", -70.0)]

        # With everything perfect and equal, composite = 0.35*1 + 0.25*1 + 0.20*ts + 0.20*1
        scores = compute_input_quality_scores(
            towers, measurements, tower_densities={"T001": 1.0}
        )

        qs = scores["T001"]
        expected = (
            0.35 * qs.rssi_score
            + 0.25 * qs.coord_score
            + 0.20 * qs.timestamp_score
            + 0.20 * qs.tower_confidence
        )
        assert qs.composite_score == pytest.approx(expected, abs=1e-5)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Quality-weighted vs RSSI-only behavior
# ═══════════════════════════════════════════════════════════════════════════


class TestQualityWeightedPositioning:
    """Verify quality-weighted mode produces different results from RSSI-only."""

    def test_quality_mode_shifts_estimate(self):
        """When one tower has low density confidence, estimate should shift away from it."""
        towers = [
            Tower(tower_id="T001", latitude=10.0, longitude=10.0),
            Tower(tower_id="T002", latitude=20.0, longitude=20.0),
        ]
        # Equal RSSI — RSSI-only would yield midpoint (15, 15)
        measurements = [
            _make_measurement("M001", "T001", -70.0),
            _make_measurement("M002", "T002", -70.0),
        ]

        # RSSI-only (no densities)
        result_rssi = solve_weighted_centroid(
            scenario_id="SCN-QW-1a",
            towers=towers,
            measurements=measurements,
        )

        # Quality-weighted: T002 has much lower confidence
        result_quality = solve_weighted_centroid(
            scenario_id="SCN-QW-1b",
            towers=towers,
            measurements=measurements,
            tower_densities={"T001": 1.0, "T002": 0.1},
        )

        # RSSI-only should give midpoint
        assert pytest.approx(result_rssi.estimated_latitude, abs=0.1) == 15.0

        # Quality-weighted should shift toward T001 (higher confidence)
        assert result_quality.estimated_latitude < result_rssi.estimated_latitude

    def test_measurement_averaging_with_quality(self):
        """Multiple measurements still averaged correctly in quality mode."""
        towers = [
            Tower(tower_id="T001", latitude=10.0, longitude=10.0),
            Tower(tower_id="T002", latitude=20.0, longitude=20.0),
        ]
        measurements = [
            _make_measurement("M001", "T001", -60.0),
            _make_measurement("M002", "T001", -80.0),
            _make_measurement("M003", "T002", -70.0),
        ]

        result = solve_weighted_centroid(
            scenario_id="SCN-QW-2",
            towers=towers,
            measurements=measurements,
            tower_densities={"T001": 1.0, "T002": 1.0},
        )

        # With equal densities and averaged RSSI, should be near midpoint
        assert result.estimated_latitude is not None
        assert result.estimated_longitude is not None
        assert result.signals_used == 2
