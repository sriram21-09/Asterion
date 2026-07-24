import sys
from pathlib import Path

# Setup path for backend imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import pytest
from app.database.session import get_db
from app.models.base import Base
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    Base.metadata.create_all(bind=connection)
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=connection)
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestScenarioAPI:
    """API tests for Scenario endpoints."""

    def test_create_scenario_success(self, client):
        response = client.post(
            "/api/v1/scenarios/",
            json={
                "name": "Urban Grid S1",
                "description": "Dense urban multi-path environment",
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "Urban Grid S1"
        assert data["description"] == "Dense urban multi-path environment"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_scenario_duplicate_name_fails(self, client):
        # Create first
        client.post("/api/v1/scenarios/", json={"name": "Duplicate Scenario"})
        # Try duplicate
        response = client.post(
            "/api/v1/scenarios/", json={"name": "Duplicate Scenario"}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["error"]["message"]

    def test_create_scenario_empty_name_fails(self, client):
        response = client.post("/api/v1/scenarios/", json={"name": "   "})
        assert response.status_code == 422  # validation handler
        data = response.json()
        assert data["success"] is False
        assert "name" in data["error"]["message"]

    def test_list_scenarios_empty(self, client):
        response = client.get("/api/v1/scenarios/")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_list_scenarios_pagination(self, client):
        # Create 3 scenarios
        for i in range(3):
            client.post("/api/v1/scenarios/", json={"name": f"Scenario {i}"})

        # List first page with size 2
        response = client.get("/api/v1/scenarios/?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        assert data[0]["name"] == "Scenario 0"
        assert data[1]["name"] == "Scenario 1"

        # List second page
        response = client.get("/api/v1/scenarios/?page=2&page_size=2")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Scenario 2"

    def test_get_scenario_by_id(self, client):
        res = client.post("/api/v1/scenarios/", json={"name": "Scenario X"})
        scenario_id = res.json()["data"]["id"]

        response = client.get(f"/api/v1/scenarios/{scenario_id}")
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Scenario X"

    def test_get_scenario_not_found(self, client):
        response = client.get("/api/v1/scenarios/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_scenario_success(self, client):
        res = client.post("/api/v1/scenarios/", json={"name": "Scenario to delete"})
        scenario_id = res.json()["data"]["id"]

        response = client.delete(f"/api/v1/scenarios/{scenario_id}")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == scenario_id

        # Verify deletion
        get_res = client.get(f"/api/v1/scenarios/{scenario_id}")
        assert get_res.status_code == 404

    def test_delete_scenario_not_found(self, client):
        response = client.delete("/api/v1/scenarios/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
