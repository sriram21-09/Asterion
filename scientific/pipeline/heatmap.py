"""
Scientific Heatmap Calculation Engine
======================================

Implements configurable spatial heatmap scoring and grid aggregation based on
Section 3D of the Asterion Master Execution Plan:

    S_j = w1 · Norm(Density_j) + w2 · Norm(DwellTime_j) + w3 · Norm(Confidence_j) + w4 · Norm(Transitions_j)

Handles zero-variance inputs safely to prevent division-by-zero errors and guarantees
output scores are strictly bounded within [0.0, 1.0].
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence, TypeVar

K = TypeVar("K")

# ---------------------------------------------------------------------------
# HeatmapWeights Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HeatmapWeights:
    """Configurable weights for heatmap probability scoring.

    Attributes:
        w_density: Weight for spatial/record density score (w1).
        w_dwell_time: Weight for stay/dwell duration score (w2).
        w_confidence: Weight for tower/data confidence score (w3).
        w_transitions: Weight for handover/movement transition score (w4).
    """

    w_density: float = 0.35
    w_dwell_time: float = 0.30
    w_confidence: float = 0.20
    w_transitions: float = 0.15

    @property
    def w1(self) -> float:
        """Alias for w_density."""
        return self.w_density

    @property
    def w2(self) -> float:
        """Alias for w_dwell_time."""
        return self.w_dwell_time

    @property
    def w3(self) -> float:
        """Alias for w_confidence."""
        return self.w_confidence

    @property
    def w4(self) -> float:
        """Alias for w_transitions."""
        return self.w_transitions

    def normalized(self) -> HeatmapWeights:
        """Return a copy of HeatmapWeights with weights normalized to sum to 1.0."""
        total = (
            abs(self.w_density)
            + abs(self.w_dwell_time)
            + abs(self.w_confidence)
            + abs(self.w_transitions)
        )
        if total == 0.0:
            return HeatmapWeights(0.25, 0.25, 0.25, 0.25)
        return HeatmapWeights(
            w_density=abs(self.w_density) / total,
            w_dwell_time=abs(self.w_dwell_time) / total,
            w_confidence=abs(self.w_confidence) / total,
            w_transitions=abs(self.w_transitions) / total,
        )


# ---------------------------------------------------------------------------
# HeatmapCellScore Data Structure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HeatmapCellScore:
    """Calculated probability score and normalized metrics for a spatial cell location.

    Attributes:
        cell_id: String or tuple identifier for the spatial cell.
        latitude: Latitude center of the cell.
        longitude: Longitude center of the cell.
        raw_density: Raw observation count / density.
        raw_dwell_time: Raw cumulative dwell time in seconds.
        raw_confidence: Raw average confidence score.
        raw_transitions: Raw transition / handover count.
        norm_density: Normalized density score in [0.0, 1.0].
        norm_dwell_time: Normalized dwell time score in [0.0, 1.0].
        norm_confidence: Normalized confidence score in [0.0, 1.0].
        norm_transitions: Normalized transition score in [0.0, 1.0].
        score: Final composite location score S_j in [0.0, 1.0].
    """

    cell_id: str | tuple[float, float]
    latitude: float
    longitude: float
    raw_density: float
    raw_dwell_time: float
    raw_confidence: float
    raw_transitions: float
    norm_density: float
    norm_dwell_time: float
    norm_confidence: float
    norm_transitions: float
    score: float


# ---------------------------------------------------------------------------
# Normalization Functions
# ---------------------------------------------------------------------------


def min_max_normalize(
    values: dict[K, float] | Sequence[float],
) -> dict[K, float] | list[float]:
    """Normalize input values to the interval [0.0, 1.0] using Min-Max scaling.

    Handles zero-variance inputs safely (division-by-zero guard):
      - If max == min and max > 0: returns 1.0 for all elements.
      - If max == min and max == 0: returns 0.0 for all elements.

    Args:
        values: Dictionary or sequence of numeric values.

    Returns:
        Normalized values in the same container type structure.
    """
    if isinstance(values, dict):
        if not values:
            return {}
        val_list = list(values.values())
        min_val = min(val_list)
        max_val = max(val_list)
        range_val = max_val - min_val

        result_dict: dict[K, float] = {}
        for k, v in values.items():
            if range_val == 0.0:
                result_dict[k] = 1.0 if max_val > 0.0 else 0.0
            else:
                norm = (v - min_val) / range_val
                result_dict[k] = max(0.0, min(1.0, norm))
        return result_dict
    else:
        if not values:
            return []
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val

        result_list: list[float] = []
        for v in values:
            if range_val == 0.0:
                result_list.append(1.0 if max_val > 0.0 else 0.0)
            else:
                norm = (v - min_val) / range_val
                result_list.append(max(0.0, min(1.0, norm)))
        return result_list


def normalize_density(densities: dict[K, float]) -> dict[K, float]:
    """Normalize density metrics for spatial cells into [0.0, 1.0]."""
    res = min_max_normalize(densities)
    assert isinstance(res, dict)
    return res


def normalize_dwell_time(dwell_times: dict[K, float]) -> dict[K, float]:
    """Normalize dwell time metrics for spatial cells into [0.0, 1.0]."""
    res = min_max_normalize(dwell_times)
    assert isinstance(res, dict)
    return res


def normalize_confidence(confidences: dict[K, float]) -> dict[K, float]:
    """Normalize confidence metrics for spatial cells into [0.0, 1.0]."""
    res = min_max_normalize(confidences)
    assert isinstance(res, dict)
    return res


def normalize_transitions(transitions: dict[K, float]) -> dict[K, float]:
    """Normalize transition metrics for spatial cells into [0.0, 1.0]."""
    res = min_max_normalize(transitions)
    assert isinstance(res, dict)
    return res


# ---------------------------------------------------------------------------
# Per-Cell Score Calculation
# ---------------------------------------------------------------------------


def calculate_cell_score(
    norm_density: float,
    norm_dwell_time: float,
    norm_confidence: float,
    norm_transitions: float,
    weights: HeatmapWeights | dict[str, float] | None = None,
) -> float:
    """Calculate the composite heatmap probability score S_j for a spatial cell.

    Formula:
        S_j = w1 · Norm(Density_j) + w2 · Norm(DwellTime_j) + w3 · Norm(Confidence_j) + w4 · Norm(Transitions_j)

    Args:
        norm_density: Normalized density score in [0.0, 1.0].
        norm_dwell_time: Normalized dwell time score in [0.0, 1.0].
        norm_confidence: Normalized confidence score in [0.0, 1.0].
        norm_transitions: Normalized transition score in [0.0, 1.0].
        weights: Optional HeatmapWeights object or dictionary of weights.

    Returns:
        Composite score S_j bounded within [0.0, 1.0].
    """
    if weights is None:
        hw = HeatmapWeights().normalized()
    elif isinstance(weights, dict):
        w_dens = weights.get("w1", weights.get("w_density", 0.35))
        w_dwell = weights.get("w2", weights.get("w_dwell_time", 0.30))
        w_conf = weights.get("w3", weights.get("w_confidence", 0.20))
        w_trans = weights.get("w4", weights.get("w_transitions", 0.15))
        hw = HeatmapWeights(
            w_density=w_dens,
            w_dwell_time=w_dwell,
            w_confidence=w_conf,
            w_transitions=w_trans,
        ).normalized()
    else:
        hw = weights.normalized()

    score = (
        hw.w1 * norm_density
        + hw.w2 * norm_dwell_time
        + hw.w3 * norm_confidence
        + hw.w4 * norm_transitions
    )
    return max(0.0, min(1.0, score))


# ---------------------------------------------------------------------------
# Heatmap Score Generation & Grid Aggregation
# ---------------------------------------------------------------------------


def compute_heatmap(
    cell_metrics: list[dict[str, Any]] | list[Any],
    weights: HeatmapWeights | dict[str, float] | None = None,
) -> list[HeatmapCellScore]:
    """Compute heatmap scores for a set of pre-aggregated location cell metrics.

    Each cell metric item can be a dict or object with keys/attributes:
      - cell_id, latitude, longitude
      - raw_density / density
      - raw_dwell_time / dwell_time
      - raw_confidence / confidence
      - raw_transitions / transitions

    Returns:
        List of HeatmapCellScore instances.
    """
    if not cell_metrics:
        return []

    def _get(
        item: Any, key: str, alt_key: str | None = None, default: Any = 0.0
    ) -> Any:
        if isinstance(item, dict):
            val = item.get(key)
            if val is None and alt_key:
                val = item.get(alt_key)
            return val if val is not None else default
        else:
            val = getattr(item, key, None)
            if val is None and alt_key:
                val = getattr(item, alt_key, None)
            return val if val is not None else default

    raw_densities: dict[int, float] = {}
    raw_dwell_times: dict[int, float] = {}
    raw_confidences: dict[int, float] = {}
    raw_transitions: dict[int, float] = {}

    cell_meta: list[dict[str, Any]] = []

    for idx, item in enumerate(cell_metrics):
        cell_id = _get(item, "cell_id", default=f"cell_{idx}")
        lat = float(_get(item, "latitude", "lat", default=0.0))
        lon = float(_get(item, "longitude", "lon", default=0.0))

        dens = float(_get(item, "raw_density", "density", default=0.0))
        dwell = float(_get(item, "raw_dwell_time", "dwell_time", default=0.0))
        conf = float(_get(item, "raw_confidence", "confidence", default=1.0))
        trans = float(_get(item, "raw_transitions", "transitions", default=0.0))

        raw_densities[idx] = dens
        raw_dwell_times[idx] = dwell
        raw_confidences[idx] = conf
        raw_transitions[idx] = trans

        cell_meta.append(
            {
                "cell_id": cell_id,
                "latitude": lat,
                "longitude": lon,
                "raw_density": dens,
                "raw_dwell_time": dwell,
                "raw_confidence": conf,
                "raw_transitions": trans,
            }
        )

    norm_dens = normalize_density(raw_densities)
    norm_dwell = normalize_dwell_time(raw_dwell_times)
    norm_conf = normalize_confidence(raw_confidences)
    norm_trans = normalize_transitions(raw_transitions)

    results: list[HeatmapCellScore] = []
    for idx, meta in enumerate(cell_meta):
        nd = norm_dens.get(idx, 0.0)
        ndw = norm_dwell.get(idx, 0.0)
        nc = norm_conf.get(idx, 0.0)
        nt = norm_trans.get(idx, 0.0)

        score = calculate_cell_score(
            norm_density=nd,
            norm_dwell_time=ndw,
            norm_confidence=nc,
            norm_transitions=nt,
            weights=weights,
        )

        results.append(
            HeatmapCellScore(
                cell_id=meta["cell_id"],
                latitude=meta["latitude"],
                longitude=meta["longitude"],
                raw_density=meta["raw_density"],
                raw_dwell_time=meta["raw_dwell_time"],
                raw_confidence=meta["raw_confidence"],
                raw_transitions=meta["raw_transitions"],
                norm_density=nd,
                norm_dwell_time=ndw,
                norm_confidence=nc,
                norm_transitions=nt,
                score=score,
            )
        )

    return results


def aggregate_grid_heatmap(
    records: list[Any],
    grid_size_deg: float = 0.01,
    weights: HeatmapWeights | dict[str, float] | None = None,
) -> list[HeatmapCellScore]:
    """Perform grid-based spatial aggregation and heatmap intensity computation.

    Groups raw observations (CDRs, measurements, or movement points) into spatial
    grid cells of dimension ``grid_size_deg`` × ``grid_size_deg`` degrees.

    For each cell j:
      - Density_j: Total count of records falling into grid cell j.
      - DwellTime_j: Sum of record durations in seconds (or time span).
      - Confidence_j: Mean confidence value of records/towers in grid cell j.
      - Transitions_j: Count of transitions (handovers or movement switches) involving cell j.

    Args:
        records: List of CDRRecords, Measurements, MovementEvents, or dicts.
        grid_size_deg: Dimensions of grid cell in degrees (default 0.01 ~ 1.1km).
        weights: Optional HeatmapWeights configuration.

    Returns:
        List of HeatmapCellScore instances ordered by cell location.
    """
    if not records:
        return []

    def _get_val(obj: Any, key: str, alt_key: str | None = None) -> Any:
        if isinstance(obj, dict):
            val = obj.get(key)
            if val is None and alt_key:
                val = obj.get(alt_key)
            return val
        val = getattr(obj, key, None)
        if val is None and alt_key:
            val = getattr(obj, alt_key, None)
        return val

    # Filter records with valid latitude and longitude
    valid_records = []
    for r in records:
        lat = _get_val(r, "latitude", "lat")
        lon = _get_val(r, "longitude", "lon")
        if lat is not None and lon is not None:
            try:
                valid_records.append((float(lat), float(lon), r))
            except (ValueError, TypeError):
                continue

    if not valid_records:
        return []

    # Sort valid records by timestamp if available for transition counting
    def _parse_ts(r: Any) -> datetime | None:
        ts = _get_val(r, "timestamp", "time")
        if isinstance(ts, datetime):
            return ts
        return None

    sorted_records = sorted(
        valid_records,
        key=lambda item: _parse_ts(item[2]) or datetime.min,
    )

    # 1. Bucket into grid cells
    grid_cells: dict[tuple[float, float], list[Any]] = {}

    for lat, lon, r in sorted_records:
        grid_lat = round(round(lat / grid_size_deg) * grid_size_deg, 6)
        grid_lon = round(round(lon / grid_size_deg) * grid_size_deg, 6)
        cell_key = (grid_lat, grid_lon)
        grid_cells.setdefault(cell_key, []).append(r)

    # 2. Compute transition counts across grid cells
    transitions_per_cell: dict[tuple[float, float], float] = {
        k: 0.0 for k in grid_cells
    }
    prev_cell: tuple[float, float] | None = None

    for lat, lon, r in sorted_records:
        grid_lat = round(round(lat / grid_size_deg) * grid_size_deg, 6)
        grid_lon = round(round(lon / grid_size_deg) * grid_size_deg, 6)
        curr_cell = (grid_lat, grid_lon)

        if prev_cell is not None:
            # Check if handover or transition event flag is present or cell boundary changed
            is_handover = _get_val(r, "event_type") == "handover" or _get_val(
                r, "is_handover"
            )
            if curr_cell != prev_cell or is_handover:
                transitions_per_cell[curr_cell] += 1.0
                transitions_per_cell[prev_cell] += 1.0

        prev_cell = curr_cell

    # 3. Calculate raw cell metrics
    cell_metrics_input: list[dict[str, Any]] = []

    for (g_lat, g_lon), cell_recs in grid_cells.items():
        density = float(len(cell_recs))

        # Dwell time: sum duration fields, or compute timestamp span if duration not explicit
        total_duration = 0.0
        timestamps: list[datetime] = []

        for r in cell_recs:
            dur = _get_val(r, "duration")
            if dur is not None:
                try:
                    total_duration += float(dur)
                except (ValueError, TypeError):
                    pass
            ts = _parse_ts(r)
            if ts:
                timestamps.append(ts)

        if total_duration == 0.0 and len(timestamps) > 1:
            span_sec = (max(timestamps) - min(timestamps)).total_seconds()
            total_duration = max(0.0, span_sec)

        # Confidence: average tower/record confidence (default 1.0)
        conf_scores: list[float] = []
        for r in cell_recs:
            conf = _get_val(r, "confidence", "tower_confidence")
            if conf is None:
                conf = _get_val(r, "validation_score")
            if conf is not None:
                try:
                    conf_scores.append(float(conf))
                except (ValueError, TypeError):
                    pass
            else:
                conf_scores.append(1.0)

        avg_conf = sum(conf_scores) / len(conf_scores) if conf_scores else 1.0
        trans_count = transitions_per_cell.get((g_lat, g_lon), 0.0)

        cell_metrics_input.append(
            {
                "cell_id": f"cell_{g_lat:.4f}_{g_lon:.4f}",
                "latitude": g_lat,
                "longitude": g_lon,
                "raw_density": density,
                "raw_dwell_time": total_duration,
                "raw_confidence": avg_conf,
                "raw_transitions": trans_count,
            }
        )

    # 4. Compute normalized heatmap scores for all cells
    return compute_heatmap(cell_metrics_input, weights=weights)
