import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import app
from app.database.session import SessionLocal
from app.models.case import Case
from app.models.cdr_record import CDRRecord
from app.models.import_job import ImportJob
from app.models.localization_result import LocalizationResult
from app.models.measurement import Measurement
from app.models.tracking_result import TrackingResult

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_benchmark_case():
    db = SessionLocal()

    # Create Case
    test_case = Case(title="Benchmark Test Case", status="open")
    db.add(test_case)
    db.commit()
    db.refresh(test_case)

    # Create Import Job for CDRs
    import_job = ImportJob(filename="test_cdrs.csv", status="completed")
    db.add(import_job)
    db.commit()
    db.refresh(import_job)

    # Create Measurements (1 valid, 1 invalid coords)
    now = datetime.now(timezone.utc)
    m1 = Measurement(
        case_id=test_case.id,
        measurement_code="M_TEST_1",
        timestamp=now,
        rssi_dbm=-70.0,
        latitude=12.9716,
        longitude=77.5946,
    )
    m2 = Measurement(
        case_id=test_case.id,
        measurement_code="M_TEST_2",
        timestamp=now,
        rssi_dbm=-70.0,
        latitude=95.0,  # Invalid latitude
        longitude=77.5946,
    )
    db.add_all([m1, m2])

    # Create CDR Records (1 resolved, 1 unresolved)
    cdr1 = CDRRecord(
        import_job_id=import_job.id,
        case_id=test_case.id,
        operator="TestOp",
        timestamp=now,
        latitude=12.9716,
        longitude=77.5946,
    )
    cdr2 = CDRRecord(
        import_job_id=import_job.id,
        case_id=test_case.id,
        operator="TestOp",
        timestamp=now,
        latitude=None,
        longitude=None,
    )
    db.add_all([cdr1, cdr2])

    # Create Localization and Tracking results for Kalman Factor
    loc1 = LocalizationResult(
        case_id=test_case.id,
        algorithm="test_algo",
        estimated_latitude=12.97,
        estimated_longitude=77.59,
        error_m=50.0,
        signals_used=3,
    )
    db.add(loc1)
    db.commit()
    db.refresh(loc1)

    trk1 = TrackingResult(
        case_id=test_case.id,
        localization_result_id=loc1.id,
        step_number=1,
        smoothed_latitude=12.971,
        smoothed_longitude=77.594,
        error_m=25.0,
    )
    db.add(trk1)
    db.commit()

    yield test_case.id

    # Teardown
    db.delete(test_case)
    db.delete(import_job)
    db.commit()
    db.close()


def test_get_benchmark(setup_benchmark_case):
    case_id = setup_benchmark_case
    res = client.get(f"/api/v1/validation/benchmark/{case_id}")
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert "metrics" in data
    assert "case_passed" in data

    metrics = {m["metric_name"]: m for m in data["metrics"]}

    # 1 valid, 1 invalid -> 50%
    assert metrics["Validation Pass Rate"]["value"] == 50.0

    # 1 with lat/lon, 1 without -> 50%
    assert metrics["Tower Resolution Rate"]["value"] == 50.0
    assert metrics["Unknown Tower Percentage"]["value"] == 50.0

    # 50.0 / 25.0 -> 2.0
    assert metrics["Kalman Improvement Factor"]["value"] == 2.0

    # Test thresholds (default thresholds might cause pass to be false)
    # Validation Pass Rate (50 < 90) -> False
    assert metrics["Validation Pass Rate"]["passed"] is False
    assert data["case_passed"] is False
