"""
Movement Reconstruction Service
=================================

Generates chronological movement event sequences from CDR records and
Kalman-smoothed tracking data, classifying handover events (cell tower
transitions) and computing kinematic properties.
"""

import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.cdr_record import CDRRecord
from app.models.movement_event import MovementEvent
from app.models.tracking_result import TrackingResult
from app.repositories.movement_repository import MovementRepository
from app.repositories.case_repository import CaseRepository
from app.shared.validation import ValidationError, decode_case_code

from scientific.constants import haversine_distance_m


# ---------------------------------------------------------------------------
# Event type constants
# ---------------------------------------------------------------------------

EVENT_TYPE_LOCATION_UPDATE = "location_update"
EVENT_TYPE_HANDOVER = "handover"
EVENT_TYPE_CALL_START = "call_start"
EVENT_TYPE_CALL_END = "call_end"
EVENT_TYPE_SMS = "sms"
EVENT_TYPE_DATA_SESSION = "data_session"

# Mapping from CDR call_type / service_type values to movement event types
_CALL_TYPE_MAP: Dict[str, str] = {
    "voice_incoming": EVENT_TYPE_CALL_START,
    "voice_outgoing": EVENT_TYPE_CALL_START,
    "voice": EVENT_TYPE_CALL_START,
    "call": EVENT_TYPE_CALL_START,
    "incoming": EVENT_TYPE_CALL_START,
    "outgoing": EVENT_TYPE_CALL_START,
    "sms_incoming": EVENT_TYPE_SMS,
    "sms_outgoing": EVENT_TYPE_SMS,
    "sms": EVENT_TYPE_SMS,
    "data": EVENT_TYPE_DATA_SESSION,
    "gprs": EVENT_TYPE_DATA_SESSION,
}


