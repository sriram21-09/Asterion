"""
Comprehensive Day 4 Verification Tests
========================================

Tests every deliverable from Day 4 (Chaitanya — Scientific Engineer):
  1. scientific/models/scenario_config.py — ScenarioConfig, TowerPlacement,
     PropagationDefaults, SimulationParameters
  2. datasets/sample/scenario_example.json — consolidated scenario example
  3. Scenario repository / service test support (pairing with Sriram)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# =====================================================================
# DELIVERABLE 1: scientific/models/scenario_config.py
# =====================================================================

from scientific.models.scenario_config import (
    PROPAGATION_PRESETS,
    PropagationDefaults,
    ScenarioConfig,
    SimulationParameters,
    TowerPlacement,
)
from scientific.models.scenario import Scenario
from scientific.models.tower import Tower


# ── TowerPlacement Tests ─────────────────────────────────────────────


class TestTowerPlacement:
    """Validate TowerPlacement creation and constraints."""

    def test_create_valid_placement(self):
        tp = TowerPlacement(
            tower_id="T001",
            latitude=12.9716,
            longitude=77.5946,
        )
        assert tp.tower_id == "T001"
        assert tp.latitude == 12.9716
        assert tp.longitude == 77.5946
        # defaults
        assert tp.antenna_height_m == 30.0
        assert tp.frequency_mhz == 1800.0
        assert tp.transmit_power_dbm == 43.0
        assert tp.coverage_radius_m == 1000.0
        assert tp.sector is None

    def test_create_full_placement(self):
        tp = TowerPlacement(
            tower_id="T002",
            latitude=-33.8688,
            longitude=151.2093,
            antenna_height_m=50.0,
            frequency_mhz=2600.0,
            transmit_power_dbm=46.0,
            coverage_radius_m=800.0,
            sector="B",
        )
        assert tp.frequency_mhz == 2600.0
        assert tp.sector == "B"
        assert tp.coverage_radius_m == 800.0

    def test_empty_tower_id_rejected(self):
        with pytest.raises(Exception):
            TowerPlacement(tower_id="", latitude=0.0, longitude=0.0)

    def test_latitude_out_of_range_rejected(self):
        with pytest.raises(Exception):
            TowerPlacement(tower_id="T001", latitude=91.0, longitude=0.0)

    def test_longitude_out_of_range_rejected(self):
        with pytest.raises(Exception):
            TowerPlacement(tower_id="T001", latitude=0.0, longitude=181.0)

    def test_negative_antenna_height_rejected(self):
        with pytest.raises(Exception):
            TowerPlacement(
                tower_id="T001", latitude=0.0, longitude=0.0,
                antenna_height_m=-5.0,
            )

    def test_serialization_roundtrip(self):
        tp = TowerPlacement(
            tower_id="T001", latitude=12.97, longitude=77.59,
            sector="C",
        )
        data = tp.model_dump()
        restored = TowerPlacement(**data)
        assert restored == tp


# ── PropagationDefaults Tests ────────────────────────────────────────


class TestPropagationDefaults:
    """Validate PropagationDefaults presets and creation."""

    def test_default_values(self):
        pd = PropagationDefaults()
        assert pd.path_loss_exponent == 3.5
        assert pd.shadow_fading_std_db == 8.0
        assert pd.reference_distance_m == 1.0
        assert pd.reference_loss_db == 38.0

    def test_urban_preset(self):
        pd = PropagationDefaults.for_environment("urban")
        assert pd.path_loss_exponent == 3.5
        assert pd.shadow_fading_std_db == 8.0

    def test_suburban_preset(self):
        pd = PropagationDefaults.for_environment("suburban")
        assert pd.path_loss_exponent == 3.0
        assert pd.shadow_fading_std_db == 6.0

    def test_rural_preset(self):
        pd = PropagationDefaults.for_environment("rural")
        assert pd.path_loss_exponent == 2.5
        assert pd.shadow_fading_std_db == 4.0

    def test_highway_preset(self):
        pd = PropagationDefaults.for_environment("highway")
        assert pd.path_loss_exponent == 2.8
        assert pd.shadow_fading_std_db == 5.0

    def test_all_environments_have_presets(self):
        for env in ["urban", "suburban", "rural", "highway"]:
            assert env in PROPAGATION_PRESETS
            pd = PropagationDefaults.for_environment(env)
            assert pd.path_loss_exponent > 0
            assert pd.shadow_fading_std_db >= 0
            assert pd.reference_distance_m > 0

    def test_unknown_environment_falls_back_to_urban(self):
        pd = PropagationDefaults.for_environment("unknown_env")
        urban = PropagationDefaults.for_environment("urban")
        assert pd == urban


# ── SimulationParameters Tests ───────────────────────────────────────


class TestSimulationParameters:
    """Validate SimulationParameters creation and constraints."""

    def test_default_values(self):
        sp = SimulationParameters()
        assert sp.algorithm == "multilateration"
        assert sp.max_iterations == 100
        assert sp.convergence_threshold_m == 1.0
        assert sp.measurement_count == 1
        assert sp.enable_noise is True
        assert sp.random_seed is None

    def test_custom_values(self):
        sp = SimulationParameters(
            algorithm="kalman",
            max_iterations=500,
            convergence_threshold_m=0.5,
            measurement_count=10,
            enable_noise=False,
            random_seed=42,
        )
        assert sp.algorithm == "kalman"
        assert sp.max_iterations == 500
        assert sp.random_seed == 42

    def test_invalid_algorithm_rejected(self):
        with pytest.raises(Exception):
            SimulationParameters(algorithm="invalid_algo")

    def test_zero_iterations_rejected(self):
        with pytest.raises(Exception):
            SimulationParameters(max_iterations=0)

    def test_negative_threshold_rejected(self):
        with pytest.raises(Exception):
            SimulationParameters(convergence_threshold_m=-1.0)

    def test_all_algorithms_accepted(self):
        for algo in ["multilateration", "kalman", "weighted_centroid", "hybrid"]:
            sp = SimulationParameters(algorithm=algo)
            assert sp.algorithm == algo


# ── ScenarioConfig Tests ────────────────────────────────────────────


class TestScenarioConfig:
    """Validate ScenarioConfig creation, validation, and factory."""

    @staticmethod
    def _make_placements(count=3):
        return [
            TowerPlacement(
                tower_id=f"T{i+1:03d}",
                latitude=12.97 + i * 0.003,
                longitude=77.59 - i * 0.005,
            )
            for i in range(count)
        ]

    def test_create_minimal_config(self):
        cfg = ScenarioConfig(
            scenario_id="SCN-001",
            name="Test Scenario",
            tower_placements=self._make_placements(3),
        )
        assert cfg.scenario_id == "SCN-001"
        assert cfg.name == "Test Scenario"
        assert len(cfg.tower_placements) == 3
        assert cfg.environment_type == "urban"
        assert cfg.noise_level_dbm == -95.0
        assert cfg.propagation is not None
        assert cfg.simulation is not None

    def test_create_full_config(self):
        cfg = ScenarioConfig(
            scenario_id="SCN-002",
            name="Full Test",
            description="A fully specified config",
            tower_placements=self._make_placements(4),
            environment_type="suburban",
            noise_level_dbm=-98.0,
            propagation=PropagationDefaults.for_environment("suburban"),
            simulation=SimulationParameters(
                algorithm="kalman",
                max_iterations=200,
                random_seed=7,
            ),
            expected_device_lat=12.972,
            expected_device_lon=77.585,
        )
        assert cfg.environment_type == "suburban"
        assert cfg.propagation.path_loss_exponent == 3.0
        assert cfg.simulation.algorithm == "kalman"
        assert cfg.expected_device_lat == 12.972

    def test_too_few_towers_rejected(self):
        with pytest.raises(Exception):
            ScenarioConfig(
                scenario_id="SCN-001",
                name="Bad",
                tower_placements=self._make_placements(2),
            )

    def test_partial_ground_truth_rejected(self):
        with pytest.raises(Exception):
            ScenarioConfig(
                scenario_id="SCN-001",
                name="Partial GT",
                tower_placements=self._make_placements(3),
                expected_device_lat=12.97,
                # missing expected_device_lon
            )

    def test_both_ground_truth_none_accepted(self):
        cfg = ScenarioConfig(
            scenario_id="SCN-001",
            name="No GT",
            tower_placements=self._make_placements(3),
        )
        assert cfg.expected_device_lat is None
        assert cfg.expected_device_lon is None

    def test_auto_propagation_for_non_urban(self):
        cfg = ScenarioConfig(
            scenario_id="SCN-001",
            name="Rural Auto",
            tower_placements=self._make_placements(3),
            environment_type="rural",
        )
        # Should auto-set rural propagation defaults
        assert cfg.propagation.path_loss_exponent == 2.5

    def test_explicit_propagation_preserved(self):
        custom = PropagationDefaults(
            path_loss_exponent=4.0,
            shadow_fading_std_db=10.0,
        )
        cfg = ScenarioConfig(
            scenario_id="SCN-001",
            name="Custom Prop",
            tower_placements=self._make_placements(3),
            environment_type="rural",
            propagation=custom,
        )
        # Custom propagation should be preserved (not overridden)
        assert cfg.propagation.path_loss_exponent == 4.0

    def test_from_scenario_factory(self):
        towers = [
            Tower(tower_id="T001", latitude=12.9716, longitude=77.5946,
                  antenna_height_m=35.0, frequency_mhz=1800.0,
                  transmit_power_dbm=43.0, coverage_radius_m=1200.0,
                  sector="A"),
            Tower(tower_id="T002", latitude=12.9750, longitude=77.5900,
                  antenna_height_m=40.0, frequency_mhz=2100.0),
            Tower(tower_id="T003", latitude=12.9700, longitude=77.6000),
        ]
        scenario = Scenario(
            scenario_id="SCN-001",
            name="Factory Test",
            description="Testing from_scenario",
            towers=towers,
            environment_type="suburban",
            noise_level_dbm=-98.0,
            expected_device_lat=12.972,
            expected_device_lon=77.595,
        )

        cfg = ScenarioConfig.from_scenario(scenario)

        assert cfg.scenario_id == "SCN-001"
        assert cfg.name == "Factory Test"
        assert cfg.description == "Testing from_scenario"
        assert len(cfg.tower_placements) == 3
        assert cfg.tower_placements[0].tower_id == "T001"
        assert cfg.tower_placements[0].antenna_height_m == 35.0
        assert cfg.tower_placements[0].sector == "A"
        assert cfg.environment_type == "suburban"
        assert cfg.propagation.path_loss_exponent == 3.0  # suburban preset
        assert cfg.noise_level_dbm == -98.0
        assert cfg.expected_device_lat == 12.972

    def test_json_serialization_roundtrip(self):
        cfg = ScenarioConfig(
            scenario_id="SCN-001",
            name="Roundtrip",
            tower_placements=self._make_placements(3),
            simulation=SimulationParameters(random_seed=42),
            expected_device_lat=12.97,
            expected_device_lon=77.59,
        )
        json_str = cfg.model_dump_json()
        restored = ScenarioConfig.model_validate_json(json_str)
        assert restored.scenario_id == cfg.scenario_id
        assert len(restored.tower_placements) == 3
        assert restored.simulation.random_seed == 42

    def test_model_config_has_examples(self):
        schema = ScenarioConfig.model_json_schema()
        assert "examples" in schema


# =====================================================================
# DELIVERABLE 2: datasets/sample/scenario_example.json
# =====================================================================


class TestScenarioExampleDataset:
    """Validate the scenario_example.json file structure and data integrity."""

    @pytest.fixture(autouse=True)
    def load_dataset(self):
        path = ROOT / "datasets" / "sample" / "scenario_example.json"
        assert path.exists(), f"scenario_example.json not found at {path}"
        with open(path) as f:
            self.data = json.load(f)

    def test_has_metadata(self):
        meta = self.data["metadata"]
        assert "file_id" in meta
        assert meta["coordinate_system"] == "WGS84"
        assert "units" in meta

    def test_has_tower_registry(self):
        registry = self.data["tower_registry"]
        towers = registry["towers"]
        assert len(towers) >= 3
        tower_ids = {t["tower_id"] for t in towers}
        assert "T001" in tower_ids

    def test_tower_registry_entries_valid(self):
        for t in self.data["tower_registry"]["towers"]:
            tower = Tower(**t)
            assert tower.tower_id
            assert -90.0 <= tower.latitude <= 90.0
            assert -180.0 <= tower.longitude <= 180.0

    def test_tower_registry_ids_unique(self):
        ids = [t["tower_id"] for t in self.data["tower_registry"]["towers"]]
        assert len(ids) == len(set(ids)), "Duplicate tower IDs in registry"

    def test_has_tower_schema_documentation(self):
        doc = self.data["tower_schema_documentation"]
        fields = doc["fields"]
        # All Tower model fields should be documented
        for field_name in [
            "tower_id", "latitude", "longitude", "antenna_height_m",
            "frequency_mhz", "transmit_power_dbm", "sector", "coverage_radius_m",
        ]:
            assert field_name in fields, f"Missing documentation for {field_name}"
            field_doc = fields[field_name]
            assert "type" in field_doc
            assert "description" in field_doc

    def test_schema_documentation_has_relationships(self):
        doc = self.data["tower_schema_documentation"]
        assert "relationships" in doc
        rels = doc["relationships"]
        assert "scenario" in rels
        assert "measurement" in rels
        assert "scenario_config" in rels

    def test_schema_documentation_has_validation_rules(self):
        doc = self.data["tower_schema_documentation"]
        assert "validation_rules" in doc
        assert len(doc["validation_rules"]) >= 3

    def test_has_scenario_configs(self):
        configs = self.data["scenario_configs"]
        assert len(configs) == 3

    def test_scenario_config_ids_unique(self):
        ids = [c["scenario_id"] for c in self.data["scenario_configs"]]
        assert len(ids) == len(set(ids)), "Duplicate scenario config IDs"

    def test_scenario_configs_load_as_pydantic(self):
        """Each scenario config must be loadable as a ScenarioConfig model."""
        for sc in self.data["scenario_configs"]:
            cfg = ScenarioConfig(**sc)
            assert cfg.scenario_id
            assert len(cfg.tower_placements) >= 3
            assert cfg.environment_type in ["urban", "suburban", "rural", "highway"]

    def test_scenario_configs_have_expected_results(self):
        for sc in self.data["scenario_configs"]:
            assert "expected_results" in sc
            er = sc["expected_results"]
            assert "max_error_m" in er
            assert "min_confidence_score" in er

    def test_scenario_configs_cover_multiple_environments(self):
        envs = {sc["environment_type"] for sc in self.data["scenario_configs"]}
        assert len(envs) >= 2, "Should cover at least 2 different environments"
        assert "urban" in envs

    def test_tower_placements_reference_valid_coords(self):
        """All tower placements in configs must have valid coordinates."""
        for sc in self.data["scenario_configs"]:
            for tp in sc["tower_placements"]:
                assert -90.0 <= tp["latitude"] <= 90.0
                assert -180.0 <= tp["longitude"] <= 180.0

    def test_propagation_params_physically_valid(self):
        """Propagation parameters must be physically plausible."""
        for sc in self.data["scenario_configs"]:
            prop = sc["propagation"]
            assert 1.0 <= prop["path_loss_exponent"] <= 6.0
            assert 0.0 <= prop["shadow_fading_std_db"] <= 20.0
            assert prop["reference_distance_m"] > 0


# =====================================================================
# DELIVERABLE 3: Scenario Repository / Service Test Support
# (Pairing with Sriram — ORM-based scenario tests)
# =====================================================================

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# Inline ORM (mirrors Sriram's expected backend models)
class _Base(DeclarativeBase):
    pass


class ScenarioORM(_Base):
    """ORM model for localization scenarios (mirrors backend/app/models/)."""

    __tablename__ = "scenarios_day4"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


@pytest.fixture(scope="function")
def scenario_db():
    """Fresh in-memory SQLite database with Scenario table."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    _Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        _Base.metadata.drop_all(engine)
        engine.dispose()


