"""
Tests for Movement Reconstruction Service & API
=================================================

Tests cover:
  - MovementEvent ORM model creation and relationships
  - MovementRepository CRUD operations
  - MovementReconstructionService event building, sorting, handover classification, and kinematics
  - Handover detection (CGI transitions between consecutive records & intra-record handovers)
  - Tracking data merging (nearest timestamp matching, coordinates & confidence)
  - API endpoint ``POST /api/v1/movement/reconstruct`` success and error handling
"""

import sys
from pathlib import Path

# Setup path for backend imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from datetime import UTC, datetime, timedelta

import app.database.base  # Ensure all ORM models are registered
import pytest
from app.database.session import get_db
from app.models.base import Base
from app.models.case import Case
from app.models.cdr_record import CDRRecord
from app.models.import_job import ImportJob
from app.models.movement_event import MovementEvent
from app.models.tracking_result import TrackingResult
from app.repositories.movement_repository import MovementRepository
from app.services.movement_service import (
    EVENT_TYPE_CALL_START,
    EVENT_TYPE_HANDOVER,
    EVENT_TYPE_SMS,
    MovementReconstructionService,
)
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Test database fixture setup
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
def client(db):
    """FastAPI TestClient using the test database session."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests: Model & Repository
# ---------------------------------------------------------------------------


def test_movement_event_orm_and_repo(db: Session):
    case = Case(id=1, title="Test Case", status="open")
    db.add(case)
    db.commit()

    now = datetime.now(UTC)
    evt1 = MovementEvent(
        case_id=case.id,
        sequence_number=1,
        event_type=EVENT_TYPE_CALL_START,
        timestamp=now,
        latitude=12.9716,
        longitude=77.5946,
        from_cgi="404-45-0001-0001",
        to_cgi="404-45-0001-0001",
        speed_kmh=0.0,
        heading_deg=None,
        distance_from_prev_m=0.0,
        dwell_time_seconds=0.0,
        confidence=0.9,
    )
    evt2 = MovementEvent(
        case_id=case.id,
        sequence_number=2,
        event_type=EVENT_TYPE_HANDOVER,
        timestamp=now + timedelta(seconds=60),
        latitude=12.9750,
        longitude=77.5980,
        from_cgi="404-45-0001-0001",
        to_cgi="404-45-0001-0002",
        speed_kmh=24.5,
        heading_deg=45.0,
        distance_from_prev_m=500.0,
        dwell_time_seconds=60.0,
        confidence=0.85,
    )

    MovementRepository.bulk_create(db, [evt1, evt2])

    events = MovementRepository.get_by_case(db, case.id)
    assert len(events) == 2
    assert events[0].sequence_number == 1
    assert events[0].event_type == EVENT_TYPE_CALL_START
    assert events[1].sequence_number == 2
    assert events[1].event_type == EVENT_TYPE_HANDOVER
    assert events[1].from_cgi == "404-45-0001-0001"
    assert events[1].to_cgi == "404-45-0001-0002"

    handovers = MovementRepository.get_by_case_and_type(
        db, case.id, EVENT_TYPE_HANDOVER
    )
    assert len(handovers) == 1
    assert handovers[0].id == events[1].id

    deleted = MovementRepository.delete_by_case(db, case.id)
    assert deleted == 2
    assert len(MovementRepository.get_by_case(db, case.id)) == 0


# ---------------------------------------------------------------------------
# Tests: MovementReconstructionService Logic
# ---------------------------------------------------------------------------


def test_reconstruct_movements_handover_and_kinematics(db: Session):
    # Setup Case and ImportJob
    case = Case(id=1, title="Handover Test Case", status="open")
    db.add(case)
    job = ImportJob(id=1, filename="test.csv", status="completed")
    db.add(job)
    db.commit()

    base_time = datetime(2026, 7, 23, 10, 0, 0, tzinfo=UTC)

    # CDR 1: Call start at CGI 1
    cdr1 = CDRRecord(
        import_job_id=job.id,
        case_id=case.id,
        operator="Airtel",
        target_number="9876543210",
        call_type="voice_outgoing",
        timestamp=base_time,
        latitude=12.9716,
        longitude=77.5946,
        first_cgi="CGI-001",
        last_cgi="CGI-001",
    )

    # CDR 2: SMS at CGI 2 (Different tower -> trigger inter-record handover)
    cdr2 = CDRRecord(
        import_job_id=job.id,
        case_id=case.id,
        operator="Airtel",
        target_number="9876543210",
        call_type="sms_outgoing",
        timestamp=base_time + timedelta(minutes=2),
        latitude=12.9816,
        longitude=77.6046,
        first_cgi="CGI-002",
        last_cgi="CGI-002",
    )

    db.add_all([cdr1, cdr2])
    db.commit()

    res = MovementReconstructionService.reconstruct_movements(db, "CASE-001")

    assert res["case_code"] == "CASE-001"
    # Should have cdr1, synthetic handover, cdr2 -> 3 events
    assert res["total_events"] == 3
    assert res["handover_count"] == 1

    events = res["events"]
    assert events[0]["event_type"] == EVENT_TYPE_CALL_START
    assert events[1]["event_type"] == EVENT_TYPE_HANDOVER
    assert events[1]["from_cgi"] == "CGI-001"
    assert events[1]["to_cgi"] == "CGI-002"
    assert events[2]["event_type"] == EVENT_TYPE_SMS

    assert res["total_distance_km"] > 0
    assert res["time_span_hours"] == pytest.approx(2 / 60.0, rel=1e-3)


def test_reconstruct_movements_with_tracking_merge(db: Session):
    case = Case(id=1, title="Tracking Merge Case", status="open")
    db.add(case)
    job = ImportJob(id=1, filename="test.csv", status="completed")
    db.add(job)
    db.commit()

    base_time = datetime(2026, 7, 23, 12, 0, 0, tzinfo=UTC)

    # CDR record without lat/lon coordinates
    cdr = CDRRecord(
        import_job_id=job.id,
        case_id=case.id,
        operator="Jio",
        target_number="9999999999",
        call_type="data",
        timestamp=base_time,
        latitude=None,
        longitude=None,
        first_cgi="CGI-100",
    )
    db.add(cdr)

    # Tracking result matching the timestamp
    tr = TrackingResult(
        case_id=case.id,
        step_number=1,
        smoothed_latitude=13.0827,
        smoothed_longitude=80.2707,
        timestamp=base_time,
        error_m=50.0,
    )
    db.add(tr)
    db.commit()

    res = MovementReconstructionService.reconstruct_movements(db, "CASE-001")

    assert res["total_events"] == 1
    evt = res["events"][0]
    assert evt["latitude"] == 13.0827
    assert evt["longitude"] == 80.2707
    assert evt["confidence"] is not None
    assert evt["confidence"] > 0.9  # exp(-50/1000) ~ 0.951


# ---------------------------------------------------------------------------
# Tests: API Router Endpoint
# ---------------------------------------------------------------------------


def test_reconstruct_movement_api_success(client: TestClient, db: Session):
    case = Case(id=1, title="API Test Case", status="open")
    db.add(case)
    job = ImportJob(id=1, filename="test.csv", status="completed")
    db.add(job)

    base_time = datetime(2026, 7, 23, 14, 0, 0, tzinfo=UTC)
    cdr = CDRRecord(
        import_job_id=job.id,
        case_id=case.id,
        operator="Vodafone",
        target_number="1234567890",
        call_type="voice",
        timestamp=base_time,
        latitude=12.9716,
        longitude=77.5946,
        first_cgi="CGI-ABC",
    )
    db.add(cdr)
    db.commit()

    response = client.post("/api/v1/movement/reconstruct?case_code=CASE-001")
    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["case_code"] == "CASE-001"
    assert data["total_events"] == 1
    assert len(data["events"]) == 1


def test_reconstruct_movement_api_not_found(client: TestClient):
    response = client.post("/api/v1/movement/reconstruct?case_code=CASE-999")
    assert response.status_code == 404


def test_reconstruct_movement_api_no_records(client: TestClient, db: Session):
    case = Case(id=1, title="Empty Case", status="open")
    db.add(case)
    db.commit()

    response = client.post("/api/v1/movement/reconstruct?case_code=CASE-001")
    assert response.status_code == 400
