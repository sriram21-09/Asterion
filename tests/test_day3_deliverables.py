"""
Comprehensive Day 3 Verification Tests
========================================

Tests every deliverable from Day 3 (Chaitanya — Scientific Engineer):
  1. scientific/validation/validators.py — interfaces & concrete validators
  2. datasets/sample/sample_dataset.json — sample dataset integrity
  3. backend/app/shared/validation.py — shared input validation helpers
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))


# =====================================================================
# DELIVERABLE 1: scientific/validation/validators.py
# =====================================================================

from scientific.models.measurement import Measurement
from scientific.models.tower import Tower
from scientific.models.scenario import Scenario
from scientific.validation.validators import (
    MeasurementValidator,
    TowerValidator,
    ScenarioValidator,
    ValidationResult,
    ValidationError as SciValidationError,
    Severity,
    validate_measurement,
    validate_tower,
    validate_scenario,
)


class TestValidationResultTypes:
    """Test ValidationResult, ValidationError, Severity."""

    def test_empty_result_is_valid(self):
        r = ValidationResult()
        assert r.is_valid is True
        assert r.errors == []
        assert r.warnings == []

    def test_result_with_error_is_invalid(self):
        r = ValidationResult(
            errors=[
                SciValidationError(field="x", message="bad", severity=Severity.ERROR)
            ]
        )
        assert r.is_valid is False

    def test_result_with_only_warnings_is_valid(self):
        r = ValidationResult(
            errors=[
                SciValidationError(field="x", message="warn", severity=Severity.WARNING)
            ]
        )
        assert r.is_valid is True
        assert len(r.warnings) == 1

    def test_merge_combines_results(self):
        r1 = ValidationResult(errors=[SciValidationError(field="a", message="err1")])
        r2 = ValidationResult(errors=[SciValidationError(field="b", message="err2")])
        r1.merge(r2)
        assert len(r1.errors) == 2

    def test_severity_enum_values(self):
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"


class TestMeasurementValidator:
    """Test MeasurementValidator with various edge cases."""

    def setup_method(self):
        self.validator = MeasurementValidator()

    def _make(self, **overrides):
        defaults = dict(
            measurement_id="M001",
            tower_id="T001",
            timestamp=datetime(2026, 7, 7, 10, 30, tzinfo=timezone.utc),
            rssi_dbm=-72.0,
        )
        defaults.update(overrides)
        return Measurement(**defaults)

    def test_valid_measurement_passes(self):
        m = self._make(latitude=12.97, longitude=77.59)
        r = self.validator.validate(m)
        assert r.is_valid is True
        assert len(r.errors) == 0

    def test_partial_coordinates_fails(self):
        m = self._make(latitude=12.97)  # longitude is None
        r = self.validator.validate(m)
        assert r.is_valid is False
        assert any("MEAS_PARTIAL_COORDS" == e.code for e in r.errors)

    def test_rssi_too_strong_warns(self):
        m = self._make(rssi_dbm=-20.0)
        r = self.validator.validate(m)
        assert r.is_valid is True  # warning, not error
        assert any("MEAS_RSSI_HIGH" == e.code for e in r.errors)

    def test_rssi_too_weak_warns(self):
        m = self._make(rssi_dbm=-130.0)
        r = self.validator.validate(m)
        assert r.is_valid is True
        assert any("MEAS_RSSI_LOW" == e.code for e in r.errors)

    def test_ta_rssi_mismatch_warns(self):
        m = self._make(rssi_dbm=-45.0, timing_advance=15.0)
        r = self.validator.validate(m)
        assert any("MEAS_TA_RSSI_MISMATCH" == e.code for e in r.errors)

    def test_future_timestamp_fails(self):
        future = datetime.now(timezone.utc) + timedelta(days=1)
        m = self._make(timestamp=future)
        r = self.validator.validate(m)
        assert r.is_valid is False
        assert any("MEAS_FUTURE_TIMESTAMP" == e.code for e in r.errors)

    def test_convenience_function(self):
        m = self._make()
        r = validate_measurement(m)
        assert r.is_valid is True


class TestTowerValidator:
    """Test TowerValidator with various edge cases."""

    def setup_method(self):
        self.validator = TowerValidator()

    def _make(self, **overrides):
        defaults = dict(
            tower_id="T001",
            latitude=12.97,
            longitude=77.59,
            frequency_mhz=1800.0,
            transmit_power_dbm=43.0,
            antenna_height_m=35.0,
            coverage_radius_m=1200.0,
        )
        defaults.update(overrides)
        return Tower(**defaults)

    def test_valid_tower_passes(self):
        t = self._make()
        r = self.validator.validate(t)
        assert r.is_valid is True
        assert len(r.errors) == 0

    def test_unusual_frequency_warns(self):
        t = self._make(frequency_mhz=1234.0)  # Not near any standard band
        r = self.validator.validate(t)
        assert any("TOWER_UNUSUAL_FREQ" == e.code for e in r.errors)

    def test_known_frequencies_pass(self):
        for freq in [700, 900, 1800, 2100, 2600, 3500]:
            t = self._make(frequency_mhz=float(freq))
            r = self.validator.validate(t)
            assert not any("TOWER_UNUSUAL_FREQ" == e.code for e in r.errors), (
                f"Frequency {freq} MHz incorrectly flagged"
            )

    def test_extreme_tx_power_warns(self):
        t = self._make(transmit_power_dbm=5.0)  # below MIN_TX_POWER_DBM
        r = self.validator.validate(t)
        assert any("TOWER_TX_POWER_RANGE" == e.code for e in r.errors)

    def test_convenience_function(self):
        t = self._make()
        r = validate_tower(t)
        assert r.is_valid is True


class TestScenarioValidator:
    """Test ScenarioValidator with various edge cases."""

    def setup_method(self):
        self.validator = ScenarioValidator()

    def _make_towers(self, count=3):
        towers = []
        for i in range(count):
            towers.append(
                Tower(
                    tower_id=f"T{i + 1:03d}",
                    latitude=12.97 + i * 0.003,
                    longitude=77.59 - i * 0.005,
                )
            )
        return towers

    def _make_measurements(self, tower_ids):
        meas = []
        for i, tid in enumerate(tower_ids):
            meas.append(
                Measurement(
                    measurement_id=f"M{i + 1:03d}",
                    tower_id=tid,
                    timestamp=datetime(2026, 7, 7, 10, 30, i, tzinfo=timezone.utc),
                    rssi_dbm=-70.0 - i * 5,
                )
            )
        return meas

    def test_valid_scenario_passes(self):
        towers = self._make_towers(3)
        meas = self._make_measurements(["T001", "T002", "T003"])
        scn = Scenario(
            scenario_id="SCN-001",
            name="Test",
            towers=towers,
            measurements=meas,
            expected_device_lat=12.972,
            expected_device_lon=77.595,
        )
        r = self.validator.validate(scn)
        assert r.is_valid is True

    def test_duplicate_tower_ids_fail(self):
        towers = [
            Tower(tower_id="T001", latitude=12.97, longitude=77.59),
            Tower(tower_id="T001", latitude=12.98, longitude=77.58),  # duplicate
            Tower(tower_id="T002", latitude=12.96, longitude=77.60),
        ]
        scn = Scenario(scenario_id="SCN-001", name="Dup Test", towers=towers)
        r = self.validator.validate(scn)
        assert r.is_valid is False
        assert any("SCENARIO_DUPLICATE_TOWER" == e.code for e in r.errors)

    def test_orphan_measurement_fails(self):
        towers = self._make_towers(3)
        meas = [
            Measurement(
                measurement_id="M001",
                tower_id="T999",  # doesn't exist
                timestamp=datetime(2026, 7, 7, 10, 30, tzinfo=timezone.utc),
                rssi_dbm=-72.0,
            )
        ]
        scn = Scenario(
            scenario_id="SCN-001",
            name="Orphan Test",
            towers=towers,
            measurements=meas,
        )
        r = self.validator.validate(scn)
        assert r.is_valid is False
        assert any("SCENARIO_ORPHAN_MEASUREMENT" == e.code for e in r.errors)

    def test_partial_ground_truth_fails(self):
        towers = self._make_towers(3)
        scn = Scenario(
            scenario_id="SCN-001",
            name="GT Test",
            towers=towers,
            expected_device_lat=12.97,
            # expected_device_lon is None
        )
        r = self.validator.validate(scn)
        assert r.is_valid is False
        assert any("SCENARIO_PARTIAL_GROUND_TRUTH" == e.code for e in r.errors)

    def test_uncovered_tower_warns(self):
        towers = self._make_towers(3)
        # Only measurement for T001, T002 missing T003
        meas = self._make_measurements(["T001", "T002"])
        scn = Scenario(
            scenario_id="SCN-001",
            name="Coverage Test",
            towers=towers,
            measurements=meas,
        )
        r = self.validator.validate(scn)
        assert any("SCENARIO_UNCOVERED_TOWER" == e.code for e in r.errors)

    def test_shallow_validation_skips_deep(self):
        shallow = ScenarioValidator(deep=False)
        towers = self._make_towers(3)
        scn = Scenario(scenario_id="SCN-001", name="Shallow", towers=towers)
        r = shallow.validate(scn)
        # No tower/measurement sub-validation findings
        tower_sub_errors = [e for e in r.errors if e.field.startswith("towers[")]
        assert len(tower_sub_errors) == 0

    def test_convenience_function(self):
        towers = self._make_towers(3)
        scn = Scenario(scenario_id="SCN-001", name="Conv", towers=towers)
        r = validate_scenario(scn)
        assert r.is_valid is True


# =====================================================================
# DELIVERABLE 2: datasets/sample/sample_dataset.json
# =====================================================================


class TestSampleDataset:
    """Validate the sample dataset's structure and data integrity."""

    @pytest.fixture(autouse=True)
    def load_dataset(self):
        dataset_path = ROOT / "datasets" / "sample" / "sample_dataset.json"
        assert dataset_path.exists(), f"Dataset not found at {dataset_path}"
        with open(dataset_path) as f:
            self.data = json.load(f)

    def test_has_metadata(self):
        meta = self.data["metadata"]
        assert meta["dataset_id"] == "DS-SAMPLE-001"
        assert meta["coordinate_system"] == "WGS84"
        assert "units" in meta

    def test_has_towers(self):
        towers = self.data["towers"]
        assert len(towers) == 4
        tower_ids = {t["tower_id"] for t in towers}
        assert tower_ids == {"T001", "T002", "T003", "T004"}

    def test_towers_load_as_pydantic(self):
        for t in self.data["towers"]:
            tower = Tower(**t)
            assert tower.tower_id

    def test_has_scenarios(self):
        assert len(self.data["scenarios"]) == 2

    def test_scenario_tower_refs_valid(self):
        """Every tower_id referenced in scenarios must exist in the towers list."""
        valid_ids = {t["tower_id"] for t in self.data["towers"]}
        for sc in self.data["scenarios"]:
            for tid in sc["tower_ids"]:
                assert tid in valid_ids, (
                    f"Scenario {sc['scenario_id']} refs unknown tower {tid}"
                )

    def test_measurement_tower_refs_valid(self):
        """Every measurement must reference a tower from its scenario."""
        for sc in self.data["scenarios"]:
            scenario_tower_ids = set(sc["tower_ids"])
            for m in sc["measurements"]:
                assert m["tower_id"] in scenario_tower_ids, (
                    f"Measurement {m['measurement_id']} refs tower {m['tower_id']} "
                    f"not in scenario {sc['scenario_id']}"
                )

    def test_measurements_load_as_pydantic(self):
        for sc in self.data["scenarios"]:
            for m in sc["measurements"]:
                meas = Measurement(**m)
                assert meas.measurement_id

    def test_measurement_ids_unique(self):
        all_ids = []
        for sc in self.data["scenarios"]:
            for m in sc["measurements"]:
                all_ids.append(m["measurement_id"])
        assert len(all_ids) == len(set(all_ids)), "Duplicate measurement IDs found"

    def test_total_measurements(self):
        total = sum(len(sc["measurements"]) for sc in self.data["scenarios"])
        assert total == 14

    def test_scenarios_validate_clean(self):
        """Each scenario must pass ScenarioValidator without errors."""
        tower_map = {t["tower_id"]: Tower(**t) for t in self.data["towers"]}
        sv = ScenarioValidator()
        for sc in self.data["scenarios"]:
            towers = [tower_map[tid] for tid in sc["tower_ids"]]
            measurements = [Measurement(**m) for m in sc["measurements"]]
            scenario = Scenario(
                scenario_id=sc["scenario_id"],
                name=sc["name"],
                description=sc.get("description"),
                towers=towers,
                measurements=measurements,
                noise_level_dbm=sc["noise_level_dbm"],
                environment_type=sc["environment_type"],
                expected_device_lat=sc.get("expected_device_lat"),
                expected_device_lon=sc.get("expected_device_lon"),
            )
            r = sv.validate(scenario)
            assert r.is_valid, (
                f"Scenario {sc['scenario_id']} has validation errors: "
                f"{[(e.field, e.message) for e in r.errors if e.severity == Severity.ERROR]}"
            )

    def test_has_expected_results(self):
        er = self.data["expected_results"]
        assert "SCN-SAMPLE-001" in er
        assert "SCN-SAMPLE-002" in er
        for key, val in er.items():
            assert "expected_latitude" in val
            assert "expected_longitude" in val
            assert "max_error_m" in val
            assert "min_confidence_score" in val

    def test_rssi_values_in_range(self):
        """All RSSI values should be within [-150, 0] dBm."""
        for sc in self.data["scenarios"]:
            for m in sc["measurements"]:
                assert -150.0 <= m["rssi_dbm"] <= 0.0, (
                    f"RSSI {m['rssi_dbm']} out of range in {m['measurement_id']}"
                )


