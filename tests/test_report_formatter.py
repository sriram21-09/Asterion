"""
Unit tests for the Report Data Formatter & Validation Summary Engine.

Validates that formatted output structures match expected report schemas,
mathematical correctness of aggregations, and Section 3F neutral terminology
enforcement across all generated text.
"""

from datetime import UTC, datetime

import pytest

from scientific.models.result import ConfidenceResult, LocalizationResult
from scientific.pipeline.movement import MovementSummary
from scientific.pipeline.report_formatter import ReportFormatter, format_full_report


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def formatter():
    """Provide a fresh ReportFormatter instance."""
    return ReportFormatter()


@pytest.fixture
def sample_records_by_operator():
    """Sample per-operator validation records."""
    return [
        {
            "operator": "Airtel",
            "records_imported": 100,
            "records_validated": 85,
            "records_rejected": 15,
            "warnings_count": 5,
        },
        {
            "operator": "BSNL",
            "records_imported": 60,
            "records_validated": 55,
            "records_rejected": 5,
            "warnings_count": 2,
        },
        {
            "operator": "Jio",
            "records_imported": 200,
            "records_validated": 190,
            "records_rejected": 10,
            "warnings_count": 8,
        },
    ]


@pytest.fixture
def sample_tower_data():
    """Sample tower resolution data."""
    return [
        {"tower_id": "T-001", "resolution_method": "exact"},
        {"tower_id": "T-002", "resolution_method": "exact"},
        {"tower_id": "T-003", "resolution_method": "exact"},
        {"tower_id": "T-004", "resolution_method": "prefix_lac"},
        {"tower_id": "T-005", "resolution_method": "prefix_mnc"},
        {"tower_id": "T-006", "resolution_method": "unresolved"},
    ]


@pytest.fixture
def sample_movement_summary():
    """Sample MovementSummary dataclass."""
    return MovementSummary(
        total_events=50,
        total_distance_m=42500.0,
        total_distance_km=42.5,
        time_span_seconds=7200.0,
        handover_count=12,
        anomaly_count=2,
        max_speed_kmh=78.2,
        avg_speed_kmh=24.8,
        velocity_distribution={
            "stationary": 5,
            "walking": 10,
            "driving": 30,
            "highway": 3,
            "anomalous": 2,
        },
        events=[],
    )


@pytest.fixture
def sample_confidence_result():
    """Sample ConfidenceResult."""
    return ConfidenceResult(
        scenario_id="SCN-001",
        confidence_score=0.87,
        confidence_level="high",
        error_ellipse_semi_major_m=120.0,
        error_ellipse_semi_minor_m=75.0,
        error_ellipse_orientation_deg=45.0,
        gdop=2.3,
        method="gdop",
    )


@pytest.fixture
def sample_localization_result():
    """Sample LocalizationResult."""
    return LocalizationResult(
        scenario_id="SCN-001",
        algorithm="multilateration",
        estimated_latitude=19.076,
        estimated_longitude=72.878,
        error_m=45.3,
        signals_used=4,
        timestamp=datetime(2026, 7, 30, 12, 0, 0, tzinfo=UTC),
    )


# ---------------------------------------------------------------------------
# Test: Validation Summary Structure
# ---------------------------------------------------------------------------


class TestValidationSummary:
    """Tests for format_validation_summary()."""

    def test_validation_summary_structure(self, formatter, sample_records_by_operator):
        """Output keys match expected schema, per-operator rows present."""
        result = formatter.format_validation_summary(sample_records_by_operator)

        assert result["section"] == "Validation Summary"
        assert "operator_rows" in result
        assert "totals" in result
        assert len(result["operator_rows"]) == 3

        for row in result["operator_rows"]:
            assert "operator" in row
            assert "records_imported" in row
            assert "records_validated" in row
            assert "records_rejected" in row
            assert "warnings_count" in row

    def test_validation_summary_totals(self, formatter, sample_records_by_operator):
        """Aggregated totals are mathematically correct."""
        result = formatter.format_validation_summary(sample_records_by_operator)
        totals = result["totals"]

        assert totals["records_imported"] == 100 + 60 + 200  # 360
        assert totals["records_validated"] == 85 + 55 + 190  # 330
        assert totals["records_rejected"] == 15 + 5 + 10  # 30
        assert totals["warnings_count"] == 5 + 2 + 8  # 15

    def test_validation_summary_empty(self, formatter):
        """Empty operator list produces zeroed totals."""
        result = formatter.format_validation_summary([])
        assert result["operator_rows"] == []
        assert result["totals"]["records_imported"] == 0
        assert result["totals"]["records_validated"] == 0
        assert result["totals"]["records_rejected"] == 0
        assert result["totals"]["warnings_count"] == 0


# ---------------------------------------------------------------------------
# Test: Tower Intelligence Summary
# ---------------------------------------------------------------------------


