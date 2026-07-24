"""
Quality-Weighted Centroid Solver
=================================

Implements a multi-factor quality-weighted centroid algorithm for initial
guess generation and fallback localization.

The weighting system combines four quality dimensions:

1. **RSSI signal strength** (35%) — normalized linear power.
2. **Coordinate availability** (25%) — whether the tower has valid coords.
3. **Timestamp completeness** (20%) — presence and freshness of timestamps.
4. **Tower confidence** (20%) — spatial density / resolution confidence.

When no quality metadata is available, the solver degrades gracefully to
the original RSSI-only weighting, ensuring full backward compatibility.

Usage::

    >>> from scientific.pipeline.weighted_centroid import (
    ...     solve_weighted_centroid,
    ...     compute_input_quality_scores,
    ... )
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime

from scientific.constants import haversine_distance_m
from scientific.models.measurement import Measurement
from scientific.models.result import LocalizationResult
from scientific.models.tower import Tower

# ---------------------------------------------------------------------------
# Quality score weights
# ---------------------------------------------------------------------------

_W_RSSI: float = 0.35
_W_COORD: float = 0.25
_W_TIMESTAMP: float = 0.20
_W_TOWER_CONF: float = 0.20


# ---------------------------------------------------------------------------
# InputQualityScore dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InputQualityScore:
    """Per-tower quality assessment for the weighted centroid algorithm.

    Each dimension is scored in ``[0.0, 1.0]`` and combined into a
    ``composite_score`` using the module-level weights.

    Attributes:
        tower_id: Identifier of the tower this score belongs to.
        rssi_score: Normalized signal strength (higher = stronger signal).
        coord_score: Coordinate availability (1.0 = valid lat/lon on tower).
        timestamp_score: Timestamp completeness (1.0 = present & fresh).
        tower_confidence: Tower density / resolution confidence.
        composite_score: Weighted combination of all dimensions.
    """

    tower_id: str
    rssi_score: float
    coord_score: float
    timestamp_score: float
    tower_confidence: float
    composite_score: float


# ---------------------------------------------------------------------------
# Quality score computation
# ---------------------------------------------------------------------------


def compute_input_quality_scores(
    towers: list[Tower],
    measurements: list[Measurement],
    tower_densities: dict[str, float] | None = None,
) -> dict[str, InputQualityScore]:
    """Compute multi-factor quality scores for each tower's measurements.

    Args:
        towers: List of tower configurations.
        measurements: List of signal measurements.
        tower_densities: Optional mapping of tower_id → normalized density
            score in ``[0.0, 1.0]``.  When ``None``, tower confidence
            defaults to ``1.0`` for all towers.

    Returns:
        A dictionary mapping tower_id → :class:`InputQualityScore`.
    """
    tower_map = {t.tower_id: t for t in towers}

    # ── 1. Group measurements by tower and compute average RSSI ──────────
    tower_rssis: dict[str, list[float]] = {}
    tower_timestamps: dict[str, list[datetime | None]] = {}
    tower_meas_coords: dict[str, list[tuple[float | None, float | None]]] = {}

    for m in measurements:
        tower_rssis.setdefault(m.tower_id, []).append(m.rssi_dbm)
        tower_timestamps.setdefault(m.tower_id, []).append(m.timestamp)
        tower_meas_coords.setdefault(m.tower_id, []).append((m.latitude, m.longitude))

    # ── 2. Compute per-dimension scores ──────────────────────────────────
    # Normalize RSSI across all towers (min-max on linear power)
    avg_rssi_linear: dict[str, float] = {}
    for tid, rssi_list in tower_rssis.items():
        avg_dbm = sum(rssi_list) / len(rssi_list)
        avg_rssi_linear[tid] = 10.0 ** (avg_dbm / 10.0)

    linear_values = list(avg_rssi_linear.values())
    min_lin = min(linear_values) if linear_values else 0.0
    max_lin = max(linear_values) if linear_values else 0.0
    range_lin = max_lin - min_lin

    scores: dict[str, InputQualityScore] = {}

    for tid in tower_rssis:
        # ── RSSI score ───────────────────────────────────────────────────
        if range_lin > 0.0:
            rssi_score = (avg_rssi_linear[tid] - min_lin) / range_lin
        else:
            rssi_score = 1.0  # All equal → all get max score

        # ── Coordinate availability score ────────────────────────────────
        tower = tower_map.get(tid)
        if (
            tower is not None
            and tower.latitude is not None
            and tower.longitude is not None
        ):
            coord_score = 1.0
        else:
            # Check if any measurement has coordinates
            meas_coords = tower_meas_coords.get(tid, [])
            has_meas_coords = any(
                lat is not None and lon is not None for lat, lon in meas_coords
            )
            coord_score = 0.5 if has_meas_coords else 0.0

        # ── Timestamp completeness score ─────────────────────────────────
        ts_list = tower_timestamps.get(tid, [])
        if not ts_list:
            ts_score = 0.0
        else:
            valid_count = 0
            now_utc = datetime.now(UTC)
            for ts in ts_list:
                if ts is not None:
                    ts_aware = ts if ts.tzinfo is not None else ts.replace(tzinfo=UTC)
                    age_days = (now_utc - ts_aware).days
                    if ts_aware <= now_utc and age_days <= 365:
                        valid_count += 1
                    else:
                        valid_count += 0.5  # Present but stale/future → partial
            ts_score = valid_count / len(ts_list)
            ts_score = min(1.0, ts_score)

        # ── Tower confidence score ───────────────────────────────────────
        if tower_densities is not None and tid in tower_densities:
            tower_conf = max(0.0, min(1.0, tower_densities[tid]))
        else:
            tower_conf = 1.0  # Default: trust all towers equally

        # ── Composite score ──────────────────────────────────────────────
        composite = (
            _W_RSSI * rssi_score
            + _W_COORD * coord_score
            + _W_TIMESTAMP * ts_score
            + _W_TOWER_CONF * tower_conf
        )

        scores[tid] = InputQualityScore(
            tower_id=tid,
            rssi_score=round(rssi_score, 6),
            coord_score=round(coord_score, 6),
            timestamp_score=round(ts_score, 6),
            tower_confidence=round(tower_conf, 6),
            composite_score=round(composite, 6),
        )

    return scores


# ---------------------------------------------------------------------------
# Weighted centroid solver
# ---------------------------------------------------------------------------


def solve_weighted_centroid(
    scenario_id: str,
    towers: list[Tower],
    measurements: list[Measurement],
    expected_device_lat: float | None = None,
    expected_device_lon: float | None = None,
    tower_densities: dict[str, float] | None = None,
) -> LocalizationResult:
    """Calculate the estimated position using a quality-weighted centroid.

    When ``tower_densities`` is provided, the algorithm uses multi-factor
    quality scores (RSSI, coordinate availability, timestamp completeness,
    tower confidence) as weights.  When ``None``, the algorithm falls back
    to the original RSSI-only linear-power weighting for full backward
    compatibility.

    The weight for each tower in quality mode is::

        w_i = rssi_linear_i × composite_quality_i

    This ensures that signal strength remains the dominant factor while
    quality dimensions modulate the contribution of each tower.

    Args:
        scenario_id: Identifier of the source scenario.
        towers: List of tower configurations.
        measurements: List of signal measurements.
        expected_device_lat: Ground-truth device latitude (for error calculation).
        expected_device_lon: Ground-truth device longitude (for error calculation).
        tower_densities: Optional mapping of tower_id → normalized density
            score in ``[0.0, 1.0]``.  Activates quality-weighted mode.

    Returns:
        A LocalizationResult containing the estimated position.
    """
    start_time = time.perf_counter()

    # 1. Group measurements by tower_id and compute average RSSI
    tower_rssis: dict[str, list[float]] = {}
    for m in measurements:
        tower_rssis.setdefault(m.tower_id, []).append(m.rssi_dbm)

    avg_tower_rssi = {
        tid: sum(rssi_list) / len(rssi_list) for tid, rssi_list in tower_rssis.items()
    }

    # 2. Compute quality scores (if quality mode is active)
    quality_scores: dict[str, InputQualityScore] | None = None
    if tower_densities is not None:
        quality_scores = compute_input_quality_scores(
            towers=towers,
            measurements=measurements,
            tower_densities=tower_densities,
        )

    # 3. Map tower ID to tower configurations
    tower_map = {t.tower_id: t for t in towers}

    total_weight = 0.0
    weighted_lat = 0.0
    weighted_lon = 0.0
    signals_used = 0

    for tid, avg_rssi in avg_tower_rssi.items():
        if tid in tower_map:
            tower = tower_map[tid]

            # Base weight: RSSI linear power
            rssi_linear = 10.0 ** (avg_rssi / 10.0)

            if quality_scores is not None and tid in quality_scores:
                # Quality-weighted mode: modulate RSSI by composite quality
                qs = quality_scores[tid]
                weight = rssi_linear * max(0.01, qs.composite_score)
            else:
                # Classic mode: RSSI-only
                weight = rssi_linear

            weighted_lat += weight * tower.latitude
            weighted_lon += weight * tower.longitude
            total_weight += weight
            signals_used += 1

    # 4. Compute estimated coordinates
    if total_weight == 0.0:
        # Fallback to simple unweighted centroid of towers if no weights/measurements
        if towers:
            est_lat = sum(t.latitude for t in towers) / len(towers)
            est_lon = sum(t.longitude for t in towers) / len(towers)
        else:
            raise ValueError("No towers available to compute weighted centroid.")
    else:
        est_lat = weighted_lat / total_weight
        est_lon = weighted_lon / total_weight

    end_time = time.perf_counter()
    computation_time_ms = (end_time - start_time) * 1000.0

    # 5. Compute error if ground truth is provided
    error_m = None
    if expected_device_lat is not None and expected_device_lon is not None:
        error_m = haversine_distance_m(
            expected_device_lat, expected_device_lon, est_lat, est_lon
        )

    return LocalizationResult(
        scenario_id=scenario_id,
        algorithm="weighted_centroid",
        estimated_latitude=est_lat,
        estimated_longitude=est_lon,
        error_m=error_m,
        computation_time_ms=computation_time_ms,
        signals_used=max(1, signals_used),
        timestamp=datetime.now(UTC),
    )
