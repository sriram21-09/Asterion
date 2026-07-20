import pytest
from datetime import datetime, timezone

from scientific.models.measurement import Measurement
from scientific.models.tower import Tower
from scientific.pipeline.weighted_centroid import solve_weighted_centroid


def test_weighted_centroid_symmetric_geometry():
    """Verify that symmetric tower placements with equal RSSI yield the exact center."""
    towers = [
        Tower(tower_id="T001", latitude=10.0, longitude=20.0),
        Tower(tower_id="T002", latitude=12.0, longitude=20.0),
        Tower(tower_id="T003", latitude=11.0, longitude=22.0),
    ]
    # Center of this triangle is (11.0, 20.66666667)
    expected_lat = 11.0
    expected_lon = (20.0 + 20.0 + 22.0) / 3.0

    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-70.0,
        ),
        Measurement(
            measurement_id="M002",
            tower_id="T002",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-70.0,
        ),
        Measurement(
            measurement_id="M003",
            tower_id="T003",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-70.0,
        ),
    ]

    result = solve_weighted_centroid(
        scenario_id="SCN-TEST-1",
        towers=towers,
        measurements=measurements,
        expected_device_lat=expected_lat,
        expected_device_lon=expected_lon,
    )

    assert result.scenario_id == "SCN-TEST-1"
    assert result.algorithm == "weighted_centroid"
    assert pytest.approx(result.estimated_latitude) == expected_lat
    assert pytest.approx(result.estimated_longitude) == expected_lon
    assert result.error_m is not None
    assert result.error_m < 1.0  # Error should be virtually zero
    assert result.signals_used == 3


def test_weighted_centroid_dominant_tower():
    """Verify that a tower with a much stronger RSSI pulls the estimate toward itself."""
    towers = [
        Tower(tower_id="T001", latitude=10.0, longitude=10.0),
        Tower(tower_id="T002", latitude=20.0, longitude=20.0),
    ]

    # Strong signal from T001, very weak signal from T002
    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-30.0,
        ),
        Measurement(
            measurement_id="M002",
            tower_id="T002",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-120.0,
        ),
    ]

    result = solve_weighted_centroid(
        scenario_id="SCN-TEST-2",
        towers=towers,
        measurements=measurements,
    )

    # Estimate should be extremely close to T001
    assert abs(result.estimated_latitude - 10.0) < 0.01
    assert abs(result.estimated_longitude - 10.0) < 0.01
    assert result.signals_used == 2


def test_weighted_centroid_measurement_averaging():
    """Verify that multiple measurements for the same tower are averaged correctly."""
    towers = [
        Tower(tower_id="T001", latitude=10.0, longitude=10.0),
        Tower(tower_id="T002", latitude=20.0, longitude=20.0),
    ]

    # T001 has two measurements that average to -70.0 dBm
    # T002 has one measurement of -70.0 dBm
    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
        ),
        Measurement(
            measurement_id="M002",
            tower_id="T001",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-80.0,
        ),
        Measurement(
            measurement_id="M003",
            tower_id="T002",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-70.0,
        ),
    ]

    result = solve_weighted_centroid(
        scenario_id="SCN-TEST-3",
        towers=towers,
        measurements=measurements,
    )

    # Since average RSSI for both towers is -70.0 dBm, the weights should be equal.
    # Therefore, the estimate should lie exactly in the middle.
    assert pytest.approx(result.estimated_latitude) == 15.0
    assert pytest.approx(result.estimated_longitude) == 15.0
    assert result.signals_used == 2


def test_weighted_centroid_empty_towers():
    """Verify that an error is raised if no towers are provided."""
    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-70.0,
        ),
    ]
    with pytest.raises(ValueError, match="No towers available"):
        solve_weighted_centroid(
            scenario_id="SCN-TEST-4",
            towers=[],
            measurements=measurements,
        )


def test_weighted_centroid_unweighted_fallback():
    """Verify that we fallback to unweighted centroid of towers if weights cannot be computed (e.g. no measurements match towers)."""
    towers = [
        Tower(tower_id="T001", latitude=10.0, longitude=10.0),
        Tower(tower_id="T002", latitude=20.0, longitude=20.0),
    ]
    # Measurement for non-existent tower
    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T999",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-70.0,
        ),
    ]

    result = solve_weighted_centroid(
        scenario_id="SCN-TEST-5",
        towers=towers,
        measurements=measurements,
    )

    # Should fallback to unweighted centroid: (15.0, 15.0)
    assert pytest.approx(result.estimated_latitude) == 15.0
    assert pytest.approx(result.estimated_longitude) == 15.0
    assert result.signals_used == 1
