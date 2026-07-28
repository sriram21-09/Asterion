import pytest
from app.database.base import Base
from app.models.case import Case
from app.models.movement_event import MovementEvent
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


def test_get_heatmap_empty_case(client, test_db_session):
    case = Case(title="Empty Case", status="open")
    test_db_session.add(case)
    test_db_session.commit()

    response = client.get(f"/api/v1/dashboard/{case.id}/heatmap")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["type"] == "FeatureCollection"
    assert len(data["data"]["features"]) == 0


def test_get_heatmap_with_data(client, test_db_session):
    case = Case(title="Test Case", status="open")
    test_db_session.add(case)
    test_db_session.commit()

    events = [
        MovementEvent(
            case_id=case.id,
            sequence_number=1,
            event_type="location_update",
            latitude=10.000,
            longitude=20.000,
            dwell_time_seconds=100,
            confidence=0.8,
        ),
        MovementEvent(
            case_id=case.id,
            sequence_number=2,
            event_type="handover",
            latitude=10.000,
            longitude=20.000,
            dwell_time_seconds=50,
            confidence=0.9,
        ),
        MovementEvent(
            case_id=case.id,
            sequence_number=3,
            event_type="location_update",
            latitude=10.010,
            longitude=20.010,
            dwell_time_seconds=300,
            confidence=0.5,
        ),
    ]
    test_db_session.add_all(events)
    test_db_session.commit()

    response = client.get(f"/api/v1/dashboard/{case.id}/heatmap")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    features = data["data"]["features"]
    assert len(features) == 2

    response = client.get(
        f"/api/v1/dashboard/{case.id}/heatmap?w1=1.0&w2=0.0&w3=0.0&w4=0.0"
    )
    assert response.status_code == 200
    data2 = response.json()
    features2 = data2["data"]["features"]
    assert len(features2) == 2


def test_get_heatmap_single_record(client, test_db_session):
    case = Case(title="Single Record Case", status="open")
    test_db_session.add(case)
    test_db_session.commit()

    event = MovementEvent(
        case_id=case.id,
        sequence_number=1,
        event_type="location_update",
        latitude=10.000,
        longitude=20.000,
        dwell_time_seconds=100,
        confidence=0.8,
    )
    test_db_session.add(event)
    test_db_session.commit()

    response = client.get(f"/api/v1/dashboard/{case.id}/heatmap")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    features = data["data"]["features"]
    assert len(features) == 1
    assert features[0]["properties"]["intensity"] == 0.75
