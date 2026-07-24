"""
Test Suite — Movement Reconstruction Scientific Module
=======================================================

Validates distance/speed calculators, handover detection, velocity
classification, anomaly flagging, and full reconstruction logic.
"""

from datetime import datetime, timezone, timedelta

import pytest

from scientific.pipeline.movement import (
    calculate_distance_m,
    calculate_speed_kmh,
    calculate_bearing_deg,
    detect_handover,
    classify_velocity,
    flag_impossible_velocity,
    reconstruct_movement_events,
)


# ── Coordinates used across tests ──────────────────────────────────────────

MUMBAI = (19.0760, 72.8777)
PUNE = (18.5204, 73.8567)
DELHI = (28.6139, 77.2090)
SURAT = (21.1702, 72.8311)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Distance Calculator
# ═══════════════════════════════════════════════════════════════════════════


class TestCalculateDistanceM:
    """Tests for calculate_distance_m."""

    def test_same_point_returns_zero(self):
        d = calculate_distance_m(*MUMBAI, *MUMBAI)
        assert d == pytest.approx(0.0, abs=0.01)

    def test_mumbai_to_pune_reference(self):
        """Well-known reference: Mumbai → Pune ≈ 120 km geodesic (straight-line)."""
        d = calculate_distance_m(*MUMBAI, *PUNE)
        assert d is not None
        assert 118_000 < d < 125_000

    def test_mumbai_to_delhi(self):
        """Mumbai → Delhi ≈ 1150 km."""
        d = calculate_distance_m(*MUMBAI, *DELHI)
        assert d is not None
        assert 1_100_000 < d < 1_200_000

    def test_null_lat1_returns_none(self):
        assert calculate_distance_m(None, 72.8, 18.5, 73.8) is None

    def test_null_lon2_returns_none(self):
        assert calculate_distance_m(19.0, 72.8, 18.5, None) is None

    def test_all_none_returns_none(self):
        assert calculate_distance_m(None, None, None, None) is None

    def test_equator_one_degree(self):
        """One degree of longitude at the equator ≈ 111.32 km."""
        d = calculate_distance_m(0.0, 0.0, 0.0, 1.0)
        assert d is not None
        assert 110_000 < d < 112_000

    def test_symmetry(self):
        d1 = calculate_distance_m(*MUMBAI, *PUNE)
        d2 = calculate_distance_m(*PUNE, *MUMBAI)
        assert d1 == pytest.approx(d2, rel=1e-9)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Speed Calculator
# ═══════════════════════════════════════════════════════════════════════════


class TestCalculateSpeedKmh:
    """Tests for calculate_speed_kmh."""

    def test_normal_speed(self):
        # 100 km in 1 hour = 100 km/h
        s = calculate_speed_kmh(100_000.0, 3600.0)
        assert s == pytest.approx(100.0, rel=1e-6)

    def test_zero_time_returns_zero(self):
        assert calculate_speed_kmh(1000.0, 0.0) == 0.0

    def test_negative_time_returns_zero(self):
        assert calculate_speed_kmh(1000.0, -5.0) == 0.0

    def test_none_distance_returns_none(self):
        assert calculate_speed_kmh(None, 60.0) is None

    def test_none_time_returns_none(self):
        assert calculate_speed_kmh(500.0, None) is None

    def test_walking_speed(self):
        # 1.4 m/s ≈ 5 km/h
        s = calculate_speed_kmh(1.4, 1.0)
        assert s == pytest.approx(5.04, rel=0.01)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Bearing Calculator
# ═══════════════════════════════════════════════════════════════════════════


class TestCalculateBearingDeg:
    """Tests for calculate_bearing_deg."""

    def test_due_north(self):
        b = calculate_bearing_deg(0.0, 0.0, 1.0, 0.0)
        assert b == pytest.approx(0.0, abs=0.1)

    def test_due_east(self):
        b = calculate_bearing_deg(0.0, 0.0, 0.0, 1.0)
        assert b == pytest.approx(90.0, abs=0.1)

    def test_due_south(self):
        b = calculate_bearing_deg(1.0, 0.0, 0.0, 0.0)
        assert b == pytest.approx(180.0, abs=0.1)

    def test_due_west(self):
        b = calculate_bearing_deg(0.0, 1.0, 0.0, 0.0)
        assert b == pytest.approx(270.0, abs=0.1)

    def test_same_point(self):
        b = calculate_bearing_deg(10.0, 20.0, 10.0, 20.0)
        assert b is not None  # Returns 0.0 by convention

    def test_null_returns_none(self):
        assert calculate_bearing_deg(None, 0.0, 1.0, 0.0) is None

    def test_result_in_range(self):
        b = calculate_bearing_deg(*MUMBAI, *PUNE)
        assert b is not None
        assert 0.0 <= b < 360.0


