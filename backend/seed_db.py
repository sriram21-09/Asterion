import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.database.session import SessionLocal
from app.models.case import Case
from app.models.confidence_result import ConfidenceResult
from app.models.localization_result import LocalizationResult
from app.models.measurement import Measurement
from app.models.scenario import Scenario
from app.models.tracking_result import TrackingResult
from app.models.movement_event import MovementEvent

def seed():
    db = SessionLocal()
    try:
        # Clear existing data
        db.query(ConfidenceResult).delete()
        db.query(TrackingResult).delete()
        db.query(LocalizationResult).delete()
        db.query(Measurement).delete()
        db.query(MovementEvent).delete()
        db.query(Case).delete()
        db.query(Scenario).delete()
        db.commit()

        # Scenarios
        s_urban = Scenario(
            name="Urban 3-Tower Test",
            description="Standard multilateration scenario in Bangalore core.",
        )
        s_rural = Scenario(
            name="Rural Single-Tower Drop",
            description="High error radius test in outskirts.",
        )
        db.add_all([s_urban, s_rural])
        db.commit()
        db.refresh(s_urban)
        db.refresh(s_rural)

        base_time = datetime.now(timezone.utc)

        # ---------------------------------------------------------
        # Case 1: Active, High Confidence, Verified Evidence
        # ---------------------------------------------------------
        c1 = Case(
            title="MG Road Missing Person Search",
            description="Tracking device signals near MG Road.",
            scenario_id=s_urban.id,
            status="open"
        )
        db.add(c1)
        db.commit()
        db.refresh(c1)

        for i in range(10):
            t = base_time - timedelta(days=1, minutes=60 - i*2)
            # Measurements
            m = Measurement(
                case_id=c1.id, scenario_id=s_urban.id,
                measurement_code=f"M-T{i%3 + 1}-00{i}",
                timestamp=t, rssi_dbm=-70.0 - (i*0.5),
                latitude=12.971 + (i * 0.0001), longitude=77.594 + (i * 0.0001),
                uncertainty_m=10.0
            )
            db.add(m)
            
            # Localization
            lr = LocalizationResult(
                case_id=c1.id, scenario_id=s_urban.id,
                estimated_latitude=12.971 + (i * 0.0001),
                estimated_longitude=77.594 + (i * 0.0001),
                algorithm="nlls", error_m=5.0, signals_used=3
            )
            db.add(lr)
            db.flush()
            
            # Tracking
            tr = TrackingResult(
                case_id=c1.id, localization_result_id=lr.id,
                step_number=i,
                smoothed_latitude=12.971 + (i * 0.0001) + 0.00005,
                smoothed_longitude=77.594 + (i * 0.0001) + 0.00005,
                velocity_lat=0.1, velocity_lon=0.1,
                algorithm="kalman", timestamp=t
            )
            db.add(tr)

            # Movement Events (Timeline)
            me = MovementEvent(
                case_id=c1.id, timestamp=t,
                latitude=12.971 + (i * 0.0001), longitude=77.594 + (i * 0.0001),
                event_type="movement", sequence_number=i,
                speed_kmh=12.5, confidence=0.92
            )
            db.add(me)

        cr1 = ConfidenceResult(
            case_id=c1.id, confidence_score=92.5,
            confidence_level="HIGH", gdop=1.2, method="monte_carlo"
        )
        db.add(cr1)

        # ---------------------------------------------------------
        # Case 2: Koramangala Suspect Tracking (Archived / Poor Signal)
        # ---------------------------------------------------------
        c2 = Case(
            title="Koramangala Suspect Tracking",
            description="Erratic ping history, likely underground or heavily obstructed.",
            scenario_id=s_rural.id,
            status="archived"
        )
        db.add(c2)
        db.commit()
        db.refresh(c2)

        for i in range(4):
            t = base_time - timedelta(days=5, hours=i*3)
            m = Measurement(
                case_id=c2.id, scenario_id=s_rural.id,
                measurement_code=f"K-T1-00{i}",
                timestamp=t, rssi_dbm=-105.0 + i,
                latitude=12.935 + (i * 0.005), longitude=77.624 + (i * 0.005),
                uncertainty_m=500.0
            )
            db.add(m)

            me = MovementEvent(
                case_id=c2.id, timestamp=t,
                latitude=12.935 + (i * 0.005), longitude=77.624 + (i * 0.005),
                event_type="alert", sequence_number=i,
                speed_kmh=80.0, confidence=0.45
            )
            db.add(me)

        cr2 = ConfidenceResult(
            case_id=c2.id, confidence_score=45.0,
            confidence_level="LOW", gdop=8.5, method="nlls_variance"
        )
        db.add(cr2)

        # ---------------------------------------------------------
        # Case 3: Indiranagar VIP Escort (Pending / No Scenario)
        # ---------------------------------------------------------
        c3 = Case(
            title="Indiranagar VIP Escort",
            description="Real-time escort telemetry. Scenario mapping pending.",
            scenario_id=None,
            status="pending"
        )
        db.add(c3)
        db.commit()
        db.refresh(c3)

        for i in range(5):
            t = base_time - timedelta(minutes=i*5)
            m = Measurement(
                case_id=c3.id, scenario_id=None,
                measurement_code=f"VIP-T{i%2 + 1}-00{i}",
                timestamp=t, rssi_dbm=-60.0 - i,
                latitude=12.978 + (i * 0.002), longitude=77.640 + (i * 0.001),
                uncertainty_m=5.0
            )
            db.add(m)

            me = MovementEvent(
                case_id=c3.id, timestamp=t,
                latitude=12.978 + (i * 0.002), longitude=77.640 + (i * 0.001),
                event_type="handover", sequence_number=i,
                speed_kmh=45.0, confidence=0.88, from_cgi="CGI-01", to_cgi="CGI-02"
            )
            db.add(me)

        # ---------------------------------------------------------
        # Case 4: PhantomNet Data Ingestion (Review)
        # ---------------------------------------------------------
        c4 = Case(
            title="PhantomNet Data Ingestion",
            description="Newly imported data from phantomnet_analytics CSV file.",
            scenario_id=None,
            status="review"
        )
        db.add(c4)
        db.commit()
        db.refresh(c4)
        
        # Add 1 raw measurement to represent the import queue
        m_phantom = Measurement(
            case_id=c4.id, scenario_id=None,
            measurement_code="PN-RAW-001",
            timestamp=base_time, rssi_dbm=-85.0,
            latitude=12.971, longitude=77.594,
            uncertainty_m=100.0
        )
        db.add(m_phantom)

        # Add import event
        me_phantom = MovementEvent(
            case_id=c4.id, timestamp=base_time,
            latitude=None, longitude=None,
            event_type="import", sequence_number=0,
            speed_kmh=0.0, confidence=1.0
        )
        db.add(me_phantom)


        db.commit()
        print("Database seeded successfully with 4 diverse cases!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
