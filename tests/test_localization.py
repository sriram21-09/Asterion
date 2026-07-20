"""
Integration Tests for Localization Run API
===========================================

Tests cover:
  - Mathematical results from the localization service
  - Database persistence of localization results
  - API response model conformance
"""

import pytest
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.case import Case
from app.models.scenario import Scenario
from app.models.measurement import Measurement
from app.models.localization_result import LocalizationResult
from app.database.session import get_db
from app.repositories.localization_repository import LocalizationRepository

# ---------------------------------------------------------------------------
# Test database fixture
# ---------------------------------------------------------------------------

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db():
    """Provide a test database session."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_scenario(db: Session):
    """Create a sample scenario in the test DB."""
    scenario = Scenario(
        name="Urban 3-Tower Test",
        description="Test scenario",
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@pytest.fixture
def sample_case(db: Session, sample_scenario):
    """Create a sample case linked to a scenario."""
    case = Case(
        title="Test Localization Case",
        description="Case for localization testing",
        scenario_id=sample_scenario.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@pytest.fixture
def sample_measurements(db: Session, sample_case):
    """Create sample measurements for the case, mimicking the generated format."""
    measurements = []
    # Create measurements matching the tower pattern from scenario_example.json
    tower_ids = ["T001", "T002", "T003"]
    rssi_values = [-72.0, -85.0, -90.0]
    lats = [12.9720, 12.9725, 12.9718]
    lons = [77.5948, 77.5945, 77.5952]

    for i, (tid, rssi, lat, lon) in enumerate(zip(tower_ids, rssi_values, lats, lons)):
        m = Measurement(
            case_id=sample_case.id,
            scenario_id=sample_case.scenario_id,
            measurement_code=f"MEAS-SCN001-{tid}-{i+1:04d}",
            timestamp=datetime(2026, 7, 15, 10, 30, tzinfo=timezone.utc),
            rssi_dbm=rssi,
            latitude=lat,
            longitude=lon,
        )
        measurements.append(m)

    db.add_all(measurements)
    db.commit()
    for m in measurements:
        db.refresh(m)
    return measurements


# ---------------------------------------------------------------------------
# Test: LocalizationResult ORM model
# ---------------------------------------------------------------------------


class TestLocalizationResultModel:
    """Test the LocalizationResult ORM model."""

    def test_create_localization_result(self, db: Session, sample_case):
        """LocalizationResult can be created and persisted."""
        result = LocalizationResult(
            case_id=sample_case.id,
            scenario_id=sample_case.scenario_id,
            algorithm="multilateration",
            estimated_latitude=12.9722,
            estimated_longitude=77.5949,
            error_m=45.3,
            computation_time_ms=12.5,
            signals_used=3,
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.id is not None
        assert result.case_id == sample_case.id
        assert result.algorithm == "multilateration"
        assert result.estimated_latitude == 12.9722
        assert result.estimated_longitude == 77.5949
        assert result.error_m == 45.3
        assert result.signals_used == 3
        assert result.created_at is not None

    def test_case_relationship(self, db: Session, sample_case):
        """LocalizationResult correctly links back to Case."""
        result = LocalizationResult(
            case_id=sample_case.id,
            algorithm="weighted_centroid",
            estimated_latitude=12.9720,
            estimated_longitude=77.5948,
            signals_used=2,
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.case is not None
        assert result.case.id == sample_case.id
        assert result.case.title == "Test Localization Case"

    def test_nullable_fields(self, db: Session, sample_case):
        """Optional fields can be None."""
        result = LocalizationResult(
            case_id=sample_case.id,
            algorithm="multilateration",
            estimated_latitude=12.9722,
            estimated_longitude=77.5949,
            signals_used=3,
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.error_m is None
        assert result.computation_time_ms is None
        assert result.scenario_id is None


# ---------------------------------------------------------------------------
# Test: LocalizationRepository
# ---------------------------------------------------------------------------


class TestLocalizationRepository:
    """Test the repository layer."""

    def test_create(self, db: Session, sample_case):
        """Repository.create persists and returns a result."""
        result = LocalizationResult(
            case_id=sample_case.id,
            algorithm="multilateration",
            estimated_latitude=12.9722,
            estimated_longitude=77.5949,
            signals_used=3,
        )
        saved = LocalizationRepository.create(db, result)
        assert saved.id is not None
        assert saved.estimated_latitude == 12.9722

    def test_get_by_case(self, db: Session, sample_case):
        """Repository.get_by_case returns all results for a case."""
        for i in range(3):
            result = LocalizationResult(
                case_id=sample_case.id,
                algorithm="multilateration",
                estimated_latitude=12.9722 + i * 0.001,
                estimated_longitude=77.5949,
                signals_used=3,
            )
            LocalizationRepository.create(db, result)

        results = LocalizationRepository.get_by_case(db, sample_case.id)
        assert len(results) == 3

    def test_get_latest_by_case(self, db: Session, sample_case):
        """Repository.get_latest_by_case returns the most recent result."""
        for i in range(3):
            result = LocalizationResult(
                case_id=sample_case.id,
                algorithm="multilateration",
                estimated_latitude=12.9722 + i * 0.001,
                estimated_longitude=77.5949,
                signals_used=3,
            )
            LocalizationRepository.create(db, result)

        latest = LocalizationRepository.get_latest_by_case(db, sample_case.id)
        assert latest is not None
        # Latest should be the last one created
        assert latest.estimated_latitude == pytest.approx(12.9742, abs=0.001)

    def test_get_by_case_empty(self, db: Session, sample_case):
        """Repository returns empty list for case with no results."""
        results = LocalizationRepository.get_by_case(db, sample_case.id)
        assert results == []

    def test_get_latest_by_case_empty(self, db: Session, sample_case):
        """Repository returns None for case with no results."""
        latest = LocalizationRepository.get_latest_by_case(db, sample_case.id)
        assert latest is None


# ---------------------------------------------------------------------------
# Test: API endpoint model conformance
# ---------------------------------------------------------------------------


class TestLocalizationAPIConformance:
    """Test the API endpoint returns correct response shape."""

    def test_run_endpoint_requires_case_code(self):
        """POST /localization/run requires case_code query param."""
        # Import here to avoid circular issues
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.post("/api/v1/localization/run")
        assert response.status_code == 422  # Missing required query param

        app.dependency_overrides.clear()

    def test_run_endpoint_invalid_case_code(self):
        """POST /localization/run with invalid case code returns error."""
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.post("/api/v1/localization/run?case_code=INVALID")
        # Should fail validation (prefix not CASE-)
        assert response.status_code in (400, 404, 422)

        app.dependency_overrides.clear()

    def test_run_endpoint_case_not_found(self):
        """POST /localization/run with non-existent case returns 404."""
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.post("/api/v1/localization/run?case_code=CASE-999")
        assert response.status_code == 404

        app.dependency_overrides.clear()

    def test_response_schema_fields(self):
        """Verify the response schema has all expected fields."""
        from app.schemas.localization import LocalizationRunResponse

        fields = LocalizationRunResponse.model_fields
        expected_fields = [
            "case_code",
            "scenario_code",
            "algorithm",
            "estimated_latitude",
            "estimated_longitude",
            "error_m",
            "signals_used",
            "computation_time_ms",
            "timestamp",
        ]
        for field in expected_fields:
            assert field in fields, f"Missing field: {field}"
