"""
Unit Tests for CDRValidationService
=====================================

Verifies the CDR Validation Service layer (Week 3, Day 2):
  1. CDRDataQualityScore — grade thresholds and score clamping.
  2. CDRValidationReport — field structure, is_valid property, summary().
  3. CDRValidationService.validate_batch():
       a. Empty batch → graceful baseline report.
       b. All-valid batch → is_valid=True, score ≈ 1.0, grade "Excellent".
       c. Mixed batch (valid + invalid) → correct rejection counts,
          failure_categories tallied, quality scores reflect errors.
       d. All-invalid batch → is_valid=False, low score.
       e. Duplicate ID detection → CDR_DUPLICATE_ID in failure_categories,
          consistency_score < 1.0.
       f. Duplicate content detection → CDR_DUPLICATE_RECORD tallied.
       g. Stale timestamps → timeliness_score < 1.0.
       h. Missing key fields → completeness_score < 1.0.
       i. Warning-only records → is_valid=True, warning_categories populated.
       j. Failure category aggregation across multiple records.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from scientific.config import ValidationThresholds
from scientific.models.cdr_record import CDRRecord
from scientific.validation.validators import (
    CDRDataQualityScore,
    CDRValidationReport,
    CDRValidationService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


_record_seq = 0
_DEFAULT = object()


def _valid_record(
    *,
    operator: str = "airtel",
    target_number: Any = _DEFAULT,
    timestamp: datetime | None = None,
    first_cgi: Any = _DEFAULT,
    latitude: float | None = 21.293,
    longitude: float | None = 72.889,
    record_id: int | None = None,
) -> CDRRecord:
    """Factory for a minimal valid CDR record."""
    global _record_seq
    _record_seq += 1
    if target_number is _DEFAULT:
        target_number = f"9714499{_record_seq:04d}"
    if first_cgi is _DEFAULT:
        first_cgi = f"404-98-8331-{_record_seq:05d}"
    ts = timestamp or (_now() - timedelta(hours=1))
    return CDRRecord(
        id=record_id,
        operator=operator,
        target_number=target_number,
        timestamp=ts,
        first_cgi=first_cgi,
        latitude=latitude,
        longitude=longitude,
    )


# ---------------------------------------------------------------------------
# 1. CDRDataQualityScore — grade helper
# ---------------------------------------------------------------------------


class TestCDRDataQualityScoreGrade:
    """Tests grade_from_score boundary values."""

    @pytest.mark.parametrize(
        "score, expected_grade",
        [
            (1.00, "Excellent"),
            (0.95, "Excellent"),
            (0.94, "Good"),
            (0.80, "Good"),
            (0.79, "Fair"),
            (0.60, "Fair"),
            (0.59, "Poor"),
            (0.40, "Poor"),
            (0.39, "Critical"),
            (0.00, "Critical"),
        ],
    )
    def test_grade_boundaries(self, score: float, expected_grade: str):
        assert CDRDataQualityScore.grade_from_score(score) == expected_grade

    def test_score_dataclass_fields(self):
        qs = CDRDataQualityScore(
            overall_score=0.88,
            validity_score=0.90,
            completeness_score=0.85,
            consistency_score=1.0,
            timeliness_score=0.80,
            grade="Good",
        )
        assert qs.overall_score == 0.88
        assert qs.grade == "Good"


# ---------------------------------------------------------------------------
# 2. CDRValidationReport — structure and properties
# ---------------------------------------------------------------------------


class TestCDRValidationReportStructure:
    """Tests report fields, is_valid, and summary()."""

    def _make_report(self, rejected: int = 0, valid: int = 5) -> CDRValidationReport:
        qs = CDRDataQualityScore(
            overall_score=0.9,
            validity_score=0.9,
            completeness_score=0.85,
            consistency_score=1.0,
            timeliness_score=0.95,
            grade="Good",
        )
        return CDRValidationReport(
            total_records=valid + rejected,
            valid_count=valid,
            rejected_count=rejected,
            warning_count=2,
            failure_categories={"CDR_FUTURE_TIMESTAMP": rejected} if rejected else {},
            warning_categories={"CDR_STALE_TIMESTAMP": 2},
            per_record_results=[],
            quality_score=qs,
        )

    def test_is_valid_true_when_no_rejections(self):
        report = self._make_report(rejected=0, valid=5)
        assert report.is_valid is True

    def test_is_valid_false_when_rejections(self):
        report = self._make_report(rejected=2, valid=3)
        assert report.is_valid is False

    def test_summary_contains_key_info(self):
        report = self._make_report(rejected=1, valid=4)
        s = report.summary()
        assert "total=5" in s
        assert "valid=4" in s
        assert "rejected=1" in s
        assert "grade=Good" in s


# ---------------------------------------------------------------------------
# 3a. Empty batch
# ---------------------------------------------------------------------------


class TestCDRValidationServiceEmptyBatch:
    """validate_batch([]) must return a well-formed baseline report."""

    def test_empty_batch_returns_report(self):
        svc = CDRValidationService()
        report = svc.validate_batch([])
        assert report.total_records == 0
        assert report.valid_count == 0
        assert report.rejected_count == 0
        assert report.warning_count == 0
        assert report.failure_categories == {}
        assert report.warning_categories == {}
        assert report.per_record_results == []

    def test_empty_batch_score_is_perfect(self):
        svc = CDRValidationService()
        report = svc.validate_batch([])
        qs = report.quality_score
        assert qs.overall_score == 1.0
        assert qs.grade == "Excellent"

    def test_empty_batch_is_valid(self):
        svc = CDRValidationService()
        report = svc.validate_batch([])
        assert report.is_valid is True


# ---------------------------------------------------------------------------
# 3b. All-valid batch
# ---------------------------------------------------------------------------


class TestCDRValidationServiceAllValid:
    """A clean batch of fully-populated valid records should score near 1.0."""

    def test_all_valid_is_valid(self):
        records = [_valid_record() for _ in range(5)]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.is_valid is True
        assert report.rejected_count == 0
        assert report.valid_count == 5
        assert report.total_records == 5

    def test_all_valid_excellent_grade(self):
        records = [_valid_record() for _ in range(5)]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.quality_score.grade == "Excellent"
        assert report.quality_score.overall_score >= 0.95

    def test_all_valid_failure_categories_empty(self):
        records = [_valid_record() for _ in range(3)]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.failure_categories == {}

    def test_all_valid_validity_score_is_one(self):
        records = [_valid_record() for _ in range(4)]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.quality_score.validity_score == 1.0

    def test_summary_runs_without_error(self):
        records = [_valid_record() for _ in range(2)]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        s = report.summary()
        assert "total=2" in s


# ---------------------------------------------------------------------------
# 3c. Mixed batch
# ---------------------------------------------------------------------------


class TestCDRValidationServiceMixedBatch:
    """Mix of valid and invalid records; counts and categories must be accurate."""

    def test_rejection_count(self):
        future_ts = _now() + timedelta(hours=2)
        records = [
            _valid_record(),
            _valid_record(),
            CDRRecord(operator="airtel", target_number="9000000001", timestamp=future_ts),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.total_records == 3
        assert report.rejected_count == 1
        assert report.valid_count == 2

    def test_future_timestamp_in_failure_categories(self):
        future_ts = _now() + timedelta(hours=2)
        records = [
            _valid_record(),
            CDRRecord(operator="airtel", target_number="9000000001", timestamp=future_ts),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert "CDR_FUTURE_TIMESTAMP" in report.failure_categories
        assert report.failure_categories["CDR_FUTURE_TIMESTAMP"] == 1

    def test_invalid_operator_in_failure_categories(self):
        records = [
            _valid_record(),
            CDRRecord(operator="unknown_op", target_number="9000000001",
                      timestamp=_now() - timedelta(hours=1)),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert "CDR_INVALID_OPERATOR" in report.failure_categories

    def test_validity_score_partial(self):
        future_ts = _now() + timedelta(hours=1)
        # 3 valid, 1 invalid → validity = 0.75
        records = [
            _valid_record(),
            _valid_record(),
            _valid_record(),
            CDRRecord(operator="airtel", target_number="9000000001", timestamp=future_ts),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.quality_score.validity_score == pytest.approx(0.75, abs=0.001)

    def test_multiple_error_codes_tallied_separately(self):
        future_ts = _now() + timedelta(hours=1)
        records = [
            CDRRecord(operator="docomo", target_number="9000000001",
                      timestamp=_now() - timedelta(hours=1)),  # CDR_INVALID_OPERATOR
            CDRRecord(operator="airtel", target_number="9000000002", timestamp=future_ts),  # CDR_FUTURE_TIMESTAMP
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert "CDR_INVALID_OPERATOR" in report.failure_categories
        assert "CDR_FUTURE_TIMESTAMP" in report.failure_categories


# ---------------------------------------------------------------------------
# 3d. All-invalid batch
# ---------------------------------------------------------------------------


class TestCDRValidationServiceAllInvalid:
    """A fully-broken batch must be is_valid=False with low score."""

    def test_all_invalid_is_not_valid(self):
        future_ts = _now() + timedelta(days=1)
        records = [
            CDRRecord(operator="airtel", target_number="9000000001", timestamp=future_ts),
            CDRRecord(operator="airtel", target_number="9000000002", timestamp=future_ts),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.is_valid is False
        assert report.rejected_count == 2
        assert report.valid_count == 0

    def test_all_invalid_low_validity_score(self):
        future_ts = _now() + timedelta(days=1)
        records = [
            CDRRecord(operator="airtel", target_number="9000000001", timestamp=future_ts),
            CDRRecord(operator="airtel", target_number="9000000002", timestamp=future_ts),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.quality_score.validity_score == 0.0

    def test_all_invalid_grade_poor_or_worse(self):
        future_ts = _now() + timedelta(days=1)
        records = [
            CDRRecord(operator="airtel", target_number=str(i), timestamp=future_ts)
            for i in range(5)
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.quality_score.grade in ("Poor", "Critical")


# ---------------------------------------------------------------------------
# 3e. Duplicate ID detection
# ---------------------------------------------------------------------------


class TestCDRValidationServiceDuplicateIds:
    """Duplicate record IDs must be tallied in failure_categories and
    reduce consistency_score."""

    def test_duplicate_id_in_failure_categories(self):
        ts = _now() - timedelta(hours=1)
        records = [
            CDRRecord(id=42, operator="airtel", target_number="9714499703", timestamp=ts),
            CDRRecord(id=42, operator="airtel", target_number="9877654321", timestamp=ts),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert "CDR_DUPLICATE_ID" in report.failure_categories
        assert report.failure_categories["CDR_DUPLICATE_ID"] >= 1

    def test_duplicate_id_reduces_consistency_score(self):
        ts = _now() - timedelta(hours=1)
        records = [
            CDRRecord(id=99, operator="airtel", target_number="9714499703", timestamp=ts),
            CDRRecord(id=99, operator="airtel", target_number="9877654321", timestamp=ts),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.quality_score.consistency_score < 1.0

    def test_unique_ids_no_duplicate_error(self):
        ts = _now() - timedelta(hours=1)
        records = [
            CDRRecord(id=1, operator="airtel", target_number="9714499703", timestamp=ts),
            CDRRecord(id=2, operator="airtel", target_number="9877654321", timestamp=ts),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert "CDR_DUPLICATE_ID" not in report.failure_categories


# ---------------------------------------------------------------------------
# 3f. Duplicate content detection
# ---------------------------------------------------------------------------


class TestCDRValidationServiceDuplicateContent:
    """Same target_number + timestamp + first_cgi triggers CDR_DUPLICATE_RECORD."""

    def test_duplicate_content_in_failure_categories(self):
        ts = _now() - timedelta(hours=2)
        records = [
            _valid_record(target_number="9714499703", timestamp=ts, first_cgi="404-1-2-3"),
            _valid_record(target_number="9714499703", timestamp=ts, first_cgi="404-1-2-3"),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert "CDR_DUPLICATE_RECORD" in report.failure_categories
        assert report.failure_categories["CDR_DUPLICATE_RECORD"] >= 1

    def test_different_timestamps_no_duplicate(self):
        ts1 = _now() - timedelta(hours=3)
        ts2 = ts1 + timedelta(seconds=30)
        records = [
            _valid_record(target_number="9714499703", timestamp=ts1, first_cgi="404-1-2-3"),
            _valid_record(target_number="9714499703", timestamp=ts2, first_cgi="404-1-2-3"),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert "CDR_DUPLICATE_RECORD" not in report.failure_categories


# ---------------------------------------------------------------------------
# 3g. Stale timestamp timeliness
# ---------------------------------------------------------------------------


class TestCDRValidationServiceTimeliness:
    """Stale timestamps reduce timeliness_score without necessarily
    marking the record as invalid (stale is WARNING-level)."""

    def test_stale_records_reduce_timeliness_score(self):
        thresholds = ValidationThresholds(max_measurement_age_days=30)
        svc = CDRValidationService(thresholds=thresholds)
        stale_ts = _now() - timedelta(days=60)
        records = [
            CDRRecord(operator="airtel", target_number="9714499703", timestamp=stale_ts),
        ]
        report = svc.validate_batch(records)
        assert report.quality_score.timeliness_score < 1.0

    def test_fresh_records_full_timeliness_score(self):
        svc = CDRValidationService()
        records = [_valid_record() for _ in range(3)]
        report = svc.validate_batch(records)
        assert report.quality_score.timeliness_score == 1.0

    def test_stale_warning_in_warning_categories(self):
        thresholds = ValidationThresholds(max_measurement_age_days=30)
        svc = CDRValidationService(thresholds=thresholds)
        stale_ts = _now() - timedelta(days=60)
        records = [
            CDRRecord(operator="airtel", target_number="9714499703", timestamp=stale_ts),
        ]
        report = svc.validate_batch(records)
        assert "CDR_STALE_TIMESTAMP" in report.warning_categories


# ---------------------------------------------------------------------------
# 3h. Completeness scoring
# ---------------------------------------------------------------------------


class TestCDRValidationServiceCompleteness:
    """Records missing key fields reduce completeness_score."""

    def test_fully_populated_records_score_one(self):
        records = [_valid_record() for _ in range(4)]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.quality_score.completeness_score == 1.0

    def test_missing_lat_lon_reduces_completeness(self):
        # Records with no lat/lon — completeness fields: operator, target_number,
        # timestamp, latitude(None), longitude(None), first_cgi
        records = [
            _valid_record(latitude=None, longitude=None),
            _valid_record(latitude=None, longitude=None),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        # 4 of 6 key fields present → completeness = 4/6 ≈ 0.667
        assert report.quality_score.completeness_score < 1.0
        assert report.quality_score.completeness_score == pytest.approx(4 / 6, abs=0.01)

    def test_missing_first_cgi_reduces_completeness(self):
        records = [
            _valid_record(first_cgi=None),
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        # 5 of 6 key fields present → completeness = 5/6 ≈ 0.833
        assert report.quality_score.completeness_score == pytest.approx(5 / 6, abs=0.01)


# ---------------------------------------------------------------------------
# 3i. Warning-only records
# ---------------------------------------------------------------------------


class TestCDRValidationServiceWarnings:
    """Records that produce only WARNINGs are still valid but inflate
    warning_categories."""

    def test_stale_records_are_valid_with_warning(self):
        thresholds = ValidationThresholds(max_measurement_age_days=10)
        svc = CDRValidationService(thresholds=thresholds)
        stale_ts = _now() - timedelta(days=20)
        records = [
            CDRRecord(operator="airtel", target_number="9714499703", timestamp=stale_ts),
        ]
        report = svc.validate_batch(records)
        # Stale is WARNING, not ERROR → record is still "valid"
        assert report.is_valid is True
        assert report.warning_count >= 1
        assert "CDR_STALE_TIMESTAMP" in report.warning_categories

    def test_warning_count_accumulates_across_records(self):
        thresholds = ValidationThresholds(max_measurement_age_days=5)
        svc = CDRValidationService(thresholds=thresholds)
        stale_ts = _now() - timedelta(days=30)
        records = [
            CDRRecord(operator="airtel", target_number="9714499703", timestamp=stale_ts),
            CDRRecord(operator="airtel", target_number="9877654321", timestamp=stale_ts),
            CDRRecord(operator="airtel", target_number="9000000000", timestamp=stale_ts),
        ]
        report = svc.validate_batch(records)
        assert report.warning_count == 3
        assert report.warning_categories.get("CDR_STALE_TIMESTAMP", 0) == 3


# ---------------------------------------------------------------------------
# 3j. Failure category aggregation
# ---------------------------------------------------------------------------


class TestCDRValidationServiceCategoryAggregation:
    """Failure categories must aggregate counts correctly across many records."""

    def test_same_error_code_aggregated(self):
        future_ts = _now() + timedelta(hours=1)
        # 3 records all with future timestamp → count should be 3
        records = [
            CDRRecord(operator="airtel", target_number=f"900000000{i}", timestamp=future_ts)
            for i in range(3)
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert report.failure_categories.get("CDR_FUTURE_TIMESTAMP", 0) == 3

    def test_per_record_results_length_matches(self):
        records = [_valid_record() for _ in range(7)]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert len(report.per_record_results) == 7

    def test_overall_score_bounded_zero_to_one(self):
        # Even worst-case inputs must not exceed bounds
        future_ts = _now() + timedelta(days=365)
        records = [
            CDRRecord(operator="invalid_op", target_number="", timestamp=future_ts)
            for _ in range(10)
        ]
        svc = CDRValidationService()
        report = svc.validate_batch(records)
        assert 0.0 <= report.quality_score.overall_score <= 1.0
