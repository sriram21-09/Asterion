"""
Comprehensive Verification Tests for Validation Extensions
===========================================================

Tests the new validation features implemented in scientific/validation/validators.py:
  1. Coordinate range checking (WGS84 & custom operational area bounds).
  2. Missing value checks.
  3. Duplicate record detection (duplicate IDs, duplicate tower-timestamp).
  4. Physics-based Timing Advance vs RSSI decay consistency cross-checks.
"""

from datetime import UTC, datetime

import pytest

from scientific.config import ValidationThresholds
from scientific.models.measurement import Measurement
from scientific.models.scenario import Scenario
from scientific.models.tower import Tower
from scientific.validation.validators import (
    MeasurementValidator,
    ScenarioValidator,
    Severity,
    TowerValidator,
    validate_measurement,
    validate_scenario,
    validate_tower,
)


class TestMissingValues:
    """Tests that missing required fields are correctly caught by validators."""

    def test_measurement_missing_fields(self):
        # We construct measurements with invalid empty strings to bypass Pydantic min_length
        m = Measurement.construct(
            measurement_id="",
            tower_id="",
            timestamp=None,
            rssi_dbm=None,
        )
        validator = MeasurementValidator()
        result = validator.validate(m)
        assert not result.is_valid
        error_codes = {e.code for e in result.errors}
        assert "MEAS_MISSING_ID" in error_codes
        assert "MEAS_MISSING_TOWER_ID" in error_codes
        assert "MEAS_MISSING_TIMESTAMP" in error_codes
        assert "MEAS_MISSING_RSSI" in error_codes

    def test_tower_missing_fields(self):
        t = Tower.construct(
            tower_id="",
            latitude=None,
            longitude=None,
            antenna_height_m=None,
            frequency_mhz=None,
            transmit_power_dbm=None,
            coverage_radius_m=None,
        )
        validator = TowerValidator()
        result = validator.validate(t)
        assert not result.is_valid
        error_codes = {e.code for e in result.errors}
        assert "TOWER_MISSING_ID" in error_codes
        assert "TOWER_MISSING_COORDS" in error_codes
        assert "TOWER_MISSING_HEIGHT" in error_codes
        assert "TOWER_MISSING_FREQUENCY" in error_codes
        assert "TOWER_MISSING_TX_POWER" in error_codes
        assert "TOWER_MISSING_RADIUS" in error_codes

    def test_scenario_missing_fields(self):
        s = Scenario.construct(
            scenario_id="",
            name="",
            towers=None,
            measurements=[],
        )
        validator = ScenarioValidator()
        result = validator.validate(s)
        assert not result.is_valid
        error_codes = {e.code for e in result.errors}
        assert "SCENARIO_MISSING_ID" in error_codes
        assert "SCENARIO_MISSING_NAME" in error_codes
        assert "SCENARIO_INSUFFICIENT_TOWERS" in error_codes


