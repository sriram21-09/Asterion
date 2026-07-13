"""
Unit tests for the Measurement Generator.
"""

import pytest

from scientific.models.scenario_config import (
    PropagationDefaults,
    ScenarioConfig,
    SimulationParameters,
    TowerPlacement,
)
from scientific.simulation.measurement_generator import MeasurementGenerator


@pytest.fixture
def base_config() -> ScenarioConfig:
    return ScenarioConfig(
        scenario_id="SCN-TEST-1",
        name="Test Scenario",
        tower_placements=[
            TowerPlacement(
                tower_id="T1",
                latitude=12.000,
                longitude=77.000,
                transmit_power_dbm=43.0,
            ),
            TowerPlacement(
                tower_id="T2",
                latitude=12.001,
                longitude=77.001,
                transmit_power_dbm=43.0,
            ),
            TowerPlacement(
                tower_id="T3",
                latitude=12.002,
                longitude=77.002,
                transmit_power_dbm=43.0,
            ),
        ],
        environment_type="urban",
        expected_device_lat=12.001,
        expected_device_lon=77.000,
        simulation=SimulationParameters(
            measurement_count=2,
            enable_noise=False,
            random_seed=42,
        ),
        propagation=PropagationDefaults(
            path_loss_exponent=3.0,
            shadow_fading_std_db=8.0,
        ),
    )


def test_measurement_generator_no_ground_truth(base_config: ScenarioConfig):
    # Removing ground truth should cause generation to fail
    base_config.expected_device_lat = None
    base_config.expected_device_lon = None
    generator = MeasurementGenerator(base_config)
    
    with pytest.raises(ValueError, match="expected_device_lat"):
        generator.generate()


def test_measurement_generator_no_noise(base_config: ScenarioConfig):
    # With 3 towers and measurement_count=2, we should get 6 measurements
    generator = MeasurementGenerator(base_config)
    measurements = generator.generate()
    
    assert len(measurements) == 6
    assert all(m.latitude == base_config.expected_device_lat for m in measurements)
    assert all(m.longitude == base_config.expected_device_lon for m in measurements)
    assert measurements[0].tower_id == "T1"
    assert measurements[1].tower_id == "T1"
    assert measurements[2].tower_id == "T2"

    # All generated IDs should be unique
    ids = [m.measurement_id for m in measurements]
    assert len(set(ids)) == 6


def test_measurement_generator_with_noise(base_config: ScenarioConfig):
    base_config.simulation.enable_noise = True
    
    gen1 = MeasurementGenerator(base_config)
    measurements1 = gen1.generate()

    # Create another generator with identical config (same seed)
    gen2 = MeasurementGenerator(base_config)
    measurements2 = gen2.generate()

    # The generated values should be identical because the seed is the same
    for m1, m2 in zip(measurements1, measurements2):
        assert m1.rssi_dbm == m2.rssi_dbm


def test_measurement_generator_different_seeds(base_config: ScenarioConfig):
    base_config.simulation.enable_noise = True
    
    gen1 = MeasurementGenerator(base_config)
    measurements1 = gen1.generate()

    base_config.simulation.random_seed = 999
    gen2 = MeasurementGenerator(base_config)
    measurements2 = gen2.generate()

    # The generated values should be different due to different seeds
    # (Technically there's an infinitesimal chance they're identical, but practically zero)
    diff_found = any(m1.rssi_dbm != m2.rssi_dbm for m1, m2 in zip(measurements1, measurements2))
    assert diff_found, "Measurements with different seeds were identical"
