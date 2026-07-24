import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

# Import all models to configure mapper correctly
from app.database.session import SessionLocal
from app.models.case import Case
from app.models.confidence_result import ConfidenceResult
from app.models.localization_result import LocalizationResult
from app.models.measurement import Measurement
from app.models.scenario import Scenario
from app.models.tracking_result import TrackingResult

db = SessionLocal()
try:
    # Clear existing if any
    db.query(ConfidenceResult).delete()
    db.query(TrackingResult).delete()
    db.query(LocalizationResult).delete()
    db.query(Measurement).delete()
    db.query(Case).delete()
    db.query(Scenario).delete()
    db.commit()

    s = Scenario(
        name="Urban 3-Tower Test",
        description="Standard multilateration scenario in Bangalore core.",
    )
    db.add(s)
    db.commit()
    db.refresh(s)

    c = Case(
        title="MG Road Missing Person Search",
        description="Tracking device signals near MG Road.",
        scenario_id=s.id,
    )
    db.add(c)
    db.commit()
    print("Database seeded successfully with case and scenario!")
finally:
    db.close()
