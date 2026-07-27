"""
Unit tests for the template-based neutral investigation summary generator.
"""

import pytest

from scientific.pipeline.summary_generator import (
    APPROVED_TERMS,
    PROHIBITED_TERMS,
    InvestigationSummaryGenerator,
    generate_device_overview,
    generate_movement_summary,
    generate_timeline_summary,
    generate_tower_summary,
    validate_neutral_terminology,
)


def test_approved_terminology_constants():
    """Verify approved and prohibited terminology constant sets."""
    assert "analyzed device" in APPROVED_TERMS
    assert "observed device" in APPROVED_TERMS
    assert "target identifier" in APPROVED_TERMS
    assert "analyzed subscriber" in APPROVED_TERMS

    assert "suspect" in PROHIBITED_TERMS
    assert "criminal" in PROHIBITED_TERMS
    assert "perpetrator" in PROHIBITED_TERMS
    assert "guilty party" in PROHIBITED_TERMS


def test_validate_neutral_terminology_valid():
    """Verify validate_neutral_terminology passes clean text."""
    clean_text = "The analyzed device was observed near tower T-101."
    assert validate_neutral_terminology(clean_text) == clean_text
    assert validate_neutral_terminology("") == ""
    assert validate_neutral_terminology(None) is None


@pytest.mark.parametrize(
    "prohibited", ["suspect", "criminal", "perpetrator", "guilty party"]
)
def test_validate_neutral_terminology_prohibited(prohibited):
    """Verify prohibited terms raise ValueError."""
    bad_text = f"The {prohibited} was moving north."
    with pytest.raises(ValueError, match="Prohibited non-neutral term detected"):
        validate_neutral_terminology(bad_text)


@pytest.mark.parametrize(
    "prohibited_caps", ["SUSPECT", "Criminal", "PERPETRATOR", "Guilty Party"]
)
def test_validate_neutral_terminology_case_insensitive(prohibited_caps):
    """Verify case-insensitive detection of prohibited terms."""
    bad_text = f"Identified {prohibited_caps} in CDR log."
    with pytest.raises(ValueError, match="Prohibited non-neutral term detected"):
        validate_neutral_terminology(bad_text)


def test_device_overview_generation():
    """Test device overview section generation."""
    gen = InvestigationSummaryGenerator(target_identifier="DEV-99812")
    overview = gen.generate_device_overview(
        total_records=150,
        active_period="2026-07-20 to 2026-07-26",
        primary_operator="Airtel",
        imei="356938035643809",
        imsi="404450123456789",
        msisdn="+919876543210",
        notes="Normalized CDR dataset",
    )

    assert "analyzed device" in overview
    assert "target identifier DEV-99812" in overview
    assert "150" in overview
    assert "Airtel" in overview
    assert "IMEI: 356938035643809" in overview
    assert "Normalized CDR dataset" in overview


def test_movement_patterns_generation():
    """Test movement patterns section generation."""
    gen = InvestigationSummaryGenerator(target_identifier="DEV-99812")
    movement = gen.generate_movement_patterns(
        total_distance_km=42.5,
        avg_speed_kmh=24.8,
        max_speed_kmh=78.2,
        handover_count=12,
        high_velocity_count=2,
    )

    assert "observed device" in movement
    assert "42.50 km" in movement
    assert "24.8 km/h" in movement
    assert "78.2 km/h" in movement
    assert "12 network handover events" in movement
    assert "2 anomaly events with velocities exceeding physical thresholds" in movement

    movement_clean = gen.generate_movement_patterns(
        total_distance_km=10.0,
        avg_speed_kmh=15.0,
        max_speed_kmh=45.0,
        handover_count=3,
        high_velocity_count=0,
    )
    assert "No physically implausible velocity anomalies" in movement_clean


def test_tower_associations_generation():
    """Test tower associations section generation."""
    gen = InvestigationSummaryGenerator(target_identifier="DEV-99812")
    tower_sec = gen.generate_tower_associations(
        total_towers=8,
        primary_tower_id="TOWER-A1",
        known_count=5,
        estimated_count=2,
        unknown_count=1,
    )

    assert "observed device" in tower_sec
    assert "analyzed subscriber" in tower_sec
    assert "8 unique cell tower sites" in tower_sec
    assert "TOWER-A1" in tower_sec
    assert "5 Known" in tower_sec
    assert "2 Estimated" in tower_sec
    assert "1 Unknown" in tower_sec


