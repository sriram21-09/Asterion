"""
Test Suite — Kalman Movement Path Smoothing
=============================================

Validates the smooth_movement_path function that bridges
movement reconstruction with the Kalman tracker.
"""

from datetime import UTC, datetime, timedelta

import pytest

from scientific.pipeline.movement import (
    reconstruct_movement_events,
    smooth_movement_path,
)


# ── Helpers ────────────────────────────────────────────────────────────────

MUMBAI = (19.0760, 72.8777)
DELHI = (28.6139, 77.2090)
SURAT = (21.1702, 72.8311)
BASE_TS = datetime(2026, 7, 23, 10, 0, 0, tzinfo=UTC)


def _make_record(ts_offset_min, lat, lon, cgi, event_type="call_start"):
    return {
        "timestamp": BASE_TS + timedelta(minutes=ts_offset_min),
        "latitude": lat,
        "longitude": lon,
        "first_cgi": cgi,
        "event_type": event_type,
        "operator": "airtel",
    }


# ═══════════════════════════════════════════════════════════════════════════
# 1. Edge cases
# ═══════════════════════════════════════════════════════════════════════════


class TestSmoothEdgeCases:
    """Edge case handling for smooth_movement_path."""

    def test_empty_summary(self):
        summary = reconstruct_movement_events([])
        smoothed = smooth_movement_path(summary)
        assert smoothed.total_events == 0
        assert smoothed.total_distance_m == 0.0

    def test_single_event_unchanged(self):
        records = [_make_record(0, 19.076, 72.878, "A")]
        summary = reconstruct_movement_events(records)
        smoothed = smooth_movement_path(summary)

        assert smoothed.total_events == 1
        assert smoothed.events[0].latitude == pytest.approx(19.076, abs=0.001)
        assert smoothed.events[0].longitude == pytest.approx(72.878, abs=0.001)

    def test_no_coordinates_returns_unchanged(self):
        """All events with None coords → no smoothing possible."""
        records = [
            _make_record(0, None, None, "A"),
            _make_record(5, None, None, "B"),
        ]
        summary = reconstruct_movement_events(records)
        smoothed = smooth_movement_path(summary)

        # Should return unchanged
        assert smoothed.total_events == 2
        assert smoothed.events[0].latitude is None


# ═══════════════════════════════════════════════════════════════════════════
# 2. Anomaly dampening
# ═══════════════════════════════════════════════════════════════════════════


class TestAnomalyDampening:
    """Verify that anomalous velocity spikes are dampened by Kalman smoothing."""

    def test_impossible_velocity_smoothed(self):
        """Mumbai→Delhi in 1 min is impossible; smoothing should reduce the jump."""
        records = [
            _make_record(0, *MUMBAI, "A"),
            _make_record(1, *DELHI, "B"),  # Impossible: ~1150km in 1 min
        ]

        raw = reconstruct_movement_events(records)
        assert raw.anomaly_count == 1
        assert raw.events[1].is_anomalous is True

        smoothed = smooth_movement_path(raw)

        # The smoothed position should NOT jump all the way to Delhi
        # because the Kalman filter distrusts the anomalous measurement
        raw_dist = raw.total_distance_m
        smoothed_dist = smoothed.total_distance_m
        assert smoothed_dist < raw_dist, (
            f"Smoothed distance ({smoothed_dist:.0f}m) should be less than "
            f"raw distance ({raw_dist:.0f}m)"
        )

    def test_anomalous_max_speed_reduced(self):
        """Smoothing a noisy sequence should reduce max speed."""
        records = [
            _make_record(0, *MUMBAI, "A"),
            _make_record(60, *SURAT, "B"),  # ~250km in 1hr = ~250 km/h
            _make_record(61, *DELHI, "C"),  # ~1000km in 1 min = anomalous
            _make_record(120, 28.62, 77.21, "D"),  # Slight move near Delhi
        ]

        raw = reconstruct_movement_events(records)
        smoothed = smooth_movement_path(raw)

        assert smoothed.max_speed_kmh < raw.max_speed_kmh


