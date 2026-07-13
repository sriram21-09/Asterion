"""
Measurement Generator
=====================

Orchestrates the propagation and noise models to output batches of synthetic
Measurement objects for a given scenario.
"""

from datetime import datetime, timezone, timedelta
from typing import List

from scientific.models.measurement import Measurement
from scientific.models.scenario_config import ScenarioConfig
from scientific.simulation.noise_model import AWGNModel
from scientific.simulation.rssi_generator import RSSIGenerator


class MeasurementGenerator:
    """Orchestrates generation of synthetic cell tower measurements."""

    def __init__(self, config: ScenarioConfig):
        """Initialize the measurement generator.

        Args:
            config: The scenario configuration detailing tower placements,
                environment, simulation parameters, and ground truth.
        """
        self.config = config
        # Use the random seed if specified in the scenario config.
        # This ensures reproducibility for both noise generation and IDs.
        seed = self.config.simulation.random_seed
        self.noise_model = AWGNModel(seed)

    def generate(self) -> List[Measurement]:
        """Generate a batch of synthetic measurements for the scenario.

        Returns:
            A list of valid Measurement objects.

        Raises:
            ValueError: If expected_device_lat or expected_device_lon is missing.
        """
        if self.config.expected_device_lat is None or self.config.expected_device_lon is None:
            raise ValueError(
                "Cannot generate measurements without expected_device_lat and "
                "expected_device_lon ground truth coordinates in the configuration."
            )

        measurements = []
        base_time = datetime.now(timezone.utc)
        ms_count = self.config.simulation.measurement_count
        enable_noise = self.config.simulation.enable_noise

        measurement_idx = 1
        for tower in self.config.tower_placements:
            # 1. Compute distance
            distance_m = RSSIGenerator.calculate_distance(
                tower_lat=tower.latitude,
                tower_lon=tower.longitude,
                device_lat=self.config.expected_device_lat,
                device_lon=self.config.expected_device_lon,
            )

            # 2. Compute ideal (noise-free) RSSI
            ideal_rssi = RSSIGenerator.compute_ideal_rssi(
                distance_m=distance_m,
                tx_power_dbm=tower.transmit_power_dbm,
                propagation=self.config.propagation,
            )

            for i in range(ms_count):
                # 3. Apply noise and fading if enabled
                if enable_noise:
                    final_rssi = self.noise_model.apply_all_noise(
                        ideal_rssi=ideal_rssi,
                        std_dev_db=self.config.propagation.shadow_fading_std_db,
                        noise_floor_dbm=self.config.noise_level_dbm,
                    )
                else:
                    from scientific.simulation.noise_model import bound_rssi
                    final_rssi = bound_rssi(ideal_rssi)

                # Generate a unique measurement ID and slightly staggered timestamp
                m_id = f"M{measurement_idx:04d}"
                timestamp = base_time + timedelta(milliseconds=i * 100)

                measurement = Measurement(
                    measurement_id=m_id,
                    tower_id=tower.tower_id,
                    timestamp=timestamp,
                    rssi_dbm=final_rssi,
                    latitude=self.config.expected_device_lat,
                    longitude=self.config.expected_device_lon,
                    # Note: We omit timing_advance and uncertainty_m for this
                    # basic RF signal generation phase.
                )
                measurements.append(measurement)
                measurement_idx += 1

        return measurements


def generate_scenario_measurements(
    config: ScenarioConfig,
) -> List[Measurement]:
    """Helper function to generate synthetic measurements with timing advance and uncertainty."""
    generator = MeasurementGenerator(config)
    measurements = generator.generate()

    # Post-process measurements to calculate timing advance and uncertainty
    # which is expected by Sriram's database models and API.
    from scientific.constants import TA_RESOLUTION_M, TA_MAX_VALUE

    for m in measurements:
        # Find the tower placement that corresponds to this measurement's tower_id
        tower = next((t for t in config.tower_placements if t.tower_id == m.tower_id), None)
        if tower:
            # Calculate distance
            distance = RSSIGenerator.calculate_distance(
                tower_lat=tower.latitude,
                tower_lon=tower.longitude,
                device_lat=config.expected_device_lat,
                device_lon=config.expected_device_lon,
            )
            # Calculate timing advance
            ta_raw = distance / TA_RESOLUTION_M
            m.timing_advance = float(min(max(0, round(ta_raw)), TA_MAX_VALUE))
            # ponytail: make uncertainty calculation parameters (0.15 multiplier and 20.0m floor) configurable via PropagationDefaults or ScenarioConfig
            # Calculate uncertainty
            m.uncertainty_m = max(20.0, distance * 0.15)
        else:
            m.timing_advance = None
            m.uncertainty_m = None

    return measurements