# =====================================================================
# DELIVERABLE 3: backend/app/shared/validation.py
# =====================================================================

from app.shared.validation import (
    validate_id_format,
    validate_non_empty_string,
    validate_latitude,
    validate_longitude,
    validate_coordinates,
    validate_coordinate_pair_optional,
    validate_rssi,
    validate_positive_float,
    validate_pagination,
    pagination_offset,
    validate_list_not_empty,
    validate_unique_ids,
    validate_timestamp_not_future,
    validate_timestamp_range,
    validate_minimum_signals,
    ValidationError as BackendValidationError,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)


class TestIdValidation:
    def test_valid_id(self):
        assert validate_id_format("SCN-001", "id") == "SCN-001"

    def test_valid_id_with_prefix(self):
        assert validate_id_format("SCN-001", "id", prefix="SCN") == "SCN-001"

    def test_invalid_prefix_rejected(self):
        with pytest.raises(BackendValidationError, match="prefix"):
            validate_id_format("T001", "id", prefix="SCN")

    def test_empty_id_rejected(self):
        with pytest.raises(BackendValidationError):
            validate_id_format("", "id")

    def test_whitespace_only_rejected(self):
        with pytest.raises(BackendValidationError):
            validate_id_format("   ", "id")

    def test_too_long_rejected(self):
        with pytest.raises(BackendValidationError):
            validate_id_format("A" * 100, "id", max_length=64)

    def test_special_characters_rejected(self):
        with pytest.raises(BackendValidationError):
            validate_id_format("bad id!", "id")

    def test_strips_whitespace(self):
        assert validate_id_format("  SCN-001  ", "id") == "SCN-001"