# ═══════════════════════════════════════════════════════════════════════════
# 4. Handover Detection
# ═══════════════════════════════════════════════════════════════════════════


class TestDetectHandover:
    """Tests for detect_handover."""

    def test_same_cgi_not_handover(self):
        assert (
            detect_handover("404-98-100-1", "404-98-100-1", 19.0, 72.8, 19.0, 72.8)
            is False
        )

    def test_different_cgi_same_coords_is_handover(self):
        """Different sector (CGI) at identical coordinates → handover."""
        assert (
            detect_handover(
                "404-98-100-1", "404-98-100-2", 19.076, 72.878, 19.076, 72.878
            )
            is True
        )

    def test_different_cgi_close_coords_is_handover(self):
        """Coords ~30m apart (within 50m tolerance) → handover."""
        # ~30m shift in latitude
        assert (
            detect_handover(
                "404-98-100-1",
                "404-98-100-2",
                19.076000,
                72.878000,
                19.076270,
                72.878000,  # ~30m north
            )
            is True
        )

    def test_different_cgi_far_coords_not_handover(self):
        """Different CGI + coordinates far apart → real movement."""
        assert detect_handover("404-98-100-1", "404-98-200-5", *MUMBAI, *PUNE) is False

    def test_none_prev_cgi(self):
        assert detect_handover(None, "404-98-100-1", 19.0, 72.8, 19.0, 72.8) is False

    def test_none_curr_cgi(self):
        assert detect_handover("404-98-100-1", None, 19.0, 72.8, 19.0, 72.8) is False

    def test_missing_coords_not_handover(self):
        """Cannot determine without coords → conservatively False."""
        assert (
            detect_handover("404-98-100-1", "404-98-100-2", None, None, None, None)
            is False
        )

    def test_boundary_at_tolerance(self):
        """Exactly at the tolerance boundary should still be a handover."""
        # Use a custom tolerance
        assert (
            detect_handover(
                "A",
                "B",
                0.0,
                0.0,
                0.0,
                0.0,
                coord_tolerance_m=0.0,
            )
            is True
        )  # distance=0 ≤ 0


# ═══════════════════════════════════════════════════════════════════════════
# 5. Velocity Classification
# ═══════════════════════════════════════════════════════════════════════════


class TestClassifyVelocity:
    """Tests for classify_velocity."""

    def test_stationary(self):
        assert classify_velocity(0.0) == "stationary"
        assert classify_velocity(0.5) == "stationary"

    def test_walking(self):
        assert classify_velocity(1.0) == "walking"
        assert classify_velocity(5.0) == "walking"

    def test_driving(self):
        assert classify_velocity(7.0) == "driving"
        assert classify_velocity(60.0) == "driving"
        assert classify_velocity(119.9) == "driving"

    def test_highway(self):
        assert classify_velocity(120.0) == "highway"
        assert classify_velocity(250.0) == "highway"
        assert classify_velocity(350.0) == "highway"

    def test_anomalous(self):
        assert classify_velocity(351.0) == "anomalous"
        assert classify_velocity(1000.0) == "anomalous"

    def test_none_returns_unknown(self):
        assert classify_velocity(None) == "unknown"

    def test_negative_returns_unknown(self):
        assert classify_velocity(-10.0) == "unknown"

    def test_custom_threshold(self):
        assert classify_velocity(200.0, max_plausible_kmh=150.0) == "anomalous"


# ═══════════════════════════════════════════════════════════════════════════
# 6. Impossible Velocity Flag
# ═══════════════════════════════════════════════════════════════════════════


class TestFlagImpossibleVelocity:
    """Tests for flag_impossible_velocity."""

    def test_below_threshold(self):
        assert flag_impossible_velocity(100.0) is False

    def test_at_threshold(self):
        assert flag_impossible_velocity(350.0) is False

    def test_above_threshold(self):
        assert flag_impossible_velocity(351.0) is True

    def test_none_returns_false(self):
        assert flag_impossible_velocity(None) is False

    def test_custom_threshold(self):
        assert flag_impossible_velocity(200.0, threshold_kmh=150.0) is True
        assert flag_impossible_velocity(100.0, threshold_kmh=150.0) is False


# ═══════════════════════════════════════════════════════════════════════════
# 7. End-to-End Reconstruction
# ═══════════════════════════════════════════════════════════════════════════


