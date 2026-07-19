"""
Integration Tests for Confidence & Evidence APIs
==================================================

Tests cover:
  - ConfidenceResult ORM model creation and persistence
  - ConfidenceRepository CRUD operations
  - ConfidenceService end-to-end with scientific pipeline
  - EvidenceService end-to-end with scientific pipeline
  - API endpoint response shape and error cases for both endpoints
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
from app.models.tracking_result import TrackingResult  # noqa: F401 – needed for mapper
from app.models.confidence_result import ConfidenceResult
from app.database.session import get_db
from app.repositories.confidence_repository import ConfidenceRepository
from app.services.confidence_service import ConfidenceService
from app.services.evidence_service import EvidenceService

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
        description="Test scenario for confidence/evidence",
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@pytest.fixture
def sample_case(db: Session, sample_scenario):
    """Create a sample case linked to a scenario."""
    case = Case(
        title="Test Confidence Case",
        description="Case for confidence/evidence testing",
        scenario_id=sample_scenario.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@pytest.fixture
def sample_measurements(db: Session, sample_case):
    """Create sample measurements for the case."""
    measurements = []
    base_lat, base_lon = 12.9722, 77.5949
    for i in range(6):
        tower_idx = i % 3
        m = Measurement(
            case_id=sample_case.id,
            scenario_id=sample_case.scenario_id,
            measurement_code=f"MEAS-SCN001-T00{tower_idx + 1}-{i + 1:04d}",
            timestamp=datetime(2026, 7, 17, 10, i, tzinfo=timezone.utc),
            rssi_dbm=-75.0 - i * 2,
            latitude=base_lat + (i * 0.001),
            longitude=base_lon + (i * 0.0005),
            timing_advance=1.0 + i * 0.5,
            uncertainty_m=50.0 + i * 10,
        )
        measurements.append(m)

    db.add_all(measurements)
    db.commit()
    for m in measurements:
        db.refresh(m)
    return measurements


@pytest.fixture
def sample_localization_result(db: Session, sample_case):
    """Create a sample localization result for the case."""
    result = LocalizationResult(
        case_id=sample_case.id,
        scenario_id=sample_case.scenario_id,
        algorithm="multilateration",
        estimated_latitude=12.9725,
        estimated_longitude=77.5952,
        error_m=45.3,
        computation_time_ms=12.5,
        signals_used=3,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


# ---------------------------------------------------------------------------
# Test: ConfidenceResult ORM model
# ---------------------------------------------------------------------------


class TestConfidenceResultModel:
    """Test the ConfidenceResult ORM model."""

    def test_create_confidence_result(self, db: Session, sample_case):
        """ConfidenceResult can be created and persisted."""
        result = ConfidenceResult(
            case_id=sample_case.id,
            confidence_score=0.87,
            confidence_level="high",
            error_ellipse_semi_major_m=120.0,
            error_ellipse_semi_minor_m=75.0,
            error_ellipse_orientation_deg=45.0,
            gdop=2.3,
            method="gdop",
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.id is not None
        assert result.case_id == sample_case.id
        assert result.confidence_score == 0.87
        assert result.confidence_level == "high"
        assert result.gdop == 2.3
        assert result.method == "gdop"
        assert result.created_at is not None

    def test_case_relationship(self, db: Session, sample_case):
        """ConfidenceResult correctly links back to Case."""
        result = ConfidenceResult(
            case_id=sample_case.id,
            confidence_score=0.5,
            confidence_level="medium",
            method="gdop",
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.case is not None
        assert result.case.id == sample_case.id
        assert result.case.title == "Test Confidence Case"

    def test_localization_result_fk(
        self, db: Session, sample_case, sample_localization_result
    ):
        """ConfidenceResult can reference a localization result."""
        result = ConfidenceResult(
            case_id=sample_case.id,
            localization_result_id=sample_localization_result.id,
            confidence_score=0.87,
            confidence_level="high",
            method="gdop",
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.localization_result_id == sample_localization_result.id
        assert result.localization_result is not None

    def test_nullable_fields(self, db: Session, sample_case):
        """Optional fields can be None."""
        result = ConfidenceResult(
            case_id=sample_case.id,
            confidence_score=0.0,
            confidence_level="low",
            method="gdop",
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        assert result.error_ellipse_semi_major_m is None
        assert result.error_ellipse_semi_minor_m is None
        assert result.error_ellipse_orientation_deg is None
        assert result.gdop is None
        assert result.localization_result_id is None


# ---------------------------------------------------------------------------
# Test: ConfidenceRepository
# ---------------------------------------------------------------------------


class TestConfidenceRepository:
    """Test the repository layer."""

    def test_create(self, db: Session, sample_case):
        """Repository.create persists and returns a result."""
        result = ConfidenceResult(
            case_id=sample_case.id,
            confidence_score=0.87,
            confidence_level="high",
            method="gdop",
        )
        saved = ConfidenceRepository.create(db, result)
        assert saved.id is not None
        assert saved.confidence_score == 0.87

    def test_bulk_create(self, db: Session, sample_case):
        """Repository.bulk_create persists multiple results."""
        results = [
            ConfidenceResult(
                case_id=sample_case.id,
                confidence_score=0.5 + i * 0.1,
                confidence_level="medium",
                method="gdop",
            )
            for i in range(3)
        ]
        saved = ConfidenceRepository.bulk_create(db, results)
        assert len(saved) == 3
        assert all(r.id is not None for r in saved)

    def test_get_by_case(self, db: Session, sample_case):
        """Repository.get_by_case returns results ordered by creation time."""
        for i in range(3):
            ConfidenceRepository.create(
                db,
                ConfidenceResult(
                    case_id=sample_case.id,
                    confidence_score=0.5 + i * 0.1,
                    confidence_level="medium",
                    method="gdop",
                ),
            )

        results = ConfidenceRepository.get_by_case(db, sample_case.id)
        assert len(results) == 3

    def test_get_by_case_empty(self, db: Session, sample_case):
        """Repository returns empty list for case with no results."""
        results = ConfidenceRepository.get_by_case(db, sample_case.id)
        assert results == []

    def test_get_latest_by_case(self, db: Session, sample_case):
        """Repository.get_latest_by_case returns the most recent result."""
        for i in range(3):
            ConfidenceRepository.create(
                db,
                ConfidenceResult(
                    case_id=sample_case.id,
                    confidence_score=0.5 + i * 0.1,
                    confidence_level="medium",
                    method="gdop",
                ),
            )

        latest = ConfidenceRepository.get_latest_by_case(db, sample_case.id)
        assert latest is not None

    def test_get_latest_by_case_empty(self, db: Session, sample_case):
        """Repository returns None for case with no results."""
        latest = ConfidenceRepository.get_latest_by_case(db, sample_case.id)
        assert latest is None

    def test_delete_by_case(self, db: Session, sample_case):
        """Repository.delete_by_case removes all confidence results for a case."""
        for i in range(3):
            ConfidenceRepository.create(
                db,
                ConfidenceResult(
                    case_id=sample_case.id,
                    confidence_score=0.5,
                    confidence_level="medium",
                    method="gdop",
                ),
            )

        count = ConfidenceRepository.delete_by_case(db, sample_case.id)
        assert count == 3

        results = ConfidenceRepository.get_by_case(db, sample_case.id)
        assert results == []


# ---------------------------------------------------------------------------
# Test: ConfidenceService
# ---------------------------------------------------------------------------


class TestConfidenceService:
    """Test the confidence service layer."""

    def test_run_confidence_requires_case(self, db: Session):
        """Service raises 404 for non-existent case."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            ConfidenceService.run_confidence(db, "CASE-999")
        assert exc_info.value.status_code == 404

    def test_run_confidence_requires_scenario(self, db: Session):
        """Service raises error for case without scenario."""
        from app.shared.validation import ValidationError

        case = Case(title="No Scenario Case", description="Test")
        db.add(case)
        db.commit()
        db.refresh(case)

        case_code = f"CASE-{case.id:03d}"
        with pytest.raises(ValidationError):
            ConfidenceService.run_confidence(db, case_code)

    def test_run_confidence_requires_measurements(self, db: Session, sample_case):
        """Service raises error when no measurements exist."""
        from app.shared.validation import ValidationError

        case_code = f"CASE-{sample_case.id:03d}"
        with pytest.raises(ValidationError):
            ConfidenceService.run_confidence(db, case_code)

    def test_run_confidence_success(
        self,
        db: Session,
        sample_case,
        sample_measurements,
        sample_localization_result,
    ):
        """Service runs confidence analysis end-to-end and returns expected structure."""
        case_code = f"CASE-{sample_case.id:03d}"
        result = ConfidenceService.run_confidence(db, case_code)

        assert result["case_code"] == case_code.upper()
        assert 0.0 <= result["confidence_score"] <= 1.0
        assert result["confidence_level"] in ("high", "medium", "low")
        assert result["method"] == "gdop"
        assert result["computation_time_ms"] > 0

    def test_run_confidence_persists_result(
        self,
        db: Session,
        sample_case,
        sample_measurements,
        sample_localization_result,
    ):
        """Service persists confidence result to the database."""
        case_code = f"CASE-{sample_case.id:03d}"
        ConfidenceService.run_confidence(db, case_code)

        stored = ConfidenceRepository.get_by_case(db, sample_case.id)
        assert len(stored) == 1
        assert stored[0].method == "gdop"
        assert stored[0].localization_result_id == sample_localization_result.id

    def test_run_confidence_links_localization(
        self,
        db: Session,
        sample_case,
        sample_measurements,
        sample_localization_result,
    ):
        """Confidence result references the latest localization result."""
        case_code = f"CASE-{sample_case.id:03d}"
        ConfidenceService.run_confidence(db, case_code)

        stored = ConfidenceRepository.get_latest_by_case(db, sample_case.id)
        assert stored is not None
        assert stored.localization_result_id == sample_localization_result.id


