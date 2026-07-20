import math
from datetime import datetime, timedelta, timezone
import pytest
import numpy as np

from scientific.constants import METERS_PER_DEGREE_LAT
from scientific.models.result import LocalizationResult
from scientific.pipeline.kalman_tracker import track_positions


def test_kalman_empty_and_single_input():
    """Verify handling of empty or single-element inputs."""
    # 1. Empty input
    assert track_positions([]) == []

    # 2. Single input
    t0 = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)
    res = LocalizationResult(
        scenario_id="SCN-001",
        algorithm="multilateration",
        estimated_latitude=12.9716,
        estimated_longitude=77.5946,
        error_m=20.0,
        signals_used=3,
        timestamp=t0,
    )

    smoothed = track_positions([res])
    assert len(smoothed) == 1
    assert smoothed[0].algorithm == "kalman"
    assert smoothed[0].estimated_latitude == pytest.approx(12.9716)
    assert smoothed[0].estimated_longitude == pytest.approx(77.5946)
    assert smoothed[0].error_m is None  # no ground truth provided

    # Verify velocities are attached
    assert hasattr(smoothed[0], "velocity_lat")
    assert smoothed[0].velocity_lat == 0.0
    assert smoothed[0].velocity_lon == 0.0
    assert smoothed[0].velocity_lat_mps == 0.0
    assert smoothed[0].velocity_lon_mps == 0.0


def test_constant_velocity_tracking():
    """Verify tracking and velocity estimation for a target moving at constant speed."""
    t0 = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)

    # Ground-truth: starts at (12.97, 77.59) and moves north at 15 m/s (~54 km/h)
    true_lat_start = 12.9700
    true_lon = 77.5900
    velocity_mps = 15.0  # m/s
    velocity_deg_s = velocity_mps / METERS_PER_DEGREE_LAT

    steps = 15
    dt = 1.0  # seconds between steps

    # Create sequence of noisy measurements
    np.random.seed(42)  # for reproducible noise
    noise_std_m = 10.0
    noise_std_deg = noise_std_m / METERS_PER_DEGREE_LAT

    results = []
    for i in range(steps):
        t = t0 + timedelta(seconds=i * dt)
        true_lat = true_lat_start + i * dt * velocity_deg_s

        # Inject noise into position
        noisy_lat = true_lat + np.random.normal(0, noise_std_deg)
        noisy_lon = true_lon + np.random.normal(
            0, noise_std_deg / math.cos(math.radians(true_lat))
        )

        results.append(
            LocalizationResult(
                scenario_id="SCN-MOVING",
                algorithm="multilateration",
                estimated_latitude=noisy_lat,
                estimated_longitude=noisy_lon,
                error_m=noise_std_m,
                signals_used=4,
                timestamp=t,
            )
        )

    # Run Kalman Filter tracking
    # Ground truth coordinates are provided at the end point to verify final error calculation
    true_lat_end = true_lat_start + (steps - 1) * dt * velocity_deg_s
    smoothed = track_positions(
        results,
        expected_device_lat=true_lat_end,
        expected_device_lon=true_lon,
        process_noise_acc=0.5,
        default_measurement_noise_m=noise_std_m,
    )

    assert len(smoothed) == steps

    # Compare errors: last smoothed position should be closer to ground truth than raw noisy estimate
    raw_final = results[-1]
    smooth_final = smoothed[-1]

    raw_error = raw_final.estimated_latitude - true_lat_end
    smooth_error = smooth_final.estimated_latitude - true_lat_end

    # The smoothed error should generally be smaller than raw error due to noise dampening
    assert abs(smooth_error) < abs(raw_error) or smooth_final.error_m < noise_std_m * 2

    # Verify velocity estimate converges towards the true velocity
    final_v_lat_mps = smooth_final.velocity_lat_mps
    # True velocity is 15.0 m/s
    assert abs(final_v_lat_mps - velocity_mps) < 5.0  # converges within a tolerance


def test_noise_smoothing_outlier_rejection():
    """Verify that a sudden huge outlier spike is smoothed and dampened."""
    t0 = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)
    base_lat = 12.9716
    base_lon = 77.5946

    # Target is stationary, but step 5 has a huge outlier (500 meter jump)
    outlier_distance_m = 500.0
    outlier_jump_deg = outlier_distance_m / METERS_PER_DEGREE_LAT

    results = []
    for i in range(10):
        t = t0 + timedelta(seconds=i * 2.0)
        lat = base_lat
        lon = base_lon
        if i == 5:
            lat += outlier_jump_deg

        results.append(
            LocalizationResult(
                scenario_id="SCN-OUTLIER",
                algorithm="multilateration",
                estimated_latitude=lat,
                estimated_longitude=lon,
                error_m=20.0,
                signals_used=3,
                timestamp=t,
            )
        )

    smoothed = track_positions(results, default_measurement_noise_m=20.0)

    # Verify that the outlier at index 5 is significantly dampened in the smoothed output
    raw_spike = results[5].estimated_latitude - base_lat
    smoothed_spike = smoothed[5].estimated_latitude - base_lat

    # The smoothed spike should be less than 60% of the raw jump
    assert abs(smoothed_spike) < 0.6 * abs(raw_spike)
    print(
        f"Raw jump: {raw_spike * METERS_PER_DEGREE_LAT:.2f}m, Smoothed: {smoothed_spike * METERS_PER_DEGREE_LAT:.2f}m"
    )


def test_zero_time_delta_handling():
    """Verify that the filter handles duplicate/zero-time-delta timestamps cleanly."""
    t0 = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)

    results = [
        LocalizationResult(
            scenario_id="SCN-ZERO-DT",
            algorithm="multilateration",
            estimated_latitude=12.9716,
            estimated_longitude=77.5946,
            error_m=20.0,
            signals_used=3,
            timestamp=t0,
        ),
        # Duplicate timestamp
        LocalizationResult(
            scenario_id="SCN-ZERO-DT",
            algorithm="multilateration",
            estimated_latitude=12.9720,
            estimated_longitude=77.5950,
            error_m=20.0,
            signals_used=3,
            timestamp=t0,
        ),
    ]

    smoothed = track_positions(results)
    assert len(smoothed) == 2
    # Ensure it didn't crash and processed both updates
    assert smoothed[1].algorithm == "kalman"
