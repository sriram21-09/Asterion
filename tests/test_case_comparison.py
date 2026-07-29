import pytest
from app.database.base import Base
from app.models.case import Case
from app.models.movement_event import MovementEvent
from app.models.confidence_result import ConfidenceResult
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database.session import get_db


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
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_compare_cases_success(client, test_db_session):
    # Setup test data
    case1 = Case(title="Case 1", status="open")
    case2 = Case(title="Case 2", status="open")
    test_db_session.add_all([case1, case2])
    test_db_session.commit()

    # Movement Events for Case 1
    events1 = [
        MovementEvent(
            case_id=case1.id,
            sequence_number=1,
            event_type="location_update",
            from_cgi="CGI-A",
            to_cgi="CGI-B",
            distance_from_prev_m=100.0,
        ),
        MovementEvent(
            case_id=case1.id,
            sequence_number=2,
            event_type="location_update",
            from_cgi="CGI-B",
            to_cgi="CGI-C",
            distance_from_prev_m=200.0,
        ),
    ]

    # Movement Events for Case 2
    events2 = [
        MovementEvent(
            case_id=case2.id,
            sequence_number=1,
            event_type="location_update",
            from_cgi="CGI-B",
            to_cgi="CGI-D",
            distance_from_prev_m=500.0,
        ),
    ]
    test_db_session.add_all(events1 + events2)

    # Confidence Results
    conf1 = ConfidenceResult(
        case_id=case1.id, confidence_score=0.8, confidence_level="high", method="gdop"
    )
    conf2 = ConfidenceResult(
        case_id=case1.id, confidence_score=0.9, confidence_level="high", method="gdop"
    )
    conf3 = ConfidenceResult(
        case_id=case2.id, confidence_score=0.6, confidence_level="medium", method="gdop"
    )
    test_db_session.add_all([conf1, conf2, conf3])
    test_db_session.commit()

    response = client.get(f"/api/v1/cases/compare?ids={case1.id},{case2.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    comparison = data["data"]
    assert len(comparison["cases"]) == 2

    # Verify Case 1 metrics
    c1_metrics = next(c for c in comparison["cases"] if c["case_id"] == case1.id)
    assert c1_metrics["total_distance_m"] == 300.0
    assert c1_metrics["average_confidence"] == pytest.approx(0.85)

    # Verify Case 2 metrics
    c2_metrics = next(c for c in comparison["cases"] if c["case_id"] == case2.id)
    assert c2_metrics["total_distance_m"] == 500.0
    assert c2_metrics["average_confidence"] == 0.6

    # Overlapping towers
    assert "CGI-B" in comparison["overlapping_towers"]
    assert "CGI-A" not in comparison["overlapping_towers"]

    # Distance diff
    assert comparison["max_distance_difference_m"] == 200.0


def test_compare_cases_not_found(client, test_db_session):
    case1 = Case(title="Case 1", status="open")
    test_db_session.add(case1)
    test_db_session.commit()

    response = client.get(f"/api/v1/cases/compare?ids={case1.id},9999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_compare_cases_bad_request(client, test_db_session):
    case1 = Case(title="Case 1", status="open")
    test_db_session.add(case1)
    test_db_session.commit()

    response = client.get(f"/api/v1/cases/compare?ids={case1.id}")
    assert response.status_code == 400
    data = response.json()
    assert "at least two case ids are required" in data["detail"].lower()


def test_compare_cases_invalid_format(client, test_db_session):
    response = client.get("/api/v1/cases/compare?ids=abc,def")
    assert response.status_code == 400
    data = response.json()
    assert "invalid case id" in data["detail"].lower()