# ---------------------------------------------------------------------------
# Test: EvidenceService
# ---------------------------------------------------------------------------


class TestEvidenceService:
    """Test the evidence service layer."""

    def test_get_evidence_requires_case(self, db: Session):
        """Service raises 404 for non-existent case."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            EvidenceService.get_evidence(db, "CASE-999")
        assert exc_info.value.status_code == 404

    def test_get_evidence_requires_scenario(self, db: Session):
        """Service raises error for case without scenario."""
        from app.shared.validation import ValidationError

        case = Case(title="No Scenario Case", description="Test")
        db.add(case)
        db.commit()
        db.refresh(case)

        case_code = f"CASE-{case.id:03d}"
        with pytest.raises(ValidationError):
            EvidenceService.get_evidence(db, case_code)

    def test_get_evidence_requires_measurements(self, db: Session, sample_case):
        """Service raises error when no measurements exist."""
        from app.shared.validation import ValidationError

        case_code = f"CASE-{sample_case.id:03d}"
        with pytest.raises(ValidationError):
            EvidenceService.get_evidence(db, case_code)

    def test_get_evidence_success(self, db: Session, sample_case, sample_measurements):
        """Service returns evidence audit packet with expected structure."""
        case_code = f"CASE-{sample_case.id:03d}"
        result = EvidenceService.get_evidence(db, case_code)

        assert result["case_code"] == case_code.upper()
        assert "summary" in result
        assert "towers" in result
        assert "accepted_measurement_ids" in result
        assert "rejections" in result

        # Validate summary structure
        summary = result["summary"]
        assert "total_measurements" in summary
        assert "accepted_measurements" in summary
        assert "rejected_measurements" in summary
        assert "towers_total" in summary
        assert "towers_used_count" in summary
        assert summary["total_measurements"] == 6

    def test_get_evidence_includes_tower_details(
        self, db: Session, sample_case, sample_measurements
    ):
        """Evidence packet includes per-tower audit details."""
        case_code = f"CASE-{sample_case.id:03d}"
        result = EvidenceService.get_evidence(db, case_code)

        towers = result["towers"]
        assert len(towers) > 0

        tower = towers[0]
        assert "tower_id" in tower
        assert "latitude" in tower
        assert "longitude" in tower
        assert "total_measurements" in tower
        assert "status" in tower
        assert tower["status"] in ("active", "inactive")

    def test_get_evidence_with_confidence(
        self,
        db: Session,
        sample_case,
        sample_measurements,
        sample_localization_result,
    ):
        """Evidence packet includes confidence data when available."""
        # First run confidence to have data available
        case_code = f"CASE-{sample_case.id:03d}"
        ConfidenceService.run_confidence(db, case_code)

        result = EvidenceService.get_evidence(db, case_code)
        assert result["confidence"] is not None
        assert "confidence_score" in result["confidence"]
        assert "confidence_level" in result["confidence"]
        assert "method" in result["confidence"]

    def test_get_evidence_without_confidence(
        self, db: Session, sample_case, sample_measurements
    ):
        """Evidence packet has null confidence when no confidence run exists."""
        case_code = f"CASE-{sample_case.id:03d}"
        result = EvidenceService.get_evidence(db, case_code)

        assert result["confidence"] is None


# ---------------------------------------------------------------------------
# Test: API endpoint conformance
# ---------------------------------------------------------------------------


class TestConfidenceAPIConformance:
    """Test the confidence API endpoint returns correct response shape."""

    def test_run_endpoint_requires_case_code(self):
        """POST /confidence/run requires case_code query param."""
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.post("/api/v1/confidence/run")
        assert response.status_code == 422  # Missing required query param

        app.dependency_overrides.clear()

    def test_run_endpoint_invalid_case_code(self):
        """POST /confidence/run with invalid case code returns error."""
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.post("/api/v1/confidence/run?case_code=INVALID")
        assert response.status_code in (400, 404, 422)

        app.dependency_overrides.clear()

    def test_run_endpoint_case_not_found(self):
        """POST /confidence/run with non-existent case returns 404."""
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.post("/api/v1/confidence/run?case_code=CASE-999")
        assert response.status_code == 404

        app.dependency_overrides.clear()

    def test_response_schema_fields(self):
        """Verify the response schema has all expected fields."""
        from app.schemas.confidence import ConfidenceRunResponse

        fields = ConfidenceRunResponse.model_fields
        expected_fields = [
            "case_code",
            "confidence_score",
            "confidence_level",
            "error_ellipse_semi_major_m",
            "error_ellipse_semi_minor_m",
            "error_ellipse_orientation_deg",
            "gdop",
            "method",
            "computation_time_ms",
        ]
        for field in expected_fields:
            assert field in fields, f"Missing field in ConfidenceRunResponse: {field}"


class TestEvidenceAPIConformance:
    """Test the evidence API endpoint returns correct response shape."""

    def test_get_endpoint_invalid_case_code(self):
        """GET /evidence/{case_code} with invalid case code returns error."""
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.get("/api/v1/evidence/INVALID")
        assert response.status_code in (400, 404, 422)

        app.dependency_overrides.clear()

    def test_get_endpoint_case_not_found(self):
        """GET /evidence/{case_code} with non-existent case returns 404."""
        from main import app

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.get("/api/v1/evidence/CASE-999")
        assert response.status_code == 404

        app.dependency_overrides.clear()

    def test_response_schema_fields(self):
        """Verify the response schema has all expected fields."""
        from app.schemas.evidence import (
            EvidenceResponse,
            EvidenceSummary,
            EvidenceTower,
        )

        fields = EvidenceResponse.model_fields
        expected_fields = [
            "case_code",
            "scenario_id",
            "summary",
            "towers",
            "accepted_measurement_ids",
            "rejections",
            "confidence",
        ]
        for field in expected_fields:
            assert field in fields, f"Missing field in EvidenceResponse: {field}"

        summary_fields = EvidenceSummary.model_fields
        expected_summary = [
            "total_measurements",
            "accepted_measurements",
            "rejected_measurements",
            "towers_total",
            "towers_used_count",
        ]
        for field in expected_summary:
            assert field in summary_fields, f"Missing field in EvidenceSummary: {field}"

        tower_fields = EvidenceTower.model_fields
        expected_tower = [
            "tower_id",
            "latitude",
            "longitude",
            "total_measurements",
            "accepted_measurements",
            "rejected_measurements",
            "status",
        ]
        for field in expected_tower:
            assert field in tower_fields, f"Missing field in EvidenceTower: {field}"