class TestStringValidation:
    def test_valid_string(self):
        assert validate_non_empty_string("Hello", "name") == "Hello"

    def test_empty_rejected(self):
        with pytest.raises(BackendValidationError):
            validate_non_empty_string("", "name")

    def test_too_long_rejected(self):
        with pytest.raises(BackendValidationError):
            validate_non_empty_string("A" * 600, "name", max_length=500)


class TestCoordinateValidation:
    def test_valid_lat(self):
        assert validate_latitude(12.97) == 12.97

    def test_lat_boundaries(self):
        assert validate_latitude(-90.0) == -90.0
        assert validate_latitude(90.0) == 90.0

    def test_invalid_lat(self):
        with pytest.raises(BackendValidationError):
            validate_latitude(91.0)
        with pytest.raises(BackendValidationError):
            validate_latitude(-91.0)

    def test_valid_lon(self):
        assert validate_longitude(77.59) == 77.59

    def test_invalid_lon(self):
        with pytest.raises(BackendValidationError):
            validate_longitude(181.0)

    def test_coordinate_pair(self):
        assert validate_coordinates(12.97, 77.59) == (12.97, 77.59)

    def test_optional_pair_both_none(self):
        assert validate_coordinate_pair_optional(None, None) == (None, None)

    def test_optional_pair_partial_fails(self):
        with pytest.raises(BackendValidationError):
            validate_coordinate_pair_optional(12.97, None)