class TestTowerIntelligenceSummary:
    """Tests for format_tower_intelligence_summary()."""

    def test_tower_intelligence_summary(self, formatter, sample_tower_data):
        """Known/Estimated/Unknown counts and percentages are correct."""
        result = formatter.format_tower_intelligence_summary(sample_tower_data)

        assert result["section"] == "Tower Intelligence Summary"
        assert result["total_towers"] == 6

        assert result["known"]["count"] == 3
        assert result["estimated"]["count"] == 2
        assert result["unknown"]["count"] == 1

        # Percentages must sum to 100%
        total_pct = (
            result["known"]["percentage"]
            + result["estimated"]["percentage"]
            + result["unknown"]["percentage"]
        )
        assert abs(total_pct - 100.0) < 0.1

        # Verify individual percentages
        assert result["known"]["percentage"] == pytest.approx(50.0, abs=0.01)
        assert result["estimated"]["percentage"] == pytest.approx(33.33, abs=0.01)
        assert result["unknown"]["percentage"] == pytest.approx(16.67, abs=0.01)

    def test_tower_intelligence_empty(self, formatter):
        """Empty tower data produces zero counts without division-by-zero."""
        result = formatter.format_tower_intelligence_summary([])

        assert result["total_towers"] == 0
        assert result["known"]["count"] == 0
        assert result["known"]["percentage"] == 0.0
        assert result["estimated"]["percentage"] == 0.0
        assert result["unknown"]["percentage"] == 0.0

    def test_percentage_calculations_all_known(self, formatter):
        """All towers as exact → 100% known, 0% others."""
        data = [
            {"tower_id": "T-1", "resolution_method": "exact"},
            {"tower_id": "T-2", "resolution_method": "exact"},
        ]
        result = formatter.format_tower_intelligence_summary(data)
        assert result["known"]["percentage"] == 100.0
        assert result["estimated"]["percentage"] == 0.0
        assert result["unknown"]["percentage"] == 0.0


# ---------------------------------------------------------------------------
# Test: Movement Reconstruction Summary
# ---------------------------------------------------------------------------


class TestMovementReconstructionSummary:
    """Tests for format_movement_reconstruction_summary()."""

    def test_movement_reconstruction_summary(self, formatter, sample_movement_summary):
        """Distance, speed, handover count match MovementSummary input."""
        result = formatter.format_movement_reconstruction_summary(
            sample_movement_summary
        )

        assert result["section"] == "Movement Reconstruction Summary"
        assert result["total_events"] == 50
        assert result["total_distance_km"] == 42.5
        assert result["total_distance_m"] == 42500.0
        assert result["time_span_seconds"] == 7200.0
        assert result["handover_count"] == 12
        assert result["anomaly_count"] == 2

        assert result["speed_statistics"]["average_speed_kmh"] == 24.8
        assert result["speed_statistics"]["max_speed_kmh"] == 78.2

        assert result["velocity_distribution"]["driving"] == 30
        assert result["velocity_distribution"]["anomalous"] == 2


# ---------------------------------------------------------------------------
# Test: Localization & Confidence Summary
# ---------------------------------------------------------------------------


class TestLocalizationSummary:
    """Tests for format_localization_summary()."""

    def test_localization_summary(
        self,
        formatter,
        sample_confidence_result,
        sample_localization_result,
    ):
        """GDOP, confidence level, error ellipse values propagated correctly."""
        result = formatter.format_localization_summary(
            sample_confidence_result, sample_localization_result
        )

        assert result["section"] == "Localization & Confidence Summary"

        # Confidence block
        assert result["confidence"]["score"] == 0.87
        assert result["confidence"]["level"] == "high"
        assert result["confidence"]["gdop"] == 2.3
        assert result["confidence"]["method"] == "gdop"

        # Error ellipse block
        assert result["error_ellipse"]["semi_major_m"] == 120.0
        assert result["error_ellipse"]["semi_minor_m"] == 75.0
        assert result["error_ellipse"]["orientation_deg"] == 45.0

        # Localization block
        assert result["localization"]["algorithm"] == "multilateration"
        assert result["localization"]["estimated_latitude"] == 19.076
        assert result["localization"]["estimated_longitude"] == 72.878
        assert result["localization"]["error_m"] == 45.3
        assert result["localization"]["signals_used"] == 4


# ---------------------------------------------------------------------------
# Test: Investigation Narrative
# ---------------------------------------------------------------------------


class TestInvestigationNarrative:
    """Tests for format_investigation_narrative()."""

    def test_investigation_narrative(self, formatter):
        """Narrative contains all section headings; no prohibited terms."""
        result = formatter.format_investigation_narrative(
            target_identifier="DEV-7701",
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
        )

        assert result["section"] == "Investigation Narrative"
        assert "full_narrative" in result
        assert "sections" in result

        narrative = result["full_narrative"]
        assert "=== NEUTRAL INVESTIGATION SUMMARY ===" in narrative
        assert "Device Overview:" in narrative
        assert "Movement Patterns:" in narrative
        assert "Tower Associations:" in narrative
        assert "Timeline Narrative:" in narrative

        # Individual sections accessible
        sections = result["sections"]
        assert "device_overview" in sections
        assert "movement_patterns" in sections
        assert "tower_associations" in sections
        assert "timeline_narrative" in sections

        # Verify neutral terms
        assert "analyzed device" in sections["device_overview"]
        assert "observed device" in sections["movement_patterns"]


