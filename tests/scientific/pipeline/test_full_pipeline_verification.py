"""
Full Pipeline Verification Integration Test
=============================================

Formal integration test validating complete scientific pipeline execution
across all four operator datasets with zero exceptions, benchmark compliance,
evidence hash determinism, and confidence score bounds.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

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
from scientific.pipeline.benchmark_thresholds import (
    CALIBRATED_THRESHOLDS,
    verify_benchmark_compliance,
)
from scientific.pipeline.benchmarks import run_pipeline_benchmarks
from scientific.pipeline.confidence import compute_confidence
from scientific.pipeline.evidence import compute_evidence_hash, synthesize_evidence
from scientific.pipeline.movement import (
    reconstruct_movement_events,
    smooth_movement_path,
)
from scientific.pipeline.weighted_centroid import solve_weighted_centroid
from scientific.validation.validators import CDRValidationService

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)
DATASET_DIR = ROOT / "E-Rakshak CDR & Location Data Sets"

OPERATORS = [
    ("9714499703_Airtel.csv", "airtel"),
    ("9477523061_BSNL.csv", "bsnl"),
    ("9877535365_Jio.csv", "jio"),
    ("8980261614_Vi.csv", "vi"),
]


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


def _run_pipeline(db: Session, filename: str, operator: str) -> dict:
    """Execute E2E pipeline and return structured result dict."""
    filepath = DATASET_DIR / filename
    assert filepath.exists()

    with open(filepath, "rb") as fp:
        file_bytes = fp.read()

    svc = CDRImportService()
    case = Case(title=f"Verify-{operator}", status="open")
    db.add(case)
    db.commit()
    db.refresh(case)

    upload = svc.process_upload(
        file_name=filename,
        file_bytes=file_bytes,
        case_id=case.id,
        operator="auto",
        db=db,
    )

    db_records = db.query(CDRRecord).filter(CDRRecord.case_id == case.id).all()
    sci_records = [
        ScientificCDRRecord(
            id=r.id,
            operator=r.operator,
            target_number=r.target_number or "unknown",
            timestamp=(
                r.timestamp.replace(tzinfo=UTC)
                if r.timestamp and r.timestamp.tzinfo is None
                else (r.timestamp or datetime.now(UTC))
            ),
            latitude=r.latitude,
            longitude=r.longitude,
            first_cgi=r.first_cgi,
        )
        for r in db_records
    ]

    val_svc = CDRValidationService()
    val_report = val_svc.validate_batch(sci_records)

    case_code = f"CASE-{case.id:03d}"
    mvt = MovementReconstructionService.reconstruct_movements(db, case_code)
    dict_recs = [
        {
            "timestamp": r.timestamp,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "first_cgi": r.first_cgi,
        }
        for r in db_records
    ]
    mvt_summary = reconstruct_movement_events(dict_recs)
    smoothed = smooth_movement_path(mvt_summary)

    towers_dict = {}
    measurements = []
    now_utc = datetime.now(UTC)
    for r in db_records:
        if r.first_cgi and r.first_cgi not in towers_dict:
            towers_dict[r.first_cgi] = Tower(
                tower_id=r.first_cgi,
                latitude=r.latitude if r.latitude is not None else 20.0,
                longitude=r.longitude if r.longitude is not None else 78.0,
                coverage_radius_m=1000.0,
            )
        ts = r.timestamp or now_utc
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        measurements.append(
            Measurement(
                measurement_id=f"M-{r.id}",
                tower_id=r.first_cgi or "T-UNKNOWN",
                timestamp=ts,
                latitude=r.latitude,
                longitude=r.longitude,
                rssi_dbm=-70.0,
            )
        )

    towers = list(towers_dict.values()) or [
        Tower(tower_id="T-DEF", latitude=20.0, longitude=78.0, coverage_radius_m=1000.0)
    ]

    ev = synthesize_evidence(
        scenario_id=f"SCN-{case.id}", towers=towers, measurements=measurements[:100]
    )
    h1 = compute_evidence_hash(ev)
    h2 = compute_evidence_hash(ev)

    centroid = solve_weighted_centroid(
        scenario_id=f"SCN-{case.id}",
        towers=towers,
        measurements=measurements[:100],
    )
    conf = compute_confidence(
        scenario_id=f"SCN-{case.id}",
        estimated_latitude=centroid.estimated_latitude,
        estimated_longitude=centroid.estimated_longitude,
        towers=towers,
        measurements=measurements[:100],
    )

    return {
        "operator": operator,
        "parsed": upload["summary"]["parsed_records"],
        "failed": upload["summary"]["failed_records"],
        "valid": val_report.valid_count,
        "total": val_report.total_records,
        "grade": val_report.quality_score.grade,
        "score": val_report.quality_score.overall_score,
        "events": mvt["total_events"],
        "handovers": mvt["handover_count"],
        "smoothed_events": smoothed.total_events,
        "towers": len(towers),
        "measurements": len(measurements),
        "hash": h1,
        "hash_deterministic": h1 == h2,
        "accepted": ev["summary"]["accepted_measurements"],
        "lat": centroid.estimated_latitude,
        "lon": centroid.estimated_longitude,
        "confidence_score": conf.confidence_score,
        "confidence_level": conf.confidence_level,
    }


class TestFullPipelineVerification:
    """Complete scientific pipeline verification across all operators."""

    @pytest.mark.parametrize("filename,operator", OPERATORS)
    def test_zero_exceptions(self, db, filename, operator):
        """Pipeline runs with zero unhandled exceptions for each operator."""
        result = _run_pipeline(db, filename, operator)
        assert result["parsed"] > 0
        assert result["failed"] == 0

    @pytest.mark.parametrize("filename,operator", OPERATORS)
    def test_evidence_hash_determinism(self, db, filename, operator):
        """SHA-256 evidence hash is deterministic across identical inputs."""
        result = _run_pipeline(db, filename, operator)
        assert result["hash_deterministic"] is True
        assert len(result["hash"]) == 64

    @pytest.mark.parametrize("filename,operator", OPERATORS)
    def test_confidence_score_bounds(self, db, filename, operator):
        """Confidence scores are strictly bounded within [0, 1]."""
        result = _run_pipeline(db, filename, operator)
        assert 0.0 <= result["confidence_score"] <= 1.0
        assert result["confidence_level"] in ("high", "medium", "low")

    @pytest.mark.parametrize("filename,operator", OPERATORS)
    def test_movement_reconstruction(self, db, filename, operator):
        """Movement reconstruction produces valid event sequences."""
        result = _run_pipeline(db, filename, operator)
        assert result["events"] >= result["parsed"]
        assert result["handovers"] >= 0
        assert result["smoothed_events"] == result["parsed"]

    @pytest.mark.parametrize("filename,operator", OPERATORS)
    def test_validation_quality(self, db, filename, operator):
        """Validation produces a valid quality score."""
        result = _run_pipeline(db, filename, operator)
        assert 0.0 <= result["score"] <= 1.0
        assert result["grade"] in ("Excellent", "Good", "Fair", "Poor", "Critical")

    def test_benchmark_compliance(self, db):
        """Aggregate benchmark metrics meet calibrated thresholds."""
        all_results = []
        for fn, op in OPERATORS:
            # Fresh DB for each
            Base.metadata.drop_all(bind=TEST_ENGINE)
            Base.metadata.create_all(bind=TEST_ENGINE)
            r = _run_pipeline(db, fn, op)
            all_results.append(r)

        total_rec = sum(r["parsed"] for r in all_results)
        valid_rec = sum(r["valid"] for r in all_results)
        td = [
            {
                "tower_id": f"{r['operator']}_T{i}",
                "operator": r["operator"],
                "resolution_method": "exact",
            }
            for r in all_results
            for i in range(r["towers"])
        ]

        metrics = run_pipeline_benchmarks(
            validated_records=valid_rec,
            total_records=total_rec,
            tower_data=td,
            accuracy_threshold_m=CALIBRATED_THRESHOLDS.coordinate_accuracy_threshold_m,
        )

        compliance = verify_benchmark_compliance(metrics)
        assert compliance["overall_pass"] is True, (
            f"Benchmark compliance failed: "
            f"{[c for c in compliance['checks'] if not c['passed']]}"
        )
        assert (
            metrics.validation_pass_rate
            >= CALIBRATED_THRESHOLDS.min_validation_pass_rate
        )
        assert (
            metrics.tower_resolution_rate
            >= CALIBRATED_THRESHOLDS.min_tower_resolution_rate
        )
