"""
Movement Reconstruction — Scientific Helpers
==============================================

Pure-function module providing distance, speed, bearing, handover detection,
velocity classification, and full movement reconstruction logic for the
Asterion scientific pipeline.

This module contains **no database or service dependencies** — every function
operates on plain Python values, making it straightforward to unit-test and
reuse across the backend service layer and the scientific validation suite.

Key Capabilities
-----------------
1. **Distance & Speed** — Haversine-based geodesic distance and km/h speed.
2. **Bearing** — Initial compass bearing between two WGS84 points.
3. **Handover Detection** — Identifies cell-tower sector handovers where the
   device stays at the same physical site (coordinates within tolerance) but
   the Cell Global Identity (CGI) changes.
4. **Velocity Classification** — Maps computed speed to human-readable
   mobility bands (stationary, walking, driving, highway, anomalous).
5. **Anomaly Flagging** — Flags impossible travel velocities (default >350
   km/h) as potential network roaming or handover noise.
6. **Reconstruction** — Processes a chronologically sorted sequence of CDR
   records into enriched ``MovementEvent`` steps with a ``MovementSummary``.

Usage::

    >>> from scientific.pipeline.movement import (
    ...     calculate_distance_m,
    ...     calculate_speed_kmh,
    ...     detect_handover,
    ...     classify_velocity,
    ...     reconstruct_movement_events,
    ... )
    >>> d = calculate_distance_m(19.076, 72.878, 18.520, 73.856)
    >>> round(d / 1000, 0)   # ~148 km Mumbai → Pune
    148.0
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from scientific.constants import haversine_distance_m

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default coordinate tolerance (meters) for handover detection.
#: Two BTS entries within this distance are treated as the same physical site.
HANDOVER_COORD_TOLERANCE_M: float = 50.0

#: Default impossible-velocity threshold (km/h).
#: Speeds above this value are flagged as network artefacts.
MAX_PLAUSIBLE_SPEED_KMH: float = 350.0

#: Velocity classification bands (km/h boundaries).
VELOCITY_BAND_STATIONARY: float = 1.0
VELOCITY_BAND_WALKING: float = 7.0
VELOCITY_BAND_DRIVING: float = 120.0
VELOCITY_BAND_HIGHWAY: float = 350.0


# ---------------------------------------------------------------------------
# Distance, speed, bearing calculators
# ---------------------------------------------------------------------------


def calculate_distance_m(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
) -> float | None:
    """Compute great-circle distance between two WGS84 points (meters).

    Wraps :func:`scientific.constants.haversine_distance_m` with null-safety
    and input validation.

    Args:
        lat1: Latitude of point 1 (decimal degrees), or ``None``.
        lon1: Longitude of point 1 (decimal degrees), or ``None``.
        lat2: Latitude of point 2 (decimal degrees), or ``None``.
        lon2: Longitude of point 2 (decimal degrees), or ``None``.

    Returns:
        Distance in meters, or ``None`` if any coordinate is missing.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    return haversine_distance_m(lat1, lon1, lat2, lon2)


def calculate_speed_kmh(
    distance_m: float | None,
    time_delta_seconds: float | None,
) -> float | None:
    """Compute travel speed in km/h.

    Args:
        distance_m: Distance travelled in meters, or ``None``.
        time_delta_seconds: Elapsed time in seconds, or ``None``.

    Returns:
        Speed in km/h, or ``None`` if inputs are missing.
        Returns ``0.0`` if *time_delta_seconds* ≤ 0.
    """
    if distance_m is None or time_delta_seconds is None:
        return None
    if time_delta_seconds <= 0.0:
        return 0.0
    speed_mps = distance_m / time_delta_seconds
    return speed_mps * 3.6  # m/s → km/h


