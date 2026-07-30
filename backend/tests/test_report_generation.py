import os
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

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_cases():
    db = SessionLocal()
    
    # 1. Empty Case (no measurements)
    empty_case = Case(title="Empty Case", status="open")
    db.add(empty_case)
    
    # 2. Minimal Case (we won't add measurements yet, just to have another case)
    minimal_case = Case(title="Minimal Case", status="open")
    db.add(minimal_case)
    
    db.commit()
    db.refresh(empty_case)
    db.refresh(minimal_case)
    
    yield {"empty": empty_case.id, "minimal": minimal_case.id}
    
    # Teardown
    db.delete(empty_case)
    db.delete(minimal_case)
    db.commit()
    db.close()

def test_report_generation_full(setup_cases):
    case_id = setup_cases["empty"]
    res = client.post(f"/api/v1/reports/{case_id}/generate?report_type=full")
    assert res.status_code == 200
    data = res.json()
    assert "report_path" in data

def test_report_generation_evidence_audit(setup_cases):
    case_id = setup_cases["empty"]
    res = client.post(f"/api/v1/reports/{case_id}/generate?report_type=evidence_audit")
    assert res.status_code == 200

def test_report_generation_validation_error(setup_cases):
    case_id = setup_cases["empty"]
    res = client.post(f"/api/v1/reports/{case_id}/generate?report_type=validation_error")
    assert res.status_code == 200

def test_report_generation_invalid_type(setup_cases):
    case_id = setup_cases["empty"]
    res = client.post(f"/api/v1/reports/{case_id}/generate?report_type=invalid_type_123")
    assert res.status_code == 400

def test_report_download(setup_cases):
    case_id = setup_cases["empty"]
    res = client.post(f"/api/v1/reports/{case_id}/generate?report_type=full")
    assert res.status_code == 200
    
    download_res = client.get(f"/api/v1/reports/{case_id}/download")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert download_res.content.startswith(b"%PDF-")
