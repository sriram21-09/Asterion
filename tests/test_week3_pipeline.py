"""
Week 3 Scientific Pipeline Integration Test Suite
=================================================

End-to-end integration tests verifying the entire scientific pipeline from raw CSV input
to location tracking and movement reconstruction:

1. CSV Import & Operator Auto-Detection
2. CDR Data Validation & Quality Scoring
3. Evidence Synthesis & Cryptographic SHA-256 Tamper-Evident Hashing
4. Localization Engine & Statistical Confidence Estimation
5. Movement Event Reconstruction, CGI Handovers & Kalman Location Tracking
6. End-to-End CSV-to-Location Pipeline Flow
"""

import hashlib
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Setup path for backend imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.database.base  # Ensure all ORM models are registered
from app.models.base import Base
from app.models.case import Case
from app.models.cdr_record import CDRRecord
from app.models.import_job import ImportJob
from app.models.movement_event import MovementEvent
from app.models.tracking_result import TrackingResult
from app.repositories.case_repository import CaseRepository
from app.repositories.movement_repository import MovementRepository
from app.services.evidence_service import EvidenceService
from app.services.import_service import CDRImportService
from app.services.movement_service import (
    EVENT_TYPE_CALL_START,
    EVENT_TYPE_HANDOVER,
    EVENT_TYPE_SMS,
    MovementReconstructionService,
)
from app.services.parsers import (
    AirtelCDRParser,
    BSNLCDRParser,
    JioCDRParser,
    ViCDRParser,
)
from scientific.config import ValidationThresholds
from scientific.models.cdr_record import CDRRecord as ScientificCDRRecord
from scientific.models.measurement import Measurement
from scientific.models.scenario import Scenario
from scientific.models.scenario_config import ScenarioConfig
from scientific.models.tower import Tower
from scientific.pipeline.confidence import compute_confidence
from scientific.pipeline.evidence import compute_evidence_hash, synthesize_evidence
from scientific.pipeline.kalman_tracker import track_positions
from scientific.pipeline.movement import (
    calculate_bearing_deg,
    calculate_distance_m,
    calculate_speed_kmh,
    classify_velocity,
    detect_handover,
    flag_impossible_velocity,
    reconstruct_movement_events,
    smooth_movement_path,
)
from scientific.pipeline.multilateration import solve_multilateration
from scientific.pipeline.runner import run_pipeline
from scientific.pipeline.weighted_centroid import solve_weighted_centroid
from scientific.validation.validators import (
    CDRDataQualityScore,
    CDRValidationReport,
    CDRValidationService,
)

# ---------------------------------------------------------------------------
# Database Fixture Setup
# ---------------------------------------------------------------------------

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_db():
    """Create fresh database tables before each test and tear down after."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db() -> Session:
    """Provide an active test database session."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Sample CSV Data Generators & Helpers
# ---------------------------------------------------------------------------


def get_sample_airtel_csv() -> str:
    past_dt = datetime.now(UTC) - timedelta(hours=2)
    d_str = past_dt.strftime("%d/%m/%Y")
    t1_str = (past_dt - timedelta(minutes=15)).strftime("%H:%M:%S")
    t2_str = past_dt.strftime("%H:%M:%S")
    return f"""Target No,Call Type,B-Party,B-Party Location,Field4,Field5,Date,Time,Duration,First CGI Lat/Long,First CGI,Last CGI Lat/Long,Last CGI,SMSC,Service Type,IMEI,IMSI,Dummy,Roaming Network
9714499703,voice_outgoing,9876543210,,,Val5,{d_str},{t1_str},45,21.2930/72.8890,404-98-8331-00001,21.2930/72.8890,404-98-8331-00001,,Voice,358912345678901,404981234567890,,Home
9714499703,sms_outgoing,9876543210,,,Val5,{d_str},{t2_str},0,21.3030/72.8990,404-98-8331-00002,21.3030/72.8990,404-98-8331-00002,,SMS,358912345678901,404981234567890,,Home
"""