def calculate_bearing_deg(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
) -> float | None:
    """Compute the initial bearing (degrees, 0–360) from point 1 to point 2.

    Uses the forward azimuth formula on a sphere.

    Args:
        lat1: Latitude of origin (decimal degrees).
        lon1: Longitude of origin (decimal degrees).
        lat2: Latitude of destination (decimal degrees).
        lon2: Longitude of destination (decimal degrees).

    Returns:
        Bearing in degrees [0, 360), or ``None`` if any coordinate is missing
        or the two points are identical.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None

    rlat1 = math.radians(lat1)
    rlat2 = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)

    x = math.sin(dlon) * math.cos(rlat2)
    y = math.cos(rlat1) * math.sin(rlat2) - math.sin(rlat1) * math.cos(
        rlat2
    ) * math.cos(dlon)

    # atan2(0, 0) is 0.0 in Python — same-point returns 0°
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360.0) % 360.0


# ---------------------------------------------------------------------------
# Handover detection
# ---------------------------------------------------------------------------


def detect_handover(
    prev_cgi: str | None,
    curr_cgi: str | None,
    prev_lat: float | None,
    prev_lon: float | None,
    curr_lat: float | None,
    curr_lon: float | None,
    coord_tolerance_m: float = HANDOVER_COORD_TOLERANCE_M,
) -> bool:
    """Determine whether a cell-tower transition is a sector handover.

    A handover is defined as: **Cell IDs differ, but the resolved coordinates
    are within *coord_tolerance_m* of each other** — indicating a same-site
    sector change rather than physical device movement.

    Args:
        prev_cgi: Cell Global Identity of the previous record.
        curr_cgi: Cell Global Identity of the current record.
        prev_lat: Latitude of the previous cell tower.
        prev_lon: Longitude of the previous cell tower.
        curr_lat: Latitude of the current cell tower.
        curr_lon: Longitude of the current cell tower.
        coord_tolerance_m: Maximum distance (meters) between the two tower
            positions to classify as a same-site handover.

    Returns:
        ``True`` if the transition is a handover (same site, different sector),
        ``False`` otherwise (including when CGIs are identical or any input
        is ``None``).
    """
    # Same CGI or missing CGI → not a handover
    if prev_cgi is None or curr_cgi is None:
        return False
    if prev_cgi == curr_cgi:
        return False

    # CGIs differ — check if coordinates are within tolerance
    dist = calculate_distance_m(prev_lat, prev_lon, curr_lat, curr_lon)
    if dist is None:
        # Cannot determine without coordinates — conservatively not a handover
        return False

    return dist <= coord_tolerance_m


# ---------------------------------------------------------------------------
# Velocity classification & anomaly flagging
# ---------------------------------------------------------------------------


def classify_velocity(
    speed_kmh: float | None,
    max_plausible_kmh: float = MAX_PLAUSIBLE_SPEED_KMH,
) -> str:
    """Classify a speed value into a human-readable mobility band.

    Bands:
        - ``"stationary"``: < 1 km/h
        - ``"walking"``:    1 – 7 km/h
        - ``"driving"``:    7 – 120 km/h
        - ``"highway"``:    120 – 350 km/h
        - ``"anomalous"``:  > 350 km/h (impossible travel)

    Args:
        speed_kmh: Travel speed in km/h, or ``None``.
        max_plausible_kmh: Threshold above which speed is anomalous.

    Returns:
        One of the classification labels above, or ``"unknown"`` if
        *speed_kmh* is ``None`` or negative.
    """
    if speed_kmh is None or speed_kmh < 0.0:
        return "unknown"
    if speed_kmh < VELOCITY_BAND_STATIONARY:
        return "stationary"
    if speed_kmh < VELOCITY_BAND_WALKING:
        return "walking"
    if speed_kmh < VELOCITY_BAND_DRIVING:
        return "driving"
    if speed_kmh <= max_plausible_kmh:
        return "highway"
    return "anomalous"


def flag_impossible_velocity(
    speed_kmh: float | None,
    threshold_kmh: float = MAX_PLAUSIBLE_SPEED_KMH,
) -> bool:
    """Check whether a speed value exceeds the plausible travel threshold.

    Speeds above *threshold_kmh* (default 350 km/h) are flagged as potential
    network roaming artefacts or handover noise.

    Args:
        speed_kmh: Travel speed in km/h, or ``None``.
        threshold_kmh: The ceiling above which speed is impossible.

    Returns:
        ``True`` if the speed exceeds the threshold, ``False`` otherwise
        (including when *speed_kmh* is ``None``).
    """
    if speed_kmh is None:
        return False
    return speed_kmh > threshold_kmh


# ---------------------------------------------------------------------------
# Movement event dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MovementEvent:
    """A single step in the reconstructed movement sequence.

    Attributes:
        sequence: 1-based position in the chronological sequence.
        timestamp: Event timestamp.
        latitude: Resolved latitude (WGS84).
        longitude: Resolved longitude (WGS84).
        cgi: Cell Global Identity for this record.
        distance_m: Distance from the previous event (meters).
        time_delta_s: Elapsed time since the previous event (seconds).
        speed_kmh: Computed travel speed (km/h).
        bearing_deg: Compass bearing from the previous event (degrees 0–360).
        is_handover: True if this is a same-site sector handover.
        is_anomalous: True if the speed exceeds the plausible threshold.
        velocity_class: Human-readable mobility classification.
        event_type: Source event type (e.g. 'call_start', 'sms', 'location_update').
        metadata: Optional dictionary of extra fields from the source record.
    """

    sequence: int
    timestamp: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    cgi: str | None = None
    distance_m: float | None = None
    time_delta_s: float | None = None
    speed_kmh: float | None = None
    bearing_deg: float | None = None
    is_handover: bool = False
    is_anomalous: bool = False
    velocity_class: str = "unknown"
    event_type: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class MovementSummary:
    """Aggregated statistics for a reconstructed movement sequence.

    Attributes:
        total_events: Number of events in the sequence.
        total_distance_m: Cumulative travel distance (meters).
        total_distance_km: Cumulative travel distance (kilometers).
        time_span_seconds: Elapsed time from first to last event (seconds).
        handover_count: Number of detected same-site handovers.
        anomaly_count: Number of impossible-velocity events.
        max_speed_kmh: Peak speed observed in the sequence.
        avg_speed_kmh: Average speed across non-zero-distance steps.
        velocity_distribution: Counts per velocity classification band.
        events: The full list of :class:`MovementEvent` instances.
    """

    total_events: int = 0
    total_distance_m: float = 0.0
    total_distance_km: float = 0.0
    time_span_seconds: float = 0.0
    handover_count: int = 0
    anomaly_count: int = 0
    max_speed_kmh: float = 0.0
    avg_speed_kmh: float = 0.0
    velocity_distribution: dict[str, int] = field(default_factory=dict)
    events: list[MovementEvent] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Full movement reconstruction
# ---------------------------------------------------------------------------


def _get_field(obj: Any, key: str, default: Any = None) -> Any:
    """Retrieve a value from a dict-like or attribute-bearing object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _ensure_tz_aware(ts: datetime | None) -> datetime | None:
    """Ensure a datetime is timezone-aware (default UTC)."""
    if ts is None:
        return None
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts


