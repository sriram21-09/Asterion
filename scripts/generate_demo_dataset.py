"""
Demo Dataset Generator
=======================

Extracts representative CDR records from all four operator CSV files
and produces a curated demo dataset for platform demonstrations.

Usage::
    python scripts/generate_demo_dataset.py
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.import_service import CDRImportService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.case import Case
from app.models.cdr_record import CDRRecord

DATASET_DIR = ROOT / "E-Rakshak CDR & Location Data Sets"
OUTPUT_DIR = ROOT / "datasets" / "demo"

OPERATOR_FILES = [
    ("9714499703_Airtel.csv", "airtel", 25),
    ("9477523061_BSNL.csv", "bsnl", 29),  # all records
    ("9877535365_Jio.csv", "jio", 25),
    ("8980261614_Vi.csv", "vi", 25),
]

DEMO_COLUMNS = [
    "operator",
    "target_number",
    "b_party_number",
    "call_type",
    "timestamp",
    "duration",
    "latitude",
    "longitude",
    "first_cgi",
    "first_bts_location",
    "last_cgi",
    "imei",
]


def _sample_indices(total, n):
    """Return n evenly-spaced indices including first 5 and last 5."""
    if total <= n:
        return list(range(total))
    head = list(range(min(5, total)))
    tail = list(range(max(total - 5, 0), total))
    middle_count = n - len(head) - len(tail)
    if middle_count > 0:
        step = (total - 10) / (middle_count + 1)
        middle = [int(5 + step * (i + 1)) for i in range(middle_count)]
    else:
        middle = []
    indices = sorted(set(head + middle + tail))
    return indices[:n]


def extract_operator_records(filename, operator, sample_size):
    """Import an operator file and return sampled records as dicts."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        filepath = DATASET_DIR / filename
        with open(filepath, "rb") as fp:
            file_bytes = fp.read()

        svc = CDRImportService()
        case = Case(title=f"Demo-{operator}", status="open")
        db.add(case)
        db.commit()
        db.refresh(case)

        svc.process_upload(
            file_name=filename,
            file_bytes=file_bytes,
            case_id=case.id,
            operator="auto",
            db=db,
        )

        records = (
            db.query(CDRRecord)
            .filter(CDRRecord.case_id == case.id)
            .order_by(CDRRecord.timestamp)
            .all()
        )

        indices = _sample_indices(len(records), sample_size)
        sampled = [records[i] for i in indices if i < len(records)]

        rows = []
        for r in sampled:
            rows.append(
                {
                    "operator": r.operator or operator,
                    "target_number": r.target_number or "",
                    "b_party_number": r.b_party_number or "",
                    "call_type": r.call_type or "",
                    "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                    "duration": r.duration or 0,
                    "latitude": r.latitude if r.latitude is not None else "",
                    "longitude": r.longitude if r.longitude is not None else "",
                    "first_cgi": r.first_cgi or "",
                    "first_bts_location": r.first_bts_location or "",
                    "last_cgi": r.last_cgi or "",
                    "imei": r.imei or "",
                }
            )
        return rows
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def write_csv(rows, filepath):
    """Write a list of dicts to a CSV file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DEMO_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    print("=" * 60)
    print("  ASTERION DEMO DATASET GENERATOR")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = []

    for fn, op, n in OPERATOR_FILES:
        print(f"\n[+] Extracting {op.upper()} ({fn}, sample={n})...")
        rows = extract_operator_records(fn, op, n)
        all_rows.extend(rows)
        print(f"  [OK] {len(rows)} records extracted")

        # Per-operator CSV
        per_op_path = OUTPUT_DIR / f"demo_{op}.csv"
        write_csv(rows, per_op_path)
        print(f"  -> {per_op_path}")

    # Combined CSV
    combined_path = OUTPUT_DIR / "asterion_demo_dataset.csv"
    write_csv(all_rows, combined_path)
    print("\n" + "-" * 60)
    print(f"  Combined dataset: {combined_path}")
    print(f"  Total records   : {len(all_rows)}")

    operators = set(r["operator"] for r in all_rows)
    print(f"  Operators       : {', '.join(sorted(operators))}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