class TestNumericValidation:
    def test_valid_rssi(self):
        assert validate_rssi(-72.0) == -72.0

    def test_rssi_boundaries(self):
        assert validate_rssi(-150.0) == -150.0
        assert validate_rssi(0.0) == 0.0

    def test_invalid_rssi(self):
        with pytest.raises(BackendValidationError):
            validate_rssi(-151.0)
        with pytest.raises(BackendValidationError):
            validate_rssi(1.0)

    def test_positive_float(self):
        assert validate_positive_float(1.0, "height") == 1.0

    def test_zero_rejected_by_default(self):
        with pytest.raises(BackendValidationError):
            validate_positive_float(0.0, "height")

    def test_zero_allowed_when_specified(self):
        assert validate_positive_float(0.0, "offset", allow_zero=True) == 0.0

    def test_negative_rejected(self):
        with pytest.raises(BackendValidationError):
            validate_positive_float(-1.0, "height")


class TestPaginationValidation:
    def test_defaults(self):
        assert validate_pagination() == (DEFAULT_PAGE, DEFAULT_PAGE_SIZE)

    def test_custom_values(self):
        assert validate_pagination(3, 50) == (3, 50)

    def test_page_zero_rejected(self):
        with pytest.raises(BackendValidationError):
            validate_pagination(0, 20)

    def test_page_size_exceeds_max(self):
        with pytest.raises(BackendValidationError):
            validate_pagination(1, MAX_PAGE_SIZE + 1)

    def test_offset_calculation(self):
        assert pagination_offset(1, 20) == 0
        assert pagination_offset(2, 20) == 20
        assert pagination_offset(3, 50) == 100