class TestScenarioRepository:
    """Scenario repository tests — pairing with Sriram."""

    def test_create_scenario(self, scenario_db: Session):
        """Create a scenario and verify persistence."""
        scenario = ScenarioORM(
            name="Urban 3-Tower Test",
            description="Multilateration test with 3 towers in Bangalore.",
        )
        scenario_db.add(scenario)
        scenario_db.commit()
        scenario_db.refresh(scenario)

        assert scenario.id is not None
        assert scenario.id > 0
        assert scenario.name == "Urban 3-Tower Test"
        assert scenario.created_at is not None

    def test_list_scenarios(self, scenario_db: Session):
        """Create multiple scenarios and verify list retrieval."""
        for i in range(5):
            scenario_db.add(ScenarioORM(
                name=f"Scenario {i+1}",
                description=f"Test scenario number {i+1}",
            ))
        scenario_db.commit()

        results = scenario_db.query(ScenarioORM).all()
        assert len(results) == 5
        names = {s.name for s in results}
        assert "Scenario 1" in names
        assert "Scenario 5" in names

    def test_get_scenario_by_id(self, scenario_db: Session):
        """Retrieve a scenario by primary key."""
        scenario = ScenarioORM(name="Lookup Test")
        scenario_db.add(scenario)
        scenario_db.commit()
        scenario_db.refresh(scenario)
        pk = scenario.id

        found = scenario_db.get(ScenarioORM, pk)
        assert found is not None
        assert found.name == "Lookup Test"

    def test_get_nonexistent_scenario_returns_none(self, scenario_db: Session):
        """Looking up a missing ID should return None, not raise."""
        result = scenario_db.get(ScenarioORM, 9999)
        assert result is None

    def test_delete_scenario(self, scenario_db: Session):
        """Create, delete, and verify removal."""
        scenario = ScenarioORM(name="Delete Me")
        scenario_db.add(scenario)
        scenario_db.commit()
        pk = scenario.id

        scenario_db.delete(scenario)
        scenario_db.commit()

        assert scenario_db.get(ScenarioORM, pk) is None

    def test_create_scenario_missing_name_fails(self, scenario_db: Session):
        """Attempt to create without required name — expect IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        scenario = ScenarioORM(name=None)
        scenario_db.add(scenario)
        with pytest.raises(IntegrityError):
            scenario_db.commit()
        scenario_db.rollback()


class TestScenarioService:
    """Scenario service-layer tests — validates business rules."""

    def test_scenario_config_from_json_is_valid(self):
        """Loading a JSON config from the example file produces valid models."""
        path = ROOT / "datasets" / "sample" / "scenario_example.json"
        with open(path) as f:
            data = json.load(f)

        for sc in data["scenario_configs"]:
            cfg = ScenarioConfig(**sc)
            assert cfg.scenario_id
            assert len(cfg.tower_placements) >= 3
            assert cfg.propagation.path_loss_exponent > 0

    def test_scenario_to_config_roundtrip(self):
        """Scenario → ScenarioConfig → JSON → ScenarioConfig roundtrip."""
        towers = [
            Tower(tower_id=f"T{i+1:03d}",
                  latitude=12.97 + i * 0.003,
                  longitude=77.59 - i * 0.005)
            for i in range(3)
        ]
        scenario = Scenario(
            scenario_id="SCN-RT-001",
            name="Roundtrip Test",
            towers=towers,
            environment_type="urban",
            expected_device_lat=12.972,
            expected_device_lon=77.585,
        )

        cfg = ScenarioConfig.from_scenario(scenario)
        json_str = cfg.model_dump_json()
        restored = ScenarioConfig.model_validate_json(json_str)

        assert restored.scenario_id == scenario.scenario_id
        assert restored.name == scenario.name
        assert len(restored.tower_placements) == 3
        assert restored.expected_device_lat == 12.972

    def test_config_environment_affects_propagation(self):
        """Different environment types should produce different propagation."""
        placements = [
            TowerPlacement(tower_id=f"T{i+1:03d}",
                           latitude=12.97 + i * 0.003,
                           longitude=77.59 - i * 0.005)
            for i in range(3)
        ]
        urban = ScenarioConfig(
            scenario_id="U", name="Urban",
            tower_placements=placements, environment_type="urban",
        )
        rural = ScenarioConfig(
            scenario_id="R", name="Rural",
            tower_placements=placements, environment_type="rural",
        )

        assert urban.propagation.path_loss_exponent > rural.propagation.path_loss_exponent
        assert urban.propagation.shadow_fading_std_db > rural.propagation.shadow_fading_std_db


# =====================================================================
# CROSS-CUTTING: File existence and size checks
# =====================================================================


class TestDay4FileExistence:
    """Verify all Day 4 deliverable files exist and have reasonable size."""

    def test_scenario_config_py_exists(self):
        path = ROOT / "scientific" / "models" / "scenario_config.py"
        assert path.exists(), f"Missing: {path}"
        assert path.stat().st_size > 3000, "scenario_config.py seems too small"

    def test_scenario_example_json_exists(self):
        path = ROOT / "datasets" / "sample" / "scenario_example.json"
        assert path.exists(), f"Missing: {path}"
        assert path.stat().st_size > 3000, "scenario_example.json seems too small"

    def test_models_init_exports_new_types(self):
        path = ROOT / "scientific" / "models" / "__init__.py"
        content = path.read_text()
        assert "ScenarioConfig" in content
        assert "TowerPlacement" in content
        assert "PropagationDefaults" in content
        assert "SimulationParameters" in content

    def test_existing_deliverables_intact(self):
        """Ensure Day 2/3 files were not broken by Day 4 changes."""
        for rel_path in [
            "scientific/models/tower.py",
            "scientific/models/measurement.py",
            "scientific/models/scenario.py",
            "scientific/models/result.py",
            "scientific/validation/validators.py",
            "datasets/sample/sample_dataset.json",
        ]:
            path = ROOT / rel_path
            assert path.exists(), f"Pre-existing deliverable missing: {path}"
            assert path.stat().st_size > 0
