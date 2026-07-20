
from datetime import datetime, timezone
from scientific.models.measurement import Measurement
from scientific.models.tower import Tower
from scientific.pipeline.confidence import compute_confidence
from scientific.pipeline.evidence import synthesize_evidence


def test_confidence_equilateral_layout():
    """Verify that an equilateral triangle geometry of towers yields a low GDOP and high confidence."""
    # Center is at (10.0, 10.0)
    # Put towers at ~550m distance in three directions (0, 120, 240 degrees)
    # 0.005 degrees latitude is ~556m
    # 0.0025 degrees latitude is ~278m
    # 0.00433 degrees longitude at lat 10.0 is ~474m (using cos(10.0) * 556m)
    towers = [
        Tower(tower_id="T001", latitude=10.005, longitude=10.0),
        Tower(tower_id="T002", latitude=9.9975, longitude=10.00433),
        Tower(tower_id="T003", latitude=9.9975, longitude=9.99567),
    ]

    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
            uncertainty_m=30.0,
        ),
        Measurement(
            measurement_id="M002",
            tower_id="T002",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
            uncertainty_m=30.0,
        ),
        Measurement(
            measurement_id="M003",
            tower_id="T003",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
            uncertainty_m=30.0,
        ),
    ]

    result = compute_confidence(
        scenario_id="SCN-EQ",
        estimated_latitude=10.0,
        estimated_longitude=10.0,
        towers=towers,
        measurements=measurements,
    )

    assert result.scenario_id == "SCN-EQ"
    assert result.gdop is not None
    assert result.gdop < 2.0  # Perfect geometry is ~1.15
    assert result.confidence_level == "high"
    assert result.confidence_score > 0.8

    # The error ellipse should be close to a circle (semi-major ≈ semi-minor)
    assert result.error_ellipse_semi_major_m is not None
    assert result.error_ellipse_semi_minor_m is not None
    assert (
        abs(result.error_ellipse_semi_major_m - result.error_ellipse_semi_minor_m) < 1.0
    )


def test_confidence_collinear_layout():
    """Verify that a collinear setup of towers is handled robustly and yields low confidence."""
    # Towers in a straight line North-South
    towers = [
        Tower(tower_id="T001", latitude=10.010, longitude=10.0),
        Tower(tower_id="T002", latitude=10.005, longitude=10.0),
        Tower(tower_id="T003", latitude=9.990, longitude=10.0),
    ]

    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
            uncertainty_m=30.0,
        ),
        Measurement(
            measurement_id="M002",
            tower_id="T002",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
            uncertainty_m=30.0,
        ),
        Measurement(
            measurement_id="M003",
            tower_id="T003",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
            uncertainty_m=30.0,
        ),
    ]

    result = compute_confidence(
        scenario_id="SCN-COLL",
        estimated_latitude=10.0,
        estimated_longitude=10.0,
        towers=towers,
        measurements=measurements,
    )

    # Det of H^T*H will be zero or near zero
    assert result.confidence_level == "low"
    assert result.confidence_score == 0.0
    assert result.gdop is None
    assert result.error_ellipse_semi_major_m is None


def test_confidence_insufficient_towers():
    """Verify that 0 or 1 active towers returns low confidence without crashing."""
    towers = [
        Tower(tower_id="T001", latitude=10.010, longitude=10.0),
    ]
    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
        ),
    ]

    result = compute_confidence(
        scenario_id="SCN-FEW",
        estimated_latitude=10.0,
        estimated_longitude=10.0,
        towers=towers,
        measurements=measurements,
    )

    assert result.confidence_level == "low"
    assert result.confidence_score == 0.0
    assert result.gdop is None
    assert result.error_ellipse_semi_major_m is None


