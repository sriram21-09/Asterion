"""
Shared test fixtures for tests/api/ integration tests.
=====================================================

Provides:
  - In-memory SQLite engine with clean wipe/seed per test function
  - FastAPI TestClient with DB dependency override
  - seed_scenario_and_case fixture for pipeline tests
"""

import sys
from pathlib import Path

# Setup path for backend imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

import pytest
from app.database.session import get_db
from app.models.base import Base
from app.models.case import Case  # noqa: F401
from app.models.confidence_result import ConfidenceResult  # noqa: F401
from app.models.localization_result import LocalizationResult  # noqa: F401
from app.models.measurement import Measurement  # noqa: F401

# Import all ORM models so metadata.create_all picks them up
from app.models.scenario import Scenario  # noqa: F401
from app.models.tower import Tower  # noqa: F401
from app.models.tracking_result import TrackingResult  # noqa: F401
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# In-memory SQLite engine (shared across tests/api)
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db_session():
    """Create a clean in-memory database per test function.

    Creates all tables before the test and drops them after — a full
    wipe/seed cycle that guarantees isolation between tests.
    """
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
    """FastAPI TestClient using the in-memory test database."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_scenario_and_case(client):
    """Seed a Scenario (id=1) and a Case linked to it.

    This is the minimum data required for the full
    simulation → localization → tracking → confidence → evidence pipeline.

    Returns:
        tuple: (scenario_id, case_id)
    """
    # Create scenario
    scn_res = client.post(
        "/api/v1/scenarios/",
        json={
            "name": "Urban 3-Tower Test",
            "description": "Standard multilateration scenario in Bangalore core.",
        },
    )
    assert scn_res.status_code == 201, f"Scenario creation failed: {scn_res.json()}"
    scenario_id = scn_res.json()["data"]["id"]

    # Create case linked to scenario
    case_res = client.post(
        "/api/v1/cases/",
        json={
            "title": "E2E Pipeline Test Case",
            "description": "Integration test case for scientific pipeline.",
            "scenario_id": scenario_id,
        },
    )
    assert case_res.status_code == 201, f"Case creation failed: {case_res.json()}"
    case_id = case_res.json()["data"]["id"]

    return scenario_id, case_id
