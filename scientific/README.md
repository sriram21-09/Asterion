# 🔬 Asterion Scientific Engine

Welcome to the **Asterion Scientific Engine** package. This is a standalone, decoupled Python package dedicated to telecom localization, signal simulation, multilateration solving, Kalman state tracking, and confidence estimation.

## Design Philosophy

1. **Decoupled from FastAPI**: The engine operates purely on standard Python data structures, Pydantic schemas, and scientific libraries (`numpy`, `scipy`). It has no direct dependency on the database or the web framework and can be imported in notebooks, research scripts, or batch simulation pipelines.
2. **Immutable Configuration**: All configuration parameters are defined as frozen dataclasses to avoid side-effects and concurrency issues during execution sweeps.
3. **Rigorous Validation**: Built-in physical and logical validators enforce real-world constraints (e.g., coordinate bounds, signal thresholds, time-of-arrival checks) before processing computations.

---

## Package Structure

```text
scientific/
├── __init__.py              # Package entrypoint (specifies version 0.2.0)
├── config.py                # Frozen SimulationConfig, ValidationThresholds, EnvironmentConfig
├── constants.py             # Haversine distance, dB/linear conversions, WGS84, Cellular Bands
├── logger.py                # Standardized console logging helper
├── models/
│   ├── __init__.py          # Combined model exports
│   ├── tower.py             # Tower data model (coordinate, RF properties)
│   ├── measurement.py       # RSSI measurement reading model
│   ├── scenario.py          # Scenario model combining towers and measurements
│   ├── scenario_config.py   # Simulation parameter config
│   └── result.py            # Localization and confidence calculation outputs
├── validation/
│   ├── __init__.py          # Combined validator exports
│   └── validators.py        # Measurement, Tower, Scenario, and Result validators
├── simulation/
│   ├── rssi_generator.py    # RSSI signal strength generator using path-loss models
│   ├── noise_model.py       # Gaussian noise fading models
│   └── generator.py         # Synthetic measurement generator
└── pipeline/
    ├── multilateration.py   # NLLS multilateration localization solver
    ├── weighted_centroid.py # Fallback weighted centroid localization solver
    ├── kalman_tracker.py    # Kalman tracking filter for device tracks
    ├── confidence.py        # GDOP and error covariance ellipse estimator
    └── runner.py            # Central coordinator for E2E processing
```

---

## Submodule Overview

### 1. Configuration (`scientific/config.py`)
Centralizes all threshold limits, solver constants, and environment propagation parameters.
- **`SimulationConfig`**: Handles iteration limits, convergence thresholds, noise enablement, and default solver selection.
- **`ValidationThresholds`**: Houses physical boundaries like RSSI range `[-150, 0]`, valid coordinates, cellular frequency band offsets, and GDOP classification brackets.
- **`EnvironmentConfig`**: Holds path-loss exponents and standard deviations for fading in `urban`, `suburban`, `rural`, and `highway` environments.

### 2. Physical & RF Constants (`scientific/constants.py`)
Contains physical and telecom constants, including:
- Geodesy values (WGS84 ellipsoidal axes, flattening ratio, Earth radius).
- **`haversine_distance_m(lat1, lon1, lat2, lon2)`**: Calculates distance over Earth's sphere.
- **`db_to_linear(db)` / `linear_to_db(val)`**: RF conversions.
- Cellular Band frequency tables (LTE, GSM, WCDMA, 5G NR).

### 3. Logger (`scientific/logger.py`)
Idempotent logging wrapper utilizing standard library `logging`. Ensures messages are consistently formatted across console environments.

### 4. Data Models (`scientific/models/`)
Utilizes Pydantic (v2) for strict type safety and baseline schema validation:
- `Tower`: Represents a cell tower layout (ID, location, transmit power, antenna height, sector).
- `Measurement`: A single device measurement (RSSI, timestamp, sector, cell ID, timing advance).
- `Scenario`: Collection of towers and associated measurements.

### 5. Domain Validators (`scientific/validation/validators.py`)
Implements physical and logical integrity validation:
- **`MeasurementValidator`**: Cross-validates Timing Advance (TA) and RSSI values to catch anomalies.
- **`TowerValidator`**: Checks RF parameters against cellular bands.
- **`ScenarioValidator`**: Enforces referential integrity (measurements must refer to existing towers).

---

## Standalone Usage Example

```python
from scientific.models.tower import Tower
from scientific.models.measurement import Measurement
from scientific.models.scenario import Scenario
from scientific.validation.validators import ScenarioValidator

# 1. Define Tower layout
tower = Tower(
    tower_id="T001",
    latitude=12.9716,
    longitude=77.5946,
    transmit_power_dbm=43.0,
    antenna_height_m=30.0,
    coverage_radius_m=1000.0,
    frequency_mhz=1800.0,
)

# 2. Define Measurement
measurement = Measurement(
    tower_id="T001",
    timestamp="2026-07-12T10:18:53Z",
    rssi=-75.0,
    timing_advance=2,
)

# 3. Create Scenario
scenario = Scenario(
    scenario_id="S001",
    name="Bangalore Core Test",
    towers=[tower],
    measurements=[measurement],
)

# 4. Run Domain Validation
validator = ScenarioValidator()
result = validator.validate(scenario)
print(f"Validation successful: {result.is_valid}")
```

---

## Formatting & Code Quality Checks

To keep the scientific package stabilized and compliant with styling guides, run these tools from the workspace root:

```bash
# Activate virtual environment
.\backend\.venv\Scripts\activate

# Run Ruff linting check and auto-fix simple issues
ruff check scientific --fix

# Run Black formatting check & reformat files
black scientific

# Run the test suite
pytest
```

---

## 🚀 Completed Scientific Engine Features (v0.2.0)

The core scientific and mathematical components are fully implemented and integrated:

1. **RSSI Signal Generator** (`scientific/simulation/rssi_generator.py`): Simulates log-distance path loss.
2. **Noise Injection Model** (`scientific/simulation/noise_model.py`): Models shadow fading using standard normal distributions.
3. **Measurement Synthesizer** (`scientific/simulation/generator.py`): Produces synthetic measurements from scenarios.
4. **Non-Linear Least Squares Solver (NLLS)** (`scientific/pipeline/multilateration.py`): Performs trilateration.
5. **Weighted Centroid Fallback** (`scientific/pipeline/weighted_centroid.py`): Centroid estimation based on RSSI weights.
6. **Kalman Position Tracker** (`scientific/pipeline/kalman_tracker.py`): Performs 2D constant-velocity smoothing.
7. **GDOP & Covariance confidence estimator** (`scientific/pipeline/confidence.py`): Evaluates geometric errors.
8. **End-to-End Pipeline Orchestrator** (`scientific/pipeline/runner.py`): Orchestrates simulation, validation, localization, tracking, and confidence.
