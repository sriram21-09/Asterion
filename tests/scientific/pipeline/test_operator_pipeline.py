"""
Operator Pipeline Verification Test Suite
==========================================

Verifies zero exceptions during scientific localization pipeline runs on all real
operator datasets (Airtel, BSNL, Jio, Vi).

Covers:
1. Raw CSV operator auto-detection & ingestion parsing.
2. Scientific CDR validation & quality scoring.
3. Movement event sequence reconstruction & CGI handover classification.
4. Kalman movement path smoothing.
5. Evidence synthesis & cryptographic SHA-256 tamper-evident hashing.
6. Multi-factor quality-weighted centroid positioning & statistical confidence estimation.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Setup path for backend imports
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.base import Base
from app.models.case import Case
from app.models.cdr_record import CDRRecord
from app.services.import_service import CDRImportService
from app.services.movement_service import MovementReconstructionService
from scientific.models.cdr_record import CDRRecord as ScientificCDRRecord
from scientific.models.measurement import Measurement
from scientific.models.tower import Tower
from scientific.pipeline.confidence import compute_confidence
from scientific.pipeline.evidence import compute_evidence_hash, synthesize_evidence
from scientific.pipeline.movement import reconstruct_movement_events, smooth_movement_path
from scientific.pipeline.weighted_centroid import solve_weighted_centroid
from scientific.validation.validators import CDRValidationService

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


DATASET_DIR = ROOT / "E-Rakshak CDR & Location Data Sets"


def _run_full_operator_pipeline(db: Session, filename: str, expected_operator: str) -> dict:
    """Helper to run the end-to-end scientific pipeline on a specific operator file."""
    filepath = DATASET_DIR / filename
    assert filepath.exists(), f"Dataset file {filename} not found at {filepath}"

    with open(filepath, "rb") as fp:
        file_bytes = fp.read()

    # 1. Ingestion & Auto-detection
    service = CDRImportService()
    detected_op = service.detect_operator(file_bytes.decode("utf-8", errors="ignore"))
    assert (
        detected_op == expected_operator
    ), f"Expected operator '{expected_operator}', but detected '{detected_op}'"

    case = Case(title=f"Test Case for {filename}", status="open")
    db.add(case)
    db.commit()
    db.refresh(case)

    upload_result = service.process_upload(
        file_name=filename,
        file_bytes=file_bytes,
        case_id=case.id,
        operator="auto",
        db=db,
    )
    assert upload_result["summary"]["status"] == "completed"
    assert upload_result["summary"]["parsed_records"] > 0
    assert upload_result["summary"]["failed_records"] == 0

    # 2. CDR Validation & Quality Scoring
    db_records = db.query(CDRRecord).filter(CDRRecord.case_id == case.id).all()
    sci_records = [
        ScientificCDRRecord(
            id=r.id,
            operator=r.operator,
            target_number=r.target_number or "unknown",
            timestamp=r.timestamp.replace(tzinfo=UTC)
            if r.timestamp and r.timestamp.tzinfo is None
            else (r.timestamp or datetime.now(UTC)),
            latitude=r.latitude,
            longitude=r.longitude,
            first_cgi=r.first_cgi,
        )
        for r in db_records
    ]
    val_service = CDRValidationService()
    val_report = val_service.validate_batch(sci_records)
    assert val_report.total_records == len(db_records)
    assert val_report.quality_score.overall_score >= 0.0

    # 3. Movement Reconstruction & Kalman Path Smoothing
    case_code = f"CASE-{case.id:03d}"
    mvt_res = MovementReconstructionService.reconstruct_movements(db, case_code)
    assert mvt_res["total_events"] >= len(db_records)
    assert mvt_res["handover_count"] >= 0

    dict_records = [
        {
            "timestamp": r.timestamp,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "first_cgi": r.first_cgi,
        }
        for r in db_records
    ]
    mvt_summary = reconstruct_movement_events(dict_records)
    smoothed_summary = smooth_movement_path(mvt_summary)
    assert smoothed_summary.total_events == len(dict_records)

    # 4. Tower Extraction & Measurement Synthesis
    towers_dict = {}
    measurements = []
    now_utc = datetime.now(UTC)
    for r in db_records:
        if r.first_cgi and r.first_cgi not in towers_dict:
            lat = r.latitude if r.latitude is not None else 20.0
            lon = r.longitude if r.longitude is not None else 78.0
            towers_dict[r.first_cgi] = Tower(
                tower_id=r.first_cgi,
                latitude=lat,
                longitude=lon,
                coverage_radius_m=1000.0,
            )
        meas_ts = r.timestamp if r.timestamp else now_utc
        if meas_ts.tzinfo is None:
            meas_ts = meas_ts.replace(tzinfo=UTC)
        measurements.append(
            Measurement(
                measurement_id=f"M-{r.id}",
                tower_id=r.first_cgi or "T-UNKNOWN",
                timestamp=meas_ts,
                latitude=r.latitude,
                longitude=r.longitude,
                rssi_dbm=-70.0,
            )
        )
    towers = list(towers_dict.values())
    if not towers:
        towers = [Tower(tower_id="T-DEFAULT", latitude=20.0, longitude=78.0, coverage_radius_m=1000.0)]

    # 5. Evidence Synthesis & Cryptographic SHA-256 Hashing
    ev_report = synthesize_evidence(
        scenario_id=f"SCN-{case.id}",
        towers=towers,
        measurements=measurements[:100],
    )
    hash_val = compute_evidence_hash(ev_report)
    assert len(hash_val) == 64

    # 6. Weighted Centroid Positioning & Confidence
    centroid_res = solve_weighted_centroid(
        scenario_id=f"SCN-{case.id}",
        towers=towers,
        measurements=measurements[:100],
    )
    conf_res = compute_confidence(
        scenario_id=f"SCN-{case.id}",
        estimated_latitude=centroid_res.estimated_latitude,
        estimated_longitude=centroid_res.estimated_longitude,
        towers=towers,
        measurements=measurements[:100],
    )
    assert conf_res.confidence_level in ("high", "medium", "low")
    assert 0.0 <= conf_res.confidence_score <= 1.0

    return {
        "operator": expected_operator,
        "parsed_records": upload_result["summary"]["parsed_records"],
        "validation_grade": val_report.quality_score.grade,
        "total_events": mvt_res["total_events"],
        "evidence_hash": hash_val,
        "centroid": (centroid_res.estimated_latitude, centroid_res.estimated_longitude),
        "confidence_level": conf_res.confidence_level,
    }


class TestOperatorPipelineRuns:
    """Verifies that all 4 operator files (Airtel, BSNL, Jio, Vi) complete pipeline runs with zero exceptions."""

    def test_airtel_operator_pipeline(self, db: Session):
        res = _run_full_operator_pipeline(db, "9714499703_Airtel.csv", "airtel")
        assert res["parsed_records"] == 1570
        assert len(res["evidence_hash"]) == 64

    def test_bsnl_operator_pipeline(self, db: Session):
        res = _run_full_operator_pipeline(db, "9477523061_BSNL.csv", "bsnl")
        assert res["parsed_records"] == 29
        assert len(res["evidence_hash"]) == 64

    def test_jio_operator_pipeline(self, db: Session):
        res = _run_full_operator_pipeline(db, "9877535365_Jio.csv", "jio")
        assert res["parsed_records"] == 7101
        assert len(res["evidence_hash"]) == 64

    def test_vi_operator_pipeline(self, db: Session):
        res = _run_full_operator_pipeline(db, "8980261614_Vi.csv", "vi")
        assert res["parsed_records"] == 4134
        assert len(res["evidence_hash"]) == 64

    def test_all_operator_files_batch_run(self, db: Session):
        """Iterates over all CSV files in dataset directory and asserts zero exceptions."""
        csv_files = list(DATASET_DIR.glob("*.csv"))
        assert len(csv_files) == 4, f"Expected 4 operator CSV files, found {len(csv_files)}"

        for f in csv_files:
            if "Airtel" in f.name:
                op = "airtel"
            elif "BSNL" in f.name:
                op = "bsnl"
            elif "Jio" in f.name:
                op = "jio"
            elif "Vi" in f.name:
                op = "vi"
            else:
                op = "unknown"

            res = _run_full_operator_pipeline(db, f.name, op)
            assert res["parsed_records"] > 0
            assert len(res["evidence_hash"]) == 64