class TestCoordinateOperationalBounds:
    """Tests WGS84 spatial bounds verification against expected operational areas."""

    def test_default_wgs84_bounds(self):
        # Default WGS84 coordinates bounds are [-90, 90] and [-180, 180].
        # Pydantic validates these at model initialization. Let's test out of bounds via construct().
        m = Measurement.construct(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(UTC),
            rssi_dbm=-70.0,
            latitude=95.0,
            longitude=190.0,
        )
        r = validate_measurement(m)
        assert not r.is_valid
        assert any(e.code == "MEAS_COORDS_OUT_OF_BOUNDS" for e in r.errors)

    def test_custom_operational_bounds(self):
        # Define a custom operational boundary (e.g., Bengaluru region)
        bengaluru_thresholds = ValidationThresholds(
            latitude_range=(12.8, 13.1),
            longitude_range=(77.4, 77.8),
        )

        # Coordinate inside bounds
        m_inside = Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(UTC),
            rssi_dbm=-70.0,
            latitude=12.9716,
            longitude=77.5946,
        )
        r_inside = validate_measurement(m_inside, thresholds=bengaluru_thresholds)
        assert r_inside.is_valid

        # Coordinate outside bounds (New Delhi)
        m_outside = Measurement(
            measurement_id="M002",
            tower_id="T001",
            timestamp=datetime.now(UTC),
            rssi_dbm=-70.0,
            latitude=28.6139,
            longitude=77.2090,
        )
        r_outside = validate_measurement(m_outside, thresholds=bengaluru_thresholds)
        assert not r_outside.is_valid
        assert any(e.code == "MEAS_COORDS_OUT_OF_BOUNDS" for e in r_outside.errors)

    def test_tower_custom_operational_bounds(self):
        bengaluru_thresholds = ValidationThresholds(
            latitude_range=(12.8, 13.1),
            longitude_range=(77.4, 77.8),
        )

        # Tower outside bounds (New Delhi)
        t_outside = Tower(
            tower_id="T001",
            latitude=28.6139,
            longitude=77.2090,
        )
        r = validate_tower(t_outside, thresholds=bengaluru_thresholds)
        assert not r.is_valid
        assert any(e.code == "TOWER_COORDS_OUT_OF_BOUNDS" for e in r.errors)

    def test_scenario_custom_operational_bounds(self):
        bengaluru_thresholds = ValidationThresholds(
            latitude_range=(12.8, 13.1),
            longitude_range=(77.4, 77.8),
        )

        towers = [
            Tower(tower_id="T001", latitude=12.9716, longitude=77.5946),
            Tower(tower_id="T002", latitude=12.9750, longitude=77.5900),
            Tower(tower_id="T003", latitude=12.9700, longitude=77.6000),
        ]

        # Scenario ground-truth outside bounds
        s_outside = Scenario(
            scenario_id="SCN-001",
            name="Delhi GT Test",
            towers=towers,
            expected_device_lat=28.6139,
            expected_device_lon=77.2090,
        )
        r = validate_scenario(s_outside, thresholds=bengaluru_thresholds)
        assert not r.is_valid
        assert any(e.code == "SCENARIO_COORDS_OUT_OF_BOUNDS" for e in r.errors)


class TestDuplicateRecords:
    """Tests duplicate checking (IDs and records/timestamps) in ScenarioValidator."""

    @pytest.fixture
    def valid_towers(self):
        return [
            Tower(tower_id="T001", latitude=12.9716, longitude=77.5946),
            Tower(tower_id="T002", latitude=12.9750, longitude=77.5900),
            Tower(tower_id="T003", latitude=12.9700, longitude=77.6000),
        ]

    def test_duplicate_measurement_ids_rejected(self, valid_towers):
        ts = datetime.now(UTC)
        measurements = [
            Measurement(
                measurement_id="M001", tower_id="T001", timestamp=ts, rssi_dbm=-70.0
            ),
            Measurement(
                measurement_id="M001", tower_id="T002", timestamp=ts, rssi_dbm=-80.0
            ),  # Dup ID
        ]
        s = Scenario(
            scenario_id="SCN-001",
            name="Duplicate ID Scenario",
            towers=valid_towers,
            measurements=measurements,
        )
        r = validate_scenario(s)
        assert not r.is_valid
        assert any(e.code == "SCENARIO_DUPLICATE_MEASUREMENT" for e in r.errors)

    def test_duplicate_timestamps_for_same_tower_rejected(self, valid_towers):
        ts = datetime.now(UTC)
        measurements = [
            Measurement(
                measurement_id="M001", tower_id="T001", timestamp=ts, rssi_dbm=-70.0
            ),
            Measurement(
                measurement_id="M002", tower_id="T001", timestamp=ts, rssi_dbm=-72.0
            ),  # Same tower & timestamp
        ]
        s = Scenario(
            scenario_id="SCN-001",
            name="Duplicate Timestamp Scenario",
            towers=valid_towers,
            measurements=measurements,
        )
        r = validate_scenario(s)
        assert not r.is_valid
        assert any(e.code == "SCENARIO_DUPLICATE_RECORD" for e in r.errors)


