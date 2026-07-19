import sys
from pathlib import Path
import datetime

# Setup path for backend imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.database.session import get_db
from app.models.base import Base
from app.models.case import Case
from app.models.scenario import Scenario
from app.models.measurement import Measurement
from app.shared.validation import (
    decode_case_code,
    encode_case_code,
    decode_scenario_code,
    encode_scenario_code,
    decode_measurement_code,
    encode_measurement_code,
    ValidationError,
)

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


class TestIdentifierTranslation:
    """Validate that human-readable codes map cleanly to database integer IDs."""

    def test_case_code_translation(self):
        assert encode_case_code(1) == "CASE-001"
        assert encode_case_code(42) == "CASE-042"
        assert encode_case_code(999) == "CASE-999"
        assert decode_case_code("CASE-001") == 1
        assert decode_case_code("CASE-042") == 42
        assert decode_case_code("CASE-999") == 999

        # Case sensitivity validation
        assert decode_case_code("case-001") == 1

        # Failure paths
        with pytest.raises(ValidationError):
            decode_case_code("INVALID-001")
        with pytest.raises(ValidationError):
            decode_case_code("CASE-")
        with pytest.raises(ValidationError):
            decode_case_code("CASE-abc")

    def test_scenario_code_translation(self):
        assert encode_scenario_code(1) == "SCN-001"
        assert decode_scenario_code("SCN-001") == 1

        with pytest.raises(ValidationError):
            decode_scenario_code("SCN-")

    def test_measurement_code_translation(self):
        assert encode_measurement_code(1) == "MEAS-0001"
        assert decode_measurement_code("MEAS-0001") == 1

        with pytest.raises(ValidationError):
            decode_measurement_code("MEAS-")


class TestMeasurementDatabase:
    """Validate DB persistence and cascade behaviors on scenarios and cases."""

    def test_create_measurement_valid(self, db_session):
        scenario = Scenario(name="Urban 3-Tower Test")
        db_session.add(scenario)
        db_session.commit()

        case = Case(title="Tracking Device", scenario_id=scenario.id)
        db_session.add(case)
        db_session.commit()

        meas = Measurement(
            case_id=case.id,
            scenario_id=scenario.id,
            measurement_code="MEAS-0001",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            rssi_dbm=-75.5,
            latitude=12.9716,
            longitude=77.5946,
            timing_advance=1.0,
            uncertainty_m=10.0,
        )
        db_session.add(meas)
        db_session.commit()
        db_session.refresh(meas)

        assert meas.id is not None
        assert meas.case_id == case.id
        assert meas.scenario_id == scenario.id
        assert meas.measurement_code == "MEAS-0001"
        assert meas.rssi_dbm == -75.5
        assert meas.latitude == 12.9716
        assert meas.longitude == 77.5946
        assert meas.timing_advance == 1.0
        assert meas.uncertainty_m == 10.0

    def test_get_by_case_code(self, db_session):
        scenario = Scenario(name="Urban 3-Tower Test")
        db_session.add(scenario)
        db_session.commit()

        case = Case(title="Tracking Device", scenario_id=scenario.id)
        db_session.add(case)
        db_session.commit()

        meas = Measurement(
            case_id=case.id,
            scenario_id=scenario.id,
            measurement_code="MEAS-0001",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            rssi_dbm=-75.5,
        )
        db_session.add(meas)
        db_session.commit()

        from app.repositories.measurement_repository import MeasurementRepository

        results = MeasurementRepository.get_by_case_code(db_session, "CASE-001")
        assert len(results) == 1
        assert results[0].id == meas.id

        # Non-existent or invalid codes
        assert len(MeasurementRepository.get_by_case_code(db_session, "CASE-999")) == 0
        with pytest.raises(ValidationError):
            MeasurementRepository.get_by_case_code(db_session, "INVALID-001")

    def test_cascade_delete_case(self, db_session):
        scenario = Scenario(name="Urban Test")
        db_session.add(scenario)
        db_session.commit()

        case = Case(title="Case to Delete", scenario_id=scenario.id)
        db_session.add(case)
        db_session.commit()

        meas = Measurement(
            case_id=case.id,
            scenario_id=scenario.id,
            measurement_code="MEAS-0001",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            rssi_dbm=-75.5,
        )
        db_session.add(meas)
        db_session.commit()

        # Delete case
        db_session.delete(case)
        db_session.commit()

        # Verify measurement cascade deleted
        db_meas = (
            db_session.query(Measurement)
            .filter_by(measurement_code="MEAS-0001")
            .first()
        )
        assert db_meas is None

    def test_cascade_delete_scenario(self, db_session):
        scenario = Scenario(name="Scenario to Delete")
        db_session.add(scenario)
        db_session.commit()

        case = Case(title="Case A", scenario_id=scenario.id)
        db_session.add(case)
        db_session.commit()

        meas = Measurement(
            case_id=case.id,
            scenario_id=scenario.id,
            measurement_code="MEAS-0002",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            rssi_dbm=-85.0,
        )
        db_session.add(meas)
        db_session.commit()

        # Delete scenario
        db_session.delete(scenario)
        db_session.commit()

        # Verify measurement cascade deleted
        db_meas = (
            db_session.query(Measurement)
            .filter_by(measurement_code="MEAS-0002")
            .first()
        )
        assert db_meas is None


class TestSimulationAPI:
    """Validate API contract, parameter override, and error cases."""

    def test_generate_simulation_success(self, client, db_session):
        # Create scenario in DB mapping SCN-CFG-001 in json
        scenario = Scenario(name="Urban 3-Tower Multilateration")
        db_session.add(scenario)
        db_session.commit()
        assert scenario.id == 1

        case = Case(title="Device tracking case", scenario_id=scenario.id)
        db_session.add(case)
        db_session.commit()
        assert case.id == 1

        payload = {
            "algorithm": "multilateration",
            "max_iterations": 100,
            "convergence_threshold_m": 1.0,
            "measurement_count": 2,
            "enable_noise": True,
            "random_seed": 42,
        }

        response = client.post(
            "/api/v1/simulation/generate?case_code=CASE-001", json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        measurements = data["data"]
        assert len(measurements) > 0

        # Verify fields in the API response
        first_meas = measurements[0]
        assert first_meas["case_code"] == "CASE-001"
        assert first_meas["scenario_code"] == "SCN-001"
        assert "measurement_code" in first_meas
        assert "rssi_dbm" in first_meas
        assert first_meas["latitude"] is not None
        assert first_meas["longitude"] is not None

        # Verify DB records match
        db_meas = db_session.query(Measurement).filter_by(case_id=case.id).all()
        assert len(db_meas) == len(measurements)

    def test_generate_simulation_nonexistent_case(self, client):
        payload = {
            "algorithm": "multilateration",
            "max_iterations": 100,
            "convergence_threshold_m": 1.0,
            "measurement_count": 2,
            "enable_noise": True,
            "random_seed": 42,
        }
        response = client.post(
            "/api/v1/simulation/generate?case_code=CASE-999", json=payload
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_simulation_case_no_scenario(self, client, db_session):
        # Create case without scenario_id
        case = Case(title="Orphan Case")
        db_session.add(case)
        db_session.commit()

        case_code = encode_case_code(case.id)
        payload = {
            "algorithm": "multilateration",
            "max_iterations": 100,
            "convergence_threshold_m": 1.0,
            "measurement_count": 2,
            "enable_noise": True,
            "random_seed": 42,
        }
        response = client.post(
            f"/api/v1/simulation/generate?case_code={case_code}", json=payload
        )
        assert response.status_code == 400
        assert "scenario" in response.json()["error"]["message"].lower()
