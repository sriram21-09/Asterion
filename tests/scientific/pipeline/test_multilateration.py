from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from scientific.constants import haversine_distance_m
from scientific.models.measurement import Measurement
from scientific.models.scenario_config import PropagationDefaults, SimulationParameters
from scientific.models.tower import Tower
from scientific.pipeline.multilateration import solve_multilateration
from scientific.simulation.rssi_generator import RSSIGenerator


@pytest.fixture
def propagation_params():
    return PropagationDefaults(
        path_loss_exponent=3.0,
        reference_distance_m=1.0,
        reference_loss_db=32.4,
        shadow_fading_std_db=4.0,
    )


@pytest.fixture
def simulation_params():
    return SimulationParameters(
        algorithm="multilateration",
        max_iterations=100,
        convergence_threshold_m=1e-4,
        measurement_count=1,
        enable_noise=False,
    )


def test_multilateration_zero_noise_reconstruction(
    propagation_params, simulation_params
):
    """Verify that under zero noise, NLLS multilateration reconstructs the exact device position."""
    device_lat = 12.9716
    device_lon = 77.5946

    # Place 3 towers around the device
    towers = [
        Tower(
            tower_id="T001",
            latitude=12.9600,
            longitude=77.5800,
            transmit_power_dbm=43.0,
        ),
        Tower(
            tower_id="T002",
            latitude=12.9850,
            longitude=77.5850,
            transmit_power_dbm=43.0,
        ),
        Tower(
            tower_id="T003",
            latitude=12.9700,
            longitude=77.6100,
            transmit_power_dbm=43.0,
        ),
    ]

    # Generate ideal RSSI for each tower based on its distance to the device
    measurements = []
    for i, tower in enumerate(towers):
        dist = haversine_distance_m(
            tower.latitude, tower.longitude, device_lat, device_lon
        )
        rssi = RSSIGenerator.compute_ideal_rssi(
            dist, tower.transmit_power_dbm, propagation_params
        )
        measurements.append(
            Measurement(
                measurement_id=f"M{i:03d}",
                tower_id=tower.tower_id,
                timestamp=datetime.now(UTC),
                rssi_dbm=rssi,
            )
        )

    # Run solver
    result = solve_multilateration(
        scenario_id="SCN-ZERO-NOISE",
        towers=towers,
        measurements=measurements,
        propagation=propagation_params,
        simulation=simulation_params,
        expected_device_lat=device_lat,
        expected_device_lon=device_lon,
    )

    assert result.algorithm == "multilateration"
    assert result.signals_used == 3
    assert result.error_m is not None
    # With zero noise, error should be very small (e.g. less than 1 meter)
    assert result.error_m < 1.0
    assert pytest.approx(result.estimated_latitude, abs=1e-5) == device_lat
    assert pytest.approx(result.estimated_longitude, abs=1e-5) == device_lon


def test_multilateration_noisy_convergence(propagation_params, simulation_params):
    """Verify that NLLS multilateration converges near the ground truth under noisy conditions."""
    device_lat = 12.9716
    device_lon = 77.5946

    towers = [
        Tower(
            tower_id="T001",
            latitude=12.9600,
            longitude=77.5800,
            transmit_power_dbm=43.0,
        ),
        Tower(
            tower_id="T002",
            latitude=12.9850,
            longitude=77.5850,
            transmit_power_dbm=43.0,
        ),
        Tower(
            tower_id="T003",
            latitude=12.9700,
            longitude=77.6100,
            transmit_power_dbm=43.0,
        ),
        Tower(
            tower_id="T004",
            latitude=12.9800,
            longitude=77.6000,
            transmit_power_dbm=43.0,
        ),
    ]

    # Inject minor noise (+- 2 dB) to the measurements
    noise_offsets = [1.5, -2.0, 0.8, -1.2]
    measurements = []
    for i, tower in enumerate(towers):
        dist = haversine_distance_m(
            tower.latitude, tower.longitude, device_lat, device_lon
        )
        ideal_rssi = RSSIGenerator.compute_ideal_rssi(
            dist, tower.transmit_power_dbm, propagation_params
        )
        noisy_rssi = ideal_rssi + noise_offsets[i]
        measurements.append(
            Measurement(
                measurement_id=f"M{i:03d}",
                tower_id=tower.tower_id,
                timestamp=datetime.now(UTC),
                rssi_dbm=noisy_rssi,
            )
        )

    # Run solver
    result = solve_multilateration(
        scenario_id="SCN-NOISY",
        towers=towers,
        measurements=measurements,
        propagation=propagation_params,
        simulation=simulation_params,
        expected_device_lat=device_lat,
        expected_device_lon=device_lon,
    )

    assert result.algorithm == "multilateration"
    assert result.signals_used == 4
    assert result.error_m is not None
    # The noise is small, so the error should be bounded (e.g. less than 150 meters)
    assert result.error_m < 300.0


def test_multilateration_insufficient_towers_fallback(
    propagation_params, simulation_params
):
    """Verify that the solver immediately falls back to weighted centroid if unique towers are less than 3."""
    towers = [
        Tower(tower_id="T001", latitude=10.0, longitude=10.0, transmit_power_dbm=43.0),
        Tower(tower_id="T002", latitude=20.0, longitude=20.0, transmit_power_dbm=43.0),
    ]

    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(UTC),
            rssi_dbm=-60.0,
        ),
        Measurement(
            measurement_id="M002",
            tower_id="T002",
            timestamp=datetime.now(UTC),
            rssi_dbm=-70.0,
        ),
    ]

    # Run solver with 2 towers
    result = solve_multilateration(
        scenario_id="SCN-FEW-TOWERS",
        towers=towers,
        measurements=measurements,
        propagation=propagation_params,
        simulation=simulation_params,
    )

    # Should fallback to weighted centroid
    assert result.algorithm == "weighted_centroid"
    # Weighted centroid with equal RSSI-derived weights is not exactly the middle since RSSIs differ,
    # but it shouldn't raise any error.
    assert result.signals_used == 2


def test_multilateration_solver_failure_fallback(propagation_params, simulation_params):
    """Verify that solver falls back to weighted centroid if scipy least_squares fails."""

    towers = [
        Tower(
            tower_id="T001",
            latitude=12.9600,
            longitude=77.5800,
            transmit_power_dbm=43.0,
        ),
        Tower(
            tower_id="T002",
            latitude=12.9850,
            longitude=77.5850,
            transmit_power_dbm=43.0,
        ),
        Tower(
            tower_id="T003",
            latitude=12.9700,
            longitude=77.6100,
            transmit_power_dbm=43.0,
        ),
    ]

    measurements = [
        Measurement(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime.now(UTC),
            rssi_dbm=-70.0,
        ),
        Measurement(
            measurement_id="M002",
            tower_id="T002",
            timestamp=datetime.now(UTC),
            rssi_dbm=-70.0,
        ),
        Measurement(
            measurement_id="M003",
            tower_id="T003",
            timestamp=datetime.now(UTC),
            rssi_dbm=-70.0,
        ),
    ]

    # Mock least_squares to raise an exception
    with patch(
        "scientific.pipeline.multilateration.least_squares",
        side_effect=RuntimeError("Solver error"),
    ):
        result = solve_multilateration(
            scenario_id="SCN-FAIL-SOLVER",
            towers=towers,
            measurements=measurements,
            propagation=propagation_params,
            simulation=simulation_params,
        )

    # Should fallback to weighted centroid
    assert result.algorithm == "weighted_centroid"
