import sys
from pathlib import Path

# Setup path for backend imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.database.session import get_db
from app.models.base import Base

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


class TestCaseAPI:
    """API tests for Case endpoints, exception handling, and middleware."""

    def test_cases_router_health(self, client):
        response = client.get("/api/v1/cases/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cases-api"

    def test_create_case_success(self, client):
        response = client.post(
            "/api/v1/cases/",
            json={
                "title": "Abducted Device Track",
                "description": "Tracking stolen phone location",
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["title"] == "Abducted Device Track"
        assert data["description"] == "Tracking stolen phone location"
        assert data["status"] == "open"
        assert data["scenario_id"] is None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_case_missing_title_fails(self, client):
        response = client.post(
            "/api/v1/cases/", json={"description": "No title provided"}
        )
        # Pydantic validation error or empty string check
        assert response.status_code in (400, 422)
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_create_case_empty_title_fails(self, client):
        response = client.post(
            "/api/v1/cases/", json={"title": "   ", "description": "Whitespace only"}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "title" in data["error"]["message"]

    def test_create_case_with_nonexistent_scenario_id_fails(self, client):
        response = client.post(
            "/api/v1/cases/", json={"title": "Orphan Case", "scenario_id": 9999}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "scenario_id" in data["error"]["message"]

    def test_create_case_with_valid_scenario_id_success(self, client):
        # Create scenario first
        scenario_res = client.post(
            "/api/v1/scenarios/", json={"name": "Reference Scenario"}
        )
        scenario_id = scenario_res.json()["data"]["id"]

        # Create case referencing that scenario
        response = client.post(
            "/api/v1/cases/", json={"title": "Linked Case", "scenario_id": scenario_id}
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["scenario_id"] == scenario_id

    def test_list_cases_empty(self, client):
        response = client.get("/api/v1/cases/")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_list_cases_pagination(self, client):
        # Create 3 cases
        for i in range(3):
            client.post("/api/v1/cases/", json={"title": f"Case {i}"})

        # List first page with size 2
        response = client.get("/api/v1/cases/?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        assert data[0]["title"] == "Case 0"
        assert data[1]["title"] == "Case 1"

        # List second page
        response = client.get("/api/v1/cases/?page=2&page_size=2")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["title"] == "Case 2"

    def test_get_case_by_id(self, client):
        res = client.post("/api/v1/cases/", json={"title": "Target Case"})
        case_id = res.json()["data"]["id"]

        response = client.get(f"/api/v1/cases/{case_id}")
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "Target Case"

    def test_get_case_not_found(self, client):
        response = client.get("/api/v1/cases/9999")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]["message"].lower()
        # Verify compatibility with tests checking "detail"
        assert "not found" in data["detail"].lower()

    def test_delete_case_success(self, client):
        res = client.post("/api/v1/cases/", json={"title": "Delete Target"})
        case_id = res.json()["data"]["id"]

        response = client.delete(f"/api/v1/cases/{case_id}")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == case_id

        # Verify deletion
        get_res = client.get(f"/api/v1/cases/{case_id}")
        assert get_res.status_code == 404

    def test_delete_case_not_found(self, client):
        response = client.delete("/api/v1/cases/9999")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]["message"].lower()

    def test_logging_middleware_adds_process_time_header(self, client):
        response = client.get("/api/v1/cases/health")
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        duration_str = response.headers["X-Process-Time"]
        assert duration_str.endswith("s")
        # Ensure it is a valid float duration
        assert float(duration_str[:-1]) >= 0.0
