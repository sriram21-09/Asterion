"""
Result Data Models
==================

Defines output schemas for the localization pipeline:

- **LocalizationResult**: The estimated device position produced by a
  localization algorithm (multilateration, Kalman filter, etc.).
- **ConfidenceResult**: A statistical confidence assessment of the
  localization estimate, including error ellipse parameters and GDOP.

These models are the outputs of the pipeline:

    Scenario → Algorithm → LocalizationResult → ConfidenceResult

Example:
    >>> from scientific.models.result import LocalizationResult, ConfidenceResult
    >>> from datetime import datetime, timezone
    >>> loc = LocalizationResult(
    ...     scenario_id="SCN-001",
    ...     algorithm="multilateration",
    ...     estimated_latitude=12.9722,
    ...     estimated_longitude=77.5949,
    ...     signals_used=3,
    ...     timestamp=datetime.now(timezone.utc),
    ... )
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# Supported localization algorithms
AlgorithmType = Literal["multilateration", "kalman", "weighted_centroid", "hybrid"]

# Confidence level classification
ConfidenceLevel = Literal["high", "medium", "low"]

# Confidence estimation methods
ConfidenceMethod = Literal["gdop", "residual_analysis", "bootstrap", "covariance"]


class LocalizationResult(BaseModel):
    """Schema for the output of a localization algorithm.

    Attributes:
        scenario_id: Identifier of the source scenario.
        algorithm: Name of the algorithm used.
        estimated_latitude: Estimated device latitude (WGS84).
        estimated_longitude: Estimated device longitude (WGS84).
        error_m: Error distance from ground truth in meters, if known.
        computation_time_ms: Processing time in milliseconds.
        signals_used: Number of tower signals used in computation.
        timestamp: When the result was computed.
    """

    scenario_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the source scenario",
        examples=["SCN-001"],
    )
    algorithm: AlgorithmType = Field(
        ...,
        description="Name of the localization algorithm used",
        examples=["multilateration"],
    )
    estimated_latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Estimated device latitude (WGS84)",
        examples=[12.9722],
    )
    estimated_longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Estimated device longitude (WGS84)",
        examples=[77.5949],
    )
    error_m: Optional[float] = Field(
        default=None,
        ge=0,
        description="Error distance from ground truth in meters",
        examples=[45.3],
    )
    computation_time_ms: Optional[float] = Field(
        default=None,
        ge=0,
        description="Processing time in milliseconds",
        examples=[12.5],
    )
    signals_used: int = Field(
        ...,
        ge=1,
        description="Number of tower signals used in computation",
        examples=[3],
    )
    timestamp: datetime = Field(
        ...,
        description="When the result was computed (ISO 8601)",
        examples=["2026-07-07T10:31:00Z"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scenario_id": "SCN-001",
                    "algorithm": "multilateration",
                    "estimated_latitude": 12.9722,
                    "estimated_longitude": 77.5949,
                    "error_m": 45.3,
                    "computation_time_ms": 12.5,
                    "signals_used": 3,
                    "timestamp": "2026-07-07T10:31:00Z",
                }
            ]
        }
    }


class ConfidenceResult(BaseModel):
    """Schema for a statistical confidence assessment of a localization result.

    The confidence result quantifies the reliability of a localization
    estimate using metrics like GDOP (Geometric Dilution of Precision)
    and error ellipse parameters.

    Attributes:
        scenario_id: Identifier of the source scenario.
        confidence_score: Overall confidence score (0.0 – 1.0).
        confidence_level: Categorical confidence classification.
        error_ellipse_semi_major_m: Semi-major axis of error ellipse (meters).
        error_ellipse_semi_minor_m: Semi-minor axis of error ellipse (meters).
        error_ellipse_orientation_deg: Orientation of the error ellipse (degrees).
        gdop: Geometric Dilution of Precision.
        method: Confidence estimation method used.
    """

    scenario_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the source scenario",
        examples=["SCN-001"],
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score (0.0 = no confidence, 1.0 = certain)",
        examples=[0.87],
    )
    confidence_level: ConfidenceLevel = Field(
        ...,
        description="Categorical confidence classification",
        examples=["high"],
    )
    error_ellipse_semi_major_m: Optional[float] = Field(
        default=None,
        ge=0,
        description="Semi-major axis of the error ellipse in meters",
        examples=[120.0],
    )
    error_ellipse_semi_minor_m: Optional[float] = Field(
        default=None,
        ge=0,
        description="Semi-minor axis of the error ellipse in meters",
        examples=[75.0],
    )
    error_ellipse_orientation_deg: Optional[float] = Field(
        default=None,
        ge=0,
        le=360.0,
        description="Orientation of the error ellipse in degrees from north",
        examples=[45.0],
    )
    gdop: Optional[float] = Field(
        default=None,
        ge=0,
        description="Geometric Dilution of Precision (lower = better geometry)",
        examples=[2.3],
    )
    method: ConfidenceMethod = Field(
        ...,
        description="Confidence estimation method used",
        examples=["gdop"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scenario_id": "SCN-001",
                    "confidence_score": 0.87,
                    "confidence_level": "high",
                    "error_ellipse_semi_major_m": 120.0,
                    "error_ellipse_semi_minor_m": 75.0,
                    "error_ellipse_orientation_deg": 45.0,
                    "gdop": 2.3,
                    "method": "gdop",
                }
            ]
        }
    }
