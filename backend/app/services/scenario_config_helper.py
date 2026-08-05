import json
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.measurement import Measurement
from app.models.tower import Tower
from app.models.cdr_record import CDRRecord
from app.repositories.measurement_repository import MeasurementRepository
from scientific.models.scenario_config import (
    ScenarioConfig,
    TowerPlacement,
    PropagationDefaults,
    SimulationParameters,
)


def load_scenario_config(
    db: Session, scenario_id: int, case_id: int | None = None
) -> ScenarioConfig:
    """Load scenario config from dataset JSON if present, or dynamically build one from DB data."""
    dataset_path = (
        Path(__file__).resolve().parents[2]
        / "datasets"
        / "sample"
        / "scenario_example.json"
    )
    if dataset_path.exists():
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            configs_list = data.get("scenario_configs", [])
            for cfg_dict in configs_list:
                sc_id_str = cfg_dict.get("scenario_id", "")
                try:
                    cfg_id_int = int(sc_id_str.split("-")[-1])
                except (ValueError, IndexError):
                    continue
                if cfg_id_int == scenario_id:
                    return ScenarioConfig(**cfg_dict)
        except Exception:
            pass

    # If not found in JSON dataset, build a dynamic ScenarioConfig from DB measurements & towers
    db_measurements = []
    if case_id:
        db_measurements = MeasurementRepository.get_by_case(db, case_id)
    if not db_measurements and scenario_id:
        db_measurements = (
            db.query(Measurement).filter(Measurement.scenario_id == scenario_id).all()
        )

    lats = [m.latitude for m in db_measurements if m.latitude is not None]
    lons = [m.longitude for m in db_measurements if m.longitude is not None]

    if not lats and case_id:
        cdrs = db.query(CDRRecord).filter(CDRRecord.case_id == case_id).all()
        lats = [c.latitude for c in cdrs if c.latitude is not None]
        lons = [c.longitude for c in cdrs if c.longitude is not None]

    center_lat = sum(lats) / len(lats) if lats else 12.9716
    center_lon = sum(lons) / len(lons) if lons else 77.5946

    # Gather unique towers from DB
    placements: list[TowerPlacement] = []
    registered_towers = db.query(Tower).all()
    for t in registered_towers:
        if t.latitude is not None and t.longitude is not None:
            placements.append(
                TowerPlacement(
                    tower_id=t.cgi or f"T{t.id:03d}",
                    latitude=t.latitude,
                    longitude=t.longitude,
                    antenna_height_m=getattr(t, "antenna_height_m", None) or 30.0,
                    frequency_mhz=getattr(t, "frequency_mhz", None) or 1800.0,
                    transmit_power_dbm=getattr(t, "transmit_power_dbm", None) or 43.0,
                    coverage_radius_m=getattr(t, "coverage_radius_m", None) or 1000.0,
                    sector=getattr(t, "sector_identifier", None) or "A",
                )
            )

    # Ensure at least 3 distinct towers for multilateration
    if len(placements) < 3:
        offsets = [
            (0.0, 0.0, "T001"),
            (0.005, -0.005, "T002"),
            (-0.005, 0.005, "T003"),
        ]
        placements = []
        for dlat, dlon, tid in offsets:
            placements.append(
                TowerPlacement(
                    tower_id=tid,
                    latitude=center_lat + dlat,
                    longitude=center_lon + dlon,
                    antenna_height_m=35.0,
                    frequency_mhz=1800.0,
                    transmit_power_dbm=43.0,
                    coverage_radius_m=1200.0,
                    sector="A",
                )
            )

    return ScenarioConfig(
        scenario_id=f"SCN-{scenario_id:03d}",
        name=f"Scenario #{scenario_id}",
        description=f"Auto-generated scenario for scenario ID {scenario_id}",
        tower_placements=placements,
        environment_type="urban",
        noise_level_dbm=-95.0,
        propagation=PropagationDefaults.for_environment("urban"),
        simulation=SimulationParameters(),
        expected_device_lat=center_lat,
        expected_device_lon=center_lon,
    )
