"""Unit tests for ProvenanceService and Provenance API endpoints."""

from datetime import datetime, timezone
from app.models.case import Case
from app.models.measurement import Measurement
from app.services.provenance_service import ProvenanceService


def test_provenance_service_real_data(db_session):
    """Test provenance calculation with 100% REAL measurements."""
    case = Case(
        title="Test Real Case", description="Real data case", enable_augmentation=True
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Add 10 REAL measurements
    for i in range(10):
        m = Measurement(
            case_id=case.id,
            measurement_code=f"REAL-{i}",
            timestamp=datetime.now(timezone.utc),
            latitude=28.6139,
            longitude=77.2090,
            rssi_dbm=-75.0,
            is_simulated=False,
            source="REAL",
        )
        db_session.add(m)
    db_session.commit()

    prov = ProvenanceService.get_case_provenance(db_session, case.id)

    assert prov["case_id"] == case.id
    assert prov["status"] == "Imported Dataset Only"
    assert prov["counts"]["REAL"] == 10
    assert prov["counts"]["AUGMENTED_RSSI"] == 0
    assert prov["counts"]["AUGMENTED_TA"] == 0
    assert prov["counts"]["SIMULATED"] == 0
    assert prov["percentages"]["imported_pct"] == 100.0
    assert prov["percentages"]["generated_pct"] == 0.0
    assert prov["has_generated_data"] is False
    assert prov["has_augmentation"] is False
    assert prov["has_simulation"] is False
    assert prov["evidence_integrity"] == "Verified ✓"
    assert prov["scientific_transparency"] == "Verified ✓"


def test_provenance_service_augmented_data(db_session):
    """Test provenance calculation with REAL and AUGMENTED_RSSI measurements."""
    case = Case(
        title="Test Augmented Case",
        description="Augmented data case",
        enable_augmentation=True,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Add 8 REAL, 2 AUGMENTED_RSSI
    for i in range(8):
        m = Measurement(
            case_id=case.id,
            measurement_code=f"M-{i}",
            timestamp=datetime.now(timezone.utc),
            latitude=28.6139,
            longitude=77.2090,
            rssi_dbm=-70.0,
            is_simulated=False,
            source="REAL",
        )
        db_session.add(m)

    for i in range(2):
        m = Measurement(
            case_id=case.id,
            measurement_code=f"AUG-{i}",
            timestamp=datetime.now(timezone.utc),
            latitude=28.6139,
            longitude=77.2090,
            rssi_dbm=-88.5,
            is_simulated=True,
            source="AUGMENTED_RSSI",
        )
        db_session.add(m)
    db_session.commit()

    prov = ProvenanceService.get_case_provenance(db_session, case.id)

    assert prov["status"] == "Measurement Augmentation Active"
    assert prov["counts"]["REAL"] == 8
    assert prov["counts"]["AUGMENTED_RSSI"] == 2
    assert prov["percentages"]["imported_pct"] == 80.0
    assert prov["percentages"]["generated_pct"] == 20.0
    assert prov["has_generated_data"] is True
    assert prov["has_augmentation"] is True
    assert prov["has_simulation"] is False


def test_provenance_api_endpoint(client, db_session):
    """Test GET /api/v1/cases/{case_id}/provenance endpoint."""
    case = Case(
        title="API Case", description="Testing provenance API", enable_augmentation=True
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    response = client.get(f"/api/v1/cases/{case.id}/provenance")
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["success"] is True
    assert json_resp["data"]["case_id"] == case.id
    assert json_resp["data"]["status"] == "Imported Dataset Only"
