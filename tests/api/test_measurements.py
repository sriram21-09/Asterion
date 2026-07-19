import sys
from pathlib import Path

# Setup path for backend imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta

from main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestMeasurementsValidationAPI:
    """Integration tests for measurement validation API endpoint."""

    def test_validate_measurements_success(self, client):
        # Valid measurements batch
        payload = {
            "measurements": [
                {
                    "measurement_id": "M001",
                    "tower_id": "T001",
                    "timestamp": "2026-07-07T10:30:00Z",
                    "rssi_dbm": -72.0,
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "timing_advance": 2.0,
                    "uncertainty_m": 15.0,
                },
                {
                    "measurement_id": "M002",
                    "tower_id": "T002",
                    "timestamp": "2026-07-07T10:31:00Z",
                    "rssi_dbm": -85.0,
                    # Optional coordinates left as None
                    "timing_advance": None,
                    "uncertainty_m": None,
                }
            ]
        }

        response = client.post("/api/v1/measurements/validate", json=payload)
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["success"] is True
        
        data = res_data["data"]
        assert data["is_valid"] is True
        assert data["valid_count"] == 2
        assert data["rejected_count"] == 0
        assert data["warning_count"] == 0
        assert len(data["errors"]) == 0

    def test_validate_measurements_invalid_rssi_fails(self, client):
        # RSSI is out of basic -150 to 0 bounds
        payload = {
            "measurements": [
                {
                    "measurement_id": "M001",
                    "tower_id": "T001",
                    "timestamp": "2026-07-07T10:30:00Z",
                    "rssi_dbm": -200.0,  # Invalid
                }
            ]
        }

        response = client.post("/api/v1/measurements/validate", json=payload)
        assert response.status_code == 422
        res_data = response.json()
        assert res_data["success"] is False
        assert res_data["error"]["code"] == "VALIDATION_ERROR"
        
        data = res_data["data"]
        assert data["is_valid"] is False
        assert data["valid_count"] == 0
        assert data["rejected_count"] == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["field"] == "rssi_dbm"
        assert "must be between" in data["errors"][0]["message"]

    def test_validate_measurements_partial_coordinates_fails(self, client):
        # Latitude without longitude
        payload = {
            "measurements": [
                {
                    "measurement_id": "M001",
                    "tower_id": "T001",
                    "timestamp": "2026-07-07T10:30:00Z",
                    "rssi_dbm": -72.0,
                    "latitude": 12.9716,
                    "longitude": None,  # Missing longitude
                }
            ]
        }

        response = client.post("/api/v1/measurements/validate", json=payload)
        assert response.status_code == 422
        res_data = response.json()
        assert res_data["success"] is False
        
        data = res_data["data"]
        assert data["is_valid"] is False
        assert data["rejected_count"] == 1
        assert len(data["errors"]) == 1
        assert "latitude/longitude" in data["errors"][0]["field"]
        assert "both be provided" in data["errors"][0]["message"]

    def test_validate_measurements_future_timestamp_fails(self, client):
        # Timestamp is in the future (flagged as ERROR by scientific validator)
        future_ts = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat().replace("+00:00", "Z")
        payload = {
            "measurements": [
                {
                    "measurement_id": "M001",
                    "tower_id": "T001",
                    "timestamp": future_ts,
                    "rssi_dbm": -72.0,
                }
            ]
        }

        response = client.post("/api/v1/measurements/validate", json=payload)
        assert response.status_code == 422
        res_data = response.json()
        assert res_data["success"] is False
        
        data = res_data["data"]
        assert data["is_valid"] is False
        assert data["rejected_count"] == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["field"] == "timestamp"
        assert "future" in data["errors"][0]["message"]

    def test_validate_measurements_empty_ids_fails(self, client):
        payload = {
            "measurements": [
                {
                    "measurement_id": "  ",
                    "tower_id": "T001",
                    "timestamp": "2026-07-07T10:30:00Z",
                    "rssi_dbm": -72.0,
                }
            ]
        }

        response = client.post("/api/v1/measurements/validate", json=payload)
        assert response.status_code == 422
        res_data = response.json()
        assert res_data["success"] is False
        
        data = res_data["data"]
        assert data["is_valid"] is False
        assert data["rejected_count"] == 1
        assert data["errors"][0]["field"] == "measurement_id"

    def test_validate_measurements_warnings_succeeds_with_200(self, client):
        # -125 dBm RSSI is in [-150, 0] so it is not an error, but it is outside [-120, -30] so it triggers a warning
        payload = {
            "measurements": [
                {
                    "measurement_id": "M001",
                    "tower_id": "T001",
                    "timestamp": "2026-07-07T10:30:00Z",
                    "rssi_dbm": -125.0,
                }
            ]
        }

        response = client.post("/api/v1/measurements/validate", json=payload)
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["success"] is True
        
        data = res_data["data"]
        assert data["is_valid"] is True
        assert data["valid_count"] == 1
        assert data["rejected_count"] == 0
        assert data["warning_count"] == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["severity"] == "warning"
        assert data["errors"][0]["field"] == "rssi_dbm"