class TestCollectionValidation:
    def test_non_empty_list(self):
        items = [1, 2, 3]
        assert validate_list_not_empty(items, "signals") == items

    def test_empty_list_rejected(self):
        with pytest.raises(BackendValidationError):
            validate_list_not_empty([], "signals")

    def test_exceeds_max_rejected(self):
        with pytest.raises(BackendValidationError):
            validate_list_not_empty(list(range(600)), "signals", max_items=500)

    def test_unique_ids(self):
        items = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
        ids = validate_unique_ids(items, "id")
        assert ids == ["A", "B", "C"]

    def test_duplicate_ids_rejected(self):
        items = [{"id": "A"}, {"id": "A"}]
        with pytest.raises(BackendValidationError, match="Duplicate"):
            validate_unique_ids(items, "id")


class TestTimestampValidation:
    def test_past_timestamp_passes(self):
        ts = datetime(2026, 7, 7, 10, 0, tzinfo=timezone.utc)
        assert validate_timestamp_not_future(ts) == ts

    def test_future_timestamp_rejected(self):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        with pytest.raises(BackendValidationError):
            validate_timestamp_not_future(future)

    def test_valid_range(self):
        start = datetime(2026, 7, 1, tzinfo=timezone.utc)
        end = datetime(2026, 7, 7, tzinfo=timezone.utc)
        assert validate_timestamp_range(start, end) == (start, end)

    def test_invalid_range(self):
        start = datetime(2026, 7, 7, tzinfo=timezone.utc)
        end = datetime(2026, 7, 1, tzinfo=timezone.utc)
        with pytest.raises(BackendValidationError):
            validate_timestamp_range(start, end)