def test_timeline_narrative_generation():
    """Test timeline narrative section generation."""
    gen = InvestigationSummaryGenerator(target_identifier="DEV-99812")
    timeline = gen.generate_timeline_narrative(
        first_seen="2026-07-20 08:00:00 UTC",
        first_location="Sector 12, Delhi",
        last_seen="2026-07-26 18:30:00 UTC",
        last_location="Connaught Place, Delhi",
        peak_period="12:00-14:00 UTC",
    )

    assert "analyzed device" in timeline
    assert "target identifier" in timeline
    assert "2026-07-20 08:00:00 UTC" in timeline
    assert "Sector 12, Delhi" in timeline
    assert "Connaught Place, Delhi" in timeline
    assert "12:00-14:00 UTC" in timeline


def test_full_investigation_summary():
    """Test complete multi-section investigation summary generation."""
    gen = InvestigationSummaryGenerator(target_identifier="DEV-001")
    full_summary = gen.generate_full_investigation_summary(
        total_records=200,
        active_period="2026-07-01 to 2026-07-07",
        total_distance_km=120.4,
        avg_speed_kmh=35.0,
        max_speed_kmh=90.0,
        total_towers=15,
        primary_tower_id="SITE-404",
        first_seen="2026-07-01 00:00:00 UTC",
        first_location="Tower A",
        last_seen="2026-07-07 23:59:59 UTC",
        last_location="Tower Z",
        primary_operator="Jio",
        handover_count=20,
        high_velocity_count=1,
        known_towers=10,
        estimated_towers=4,
        unknown_towers=1,
        peak_period="08:00-10:00 UTC",
        custom_notes="Audit verified and cryptographically signed.",
    )

    assert "=== NEUTRAL INVESTIGATION SUMMARY ===" in full_summary
    assert "Device Overview:" in full_summary
    assert "Movement Patterns:" in full_summary
    assert "Tower Associations:" in full_summary
    assert "Timeline Narrative:" in full_summary
    assert "Executive Notes:" in full_summary
    assert "Audit verified and cryptographically signed." in full_summary


def test_generator_prohibited_terms_input():
    """Test that passing prohibited terms in parameters raises ValueError."""
    with pytest.raises(ValueError):
        InvestigationSummaryGenerator(target_identifier="Suspect Device")

    gen = InvestigationSummaryGenerator(target_identifier="DEV-101")

    with pytest.raises(ValueError):
        gen.generate_device_overview(
            total_records=10,
            active_period="2026-07-01",
            notes="Belongs to suspect",
        )

    with pytest.raises(ValueError):
        gen.generate_movement_patterns(
            total_distance_km=5.0,
            avg_speed_kmh=10.0,
            max_speed_kmh=20.0,
            notes="Criminal movement path",
        )

    with pytest.raises(ValueError):
        gen.generate_tower_associations(
            total_towers=2,
            primary_tower_id="T1",
            notes="Perpetrator connected here",
        )

    with pytest.raises(ValueError):
        gen.generate_timeline_narrative(
            first_seen="T1",
            first_location="L1",
            last_seen="T2",
            last_location="L2",
            notes="Guilty party active",
        )


def test_convenience_functions():
    """Test module-level convenience functions."""
    dev_ov = generate_device_overview("DEV-77", 50, "2026-07-01", operator="BSNL")
    assert "analyzed device" in dev_ov
    assert "DEV-77" in dev_ov

    mv_sum = generate_movement_summary("DEV-77", 12.0, 10.0, 30.0)
    assert "observed device" in mv_sum

    tw_sum = generate_tower_summary("DEV-77", 4, "TOWER-5")
    assert "observed device" in tw_sum

    tl_sum = generate_timeline_summary("DEV-77", "08:00", "Loc A", "18:00", "Loc B")
    assert "analyzed device" in tl_sum
