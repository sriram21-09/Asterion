"""
Scientific Simulation Module
=============================

Provides components for synthetic measurement generation:
- log-distance path-loss model
- shadow fading and noise injection
- scenario-based measurement synthesizer
"""

from scientific.simulation.rssi_generator import generate_rssi, calculate_path_loss
from scientific.simulation.noise_model import apply_noise
from scientific.simulation.measurement_generator import generate_scenario_measurements

__all__ = [
    "generate_rssi",
    "calculate_path_loss",
    "apply_noise",
    "generate_scenario_measurements",
]
