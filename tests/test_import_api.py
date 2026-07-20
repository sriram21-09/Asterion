import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.import_job import ImportJob  # noqa: F401
from app.models.cdr_record import CDRRecord  # noqa: F401
from main import app
from app.database.session import get_db

SAMPLE_AIRTEL_CONTENT = """BHARTI AIRTEL LIMITED 

Target No,Call Type,TOC,B Party No,LRN No,LRN TSP-LSA,Date,Time,Dur(s),First CGI Lat/Long,First CGI,Last CGI Lat/Long,Last CGI,SMSC No,Service Type,IMEI,IMSI,Call Fow No,Roam Nw,SW & MSC ID,IN TG,OUT TG,Vowifi First UE IP,Port1,Vowifi Last UE IP,Port2
'9714499703',SMT,Post,'AD-Airtel-S',,-,'15/04/2026',08:26:10,0,21.29669/72.8915,404-98-8331-230711555,,---,'919892341012',SMS,'866588055801530','404980531580367',-,AIR GJ,'9898092816',,,,,,
"""

SAMPLE_BSNL_CONTENT = """Search Criteria : MSISDN
Target/A-Party Number,Call Type,Type of Connection,Other/B-party Number,LRN of B-Party Number,Translation of LRN,Call Date,Call Initiation Time,Call Duration,First BTS Location,First Cell Global ID,Last BTS Location,Last Cell Global ID,SMS Centre No.,Service Type,IMEI,IMSI,Original Calling Party,Roaming Network/Circle,Switch/MSC ID,In TG,Out TG
9477523061,IN,,57645,,,17/06/2026,15:58:21,1,Mallickpur II C; Kolkata; Lat-22.39711; Long-88.43938,404-81-724-24723,,-,919417899997,SMS,359912109839650,404819000158900,,BSNL - Kolkata,919433599995,,
"""


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()



def test_upload_airtel_file(client):
    files = {
        "file": ("9714499703_Airtel.csv", SAMPLE_AIRTEL_CONTENT.encode("utf-8"), "text/csv")
    }
    response = client.post("/api/v1/import/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["job"]["operator"] == "airtel"
    assert data["data"]["summary"]["parsed_records"] == 1

    job_id = data["data"]["job"]["id"]

    # Query job details
    job_resp = client.get(f"/api/v1/import/jobs/{job_id}")
    assert job_resp.status_code == 200
    assert job_resp.json()["data"]["filename"] == "9714499703_Airtel.csv"

    # Query records
    records_resp = client.get(f"/api/v1/import/jobs/{job_id}/records")
    assert records_resp.status_code == 200
    records = records_resp.json()["data"]
    assert len(records) == 1
    assert records[0]["latitude"] == pytest.approx(21.29669)
    assert records[0]["longitude"] == pytest.approx(72.8915)


def test_upload_bsnl_file(client):
    files = {
        "file": ("9477523061_BSNL.csv", SAMPLE_BSNL_CONTENT.encode("utf-8"), "text/csv")
    }
    response = client.post("/api/v1/import/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["job"]["operator"] == "bsnl"
    assert data["data"]["summary"]["parsed_records"] == 1

    job_id = data["data"]["job"]["id"]

    records_resp = client.get(f"/api/v1/import/jobs/{job_id}/records")
    assert records_resp.status_code == 200
    records = records_resp.json()["data"]
    assert len(records) == 1
    assert records[0]["latitude"] == pytest.approx(22.39711)
    assert records[0]["longitude"] == pytest.approx(88.43938)


def test_upload_invalid_extension(client):
    files = {
        "file": ("test.pdf", b"fake pdf content", "application/pdf")
    }
    response = client.post("/api/v1/import/upload", files=files)
    assert response.status_code == 400
