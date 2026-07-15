"""
AWGN Model and Shadow Fading
============================

Injects realistic radio frequency noise and shadow fading into ideal signal
strength values.
"""

import random
from typing import Optional

from scientific.constants import (
    RSSI_ABSOLUTE_MAX_DBM,
    RSSI_ABSOLUTE_MIN_DBM,
    db_to_linear,
    dbm_to_watts,
    watts_to_dbm,
)


def bound_rssi(rssi_dbm: float) -> float:
    """Clamp the RSSI value between absolute minimum and maximum boundaries.

    Args:
        rssi_dbm: The input RSSI in dBm.

    Returns:
        The clamped RSSI in dBm.
    """
    return max(RSSI_ABSOLUTE_MIN_DBM, min(rssi_dbm, RSSI_ABSOLUTE_MAX_DBM))


class AWGNModel:
    """Additive White Gaussian Noise and shadow fading model for RF signals."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize the noise model.

        Args:
            seed: Optional seed for the random number generator to ensure
                reproducible simulations.
        """
        self.rng = random.Random(seed)

    def apply_shadow_fading(self, ideal_rssi: float, std_dev_db: float) -> float:
        """Apply log-normal shadow fading to an ideal RSSI value.

        Log-normal shadowing means the signal strength in dBm experiences
        Gaussian variation around its mean value.

        Args:
            ideal_rssi: Ideal RSSI without fading in dBm.
            std_dev_db: Standard deviation of the shadow fading in dB.

        Returns:
            Faded RSSI in dBm.
        """
        if std_dev_db <= 0:
            return ideal_rssi
        
        fading = self.rng.gauss(0.0, std_dev_db)
        return ideal_rssi + fading

    def apply_thermal_noise(self, rssi_dbm: float, noise_floor_dbm: float) -> float:
        """Combine an RSSI signal with a background noise floor.

        Since powers add linearly, the values are converted to Watts,
        added, and converted back to dBm.

        Args:
            rssi_dbm: Faded RSSI in dBm.
            noise_floor_dbm: Background noise level in dBm.

        Returns:
            The combined RSSI + noise in dBm.
        """
        signal_w = dbm_to_watts(rssi_dbm)
        noise_w = dbm_to_watts(noise_floor_dbm)
        combined_w = signal_w + noise_w
        return watts_to_dbm(combined_w)

    def apply_all_noise(
        self, ideal_rssi: float, std_dev_db: float, noise_floor_dbm: float
    ) -> float:
        """Apply shadow fading, thermal noise, and bound the result.

        Args:
            ideal_rssi: Ideal RSSI without noise in dBm.
            std_dev_db: Standard deviation of shadow fading in dB.
            noise_floor_dbm: Background noise floor in dBm.

        Returns:
            The final noisy, bounded RSSI in dBm.
        """
        faded = self.apply_shadow_fading(ideal_rssi, std_dev_db)
        noisy = self.apply_thermal_noise(faded, noise_floor_dbm)
        return bound_rssi(noisy)
