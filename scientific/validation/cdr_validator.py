"""
CDR Record Validator & CDR Validation Service
============================================
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

from scientific.config import ValidationThresholds, DEFAULT_VALIDATION_THRESHOLDS
from scientific.models.cdr_record import CDRRecord
from scientific.validation.types import Severity, ValidationError, ValidationResult


class CDRRecordValidator:
    """Validates a single :class:`CDRRecord` instance.

    Checks:
        1. Required fields presence (operator, target_number, timestamp).
        2. Valid operator (must be case-insensitively one of airtel, bsnl, jio, vi).
        3. Coordinates operational bounds check (for latitude/longitude and last_latitude/last_longitude).
        4. Coordinate parity (both lat/lon must be provided or both must be omitted).
        5. Future timestamp check.
        6. Stale timestamp check (older than thresholds.max_measurement_age_days).
        7. Timestamp format (missing seconds warning, e.g. HH:MM instead of HH:MM:SS).
    """

    def __init__(
        self, thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS
    ) -> None:
        self.thresholds = thresholds

    def validate(self, record: CDRRecord) -> ValidationResult:
        result = ValidationResult()

        # 1. Presence checks
        if not getattr(record, "operator", None):
            result.errors.append(
                ValidationError(
                    field="operator",
                    message="Operator must be provided.",
                    severity=Severity.ERROR,
                    code="CDR_INVALID_OPERATOR",
                )
            )

        if (
            not getattr(record, "target_number", None)
            or not str(record.target_number).strip()
        ):
            result.errors.append(
                ValidationError(
                    field="target_number",
                    message="Target number must be provided and non-empty.",
                    severity=Severity.ERROR,
                    code="CDR_MISSING_TARGET_NUMBER",
                )
            )

        if getattr(record, "timestamp", None) is None:
            result.errors.append(
                ValidationError(
                    field="timestamp",
                    message="Timestamp must be provided.",
                    severity=Severity.ERROR,
                    code="CDR_MISSING_TIMESTAMP",
                )
            )

        # Stop early if required fields are missing/invalid to prevent secondary validation errors
        if not result.is_valid:
            return result

        # 2. Operator validation
        valid_operators = {"airtel", "bsnl", "jio", "vi"}
        op_lower = record.operator.lower()
        if op_lower not in valid_operators:
            result.errors.append(
                ValidationError(
                    field="operator",
                    message=f"Operator '{record.operator}' is not supported. Must be one of: airtel, bsnl, jio, vi.",
                    severity=Severity.ERROR,
                    code="CDR_INVALID_OPERATOR",
                )
            )

        # 3 & 4. Coordinate checks for start location
        lat = record.latitude
        lon = record.longitude
        has_lat = lat is not None
        has_lon = lon is not None

        if has_lat != has_lon:
            result.errors.append(
                ValidationError(
                    field="latitude/longitude",
                    message="Latitude and longitude must both be provided or both be omitted.",
                    severity=Severity.ERROR,
                    code="CDR_PARTIAL_COORDS",
                )
            )
        elif has_lat and has_lon:
            lat_min, lat_max = self.thresholds.latitude_range
            lon_min, lon_max = self.thresholds.longitude_range
            if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
                result.errors.append(
                    ValidationError(
                        field="latitude/longitude",
                        message=f"Coordinates ({lat}, {lon}) are outside valid WGS84 bounds.",
                        severity=Severity.ERROR,
                        code="CDR_COORDS_OUT_OF_BOUNDS",
                    )
                )
            elif not (lat_min <= lat <= lat_max) or not (lon_min <= lon <= lon_max):
                result.errors.append(
                    ValidationError(
                        field="latitude/longitude",
                        message=f"Coordinates ({lat}, {lon}) are outside operational ranges.",
                        severity=Severity.ERROR,
                        code="CDR_COORDS_OUT_OF_BOUNDS",
                    )
                )

        # 3 & 4. Coordinate checks for end location (last_latitude / last_longitude)
        last_lat = record.last_latitude
        last_lon = record.last_longitude
        has_last_lat = last_lat is not None
        has_last_lon = last_lon is not None

        if has_last_lat != has_last_lon:
            result.errors.append(
                ValidationError(
                    field="last_latitude/last_longitude",
                    message="Last latitude and last longitude must both be provided or both be omitted.",
                    severity=Severity.ERROR,
                    code="CDR_PARTIAL_LAST_COORDS",
                )
            )
        elif has_last_lat and has_last_lon:
            lat_min, lat_max = self.thresholds.latitude_range
            lon_min, lon_max = self.thresholds.longitude_range
            if not (-90.0 <= last_lat <= 90.0) or not (-180.0 <= last_lon <= 180.0):
                result.errors.append(
                    ValidationError(
                        field="last_latitude/last_longitude",
                        message=f"Last coordinates ({last_lat}, {last_lon}) are outside valid WGS84 bounds.",
                        severity=Severity.ERROR,
                        code="CDR_LAST_COORDS_OUT_OF_BOUNDS",
                    )
                )
            elif not (lat_min <= last_lat <= lat_max) or not (
                lon_min <= last_lon <= lon_max
            ):
                result.errors.append(
                    ValidationError(
                        field="last_latitude/last_longitude",
                        message=f"Last coordinates ({last_lat}, {last_lon}) are outside operational ranges.",
                        severity=Severity.ERROR,
                        code="CDR_LAST_COORDS_OUT_OF_BOUNDS",
                    )
                )

        # 5, 6, & 7. Timestamp validation
        if record.timestamp is not None:
            dt = record.timestamp
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            now_utc = datetime.now(timezone.utc)
            if dt > now_utc:
                result.errors.append(
                    ValidationError(
                        field="timestamp",
                        message=f"Timestamp {dt} is in the future relative to current time {now_utc}.",
                        severity=Severity.ERROR,
                        code="CDR_FUTURE_TIMESTAMP",
                    )
                )

            age_days = (now_utc - dt).days
            if age_days > self.thresholds.max_measurement_age_days:
                result.errors.append(
                    ValidationError(
                        field="timestamp",
                        message=f"Timestamp age ({age_days} days) exceeds maximum age threshold ({self.thresholds.max_measurement_age_days} days).",
                        severity=Severity.WARNING,
                        code="CDR_STALE_TIMESTAMP",
                    )
                )

            missing_seconds = False
            if record.raw_data and isinstance(record.raw_data, dict):
                row = record.raw_data.get("row")
                if isinstance(row, list) and len(row) > 7:
                    time_val = str(row[7]).strip().strip("'").strip('"')
                    if time_val and ":" in time_val and time_val.count(":") == 1:
                        if re.match(r"^\d{1,2}:\d{2}$", time_val) or re.match(
                            r"^\d{1,2}:\d{2}\s*(?:AM|PM)?$", time_val, re.IGNORECASE
                        ):
                            missing_seconds = True

            if missing_seconds:
                result.errors.append(
                    ValidationError(
                        field="timestamp",
                        message="Timestamp is missing seconds component.",
                        severity=Severity.WARNING,
                        code="CDR_TIMESTAMP_MISSING_SECONDS",
                    )
                )

        return result


def validate_cdr_batch(
    records: List[CDRRecord],
    *,
    thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
) -> ValidationResult:
    """Validate a batch of CDR records, including checking for duplicates."""
    result = ValidationResult()
    validator = CDRRecordValidator(thresholds=thresholds)

    for idx, record in enumerate(records):
        sub_res = validator.validate(record)
        for err in sub_res.errors:
            result.errors.append(
                ValidationError(
                    field=f"records[{idx}].{err.field}",
                    message=err.message,
                    severity=err.severity,
                    code=err.code,
                )
            )

    seen_ids = set()
    for idx, record in enumerate(records):
        if record.id is not None:
            if record.id in seen_ids:
                result.errors.append(
                    ValidationError(
                        field=f"records[{idx}].id",
                        message=f"Duplicate record ID found: {record.id}",
                        severity=Severity.ERROR,
                        code="CDR_DUPLICATE_ID",
                    )
                )
            seen_ids.add(record.id)

    seen_records = {}
    for idx, record in enumerate(records):
        if record.target_number and record.timestamp:
            key = (record.target_number, record.timestamp, record.first_cgi)
            if key in seen_records:
                orig_idx = seen_records[key]
                result.errors.append(
                    ValidationError(
                        field=f"records[{idx}]",
                        message=(
                            f"Duplicate record detected. Same target_number, timestamp, "
                            f"and first_cgi as records[{orig_idx}]."
                        ),
                        severity=Severity.ERROR,
                        code="CDR_DUPLICATE_RECORD",
                    )
                )
            else:
                seen_records[key] = idx

    return result


@dataclass
class CDRDataQualityScore:
    """Quantitative quality assessment for a CDR import batch."""

    overall_score: float
    validity_score: float
    completeness_score: float
    consistency_score: float
    timeliness_score: float
    grade: str

    _W_VALIDITY: float = field(default=0.40, init=False, repr=False, compare=False)
    _W_COMPLETENESS: float = field(default=0.25, init=False, repr=False, compare=False)
    _W_CONSISTENCY: float = field(default=0.20, init=False, repr=False, compare=False)
    _W_TIMELINESS: float = field(default=0.15, init=False, repr=False, compare=False)

    @staticmethod
    def grade_from_score(score: float) -> str:
        if score >= 0.95:
            return "Excellent"
        if score >= 0.80:
            return "Good"
        if score >= 0.60:
            return "Fair"
        if score >= 0.40:
            return "Poor"
        return "Critical"


@dataclass
class CDRValidationReport:
    """Structured report produced by :class:`CDRValidationService` for a batch."""

    total_records: int
    valid_count: int
    rejected_count: int
    warning_count: int
    failure_categories: Dict[str, int]
    warning_categories: Dict[str, int]
    per_record_results: List[ValidationResult]
    quality_score: CDRDataQualityScore

    @property
    def is_valid(self) -> bool:
        return self.rejected_count == 0

    def summary(self) -> str:
        return (
            f"CDRValidationReport | total={self.total_records} "
            f"valid={self.valid_count} rejected={self.rejected_count} "
            f"warnings={self.warning_count} "
            f"quality={self.quality_score.overall_score:.2f} "
            f"grade={self.quality_score.grade}"
        )


_CDR_COMPLETENESS_FIELDS = (
    "operator",
    "target_number",
    "timestamp",
    "latitude",
    "longitude",
    "first_cgi",
)


class CDRValidationService:
    """Orchestrates CDR validation across import batches."""

    def __init__(
        self,
        thresholds: ValidationThresholds = DEFAULT_VALIDATION_THRESHOLDS,
    ) -> None:
        self.thresholds = thresholds
        self._record_validator = CDRRecordValidator(thresholds=thresholds)

    def validate_batch(self, records: List[CDRRecord]) -> CDRValidationReport:
        if not records:
            empty_score = CDRDataQualityScore(
                overall_score=1.0,
                validity_score=1.0,
                completeness_score=1.0,
                consistency_score=1.0,
                timeliness_score=1.0,
                grade="Excellent",
            )
            return CDRValidationReport(
                total_records=0,
                valid_count=0,
                rejected_count=0,
                warning_count=0,
                failure_categories={},
                warning_categories={},
                per_record_results=[],
                quality_score=empty_score,
            )

        per_record_results: List[ValidationResult] = []
        for record in records:
            per_record_results.append(self._record_validator.validate(record))

        duplicate_id_indices: set[int] = set()
        duplicate_record_indices: set[int] = set()

        seen_ids: Dict[int, int] = {}
        seen_keys: Dict[tuple, int] = {}

        for idx, record in enumerate(records):
            if record.id is not None:
                if record.id in seen_ids:
                    dup_err = ValidationError(
                        field="id",
                        message=f"Duplicate record ID found: {record.id}",
                        severity=Severity.ERROR,
                        code="CDR_DUPLICATE_ID",
                    )
                    per_record_results[idx].errors.append(dup_err)
                    duplicate_id_indices.add(idx)
                else:
                    seen_ids[record.id] = idx

            if record.target_number and record.timestamp:
                key = (record.target_number, record.timestamp, record.first_cgi)
                if key in seen_keys:
                    dup_err = ValidationError(
                        field="target_number/timestamp/first_cgi",
                        message=(
                            f"Duplicate record detected. Same target_number, timestamp, "
                            f"and first_cgi as records[{seen_keys[key]}]."
                        ),
                        severity=Severity.ERROR,
                        code="CDR_DUPLICATE_RECORD",
                    )
                    per_record_results[idx].errors.append(dup_err)
                    duplicate_record_indices.add(idx)
                else:
                    seen_keys[key] = idx

        valid_count = 0
        rejected_count = 0
        warning_count = 0
        failure_categories: Dict[str, int] = {}
        warning_categories: Dict[str, int] = {}

        for res in per_record_results:
            has_error = not res.is_valid
            if has_error:
                rejected_count += 1
            else:
                valid_count += 1

            for err in res.errors:
                code = err.code or "UNKNOWN"
                if err.severity == Severity.ERROR:
                    failure_categories[code] = failure_categories.get(code, 0) + 1
                elif err.severity == Severity.WARNING:
                    warning_categories[code] = warning_categories.get(code, 0) + 1
                    warning_count += 1

        total_duplicates = len(duplicate_id_indices | duplicate_record_indices)
        quality_score = self._calculate_quality_score(
            records=records,
            per_record_results=per_record_results,
            valid_count=valid_count,
            total_duplicates=total_duplicates,
        )

        return CDRValidationReport(
            total_records=len(records),
            valid_count=valid_count,
            rejected_count=rejected_count,
            warning_count=warning_count,
            failure_categories=failure_categories,
            warning_categories=warning_categories,
            per_record_results=per_record_results,
            quality_score=quality_score,
        )

    def _calculate_quality_score(
        self,
        records: List[CDRRecord],
        per_record_results: List[ValidationResult],
        valid_count: int,
        total_duplicates: int,
    ) -> CDRDataQualityScore:
        n = len(records)

        validity_score = valid_count / n
        completeness_score = self._compute_completeness(records)
        consistency_score = max(0.0, 1.0 - (total_duplicates / n))
        timeliness_score = self._compute_timeliness(records)

        overall = (
            0.40 * validity_score
            + 0.25 * completeness_score
            + 0.20 * consistency_score
            + 0.15 * timeliness_score
        )
        overall = max(0.0, min(1.0, overall))

        return CDRDataQualityScore(
            overall_score=round(overall, 4),
            validity_score=round(validity_score, 4),
            completeness_score=round(completeness_score, 4),
            consistency_score=round(consistency_score, 4),
            timeliness_score=round(timeliness_score, 4),
            grade=CDRDataQualityScore.grade_from_score(overall),
        )

    def _compute_completeness(self, records: List[CDRRecord]) -> float:
        if not records:
            return 1.0
        total_ratio = 0.0
        n_fields = len(_CDR_COMPLETENESS_FIELDS)
        for record in records:
            present = sum(
                1
                for f in _CDR_COMPLETENESS_FIELDS
                if getattr(record, f, None) not in (None, "")
            )
            total_ratio += present / n_fields
        return total_ratio / len(records)

    def _compute_timeliness(self, records: List[CDRRecord]) -> float:
        if not records:
            return 1.0
        now_utc = datetime.now(timezone.utc)
        max_age_days = self.thresholds.max_measurement_age_days
        timely_count = 0
        for record in records:
            ts = record.timestamp
            if ts is None:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts <= now_utc and (now_utc - ts).days <= max_age_days:
                timely_count += 1
        return timely_count / len(records)
