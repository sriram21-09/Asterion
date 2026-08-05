import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scientific.pipeline.kalman_tracker import KalmanTracker
from scientific.pipeline.weighted_centroid import solve_weighted_centroid


def test_kalman_tracker_negative_dt():
    tracker = KalmanTracker()
    tracker.initialize(10.0, 20.0, 50.0)
    with pytest.raises(ValueError, match="Negative time delta"):
        tracker.predict(-1.0)


def test_kalman_tracker_zero_dt():
    tracker = KalmanTracker()
    tracker.initialize(10.0, 20.0, 50.0)
    tracker.predict(0.0)  # Should not raise


def test_weighted_centroid_none_coordinates():
    # Test that solve_weighted_centroid handles towers with None coordinates
    class DummyTower:
        def __init__(self, cgi, lat, lon):
            self.cgi = cgi
            self.tower_id = cgi
            self.latitude = lat
            self.longitude = lon

    class DummyMeasurement:
        def __init__(self, tower_id, rssi):
            self.tower_id = tower_id
            self.rssi_dbm = rssi

    towers = [
        DummyTower("1", None, None),
        DummyTower("2", 10.0, 20.0),
    ]
    measurements = [
        DummyMeasurement("1", -75),
        DummyMeasurement("2", -80),
    ]

    # Should not crash, and should compute centroid based on valid tower only
    res = solve_weighted_centroid("scen-1", towers, measurements)
    assert res.estimated_latitude == 10.0
    assert res.estimated_longitude == 20.0
