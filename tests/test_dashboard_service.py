from datetime import datetime, timezone
import pytest
from app.database.base import Base
from app.database.session import get_db
from app.models.case import Case
from app.models.cdr_record import CDRRecord
from app.models.confidence_result import ConfidenceResult
from app.models.import_job import ImportJob
from app.models.localization_result import LocalizationResult
from app.models.measurement import Measurement
from app.models.movement_event import MovementEvent
from app.models.tower import Tower
from app.models.tracking_result import TrackingResult
from app.services.dashboard_service import DashboardService
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def test_db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(test_db_session):
    def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_dashboard_health(client):
    response = client.get("/api/v1/dashboard/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "dashboard-api"


def test_get_case_summary_non_existent(test_db_session):
    with pytest.raises(Exception) as exc_info:
        DashboardService.get_case_summary(test_db_session, case_id=99999)
    assert "99999" in str(exc_info.value.detail)


def test_get_case_summary_non_existent_api(client):
    response = client.get("/api/v1/dashboard/99999/summary")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"


def test_get_case_summary_empty_case(test_db_session, client):
    # Create empty case
    case = Case(
        title="Test Empty Case", description="No data attached yet", status="open"
    )
    test_db_session.add(case)
    test_db_session.commit()
    test_db_session.refresh(case)

    # Test service directly
    summary = DashboardService.get_case_summary(test_db_session, case_id=case.id)
    assert summary.case.id == case.id
    assert summary.case.title == "Test Empty Case"
    assert summary.cdr.total_records == 0
    assert summary.towers.total_towers == 0
    assert summary.movement.total_events == 0
    assert summary.localization.total_results == 0
    assert summary.pipeline_status.imported is False

    # Test via API endpoint
    response = client.get(f"/api/v1/dashboard/{case.id}/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    payload = data["data"]
    assert payload["case"]["id"] == case.id
    assert payload["case"]["title"] == "Test Empty Case"
    assert payload["cdr"]["total_records"] == 0
    assert payload["pipeline_status"]["imported"] is False


def test_get_case_summary_populated_case(test_db_session, client):
    # 1. Create Case
    case = Case(
        title="Full Investigation Case",
        description="Populated test case",
        status="active",
    )
    test_db_session.add(case)
    test_db_session.commit()
    test_db_session.refresh(case)

    # 2. Add ImportJob
    job = ImportJob(
        filename="test_airtel.csv",
        operator="airtel",
        status="completed",
        case_id=case.id,
    )
    test_db_session.add(job)
    test_db_session.commit()
    test_db_session.refresh(job)

    # 3. Add CDRRecords
    now = datetime.now(timezone.utc)
    rec1 = CDRRecord(
        import_job_id=job.id,
        case_id=case.id,
        operator="airtel",
        target_number="9876543210",
        b_party_number="9123456789",
        call_type="Voice",
        service_type="MOC",
        timestamp=now,
        latitude=21.29669,
        longitude=72.8915,
        first_cgi="404-98-8331-23071",
        last_cgi="404-98-8331-23071",
        imei="866588055801530",
        imsi="404980531580367",
    )
    rec2 = CDRRecord(
        import_job_id=job.id,
        case_id=case.id,
        operator="jio",
        target_number="9876543210",
        b_party_number="9988776655",
        call_type="SMS",
        service_type="SMS",
        timestamp=now,
        latitude=None,
        longitude=None,
        first_cgi="404-05-1234-56789",
        imei="866588055801530",
    )
    test_db_session.add_all([rec1, rec2])

    # 4. Add Towers
    t1 = Tower(
        tower_name="Tower Airtel 1",
        cgi="404-98-8331-23071",
        latitude=21.29669,
        longitude=72.8915,
        confidence=1.0,
        confidence_category="Known",
    )
    t2 = Tower(
        tower_name="Tower Jio 1",
        cgi="404-05-1234-56789",
        latitude=None,
        longitude=None,
        confidence=0.2,
        confidence_category="Unknown",
    )
    test_db_session.add_all([t1, t2])

    # 5. Add Measurement
    m = Measurement(
        case_id=case.id,
        measurement_code="M001",
        timestamp=now,
        rssi_dbm=-75.0,
        latitude=21.29669,
        longitude=72.8915,
    )
    test_db_session.add(m)

    # 6. Add MovementEvents
    m_ev1 = MovementEvent(
        case_id=case.id,
        sequence_number=1,
        event_type="location_update",
        timestamp=now,
        latitude=21.29669,
        longitude=72.8915,
        speed_kmh=20.0,
        distance_from_prev_m=0.0,
    )
    m_ev2 = MovementEvent(
        case_id=case.id,
        sequence_number=2,
        event_type="handover",
        timestamp=now,
        latitude=21.29669,
        longitude=72.8915,
        speed_kmh=0.0,
        distance_from_prev_m=500.0,
    )
    test_db_session.add_all([m_ev1, m_ev2])

    # 7. Add LocalizationResult
    loc_res = LocalizationResult(
        case_id=case.id,
        algorithm="weighted_centroid",
        estimated_latitude=21.29670,
        estimated_longitude=72.89160,
        error_m=12.5,
        computation_time_ms=4.2,
        signals_used=2,
    )
    test_db_session.add(loc_res)
    test_db_session.commit()
    test_db_session.refresh(loc_res)

    # 8. Add TrackingResult
    track_res = TrackingResult(
        case_id=case.id,
        localization_result_id=loc_res.id,
        step_number=1,
        smoothed_latitude=21.29670,
        smoothed_longitude=72.89160,
        velocity_mps=5.5,
        heading_deg=90.0,
        algorithm="kalman",
    )
    test_db_session.add(track_res)

    # 9. Add ConfidenceResult
    conf_res = ConfidenceResult(
        case_id=case.id,
        localization_result_id=loc_res.id,
        confidence_score=0.85,
        confidence_level="high",
        gdop=1.4,
        method="gdop",
    )
    test_db_session.add(conf_res)
    test_db_session.commit()

    # Query dashboard summary API
    response = client.get(f"/api/v1/dashboard/{case.id}/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    summary = data["data"]
    # Check Case Info
    assert summary["case"]["id"] == case.id
    assert summary["case"]["title"] == "Full Investigation Case"

    # Check CDR Summary
    assert summary["cdr"]["total_records"] == 2
    assert summary["cdr"]["total_measurements"] == 1
    assert summary["cdr"]["operator_breakdown"] == {"airtel": 1, "jio": 1}
    assert summary["cdr"]["target_numbers"] == ["9876543210"]
    assert summary["cdr"]["imeis"] == ["866588055801530"]
    assert summary["cdr"]["imsis"] == ["404980531580367"]

    # Check Towers Summary
    assert summary["towers"]["total_towers"] == 2
    assert summary["towers"]["known_coords_count"] == 1
    assert summary["towers"]["unknown_coords_count"] == 1

    # Check Movement Summary
    assert summary["movement"]["total_events"] == 2
    assert summary["movement"]["handover_events"] == 1
    assert summary["movement"]["total_distance_km"] == 0.5
    assert summary["movement"]["max_speed_kmh"] == 20.0

    # Check Localization Summary
    assert summary["localization"]["total_results"] == 1
    assert summary["localization"]["latest_result"]["algorithm"] == "weighted_centroid"
    assert summary["localization"]["latest_result"]["error_m"] == 12.5

    # Check Tracking Summary
    assert summary["tracking"]["total_steps"] == 1
    assert summary["tracking"]["latest_step"]["algorithm"] == "kalman"

    # Check Confidence Summary
    assert summary["confidence"]["latest_result"]["confidence_score"] == 0.85
    assert summary["confidence"]["latest_result"]["confidence_level"] == "high"

    # Check Pipeline Health Status
    ps = summary["pipeline_status"]
    assert ps["imported"] is True
    assert ps["validated"] is True
    assert ps["towers_resolved"] is True
    assert ps["movement_reconstructed"] is True
    assert ps["localization_complete"] is True
    assert ps["confidence_generated"] is True
    assert ps["evidence_logged"] is True
    assert ps["report_ready"] is True
