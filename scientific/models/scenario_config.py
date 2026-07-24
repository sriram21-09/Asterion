"""
Scenario Configuration Model
==============================

Maps a localization scenario into simulation-ready input parameters.

This module bridges the :class:`~scientific.models.scenario.Scenario` data
model (which stores *what* a scenario contains) with the simulation engine
(which needs to know *how* to run it).  The separation lets the pipeline
evolve independently of the persistence layer.

Configuration Hierarchy
------------------------
::

    ScenarioConfig            ← top-level simulation input
    ├── TowerPlacement[]      ← tower positions + RF parameters
    ├── SimulationParameters  ← solver / iteration settings
    └── PropagationDefaults   ← environment-specific RF presets

Usage
------
Build a config from an existing :class:`Scenario`:

    >>> from scientific.models.scenario_config import ScenarioConfig
    >>> config = ScenarioConfig.from_scenario(scenario)

Or construct one directly for quick experimentation:

    >>> config = ScenarioConfig(
    ...     scenario_id="SCN-001",
    ...     name="Urban 3-Tower Test",
    ...     tower_placements=[...],
    ...     environment_type="urban",
    ... )
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from scientific.models.scenario import EnvironmentType

# ── Tower Placement ─────────────────────────────────────────────────────


class TowerPlacement(BaseModel):
    """Lightweight tower position for simulation input.

    This intentionally duplicates a subset of
    :class:`~scientific.models.tower.Tower` fields so that a
    ``ScenarioConfig`` can be serialized / deserialized without
    importing the full Tower model.

    Attributes:
        tower_id: Unique identifier matching the parent tower.
        latitude: Tower latitude in decimal degrees (WGS84).
        longitude: Tower longitude in decimal degrees (WGS84).
        antenna_height_m: Antenna height above ground level in meters.
        frequency_mhz: Operating frequency in MHz.
        transmit_power_dbm: EIRP in dBm.
        coverage_radius_m: Effective coverage radius in meters.
        sector: Optional sector identifier.
    """

    tower_id: str = Field(
        ...,
        min_length=1,
        description="Unique tower identifier",
        examples=["T001"],
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Tower latitude (WGS84)",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Tower longitude (WGS84)",
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
        description="EIRP in dBm",
    )
    coverage_radius_m: float = Field(
        default=1000.0,
        gt=0,
        description="Effective coverage radius in meters",
    )
    sector: str | None = Field(
        default=None,
        description="Sector identifier (e.g., 'A', 'B', 'C')",
    )


# ── Propagation Defaults ────────────────────────────────────────────────

# Pre-tuned defaults per environment.  Week 2 will expose these as
# overridable parameters; for now they provide sane starting points.
PROPAGATION_PRESETS: dict[str, dict] = {
    "urban": {
        "path_loss_exponent": 3.5,
        "shadow_fading_std_db": 8.0,
        "reference_distance_m": 1.0,
        "reference_loss_db": 38.0,
    },
    "suburban": {
        "path_loss_exponent": 3.0,
        "shadow_fading_std_db": 6.0,
        "reference_distance_m": 1.0,
        "reference_loss_db": 36.0,
    },
    "rural": {
        "path_loss_exponent": 2.5,
        "shadow_fading_std_db": 4.0,
        "reference_distance_m": 1.0,
        "reference_loss_db": 32.0,
    },
    "highway": {
        "path_loss_exponent": 2.8,
        "shadow_fading_std_db": 5.0,
        "reference_distance_m": 1.0,
        "reference_loss_db": 34.0,
    },
}


class PropagationDefaults(BaseModel):
    """Environment-specific RF propagation parameters.

    These defaults are used by the simulation engine to compute
    synthetic RSSI values from tower-to-device distances via a
    log-distance path-loss model.

    Attributes:
        path_loss_exponent: Rate at which signal decays with distance.
        shadow_fading_std_db: Standard deviation of log-normal shadowing.
        reference_distance_m: Reference distance for free-space loss.
        reference_loss_db: Path loss at the reference distance.
    """

    path_loss_exponent: float = Field(
        default=3.5,
        gt=0,
        description="Path-loss exponent (n) — higher = faster decay",
    )
    shadow_fading_std_db: float = Field(
        default=8.0,
        ge=0,
        description="Shadow-fading standard deviation in dB",
    )
    reference_distance_m: float = Field(
        default=1.0,
        gt=0,
        description="Reference distance d₀ in meters",
    )
    reference_loss_db: float = Field(
        default=38.0,
        description="Free-space path loss at d₀ in dB",
    )

    @classmethod
    def for_environment(cls, env: EnvironmentType) -> PropagationDefaults:
        """Return preset propagation defaults for a given environment.

        Args:
            env: One of ``"urban"``, ``"suburban"``, ``"rural"``, ``"highway"``.

        Returns:
            A :class:`PropagationDefaults` populated from
            :data:`PROPAGATION_PRESETS`.
        """
        return cls(**PROPAGATION_PRESETS.get(env, PROPAGATION_PRESETS["urban"]))


# ── Simulation Parameters ───────────────────────────────────────────────


class SimulationParameters(BaseModel):
    """Controls for the simulation / solver engine.

    These settings determine how the localization algorithm processes
    a scenario (iteration limits, convergence thresholds, etc.).
    They are separate from the *data* of a scenario to keep
    configuration DRY.

    Attributes:
        algorithm: Localization algorithm to run.
        max_iterations: Upper bound on solver iterations.
        convergence_threshold_m: Stop when position delta falls below
            this distance (meters).
        measurement_count: Number of synthetic RSSI snapshots to
            generate per tower during simulation.
        enable_noise: Whether to add Gaussian noise to synthetic
            measurements.
        random_seed: Optional seed for reproducible simulation runs.
    """

    algorithm: Literal["multilateration", "kalman", "weighted_centroid", "hybrid"] = (
        Field(
            default="multilateration",
            description="Localization algorithm to use",
        )
    )
    max_iterations: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum solver iterations",
    )
    convergence_threshold_m: float = Field(
        default=1.0,
        gt=0,
        description="Position convergence threshold in meters",
    )
    measurement_count: int = Field(
        default=1,
        ge=1,
        le=1000,
        description="RSSI snapshots to generate per tower",
    )
    enable_noise: bool = Field(
        default=True,
        description="Inject Gaussian noise into synthetic RSSI",
    )
    random_seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility (None = non-deterministic)",
    )


# ── Top-Level Scenario Configuration ────────────────────────────────────


class ScenarioConfig(BaseModel):
    """Simulation-ready configuration derived from a Scenario.

    This is the primary input to the Week 2 simulation pipeline.
    It bundles tower placements, environment parameters, simulation
    controls, and optional ground-truth into a single validated unit.

    Mapping from :class:`Scenario`:

    +---------------------------+-------------------------------+
    | Scenario field            | ScenarioConfig field          |
    +===========================+===============================+
    | scenario_id               | scenario_id                   |
    | name                      | name                          |
    | description               | description                   |
    | towers[]                  | tower_placements[]            |
    | environment_type          | environment_type              |
    | noise_level_dbm           | noise_level_dbm               |
    | expected_device_lat/lon   | expected_device_lat/lon       |
    +---------------------------+-------------------------------+

    Attributes:
        scenario_id: Unique scenario identifier.
        name: Human-readable scenario name.
        description: Optional textual description.
        tower_placements: Inline tower positions for the simulation.
        environment_type: Environment classification for RF modeling.
        noise_level_dbm: Background noise floor in dBm.
        propagation: Environment-specific propagation parameters.
        simulation: Solver / iteration settings.
        expected_device_lat: Ground-truth device latitude (validation).
        expected_device_lon: Ground-truth device longitude (validation).
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
        description="Optional scenario description",
    )

    # ── Tower layout ────────────────────────────────────────────────
    tower_placements: list[TowerPlacement] = Field(
        ...,
        min_length=3,
        description="Tower positions (minimum 3 for multilateration)",
    )

    # ── Environment ─────────────────────────────────────────────────
    environment_type: EnvironmentType = Field(
        default="urban",
        description="Environment classification for propagation modeling",
    )
    noise_level_dbm: float = Field(
        default=-95.0,
        description="Background noise floor in dBm",
    )

    # ── Propagation & simulation knobs ──────────────────────────────
    propagation: PropagationDefaults = Field(
        default_factory=PropagationDefaults,
        description="RF propagation parameters (auto-set from environment)",
    )
    simulation: SimulationParameters = Field(
        default_factory=SimulationParameters,
        description="Simulation / solver settings",
    )

    # ── Ground truth (optional, for validation) ─────────────────────
    expected_device_lat: float | None = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Ground-truth device latitude (WGS84)",
    )
    expected_device_lon: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Ground-truth device longitude (WGS84)",
    )

    # ── Validators ──────────────────────────────────────────────────

    @model_validator(mode="after")
    def _auto_propagation_defaults(self) -> ScenarioConfig:
        """Set propagation defaults from environment if not overridden."""
        # Only override if the user supplied the factory default (urban/3.5).
        # A simple heuristic: if propagation was left at its default values
        # and the environment is *not* urban, swap in the preset.
        default = PropagationDefaults()
        if self.propagation == default and self.environment_type != "urban":
            self.propagation = PropagationDefaults.for_environment(
                self.environment_type
            )
        return self

    @model_validator(mode="after")
    def _validate_ground_truth_pair(self) -> ScenarioConfig:
        """Ensure ground-truth coordinates are either both set or both None."""
        lat_set = self.expected_device_lat is not None
        lon_set = self.expected_device_lon is not None
        if lat_set != lon_set:
            raise ValueError(
                "expected_device_lat and expected_device_lon must both "
                "be set or both be None"
            )
        return self

    # ── Factory helpers ─────────────────────────────────────────────

    @classmethod
    def from_scenario(cls, scenario) -> ScenarioConfig:
        """Build a :class:`ScenarioConfig` from a :class:`Scenario`.

        Args:
            scenario: A :class:`~scientific.models.scenario.Scenario` instance.

        Returns:
            A fully populated :class:`ScenarioConfig` ready for the
            simulation pipeline.
        """
        placements = [
            TowerPlacement(
                tower_id=t.tower_id,
                latitude=t.latitude,
                longitude=t.longitude,
                antenna_height_m=t.antenna_height_m,
                frequency_mhz=t.frequency_mhz,
                transmit_power_dbm=t.transmit_power_dbm,
                coverage_radius_m=t.coverage_radius_m,
                sector=t.sector,
            )
            for t in scenario.towers
        ]
        return cls(
            scenario_id=scenario.scenario_id,
            name=scenario.name,
            description=scenario.description,
            tower_placements=placements,
            environment_type=scenario.environment_type,
            noise_level_dbm=scenario.noise_level_dbm,
            propagation=PropagationDefaults.for_environment(scenario.environment_type),
            expected_device_lat=scenario.expected_device_lat,
            expected_device_lon=scenario.expected_device_lon,
        )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scenario_id": "SCN-001",
                    "name": "Urban 3-Tower Test",
                    "description": "Standard urban multilateration scenario",
                    "tower_placements": [
                        {
                            "tower_id": "T001",
                            "latitude": 12.9716,
                            "longitude": 77.5946,
                            "antenna_height_m": 35.0,
                            "frequency_mhz": 1800.0,
                            "transmit_power_dbm": 43.0,
                            "coverage_radius_m": 1200.0,
                            "sector": "A",
                        },
                        {
                            "tower_id": "T002",
                            "latitude": 12.9750,
                            "longitude": 77.5900,
                            "antenna_height_m": 40.0,
                            "frequency_mhz": 2100.0,
                            "transmit_power_dbm": 46.0,
                            "coverage_radius_m": 1000.0,
                            "sector": "B",
                        },
                        {
                            "tower_id": "T003",
                            "latitude": 12.9700,
                            "longitude": 77.6000,
                            "antenna_height_m": 30.0,
                            "frequency_mhz": 900.0,
                            "transmit_power_dbm": 40.0,
                            "coverage_radius_m": 1500.0,
                            "sector": "A",
                        },
                    ],
                    "environment_type": "urban",
                    "noise_level_dbm": -95.0,
                    "propagation": {
                        "path_loss_exponent": 3.5,
                        "shadow_fading_std_db": 8.0,
                        "reference_distance_m": 1.0,
                        "reference_loss_db": 38.0,
                    },
                    "simulation": {
                        "algorithm": "multilateration",
                        "max_iterations": 100,
                        "convergence_threshold_m": 1.0,
                        "measurement_count": 1,
                        "enable_noise": True,
                        "random_seed": None,
                    },
                    "expected_device_lat": 12.9722,
                    "expected_device_lon": 77.5949,
                }
            ]
        }
    }