# ═══════════════════════════════════════════════════════════════════════════
# 3. Handover preservation
# ═══════════════════════════════════════════════════════════════════════════


class TestHandoverPreservation:
    """Verify handover events maintain their semantics after smoothing."""

    def test_handover_preserved(self):
        """Handover events should retain is_handover=True and zero distance."""
        records = [
            _make_record(0, 19.076, 72.878, "404-98-100-1"),
            _make_record(5, 19.076, 72.878, "404-98-100-2"),  # Handover
            _make_record(10, 19.080, 72.880, "404-98-200-5"),  # Movement
        ]

        raw = reconstruct_movement_events(records)
        assert raw.handover_count == 1

        smoothed = smooth_movement_path(raw)

        assert smoothed.handover_count == 1
        assert smoothed.events[1].is_handover is True
        assert smoothed.events[1].distance_m == 0.0
        assert smoothed.events[1].speed_kmh == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 4. General smoothing properties
# ═══════════════════════════════════════════════════════════════════════════


class TestSmoothingProperties:
    """Verify general properties of the smoothing operation."""

    def test_event_count_preserved(self):
        """Smoothing should not add or remove events."""
        records = [
            _make_record(0, 19.076, 72.878, "A"),
            _make_record(30, 19.080, 72.880, "B"),
            _make_record(60, 19.085, 72.882, "C"),
            _make_record(90, 19.090, 72.884, "D"),
        ]

        raw = reconstruct_movement_events(records)
        smoothed = smooth_movement_path(raw)

        assert smoothed.total_events == raw.total_events

    def test_time_span_preserved(self):
        """Time span should be identical before and after smoothing."""
        records = [
            _make_record(0, 19.076, 72.878, "A"),
            _make_record(120, 19.090, 72.890, "B"),
        ]

        raw = reconstruct_movement_events(records)
        smoothed = smooth_movement_path(raw)

        assert smoothed.time_span_seconds == pytest.approx(
            raw.time_span_seconds, abs=1.0
        )

    def test_velocity_distribution_populated(self):
        """Smoothed summary should still have velocity distribution."""
        records = [
            _make_record(0, 19.076, 72.878, "A"),
            _make_record(60, 19.080, 72.880, "B"),
            _make_record(120, 19.085, 72.882, "C"),
        ]

        raw = reconstruct_movement_events(records)
        smoothed = smooth_movement_path(raw)

        assert isinstance(smoothed.velocity_distribution, dict)
        assert sum(smoothed.velocity_distribution.values()) == smoothed.total_events

    def test_smooth_normal_path_minimal_change(self):
        """A smooth, plausible path should see minimal coordinate changes."""
        # Slow, consistent movement — Kalman should track closely
        records = [
            _make_record(0, 19.0760, 72.8780, "A"),
            _make_record(60, 19.0765, 72.8785, "B"),
            _make_record(120, 19.0770, 72.8790, "C"),
            _make_record(180, 19.0775, 72.8795, "D"),
        ]

        raw = reconstruct_movement_events(records)
        smoothed = smooth_movement_path(raw)

        # Coordinates should be very close to originals for smooth input
        for raw_evt, sm_evt in zip(raw.events, smoothed.events):
            if raw_evt.latitude is not None:
                assert sm_evt.latitude == pytest.approx(raw_evt.latitude, abs=0.01)
                assert sm_evt.longitude == pytest.approx(raw_evt.longitude, abs=0.01)

    def test_distance_km_consistent(self):
        """total_distance_km should be total_distance_m / 1000."""
        records = [
            _make_record(0, *MUMBAI, "A"),
            _make_record(120, *SURAT, "B"),
        ]

        raw = reconstruct_movement_events(records)
        smoothed = smooth_movement_path(raw)

        assert smoothed.total_distance_km == pytest.approx(
            smoothed.total_distance_m / 1000.0, rel=0.01
        )
