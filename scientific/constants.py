"""
Scientific Constants
=====================

Physical, mathematical, and telecom-domain constants used throughout the
Asterion scientific engine.

This module is the **single source of truth** for every physical constant,
unit-conversion factor, and domain-specific reference value that the
simulation and validation subsystems rely on.

Organisation
-------------
Constants are grouped into logical sections:

1. **Physical & Mathematical** — speed of light, π, Boltzmann constant.
2. **Unit Conversion** — dB ↔ linear, degrees ↔ radians helpers.
3. **Earth / Geodesy** — WGS84 ellipsoid parameters, Haversine helpers.
4. **RF / Signal Propagation** — free-space path-loss reference, thermal
   noise, Boltzmann constant in dBm form.
5. **Cellular Frequency Bands** — canonical band centres and the
   tolerance window used for plausibility checks.
6. **RSSI Reference Levels** — human-readable signal-quality thresholds.
7. **Timing Advance (TA)** — GSM TA resolution and range.

Usage::

    >>> from scientific.constants import SPEED_OF_LIGHT_M_S, EARTH_RADIUS_M
    >>> wavelength = SPEED_OF_LIGHT_M_S / 1800e6   # λ at 1800 MHz
    >>> round(wavelength, 4)
    0.1667
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

# ═══════════════════════════════════════════════════════════════════════════
# 1. Physical & Mathematical Constants
# ═══════════════════════════════════════════════════════════════════════════

#: Speed of light in vacuum (m/s).  Used in free-space loss equations.
SPEED_OF_LIGHT_M_S: float = 299_792_458.0

#: Boltzmann constant (J/K).
BOLTZMANN_CONSTANT_J_K: float = 1.380649e-23

#: Boltzmann constant expressed in dBm/Hz/K for noise-floor calculations.
#:     k_dBm = 10·log10(k) + 30 ≈ -198.6 dBm/Hz/K
BOLTZMANN_DBM_HZ_K: float = 10 * math.log10(BOLTZMANN_CONSTANT_J_K) + 30

#: Pi — re-exported for convenience so callers don't need ``import math``.
PI: float = math.pi

#: Degrees-to-radians multiplier.
DEG_TO_RAD: float = math.pi / 180.0

#: Radians-to-degrees multiplier.
RAD_TO_DEG: float = 180.0 / math.pi


# ═══════════════════════════════════════════════════════════════════════════
# 2. Unit Conversion Helpers
# ═══════════════════════════════════════════════════════════════════════════


def db_to_linear(db: float) -> float:
    """Convert a value from decibels to linear scale.

    Args:
        db: Value in dB.

    Returns:
        Linear-scale value (10^(db/10)).
    """
    return 10.0 ** (db / 10.0)


def linear_to_db(linear: float) -> float:
    """Convert a value from linear scale to decibels.

    Args:
        linear: Positive linear-scale value.

    Returns:
        Value in dB (10·log10(linear)).

    Raises:
        ValueError: If *linear* ≤ 0.
    """
    if linear <= 0:
        raise ValueError(f"linear_to_db requires a positive value, got {linear}")
    return 10.0 * math.log10(linear)


def dbm_to_watts(dbm: float) -> float:
    """Convert power from dBm to Watts.

    Args:
        dbm: Power in dBm.

    Returns:
        Power in Watts.
    """
    return 10.0 ** ((dbm - 30.0) / 10.0)


def watts_to_dbm(watts: float) -> float:
    """Convert power from Watts to dBm.

    Args:
        watts: Power in Watts (must be > 0).

    Returns:
        Power in dBm.

    Raises:
        ValueError: If *watts* ≤ 0.
    """
    if watts <= 0:
        raise ValueError(f"watts_to_dbm requires a positive value, got {watts}")
    return 10.0 * math.log10(watts) + 30.0


# ═══════════════════════════════════════════════════════════════════════════
# 3. Earth / Geodesy (WGS84)
# ═══════════════════════════════════════════════════════════════════════════

#: WGS84 mean Earth radius in meters (used in Haversine approximation).
EARTH_RADIUS_M: float = 6_371_000.0

#: WGS84 semi-major axis (equatorial radius) in meters.
WGS84_SEMI_MAJOR_M: float = 6_378_137.0

#: WGS84 flattening factor (1/f).
WGS84_FLATTENING_INV: float = 298.257223563

#: Approximate meters-per-degree of latitude at mid-latitudes.
METERS_PER_DEGREE_LAT: float = 111_320.0

#: Coordinate bounds (WGS84).
LATITUDE_RANGE: Tuple[float, float] = (-90.0, 90.0)
LONGITUDE_RANGE: Tuple[float, float] = (-180.0, 180.0)


def haversine_distance_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Compute great-circle distance between two WGS84 points (meters).

    Uses the Haversine formula with :data:`EARTH_RADIUS_M`.

    Args:
        lat1: Latitude of point 1 (decimal degrees).
        lon1: Longitude of point 1 (decimal degrees).
        lat2: Latitude of point 2 (decimal degrees).
        lon2: Longitude of point 2 (decimal degrees).

    Returns:
        Distance in meters.
    """
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)

    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    )
    return EARTH_RADIUS_M * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ═══════════════════════════════════════════════════════════════════════════
# 4. RF / Signal Propagation
# ═══════════════════════════════════════════════════════════════════════════

