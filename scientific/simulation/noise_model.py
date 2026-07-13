"""
Noise Model
===========

Simulates RF noise, including log-normal shadow fading and thermal noise floor.
"""

from __future__ import annotations

import random
from typing import Optional
from scientific.constants import dbm_to_watts, watts_to_dbm


def apply_noise(
    rssi_clean: float,
    shadow_fading_std_db: float,
    noise_level_dbm: float,
    enable_noise: bool = True,
    seed: Optional[int] = None,
) -> float:
    """Apply shadow fading and thermal noise to clean RSSI.

    Clamps the output between -150.0 and 0.0 dBm.
    """
    if not enable_noise:
        return max(-150.0, min(rssi_clean, 0.0))

    # ponytail: use stdlib random to support thread-safe local seeding
    rng = random.Random(seed) if seed is not None else random

    # 1. Log-normal shadow fading (Gaussian in dB domain)
    fading = rng.gauss(0.0, shadow_fading_std_db)
    rssi_faded = rssi_clean + fading

    # 2. Combined noise model (summing signal + noise floor in linear power domain)
    try:
        p_signal = dbm_to_watts(rssi_faded)
        p_noise = dbm_to_watts(noise_level_dbm)
        rssi_noisy = watts_to_dbm(p_signal + p_noise)
    except ValueError:
        # Fallback if math range error occurs
        rssi_noisy = max(rssi_faded, noise_level_dbm)

    # 3. Physical clamping
    return max(-150.0, min(rssi_noisy, 0.0))
