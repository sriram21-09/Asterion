"""
Shared Input Validation Helpers
================================

Reusable validation utilities for the Asterion backend API layer.

These helpers are designed to be used across FastAPI route handlers,
middleware, and service functions. They complement Pydantic's field-level
validation with higher-level, cross-field, and business-rule checks that
are common to multiple endpoints.

Architecture Note
------------------
This module lives in ``backend/app/shared/`` and is intentionally separate
from ``scientific/validation/``:

- **scientific/validation**: Domain-specific, physics-aware validators
  (e.g. RSSI plausibility, tower geometry).
- **backend/app/shared/validation**: HTTP-layer helpers — ID formats,
  pagination bounds, coordinate sanitization, bulk payload limits.

Usage::

    from app.shared.validation import (
        validate_id_format,
        validate_coordinates,
        validate_pagination,
    )

    @router.get("/api/v1/scenarios/{scenario_id}")
    async def get_scenario(scenario_id: str):
        validate_id_format(scenario_id, prefix="SCN")
        ...
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Asterion ID pattern: PREFIX-ALPHANUMERIC (e.g., SCN-001, T001, M001)
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_]{0,63}$")

# Pagination defaults and limits
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Bulk payload limits
MAX_BULK_ITEMS = 500

# WGS84 coordinate bounds
LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0

# RSSI bounds (dBm)
RSSI_MIN, RSSI_MAX = -150.0, 0.0


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when input validation fails.

    Attributes:
        field: Name of the invalid field.
        message: Human-readable error description.
        status_code: HTTP status code to return (default 422).
    """

    def __init__(
        self,
        field: str,
        message: str,
        *,
        status_code: int = 422,
    ) -> None:
        self.field = field
        self.message = message
        self.status_code = status_code
        super().__init__(f"{field}: {message}")

    def to_http_exception(self) -> HTTPException:
        """Convert to a FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={"field": self.field, "message": self.message},
        )


# ---------------------------------------------------------------------------
# ID & string validators
# ---------------------------------------------------------------------------

def validate_id_format(
    value: str,
    field_name: str = "id",
    *,
    prefix: Optional[str] = None,
    min_length: int = 1,
    max_length: int = 64,
) -> str:
    """Validate that *value* is a well-formed Asterion identifier.

    Args:
        value: The ID string to validate.
        field_name: Name of the field (for error messages).
        prefix: If provided, the ID must start with this prefix
                (case-insensitive).
        min_length: Minimum allowed length.
        max_length: Maximum allowed length.

    Returns:
        The stripped, validated ID.

    Raises:
        ValidationError: If validation fails.
    """
    value = value.strip()
    if len(value) < min_length:
        raise ValidationError(
            field_name,
            f"ID must be at least {min_length} character(s) long.",
        )
    if len(value) > max_length:
        raise ValidationError(
            field_name,
            f"ID must be at most {max_length} characters long.",
        )
    if not _ID_PATTERN.match(value):
        raise ValidationError(
            field_name,
            "ID must start with an alphanumeric character and contain only "
            "letters, digits, hyphens, and underscores.",
        )
    if prefix and not value.upper().startswith(prefix.upper()):
        raise ValidationError(
            field_name,
            f"ID must start with prefix '{prefix}'.",
        )
    return value


def validate_non_empty_string(
    value: str,
    field_name: str,
    *,
    max_length: int = 500,
) -> str:
    """Validate that *value* is a non-empty, length-bounded string.

    Returns:
        The stripped, validated string.

    Raises:
        ValidationError: If the string is empty or exceeds max_length.
    """
    value = value.strip()
    if not value:
        raise ValidationError(field_name, "Value must not be empty.")
    if len(value) > max_length:
        raise ValidationError(
            field_name,
            f"Value must not exceed {max_length} characters.",
        )
    return value


# ---------------------------------------------------------------------------
# Coordinate validators
# ---------------------------------------------------------------------------

def validate_latitude(value: float, field_name: str = "latitude") -> float:
    """Validate that *value* is a valid WGS84 latitude.

    Raises:
        ValidationError: If outside [-90, 90].
    """
    if not (LAT_MIN <= value <= LAT_MAX):
        raise ValidationError(
            field_name,
            f"Latitude must be between {LAT_MIN} and {LAT_MAX}. Got {value}.",
        )
    return value


def validate_longitude(value: float, field_name: str = "longitude") -> float:
    """Validate that *value* is a valid WGS84 longitude.

    Raises:
        ValidationError: If outside [-180, 180].
    """
    if not (LON_MIN <= value <= LON_MAX):
        raise ValidationError(
            field_name,
            f"Longitude must be between {LON_MIN} and {LON_MAX}. Got {value}.",
        )
    return value


def validate_coordinates(
    latitude: float,
    longitude: float,
    *,
    lat_field: str = "latitude",
    lon_field: str = "longitude",
) -> Tuple[float, float]:
    """Validate a latitude/longitude pair.

    Returns:
        A ``(latitude, longitude)`` tuple.

    Raises:
        ValidationError: If either coordinate is out of bounds.
    """
    validate_latitude(latitude, lat_field)
    validate_longitude(longitude, lon_field)
    return (latitude, longitude)


def validate_coordinate_pair_optional(
    latitude: Optional[float],
    longitude: Optional[float],
    *,
    lat_field: str = "latitude",
    lon_field: str = "longitude",
) -> Tuple[Optional[float], Optional[float]]:
    """Validate that optional lat/lon are provided together or not at all.

    Returns:
        A ``(latitude, longitude)`` tuple (both may be ``None``).

    Raises:
        ValidationError: If only one of lat/lon is provided, or if
                         values are out of bounds.
    """
    has_lat = latitude is not None
    has_lon = longitude is not None
    if has_lat != has_lon:
        raise ValidationError(
            f"{lat_field}/{lon_field}",
            "Latitude and longitude must both be provided or both be omitted.",
        )
    if has_lat and has_lon:
        validate_latitude(latitude, lat_field)  # type: ignore[arg-type]
        validate_longitude(longitude, lon_field)  # type: ignore[arg-type]
    return (latitude, longitude)


# ---------------------------------------------------------------------------
# Numeric validators
# ---------------------------------------------------------------------------

def validate_rssi(
    value: float,
    field_name: str = "rssi_dbm",
) -> float:
    """Validate that *value* is within the accepted RSSI range.

    Raises:
        ValidationError: If outside [-150, 0] dBm.
    """
    if not (RSSI_MIN <= value <= RSSI_MAX):
        raise ValidationError(
            field_name,
            f"RSSI must be between {RSSI_MIN} and {RSSI_MAX} dBm. Got {value}.",
        )
    return value


def validate_positive_float(
    value: float,
    field_name: str,
    *,
    allow_zero: bool = False,
) -> float:
    """Validate that *value* is a positive number.

    Args:
        value: The numeric value to check.
        field_name: Field name for error messages.
        allow_zero: If ``True``, zero is accepted.

    Raises:
        ValidationError: If the value is negative (or zero when not allowed).
    """
    if allow_zero and value < 0:
        raise ValidationError(field_name, f"Value must be >= 0. Got {value}.")
    if not allow_zero and value <= 0:
        raise ValidationError(field_name, f"Value must be > 0. Got {value}.")
    return value


# ---------------------------------------------------------------------------
# Pagination validators
# ---------------------------------------------------------------------------

def validate_pagination(
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Tuple[int, int]:
    """Normalize and validate pagination parameters.

    Returns:
        A ``(page, page_size)`` tuple with defaults applied.

    Raises:
        ValidationError: If page < 1 or page_size is out of [1, MAX_PAGE_SIZE].
    """
    if page is None:
        page = DEFAULT_PAGE
    if page_size is None:
        page_size = DEFAULT_PAGE_SIZE

    if page < 1:
        raise ValidationError("page", "Page number must be >= 1.")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise ValidationError(
            "page_size",
            f"Page size must be between 1 and {MAX_PAGE_SIZE}.",
        )
    return (page, page_size)


def pagination_offset(page: int, page_size: int) -> int:
    """Compute the SQL OFFSET for a given page and page_size."""
    return (page - 1) * page_size


# ---------------------------------------------------------------------------
# Bulk / collection validators
# ---------------------------------------------------------------------------

def validate_list_not_empty(
    items: Sequence[Any],
    field_name: str,
    *,
    max_items: int = MAX_BULK_ITEMS,
    min_items: int = 1,
) -> Sequence[Any]:
    """Validate that a list is non-empty and within size bounds.

    Args:
        items: The list to validate.
        field_name: Field name for error messages.
        max_items: Upper bound on list length.
        min_items: Lower bound on list length.

    Raises:
        ValidationError: If the list length is out of bounds.
    """
    if len(items) < min_items:
        raise ValidationError(
            field_name,
            f"Must contain at least {min_items} item(s). Got {len(items)}.",
        )
    if len(items) > max_items:
        raise ValidationError(
            field_name,
            f"Must contain at most {max_items} items. Got {len(items)}.",
        )
    return items


def validate_unique_ids(
    items: Sequence[Dict[str, Any]],
    id_field: str,
    collection_name: str = "items",
) -> List[str]:
    """Check that all *id_field* values are unique across *items*.

    Returns:
        The list of extracted IDs.

    Raises:
        ValidationError: If duplicates are found.
    """
    ids: List[str] = []
    seen: set[str] = set()
    duplicates: List[str] = []
    for item in items:
        val = str(item.get(id_field, ""))
        if val in seen:
            duplicates.append(val)
        seen.add(val)
        ids.append(val)
    if duplicates:
        raise ValidationError(
            collection_name,
            f"Duplicate {id_field} values found: {duplicates}.",
        )
    return ids


# ---------------------------------------------------------------------------
# Timestamp validators
# ---------------------------------------------------------------------------

def validate_timestamp_not_future(
    ts: datetime,
    field_name: str = "timestamp",
) -> datetime:
    """Validate that *ts* is not in the future.

    Raises:
        ValidationError: If the timestamp is in the future.
    """
    now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if ts > now:
        raise ValidationError(
            field_name,
            f"Timestamp {ts.isoformat()} is in the future.",
        )
    return ts


def validate_timestamp_range(
    start: datetime,
    end: datetime,
    *,
    start_field: str = "start_time",
    end_field: str = "end_time",
) -> Tuple[datetime, datetime]:
    """Validate that *start* ≤ *end*.

    Raises:
        ValidationError: If start is after end.
    """
    if start > end:
        raise ValidationError(
            f"{start_field}/{end_field}",
            f"Start time ({start.isoformat()}) must be before or equal to "
            f"end time ({end.isoformat()}).",
        )
    return (start, end)


# ---------------------------------------------------------------------------
# Signal-count validators (for localization API)
# ---------------------------------------------------------------------------

def validate_minimum_signals(
    signals: Sequence[Any],
    min_count: int = 3,
    field_name: str = "signals",
) -> Sequence[Any]:
    """Validate that enough signals are provided for localization.

    The minimum is typically 3 for multilateration (trilateration).

    Raises:
        ValidationError: If fewer than *min_count* signals provided.
    """
    if len(signals) < min_count:
        raise ValidationError(
            field_name,
            f"At least {min_count} signals are required for localization. "
            f"Got {len(signals)}.",
            status_code=400,
        )
    return signals
