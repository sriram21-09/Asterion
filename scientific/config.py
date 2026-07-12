"""
Scientific Configuration
=========================

Central configuration module for the Asterion scientific engine.

Provides simulation bounds, validation thresholds, algorithm defaults,
and environment-specific presets used throughout the pipeline.  All
configuration objects are **frozen dataclasses** so they can be used
safely across threads and remain hashable.

Design Principles
------------------
1. **Single source of truth** — every numeric threshold in the pipeline
   is defined here, not scattered across validators / models.
2. **Immutable by default** — frozen dataclasses prevent accidental
   mutation during long-running simulation batches.
3. **Environment-aware** — ``get_environment_config()`` returns presets
   tuned for urban / suburban / rural / highway deployments.
4. **Override-friendly** — ``SimulationConfig.override()`` returns a
   *new* instance with selected fields replaced (useful for parameter
   sweeps in Week 2).

Usage::

    >>> from scientific.config import (
    ...     SimulationConfig,
    ...     ValidationThresholds,
    ...     get_environment_config,
    ... )
    >>> cfg = SimulationConfig()
    >>> cfg.max_iterations
    100
    >>> thresholds = ValidationThresholds()
    >>> thresholds.rssi_min_dbm
    -150.0
    >>> env_cfg = get_environment_config("rural")
    >>> env_cfg.path_loss_exponent
    2.5
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Literal, Tuple


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

EnvironmentType = Literal["urban", "suburban", "rural", "highway"]
AlgorithmType = Literal["multilateration", "kalman", "weighted_centroid", "hybrid"]


# ---------------------------------------------------------------------------
# Simulation configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SimulationConfig:
    """Top-level simulation engine settings.

    These values control the solver loop, convergence criteria, and
    output limits for every simulation run.

    Attributes:
        max_iterations: Upper bound on solver iterations.
        convergence_threshold_m: Stop when position delta falls below
            this distance (meters).
        default_measurement_count: Number of synthetic RSSI snapshots
            to generate per tower during simulation.
        enable_noise: Whether to inject Gaussian noise into synthetic
            measurements.
        default_random_seed: Seed for reproducibility (``None`` for
            non-deterministic runs).
        default_algorithm: Localization algorithm to run when none is
            explicitly requested.
        min_towers_for_localization: Minimum towers required for
            multilateration.
        max_towers_per_scenario: Safety cap on tower count.
        max_measurements_per_scenario: Safety cap on measurement count.
        position_clamp_lat: Latitude bounds ``(min, max)`` for result
            clamping (WGS84).
        position_clamp_lon: Longitude bounds ``(min, max)`` for result
            clamping (WGS84).
    """

    # Solver controls
    max_iterations: int = 100
    convergence_threshold_m: float = 1.0
    default_measurement_count: int = 1
    enable_noise: bool = True
    default_random_seed: int | None = None
    default_algorithm: AlgorithmType = "multilateration"

    # Structural limits
    min_towers_for_localization: int = 3
    max_towers_per_scenario: int = 50
    max_measurements_per_scenario: int = 5_000

    # Position clamping (WGS84)
    position_clamp_lat: Tuple[float, float] = (-90.0, 90.0)
    position_clamp_lon: Tuple[float, float] = (-180.0, 180.0)

    def override(self, **kwargs) -> SimulationConfig:
        """Return a *new* config with selected fields replaced.

        This is the preferred way to tweak simulation settings for
        parameter sweeps or test fixtures without mutating the global
        default.

        Example::

            >>> cfg = SimulationConfig()
            >>> fast = cfg.override(max_iterations=10, enable_noise=False)
            >>> fast.max_iterations
            10
        """
        return replace(self, **kwargs)


# ---------------------------------------------------------------------------
# Validation thresholds
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationThresholds:
    """Domain-specific thresholds used by scientific validators.

    Groups every magic number that appears in
    :mod:`scientific.validation.validators` into a single importable
    location.

    Attributes:
        rssi_min_dbm: Absolute minimum RSSI (dBm) accepted by the model.
        rssi_max_dbm: Absolute maximum RSSI (dBm) accepted by the model.
        rssi_plausible_min_dbm: Lower bound of "typical" cellular RSSI.
        rssi_plausible_max_dbm: Upper bound of "typical" cellular RSSI.
        latitude_range: Valid WGS84 latitude ``(min, max)``.
        longitude_range: Valid WGS84 longitude ``(min, max)``.
        min_tx_power_dbm: Minimum realistic transmit power.
        max_tx_power_dbm: Maximum realistic transmit power.
        min_antenna_height_m: Minimum realistic antenna height.
        max_antenna_height_m: Maximum realistic antenna height.
        max_coverage_radius_m: Plausible coverage radius ceiling.
        max_measurement_age_days: Staleness threshold for timestamps.
        band_tolerance_mhz: Tolerance when matching known cellular bands.
        ta_rssi_ta_threshold: Timing advance threshold for TA/RSSI
            consistency check.
        ta_rssi_rssi_threshold_dbm: RSSI threshold (dBm) for TA/RSSI
            consistency check.
        min_confidence_score: Floor for confidence scores.
        max_confidence_score: Ceiling for confidence scores.
        gdop_excellent: GDOP ≤ this is "excellent" geometry.
        gdop_good: GDOP ≤ this is "good" geometry.
        gdop_poor: GDOP above this indicates poor geometry.
    """

    # RSSI bounds (dBm)
    rssi_min_dbm: float = -150.0
    rssi_max_dbm: float = 0.0
    rssi_plausible_min_dbm: float = -120.0
    rssi_plausible_max_dbm: float = -30.0

    # Coordinate bounds (WGS84)
    latitude_range: Tuple[float, float] = (-90.0, 90.0)
    longitude_range: Tuple[float, float] = (-180.0, 180.0)

    # Tower RF plausibility
    min_tx_power_dbm: float = 10.0
    max_tx_power_dbm: float = 60.0
    min_antenna_height_m: float = 1.0
    max_antenna_height_m: float = 300.0
    max_coverage_radius_m: float = 50_000.0

    # Timestamp sanity
    max_measurement_age_days: int = 365 * 5  # 5 years

    # Frequency band matching
    band_tolerance_mhz: float = 50.0

    # TA ↔ RSSI consistency thresholds
    ta_rssi_ta_threshold: float = 10.0
    ta_rssi_rssi_threshold_dbm: float = -50.0

    # Confidence scoring
    min_confidence_score: float = 0.0
    max_confidence_score: float = 1.0
    gdop_excellent: float = 2.0
    gdop_good: float = 5.0
    gdop_poor: float = 10.0


# ---------------------------------------------------------------------------
# Environment-specific configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EnvironmentConfig:
    """Propagation and noise parameters tuned for a specific environment.

    Attributes:
        environment_type: Environment classification label.
        path_loss_exponent: Rate of signal decay with distance.
        shadow_fading_std_db: Log-normal shadowing standard deviation (dB).
        reference_distance_m: Free-space reference distance d₀ (m).
        reference_loss_db: Path loss at d₀ (dB).
        typical_noise_floor_dbm: Expected background noise floor (dBm).
        typical_coverage_radius_m: Representative coverage radius (m).
    """

    environment_type: EnvironmentType = "urban"
    path_loss_exponent: float = 3.5
    shadow_fading_std_db: float = 8.0
    reference_distance_m: float = 1.0
    reference_loss_db: float = 38.0
    typical_noise_floor_dbm: float = -95.0
    typical_coverage_radius_m: float = 1_000.0


# Pre-built environment presets (immutable registry)
ENVIRONMENT_PRESETS: Dict[EnvironmentType, EnvironmentConfig] = {
    "urban": EnvironmentConfig(
        environment_type="urban",
        path_loss_exponent=3.5,
        shadow_fading_std_db=8.0,
        reference_distance_m=1.0,
        reference_loss_db=38.0,
        typical_noise_floor_dbm=-95.0,
        typical_coverage_radius_m=1_000.0,
    ),
    "suburban": EnvironmentConfig(
        environment_type="suburban",
        path_loss_exponent=3.0,
        shadow_fading_std_db=6.0,
        reference_distance_m=1.0,
        reference_loss_db=36.0,
        typical_noise_floor_dbm=-98.0,
        typical_coverage_radius_m=2_000.0,
    ),
    "rural": EnvironmentConfig(
        environment_type="rural",
        path_loss_exponent=2.5,
        shadow_fading_std_db=4.0,
        reference_distance_m=1.0,
        reference_loss_db=32.0,
        typical_noise_floor_dbm=-100.0,
        typical_coverage_radius_m=5_000.0,
    ),
    "highway": EnvironmentConfig(
        environment_type="highway",
        path_loss_exponent=2.8,
        shadow_fading_std_db=5.0,
        reference_distance_m=1.0,
        reference_loss_db=34.0,
        typical_noise_floor_dbm=-97.0,
        typical_coverage_radius_m=3_000.0,
    ),
}


def get_environment_config(env: EnvironmentType) -> EnvironmentConfig:
    """Return the preset :class:`EnvironmentConfig` for a given environment.

    Falls back to ``"urban"`` if *env* is not recognized.

    Args:
        env: One of ``"urban"``, ``"suburban"``, ``"rural"``, ``"highway"``.

    Returns:
        A frozen :class:`EnvironmentConfig` instance.
    """
    return ENVIRONMENT_PRESETS.get(env, ENVIRONMENT_PRESETS["urban"])


# ---------------------------------------------------------------------------
# Module-level convenience instances
# ---------------------------------------------------------------------------

#: Default simulation configuration (importable as a ready-to-use singleton).
DEFAULT_SIMULATION_CONFIG = SimulationConfig()

#: Default validation thresholds (importable as a ready-to-use singleton).
DEFAULT_VALIDATION_THRESHOLDS = ValidationThresholds()
