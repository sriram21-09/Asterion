"""
Tower Data Model
================

Defines the schema for a cell tower used in telecom localization scenarios.
Each tower represents a fixed base station with known coordinates, antenna
characteristics, and coverage parameters.

Example:
    >>> from scientific.models.tower import Tower
    >>> tower = Tower(
    ...     tower_id="T001",
    ...     latitude=12.9716,
    ...     longitude=77.5946,
    ...     antenna_height_m=35.0,
    ...     frequency_mhz=1800.0,
    ...     transmit_power_dbm=43.0,
    ...     sector="A",
    ...     coverage_radius_m=1200.0,
    ... )
"""

from typing import Optional

from pydantic import BaseModel, Field


class Tower(BaseModel):
    """Schema for a single cell tower in a localization scenario.

    Attributes:
        tower_id: Unique cell tower identifier (e.g., ``"T001"``).
        latitude: Tower latitude in decimal degrees (WGS84).
        longitude: Tower longitude in decimal degrees (WGS84).
        antenna_height_m: Antenna height above ground level in meters.
        frequency_mhz: Operating frequency in MHz.
        transmit_power_dbm: Effective Isotropic Radiated Power (EIRP) in dBm.
        sector: Optional sector identifier (e.g., ``"A"``, ``"B"``, ``"C"``).
        coverage_radius_m: Effective coverage radius in meters.
    """

    tower_id: str = Field(
        ...,
        min_length=1,
        description="Unique cell tower identifier (e.g., 'T001')",
        examples=["T001"],
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Tower latitude in decimal degrees (WGS84)",
        examples=[12.9716],
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Tower longitude in decimal degrees (WGS84)",
        examples=[77.5946],
    )
    antenna_height_m: float = Field(
        default=30.0,
        gt=0,
        description="Antenna height above ground level in meters",
    )
    frequency_mhz: float = Field(
        default=1800.0,
        gt=0,
        description="Operating frequency in MHz",
    )
    transmit_power_dbm: float = Field(
        default=43.0,
        description="Effective Isotropic Radiated Power (EIRP) in dBm",
    )
    sector: Optional[str] = Field(
        default=None,
        description="Sector identifier (e.g., 'A', 'B', 'C')",
        examples=["A"],
    )
    coverage_radius_m: float = Field(
        default=1000.0,
        gt=0,
        description="Effective coverage radius in meters",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tower_id": "T001",
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "antenna_height_m": 35.0,
                    "frequency_mhz": 1800.0,
                    "transmit_power_dbm": 43.0,
                    "sector": "A",
                    "coverage_radius_m": 1200.0,
                }
            ]
        }
    }