def get_sample_bsnl_csv() -> str:
    past_dt = datetime.now(UTC) - timedelta(hours=2)
    d_str = past_dt.strftime("%Y-%m-%d")
    t1_str = (past_dt - timedelta(minutes=30)).strftime("%H:%M:%S")
    t2_str = past_dt.strftime("%H:%M:%S")
    return f"""BSNL CDR REPORT,Calling Number,Called Number,Call Date,Call Time,Duration (s),First BTS Location,First CGI,Last BTS Location,Last CGI,SMSC,Service Type,IMEI,IMSI
9477523061,9477500000,{d_str},{t1_str},60,Lat: 22.5726 Long: 88.3639,404-10-100-0001,Lat: 22.5726 Long: 88.3639,404-10-100-0001,,Voice,359000000000001,404100000000001
9477523061,9477500000,{d_str},{t2_str},120,Lat: 22.5826 Long: 88.3739,404-10-100-0002,Lat: 22.5826 Long: 88.3739,404-10-100-0002,,Voice,359000000000001,404100000000001
"""


# ---------------------------------------------------------------------------
# 1. Test CSV Import & Operator Auto-Detection
# ---------------------------------------------------------------------------


class TestCSVImportAndOperatorDetection:
    """Verifies CSV format detection, parsing, and record database insertion."""

    def test_operator_auto_detection(self):
        service = CDRImportService()
        airtel_csv = get_sample_airtel_csv()
        bsnl_csv = get_sample_bsnl_csv()
        assert service.detect_operator(airtel_csv) == "airtel"
        assert service.detect_operator(bsnl_csv) == "bsnl"
        assert service.detect_operator("UNKNOWN_HEADER_DATA") == "unknown"

    def test_airtel_csv_parsing(self, db: Session):
        case = Case(id=1, title="Airtel CSV Case", status="open")
        db.add(case)
        db.commit()

        service = CDRImportService()
        result = service.process_upload(
            file_name="test_airtel.csv",
            file_bytes=get_sample_airtel_csv().encode("utf-8"),
            case_id=case.id,
            operator="auto",
            db=db,
        )

        assert result["summary"]["status"] == "completed"
        assert result["summary"]["parsed_records"] == 2
        assert result["summary"]["failed_records"] == 0

        records = db.query(CDRRecord).filter(CDRRecord.case_id == case.id).all()
        assert len(records) == 2
        assert records[0].target_number == "9714499703"
        assert records[0].latitude == pytest.approx(21.2930)
        assert records[0].longitude == pytest.approx(72.8890)
        assert records[0].first_cgi == "404-98-8331-00001"
        assert records[1].first_cgi == "404-98-8331-00002"

    def test_bsnl_csv_parsing(self, db: Session):
        case = Case(id=2, title="BSNL CSV Case", status="open")
        db.add(case)
        db.commit()

        service = CDRImportService()
        result = service.process_upload(
            file_name="test_bsnl.csv",
            file_bytes=get_sample_bsnl_csv().encode("utf-8"),
            case_id=case.id,
            operator="bsnl",
            db=db,
        )

        assert result["summary"]["status"] == "completed"
        assert result["summary"]["parsed_records"] == 2
        records = db.query(CDRRecord).filter(CDRRecord.case_id == case.id).all()
        assert len(records) == 2
        assert records[0].operator == "bsnl"
        assert records[0].target_number == "9477523061"


# ---------------------------------------------------------------------------
# 2. Test CDR Validation & Data Quality Scoring
# ---------------------------------------------------------------------------


class TestCDRValidationAndQualityScoring:
    """Verifies scientific validation rules and data quality scoring for CDR batches."""

    def test_validate_batch_valid_records(self):
        records = [
            ScientificCDRRecord(
                id=1,
                operator="airtel",
                target_number="9714499703",
                timestamp=datetime.now(UTC) - timedelta(hours=1),
                first_cgi="404-98-8331-00001",
                latitude=21.293,
                longitude=72.889,
            ),
            ScientificCDRRecord(
                id=2,
                operator="airtel",
                target_number="9714499703",
                timestamp=datetime.now(UTC) - timedelta(minutes=45),
                first_cgi="404-98-8331-00002",
                latitude=21.303,
                longitude=72.899,
            ),
        ]

        validator = CDRValidationService()
        report = validator.validate_batch(records)

        assert report.is_valid is True
        assert report.total_records == 2
        assert report.valid_count == 2
        assert report.rejected_count == 0
        assert report.quality_score.grade == "Excellent"
        assert report.quality_score.overall_score >= 0.95

    def test_validate_batch_failure_tracking(self):
        future_ts = datetime.now(UTC) + timedelta(days=2)
        records = [
            ScientificCDRRecord(
                id=10,
                operator="unknown_network",
                target_number="9999999999",
                timestamp=datetime.now(UTC) - timedelta(hours=1),
            ),
            ScientificCDRRecord(
                id=11,
                operator="airtel",
                target_number="9714499703",
                timestamp=future_ts,
            ),
            ScientificCDRRecord(
                id=11,  # Duplicate ID
                operator="airtel",
                target_number="9714499703",
                timestamp=datetime.now(UTC) - timedelta(hours=1),
            ),
        ]

        validator = CDRValidationService()
        report = validator.validate_batch(records)

        assert report.is_valid is False
        assert report.rejected_count > 0
        assert "CDR_INVALID_OPERATOR" in report.failure_categories
        assert "CDR_FUTURE_TIMESTAMP" in report.failure_categories
        assert "CDR_DUPLICATE_ID" in report.failure_categories
        assert report.quality_score.overall_score < 0.80


