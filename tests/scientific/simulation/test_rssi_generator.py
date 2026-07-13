"""
Unit tests for the RSSI Generator.
"""

import pytest

from scientific.models.scenario_config import PropagationDefaults
from scientific.simulation.rssi_generator import RSSIGenerator


def test_calculate_distance():
    # Example: two points roughly 111 km apart (1 degree latitude)
    dist = RSSIGenerator.calculate_distance(0.0, 0.0, 1.0, 0.0)
    # Earth radius is 6371 km, 1 degree is ~111.19 km
    assert 111_000 < dist < 112_000


def test_calculate_path_loss_reference_distance():
    prop = PropagationDefaults(
        path_loss_exponent=3.0,
        reference_distance_m=1.0,
        reference_loss_db=38.0,
        shadow_fading_std_db=0.0,
    )
    # At reference distance, loss should be exactly reference_loss_db
    loss = RSSIGenerator.calculate_path_loss(1.0, prop)
    assert loss == pytest.approx(38.0)


def test_calculate_path_loss_log_distance():
    prop = PropagationDefaults(
        path_loss_exponent=3.0,
        reference_distance_m=1.0,
        reference_loss_db=38.0,
        shadow_fading_std_db=0.0,
    )
    # At 10m, d/d0 = 10, log10(10) = 1. Loss = 38 + 10 * 3.0 * 1 = 68.0
    loss = RSSIGenerator.calculate_path_loss(10.0, prop)
    assert loss == pytest.approx(68.0)

    # At 100m, d/d0 = 100, log10(100) = 2. Loss = 38 + 10 * 3.0 * 2 = 98.0
    loss = RSSIGenerator.calculate_path_loss(100.0, prop)
    assert loss == pytest.approx(98.0)


def test_calculate_path_loss_clamped_distance():
    prop = PropagationDefaults(
        path_loss_exponent=3.0,
        reference_distance_m=1.0,
        reference_loss_db=38.0,
        shadow_fading_std_db=0.0,
    )
    # At < 1m, distance should be clamped to 1m, loss = 38.0
    loss = RSSIGenerator.calculate_path_loss(0.5, prop)
    assert loss == pytest.approx(38.0)

    loss_zero = RSSIGenerator.calculate_path_loss(0.0, prop)
    assert loss_zero == pytest.approx(38.0)


def test_compute_ideal_rssi():
    prop = PropagationDefaults(
        path_loss_exponent=2.0,
        reference_distance_m=1.0,
        reference_loss_db=30.0,
        shadow_fading_std_db=0.0,
    )
    # Distance 100m -> loss = 30 + 10 * 2 * 2 = 70.0 dB
    # TX Power = 43 dBm -> RSSI = 43 - 70 = -27 dBm
    rssi = RSSIGenerator.compute_ideal_rssi(100.0, 43.0, prop)
    assert rssi == pytest.approx(-27.0)
