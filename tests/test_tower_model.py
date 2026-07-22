"""
Tower Model Unit Tests
========================

Comprehensive unit tests for ``scientific.models.tower.Tower`` covering:

- Construction with default values
- Construction with all explicit values
- Required field validation (tower_id, latitude, longitude)
- Boundary conditions (lat/lon edges, zero-crossing, poles)
- Field constraints (min_length, ge/le/gt)
- Optional sector field handling
- JSON serialization and deserialization round-trip
- Model schema and json_schema_extra
- Integration with TowerValidator domain validation
- Loading from sample dataset file

Test count: 45 tests
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scientific.models.tower import Tower
from scientific.validation.validators import TowerValidator, Severity


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def minimal_tower() -> Tower:
    """Tower with only required fields (tower_id, latitude, longitude)."""
    return Tower(tower_id="T001", latitude=12.9716, longitude=77.5946)


@pytest.fixture
def full_tower() -> Tower:
    """Tower with all fields explicitly set."""
    return Tower(
        tower_id="T001",
        latitude=12.9716,
        longitude=77.5946,
        antenna_height_m=35.0,
        frequency_mhz=1800.0,
        transmit_power_dbm=43.0,
        sector="A",
        coverage_radius_m=1200.0,
    )


@pytest.fixture
def tower_validator() -> TowerValidator:
    """Pre-constructed TowerValidator instance."""
    return TowerValidator()


# ═══════════════════════════════════════════════════════════════════════════
# 1. Construction — Defaults
# ═══════════════════════════════════════════════════════════════════════════


class TestTowerDefaults:
    """Tests for Tower model construction with default values."""

    def test_minimal_construction_succeeds(self, minimal_tower):
        assert minimal_tower.tower_id == "T001"
        assert minimal_tower.latitude == 12.9716
        assert minimal_tower.longitude == 77.5946

    def test_default_antenna_height(self, minimal_tower):
        assert minimal_tower.antenna_height_m == 30.0

    def test_default_frequency(self, minimal_tower):
        assert minimal_tower.frequency_mhz == 1800.0

    def test_default_transmit_power(self, minimal_tower):
        assert minimal_tower.transmit_power_dbm == 43.0

    def test_default_sector_is_none(self, minimal_tower):
        assert minimal_tower.sector is None

    def test_default_coverage_radius(self, minimal_tower):
        assert minimal_tower.coverage_radius_m == 1000.0


# ═══════════════════════════════════════════════════════════════════════════
# 2. Construction — All Fields
# ═══════════════════════════════════════════════════════════════════════════


class TestTowerFullConstruction:
    """Tests for Tower model with all fields explicitly provided."""

    def test_all_fields_set(self, full_tower):
        assert full_tower.tower_id == "T001"
        assert full_tower.latitude == 12.9716
        assert full_tower.longitude == 77.5946
        assert full_tower.antenna_height_m == 35.0
        assert full_tower.frequency_mhz == 1800.0
        assert full_tower.transmit_power_dbm == 43.0
        assert full_tower.sector == "A"
        assert full_tower.coverage_radius_m == 1200.0

    def test_sector_string_values(self):
        """Sector can be any string (A, B, C, alpha, etc.)."""
        for sec in ["A", "B", "C", "alpha", "sector-1"]:
            t = Tower(tower_id="TX", latitude=0.0, longitude=0.0, sector=sec)
            assert t.sector == sec


# ═══════════════════════════════════════════════════════════════════════════
# 3. Required Field Validation
# ═══════════════════════════════════════════════════════════════════════════


class TestTowerRequiredFields:
    """Tests that missing required fields raise ValidationError."""

    def test_missing_tower_id_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            Tower(latitude=12.0, longitude=77.0)
        assert "tower_id" in str(exc_info.value)

    def test_missing_latitude_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            Tower(tower_id="T001", longitude=77.0)
        assert "latitude" in str(exc_info.value)

    def test_missing_longitude_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            Tower(tower_id="T001", latitude=12.0)
        assert "longitude" in str(exc_info.value)

    def test_empty_tower_id_raises(self):
        """tower_id has min_length=1, so empty string should fail."""
        with pytest.raises(ValidationError):
            Tower(tower_id="", latitude=12.0, longitude=77.0)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Boundary Conditions — Coordinates
# ═══════════════════════════════════════════════════════════════════════════


class TestTowerCoordinateBoundaries:
    """Tests for latitude and longitude edge cases."""

    @pytest.mark.parametrize(
        "lat,lon,desc",
        [
            (90.0, 0.0, "North Pole"),
            (-90.0, 0.0, "South Pole"),
            (0.0, 180.0, "Date Line East"),
            (0.0, -180.0, "Date Line West"),
            (0.0, 0.0, "Null Island"),
            (-33.8688, 151.2093, "Sydney"),
            (40.7128, -74.0060, "New York"),
        ],
    )
    def test_valid_coordinates(self, lat, lon, desc):
        t = Tower(tower_id=f"T-{desc}", latitude=lat, longitude=lon)
        assert t.latitude == lat
        assert t.longitude == lon

    def test_latitude_above_90_raises(self):
        with pytest.raises(ValidationError):
            Tower(tower_id="T001", latitude=90.1, longitude=0.0)

    def test_latitude_below_minus_90_raises(self):
        with pytest.raises(ValidationError):
            Tower(tower_id="T001", latitude=-90.1, longitude=0.0)

    def test_longitude_above_180_raises(self):
        with pytest.raises(ValidationError):
            Tower(tower_id="T001", latitude=0.0, longitude=180.1)

    def test_longitude_below_minus_180_raises(self):
        with pytest.raises(ValidationError):
            Tower(tower_id="T001", latitude=0.0, longitude=-180.1)


# ═══════════════════════════════════════════════════════════════════════════
# 5. Field Constraints — Physical Parameters
# ═══════════════════════════════════════════════════════════════════════════


class TestTowerFieldConstraints:
    """Tests for gt/ge/le constraints on physical parameter fields."""

    def test_antenna_height_must_be_positive(self):
        with pytest.raises(ValidationError):
            Tower(
                tower_id="T001",
                latitude=0.0,
                longitude=0.0,
                antenna_height_m=0.0,
            )

    def test_antenna_height_negative_raises(self):
        with pytest.raises(ValidationError):
            Tower(
                tower_id="T001",
                latitude=0.0,
                longitude=0.0,
                antenna_height_m=-5.0,
            )

    def test_frequency_must_be_positive(self):
        with pytest.raises(ValidationError):
            Tower(
                tower_id="T001",
                latitude=0.0,
                longitude=0.0,
                frequency_mhz=0.0,
            )

    def test_coverage_radius_must_be_positive(self):
        with pytest.raises(ValidationError):
            Tower(
                tower_id="T001",
                latitude=0.0,
                longitude=0.0,
                coverage_radius_m=0.0,
            )

    def test_very_small_positive_values_accepted(self):
        """Positive epsilon values should be accepted for gt=0 fields."""
        t = Tower(
            tower_id="T001",
            latitude=0.0,
            longitude=0.0,
            antenna_height_m=0.01,
            frequency_mhz=0.01,
            coverage_radius_m=0.01,
        )
        assert t.antenna_height_m == 0.01

    def test_transmit_power_accepts_negative(self):
        """transmit_power_dbm has no lower bound in the model."""
        t = Tower(
            tower_id="T001",
            latitude=0.0,
            longitude=0.0,
            transmit_power_dbm=-10.0,
        )
        assert t.transmit_power_dbm == -10.0


# ═══════════════════════════════════════════════════════════════════════════
# 6. JSON Serialization Round-Trip
# ═══════════════════════════════════════════════════════════════════════════


class TestTowerSerialization:
    """Tests for JSON serialization and deserialization."""

    def test_model_dump_contains_all_fields(self, full_tower):
        data = full_tower.model_dump()
        expected_keys = {
            "tower_id",
            "latitude",
            "longitude",
            "antenna_height_m",
            "frequency_mhz",
            "transmit_power_dbm",
            "sector",
            "coverage_radius_m",
        }
        assert set(data.keys()) == expected_keys

    def test_json_roundtrip(self, full_tower):
        json_str = full_tower.model_dump_json()
        restored = Tower.model_validate_json(json_str)
        assert restored == full_tower

    def test_dict_roundtrip(self, full_tower):
        data = full_tower.model_dump()
        restored = Tower.model_validate(data)
        assert restored == full_tower

    def test_model_json_schema_has_examples(self):
        schema = Tower.model_json_schema()
        assert "examples" in schema

    def test_model_json_schema_example_is_valid(self):
        """The JSON schema example should be parseable as a valid Tower."""
        schema = Tower.model_json_schema()
        for example in schema["examples"]:
            tower = Tower.model_validate(example)
            assert tower.tower_id == "T001"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Integration with TowerValidator
# ═══════════════════════════════════════════════════════════════════════════


class TestTowerValidatorIntegration:
    """Tests that TowerValidator accepts/warns for various Tower instances."""

    def test_standard_tower_passes_validation(self, full_tower, tower_validator):
        result = tower_validator.validate(full_tower)
        assert result.is_valid

    def test_standard_tower_no_errors(self, full_tower, tower_validator):
        result = tower_validator.validate(full_tower)
        errors_only = [e for e in result.errors if e.severity == Severity.ERROR]
        assert len(errors_only) == 0

    def test_unusual_frequency_triggers_warning(self, tower_validator):
        t = Tower(
            tower_id="T001",
            latitude=0.0,
            longitude=0.0,
            frequency_mhz=999.0,  # Not near any standard band
        )
        result = tower_validator.validate(t)
        # Should still be valid (warnings only, no errors)
        assert result.is_valid
        warning_codes = [e.code for e in result.warnings]
        assert "TOWER_UNUSUAL_FREQ" in warning_codes

    def test_extreme_transmit_power_triggers_warning(self, tower_validator):
        t = Tower(
            tower_id="T001",
            latitude=0.0,
            longitude=0.0,
            transmit_power_dbm=70.0,  # Outside [10, 60] range
        )
        result = tower_validator.validate(t)
        assert result.is_valid
        warning_codes = [e.code for e in result.warnings]
        assert "TOWER_TX_POWER_RANGE" in warning_codes

    def test_extreme_coverage_radius_triggers_warning(self, tower_validator):
        t = Tower(
            tower_id="T001",
            latitude=0.0,
            longitude=0.0,
            coverage_radius_m=51_000.0,  # Above 50,000 m
        )
        result = tower_validator.validate(t)
        assert result.is_valid
        warning_codes = [e.code for e in result.warnings]
        assert "TOWER_COVERAGE_EXTREME" in warning_codes


# ═══════════════════════════════════════════════════════════════════════════
# 8. Sample Dataset Loading
# ═══════════════════════════════════════════════════════════════════════════


class TestTowerFromDataset:
    """Tests that towers defined in the sample dataset parse correctly."""

    @pytest.fixture
    def dataset_towers(self) -> list[Tower]:
        dataset_path = (
            Path(__file__).resolve().parent.parent
            / "datasets"
            / "sample"
            / "sample_dataset.json"
        )
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Tower.model_validate(t) for t in data["towers"]]

    def test_dataset_loads_four_towers(self, dataset_towers):
        assert len(dataset_towers) == 4

    def test_dataset_tower_ids_unique(self, dataset_towers):
        ids = [t.tower_id for t in dataset_towers]
        assert len(ids) == len(set(ids))

    def test_dataset_towers_have_valid_coordinates(self, dataset_towers):
        for t in dataset_towers:
            assert -90.0 <= t.latitude <= 90.0
            assert -180.0 <= t.longitude <= 180.0

    def test_dataset_towers_pass_validation(self, dataset_towers):
        validator = TowerValidator()
        for t in dataset_towers:
            result = validator.validate(t)
            assert result.is_valid, (
                f"Tower {t.tower_id} failed validation: "
                f"{[e.message for e in result.errors]}"
            )