class TestPhysicsTAvsRSSI:
    """Tests the physics-based Timing Advance vs RSSI signal decay model consistency checks."""

    @pytest.fixture
    def standard_towers(self):
        # standard macro cells with 43 dBm EIRP
        return [
            Tower(
                tower_id="T001",
                latitude=12.9716,
                longitude=77.5946,
                transmit_power_dbm=43.0,
            ),
            Tower(
                tower_id="T002",
                latitude=12.9750,
                longitude=77.5900,
                transmit_power_dbm=43.0,
            ),
            Tower(
                tower_id="T003",
                latitude=12.9700,
                longitude=77.6000,
                transmit_power_dbm=43.0,
            ),
        ]

    def test_consistent_ta_rssi_passes(self, standard_towers):
        # TA of 1 implies distance ~550m.
        # In urban environment: PL exponent=3.5, ref loss=38dB.
        # Expected path loss at 550m ≈ 38 + 35 * log10(550) ≈ 38 + 95.9 ≈ 133.9 dB.
        # Expected RSSI ≈ 43 - 133.9 = -90.9 dBm.
        # An RSSI of -90 dBm should be perfectly fine.
        ts = datetime.now(UTC)
        measurements = [
            Measurement(
                measurement_id="M001",
                tower_id="T001",
                timestamp=ts,
                rssi_dbm=-90.0,
                timing_advance=1,
            ),
        ]
        s = Scenario(
            scenario_id="SCN-001",
            name="Consistent Scenario",
            towers=standard_towers,
            measurements=measurements,
            environment_type="urban",
        )
        r = validate_scenario(s)
        assert r.is_valid
        # Check there are no warnings for TA/RSSI mismatch
        assert not any(e.code == "SCENARIO_TA_RSSI_PHYSICS_MISMATCH" for e in r.errors)

    def test_inconsistent_strong_rssi_warns(self, standard_towers):
        # TA of 10 implies distance ~5500m (5.5km).
        # Expected path loss at 5500m ≈ 38 + 35 * log10(5500) ≈ 38 + 130.9 ≈ 168.9 dB.
        # Expected RSSI ≈ 43 - 168.9 = -125.9 dBm.
        # Shadow fading std is 8dB. 3 * std = 24dB. Upper bound ≈ -101.9 dBm.
        # A measurement with RSSI of -50 dBm is physically way too strong for 5.5km!
        ts = datetime.now(UTC)
        measurements = [
            Measurement(
                measurement_id="M001",
                tower_id="T001",
                timestamp=ts,
                rssi_dbm=-50.0,
                timing_advance=10,
            ),
        ]
        s = Scenario(
            scenario_id="SCN-001",
            name="Inconsistent Strong Scenario",
            towers=standard_towers,
            measurements=measurements,
            environment_type="urban",
        )
        r = validate_scenario(s)
        # Should be valid but raise warning
        assert r.is_valid
        assert any(
            e.code == "SCENARIO_TA_RSSI_PHYSICS_MISMATCH"
            and e.severity == Severity.WARNING
            for e in r.errors
        )

    def test_inconsistent_weak_rssi_warns(self, standard_towers):
        # TA of 0 implies distance range 0 to 275m.
        # Max distance 275m. Expected path loss at 275m ≈ 38 + 35 * log10(275) ≈ 38 + 85.3 ≈ 123.3 dB.
        # Expected RSSI at 275m ≈ 43 - 123.3 = -80.3 dBm.
        # Shadow fading std is 8dB. 4 * std = 32dB. Lower bound ≈ -112.3 dBm.
        # A measurement with RSSI of -140 dBm is physically way too weak for TA 0!
        ts = datetime.now(UTC)
        measurements = [
            Measurement(
                measurement_id="M001",
                tower_id="T001",
                timestamp=ts,
                rssi_dbm=-140.0,
                timing_advance=0,
            ),
        ]
        s = Scenario(
            scenario_id="SCN-001",
            name="Inconsistent Weak Scenario",
            towers=standard_towers,
            measurements=measurements,
            environment_type="urban",
        )
        r = validate_scenario(s)
        assert r.is_valid
        assert any(
            e.code == "SCENARIO_TA_RSSI_PHYSICS_MISMATCH"
            and e.severity == Severity.WARNING
            for e in r.errors
        )
