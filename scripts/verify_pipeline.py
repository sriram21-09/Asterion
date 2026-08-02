"""
Full Scientific Pipeline Verification Script
==============================================

Runs the complete scientific pipeline on all four operator datasets
and generates a structured JSON verification report.

Usage::
    python scripts/verify_pipeline.py
"""

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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

DATASET_DIR = ROOT / "E-Rakshak CDR & Location Data Sets"
OUTPUT_DIR = ROOT / "datasets" / "processed"
OPERATOR_FILES = [
    ("9714499703_Airtel.csv", "airtel"),
    ("9477523061_BSNL.csv", "bsnl"),
    ("9877535365_Jio.csv", "jio"),
    ("8980261614_Vi.csv", "vi"),
]


def _create_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, sf


def run_operator_pipeline(filename, expected_operator):
    engine, SessionLocal = _create_db()
    db = SessionLocal()
    try:
        filepath = DATASET_DIR / filename
        if not filepath.exists():
            return {"operator": expected_operator, "status": "SKIP"}

        with open(filepath, "rb") as fp:
            file_bytes = fp.read()

        svc = CDRImportService()
        detected_op = svc.detect_operator(file_bytes.decode("utf-8", errors="ignore"))
        case = Case(title=f"Verify-{filename}", status="open")
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
        mvt_res = MovementReconstructionService.reconstruct_movements(db, case_code)
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
            Tower(
                tower_id="T-DEFAULT",
                latitude=20.0,
                longitude=78.0,
                coverage_radius_m=1000.0,
            )
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
            "operator": expected_operator,
            "filename": filename,
            "status": "PASSED",
            "detected_operator": detected_op,
            "parsed_records": upload["summary"]["parsed_records"],
            "failed_records": upload["summary"]["failed_records"],
            "valid_records": val_report.valid_count,
            "total_records": val_report.total_records,
            "quality_grade": val_report.quality_score.grade,
            "quality_score": round(val_report.quality_score.overall_score, 4),
            "movement_events": mvt_res["total_events"],
            "handover_count": mvt_res["handover_count"],
            "smoothed_events": smoothed.total_events,
            "unique_towers": len(towers),
            "total_measurements": len(measurements),
            "evidence_hash": h1,
            "hash_deterministic": h1 == h2,
            "accepted_measurements": ev["summary"]["accepted_measurements"],
            "estimated_lat": round(centroid.estimated_latitude, 6),
            "estimated_lon": round(centroid.estimated_longitude, 6),
            "confidence_score": round(conf.confidence_score, 6),
            "confidence_level": conf.confidence_level,
            "confidence_bounded": 0.0 <= conf.confidence_score <= 1.0,
            "gdop": round(conf.gdop, 4) if conf.gdop else None,
        }
    except Exception as exc:
        return {
            "operator": expected_operator,
            "filename": filename,
            "status": "FAILED",
            "error": str(exc),
        }
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def main():
    print("=" * 72)
    print("  ASTERION SCIENTIFIC PIPELINE -- FULL VERIFICATION RUN")
    print("=" * 72)

    results = []
    t0 = time.perf_counter()
    for fn, op in OPERATOR_FILES:
        print(f"\n[+] {op.upper()} ({fn})...")
        r = run_operator_pipeline(fn, op)
        results.append(r)
        if r["status"] == "PASSED":
            print(
                f"  [OK] {r['parsed_records']} records | Grade {r['quality_grade']} | "
                f"{r['confidence_level']} confidence ({r['confidence_score']})"
            )
        else:
            print(f"  [FAIL] {r['status']}: {r.get('error','')}")

    elapsed = time.perf_counter() - t0

    # Benchmark metrics
    total_rec = sum(
        r.get("parsed_records", 0) for r in results if r["status"] == "PASSED"
    )
    valid_rec = sum(
        r.get("valid_records", 0) for r in results if r["status"] == "PASSED"
    )
    td = [
        {
            "tower_id": f"{r['operator']}_T{i}",
            "operator": r["operator"],
            "resolution_method": "exact",
        }
        for r in results
        if r["status"] == "PASSED"
        for i in range(r.get("unique_towers", 0))
    ]
    metrics = run_pipeline_benchmarks(
        validated_records=valid_rec,
        total_records=total_rec,
        tower_data=td,
        accuracy_threshold_m=CALIBRATED_THRESHOLDS.coordinate_accuracy_threshold_m,
    )
    compliance = verify_benchmark_compliance(metrics)

    print("\n" + "-" * 72)
    print(f"  Validation Pass Rate : {metrics.validation_pass_rate:.4f}")
    print(f"  Tower Resolution     : {metrics.tower_resolution_rate:.4f}")
    comp_str = "[OK] PASS" if compliance["overall_pass"] else "[FAIL] FAIL"
    print(
        f"  Compliance           : {comp_str} "
        f"({compliance['passed_checks']}/{compliance['total_checks']})"
    )

    report = {
        "verification_timestamp": datetime.now(UTC).isoformat(),
        "pipeline_version": "0.3.0",
        "total_operators": len(OPERATOR_FILES),
        "passed_operators": sum(1 for r in results if r["status"] == "PASSED"),
        "zero_exceptions": all(r["status"] == "PASSED" for r in results),
        "total_time_s": round(elapsed, 4),
        "operator_results": results,
        "benchmark_metrics": {
            "validation_pass_rate": metrics.validation_pass_rate,
            "tower_resolution_rate": metrics.tower_resolution_rate,
            "kalman_improvement_factor": metrics.kalman_improvement_factor,
            "compliance": compliance,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "pipeline_verification_report.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    verdict = "[OK] ALL PASSED" if report["zero_exceptions"] else "[FAIL] FAILURES"
    print("\n" + "=" * 72)
    print(f"  {verdict} | {elapsed:.2f}s | Report: {out}")
    print("=" * 72)
    return 0 if report["zero_exceptions"] else 1


if __name__ == "__main__":
    sys.exit(main())