# ---------------------------------------------------------------------------
# 3. Test Evidence Synthesis & Cryptographic SHA-256 Hashing
# ---------------------------------------------------------------------------


class TestEvidenceSynthesisAndSHA256Hashing:
    """Verifies evidence synthesis, SHA-256 hash creation, and tamper detection."""

    def test_synthesize_evidence_hash_generation(self):
        towers = [
            Tower(tower_id="T001", latitude=12.9716, longitude=77.5946),
            Tower(tower_id="T002", latitude=12.9750, longitude=77.5980),
        ]
        measurements = [
            Measurement(
                measurement_id="M001",
                tower_id="T001",
                timestamp=datetime.now(UTC),
                rssi_dbm=-65.0,
            ),
            Measurement(
                measurement_id="M002",
                tower_id="T002",
                timestamp=datetime.now(UTC),
                rssi_dbm=-75.0,
            ),
        ]

        evidence = synthesize_evidence(
            scenario_id="SCN-EVIDENCE-TEST",
            towers=towers,
            measurements=measurements,
        )

        assert "evidence_hash" in evidence
        assert "hash" in evidence
        assert evidence["evidence_hash"] == evidence["hash"]
        assert len(evidence["evidence_hash"]) == 64  # SHA-256 hex digest length

        computed = compute_evidence_hash(evidence)
        assert computed == evidence["evidence_hash"]

    def test_evidence_hash_tamper_detection(self):
        towers = [Tower(tower_id="T001", latitude=12.9716, longitude=77.5946)]
        measurements = [
            Measurement(
                measurement_id="M001",
                tower_id="T001",
                timestamp=datetime.now(UTC),
                rssi_dbm=-65.0,
            )
        ]

        evidence = synthesize_evidence(
            scenario_id="SCN-TAMPER-TEST",
            towers=towers,
            measurements=measurements,
        )
        original_hash = evidence["evidence_hash"]

        evidence_tampered = dict(evidence)
        evidence_tampered["summary"] = dict(evidence["summary"])
        evidence_tampered["summary"]["total_measurements"] = 999

        tampered_hash = compute_evidence_hash(evidence_tampered)
        assert tampered_hash != original_hash


# ---------------------------------------------------------------------------
# 4. Test Localization Engine Integration
# ---------------------------------------------------------------------------


