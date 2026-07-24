"""
Scientific Simulation Module
=============================

Provides components for synthetic measurement generation:
- log-distance path-loss model (RSSIGenerator)
- shadow fading and noise injection (AWGNModel)
- scenario-based measurement synthesizer (MeasurementGenerator)
"""

from scientific.simulation.measurement_generator import (
    MeasurementGenerator,
    generate_scenario_measurements,
)
from scientific.simulation.noise_model import AWGNModel
from scientific.simulation.rssi_generator import RSSIGenerator

__all__ = [
    "AWGNModel",
    "MeasurementGenerator",
    "RSSIGenerator",
    "generate_scenario_measurements",
]
