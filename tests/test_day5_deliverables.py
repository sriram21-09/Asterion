"""
Day 5 Deliverable Tests — Config, Constants & Logger
======================================================

Comprehensive tests for the three new scientific infrastructure modules:

- ``scientific/config.py``     — SimulationConfig, ValidationThresholds,
                                 EnvironmentConfig, get_environment_config
- ``scientific/constants.py``  — Physical constants, unit conversions,
                                 Haversine, cellular bands, RSSI tiers
- ``scientific/logger.py``     — get_logger, set_level, silence

Test count: 72 tests
"""

import logging
import math

import pytest

# ── Module under test ────────────────────────────────────────────────────

from scientific.config import (
    DEFAULT_SIMULATION_CONFIG,
    DEFAULT_VALIDATION_THRESHOLDS,
    ENVIRONMENT_PRESETS,
    EnvironmentConfig,
    SimulationConfig,
    ValidationThresholds,
    get_environment_config,
)
from scientific.constants import (
    BAND_GROUPS,
    BAND_TOLERANCE_MHZ,
    BOLTZMANN_CONSTANT_J_K,
    BOLTZMANN_DBM_HZ_K,
    CELLULAR_BANDS_MHZ,
    DEFAULT_ANTENNA_HEIGHT_M,
    DEFAULT_COVERAGE_RADIUS_M,
    DEFAULT_FREQUENCY_MHZ,
    DEFAULT_TRANSMIT_POWER_DBM,
    DEG_TO_RAD,
    EARTH_RADIUS_M,
    FREE_SPACE_LOSS_1M_1GHZ_DB,
    LATITUDE_RANGE,
    LONGITUDE_RANGE,
    MAX_ANTENNA_HEIGHT_M,
    MAX_COVERAGE_RADIUS_M,
    MAX_TX_POWER_DBM,
    MIN_ANTENNA_HEIGHT_M,
    MIN_TX_POWER_DBM,
    PI,
    RAD_TO_DEG,
    RSSI_ABSOLUTE_MAX_DBM,
    RSSI_ABSOLUTE_MIN_DBM,
    RSSI_PLAUSIBLE_MAX_DBM,
    RSSI_PLAUSIBLE_MIN_DBM,
    RSSI_QUALITY_TIERS,
    SPEED_OF_LIGHT_M_S,
    TA_MAX_DISTANCE_M,
    TA_MAX_VALUE,
    TA_RESOLUTION_M,
    THERMAL_NOISE_DBM_HZ,
    WGS84_FLATTENING_INV,
    WGS84_SEMI_MAJOR_M,
    db_to_linear,
    dbm_to_watts,
    haversine_distance_m,
    linear_to_db,
    rssi_quality_label,
    watts_to_dbm,
)
from scientific.logger import (
    FALLBACK_LEVEL,
    LOG_LEVEL_ENV_VAR,
    ROOT_LOGGER_NAME,
    get_logger,
    set_level,
    silence,
)

# ══════════════════════════════════════════════════════════════════════════
# Tests for scientific/config.py
# ══════════════════════════════════════════════════════════════════════════


