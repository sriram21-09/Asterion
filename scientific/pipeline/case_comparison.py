"""
Scientific Case Comparison Analysis Engine
===========================================

Provides pure-function analytics for comparing two or more telecom investigation
cases side-by-side based on Section 6 (Day 10) of the Asterion Master Execution Plan:

1. **Cell Sector Overlap** — Jaccard similarity, intersection/union count, and case-relative percentages.
2. **Speed & Mobility Trend Analysis** — Statistical speed summaries (mean, max, median, std), handover counts, velocity anomalies, and speed profile alignment score.
3. **Spatial Centroid Proximity** — Geodesic distance between case centroids (WGS84), bounding box intersection/union ratios.
4. **Data Confidence Comparison** — Quality and tower confidence score deltas.
5. **Composite Similarity Index** — Bounded similarity score S_sim in [0.0, 1.0].
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import mean, median, stdev
from typing import Any

from scientific.logger import get_logger

logger = get_logger(__name__)
from scientific.pipeline.movement import (
    MovementEvent,
    MovementSummary,
    calculate_distance_m,
    reconstruct_movement_events,
)

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CellOverlapMetrics:
    """Metrics quantifying cell/sector overlap between two cases.

    Attributes:
        overlapping_cells: List of unique cell/sector IDs present in both cases.
        unique_cells_a: List of unique cell/sector IDs present only in Case A.
        unique_cells_b: List of unique cell/sector IDs present only in Case B.
        overlap_count: Number of shared cells/sectors.
        total_unique_count: Total unique cells across both cases.
        jaccard_similarity: Jaccard similarity index in [0.0, 1.0].
        overlap_percentage_a: Percentage of Case A cells shared with Case B (0–100%).
        overlap_percentage_b: Percentage of Case B cells shared with Case A (0–100%).
    """

    overlapping_cells: list[str] = field(default_factory=list)
    unique_cells_a: list[str] = field(default_factory=list)
    unique_cells_b: list[str] = field(default_factory=list)
    overlap_count: int = 0
    total_unique_count: int = 0
    jaccard_similarity: float = 0.0
    overlap_percentage_a: float = 0.0
    overlap_percentage_b: float = 0.0


@dataclass(frozen=True)
class SpeedTrendMetrics:
    """Metrics comparing velocity distribution and movement speed trends.

    Attributes:
        mean_speed_a: Mean speed in km/h for Case A.
        mean_speed_b: Mean speed in km/h for Case B.
        max_speed_a: Peak speed in km/h for Case A.
        max_speed_b: Peak speed in km/h for Case B.
        median_speed_a: Median speed in km/h for Case A.
        median_speed_b: Median speed in km/h for Case B.
        std_speed_a: Standard deviation of speed in km/h for Case A.
        std_speed_b: Standard deviation of speed in km/h for Case B.
        speed_difference_mean: Absolute difference between mean speeds in km/h.
        speed_trend_alignment: Profile alignment score in [0.0, 1.0].
        handover_count_a: Total same-site handovers in Case A.
        handover_count_b: Total same-site handovers in Case B.
        impossible_velocity_count_a: Total anomalous high-speed steps (>350 km/h) in Case A.
        impossible_velocity_count_b: Total anomalous high-speed steps (>350 km/h) in Case B.
    """

    mean_speed_a: float = 0.0
    mean_speed_b: float = 0.0
    max_speed_a: float = 0.0
    max_speed_b: float = 0.0
    median_speed_a: float = 0.0
    median_speed_b: float = 0.0
    std_speed_a: float = 0.0
    std_speed_b: float = 0.0
    speed_difference_mean: float = 0.0
    speed_trend_alignment: float = 1.0
    handover_count_a: int = 0
    handover_count_b: int = 0
    impossible_velocity_count_a: int = 0
    impossible_velocity_count_b: int = 0


@dataclass(frozen=True)
class SpatialCentroidComparison:
    """Geographical comparison of spatial coverage and centroids.

    Attributes:
        centroid_a: Tuple (latitude, longitude) of Case A spatial centroid.
        centroid_b: Tuple (latitude, longitude) of Case B spatial centroid.
        distance_difference_m: Geodesic distance between centroids in meters.
        distance_difference_km: Geodesic distance between centroids in kilometers.
        bounding_box_overlap_ratio: Overlap ratio (IoU) of spatial bounding boxes in [0.0, 1.0].
    """

    centroid_a: tuple[float, float] | None = None
    centroid_b: tuple[float, float] | None = None
    distance_difference_m: float = 0.0
    distance_difference_km: float = 0.0
    bounding_box_overlap_ratio: float = 0.0


@dataclass(frozen=True)
class CaseComparisonResult:
    """Comprehensive comparison summary object.

    Attributes:
        case_a_id: Identifier for Case A.
        case_b_id: Identifier for Case B.
        cell_overlap: Detailed cell/sector overlap metrics.
        speed_trends: Detailed speed and velocity trend metrics.
        spatial_comparison: Detailed centroid and bounding box comparison.
        avg_confidence_a: Average data/tower confidence for Case A in [0.0, 1.0].
        avg_confidence_b: Average data/tower confidence for Case B in [0.0, 1.0].
        confidence_difference: Absolute confidence delta |Conf_A - Conf_B|.
        overall_similarity_score: Composite similarity index S_sim in [0.0, 1.0].
    """

    case_a_id: str | int = "Case A"
    case_b_id: str | int = "Case B"
    cell_overlap: CellOverlapMetrics = field(default_factory=CellOverlapMetrics)
    speed_trends: SpeedTrendMetrics = field(default_factory=SpeedTrendMetrics)
    spatial_comparison: SpatialCentroidComparison = field(
        default_factory=SpatialCentroidComparison
    )
    avg_confidence_a: float = 1.0
    avg_confidence_b: float = 1.0
    confidence_difference: float = 0.0
    overall_similarity_score: float = 0.0


# ---------------------------------------------------------------------------
# Helper Extraction Functions
# ---------------------------------------------------------------------------


def _get_val(obj: Any, key: str, alt_key: str | None = None) -> Any:
    """Safely extract field from dict or object."""
    if isinstance(obj, dict):
        val = obj.get(key)
        if val is None and alt_key:
            val = obj.get(alt_key)
        return val
    val = getattr(obj, key, None)
    if val is None and alt_key:
        val = getattr(obj, alt_key, None)
    return val


def _extract_cell_ids(records: list[Any]) -> list[str]:
    """Extract non-empty cell/CGI identifiers from a list of records."""
    cell_ids: list[str] = []
    for r in records:
        cgi = (
            _get_val(r, "first_cgi")
            or _get_val(r, "cgi")
            or _get_val(r, "cell_id")
            or _get_val(r, "tower_id")
        )
        if cgi is not None:
            c_str = str(cgi).strip()
            if c_str:
                cell_ids.append(c_str)
    return cell_ids


def _extract_coordinates(records: list[Any]) -> list[tuple[float, float]]:
    """Extract valid (lat, lon) coordinate tuples from records."""
    coords: list[tuple[float, float]] = []
    for r in records:
        lat = _get_val(r, "latitude", "lat")
        lon = _get_val(r, "longitude", "lon")
        if lat is not None and lon is not None:
            try:
                f_lat, f_lon = float(lat), float(lon)
                if -90.0 <= f_lat <= 90.0 and -180.0 <= f_lon <= 180.0:
                    coords.append((f_lat, f_lon))
            except (ValueError, TypeError):
                continue
    return coords


def _extract_confidence_scores(records: list[Any]) -> list[float]:
    """Extract confidence values from records, default to 1.0 if unspecified."""
    scores: list[float] = []
    for r in records:
        conf = _get_val(r, "confidence")
        if conf is None:
            conf = _get_val(r, "tower_confidence")
        if conf is None:
            conf = _get_val(r, "validation_score")
        if conf is not None:
            try:
                scores.append(max(0.0, min(1.0, float(conf))))
            except (ValueError, TypeError):
                scores.append(1.0)
        else:
            scores.append(1.0)
    return scores


# ---------------------------------------------------------------------------
# Core Scientific Functions
# ---------------------------------------------------------------------------


def calculate_cell_overlap(
    records_a: list[Any], records_b: list[Any]
) -> CellOverlapMetrics:
    """Calculate cell sector overlap, Jaccard similarity, and coverage metrics.

    Args:
        records_a: List of records or dicts for Case A.
        records_b: List of records or dicts for Case B.

    Returns:
        CellOverlapMetrics dataclass.
    """
    cells_a = set(_extract_cell_ids(records_a))
    cells_b = set(_extract_cell_ids(records_b))

    overlapping = sorted(list(cells_a & cells_b))
    unique_a = sorted(list(cells_a - cells_b))
    unique_b = sorted(list(cells_b - cells_a))

    overlap_cnt = len(overlapping)
    union_cnt = len(cells_a | cells_b)

    jaccard = (overlap_cnt / union_cnt) if union_cnt > 0 else 0.0
    overlap_pct_a = (overlap_cnt / len(cells_a) * 100.0) if len(cells_a) > 0 else 0.0
    overlap_pct_b = (overlap_cnt / len(cells_b) * 100.0) if len(cells_b) > 0 else 0.0

    return CellOverlapMetrics(
        overlapping_cells=overlapping,
        unique_cells_a=unique_a,
        unique_cells_b=unique_b,
        overlap_count=overlap_cnt,
        total_unique_count=union_cnt,
        jaccard_similarity=round(jaccard, 4),
        overlap_percentage_a=round(overlap_pct_a, 2),
        overlap_percentage_b=round(overlap_pct_b, 2),
    )


def calculate_speed_trends(
    movements_a: list[Any] | MovementSummary,
    movements_b: list[Any] | MovementSummary,
) -> SpeedTrendMetrics:
    """Compare travel speed distributions and velocity trends.

    Args:
        movements_a: List of MovementEvents, CDR records, or MovementSummary for Case A.
        movements_b: List of MovementEvents, CDR records, or MovementSummary for Case B.

    Returns:
        SpeedTrendMetrics dataclass.
    """

    def _process_movements(
        m_input: list[Any] | MovementSummary,
    ) -> tuple[list[float], int, int]:
        if isinstance(m_input, MovementSummary):
            events = m_input.events
            ho_cnt = m_input.handover_count
            anom_cnt = m_input.anomaly_count
        elif isinstance(m_input, list):
            if not m_input:
                return [], 0, 0
            # Check if elements are already MovementEvent instances
            if isinstance(m_input[0], MovementEvent):
                events = m_input
                ho_cnt = sum(1 for e in events if e.is_handover)
                anom_cnt = sum(1 for e in events if e.is_anomalous)
            else:
                # Reconstruct movement sequence
                summary = reconstruct_movement_events(m_input)
                events = summary.events
                ho_cnt = summary.handover_count
                anom_cnt = summary.anomaly_count
        else:
            return [], 0, 0

        speeds: list[float] = []
        for e in events:
            sp = _get_val(e, "speed_kmh")
            if sp is not None:
                try:
                    f_sp = float(sp)
                    if f_sp >= 0.0:
                        speeds.append(f_sp)
                except (ValueError, TypeError):
                    pass
        return speeds, ho_cnt, anom_cnt

    speeds_a, ho_a, anom_a = _process_movements(movements_a)
    speeds_b, ho_b, anom_b = _process_movements(movements_b)

    def _stats(speeds: list[float]) -> tuple[float, float, float, float]:
        if not speeds:
            return 0.0, 0.0, 0.0, 0.0
        mn = float(mean(speeds))
        mx = float(max(speeds))
        med = float(median(speeds))
        sd = float(stdev(speeds)) if len(speeds) > 1 else 0.0
        return mn, mx, med, sd

    mean_a, max_a, med_a, std_a = _stats(speeds_a)
    mean_b, max_b, med_b, std_b = _stats(speeds_b)

    speed_diff = abs(mean_a - mean_b)
    denom = max(mean_a, mean_b, 1.0)
    alignment = max(0.0, min(1.0, 1.0 - (speed_diff / denom)))

    return SpeedTrendMetrics(
        mean_speed_a=round(mean_a, 2),
        mean_speed_b=round(mean_b, 2),
        max_speed_a=round(max_a, 2),
        max_speed_b=round(max_b, 2),
        median_speed_a=round(med_a, 2),
        median_speed_b=round(med_b, 2),
        std_speed_a=round(std_a, 2),
        std_speed_b=round(std_b, 2),
        speed_difference_mean=round(speed_diff, 2),
        speed_trend_alignment=round(alignment, 4),
        handover_count_a=ho_a,
        handover_count_b=ho_b,
        impossible_velocity_count_a=anom_a,
        impossible_velocity_count_b=anom_b,
    )


def calculate_spatial_centroid_comparison(
    records_a: list[Any], records_b: list[Any]
) -> SpatialCentroidComparison:
    """Calculate geographical centroid distance and bounding box overlap.

    Args:
        records_a: List of records or dicts for Case A.
        records_b: List of records or dicts for Case B.

    Returns:
        SpatialCentroidComparison dataclass.
    """
    coords_a = _extract_coordinates(records_a)
    coords_b = _extract_coordinates(records_b)

    if not coords_a and not coords_b:
        return SpatialCentroidComparison()

    centroid_a: tuple[float, float] | None = None
    if coords_a:
        mean_lat_a = mean([c[0] for c in coords_a])
        mean_lon_a = mean([c[1] for c in coords_a])
        centroid_a = (round(mean_lat_a, 6), round(mean_lon_a, 6))

    centroid_b: tuple[float, float] | None = None
    if coords_b:
        mean_lat_b = mean([c[0] for c in coords_b])
        mean_lon_b = mean([c[1] for c in coords_b])
        centroid_b = (round(mean_lat_b, 6), round(mean_lon_b, 6))

    dist_m = 0.0
    if centroid_a and centroid_b:
        calc_dist = calculate_distance_m(
            centroid_a[0], centroid_a[1], centroid_b[0], centroid_b[1]
        )
        if calc_dist is not None:
            dist_m = calc_dist

    dist_km = dist_m / 1000.0

    # Bounding Box Overlap Ratio (Intersection over Union)
    bbox_iou = 0.0
    if coords_a and coords_b:
        min_lat_a, max_lat_a = min([c[0] for c in coords_a]), max([c[0] for c in coords_a])
        min_lon_a, max_lon_a = min([c[1] for c in coords_a]), max([c[1] for c in coords_a])

        min_lat_b, max_lat_b = min([c[0] for c in coords_b]), max([c[0] for c in coords_b])
        min_lon_b, max_lon_b = min([c[1] for c in coords_b]), max([c[1] for c in coords_b])

        lat_inter = max(0.0, min(max_lat_a, max_lat_b) - max(min_lat_a, min_lat_b))
        lon_inter = max(0.0, min(max_lon_a, max_lon_b) - max(min_lon_a, min_lon_b))
        area_inter = lat_inter * lon_inter

        area_a = (max_lat_a - min_lat_a) * (max_lon_a - min_lon_a)
        area_b = (max_lat_b - min_lat_b) * (max_lon_b - min_lon_b)

        area_union = area_a + area_b - area_inter
        if area_union > 0.0:
            bbox_iou = area_inter / area_union
        elif area_a == 0.0 and area_b == 0.0:
            # Single-point bounding boxes
            bbox_iou = 1.0 if dist_m <= 50.0 else 0.0

    return SpatialCentroidComparison(
        centroid_a=centroid_a,
        centroid_b=centroid_b,
        distance_difference_m=round(dist_m, 2),
        distance_difference_km=round(dist_km, 4),
        bounding_box_overlap_ratio=round(max(0.0, min(1.0, bbox_iou)), 4),
    )


def compare_cases(
    case_a_records: list[Any],
    case_b_records: list[Any],
    case_a_movements: list[Any] | MovementSummary | None = None,
    case_b_movements: list[Any] | MovementSummary | None = None,
    case_a_id: str | int = "Case A",
    case_b_id: str | int = "Case B",
) -> CaseComparisonResult:
    """Orchestrate side-by-side comparison between Case A and Case B.

    Computes cell sector overlap, speed trends, spatial centroid distance,
    and composite similarity score S_sim in [0.0, 1.0].

    Args:
        case_a_records: Input CDR/measurement records for Case A.
        case_b_records: Input CDR/measurement records for Case B.
        case_a_movements: Optional movement events or summary for Case A.
        case_b_movements: Optional movement events or summary for Case B.
        case_a_id: Identifier label for Case A.
        case_b_id: Identifier label for Case B.

    Returns:
        CaseComparisonResult instance.
    """
    logger.info(
        "Executing case comparison analysis for Case %s vs Case %s",
        case_a_id,
        case_b_id,
    )

    cell_overlap = calculate_cell_overlap(case_a_records, case_b_records)

    m_a = case_a_movements if case_a_movements is not None else case_a_records
    m_b = case_b_movements if case_b_movements is not None else case_b_records
    speed_trends = calculate_speed_trends(m_a, m_b)

    spatial_comp = calculate_spatial_centroid_comparison(
        case_a_records, case_b_records
    )

    conf_scores_a = _extract_confidence_scores(case_a_records)
    conf_scores_b = _extract_confidence_scores(case_b_records)

    avg_conf_a = mean(conf_scores_a) if conf_scores_a else 1.0
    avg_conf_b = mean(conf_scores_b) if conf_scores_b else 1.0
    conf_diff = abs(avg_conf_a - avg_conf_b)

    # -----------------------------------------------------------------------
    # Composite Similarity Index Calculation (S_sim in [0.0, 1.0])
    # Formula:
    # S_sim = 0.40 * Jaccard_Cell + 0.30 * Spatial_Sim + 0.15 * Speed_Align + 0.15 * (1 - Conf_Diff)
    # -----------------------------------------------------------------------
    jaccard_score = cell_overlap.jaccard_similarity

    # Spatial proximity score: exponential decay with scale 10km (10000m)
    spatial_proximity = math.exp(-spatial_comp.distance_difference_m / 10000.0)
    spatial_score = (
        0.5 * spatial_proximity + 0.5 * spatial_comp.bounding_box_overlap_ratio
    )

    speed_score = speed_trends.speed_trend_alignment
    conf_score = max(0.0, min(1.0, 1.0 - conf_diff))

    overall_similarity = (
        0.40 * jaccard_score
        + 0.30 * spatial_score
        + 0.15 * speed_score
        + 0.15 * conf_score
    )
    overall_similarity_score = max(0.0, min(1.0, float(overall_similarity)))

    return CaseComparisonResult(
        case_a_id=case_a_id,
        case_b_id=case_b_id,
        cell_overlap=cell_overlap,
        speed_trends=speed_trends,
        spatial_comparison=spatial_comp,
        avg_confidence_a=round(avg_conf_a, 4),
        avg_confidence_b=round(avg_conf_b, 4),
        confidence_difference=round(conf_diff, 4),
        overall_similarity_score=round(overall_similarity_score, 4),
    )