#: Free-space path loss at 1 m reference distance and 1 GHz (dB).
#: FSPL(d₀=1m, f=1GHz) = 20·log10(4π·1·1e9 / c) ≈ 32.44 dB
FREE_SPACE_LOSS_1M_1GHZ_DB: float = 20.0 * math.log10(
    4.0 * math.pi * 1e9 / SPEED_OF_LIGHT_M_S
)

#: Thermal noise power at 290 K over 1 Hz bandwidth (dBm).
#: N = k·T·B  →  10·log10(1.38e-23 · 290 · 1) + 30 ≈ -174 dBm/Hz
THERMAL_NOISE_DBM_HZ: float = 10.0 * math.log10(BOLTZMANN_CONSTANT_J_K * 290.0) + 30.0

#: Typical cellular channel bandwidth (Hz) — used to estimate noise floor.
TYPICAL_CHANNEL_BW_HZ: float = 10e6  # 10 MHz (LTE)


# ═══════════════════════════════════════════════════════════════════════════
# 5. Cellular Frequency Bands
# ═══════════════════════════════════════════════════════════════════════════

#: Canonical centre frequencies of common cellular bands (MHz).
CELLULAR_BANDS_MHZ: List[int] = [
    # Low-band
    700,
    800,
    850,
    900,
    # Mid-band
    1700,
    1800,
    1900,
    2100,
    # Upper mid-band
    2300,
    2500,
    2600,
    # C-band (5G NR)
    3500,
    3700,
    # mmWave (5G NR)
    26000,
    28000,
    39000,
]

#: Tolerance (± MHz) used when checking whether a frequency is near a
#: known cellular band.
BAND_TOLERANCE_MHZ: float = 50.0

#: Human-readable band grouping for reporting.
BAND_GROUPS: Dict[str, Tuple[int, ...]] = {
    "low": (700, 800, 850, 900),
    "mid": (1700, 1800, 1900, 2100),
    "upper_mid": (2300, 2500, 2600),
    "c_band": (3500, 3700),
    "mmwave": (26000, 28000, 39000),
}


# ═══════════════════════════════════════════════════════════════════════════
# 6. RSSI Reference Levels
# ═══════════════════════════════════════════════════════════════════════════

#: Absolute RSSI bounds accepted by the Measurement model (dBm).
RSSI_ABSOLUTE_MIN_DBM: float = -150.0
RSSI_ABSOLUTE_MAX_DBM: float = 0.0

#: "Typical" cellular RSSI bounds for plausibility warnings (dBm).
RSSI_PLAUSIBLE_MIN_DBM: float = -120.0
RSSI_PLAUSIBLE_MAX_DBM: float = -30.0

#: Signal-quality tiers (upper-bound RSSI in dBm for each tier).
RSSI_QUALITY_TIERS: Dict[str, Tuple[float, float]] = {
    "excellent": (-50.0, 0.0),
    "good": (-70.0, -50.0),
    "fair": (-90.0, -70.0),
    "weak": (-110.0, -90.0),
    "very_weak": (-150.0, -110.0),
}


def rssi_quality_label(rssi_dbm: float) -> str:
    """Return a human-readable quality label for a given RSSI value.

    Args:
        rssi_dbm: Received signal strength in dBm.

    Returns:
        One of ``"excellent"``, ``"good"``, ``"fair"``, ``"weak"``,
        ``"very_weak"``, or ``"out_of_range"``.
    """
    for label, (low, high) in RSSI_QUALITY_TIERS.items():
        if low <= rssi_dbm <= high:
            return label
    return "out_of_range"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Timing Advance (GSM)
# ═══════════════════════════════════════════════════════════════════════════

#: GSM Timing Advance resolution — each TA unit ≈ 550 m round-trip,
#: which corresponds to ≈ 550 m one-way distance.
TA_RESOLUTION_M: float = 550.0

#: Maximum TA value in GSM (0–63).
TA_MAX_VALUE: int = 63

#: Maximum one-way distance estimable via TA (m).
TA_MAX_DISTANCE_M: float = TA_RESOLUTION_M * TA_MAX_VALUE


# ═══════════════════════════════════════════════════════════════════════════
# 8. Tower Parameter Defaults & Bounds
# ═══════════════════════════════════════════════════════════════════════════

#: Default antenna height above ground level (m).
DEFAULT_ANTENNA_HEIGHT_M: float = 30.0

#: Default operating frequency (MHz).
DEFAULT_FREQUENCY_MHZ: float = 1800.0

#: Default EIRP transmit power (dBm).
DEFAULT_TRANSMIT_POWER_DBM: float = 43.0

#: Default coverage radius (m).
DEFAULT_COVERAGE_RADIUS_M: float = 1_000.0

#: Realistic transmit power range (dBm).
MIN_TX_POWER_DBM: float = 10.0
MAX_TX_POWER_DBM: float = 60.0

#: Realistic antenna height range (m).
MIN_ANTENNA_HEIGHT_M: float = 1.0
MAX_ANTENNA_HEIGHT_M: float = 300.0

#: Maximum plausible coverage radius (m).
MAX_COVERAGE_RADIUS_M: float = 50_000.0

#: Default background noise floor (dBm).
DEFAULT_NOISE_FLOOR_DBM: float = -95.0
