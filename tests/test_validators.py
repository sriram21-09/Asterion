"""
Unit Tests for CDR Validators
==============================

Verifies validation rules for Call Detail Records (CDRs):
  1. Required fields presence (operator, target_number, timestamp).
  2. Supported cellular operators validation.
  3. Timestamp validation (future checks, stale warning, missing seconds).
  4. Spatial coordinate bounds checking (operational ranges and parity).
  5. Duplicate record detection in batches (ID duplicates, content duplicates).
"""

from datetime import datetime, timedelta, timezone
import pytest

from scientific.config import ValidationThresholds
from scientific.models.cdr_record import CDRRecord
from scientific.validation.validators import (
    CDRRecordValidator,
    validate_cdr_batch,
    Severity,
)


class TestCDRRecordValidatorBasic:
    """Tests basic validation fields (presence and operator)."""

    def test_missing_required_fields(self):
        # Missing operator
        r_op = CDRRecord.model_construct(
            operator="",
            target_number="9714499703",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        validator = CDRRecordValidator()
        res = validator.validate(r_op)
        assert not res.is_valid
        assert any(e.code == "CDR_INVALID_OPERATOR" for e in res.errors)

        # Missing target number
        r_target = CDRRecord.model_construct(
            operator="airtel",
            target_number="",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        res = validator.validate(r_target)
        assert not res.is_valid
        assert any(e.code == "CDR_MISSING_TARGET_NUMBER" for e in res.errors)

        # Missing timestamp
        r_ts = CDRRecord.model_construct(
            operator="airtel",
            target_number="9714499703",
            timestamp=None,
        )
        res = validator.validate(r_ts)
        assert not res.is_valid
        assert any(e.code == "CDR_MISSING_TIMESTAMP" for e in res.errors)

    def test_supported_operators(self):
        validator = CDRRecordValidator()

        # Valid operators (case-insensitive)
        for op in ["airtel", "BSNL", "jio", "VI"]:
            r = CDRRecord(
                operator=op,
                target_number="9714499703",
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=5),
            )
            res = validator.validate(r)
            assert res.is_valid, f"Failed for operator {op}"

        # Invalid operator
        r_inv = CDRRecord(
            operator="docomo",
            target_number="9714499703",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        res = validator.validate(r_inv)
        assert not res.is_valid
        assert any(e.code == "CDR_INVALID_OPERATOR" for e in res.errors)


class TestCDRRecordValidatorTimestamp:
    """Tests timestamp checks: future check, stale check, and missing seconds check."""

    def test_future_timestamp(self):
        validator = CDRRecordValidator()
        future_ts = datetime.now(timezone.utc) + timedelta(hours=2)
        r = CDRRecord(
            operator="airtel",
            target_number="9714499703",
            timestamp=future_ts,
        )
        res = validator.validate(r)
        assert not res.is_valid
        assert any(e.code == "CDR_FUTURE_TIMESTAMP" for e in res.errors)

    def test_stale_timestamp(self):
        thresholds = ValidationThresholds(max_measurement_age_days=30)
        validator = CDRRecordValidator(thresholds=thresholds)
        stale_ts = datetime.now(timezone.utc) - timedelta(days=35)
        r = CDRRecord(
            operator="airtel",
            target_number="9714499703",
            timestamp=stale_ts,
        )
        res = validator.validate(r)
        # Should be valid but have a stale warning
        assert res.is_valid
        assert any(
            e.code == "CDR_STALE_TIMESTAMP" and e.severity == Severity.WARNING
            for e in res.errors
        )

    def test_missing_seconds_warning(self):
        validator = CDRRecordValidator()
        base_time = datetime.now(timezone.utc) - timedelta(hours=1)

        # With seconds in raw row (Airtel index 7)
        r_with_seconds = CDRRecord(
            operator="airtel",
            target_number="9714499703",
            timestamp=base_time,
            raw_data={"row": ["9714499703", "SMT", "Post", "BParty", "", "", "15/04/2026", "14:30:45"]},
        )
        res_sec = validator.validate(r_with_seconds)
        assert res_sec.is_valid
        assert not any(e.code == "CDR_TIMESTAMP_MISSING_SECONDS" for e in res_sec.errors)

        # Missing seconds in raw row
        r_missing_seconds = CDRRecord(
            operator="airtel",
            target_number="9714499703",
            timestamp=base_time.replace(second=0, microsecond=0),
            raw_data={"row": ["9714499703", "SMT", "Post", "BParty", "", "", "15/04/2026", "14:30"]},
        )
        res_missing = validator.validate(r_missing_seconds)
        assert res_missing.is_valid
        assert any(
            e.code == "CDR_TIMESTAMP_MISSING_SECONDS" and e.severity == Severity.WARNING
            for e in res_missing.errors
        )


class TestCDRRecordValidatorCoordinates:
    """Tests coordinate bounds and parity validations for start and end location."""

    def test_coordinate_parity(self):
        validator = CDRRecordValidator()
        ts = datetime.now(timezone.utc) - timedelta(minutes=5)

        # Start location parity: latitude provided, longitude None
        r_start_parity = CDRRecord.model_construct(
            operator="airtel",
            target_number="9714499703",
            timestamp=ts,
            latitude=12.9716,
            longitude=None,
        )
        res = validator.validate(r_start_parity)
        assert not res.is_valid
        assert any(e.code == "CDR_PARTIAL_COORDS" for e in res.errors)

        # End location parity: last_longitude provided, last_latitude None
        r_end_parity = CDRRecord.model_construct(
            operator="airtel",
            target_number="9714499703",
            timestamp=ts,
            last_latitude=None,
            last_longitude=77.5946,
        )
        res = validator.validate(r_end_parity)
        assert not res.is_valid
        assert any(e.code == "CDR_PARTIAL_LAST_COORDS" for e in res.errors)

    def test_operational_bounds(self):
        custom_thresholds = ValidationThresholds(
            latitude_range=(10.0, 20.0),
            longitude_range=(70.0, 80.0),
        )
        validator = CDRRecordValidator(thresholds=custom_thresholds)
        ts = datetime.now(timezone.utc) - timedelta(minutes=5)

        # Inside bounds
        r_inside = CDRRecord(
            operator="airtel",
            target_number="9714499703",
            timestamp=ts,
            latitude=15.0,
            longitude=75.0,
            last_latitude=16.0,
            last_longitude=76.0,
        )
        res = validator.validate(r_inside)
        assert res.is_valid

        # Start coords outside bounds
        r_outside_start = CDRRecord(
            operator="airtel",
            target_number="9714499703",
            timestamp=ts,
            latitude=25.0,  # outside
            longitude=75.0,
        )
        res = validator.validate(r_outside_start)
        assert not res.is_valid
        assert any(e.code == "CDR_COORDS_OUT_OF_BOUNDS" for e in res.errors)

        # End coords outside bounds
        r_outside_end = CDRRecord(
            operator="airtel",
            target_number="9714499703",
            timestamp=ts,
            latitude=15.0,
            longitude=75.0,
            last_latitude=15.0,
            last_longitude=85.0,  # outside
        )
        res = validator.validate(r_outside_end)
        assert not res.is_valid
        assert any(e.code == "CDR_LAST_COORDS_OUT_OF_BOUNDS" for e in res.errors)


class TestCDRBatchValidator:
    """Tests batch-wide validations like duplicate record detection."""

    def test_duplicate_record_ids(self):
        ts = datetime.now(timezone.utc) - timedelta(minutes=5)
        records = [
            CDRRecord(id=101, operator="airtel", target_number="9714499703", timestamp=ts),
            CDRRecord(id=101, operator="bsnl", target_number="9477523061", timestamp=ts),  # duplicate ID
        ]
        res = validate_cdr_batch(records)
        assert not res.is_valid
        assert any(e.code == "CDR_DUPLICATE_ID" for e in res.errors)

    def test_duplicate_record_values(self):
        ts = datetime.now(timezone.utc) - timedelta(hours=2)
        records = [
            CDRRecord(
                operator="airtel",
                target_number="9714499703",
                timestamp=ts,
                first_cgi="404-98-8331-230711555",
            ),
            CDRRecord(
                operator="airtel",
                target_number="9714499703",
                timestamp=ts,
                first_cgi="404-98-8331-230711555",  # exact duplicate details
            ),
        ]
        res = validate_cdr_batch(records)
        assert not res.is_valid
        assert any(e.code == "CDR_DUPLICATE_RECORD" for e in res.errors)

    def test_no_duplicates_succeeds(self):
        ts1 = datetime.now(timezone.utc) - timedelta(hours=3)
        ts2 = ts1 + timedelta(seconds=1)
        records = [
            CDRRecord(
                operator="airtel",
                target_number="9714499703",
                timestamp=ts1,
                first_cgi="404-98-8331-230711555",
            ),
            # Different timestamp
            CDRRecord(
                operator="airtel",
                target_number="9714499703",
                timestamp=ts2,
                first_cgi="404-98-8331-230711555",
            ),
            # Different CGI
            CDRRecord(
                operator="airtel",
                target_number="9714499703",
                timestamp=ts1,
                first_cgi="404-98-8331-999999999",
            ),
            # Different target_number
            CDRRecord(
                operator="airtel",
                target_number="9876543210",
                timestamp=ts1,
                first_cgi="404-98-8331-230711555",
            ),
        ]
        res = validate_cdr_batch(records)
        assert res.is_valid
        assert len(res.errors) == 0
