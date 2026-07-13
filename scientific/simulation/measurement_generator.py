"""
Measurement Synthesizer
=======================

Generates synthetic measurements list from ScenarioConfig.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional

from scientific.models.measurement import Measurement
from scientific.models.scenario_config import ScenarioConfig
from scientific.constants import haversine_distance_m, TA_RESOLUTION_M, TA_MAX_VALUE
from scientific.simulation.rssi_generator import generate_rssi
from scientific.simulation.noise_model import apply_noise


def generate_scenario_measurements(
    config: ScenarioConfig,
    base_timestamp: Optional[datetime] = None,
) -> List[Measurement]:
    """Generate synthetic Measurement snapshots for a ScenarioConfig."""
    if config.expected_device_lat is None or config.expected_device_lon is None:
        raise ValueError(
            "Ground-truth device position (expected_device_lat/lon) must be "
            "specified in ScenarioConfig to generate measurements."
        )

    if base_timestamp is None:
        base_timestamp = datetime.now(timezone.utc)
    elif base_timestamp.tzinfo is None:
        base_timestamp = base_timestamp.replace(tzinfo=timezone.utc)

    measurements: List[Measurement] = []
    measurement_idx = 1

    # Fetch simulation parameters
    sim_params = config.simulation
    measurement_count = sim_params.measurement_count
    base_seed = sim_params.random_seed

    for tower_idx, tower in enumerate(config.tower_placements):
        # 1. Compute distance from device to tower
        distance = haversine_distance_m(
            config.expected_device_lat,
            config.expected_device_lon,
            tower.latitude,
            tower.longitude,
        )

        # 2. Generate clean RSSI
        rssi_clean = generate_rssi(
            distance_m=distance,
            transmit_power_dbm=tower.transmit_power_dbm,
            coverage_radius_m=tower.coverage_radius_m,
            path_loss_exponent=config.propagation.path_loss_exponent,
            reference_loss_db=config.propagation.reference_loss_db,
            reference_distance_m=config.propagation.reference_distance_m,
        )

        # If tower is out of range, skip generating signals for it
        if rssi_clean is None:
            continue

        # 3. Compute timing advance and uncertainty
        # GSM TA resolution is TA_RESOLUTION_M (550m) per unit, clamped to [0, TA_MAX_VALUE]
        ta_raw = distance / TA_RESOLUTION_M
        timing_advance = float(min(max(0, round(ta_raw)), TA_MAX_VALUE))
        
        # Estimate uncertainty as a function of path loss exponent and distance
        uncertainty = max(20.0, distance * 0.15)

        # 4. Generate multiple snapshots
        for step in range(measurement_count):
            # Deterministic seed offset per tower and snapshot
            seed = None
            if base_seed is not None:
                seed = base_seed + tower_idx * 1000 + step

            rssi_noisy = apply_noise(
                rssi_clean=rssi_clean,
                shadow_fading_std_db=config.propagation.shadow_fading_std_db,
                noise_level_dbm=config.noise_level_dbm,
                enable_noise=sim_params.enable_noise,
                seed=seed,
            )

            # Build measurement
            # Code follows pattern MEAS-0001, MEAS-0002, etc.
            meas_code = f"MEAS-{measurement_idx:04d}"
            
            # Snapshots separated by 1-second intervals
            timestamp = base_timestamp + timedelta(seconds=step)

            measurements.append(
                Measurement(
                    measurement_id=meas_code,
                    tower_id=tower.tower_id,
                    timestamp=timestamp,
                    rssi_dbm=rssi_noisy,
                    latitude=config.expected_device_lat,
                    longitude=config.expected_device_lon,
                    timing_advance=timing_advance,
                    uncertainty_m=uncertainty,
                )
            )
            measurement_idx += 1

    return measurements