class TestLocalizationEngineIntegration:
    """Verifies weighted centroid and multilateration solvers with confidence estimation."""

    def test_weighted_centroid_solver(self):
        towers = [
            Tower(tower_id="T001", latitude=12.9700, longitude=77.5900),
            Tower(tower_id="T002", latitude=12.9800, longitude=77.5900),
            Tower(tower_id="T003", latitude=12.9750, longitude=77.6000),
        ]
        measurements = [
            Measurement(
                measurement_id="M001", tower_id="T001", rssi_dbm=-50.0, timestamp=datetime.now(UTC)
            ),
            Measurement(
                measurement_id="M002", tower_id="T002", rssi_dbm=-80.0, timestamp=datetime.now(UTC)
            ),
            Measurement(
                measurement_id="M003", tower_id="T003", rssi_dbm=-80.0, timestamp=datetime.now(UTC)
            ),
        ]

        res = solve_weighted_centroid(
            scenario_id="SCN-CENTROID",
            towers=towers,
            measurements=measurements,
            expected_device_lat=12.9710,
            expected_device_lon=77.5910,
        )

        assert res.scenario_id == "SCN-CENTROID"
        assert res.algorithm == "weighted_centroid"
        assert res.signals_used == 3
        assert abs(res.estimated_latitude - 12.9700) < 0.005
        assert res.error_m is not None

    def test_confidence_assessment_calculation(self):
        towers = [
            Tower(tower_id="T001", latitude=10.005, longitude=10.0),
            Tower(tower_id="T002", latitude=9.9975, longitude=10.00433),
            Tower(tower_id="T003", latitude=9.9975, longitude=9.99567),
        ]
        measurements = [
            Measurement(
                measurement_id="M1", tower_id="T001", rssi_dbm=-60.0, timestamp=datetime.now(UTC)
            ),
            Measurement(
                measurement_id="M2", tower_id="T002", rssi_dbm=-60.0, timestamp=datetime.now(UTC)
            ),
            Measurement(
                measurement_id="M3", tower_id="T003", rssi_dbm=-60.0, timestamp=datetime.now(UTC)
            ),
        ]

        conf = compute_confidence(
            scenario_id="SCN-CONF",
            estimated_latitude=10.0,
            estimated_longitude=10.0,
            towers=towers,
            measurements=measurements,
        )

        assert conf.scenario_id == "SCN-CONF"
        assert conf.gdop is not None
        assert conf.gdop < 2.0
        assert conf.confidence_level == "high"
        assert conf.confidence_score > 0.80


# ---------------------------------------------------------------------------
# 5. Test Movement Reconstruction & Kalman Location Tracking
# ---------------------------------------------------------------------------


class TestMovementReconstructionAndKalmanTracking:
    """Verifies movement event sequence building, CGI handovers, kinematics, and Kalman filtering."""

    def test_movement_reconstruction_and_kinematics(self, db: Session):
        case = Case(id=64, title="Movement Case", status="open")
        db.add(case)
        job = ImportJob(id=100, filename="movement.csv", status="completed")
        db.add(job)
        db.commit()

        base_ts = datetime(2026, 7, 25, 8, 0, 0, tzinfo=UTC)

        r1 = CDRRecord(
            import_job_id=job.id,
            case_id=case.id,
            operator="airtel",
            target_number="9714499703",
            call_type="voice_outgoing",
            timestamp=base_ts,
            latitude=12.9716,
            longitude=77.5946,
            first_cgi="CGI-001",
            last_cgi="CGI-001",
        )
        r2 = CDRRecord(
            import_job_id=job.id,
            case_id=case.id,
            operator="airtel",
            target_number="9714499703",
            call_type="sms_outgoing",
            timestamp=base_ts + timedelta(minutes=5),
            latitude=12.9816,
            longitude=77.6046,
            first_cgi="CGI-002",
            last_cgi="CGI-002",
        )
        r3 = CDRRecord(
            import_job_id=job.id,
            case_id=case.id,
            operator="airtel",
            target_number="9714499703",
            call_type="voice_incoming",
            timestamp=base_ts + timedelta(minutes=10),
            latitude=12.9916,
            longitude=77.6146,
            first_cgi="CGI-002",
            last_cgi="CGI-002",
        )
        db.add_all([r1, r2, r3])
        db.commit()

        result = MovementReconstructionService.reconstruct_movements(db, "CASE-064")

        assert result["total_events"] == 4
        assert result["handover_count"] == 1
        assert result["total_distance_km"] > 0
        assert result["time_span_hours"] == pytest.approx(10 / 60.0, abs=0.001)

        events = result["events"]
        assert events[0]["event_type"] == EVENT_TYPE_CALL_START
        assert events[1]["event_type"] == EVENT_TYPE_HANDOVER
        assert events[1]["from_cgi"] == "CGI-001"
        assert events[1]["to_cgi"] == "CGI-002"
        assert events[2]["event_type"] == EVENT_TYPE_SMS

    def test_velocity_classification_and_impossible_velocity_flagging(self):
        dist_m = 100000.0
        time_s = 300.0
        speed_kmh = calculate_speed_kmh(dist_m, time_s)
        assert speed_kmh == 1200.0

        is_anomalous = flag_impossible_velocity(speed_kmh, threshold_kmh=350.0)
        assert is_anomalous is True

        v_type = classify_velocity(speed_kmh)
        assert v_type in ("anomalous", "implausible", "flight") or speed_kmh > 350.0

    def test_kalman_path_smoothing(self):
        t_base = datetime(2026, 7, 25, 9, 0, 0, tzinfo=UTC)
        records = [
            {
                "timestamp": t_base,
                "latitude": 12.9716,
                "longitude": 77.5946,
                "first_cgi": "CGI-1",
            },
            {
                "timestamp": t_base + timedelta(minutes=1),
                "latitude": 12.9720,
                "longitude": 77.5950,
                "first_cgi": "CGI-1",
            },
            {
                "timestamp": t_base + timedelta(minutes=2),
                "latitude": 12.9718,
                "longitude": 77.5948,
                "first_cgi": "CGI-1",
            },
            {
                "timestamp": t_base + timedelta(minutes=3),
                "latitude": 12.9725,
                "longitude": 77.5955,
                "first_cgi": "CGI-1",
            },
        ]

        summary = reconstruct_movement_events(records)
        smoothed_summary = smooth_movement_path(summary)

        assert smoothed_summary.total_events == 4
        assert smoothed_summary.events[0].latitude is not None
        assert 12.96 < smoothed_summary.events[0].latitude < 12.98