class TestSignalValidation:
    def test_enough_signals(self):
        signals = [1, 2, 3]
        assert validate_minimum_signals(signals) == signals

    def test_too_few_signals_rejected(self):
        with pytest.raises(BackendValidationError) as exc_info:
            validate_minimum_signals([1, 2])
        assert exc_info.value.status_code == 400

    def test_custom_minimum(self):
        with pytest.raises(BackendValidationError):
            validate_minimum_signals([1, 2, 3], min_count=4)


class TestValidationErrorConversion:
    def test_to_http_exception(self):
        err = BackendValidationError("field", "message", status_code=422)
        http_exc = err.to_http_exception()
        assert http_exc.status_code == 422
        assert http_exc.detail["field"] == "field"
        assert http_exc.detail["message"] == "message"


# =====================================================================
# CROSS-CUTTING: Verify all files exist
# =====================================================================


class TestFileExistence:
    """Verify all Day 3 deliverable files exist."""

    def test_validators_py_exists(self):
        path = ROOT / "scientific" / "validation" / "validators.py"
        assert path.exists(), f"Missing: {path}"
        # validators.py is now a facade that re-exports from modular sub-modules
        content = path.read_text()
        assert "MeasurementValidator" in content, "Facade missing MeasurementValidator"
        assert "TowerValidator" in content, "Facade missing TowerValidator"
        assert "ScenarioValidator" in content, "Facade missing ScenarioValidator"
        # Verify the modular sub-modules exist
        validation_dir = ROOT / "scientific" / "validation"
        for module in [
            "types.py",
            "measurement_validator.py",
            "tower_validator.py",
            "scenario_validator.py",
            "cdr_validator.py",
            "result_validator.py",
        ]:
            mod_path = validation_dir / module
            assert mod_path.exists(), f"Missing validator module: {mod_path}"

    def test_validation_init_exports(self):
        path = ROOT / "scientific" / "validation" / "__init__.py"
        assert path.exists()
        content = path.read_text()
        assert "MeasurementValidator" in content
        assert "TowerValidator" in content
        assert "ScenarioValidator" in content

    def test_sample_dataset_exists(self):
        path = ROOT / "datasets" / "sample" / "sample_dataset.json"
        assert path.exists(), f"Missing: {path}"
        assert path.stat().st_size > 3000, "Dataset seems too small"

    def test_shared_validation_exists(self):
        path = ROOT / "backend" / "app" / "shared" / "validation.py"
        assert path.exists(), f"Missing: {path}"
        assert path.stat().st_size > 3000, "validation.py seems too small"

    def test_shared_init_exists(self):
        path = ROOT / "backend" / "app" / "shared" / "__init__.py"
        assert path.exists(), f"Missing: {path}"