def reconstruct_movement_events(
    records: list[Any],
    coord_tolerance_m: float = HANDOVER_COORD_TOLERANCE_M,
    max_plausible_kmh: float = MAX_PLAUSIBLE_SPEED_KMH,
) -> MovementSummary:
    """Reconstruct a movement event sequence from chronologically sorted records.

    Each record should be a dict or object exposing at minimum:
        - ``timestamp``: ``datetime``
        - ``latitude``: ``float | None``
        - ``longitude``: ``float | None``
        - ``first_cgi`` or ``cgi``: ``str | None``

    Optional fields:
        - ``event_type``: ``str``
        - ``call_type``: ``str``
        - ``operator``, ``duration``, ``imei``, ``imsi``, etc.

    The function computes per-step distance, speed, bearing, handover
    classification, and velocity anomaly flags, then returns a
    :class:`MovementSummary` containing both the event list and aggregate
    statistics.

    Args:
        records: Chronologically sorted CDR record dicts/objects.
        coord_tolerance_m: Handover coordinate tolerance (meters).
        max_plausible_kmh: Speed ceiling for anomaly flagging (km/h).

    Returns:
        A :class:`MovementSummary` with the enriched event list and statistics.
    """
    events: list[MovementEvent] = []
    velocity_dist: dict[str, int] = {}
    total_distance = 0.0
    max_speed = 0.0
    speed_sum = 0.0
    speed_count = 0
    handover_count = 0
    anomaly_count = 0

    for i, rec in enumerate(records):
        ts = _ensure_tz_aware(_get_field(rec, "timestamp"))
        lat = _get_field(rec, "latitude")
        lon = _get_field(rec, "longitude")
        cgi = _get_field(rec, "first_cgi") or _get_field(rec, "cgi")
        evt_type = _get_field(rec, "event_type") or _get_field(rec, "call_type")

        # Build metadata from extra fields
        meta: dict[str, Any] = {}
        for key in (
            "operator",
            "target_number",
            "b_party_number",
            "duration",
            "imei",
            "imsi",
            "service_type",
        ):
            val = _get_field(rec, key)
            if val is not None:
                meta[key] = val

        if i == 0:
            # First event — no previous to compare against
            v_class = classify_velocity(0.0, max_plausible_kmh)
            velocity_dist[v_class] = velocity_dist.get(v_class, 0) + 1

            events.append(
                MovementEvent(
                    sequence=1,
                    timestamp=ts,
                    latitude=lat,
                    longitude=lon,
                    cgi=cgi,
                    distance_m=0.0,
                    time_delta_s=0.0,
                    speed_kmh=0.0,
                    bearing_deg=None,
                    is_handover=False,
                    is_anomalous=False,
                    velocity_class=v_class,
                    event_type=evt_type,
                    metadata=meta if meta else None,
                )
            )
            continue

        # Previous event data
        prev = events[i - 1]
        prev_ts = prev.timestamp
        prev_lat = prev.latitude
        prev_lon = prev.longitude
        prev_cgi = prev.cgi

        # --- Distance ---
        dist = calculate_distance_m(prev_lat, prev_lon, lat, lon)

        # --- Time delta ---
        dt_s: float | None = None
        if prev_ts is not None and ts is not None:
            dt_s = max((ts - prev_ts).total_seconds(), 0.0)

        # --- Handover detection ---
        is_ho = detect_handover(
            prev_cgi,
            cgi,
            prev_lat,
            prev_lon,
            lat,
            lon,
            coord_tolerance_m,
        )

        # --- Speed & bearing ---
        if is_ho:
            # Handover: zero out distance and speed
            speed = 0.0
            dist = 0.0
            bearing = None
        else:
            speed_val = calculate_speed_kmh(dist, dt_s)
            speed = speed_val if speed_val is not None else 0.0
            if dist is not None and dist > 1.0:
                bearing = calculate_bearing_deg(prev_lat, prev_lon, lat, lon)
            else:
                bearing = None

        # --- Anomaly flagging ---
        is_anom = flag_impossible_velocity(speed, max_plausible_kmh)

        # --- Velocity classification ---
        v_class = classify_velocity(speed, max_plausible_kmh)

        # --- Accumulate ---
        if dist is not None and not is_ho:
            total_distance += dist
        if speed is not None and speed > max_speed:
            max_speed = speed
        if speed is not None and speed > 0.0 and not is_ho:
            speed_sum += speed
            speed_count += 1
        if is_ho:
            handover_count += 1
        if is_anom:
            anomaly_count += 1
        velocity_dist[v_class] = velocity_dist.get(v_class, 0) + 1

        events.append(
            MovementEvent(
                sequence=i + 1,
                timestamp=ts,
                latitude=lat,
                longitude=lon,
                cgi=cgi,
                distance_m=round(dist, 2) if dist is not None else None,
                time_delta_s=round(dt_s, 2) if dt_s is not None else None,
                speed_kmh=round(speed, 4) if speed is not None else None,
                bearing_deg=round(bearing, 2) if bearing is not None else None,
                is_handover=is_ho,
                is_anomalous=is_anom,
                velocity_class=v_class,
                event_type=evt_type,
                metadata=meta if meta else None,
            )
        )

    # --- Build summary ---
    time_span = 0.0
    if len(events) >= 2:
        first_ts = events[0].timestamp
        last_ts = events[-1].timestamp
        if first_ts is not None and last_ts is not None:
            time_span = max((last_ts - first_ts).total_seconds(), 0.0)

    avg_speed = (speed_sum / speed_count) if speed_count > 0 else 0.0

    return MovementSummary(
        total_events=len(events),
        total_distance_m=round(total_distance, 2),
        total_distance_km=round(total_distance / 1000.0, 4),
        time_span_seconds=round(time_span, 2),
        handover_count=handover_count,
        anomaly_count=anomaly_count,
        max_speed_kmh=round(max_speed, 4),
        avg_speed_kmh=round(avg_speed, 4),
        velocity_distribution=velocity_dist,
        events=events,
    )
