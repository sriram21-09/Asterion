from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_localize_insufficient_signals():
    response = client.post("/api/localize", json={
        "signals": [
            {"tower_id": "T1", "latitude": 12.9716, "longitude": 77.5946, "signal_strength_dbm": -70.0, "timestamp": 1625097600.0}
        ]
    })
    assert response.status_code == 400
    assert "At least 3 tower signals are required" in response.json()["detail"]

def test_localize_valid_signals():
    response = client.post("/api/localize", json={
        "signals": [
            {"tower_id": "T1", "latitude": 12.9716, "longitude": 77.5946, "signal_strength_dbm": -70.0, "timestamp": 1625097600.0},
            {"tower_id": "T2", "latitude": 12.9718, "longitude": 77.5948, "signal_strength_dbm": -65.0, "timestamp": 1625097601.0},
            {"tower_id": "T3", "latitude": 12.9720, "longitude": 77.5950, "signal_strength_dbm": -80.0, "timestamp": 1625097602.0}
        ]
    })
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "estimated_latitude" in res_data["data"]
    assert "estimated_longitude" in res_data["data"]
    assert res_data["data"]["signals_used"] == 3

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "asterion-api",
        "version": "1.0.0"
    }
