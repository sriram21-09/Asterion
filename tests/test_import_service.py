import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.import_job import ImportJob
from app.models.cdr_record import CDRRecord
from app.services.import_service import (
    AirtelCDRParser,
    BSNLCDRParser,
    CDRImportService,
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


SAMPLE_AIRTEL_CONTENT = """BHARTI AIRTEL LIMITED 

PAN India 

Call Details of Mobile No '9714499703' from '01-Jun-2025' to '05-Jun-2026' 

Target No,Call Type,TOC,B Party No,LRN No,LRN TSP-LSA,Date,Time,Dur(s),First CGI Lat/Long,First CGI,Last CGI Lat/Long,Last CGI,SMSC No,Service Type,IMEI,IMSI,Call Fow No,Roam Nw,SW & MSC ID,IN TG,OUT TG,Vowifi First UE IP,Port1,Vowifi Last UE IP,Port2
'9714499703',SMT,Post,'AD-Airtel-S',,-,'15/04/2026',08:26:10,0,21.29669/72.8915,404-98-8331-230711555,,---,'919892341012',SMS,'866588055801530','404980531580367',-,AIR GJ,'9898092816',,,,,,
'9714499703',OUT,Post,'8128778750',4106,VODA-GJ,'15/04/2026',09:42:17,41,21.29327/72.88987,404-98-8331-221532674,21.2741/72.86936,404-98-8331-236717574,'-',Voice,'866588055801530','404980531580367',-,AIR GJ,'9898081890',ims.mnc092.mcc404.3gppnetwork.org,10.92.26.67,,,,
"""


SAMPLE_BSNL_CONTENT = """Search Criteria : MSISDN
Search Value : 9477523061
Start Date : 202601010000
End Date : 202606250000

Target/A-Party Number,Call Type,Type of Connection,Other/B-party Number,LRN of B-Party Number,Translation of LRN,Call Date,Call Initiation Time,Call Duration,First BTS Location,First Cell Global ID,Last BTS Location,Last Cell Global ID,SMS Centre No.,Service Type,IMEI,IMSI,Original Calling Party,Roaming Network/Circle,Switch/MSC ID,In TG,Out TG
9477523061,IN,,57645,,,17/06/2026,15:58:21,1,Mallickpur II C; Kolkata; Lat-22.39711; Long-88.43938,404-81-724-24723,,-,919417899997,SMS,359912109839650,404819000158900,,BSNL - Kolkata,919433599995,,
9477523061,OUT,,9875651858,3104,Reliance Jio - Kolkata,19/06/2026,12:15:04,760,Mallickpur II C; Kolkata; Lat-22.39711; Long-88.43938,404-81-724-24723,Mallickpur II C; Kolkata; Lat-22.39711; Long-88.43938,404-81-724-24723,,Voice Call,353832116804840,404819000158900,,BSNL - Kolkata,919433599995,BSZJDV1,RJILKO_C
*** END OF REPORT ***
CDR COUNT : 2
"""


class TestAirtelCDRParser:
    def test_detect_airtel(self):
        parser = AirtelCDRParser()
        assert parser.detect(SAMPLE_AIRTEL_CONTENT) is True
        assert parser.detect("random content") is False

    def test_parse_airtel_records(self):
        parser = AirtelCDRParser()
        records, failed = parser.parse(SAMPLE_AIRTEL_CONTENT)
        assert failed == 0
        assert len(records) == 2

        rec0 = records[0]
        assert rec0["operator"] == "airtel"
        assert rec0["target_number"] == "9714499703"
        assert rec0["call_type"] == "SMT"
        assert rec0["b_party_number"] == "AD-Airtel-S"
        assert rec0["service_type"] == "SMS"
        assert rec0["duration"] == 0
        assert rec0["latitude"] == pytest.approx(21.29669)
        assert rec0["longitude"] == pytest.approx(72.8915)
        assert rec0["first_cgi"] == "404-98-8331-230711555"
        assert rec0["imei"] == "866588055801530"
        assert rec0["imsi"] == "404980531580367"
        assert isinstance(rec0["timestamp"], datetime)
        assert rec0["timestamp"].year == 2026
        assert rec0["timestamp"].month == 4
        assert rec0["timestamp"].day == 15

        rec1 = records[1]
        assert rec1["call_type"] == "OUT"
        assert rec1["b_party_number"] == "8128778750"
        assert rec1["duration"] == 41
        assert rec1["latitude"] == pytest.approx(21.29327)
        assert rec1["longitude"] == pytest.approx(72.88987)
        assert rec1["last_latitude"] == pytest.approx(21.2741)
        assert rec1["last_longitude"] == pytest.approx(72.86936)
        assert rec1["last_cgi"] == "404-98-8331-236717574"


class TestBSNLCDRParser:
    def test_detect_bsnl(self):
        parser = BSNLCDRParser()
        assert parser.detect(SAMPLE_BSNL_CONTENT) is True
        assert parser.detect("random content") is False

    def test_parse_bsnl_records(self):
        parser = BSNLCDRParser()
        records, failed = parser.parse(SAMPLE_BSNL_CONTENT)
        assert failed == 0
        assert len(records) == 2

        rec0 = records[0]
        assert rec0["operator"] == "bsnl"
        assert rec0["target_number"] == "9477523061"
        assert rec0["call_type"] == "IN"
        assert rec0["b_party_number"] == "57645"
        assert rec0["service_type"] == "SMS"
        assert rec0["duration"] == 1
        assert rec0["latitude"] == pytest.approx(22.39711)
        assert rec0["longitude"] == pytest.approx(88.43938)
        assert rec0["first_cgi"] == "404-81-724-24723"
        assert rec0["imei"] == "359912109839650"
        assert rec0["imsi"] == "404819000158900"
        assert isinstance(rec0["timestamp"], datetime)
        assert rec0["timestamp"].year == 2026
        assert rec0["timestamp"].month == 6
        assert rec0["timestamp"].day == 17

        rec1 = records[1]
        assert rec1["call_type"] == "OUT"
        assert rec1["duration"] == 760
        assert rec1["latitude"] == pytest.approx(22.39711)
        assert rec1["longitude"] == pytest.approx(88.43938)
        assert rec1["last_latitude"] == pytest.approx(22.39711)
        assert rec1["last_longitude"] == pytest.approx(88.43938)


class TestCDRImportService:
    def test_detect_operator(self):
        service = CDRImportService()
        assert service.detect_operator(SAMPLE_AIRTEL_CONTENT) == "airtel"
        assert service.detect_operator(SAMPLE_BSNL_CONTENT) == "bsnl"
        assert service.detect_operator("random content") == "unknown"

    def test_process_upload_airtel(self, db_session):
        service = CDRImportService()
        res = service.process_upload(
            file_name="test_airtel.csv",
            file_bytes=SAMPLE_AIRTEL_CONTENT.encode("utf-8"),
            db=db_session,
        )
        assert res["summary"]["status"] == "completed"
        assert res["summary"]["parsed_records"] == 2
        assert res["summary"]["failed_records"] == 0

        job_id = res["job"].id
        job = db_session.query(ImportJob).filter(ImportJob.id == job_id).first()
        assert job is not None
        assert job.filename == "test_airtel.csv"
        assert job.operator == "airtel"
        assert job.parsed_records == 2

        db_records = (
            db_session.query(CDRRecord)
            .filter(CDRRecord.import_job_id == job_id)
            .all()
        )
        assert len(db_records) == 2
        assert isinstance(db_records[0].latitude, float)
        assert isinstance(db_records[0].longitude, float)

    def test_process_upload_bsnl(self, db_session):
        service = CDRImportService()
        res = service.process_upload(
            file_name="test_bsnl.csv",
            file_bytes=SAMPLE_BSNL_CONTENT.encode("utf-8"),
            db=db_session,
        )
        assert res["summary"]["status"] == "completed"
        assert res["summary"]["parsed_records"] == 2

        job_id = res["job"].id
        db_records = (
            db_session.query(CDRRecord)
            .filter(CDRRecord.import_job_id == job_id)
            .all()
        )
        assert len(db_records) == 2
        assert db_records[0].latitude == pytest.approx(22.39711)
        assert db_records[0].longitude == pytest.approx(88.43938)
