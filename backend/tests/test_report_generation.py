import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path to resolve 'app'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import app
from app.database.session import SessionLocal
from app.models.case import Case

from app.models.base import Base
from app.database.engine import engine

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_cases():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Empty Case (no measurements)
    empty_case = Case(title="Empty Case", status="open")
    db.add(empty_case)

    # 2. Minimal Case with actual measurements and CDR records
    minimal_case = Case(title="Minimal Case", status="open")
    db.add(minimal_case)
    db.commit()
    db.refresh(minimal_case)

    from datetime import datetime, timezone
    from app.models.measurement import Measurement
    from app.models.cdr_record import CDRRecord
    from app.models.import_job import ImportJob

    job = ImportJob(case_id=minimal_case.id, filename="test.csv", status="completed")
    db.add(job)
    db.commit()
    db.refresh(job)

    meas = Measurement(
        case_id=minimal_case.id,
        measurement_code="M-001",
        timestamp=datetime.now(timezone.utc),
        latitude=19.0760,
        longitude=72.8780,
        rssi_dbm=-75.0,
        source="REAL",
    )
    cdr = CDRRecord(
        import_job_id=job.id,
        case_id=minimal_case.id,
        operator="Airtel",
        target_number="9876543210",
        call_type="VOICE",
        timestamp=datetime.now(timezone.utc),
        first_cgi="CGI-404-45-13872",
        latitude=19.0760,
        longitude=72.8780,
        duration=120,
    )
    db.add(meas)
    db.add(cdr)

    db.commit()

    yield {"empty": empty_case.id, "minimal": minimal_case.id}

    # Teardown
    db.query(Measurement).filter(Measurement.case_id == minimal_case.id).delete()
    db.query(CDRRecord).filter(CDRRecord.case_id == minimal_case.id).delete()
    db.query(ImportJob).filter(ImportJob.case_id == minimal_case.id).delete()
    db.delete(empty_case)
    db.delete(minimal_case)
    db.commit()
    db.close()


def test_report_generation_full(setup_cases):
    case_id = setup_cases["empty"]
    res = client.post(f"/api/v1/reports/{case_id}/generate?report_type=full")
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    assert "report_path" in res_data["data"]


def test_report_generation_evidence_audit(setup_cases):
    case_id = setup_cases["empty"]
    res = client.post(f"/api/v1/reports/{case_id}/generate?report_type=evidence_audit")
    assert res.status_code == 200


def test_report_generation_validation_error(setup_cases):
    case_id = setup_cases["empty"]
    res = client.post(
        f"/api/v1/reports/{case_id}/generate?report_type=validation_error"
    )
    assert res.status_code == 200


def test_report_generation_invalid_type(setup_cases):
    case_id = setup_cases["empty"]
    res = client.post(
        f"/api/v1/reports/{case_id}/generate?report_type=invalid_type_123"
    )
    assert res.status_code == 400


def test_report_download(setup_cases):
    case_id = setup_cases["empty"]
    res = client.post(f"/api/v1/reports/{case_id}/generate?report_type=full")
    assert res.status_code == 200

    download_res = client.get(f"/api/v1/reports/{case_id}/download")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert download_res.content.startswith(b"%PDF-")


def test_report_preview_structure(setup_cases):
    case_id = setup_cases["empty"]
    res = client.get(f"/api/v1/reports/{case_id}/preview?report_type=full")
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert "metadata" in data
    assert "report_id" in data["metadata"]
    assert data["metadata"]["crs"] == "WGS84 (EPSG:4326)"
    assert "data_quality" in data
    assert "dataset_completeness" in data["data_quality"]
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    assert "evidence_hash" in data["evidence"]


def test_report_generation_with_measurements(setup_cases):
    case_id = setup_cases["minimal"]
    res = client.post(f"/api/v1/reports/{case_id}/generate?report_type=full")
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    assert "report_path" in res_data["data"]