# ---------------------------------------------------------------------------
# Test: Full Report Assembly
# ---------------------------------------------------------------------------


class TestFullReport:
    """Tests for format_full_report()."""

    def test_full_report_structure(
        self,
        formatter,
        sample_records_by_operator,
        sample_tower_data,
        sample_movement_summary,
        sample_confidence_result,
        sample_localization_result,
    ):
        """Top-level keys present: all 6 sections."""
        result = formatter.format_full_report(
            records_by_operator=sample_records_by_operator,
            tower_data=sample_tower_data,
            movement_summary=sample_movement_summary,
            confidence_result=sample_confidence_result,
            localization_result=sample_localization_result,
            target_identifier="DEV-7701",
            total_records=360,
            active_period="2026-07-01 to 2026-07-07",
            total_towers=6,
            primary_tower_id="T-001",
            first_seen="2026-07-01 00:00:00 UTC",
            first_location="Sector 12, Delhi",
            last_seen="2026-07-07 18:30:00 UTC",
            last_location="Connaught Place, Delhi",
            primary_operator="Airtel",
        )

        # All 6 top-level sections must be present
        assert "report_metadata" in result
        assert "validation_summary" in result
        assert "tower_intelligence" in result
        assert "movement_reconstruction" in result
        assert "localization_confidence" in result
        assert "investigation_narrative" in result

        # Metadata
        assert result["report_metadata"]["target_identifier"] == "DEV-7701"
        assert result["report_metadata"]["scenario_id"] == "SCN-001"
        assert "generated_at" in result["report_metadata"]


# ---------------------------------------------------------------------------
# Test: Neutral Terminology Enforcement
# ---------------------------------------------------------------------------


class TestNeutralTerminologyEnforcement:
    """Tests for prohibited terminology detection across formatters."""

    def test_prohibited_term_in_operator_name(self, formatter):
        """Prohibited terms in operator name raise ValueError."""
        bad_data = [
            {
                "operator": "Suspect Network",
                "records_imported": 10,
                "records_validated": 8,
                "records_rejected": 2,
                "warnings_count": 0,
            },
        ]
        with pytest.raises(ValueError, match="Prohibited non-neutral term"):
            formatter.format_validation_summary(bad_data)

    def test_prohibited_term_in_report_title(
        self,
        formatter,
        sample_records_by_operator,
        sample_tower_data,
        sample_movement_summary,
        sample_confidence_result,
        sample_localization_result,
    ):
        """Prohibited terms in report title raise ValueError."""
        with pytest.raises(ValueError, match="Prohibited non-neutral term"):
            formatter.format_full_report(
                records_by_operator=sample_records_by_operator,
                tower_data=sample_tower_data,
                movement_summary=sample_movement_summary,
                confidence_result=sample_confidence_result,
                localization_result=sample_localization_result,
                target_identifier="DEV-001",
                total_records=100,
                active_period="2026-07-01",
                total_towers=5,
                primary_tower_id="T-1",
                first_seen="08:00",
                first_location="A",
                last_seen="18:00",
                last_location="B",
                report_title="Criminal Activity Report",
            )

    def test_prohibited_term_in_narrative_identifier(self, formatter):
        """Prohibited terms in target identifier raise ValueError."""
        with pytest.raises(ValueError, match="Prohibited non-neutral term"):
            formatter.format_investigation_narrative(
                target_identifier="Suspect Device",
                total_records=10,
                active_period="2026-07-01",
                total_distance_km=5.0,
                avg_speed_kmh=10.0,
                max_speed_kmh=20.0,
                total_towers=2,
                primary_tower_id="T-1",
                first_seen="08:00",
                first_location="A",
                last_seen="18:00",
                last_location="B",
            )


# ---------------------------------------------------------------------------
# Test: Convenience Function
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    """Tests for module-level format_full_report()."""

    def test_convenience_function_produces_same_output(
        self,
        formatter,
        sample_records_by_operator,
        sample_tower_data,
        sample_movement_summary,
        sample_confidence_result,
        sample_localization_result,
    ):
        """Module-level function returns structure matching class method."""
        kwargs = dict(
            records_by_operator=sample_records_by_operator,
            tower_data=sample_tower_data,
            movement_summary=sample_movement_summary,
            confidence_result=sample_confidence_result,
            localization_result=sample_localization_result,
            target_identifier="DEV-7701",
            total_records=360,
            active_period="2026-07-01 to 2026-07-07",
            total_towers=6,
            primary_tower_id="T-001",
            first_seen="2026-07-01 00:00:00 UTC",
            first_location="Sector 12",
            last_seen="2026-07-07 18:30:00 UTC",
            last_location="Connaught Place",
        )

        result_class = formatter.format_full_report(**kwargs)
        result_func = format_full_report(**kwargs)

        # Both should have same top-level structure
        assert set(result_class.keys()) == set(result_func.keys())
        assert result_class["validation_summary"] == result_func["validation_summary"]
        assert result_class["tower_intelligence"] == result_func["tower_intelligence"]
