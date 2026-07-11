# Asterion Documentation

Welcome to the documentation folder for Asterion, the Explainable Telecom Localization & Investigation Support Platform.

## Contents

- [architecture.md](architecture.md): Overview of system design, backend engines, and React integration.
- [localization.md](localization.md): Mathematical explanation of multilateration, Kalman filter tracking, and confidence estimation.
- [api.md](api.md): REST API endpoints documentation.

---

## Scientific Engine — Week 1 Foundation Summary

The `scientific/` package provides a standalone, import-ready computation engine for telecom localization. It is fully decoupled from the FastAPI backend and can be used independently for research, simulation, and validation.

### Package Structure

```text
scientific/
├── __init__.py              # Package root (v0.1.0), submodule docstrings
├── config.py                # SimulationConfig, ValidationThresholds, EnvironmentConfig
├── constants.py             # Physical, RF, geodesy, cellular-band, RSSI constants
├── logger.py                # Console logging helper (get_logger, set_level, silence)
├── models/
│   ├── __init__.py          # Aggregated exports for all data models
│   ├── tower.py             # Tower schema (cell tower configuration)
│   ├── measurement.py       # Measurement schema (RSSI signal reading)
│   ├── scenario.py          # Scenario schema (localization scenario)
│   ├── scenario_config.py   # ScenarioConfig (simulation-ready input)
│   └── result.py            # LocalizationResult + ConfidenceResult (outputs)
├── validation/
│   ├── __init__.py          # Aggregated exports for validators
│   └── validators.py        # MeasurementValidator, TowerValidator, ScenarioValidator
├── simulation/
│   └── __init__.py          # Placeholder (Week 2: RSSI generation, noise models)
└── pipeline/
    └── __init__.py          # Placeholder (Week 2: end-to-end pipeline runner)
```

### Data Models

| Model | Module | Purpose |
|---|---|---|
| `Tower` | `models/tower.py` | Cell tower with coordinates, RF parameters, sector |
| `Measurement` | `models/measurement.py` | Single RSSI reading with timestamp, tower reference |
| `Scenario` | `models/scenario.py` | Localization scenario bundling towers + measurements |
| `ScenarioConfig` | `models/scenario_config.py` | Simulation-ready config with solver & propagation settings |
| `LocalizationResult` | `models/result.py` | Estimated device position from localization algorithm |
| `ConfidenceResult` | `models/result.py` | Statistical confidence (GDOP, error ellipse, score) |

### Configuration & Constants

- **`config.py`** — Frozen dataclasses: `SimulationConfig` (solver bounds), `ValidationThresholds` (domain ranges), `EnvironmentConfig` (propagation presets for urban/suburban/rural/highway).
- **`constants.py`** — Physical constants (speed of light, Boltzmann), unit conversions (dB↔linear, dBm↔Watts), Haversine distance, cellular frequency bands, RSSI quality tiers, timing advance resolution.
- **`logger.py`** — `get_logger(__name__)` returns a pre-configured console logger. Idempotent, no global side-effects. Level controllable via `ASTERION_LOG_LEVEL` env var.

### Validation Engine

Three concrete validators with domain-specific checks beyond Pydantic field validation:

- **`MeasurementValidator`** — Lat/lon pairing, RSSI plausibility, TA↔RSSI consistency, timestamp sanity.
- **`TowerValidator`** — Frequency band check, transmit power range, antenna height, coverage radius.
- **`ScenarioValidator`** — Tower ID uniqueness, measurement→tower referential integrity, ground-truth pairing, deep validation.

### Datasets

```text
datasets/
├── .gitkeep
└── sample/
    ├── sample_dataset.json      # 4 towers, 2 scenarios, 14 measurements (Bangalore)
    └── scenario_example.json    # 3 scenario configs (urban/suburban/rural)
```

### Test Coverage

| Test File | Tests | Scope |
|---|---|---|
| `tests/test_day3_deliverables.py` | 88 | Models, Scenario, Measurement, Validators |
| `tests/test_day4_deliverables.py` | 68 | ScenarioConfig, TowerPlacement, PropagationDefaults |
| `tests/test_day5_deliverables.py` | 72 | Config, Constants, Logger |
| `tests/test_tower_model.py` | 43 | Tower model (construction, boundaries, serialization, validation) |
| **Total** | **271** | |

---

## Week 2 — Scientific Engine Sprint

See `Plans/week2_scientific_checklist.md` for the detailed Week 2 development checklist covering:

- RSSI Signal Generator
- Noise Model
- Multilateration Solver (NLLS)
- Kalman Filter Tracker
- Confidence & GDOP Estimator
- End-to-End Pipeline Runner