class MovementReconstructionService:
    """Service that reconstructs chronological movement paths from CDR and tracking data."""

    @staticmethod
    def reconstruct_movements(
        db: Session,
        case_code: str,
    ) -> Dict[str, Any]:
        """Reconstruct a chronological movement event sequence for a case.

        1. Decode case_code → load case
        2. Load CDR records and tracking results
        3. Build raw event list from CDR records
        4. Sort chronologically
        5. Detect handover events (CGI transitions)
        6. Merge tracking data for enriched lat/lon
        7. Compute kinematics (speed, heading, distance, dwell time)
        8. Persist MovementEvent rows
        9. Return structured response

        Returns:
            Dictionary with case_code, total_events, events[], handover_count,
            total_distance_km, time_span_hours, computation_time_ms.
        """
        overall_start = time.perf_counter()

        # 1. Decode case code and load case
        case_id = decode_case_code(case_code)
        case = CaseRepository.get(db, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # 2. Load CDR records and tracking results
        cdr_records: List[CDRRecord] = (
            db.query(CDRRecord)
            .filter(CDRRecord.case_id == case_id)
            .order_by(CDRRecord.timestamp.asc())
            .all()
        )

        tracking_results: List[TrackingResult] = (
            db.query(TrackingResult)
            .filter(TrackingResult.case_id == case_id)
            .order_by(TrackingResult.step_number.asc())
            .all()
        )

        if not cdr_records and not tracking_results:
            raise ValidationError(
                "data",
                "No CDR records or tracking results found for this case. "
                "Import CDR data or run tracking first.",
                status_code=400,
            )

        # 3. Build raw event list from CDR records
        raw_events: List[Dict[str, Any]] = []
        for cdr in cdr_records:
            event_type = MovementReconstructionService._classify_event_type(cdr)
            raw_events.append(
                {
                    "cdr_record_id": cdr.id,
                    "tracking_result_id": None,
                    "event_type": event_type,
                    "timestamp": cdr.timestamp,
                    "latitude": cdr.latitude,
                    "longitude": cdr.longitude,
                    "cgi": cdr.first_cgi,
                    "last_cgi": cdr.last_cgi,
                    "metadata": {
                        "operator": cdr.operator,
                        "target_number": cdr.target_number,
                        "b_party_number": cdr.b_party_number,
                        "call_type": cdr.call_type,
                        "service_type": cdr.service_type,
                        "duration": cdr.duration,
                        "imei": cdr.imei,
                        "imsi": cdr.imsi,
                    },
                }
            )

        # 4. Sort chronologically by timestamp
        raw_events.sort(
            key=lambda e: e["timestamp"] or datetime.min.replace(tzinfo=timezone.utc)
        )

        # 5. Detect handover events (CGI transitions between consecutive events)
        events_with_handovers = MovementReconstructionService._detect_handovers(
            raw_events
        )

        # 6. Merge tracking data for enriched coordinates
        MovementReconstructionService._merge_tracking_data(
            events_with_handovers, tracking_results
        )

        # 7. Compute kinematics and assign sequence numbers
        MovementReconstructionService._compute_kinematics(events_with_handovers)

        # 8. Delete previous movement events and persist new ones
        MovementRepository.delete_by_case(db, case_id)

        movement_rows: List[MovementEvent] = []
        for i, evt in enumerate(events_with_handovers):
            row = MovementEvent(
                case_id=case_id,
                cdr_record_id=evt.get("cdr_record_id"),
                tracking_result_id=evt.get("tracking_result_id"),
                sequence_number=i + 1,
                event_type=evt["event_type"],
                timestamp=evt.get("timestamp"),
                latitude=evt.get("latitude"),
                longitude=evt.get("longitude"),
                from_cgi=evt.get("from_cgi"),
                to_cgi=evt.get("to_cgi"),
                speed_kmh=evt.get("speed_kmh"),
                heading_deg=evt.get("heading_deg"),
                distance_from_prev_m=evt.get("distance_from_prev_m"),
                dwell_time_seconds=evt.get("dwell_time_seconds"),
                confidence=evt.get("confidence"),
                metadata_json=evt.get("metadata"),
            )
            movement_rows.append(row)

        if movement_rows:
            MovementRepository.bulk_create(db, movement_rows)

        # 9. Build response
        overall_ms = (time.perf_counter() - overall_start) * 1000.0

        handover_count = sum(
            1 for r in movement_rows if r.event_type == EVENT_TYPE_HANDOVER
        )
        total_distance_m = sum(
            r.distance_from_prev_m or 0.0 for r in movement_rows
        )

        # Time span
        timestamps = [
            r.timestamp for r in movement_rows if r.timestamp is not None
        ]
        time_span_hours = 0.0
        if len(timestamps) >= 2:
            first_ts = min(timestamps)
            last_ts = max(timestamps)
            # Ensure both are tz-aware for subtraction
            if first_ts.tzinfo is None:
                first_ts = first_ts.replace(tzinfo=timezone.utc)
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=timezone.utc)
            time_span_hours = (last_ts - first_ts).total_seconds() / 3600.0

        events_response = []
        for row in movement_rows:
            events_response.append(
                {
                    "sequence_number": row.sequence_number,
                    "event_type": row.event_type,
                    "timestamp": (
                        row.timestamp.isoformat() if row.timestamp else None
                    ),
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "from_cgi": row.from_cgi,
                    "to_cgi": row.to_cgi,
                    "speed_kmh": (
                        round(row.speed_kmh, 2)
                        if row.speed_kmh is not None
                        else None
                    ),
                    "heading_deg": (
                        round(row.heading_deg, 1)
                        if row.heading_deg is not None
                        else None
                    ),
                    "distance_from_prev_m": (
                        round(row.distance_from_prev_m, 2)
                        if row.distance_from_prev_m is not None
                        else None
                    ),
                    "dwell_time_seconds": (
                        round(row.dwell_time_seconds, 1)
                        if row.dwell_time_seconds is not None
                        else None
                    ),
                    "confidence": (
                        round(row.confidence, 3)
                        if row.confidence is not None
                        else None
                    ),
                }
            )

        return {
            "case_code": case_code.upper(),
            "total_events": len(movement_rows),
            "events": events_response,
            "handover_count": handover_count,
            "total_distance_km": round(total_distance_m / 1000.0, 4),
            "time_span_hours": round(time_span_hours, 4),
            "computation_time_ms": round(overall_ms, 2),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_event_type(cdr: CDRRecord) -> str:
        """Map a CDR record's call_type / service_type to a movement event type."""
        call_type = (cdr.call_type or "").strip().lower()
        service_type = (cdr.service_type or "").strip().lower()

        # Try call_type first, then service_type
        for raw_type in (call_type, service_type):
            if raw_type in _CALL_TYPE_MAP:
                return _CALL_TYPE_MAP[raw_type]

        # Default: treat as a generic location update
        return EVENT_TYPE_LOCATION_UPDATE

    @staticmethod
    def _detect_handovers(
        sorted_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Detect cell tower handovers between consecutive CDR events.

        When two consecutive events have different CGI values, a synthetic
        handover event is inserted between them.
        """
        result: List[Dict[str, Any]] = []
        prev_cgi: Optional[str] = None

        for evt in sorted_events:
            current_cgi = evt.get("cgi")

            # Check for handover: CGI changed between consecutive events
            if (
                prev_cgi is not None
                and current_cgi is not None
                and prev_cgi != current_cgi
            ):
                # Insert a synthetic handover event
                handover_evt: Dict[str, Any] = {
                    "cdr_record_id": evt.get("cdr_record_id"),
                    "tracking_result_id": None,
                    "event_type": EVENT_TYPE_HANDOVER,
                    "timestamp": evt.get("timestamp"),
                    "latitude": evt.get("latitude"),
                    "longitude": evt.get("longitude"),
                    "from_cgi": prev_cgi,
                    "to_cgi": current_cgi,
                    "cgi": current_cgi,
                    "metadata": {
                        "handover_from": prev_cgi,
                        "handover_to": current_cgi,
                        "source_event_type": evt["event_type"],
                    },
                }
                result.append(handover_evt)

            # Also check within a single CDR if first_cgi ≠ last_cgi (mid-call handover)
            last_cgi = evt.get("last_cgi")
            if (
                current_cgi is not None
                and last_cgi is not None
                and current_cgi != last_cgi
            ):
                evt["from_cgi"] = current_cgi
                evt["to_cgi"] = last_cgi
                # Keep the original event type but flag the intra-record handover
                if evt.get("metadata") is None:
                    evt["metadata"] = {}
                evt["metadata"]["intra_record_handover"] = True

            result.append(evt)
            prev_cgi = last_cgi if last_cgi else current_cgi

        return result

    @staticmethod
    def _merge_tracking_data(
        events: List[Dict[str, Any]],
        tracking_results: List[TrackingResult],
    ) -> None:
        """Enrich movement events with smoothed lat/lon from tracking results.

        For each event with a timestamp, find the nearest tracking result by
        timestamp and use its smoothed coordinates if they provide better data.
        Also assigns tracking_result_id and confidence from tracking error.
        """
        if not tracking_results:
            return

        # Build a list of (timestamp, tracking_result) for binary search
        tr_with_ts: List[Tuple[datetime, TrackingResult]] = []
        for tr in tracking_results:
            ts = tr.timestamp
            if ts is not None:
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts)
                    except (ValueError, TypeError):
                        continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                tr_with_ts.append((ts, tr))

        if not tr_with_ts:
            return

        tr_with_ts.sort(key=lambda x: x[0])
        tr_timestamps = [t[0] for t in tr_with_ts]

        for evt in events:
            evt_ts = evt.get("timestamp")
            if evt_ts is None:
                continue
            if evt_ts.tzinfo is None:
                evt_ts = evt_ts.replace(tzinfo=timezone.utc)

            # Find the nearest tracking result by binary search
            idx = _bisect_nearest(tr_timestamps, evt_ts)
            nearest_ts, nearest_tr = tr_with_ts[idx]

            # Only merge if within 5 minutes
            delta_s = abs((evt_ts - nearest_ts).total_seconds())
            if delta_s <= 300:
                # Use smoothed coordinates if the event lacks them
                if evt.get("latitude") is None or evt.get("longitude") is None:
                    evt["latitude"] = nearest_tr.smoothed_latitude
                    evt["longitude"] = nearest_tr.smoothed_longitude

                evt["tracking_result_id"] = nearest_tr.id

                # Compute confidence from tracking error
                error_m = nearest_tr.error_m
                if error_m is not None:
                    # Confidence inversely proportional to error
                    # 0m → 1.0, 1000m → ~0.37, 5000m → ~0.007
                    evt["confidence"] = math.exp(-error_m / 1000.0)

    @staticmethod
    def _compute_kinematics(events: List[Dict[str, Any]]) -> None:
        """Compute speed, heading, distance, and dwell time between consecutive events."""
        for i, evt in enumerate(events):
            if i == 0:
                evt["distance_from_prev_m"] = 0.0
                evt["speed_kmh"] = 0.0
                evt["dwell_time_seconds"] = 0.0
                continue

            prev = events[i - 1]
            lat1, lon1 = prev.get("latitude"), prev.get("longitude")
            lat2, lon2 = evt.get("latitude"), evt.get("longitude")
            ts1, ts2 = prev.get("timestamp"), evt.get("timestamp")

            # Distance
            dist_m = 0.0
            if (
                lat1 is not None
                and lon1 is not None
                and lat2 is not None
                and lon2 is not None
            ):
                dist_m = haversine_distance_m(lat1, lon1, lat2, lon2)
            evt["distance_from_prev_m"] = dist_m

            # Time delta
            dt_seconds = 0.0
            if ts1 is not None and ts2 is not None:
                if ts1.tzinfo is None:
                    ts1 = ts1.replace(tzinfo=timezone.utc)
                if ts2.tzinfo is None:
                    ts2 = ts2.replace(tzinfo=timezone.utc)
                dt_seconds = max((ts2 - ts1).total_seconds(), 0.0)

            # Speed (km/h)
            if dt_seconds > 0:
                speed_mps = dist_m / dt_seconds
                evt["speed_kmh"] = speed_mps * 3.6
            else:
                evt["speed_kmh"] = 0.0

            # Heading (bearing from prev to current)
            if (
                lat1 is not None
                and lon1 is not None
                and lat2 is not None
                and lon2 is not None
                and dist_m > 1.0  # only compute if moved > 1m
            ):
                evt["heading_deg"] = _compute_bearing(lat1, lon1, lat2, lon2)
            else:
                evt["heading_deg"] = None

            # Dwell time: time spent at previous location
            evt["dwell_time_seconds"] = dt_seconds


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _bisect_nearest(sorted_ts: List[datetime], target: datetime) -> int:
    """Find the index of the nearest timestamp in a sorted list."""
    import bisect

    pos = bisect.bisect_left(sorted_ts, target)
    if pos == 0:
        return 0
    if pos == len(sorted_ts):
        return len(sorted_ts) - 1
    before = sorted_ts[pos - 1]
    after = sorted_ts[pos]
    if abs((target - before).total_seconds()) <= abs(
        (after - target).total_seconds()
    ):
        return pos - 1
    return pos


def _compute_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute initial bearing (degrees, 0-360) from point 1 to point 2."""
    rlat1 = math.radians(lat1)
    rlat2 = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)

    x = math.sin(dlon) * math.cos(rlat2)
    y = math.cos(rlat1) * math.sin(rlat2) - math.sin(rlat1) * math.cos(
        rlat2
    ) * math.cos(dlon)

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360.0) % 360.0
