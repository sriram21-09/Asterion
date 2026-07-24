"""
Scenario Data Model
====================

Defines the schema for a localization scenario — a self-contained configuration
that bundles tower placements, signal measurements, environmental parameters,
and optional ground-truth device position for validation.

A scenario is the primary input unit to the localization pipeline:

    Scenario → Simulation → Localization → Result → Confidence

Example:
    >>> from scientific.models.scenario import Scenario
    >>> from scientific.models.tower import Tower
    >>> scenario = Scenario(
    ...     scenario_id="SCN-001",
    ...     name="Urban 3-Tower Test",
    ...     towers=[
    ...         Tower(tower_id="T001", latitude=12.9716, longitude=77.5946),
    ...         Tower(tower_id="T002", latitude=12.9750, longitude=77.5900),
    ...         Tower(tower_id="T003", latitude=12.9700, longitude=77.6000),
    ...     ],
    ...     environment_type="urban",
    ... )
"""

from typing import Literal

from pydantic import BaseModel, Field

from scientific.models.measurement import Measurement
from scientific.models.tower import Tower

# Supported environment types for signal propagation modeling
EnvironmentType = Literal["urban", "suburban", "rural", "highway"]


class Scenario(BaseModel):
    """Schema for a localization scenario configuration.

    A scenario groups towers, measurements, and environmental parameters
    into a single unit that can be fed into the localization pipeline.

    Attributes:
        scenario_id: Unique identifier for the scenario.
        name: Human-readable scenario name.
        description: Optional textual description.
        towers: List of tower configurations (minimum 3 for multilateration).
        measurements: List of signal measurements for this scenario.
        noise_level_dbm: Background noise level in dBm.
        environment_type: Environment classification for propagation modeling.
        expected_device_lat: Ground-truth device latitude (for validation).
        expected_device_lon: Ground-truth device longitude (for validation).
    """

    scenario_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the scenario",
        examples=["SCN-001"],
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Human-readable scenario name",
        examples=["Urban 3-Tower Test"],
    )
    description: str | None = Field(
        default=None,
        description="Optional textual description of the scenario",
    )
    towers: list[Tower] = Field(
        ...,
        min_length=3,
        description="Tower configurations (minimum 3 for multilateration)",
    )
    measurements: list[Measurement] = Field(
        default_factory=list,
        description="Signal measurements for this scenario",
    )
    noise_level_dbm: float = Field(
        default=-95.0,
        description="Background noise level in dBm",
    )
    environment_type: EnvironmentType = Field(
        default="urban",
        description="Environment classification: urban, suburban, rural, highway",
    )
    expected_device_lat: float | None = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Ground-truth device latitude for validation (WGS84)",
    )
    expected_device_lon: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Ground-truth device longitude for validation (WGS84)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scenario_id": "SCN-001",
                    "name": "Urban 3-Tower Test",
                    "description": "Basic urban multilateration with 3 towers",
                    "towers": [
                        {"tower_id": "T001", "latitude": 12.9716, "longitude": 77.5946},
                        {"tower_id": "T002", "latitude": 12.9750, "longitude": 77.5900},
                        {"tower_id": "T003", "latitude": 12.9700, "longitude": 77.6000},
                    ],
                    "measurements": [],
                    "noise_level_dbm": -95.0,
                    "environment_type": "urban",
                    "expected_device_lat": 12.9722,
                    "expected_device_lon": 77.5949,
                }
            ]
        }
    }