class TestSimulationConfig:
    """Tests for SimulationConfig frozen dataclass."""

    def test_default_values(self):
        cfg = SimulationConfig()
        assert cfg.max_iterations == 100
        assert cfg.convergence_threshold_m == 1.0
        assert cfg.default_measurement_count == 1
        assert cfg.enable_noise is True
        assert cfg.default_random_seed is None
        assert cfg.default_algorithm == "multilateration"
        assert cfg.min_towers_for_localization == 3
        assert cfg.max_towers_per_scenario == 50
        assert cfg.max_measurements_per_scenario == 5_000
        assert cfg.position_clamp_lat == (-90.0, 90.0)
        assert cfg.position_clamp_lon == (-180.0, 180.0)

    def test_frozen_immutability(self):
        cfg = SimulationConfig()
        with pytest.raises(AttributeError):
            cfg.max_iterations = 999

    def test_override_creates_new_instance(self):
        cfg = SimulationConfig()
        fast = cfg.override(max_iterations=10, enable_noise=False)
        assert fast.max_iterations == 10
        assert fast.enable_noise is False
        # Original unchanged
        assert cfg.max_iterations == 100
        assert cfg.enable_noise is True

    def test_override_preserves_other_fields(self):
        cfg = SimulationConfig()
        patched = cfg.override(default_algorithm="kalman")
        assert patched.default_algorithm == "kalman"
        assert patched.convergence_threshold_m == cfg.convergence_threshold_m
        assert patched.max_towers_per_scenario == cfg.max_towers_per_scenario

    def test_custom_construction(self):
        cfg = SimulationConfig(
            max_iterations=500,
            convergence_threshold_m=0.5,
            default_random_seed=42,
        )
        assert cfg.max_iterations == 500
        assert cfg.convergence_threshold_m == 0.5
        assert cfg.default_random_seed == 42

    def test_default_singleton_matches_fresh_instance(self):
        assert DEFAULT_SIMULATION_CONFIG == SimulationConfig()