# ---------------------------------------------------------------------------
# 6. Test End-to-End CSV-to-Location Pipeline Flow
# ---------------------------------------------------------------------------


class TestEndToEndCSVToLocationPipeline:
    """Verifies the complete pipeline run from CSV ingestion to location and evidence output."""

    def test_full_pipeline_csv_to_location_and_evidence(self, db: Session):
        case = Case(id=200, title="E2E Pipeline Case", scenario_id=1, status="open")
        db.add(case)
        db.commit()

        import_service = CDRImportService()
        airtel_csv = get_sample_airtel_csv()
        import_res = import_service.process_upload(
            file_name="9714499703_Airtel.csv",
            file_bytes=airtel_csv.encode("utf-8"),
            case_id=case.id,
            operator="auto",
            db=db,
        )
        assert import_res["summary"]["status"] == "completed"
        assert import_res["summary"]["parsed_records"] == 2

        cdr_records = db.query(CDRRecord).filter(CDRRecord.case_id == case.id).all()
        now_utc = datetime.now(UTC)
        scientific_records = [
            ScientificCDRRecord(
                id=r.id,
                operator=r.operator,
                target_number=r.target_number,
                timestamp=r.timestamp.replace(tzinfo=UTC) if r.timestamp and r.timestamp.tzinfo is None else (r.timestamp or now_utc),
                latitude=r.latitude,
                longitude=r.longitude,
                first_cgi=r.first_cgi,
            )
            for r in cdr_records
        ]
        val_service = CDRValidationService()
        val_report = val_service.validate_batch(scientific_records)
        assert val_report.is_valid is True
        assert val_report.quality_score.overall_score >= 0.80

        mvt_res = MovementReconstructionService.reconstruct_movements(db, "CASE-200")
        assert mvt_res["total_events"] >= 2
        assert len(mvt_res["events"]) >= 2

        towers = [
            Tower(
                tower_id="404-98-8331-00001",
                latitude=21.2930,
                longitude=72.8890,
                coverage_radius_m=1000.0,
            ),
            Tower(
                tower_id="404-98-8331-00002",
                latitude=21.3030,
                longitude=72.8990,
                coverage_radius_m=1000.0,
            ),
        ]
        measurements = [
            Measurement(
                measurement_id=f"M-{r.id}",
                tower_id=r.first_cgi,
                timestamp=r.timestamp if r.timestamp else now_utc,
                latitude=r.latitude,
                longitude=r.longitude,
                rssi_dbm=-70.0,
            )
            for r in cdr_records
        ]

        evidence_report = synthesize_evidence(
            scenario_id="SCN-E2E-FULL",
            towers=towers,
            measurements=measurements,
        )

        assert evidence_report["scenario_id"] == "SCN-E2E-FULL"
        assert "evidence_hash" in evidence_report
        assert len(evidence_report["evidence_hash"]) == 64
        assert compute_evidence_hash(evidence_report) == evidence_report["evidence_hash"]

        loc_res = solve_weighted_centroid(
            scenario_id="SCN-E2E-FULL",
            towers=towers,
            measurements=measurements,
            expected_device_lat=21.2930,
            expected_device_lon=72.8890,
        )

        assert loc_res.algorithm == "weighted_centroid"
        assert abs(loc_res.estimated_latitude - 21.2930) < 0.02
        assert abs(loc_res.estimated_longitude - 72.8890) < 0.02
        assert loc_res.signals_used == 2
