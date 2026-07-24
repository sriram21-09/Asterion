"""
Integration Tests for Tracking Run API
========================================

Tests cover:
  - TrackingResult ORM model creation and persistence
  - TrackingRepository CRUD operations
  - TrackingService end-to-end with scientific pipeline
  - API endpoint response shape and error cases
"""

from datetime import UTC, datetime

import pytest
from app.database.session import get_db
from app.models.base import Base
from app.models.case import Case
from app.models.localization_result import LocalizationResult
from app.models.scenario import Scenario
from app.models.tracking_result import TrackingResult
from app.repositories.tracking_repository import TrackingRepository
from app.services.tracking_service import TrackingService
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

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
        description="Test scenario for tracking",
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@pytest.fixture
def sample_case(db: Session, sample_scenario):
    """Create a sample case linked to a scenario."""
    case = Case(
        title="Test Tracking Case",
        description="Case for tracking testing",
        scenario_id=sample_scenario.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@pytest.fixture
def sample_localization_results(db: Session, sample_case):
    """Create sample localization results for the case (needed as tracker input)."""
    results = []
    base_lat, base_lon = 12.9722, 77.5949
    for i in range(5):
        result = LocalizationResult(
            case_id=sample_case.id,
            scenario_id=sample_case.scenario_id,
            algorithm="multilateration",
            estimated_latitude=base_lat + i * 0.001,
            estimated_longitude=base_lon + i * 0.0005,
            error_m=45.0 + i * 5,
            computation_time_ms=10.0 + i,
            signals_used=3,
        )
        results.append(result)

    db.add_all(results)
    db.commit()
    for r in results:
        db.refresh(r)
    return results


# ---------------------------------------------------------------------------
# Test: TrackingResult ORM model
# ---------------------------------------------------------------------------


class TestTrackingResultModel:
    """Test the TrackingResult ORM model."""

    def test_create_tracking_result(self, db: Session, sample_case):
        """TrackingResult can be created and persisted."""
        result = TrackingResult(
            case_id=sample_case.id,
            step_number=1,
            smoothed_latitude=12.9722,
            smoothed_longitude=77.5949,
            velocity_lat=0.0,
            velocity_lon=0.0,
            velocity_mps=0.0,
            heading_deg=None,
            error_m=45.3,
            computation_time_ms=1.2,
            algorithm="kalman",
            timestamp=datetime(2026, 7, 16, 10, 30, tzinfo=UTC),
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.id is not None
        assert result.case_id == sample_case.id
        assert result.step_number == 1
        assert result.smoothed_latitude == 12.9722
        assert result.smoothed_longitude == 77.5949
        assert result.algorithm == "kalman"
        assert result.created_at is not None

    def test_case_relationship(self, db: Session, sample_case):
        """TrackingResult correctly links back to Case."""
        result = TrackingResult(
            case_id=sample_case.id,
            step_number=1,
            smoothed_latitude=12.9722,
            smoothed_longitude=77.5949,
            algorithm="kalman",
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.case is not None
        assert result.case.id == sample_case.id
        assert result.case.title == "Test Tracking Case"

    def test_nullable_fields(self, db: Session, sample_case):
        """Optional fields can be None."""
        result = TrackingResult(
            case_id=sample_case.id,
            step_number=1,
            smoothed_latitude=12.9722,
            smoothed_longitude=77.5949,
            algorithm="kalman",
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.velocity_mps is None
        assert result.heading_deg is None
        assert result.error_m is None
        assert result.computation_time_ms is None
        assert result.localization_result_id is None

    def test_localization_result_fk(
        self, db: Session, sample_case, sample_localization_results
    ):
        """TrackingResult can reference a localization result."""
        loc = sample_localization_results[0]
        result = TrackingResult(
            case_id=sample_case.id,
            localization_result_id=loc.id,
            step_number=1,
            smoothed_latitude=12.9722,
            smoothed_longitude=77.5949,
            algorithm="kalman",
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.localization_result_id == loc.id
        assert result.localization_result is not None


# ---------------------------------------------------------------------------
# Test: TrackingRepository
# ---------------------------------------------------------------------------


class TestTrackingRepository:
    """Test the repository layer."""

    def test_create(self, db: Session, sample_case):
        """Repository.create persists and returns a result."""
        result = TrackingResult(
            case_id=sample_case.id,
            step_number=1,
            smoothed_latitude=12.9722,
            smoothed_longitude=77.5949,
            algorithm="kalman",
        )
        saved = TrackingRepository.create(db, result)
        assert saved.id is not None
        assert saved.smoothed_latitude == 12.9722

    def test_bulk_create(self, db: Session, sample_case):
        """Repository.bulk_create persists multiple results."""
        results = [
            TrackingResult(
                case_id=sample_case.id,
                step_number=i + 1,
                smoothed_latitude=12.9722 + i * 0.001,
                smoothed_longitude=77.5949 + i * 0.0005,
                algorithm="kalman",
            )
            for i in range(5)
        ]
        saved = TrackingRepository.bulk_create(db, results)
        assert len(saved) == 5
        assert all(r.id is not None for r in saved)

    def test_get_by_case(self, db: Session, sample_case):
        """Repository.get_by_case returns results ordered by step_number."""
        for i in range(3):
            result = TrackingResult(
                case_id=sample_case.id,
                step_number=i + 1,
                smoothed_latitude=12.9722 + i * 0.001,
                smoothed_longitude=77.5949,
                algorithm="kalman",
            )
            TrackingRepository.create(db, result)

        results = TrackingRepository.get_by_case(db, sample_case.id)
        assert len(results) == 3
        # Check ordering
        assert results[0].step_number == 1
        assert results[1].step_number == 2
        assert results[2].step_number == 3

    def test_get_by_case_empty(self, db: Session, sample_case):
        """Repository returns empty list for case with no results."""
        results = TrackingRepository.get_by_case(db, sample_case.id)
        assert results == []

    def test_delete_by_case(self, db: Session, sample_case):
        """Repository.delete_by_case removes all tracking results for a case."""
        for i in range(3):
            TrackingRepository.create(
                db,
                TrackingResult(
                    case_id=sample_case.id,
                    step_number=i + 1,
                    smoothed_latitude=12.9722,
                    smoothed_longitude=77.5949,
                    algorithm="kalman",
                ),
            )

        count = TrackingRepository.delete_by_case(db, sample_case.id)
        assert count == 3

        results = TrackingRepository.get_by_case(db, sample_case.id)
        assert results == []

    def test_get_latest_by_case(self, db: Session, sample_case):
        """Repository.get_latest_by_case returns the most recent result."""
        for i in range(3):
            TrackingRepository.create(
                db,
                TrackingResult(
                    case_id=sample_case.id,
                    step_number=i + 1,
                    smoothed_latitude=12.9722 + i * 0.001,
                    smoothed_longitude=77.5949,
                    algorithm="kalman",
                ),
            )

        latest = TrackingRepository.get_latest_by_case(db, sample_case.id)
        assert latest is not None

    def test_get_latest_by_case_empty(self, db: Session, sample_case):
        """Repository returns None for case with no results."""
        latest = TrackingRepository.get_latest_by_case(db, sample_case.id)
        assert latest is None


# ---------------------------------------------------------------------------
# Test: TrackingService
# ---------------------------------------------------------------------------


class TestTrackingService:
    """Test the service layer."""

    def test_run_tracking_requires_case(self, db: Session):
        """Service raises 404 for non-existent case."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            TrackingService.run_tracking(db, "CASE-999")
        assert exc_info.value.status_code == 404

    def test_run_tracking_requires_scenario(self, db: Session):
        """Service raises error for case without scenario."""
        from app.shared.validation import ValidationError

        case = Case(title="No Scenario Case", description="Test")
        db.add(case)
        db.commit()
        db.refresh(case)

        case_code = f"CASE-{case.id:03d}"
        with pytest.raises(ValidationError):
            TrackingService.run_tracking(db, case_code)

    def test_run_tracking_requires_localization_results(self, db: Session, sample_case):
        """Service raises error when fewer than 2 localization results exist."""
        from app.shared.validation import ValidationError

        case_code = f"CASE-{sample_case.id:03d}"
        with pytest.raises(ValidationError):
            TrackingService.run_tracking(db, case_code)

    def test_run_tracking_success(
        self, db: Session, sample_case, sample_localization_results
    ):
        """Service runs tracking end-to-end and returns expected structure."""
        case_code = f"CASE-{sample_case.id:03d}"
        result = TrackingService.run_tracking(db, case_code)

        assert result["case_code"] == case_code.upper()
        assert result["total_steps"] == 5
        assert len(result["path"]) == 5
        assert result["distance_km"] >= 0
        assert result["avg_velocity_kmh"] >= 0
        assert result["computation_time_ms"] > 0

        # Check path step structure
        step = result["path"][0]
        assert "step_number" in step
        assert "latitude" in step
        assert "longitude" in step
        assert "velocity_kmh" in step
        assert step["step_number"] == 1

    def test_run_tracking_persists_results(
        self, db: Session, sample_case, sample_localization_results
    ):
        """Service persists tracking results to the database."""
        case_code = f"CASE-{sample_case.id:03d}"
        TrackingService.run_tracking(db, case_code)

        stored = TrackingRepository.get_by_case(db, sample_case.id)
        assert len(stored) == 5
        assert stored[0].step_number == 1
        assert stored[4].step_number == 5
        assert stored[0].algorithm == "kalman"

    def test_run_tracking_replaces_old_results(
        self, db: Session, sample_case, sample_localization_results
    ):
        """Running tracking again replaces old tracking results."""
        case_code = f"CASE-{sample_case.id:03d}"
        TrackingService.run_tracking(db, case_code)
        TrackingService.run_tracking(db, case_code)

        stored = TrackingRepository.get_by_case(db, sample_case.id)
        # Should still be 5, not 10
        assert len(stored) == 5

    def test_compute_heading(self):
        """Heading computation returns correct bearings."""
        # North: v_lat > 0, v_lon = 0 → 0°
        h = TrackingService._compute_heading(1.0, 0.0)
        assert h is not None
        assert abs(h - 0.0) < 0.01

        # East: v_lat = 0, v_lon > 0 → 90°
        h = TrackingService._compute_heading(0.0, 1.0)
        assert h is not None
        assert abs(h - 90.0) < 0.01

        # South: v_lat < 0, v_lon = 0 → 180°
        h = TrackingService._compute_heading(-1.0, 0.0)
        assert h is not None
        assert abs(h - 180.0) < 0.01

        # West: v_lat = 0, v_lon < 0 → 270°
        h = TrackingService._compute_heading(0.0, -1.0)
        assert h is not None
        assert abs(h - 270.0) < 0.01

        # Zero velocity → None
        h = TrackingService._compute_heading(0.0, 0.0)
        assert h is None


# ---------------------------------------------------------------------------
# Test: API endpoint conformance
# ---------------------------------------------------------------------------


class TestTrackingAPIConformance:
    """Test the API endpoint returns correct response shape."""

    def test_run_endpoint_requires_case_code(self):
        """POST /tracking/run requires case_code query param."""
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.post("/api/v1/tracking/run")
        assert response.status_code == 422  # Missing required query param

        app.dependency_overrides.clear()

    def test_run_endpoint_invalid_case_code(self):
        """POST /tracking/run with invalid case code returns error."""
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.post("/api/v1/tracking/run?case_code=INVALID")
        assert response.status_code in (400, 404, 422)

        app.dependency_overrides.clear()

    def test_run_endpoint_case_not_found(self):
        """POST /tracking/run with non-existent case returns 404."""
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.post("/api/v1/tracking/run?case_code=CASE-999")
        assert response.status_code == 404

        app.dependency_overrides.clear()

    def test_response_schema_fields(self):
        """Verify the response schema has all expected fields."""
        from app.schemas.tracking import TrackingRunResponse, TrackingStepResponse

        run_fields = TrackingRunResponse.model_fields
        expected_run_fields = [
            "case_code",
            "total_steps",
            "path",
            "distance_km",
            "avg_velocity_kmh",
            "computation_time_ms",
        ]
        for field in expected_run_fields:
            assert field in run_fields, f"Missing field in TrackingRunResponse: {field}"

        step_fields = TrackingStepResponse.model_fields
        expected_step_fields = [
            "step_number",
            "latitude",
            "longitude",
            "velocity_kmh",
            "timestamp",
            "heading_deg",
        ]
        for field in expected_step_fields:
            assert field in step_fields, (
                f"Missing field in TrackingStepResponse: {field}"
            )
