"""
Unit tests for the Noise Model.
"""

import math

import pytest

from scientific.constants import RSSI_ABSOLUTE_MAX_DBM, RSSI_ABSOLUTE_MIN_DBM
from scientific.simulation.noise_model import AWGNModel, bound_rssi


def test_bound_rssi():
    assert bound_rssi(-70.0) == -70.0
    assert bound_rssi(RSSI_ABSOLUTE_MAX_DBM + 10) == RSSI_ABSOLUTE_MAX_DBM
    assert bound_rssi(RSSI_ABSOLUTE_MIN_DBM - 10) == RSSI_ABSOLUTE_MIN_DBM


def test_awgn_model_seed_reproducibility():
    model1 = AWGNModel(seed=42)
    model2 = AWGNModel(seed=42)

    val1 = model1.apply_shadow_fading(-70.0, 8.0)
    val2 = model2.apply_shadow_fading(-70.0, 8.0)
    assert val1 == val2

    val3 = model1.apply_all_noise(-70.0, 8.0, -95.0)
    val4 = model2.apply_all_noise(-70.0, 8.0, -95.0)
    assert val3 == val4


def test_awgn_model_shadow_fading_zero_std_dev():
    model = AWGNModel()
    assert model.apply_shadow_fading(-70.0, 0.0) == -70.0
    assert (
        model.apply_shadow_fading(-70.0, -5.0) == -70.0
    )  # Should handle negative std dev safely


def test_awgn_model_shadow_fading_distribution():
    model = AWGNModel(seed=123)
    samples = [model.apply_shadow_fading(-70.0, 8.0) for _ in range(10000)]

    # Calculate empirical mean and std dev
    mean = sum(samples) / len(samples)
    variance = sum((x - mean) ** 2 for x in samples) / len(samples)
    std_dev = math.sqrt(variance)

    # Law of large numbers: should be close to -70 and 8
    assert mean == pytest.approx(-70.0, abs=0.5)
    assert std_dev == pytest.approx(8.0, abs=0.5)


def test_awgn_model_thermal_noise():
    model = AWGNModel()

    # If signal is much stronger than noise, it should be mostly unaffected
    strong_signal = -50.0
    noise_floor = -100.0
    combined = model.apply_thermal_noise(strong_signal, noise_floor)
    assert combined == pytest.approx(-50.0, abs=0.01)

    # If signal is equal to noise floor, it should add approx 3 dB (actually 3.0103)
    signal = -95.0
    noise_floor = -95.0
    combined = model.apply_thermal_noise(signal, noise_floor)
    assert combined == pytest.approx(-91.99, abs=0.01)

    # If signal is much weaker than noise floor, combined should be close to noise floor
    weak_signal = -120.0
    noise_floor = -90.0
    combined = model.apply_thermal_noise(weak_signal, noise_floor)
    assert combined == pytest.approx(-90.0, abs=0.01)


def test_awgn_model_apply_all_noise_bounds():
    model = AWGNModel()
    # Apply noise that would push it way over the bounds
    noisy_max = model.apply_all_noise(10.0, 0.0, -100.0)
    assert noisy_max == RSSI_ABSOLUTE_MAX_DBM

    # Apply noise that would push it way under the bounds
    noisy_min = model.apply_all_noise(-200.0, 0.0, -200.0)
    assert noisy_min == RSSI_ABSOLUTE_MIN_DBM