class TestValidationThresholds:
    """Tests for ValidationThresholds frozen dataclass."""

    def test_rssi_bounds(self):
        t = ValidationThresholds()
        assert t.rssi_min_dbm == -150.0
        assert t.rssi_max_dbm == 0.0
        assert t.rssi_plausible_min_dbm == -120.0
        assert t.rssi_plausible_max_dbm == -30.0

    def test_coordinate_bounds(self):
        t = ValidationThresholds()
        assert t.latitude_range == (-90.0, 90.0)
        assert t.longitude_range == (-180.0, 180.0)

    def test_tower_rf_bounds(self):
        t = ValidationThresholds()
        assert t.min_tx_power_dbm == 10.0
        assert t.max_tx_power_dbm == 60.0
        assert t.min_antenna_height_m == 1.0
        assert t.max_antenna_height_m == 300.0
        assert t.max_coverage_radius_m == 50_000.0

    def test_timestamp_threshold(self):
        t = ValidationThresholds()
        assert t.max_measurement_age_days == 365 * 5

    def test_gdop_tiers_ordered(self):
        t = ValidationThresholds()
        assert t.gdop_excellent < t.gdop_good < t.gdop_poor

    def test_confidence_score_range(self):
        t = ValidationThresholds()
        assert t.min_confidence_score == 0.0
        assert t.max_confidence_score == 1.0

    def test_frozen_immutability(self):
        t = ValidationThresholds()
        with pytest.raises(AttributeError):
            t.rssi_min_dbm = -200.0

    def test_default_singleton_matches_fresh_instance(self):
        assert DEFAULT_VALIDATION_THRESHOLDS == ValidationThresholds()


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig and get_environment_config()."""

    @pytest.mark.parametrize("env", ["urban", "suburban", "rural", "highway"])
    def test_preset_exists(self, env):
        assert env in ENVIRONMENT_PRESETS

    @pytest.mark.parametrize("env", ["urban", "suburban", "rural", "highway"])
    def test_get_environment_config_returns_correct_type(self, env):
        cfg = get_environment_config(env)
        assert isinstance(cfg, EnvironmentConfig)
        assert cfg.environment_type == env

    def test_urban_defaults(self):
        cfg = get_environment_config("urban")
        assert cfg.path_loss_exponent == 3.5
        assert cfg.shadow_fading_std_db == 8.0
        assert cfg.reference_distance_m == 1.0
        assert cfg.reference_loss_db == 38.0
        assert cfg.typical_noise_floor_dbm == -95.0

    def test_rural_lower_path_loss(self):
        urban = get_environment_config("urban")
        rural = get_environment_config("rural")
        assert rural.path_loss_exponent < urban.path_loss_exponent

    def test_rural_larger_coverage(self):
        urban = get_environment_config("urban")
        rural = get_environment_config("rural")
        assert rural.typical_coverage_radius_m > urban.typical_coverage_radius_m

    def test_unknown_env_falls_back_to_urban(self):
        cfg = get_environment_config("unknown_env")
        assert cfg == ENVIRONMENT_PRESETS["urban"]

    def test_frozen_immutability(self):
        cfg = get_environment_config("suburban")
        with pytest.raises(AttributeError):
            cfg.path_loss_exponent = 99.9

    def test_all_presets_have_positive_path_loss(self):
        for env, cfg in ENVIRONMENT_PRESETS.items():
            assert cfg.path_loss_exponent > 0, f"{env} path_loss_exponent must be > 0"

    def test_all_presets_have_positive_reference_distance(self):
        for env, cfg in ENVIRONMENT_PRESETS.items():
            assert cfg.reference_distance_m > 0


# ══════════════════════════════════════════════════════════════════════════
# Tests for scientific/constants.py
# ══════════════════════════════════════════════════════════════════════════


class TestPhysicalConstants:
    """Tests for physical & mathematical constants."""

    def test_speed_of_light(self):
        assert SPEED_OF_LIGHT_M_S == pytest.approx(299_792_458.0)

    def test_boltzmann(self):
        assert BOLTZMANN_CONSTANT_J_K == pytest.approx(1.380649e-23)

    def test_pi(self):
        assert PI == pytest.approx(math.pi)

    def test_deg_rad_roundtrip(self):
        assert DEG_TO_RAD * RAD_TO_DEG == pytest.approx(1.0)

    def test_earth_radius(self):
        assert EARTH_RADIUS_M == pytest.approx(6_371_000.0)

    def test_wgs84_semi_major(self):
        assert WGS84_SEMI_MAJOR_M == pytest.approx(6_378_137.0)

    def test_wgs84_flattening(self):
        assert WGS84_FLATTENING_INV == pytest.approx(298.257223563)


class TestUnitConversions:
    """Tests for dB/linear and dBm/Watts conversions."""

    def test_db_to_linear_0db(self):
        assert db_to_linear(0.0) == pytest.approx(1.0)

    def test_db_to_linear_10db(self):
        assert db_to_linear(10.0) == pytest.approx(10.0)

    def test_db_to_linear_negative(self):
        assert db_to_linear(-10.0) == pytest.approx(0.1)

    def test_linear_to_db_roundtrip(self):
        assert linear_to_db(db_to_linear(3.5)) == pytest.approx(3.5)

    def test_linear_to_db_raises_on_zero(self):
        with pytest.raises(ValueError):
            linear_to_db(0)

    def test_linear_to_db_raises_on_negative(self):
        with pytest.raises(ValueError):
            linear_to_db(-1.0)

    def test_dbm_to_watts_30dbm(self):
        # 30 dBm = 1 W
        assert dbm_to_watts(30.0) == pytest.approx(1.0)

    def test_dbm_to_watts_0dbm(self):
        # 0 dBm = 1 mW = 0.001 W
        assert dbm_to_watts(0.0) == pytest.approx(0.001)

    def test_watts_to_dbm_roundtrip(self):
        assert watts_to_dbm(dbm_to_watts(43.0)) == pytest.approx(43.0)

    def test_watts_to_dbm_raises_on_zero(self):
        with pytest.raises(ValueError):
            watts_to_dbm(0)


class TestHaversine:
    """Tests for haversine_distance_m()."""

    def test_same_point_zero_distance(self):
        assert haversine_distance_m(12.97, 77.59, 12.97, 77.59) == pytest.approx(0.0)

    def test_known_distance_bangalore(self):
        # T001 (12.9716, 77.5946) → T002 (12.9750, 77.5900)
        dist = haversine_distance_m(12.9716, 77.5946, 12.9750, 77.5900)
        # Expect ~600 m (typical urban tower spacing)
        assert 300 < dist < 1200

    def test_equator_one_degree_longitude(self):
        # At equator, 1° longitude ≈ 111.32 km
        dist = haversine_distance_m(0.0, 0.0, 0.0, 1.0)
        assert dist == pytest.approx(111_195, rel=0.01)

    def test_symmetry(self):
        d1 = haversine_distance_m(10.0, 20.0, 30.0, 40.0)
        d2 = haversine_distance_m(30.0, 40.0, 10.0, 20.0)
        assert d1 == pytest.approx(d2)


class TestCellularBands:
    """Tests for cellular frequency band constants."""

    def test_bands_list_not_empty(self):
        assert len(CELLULAR_BANDS_MHZ) > 0

    def test_bands_sorted(self):
        assert CELLULAR_BANDS_MHZ == sorted(CELLULAR_BANDS_MHZ)

    def test_1800_mhz_in_bands(self):
        assert 1800 in CELLULAR_BANDS_MHZ

    def test_band_tolerance_positive(self):
        assert BAND_TOLERANCE_MHZ > 0

    def test_band_groups_cover_all_bands(self):
        all_from_groups = set()
        for bands in BAND_GROUPS.values():
            all_from_groups.update(bands)
        assert all_from_groups == set(CELLULAR_BANDS_MHZ)


class TestRSSIConstants:
    """Tests for RSSI reference levels and quality tiers."""

    def test_absolute_range_contains_plausible(self):
        assert RSSI_ABSOLUTE_MIN_DBM <= RSSI_PLAUSIBLE_MIN_DBM
        assert RSSI_PLAUSIBLE_MAX_DBM <= RSSI_ABSOLUTE_MAX_DBM

    def test_quality_tiers_non_overlapping(self):
        # Each tier's low < high
        for label, (low, high) in RSSI_QUALITY_TIERS.items():
            assert low < high, f"Tier '{label}' has invalid range"

    def test_rssi_quality_label_excellent(self):
        assert rssi_quality_label(-40.0) == "excellent"

    def test_rssi_quality_label_good(self):
        assert rssi_quality_label(-60.0) == "good"

    def test_rssi_quality_label_weak(self):
        assert rssi_quality_label(-100.0) == "weak"

    def test_rssi_quality_label_out_of_range(self):
        assert rssi_quality_label(10.0) == "out_of_range"


class TestTimingAdvanceConstants:
    """Tests for GSM Timing Advance constants."""

    def test_ta_resolution_positive(self):
        assert TA_RESOLUTION_M > 0

    def test_ta_max_value(self):
        assert TA_MAX_VALUE == 63

    def test_ta_max_distance_consistent(self):
        assert TA_MAX_DISTANCE_M == pytest.approx(TA_RESOLUTION_M * TA_MAX_VALUE)


class TestTowerDefaults:
    """Tests for tower parameter defaults and bounds."""

    def test_defaults_within_bounds(self):
        assert MIN_TX_POWER_DBM <= DEFAULT_TRANSMIT_POWER_DBM <= MAX_TX_POWER_DBM
        assert MIN_ANTENNA_HEIGHT_M <= DEFAULT_ANTENNA_HEIGHT_M <= MAX_ANTENNA_HEIGHT_M
        assert DEFAULT_COVERAGE_RADIUS_M <= MAX_COVERAGE_RADIUS_M

    def test_default_frequency_in_cellular_bands(self):
        # Default 1800 MHz should be near a known band
        near = any(
            abs(DEFAULT_FREQUENCY_MHZ - band) <= BAND_TOLERANCE_MHZ
            for band in CELLULAR_BANDS_MHZ
        )
        assert near

    def test_coordinate_ranges(self):
        assert LATITUDE_RANGE == (-90.0, 90.0)
        assert LONGITUDE_RANGE == (-180.0, 180.0)


class TestDerivedRFConstants:
    """Tests for derived RF constants (FSPL, thermal noise)."""

    def test_free_space_loss_reasonable(self):
        # FSPL at 1m, 1GHz should be ~32.44 dB
        assert FREE_SPACE_LOSS_1M_1GHZ_DB == pytest.approx(32.44, abs=0.1)

    def test_thermal_noise_reasonable(self):
        # kTB at 290K, 1Hz ≈ -174 dBm/Hz
        assert THERMAL_NOISE_DBM_HZ == pytest.approx(-174.0, abs=0.1)

    def test_boltzmann_dbm_reasonable(self):
        # k in dBm/Hz/K ≈ -198.6
        assert BOLTZMANN_DBM_HZ_K == pytest.approx(-198.6, abs=0.1)


# ══════════════════════════════════════════════════════════════════════════
# Tests for scientific/logger.py
# ══════════════════════════════════════════════════════════════════════════


class TestGetLogger:
    """Tests for get_logger()."""

    def test_returns_logger_instance(self):
        log = get_logger("test.config_logger")
        assert isinstance(log, logging.Logger)

    def test_default_name_is_scientific(self):
        log = get_logger()
        assert log.name == ROOT_LOGGER_NAME

    def test_custom_name(self):
        log = get_logger("scientific.validation.test")
        assert log.name == "scientific.validation.test"

    def test_has_handler(self):
        log = get_logger("test.handler_check")
        assert len(log.handlers) >= 1

    def test_idempotent_no_duplicate_handlers(self):
        name = "test.idempotent_check"
        log1 = get_logger(name)
        count = len(log1.handlers)
        log2 = get_logger(name)
        assert len(log2.handlers) == count
        assert log1 is log2

    def test_default_level_is_info(self):
        log = get_logger("test.level_check")
        assert log.level == logging.INFO

    def test_custom_level_string(self):
        log = get_logger("test.custom_level_str", level="DEBUG")
        assert log.level == logging.DEBUG

    def test_custom_level_int(self):
        log = get_logger("test.custom_level_int", level=logging.WARNING)
        assert log.level == logging.WARNING

    def test_propagation_disabled(self):
        log = get_logger("test.propagation")
        assert log.propagate is False


class TestSetLevel:
    """Tests for set_level()."""

    def test_set_level_by_string(self):
        log = get_logger("test.set_level_str")
        set_level("DEBUG", "test.set_level_str")
        assert log.level == logging.DEBUG

    def test_set_level_by_int(self):
        log = get_logger("test.set_level_int")
        set_level(logging.ERROR, "test.set_level_int")
        assert log.level == logging.ERROR

    def test_set_level_default_root(self):
        original = logging.getLogger(ROOT_LOGGER_NAME).level
        set_level("WARNING")
        assert logging.getLogger(ROOT_LOGGER_NAME).level == logging.WARNING
        # Restore
        set_level(original)


class TestSilence:
    """Tests for silence()."""

    def test_silence_raises_level_above_critical(self):
        log = get_logger("test.silence_check")
        silence("test.silence_check")
        assert log.level > logging.CRITICAL

    def test_silence_default_root(self):
        original = logging.getLogger(ROOT_LOGGER_NAME).level
        silence()
        assert logging.getLogger(ROOT_LOGGER_NAME).level > logging.CRITICAL
        # Restore
        set_level(original)


class TestLogLevelEnvVar:
    """Tests for ASTERION_LOG_LEVEL environment variable."""

    def test_env_var_override(self, monkeypatch):
        monkeypatch.setenv(LOG_LEVEL_ENV_VAR, "DEBUG")
        # Use a unique name so it starts fresh
        get_logger("test.env_override")
        # Force re-resolution by creating a new logger
        from scientific.logger import _resolve_level

        assert _resolve_level() == logging.DEBUG

    def test_env_var_not_set_uses_fallback(self, monkeypatch):
        monkeypatch.delenv(LOG_LEVEL_ENV_VAR, raising=False)
        from scientific.logger import _resolve_level

        assert _resolve_level() == FALLBACK_LEVEL