def test_ellipse_orientation_alignment():
    """Verify that ellipse orientations align with the direction of highest uncertainty.

    If towers are laid out primarily along the East-West axis (collinear-ish East-West),
    uncertainty is high in the North-South direction. Hence, the major axis of the error
    ellipse should align North-South (orientation ≈ 0 or 180 degrees).
    """
    # East-West dominant layout (slightly offset North-South to avoid division by zero/singularity)
    towers = [
        Tower(tower_id="T001", latitude=10.0, longitude=10.005),
        Tower(tower_id="T002", latitude=10.0, longitude=9.995),
        Tower(tower_id="T003", latitude=10.0001, longitude=10.0),  # small offset
    ]

    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
            uncertainty_m=30.0,
        ),
        Measurement(
            measurement_id="M002",
            tower_id="T002",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
            uncertainty_m=30.0,
        ),
        Measurement(
            measurement_id="M003",
            tower_id="T003",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
            uncertainty_m=30.0,
        ),
    ]

    result = compute_confidence(
        scenario_id="SCN-EW",
        estimated_latitude=10.0,
        estimated_longitude=10.0,
        towers=towers,
        measurements=measurements,
    )

    assert result.error_ellipse_orientation_deg is not None
    # North-South stretching means orientation is close to 0.0 or 180.0
    # Let's check if it's within 15 degrees of North (0/360) or South (180)
    angle = result.error_ellipse_orientation_deg
    assert (angle < 15.0 or angle > 345.0) or (abs(angle - 180.0) < 15.0)


def test_evidence_synthesis_audit():
    """Verify that evidence synthesis correctly categorizes valid/invalid measurements and reports stats."""
    towers = [
        Tower(tower_id="T001", latitude=10.0, longitude=20.0),
        Tower(tower_id="T002", latitude=10.1, longitude=20.0),
        Tower(tower_id="T003", latitude=10.2, longitude=20.0),
    ]

    measurements = [
        # Valid measurement 1
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-70.0,
        ),
        # Valid measurement 2
        Measurement(
            measurement_id="M002",
            tower_id="T002",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-60.0,
        ),
        # Invalid measurement (partial coordinates: latitude without longitude)
        Measurement(
            measurement_id="M003",
            tower_id="T003",
            timestamp=datetime.now(timezone.utc),
            rssi_dbm=-80.0,
            latitude=10.0,
            longitude=None,
        ),
    ]

    report = synthesize_evidence(
        scenario_id="SCN-AUDIT",
        towers=towers,
        measurements=measurements,
    )

    assert report["scenario_id"] == "SCN-AUDIT"
    assert report["summary"]["total_measurements"] == 3
    assert report["summary"]["accepted_measurements"] == 2
    assert report["summary"]["rejected_measurements"] == 1
    assert report["summary"]["towers_total"] == 3
    assert (
        report["summary"]["towers_used_count"] == 2
    )  # T001 and T002 have accepted measurements, T003 does not

    # Check towers list
    towers_map = {t["tower_id"]: t for t in report["towers"]}
    assert towers_map["T001"]["total_measurements"] == 1
    assert towers_map["T001"]["accepted_measurements"] == 1
    assert towers_map["T001"]["rejected_measurements"] == 0
    assert towers_map["T001"]["status"] == "active"

    assert towers_map["T003"]["total_measurements"] == 1
    assert towers_map["T003"]["accepted_measurements"] == 0
    assert towers_map["T003"]["rejected_measurements"] == 1
    assert towers_map["T003"]["status"] == "inactive"

    # Check accepted list
    assert "M001" in report["accepted_measurement_ids"]
    assert "M002" in report["accepted_measurement_ids"]
    assert "M003" not in report["accepted_measurement_ids"]

    # Check rejections list
    assert len(report["rejections"]) == 1
    rejection = report["rejections"][0]
    assert rejection["measurement_id"] == "M003"
    assert rejection["tower_id"] == "T003"
    assert len(rejection["errors"]) == 1
    assert rejection["errors"][0]["code"] == "MEAS_PARTIAL_COORDS"