class TestReconstructMovementEvents:
    """Integration tests for reconstruct_movement_events."""

    @staticmethod
    def _make_record(ts_offset_min, lat, lon, cgi, event_type="call_start"):
        base = datetime(2026, 7, 23, 10, 0, 0, tzinfo=timezone.utc)
        return {
            "timestamp": base + timedelta(minutes=ts_offset_min),
            "latitude": lat,
            "longitude": lon,
            "first_cgi": cgi,
            "event_type": event_type,
            "operator": "airtel",
        }

    def test_empty_records(self):
        summary = reconstruct_movement_events([])
        assert summary.total_events == 0
        assert summary.total_distance_m == 0.0

    def test_single_record(self):
        records = [self._make_record(0, 19.076, 72.878, "404-98-100-1")]
        summary = reconstruct_movement_events(records)
        assert summary.total_events == 1
        assert summary.events[0].sequence == 1
        assert summary.events[0].distance_m == 0.0

    def test_normal_movement(self):
        """Two records at different locations → non-zero distance and speed."""
        records = [
            self._make_record(0, *SURAT, "404-98-100-1"),
            self._make_record(60, *MUMBAI, "404-98-200-5"),  # 1 hour later
        ]
        summary = reconstruct_movement_events(records)
        assert summary.total_events == 2
        assert summary.total_distance_m > 200_000  # Surat→Mumbai ~250km
        assert summary.events[1].speed_kmh > 0

    def test_handover_detection(self):
        """Same coords, different CGI → handover with zero distance/speed."""
        records = [
            self._make_record(0, 19.076, 72.878, "404-98-100-1"),
            self._make_record(5, 19.076, 72.878, "404-98-100-2"),
        ]
        summary = reconstruct_movement_events(records)
        assert summary.handover_count == 1
        assert summary.events[1].is_handover is True
        assert summary.events[1].distance_m == 0.0
        assert summary.events[1].speed_kmh == 0.0

    def test_impossible_velocity_flagged(self):
        """Very far apart in very short time → anomalous."""
        records = [
            self._make_record(0, *MUMBAI, "404-98-100-1"),
            self._make_record(1, *DELHI, "404-98-200-5"),  # 1 min for ~1150km
        ]
        summary = reconstruct_movement_events(records)
        assert summary.anomaly_count == 1
        assert summary.events[1].is_anomalous is True
        assert summary.events[1].velocity_class == "anomalous"

    def test_mixed_sequence(self):
        """Multi-step: normal → handover → anomalous."""
        records = [
            self._make_record(0, 19.076, 72.878, "A"),
            self._make_record(30, 19.080, 72.880, "B"),  # short move
            self._make_record(35, 19.080, 72.880, "C"),  # handover
            self._make_record(36, *DELHI, "D"),  # impossible
        ]
        summary = reconstruct_movement_events(records)
        assert summary.total_events == 4
        assert summary.handover_count == 1
        assert summary.anomaly_count == 1
        assert summary.events[2].is_handover is True
        assert summary.events[3].is_anomalous is True

    def test_velocity_distribution_populated(self):
        records = [
            self._make_record(0, 19.076, 72.878, "A"),
            self._make_record(60, 19.080, 72.880, "B"),
        ]
        summary = reconstruct_movement_events(records)
        assert isinstance(summary.velocity_distribution, dict)
        assert sum(summary.velocity_distribution.values()) == 2

    def test_time_span_calculation(self):
        records = [
            self._make_record(0, 19.0, 72.8, "A"),
            self._make_record(120, 19.1, 72.9, "B"),  # 2 hours later
        ]
        summary = reconstruct_movement_events(records)
        assert summary.time_span_seconds == pytest.approx(7200.0, abs=1.0)

    def test_summary_distance_km(self):
        records = [
            self._make_record(0, *SURAT, "A"),
            self._make_record(120, *MUMBAI, "B"),
        ]
        summary = reconstruct_movement_events(records)
        assert summary.total_distance_km > 200  # ~250 km

    def test_records_as_objects(self):
        """Verify that object-style records (attrs) also work."""

        class FakeRecord:
            def __init__(self, ts, lat, lon, cgi):
                self.timestamp = ts
                self.latitude = lat
                self.longitude = lon
                self.first_cgi = cgi
                self.event_type = "sms"

        base = datetime(2026, 7, 23, 10, 0, 0, tzinfo=timezone.utc)
        records = [
            FakeRecord(base, 19.076, 72.878, "X-1"),
            FakeRecord(base + timedelta(minutes=10), 19.076, 72.878, "X-2"),
        ]
        summary = reconstruct_movement_events(records)
        assert summary.total_events == 2
        assert summary.handover_count == 1

    def test_null_coordinates_handled(self):
        """Records with None lat/lon should not crash."""
        records = [
            self._make_record(0, None, None, "A"),
            self._make_record(5, 19.076, 72.878, "B"),
        ]
        summary = reconstruct_movement_events(records)
        assert summary.total_events == 2
        assert (
            summary.events[1].distance_m is None or summary.events[1].distance_m == 0.0
        )
