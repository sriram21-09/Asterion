"""
RSSI Generator
==============

Computes ideal (noise-free) Received Signal Strength Indicator (RSSI) using
the log-distance path-loss model.
"""

import math

from scientific.constants import haversine_distance_m
from scientific.models.scenario_config import PropagationDefaults


class RSSIGenerator:
    """Generates ideal RSSI values based on distance and propagation parameters."""

    @staticmethod
    def calculate_distance(
        tower_lat: float,
        tower_lon: float,
        device_lat: float,
        device_lon: float,
    ) -> float:
        """Calculate the distance between a tower and a device in meters.

        Args:
            tower_lat: Tower latitude in decimal degrees.
            tower_lon: Tower longitude in decimal degrees.
            device_lat: Device latitude in decimal degrees.
            device_lon: Device longitude in decimal degrees.

        Returns:
            Distance in meters.
        """
        return haversine_distance_m(tower_lat, tower_lon, device_lat, device_lon)

    @staticmethod
    def calculate_path_loss(
        distance_m: float, propagation: PropagationDefaults
    ) -> float:
        """Calculate the path loss using the log-distance model.

        Args:
            distance_m: Distance between transmitter and receiver in meters.
            propagation: Propagation parameters (exponent, reference loss, etc.).

        Returns:
            Path loss in dB.
        """
        # To avoid negative logs or excessive signal at very close ranges,
        # we clamp the distance to a minimum of the reference distance.
        eff_distance = max(distance_m, propagation.reference_distance_m)

        # Log-distance path loss formula: L = L0 + 10 * n * log10(d / d0)
        loss = (
            propagation.reference_loss_db
            + 10.0
            * propagation.path_loss_exponent
            * math.log10(eff_distance / propagation.reference_distance_m)
        )
        return loss

    @classmethod
    def compute_ideal_rssi(
        cls,
        distance_m: float,
        tx_power_dbm: float,
        propagation: PropagationDefaults,
    ) -> float:
        """Compute the ideal RSSI given distance, transmit power, and propagation.

        Args:
            distance_m: Distance between transmitter and receiver in meters.
            tx_power_dbm: Transmit power (EIRP) in dBm.
            propagation: Propagation parameters.

        Returns:
            Ideal RSSI in dBm.
        """
        path_loss = cls.calculate_path_loss(distance_m, propagation)
        return tx_power_dbm - path_loss
