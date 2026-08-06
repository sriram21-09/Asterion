from app.database.session import SessionLocal
from app.models.measurement import Measurement
from app.models.movement_event import MovementEvent
from app.models.cdr_record import CDRRecord
from app.models.tracking_result import TrackingResult
from app.models.localization_result import LocalizationResult
from app.models.confidence_result import ConfidenceResult

db = SessionLocal()

# 1. Delete all fake generated measurements, tracking, localization, and confidence results for case 1
db.query(TrackingResult).filter(TrackingResult.case_id == 1).delete()
db.query(LocalizationResult).filter(LocalizationResult.case_id == 1).delete()
db.query(ConfidenceResult).filter(ConfidenceResult.case_id == 1).delete()
db.query(Measurement).filter(Measurement.case_id == 1).delete()
db.query(MovementEvent).filter(MovementEvent.case_id == 1).delete()

# 2. Recreate measurements and movement events from CDRs
cdrs = db.query(CDRRecord).filter(CDRRecord.case_id == 1).all()

import datetime

now = datetime.datetime.utcnow()

measurements = []
movement_events = []
for i, cdr in enumerate(cdrs):
    ts = cdr.timestamp or now
    measurements.append(
        Measurement(
            case_id=1,
            scenario_id=None,
            measurement_code=f"IMP-1-{i}",
            timestamp=ts,
            rssi_dbm=None,
            latitude=cdr.latitude,
            longitude=cdr.longitude,
            uncertainty_m=None,
        )
    )
    movement_events.append(
        MovementEvent(
            case_id=1,
            timestamp=ts,
            latitude=cdr.latitude,
            longitude=cdr.longitude,
            event_type="movement",
            sequence_number=i,
            speed_kmh=None,
            confidence=None,
        )
    )

db.add_all(measurements)
db.add_all(movement_events)
db.commit()
print("Fixed DB for Case 1!")
