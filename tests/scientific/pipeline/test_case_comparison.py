"""
Unit Tests for Scientific Case Comparison Analysis Engine
================================--------------------------
"""

from datetime import datetime, UTC
from scientific.pipeline.case_comparison import (
    CaseComparisonResult,
    CellOverlapMetrics,
    SpatialCentroidComparison,
    SpeedTrendMetrics,
    calculate_cell_overlap,
    calculate_spatial_centroid_comparison,
    calculate_speed_trends,
    compare_cases,
)
from scientific.pipeline.movement import MovementEvent, MovementSummary


def test_calculate_cell_overlap_identical():
    records_a = [{"first_cgi": "404-10-100-1"}, {"first_cgi": "404-10-100-2"}]
    records_b = [{"first_cgi": "404-10-100-1"}, {"first_cgi": "404-10-100-2"}]

    res = calculate_cell_overlap(records_a, records_b)
    assert isinstance(res, CellOverlapMetrics)
    assert res.overlap_count == 2
    assert res.total_unique_count == 2
    assert res.jaccard_similarity == 1.0
    assert res.overlap_percentage_a == 100.0
    assert res.overlap_percentage_b == 100.0
    assert res.overlapping_cells == ["404-10-100-1", "404-10-100-2"]


def test_calculate_cell_overlap_disjoint():
    records_a = [{"first_cgi": "404-10-100-1"}]
    records_b = [{"first_cgi": "404-10-200-5"}]

    res = calculate_cell_overlap(records_a, records_b)
    assert res.overlap_count == 0
    assert res.total_unique_count == 2
    assert res.jaccard_similarity == 0.0
    assert res.overlap_percentage_a == 0.0
    assert res.overlap_percentage_b == 0.0


def test_calculate_cell_overlap_partial():
    records_a = [
        {"first_cgi": "A"},
        {"first_cgi": "B"},
        {"first_cgi": "C"},
    ]
    records_b = [
        {"first_cgi": "B"},
        {"first_cgi": "C"},
        {"first_cgi": "D"},
    ]

    res = calculate_cell_overlap(records_a, records_b)
    assert res.overlap_count == 2
    assert res.total_unique_count == 4
    assert res.jaccard_similarity == 0.5
    assert res.overlapping_cells == ["B", "C"]
    assert res.unique_cells_a == ["A"]
    assert res.unique_cells_b == ["D"]


def test_calculate_cell_overlap_empty():
    res = calculate_cell_overlap([], [])
    assert res.overlap_count == 0
    assert res.total_unique_count == 0
    assert res.jaccard_similarity == 0.0
    assert res.overlap_percentage_a == 0.0
    assert res.overlap_percentage_b == 0.0


def test_calculate_speed_trends_normal():
    now = datetime.now(UTC)
    movements_a = [
        MovementEvent(sequence=1, timestamp=now, speed_kmh=20.0),
        MovementEvent(sequence=2, timestamp=now, speed_kmh=40.0),
        MovementEvent(sequence=3, timestamp=now, speed_kmh=60.0),
    ]
    movements_b = [
        MovementEvent(sequence=1, timestamp=now, speed_kmh=30.0),
        MovementEvent(sequence=2, timestamp=now, speed_kmh=50.0),
    ]

    res = calculate_speed_trends(movements_a, movements_b)
    assert isinstance(res, SpeedTrendMetrics)
    assert res.mean_speed_a == 40.0
    assert res.mean_speed_b == 40.0
    assert res.speed_difference_mean == 0.0
    assert res.speed_trend_alignment == 1.0


def test_calculate_speed_trends_with_handovers_and_anomalies():
    now = datetime.now(UTC)
    movements_a = [
        MovementEvent(sequence=1, timestamp=now, speed_kmh=0.0, is_handover=True),
        MovementEvent(sequence=2, timestamp=now, speed_kmh=400.0, is_anomalous=True),
    ]
    summary_b = MovementSummary(
        handover_count=3,
        anomaly_count=1,
        events=[
            MovementEvent(sequence=1, timestamp=now, speed_kmh=10.0),
            MovementEvent(sequence=2, timestamp=now, speed_kmh=15.0),
        ],
    )

    res = calculate_speed_trends(movements_a, summary_b)
    assert res.handover_count_a == 1
    assert res.impossible_velocity_count_a == 1
    assert res.handover_count_b == 3
    assert res.impossible_velocity_count_b == 1


def test_calculate_speed_trends_zero_variance():
    res = calculate_speed_trends([], [])
    assert res.mean_speed_a == 0.0
    assert res.mean_speed_b == 0.0
    assert res.speed_difference_mean == 0.0
    assert res.speed_trend_alignment == 1.0


def test_calculate_spatial_centroid_comparison_known_distance():
    # Mumbai (19.076, 72.878) vs Pune (18.520, 73.856) ~148 km
    records_a = [{"latitude": 19.076, "longitude": 72.878}]
    records_b = [{"latitude": 18.520, "longitude": 73.856}]

    res = calculate_spatial_centroid_comparison(records_a, records_b)
    assert isinstance(res, SpatialCentroidComparison)
    assert res.centroid_a == (19.076, 72.878)
    assert res.centroid_b == (18.520, 73.856)
    assert 110000.0 <= res.distance_difference_m <= 130000.0
    assert 110.0 <= res.distance_difference_km <= 130.0


def test_calculate_spatial_centroid_comparison_empty():
    res = calculate_spatial_centroid_comparison([], [])
    assert res.centroid_a is None
    assert res.centroid_b is None
    assert res.distance_difference_m == 0.0
    assert res.bounding_box_overlap_ratio == 0.0


def test_compare_cases_orchestrator():
    recs_a = [
        {
            "latitude": 19.076,
            "longitude": 72.878,
            "first_cgi": "CGI-1",
            "confidence": 0.9,
        },
        {
            "latitude": 19.080,
            "longitude": 72.880,
            "first_cgi": "CGI-2",
            "confidence": 0.95,
        },
    ]
    recs_b = [
        {
            "latitude": 19.076,
            "longitude": 72.878,
            "first_cgi": "CGI-1",
            "confidence": 0.85,
        },
        {
            "latitude": 19.085,
            "longitude": 72.885,
            "first_cgi": "CGI-3",
            "confidence": 0.8,
        },
    ]

    res = compare_cases(recs_a, recs_b, case_a_id="CASE-001", case_b_id="CASE-002")

    assert isinstance(res, CaseComparisonResult)
    assert res.case_a_id == "CASE-001"
    assert res.case_b_id == "CASE-002"
    assert res.cell_overlap.overlap_count == 1
    assert 0.0 <= res.overall_similarity_score <= 1.0
    assert 0.0 <= res.avg_confidence_a <= 1.0
    assert 0.0 <= res.avg_confidence_b <= 1.0
