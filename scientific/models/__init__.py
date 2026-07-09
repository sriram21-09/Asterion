"""
Scientific Models
=================

Pydantic data models for the Asterion scientific engine.

Exports:
    Tower: Cell tower configuration schema.
    Measurement: Signal measurement schema (RSSI-based).
    Scenario: Localization scenario configuration schema.
    ScenarioConfig: Simulation-ready scenario configuration.
    TowerPlacement: Inline tower position for simulation input.
    PropagationDefaults: Environment-specific RF propagation parameters.
    SimulationParameters: Solver / iteration settings.
    LocalizationResult: Localization algorithm output schema.
    ConfidenceResult: Confidence assessment output schema.
"""

from scientific.models.measurement import Measurement
from scientific.models.result import ConfidenceResult, LocalizationResult
from scientific.models.scenario import Scenario
from scientific.models.scenario_config import (
    PropagationDefaults,
    ScenarioConfig,
    SimulationParameters,
    TowerPlacement,
)
from scientific.models.tower import Tower

__all__ = [
    "Tower",
    "Measurement",
    "Scenario",
    "ScenarioConfig",
    "TowerPlacement",
    "PropagationDefaults",
    "SimulationParameters",
    "LocalizationResult",
    "ConfidenceResult",
]
