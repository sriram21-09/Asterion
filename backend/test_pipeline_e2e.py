import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import SessionLocal
from app.services.import_service import CDRImportService
from app.services.dashboard_service import DashboardService
from app.services.validation_service import ValidationService
from app.services.localization_service import LocalizationService
from app.services.tracking_service import TrackingService
from app.services.confidence_service import ConfidenceService
from app.services.evidence_service import EvidenceService

def test_pipeline():
    db = SessionLocal()

    # 1. Import Data
    print("--- 1. Importing Data ---")
    with open('C:/Users/srira/Project/Asterion/test_import.csv', 'rb') as f:
        res = CDRImportService().process_upload(
            'test_import.csv', 
            f.read(), 
            None, 
            'auto', 
            db
        )
    case_id = res['case_id']
    print(f"Import Summary: {res['summary']}")
    print(f"Created Case ID: {case_id}")

    # Get Case Code
    from app.models.case import Case
    case = db.query(Case).filter(Case.id == case_id).first()
    case_code = case.reference_number if case.reference_number else f"CASE-{case_id:03d}"
    print(f"Case Code: {case_code}")

    # 2. Validation
    print("\n--- 2. Validating ---")
    val_res = ValidationService.validate_measurements(case_code, db)
    print(f"Validation: valid={val_res['valid_count']}, rejected={val_res['rejected_count']}, warnings={val_res['warning_count']}")

    # 3. Localization
    print("\n--- 3. Localizing ---")
    loc_res = LocalizationService.run_localization(case_code, db)
    print(f"Localization: lat={loc_res['estimated_latitude']}, lon={loc_res['estimated_longitude']}, error_m={loc_res.get('error_distance_m')}")

    # 4. Tracking
    print("\n--- 4. Tracking ---")
    track_res = TrackingService.run_tracking(case_code, db)
    print(f"Tracking: steps={track_res['total_steps']}, distance_km={track_res['distance_km']}")

    # 5. Confidence
    print("\n--- 5. Confidence ---")
    conf_res = ConfidenceService.analyze_confidence(case_code, db)
    print(f"Confidence: score={conf_res['confidence_score']}, level={conf_res['confidence_level']}")

    # 6. Evidence
    print("\n--- 6. Evidence ---")
    ev_res = EvidenceService.generate_evidence(case_code, db)
    print(f"Evidence hash: {ev_res['evidence_hash']}, accepted={ev_res['summary']['accepted_measurements']}, rejected={ev_res['summary']['rejected_measurements']}")

    # 7. Dashboard heat map test
    print("\n--- 7. Dashboard Heatmap ---")
    heat_res = DashboardService.get_heatmap_data(db, case_id)
    print(f"Heatmap data points: {len(heat_res)}")

if __name__ == "__main__":
    test_pipeline()
