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
├── __init__.py              # Package entrypoint (specifies version 0.3.0)
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
│   └── measurement_generator.py # Synthetic measurement generator
└── pipeline/
    ├── multilateration.py   # NLLS multilateration localization solver
    ├── weighted_centroid.py # Fallback weighted centroid localization solver
    ├── kalman_tracker.py    # Kalman tracking filter for device tracks
    ├── confidence.py        # GDOP and error covariance ellipse estimator
    ├── evidence.py          # Evidence synthesis and audit tracker
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

## 📐 Mathematical Foundations

### 1. Signal Propagation & RF Noise Simulation
The engine models radio signal decay and environmental noise dynamically to simulate realistic propagation environments.

#### Log-Distance Path Loss Model
Path loss ($PL$) in decibels (dB) experienced over distance $d$ (meters) is computed using:
$$PL(d) = PL_0 + 10 \cdot n \cdot \log_{10}\left(\frac{d_{eff}}{d_0}\right)$$

Where:
- $PL_0$ is the reference path loss (`reference_loss_db`) at reference distance $d_0$ (`reference_distance_m`).
- $n$ is the path-loss exponent (`path_loss_exponent`) capturing signal decay rate.
- $d_{eff} = \max(d, d_0)$ clamps the distance to prevent negative path loss at ranges closer than the reference distance.

The noise-free, ideal Received Signal Strength Indicator ($RSSI_{ideal}$) is computed as:
$$RSSI_{ideal} [dBm] = P_{tx} - PL(d)$$
Where $P_{tx}$ is the transmit power in dBm (`transmit_power_dbm`).

#### Shadow Fading
To model obstructions like foliage and buildings, log-normal shadow fading is injected:
$$RSSI_{faded} = RSSI_{ideal} + X_{\sigma}$$
Where $X_{\sigma} \sim \mathcal{N}(0, \sigma^2_{shadow})$ is a zero-mean Gaussian variable, with $\sigma_{shadow}$ representing the standard deviation of shadow fading in dB (`shadow_fading_std_db`).

#### Thermal Noise Addition
Faded signals are combined linearly with background thermal noise in Watts to capture realistic reception behavior:
$$P_{sig} [W] = 10^{\frac{RSSI_{faded}}{10}} \cdot 10^{-3}$$
$$P_{noise} [W] = 10^{\frac{N_{floor}}{10}} \cdot 10^{-3}$$
$$P_{total} [W] = P_{sig} + P_{noise}$$
$$RSSI_{final} [dBm] = 10 \cdot \log_{10}\left(\frac{P_{total}}{10^{-3}}\right)$$
Where $N_{floor}$ is the typical background noise floor in dBm (`typical_noise_floor_dbm`). Finally, values are clamped between absolute hardware boundaries: $RSSI \in [-150.0, 0.0]$ dBm.

---

### 2. Localization Solvers

#### Weighted Centroid (Initial Guess & Fallback)
Weights each tower's coordinates by the linear power of its average signal strength:
$$w_i = 10^{\frac{\overline{RSSI}_i}{10.0}}$$
$$\hat{\phi}_{wc} = \frac{\sum_{i=1}^N w_i \cdot \phi_i}{\sum_{i=1}^N w_i}, \quad \hat{\lambda}_{wc} = \frac{\sum_{i=1}^N w_i \cdot \lambda_i}{\sum_{i=1}^N w_i}$$
Where:
- $\phi_i, \lambda_i$ are the latitude and longitude of tower $i$.
- $\overline{RSSI}_i$ is the average signal strength (dBm) for tower $i$.
- If no weights or measurements are available, the estimator defaults to a simple, unweighted geometric average:
  $$\hat{\phi}_{wc} = \frac{1}{N}\sum_{i=1}^N \phi_i, \quad \hat{\lambda}_{wc} = \frac{1}{N}\sum_{i=1}^N \lambda_i$$

#### Non-Linear Least Squares (NLLS) Multilateration
Trilateration is performed on a local flat Cartesian plane (meters) centered at the Weighted Centroid reference origin $(\phi_{ref}, \lambda_{ref})$.

Geodetic points are projected to $(x_i, y_i)$ via:
$$x_i = (\lambda_i - \lambda_{ref}) \cdot R_{lon}$$
$$y_i = (\phi_i - \phi_{ref}) \cdot R_{lat}$$
Where $R_{lat} = 111319.9$ meters/degree (lat) and $R_{lon} = R_{lat} \cdot \cos(\text{radians}(\phi_{ref}))$.

The path loss formula is inverted to yield estimated range distances $d_i$ (meters):
$$d_i = d_0 \cdot 10^{\frac{P_{tx} - \overline{RSSI}_i - PL_0}{10 \cdot n}}$$

The solver minimizes the sum of squared residuals:
$$f(x, y) = \sum_{i=1}^N \left( \sqrt{(x_i - x)^2 + (y_i - y)^2 + \epsilon} - d_i \right)^2$$
Where $\epsilon = 10^{-9}$ guarantees differentiability at zero. Optimization is carried out via the Levenberg-Marquardt algorithm. The optimized Cartesian coordinate $(x_{opt}, y_{opt})$ is transformed back to geodetic lat/lon:
$$\hat{\phi} = \phi_{ref} + \frac{y_{opt}}{R_{lat}}, \quad \hat{\lambda} = \lambda_{ref} + \frac{x_{opt}}{R_{lon}}$$

---

### 3. Sequential Kalman Tracking
A linear 2D Kalman filter processes chronological localization coordinates using a Constant-Velocity motion model.

#### State Space Model
$$\mathbf{x}_k = \begin{bmatrix} \phi_k \\ \lambda_k \\ v_{\phi, k} \\ v_{\lambda, k} \end{bmatrix}$$
Where $\phi_k, \lambda_k$ are the smoothed geodetic coordinates, and $v_{\phi}, v_{\lambda}$ are geodetic velocities in degrees per second.

#### Predict Step
$$\mathbf{x}_{k|k-1} = \mathbf{F}_k \mathbf{x}_{k-1|k-1}$$
$$\mathbf{P}_{k|k-1} = \mathbf{F}_k \mathbf{P}_{k-1|k-1} \mathbf{F}_k^T + \mathbf{Q}_k$$

Where $\mathbf{F}_k$ is the state transition matrix for time step $\Delta t$:
$$\mathbf{F}_k = \begin{bmatrix} 1 & 0 & \Delta t & 0 \\ 0 & 1 & 0 & \Delta t \\ 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}$$

Process noise covariance $\mathbf{Q}_k$ is computed from physical acceleration standard deviation $\sigma_{acc}$ (m/s$^2$), projected to degrees/s$^2$:
$$q_{acc, \phi} = \frac{\sigma_{acc}}{R_{lat}}, \quad q_{acc, \lambda} = \frac{\sigma_{acc}}{R_{lat} \cdot \cos(\text{radians}(\phi_{ref}))}$$
Letting $w_{\phi} = q_{acc, \phi}^2$ and $w_{\lambda} = q_{acc, \lambda}^2$, the discrete process covariance matrix is formulated as:
$$\mathbf{Q}_k = \begin{bmatrix} 
\frac{\Delta t^3}{3} w_{\phi} & 0 & \frac{\Delta t^2}{2} w_{\phi} & 0 \\
0 & \frac{\Delta t^3}{3} w_{\lambda} & 0 & \frac{\Delta t^2}{2} w_{\lambda} \\
\frac{\Delta t^2}{2} w_{\phi} & 0 & \Delta t \cdot w_{\phi} & 0 \\
0 & \frac{\Delta t^2}{2} w_{\lambda} & 0 & \Delta t \cdot w_{\lambda}
\end{bmatrix}$$

#### Update Step
$$\mathbf{y}_k = \mathbf{z}_k - \mathbf{H} \mathbf{x}_{k|k-1}$$
$$\mathbf{S}_k = \mathbf{H} \mathbf{P}_{k|k-1} \mathbf{H}^T + \mathbf{R}_k$$
$$\mathbf{K}_k = \mathbf{P}_{k|k-1} \mathbf{H}^T \mathbf{S}_k^{-1}$$
$$\mathbf{x}_{k|k} = \mathbf{x}_{k|k-1} + \mathbf{K}_k \mathbf{y}_k$$
$$\mathbf{P}_{k|k} = (\mathbf{I} - \mathbf{K}_k \mathbf{H})\mathbf{P}_{k|k-1}(\mathbf{I} - \mathbf{K}_k \mathbf{H})^T + \mathbf{K}_k \mathbf{R}_k \mathbf{K}_k^T$$

Where:
- $\mathbf{z}_k = [\phi_{meas}, \lambda_{meas}]^T$ is the raw measured localization coordinate.
- $\mathbf{H} = \begin{bmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \end{bmatrix}$ maps state variables to measurements.
- $\mathbf{R}_k = \text{diag}(\sigma^2_{lat}, \sigma^2_{lon})$ is the measurement noise covariance.
- The update for $\mathbf{P}_{k|k}$ is expressed in the Joseph stabilized form to guarantee positive-definiteness.

---

### 4. GDOP & Covariance Confidence Ellipse
Geometric error scaling and uncertainty bounds are computed relative to the estimated position $(\hat{x}, \hat{y})$ in meters.

#### Geometric Dilution of Precision (GDOP)
A geometry matrix $\mathbf{H}$ ($M \times 2$) maps the unit vectors pointing toward the $M$ active towers:
$$\mathbf{H} = \begin{bmatrix} \frac{\Delta x_1}{d_1} & \frac{\Delta y_1}{d_1} \\ \vdots & \vdots \\ \frac{\Delta x_M}{d_M} & \frac{\Delta y_M}{d_M} \end{bmatrix}$$
Where $\Delta x_i, \Delta y_i$ represent the Cartesian distance of tower $i$ relative to the estimated position, and $d_i = \sqrt{\Delta x_i^2 + \Delta y_i^2}$.

The dilution matrix is:
$$\mathbf{C} = (\mathbf{H}^T \mathbf{H})^{-1} = \begin{bmatrix} C_{xx} & C_{xy} \\ C_{xy} & C_{yy} \end{bmatrix}$$
The horizontal Dilution of Precision (GDOP) is computed as:
$$GDOP = \sqrt{\text{trace}(\mathbf{C})} = \sqrt{C_{xx} + C_{yy}}$$

#### Continuous Confidence Score Mapping
Continuous scores are mapped to $[0.0, 1.0]$ via an exponential decay:
$$CS = \exp\left(-0.15 \cdot (GDOP - 1.0)\right)$$

#### Error Covariance Ellipse
The position error covariance matrix $\mathbf{\Sigma}$ (meters) is scaled by range uncertainty ($\sigma$):
$$\mathbf{\Sigma} = \sigma^2 \mathbf{C} = \begin{bmatrix} a & b \\ b & c \end{bmatrix}$$

Eigenvalues $\lambda_1, \lambda_2$ represent the error variance along principal directions:
$$\lambda_{1,2} = \frac{(a + c) \pm \sqrt{(a - c)^2 + 4b^2}}{2}$$

The semi-major and semi-minor axes of the 1-sigma uncertainty ellipse are:
$$\text{semi-major} = \sqrt{\lambda_1}, \quad \text{semi-minor} = \sqrt{\lambda_2}$$

The orientation angle ($\theta$, degrees clockwise from True North) is:
$$\phi = \frac{1}{2}\text{atan2}(2b, a - c)$$
$$\theta_{north} = (90.0 - \text{degrees}(\phi)) \pmod{360.0}$$

---

## 🎛️ Solver Boundaries & Limits

| Boundary Parameter | Configuration Field | Default Value | Description |
| :--- | :--- | :--- | :--- |
| **Max Iterations** | `max_iterations` | `100` | Hard cap on the NLLS solver iteration loop. |
| **Convergence Delta** | `convergence_threshold_m` | `1.0 m` | Stopping criterion: exit loop if position shift is $< 1.0$ meter. |
| **Min Towers (NLLS)** | `min_towers_for_localization` | `3` | Minimum unique towers with measurements required to run NLLS multilateration. |
| **Min Towers (GDOP)** | *N/A* | `2` | Minimum active towers required to construct geometry matrix $H$ and calculate GDOP. |
| **Max Towers per Scenario** | `max_towers_per_scenario` | `50` | Maximum allowed towers in scenario validation. |
| **Max Measurements** | `max_measurements_per_scenario`| `5,000` | Safety limit on measurement logs to avoid out-of-memory errors. |
| **Geodetic Clamping** | `position_clamp_lat`/`_lon` | `[-90, 90]` / `[-180, 180]`| Clamps results strictly inside WGS84 geographic limits. |

---

## 🚦 Validation Thresholds

Validation rules check physical plausibility and block corrupted inputs prior to solver processing:

### 1. Signal Strength (RSSI) Bounds
- **Absolute Limits**: $RSSI \in [-150.0, 0.0]$ dBm. Anything outside is physically impossible.
- **Plausible Range**: $RSSI \in [-120.0, -30.0]$ dBm. Warnings are raised for measurements outside this range (extreme near-field or out of coverage).

### 2. Geographic Boundary Ranges
- **Latitude Limits**: $[-90.0, 90.0]$ degrees (WGS84).
- **Longitude Limits**: $[-180.0, 180.0]$ degrees (WGS84).

### 3. Tower RF Parameters
- **Transmit Power ($P_{tx}$)**: $[10.0, 60.0]$ dBm.
- **Antenna Height**: $[1.0, 300.0]$ meters.
- **Max Coverage Radius**: $50,000$ meters.
- **Cellular Band Tolerance**: $\pm 50.0$ MHz when resolving frequency matching across known GSM, LTE, WCDMA, and 5G bands.

### 4. Physical Consistency Check (TA ↔ RSSI)
Checks distance correlations between Timing Advance (TA) delay steps and Received Signal Strength (RSSI):
- If the Timing Advance value is $> 10$ (equivalent to a distance $> 5.5$ km), yet the RSSI is stronger than $-50.0$ dBm, a `TA_RSSI_INCONSISTENCY` warning is raised.

### 5. GDOP Geometry Classifications
- **High Confidence**: $GDOP \le 2.0$ (Excellent geometry).
- **Medium Confidence**: $GDOP \le 5.0$ (Good geometry).
- **Low Confidence**: $GDOP > 5.0$ (Poor/collinear geometry).

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
# Run Ruff linting check and auto-fix simple issues
ruff check scientific --fix

# Run Black formatting check & reformat files
black scientific

# Run the test suite
pytest
```


---

## 📊 Pipeline Validation Benchmarks

Benchmark metrics are computed by `scientific.pipeline.benchmarks` and verified against calibrated thresholds defined in `scientific.pipeline.benchmark_thresholds`.

### Calibrated Threshold Constants

All thresholds are derived from empirical analysis of the four real operator datasets (Airtel, BSNL, Jio, Vi).

| Threshold Parameter | Config Field | Default | Description |
| :--- | :--- | :--- | :--- |
| **Coordinate Accuracy** | `coordinate_accuracy_threshold_m` | `500.0 m` | Maximum acceptable tower coordinate error |
| **Accuracy Coverage** | `coordinate_accuracy_acceptable_pct` | `80.0%` | Minimum % of towers within accuracy threshold |
| **Validation Pass Rate** | `min_validation_pass_rate` | `0.70` | Minimum fraction of CDR records passing validation |
| **Tower Resolution Rate** | `min_tower_resolution_rate` | `0.60` | Minimum fraction of resolved towers (exact + prefix) |
| **Max Unknown Towers** | `max_unknown_tower_pct_per_operator` | `40.0%` | Maximum unknown tower % for any single operator |
| **Kalman Improvement** | `min_kalman_improvement_factor` | `1.0` | Kalman smoothing must not degrade accuracy |
| **Confidence Bounds** | `confidence_score_min / max` | `[0.0, 1.0]` | Strict interval for all confidence scores |
| **Evidence Hash** | `evidence_hash_length` | `64` | SHA-256 hex digest length |

### Benchmark Metric Definitions

| Metric | Formula | Acceptance |
| :--- | :--- | :--- |
| **Validation Pass Rate** | `validated_records / total_records` | ≥ 0.70 |
| **Tower Resolution Rate** | `(exact + prefix_lac + prefix_mnc + prefix_mcc) / total` | ≥ 0.60 |
| **Unknown Tower %** | `unresolved / operator_total × 100` | ≤ 40% per operator |
| **Kalman Improvement Factor** | `mean(raw_errors) / mean(smoothed_errors)` | ≥ 1.0 |
| **Coordinate Accuracy** | Haversine distance between reference and computed | ≥ 80% within 500 m |

### Running Benchmarks

```python
from scientific.pipeline.benchmarks import run_pipeline_benchmarks
from scientific.pipeline.benchmark_thresholds import (
    CALIBRATED_THRESHOLDS,
    verify_benchmark_compliance,
)

metrics = run_pipeline_benchmarks(
    validated_records=850,
    total_records=1000,
    tower_data=tower_resolution_list,
)
report = verify_benchmark_compliance(metrics)
print(report["overall_pass"])  # True / False
```

---

## 🔐 Evidence & Reproducibility

### SHA-256 Evidence Hashing

The evidence engine (`scientific/pipeline/evidence.py`) generates deterministic SHA-256 tamper-evident hashes for all audit evidence packets:

1. **Hash excludes self-referential keys** (`evidence_hash`, `hash`, `sha256_hash`) to avoid circular dependencies.
2. **Canonical JSON serialization** with `sort_keys=True` ensures ordering invariance.
3. **UTF-8 encoding** guarantees platform-independent byte sequences.
4. **Determinism guarantee**: Identical inputs always produce identical 64-character hex digests.

```python
from scientific.pipeline.evidence import compute_evidence_hash, synthesize_evidence

evidence = synthesize_evidence(
    scenario_id="SCN-001", towers=towers, measurements=measurements
)
hash_1 = compute_evidence_hash(evidence)
hash_2 = compute_evidence_hash(evidence)
assert hash_1 == hash_2  # Always True — deterministic
assert len(hash_1) == 64  # SHA-256 hex digest
```

### Confidence Score Clamping

All confidence scores are strictly bounded within the `[0.0, 1.0]` interval via:
- Exponential decay mapping: $CS = \exp(-0.15 \cdot (GDOP - 1.0))$
- Post-computation clamping: `max(0.0, min(1.0, score))`
- Edge-case handling for insufficient towers, collinear geometries, and singular matrices

---

## 📦 Demo Dataset

A curated demonstration dataset is available in `datasets/demo/` containing representative CDR records from all four supported operators.

| File | Operator | Records |
| :--- | :--- | :--- |
| `demo_airtel.csv` | Airtel | 25 |
| `demo_bsnl.csv` | BSNL | 29 (complete) |
| `demo_jio.csv` | Jio | 25 |
| `demo_vi.csv` | Vi | 25 |
| `asterion_demo_dataset.csv` | All operators | ~104 |

### Regeneration

```bash
python scripts/generate_demo_dataset.py
```

### Full Pipeline Verification

```bash
# Run verification script (generates JSON report)
python scripts/verify_pipeline.py

# Run verification test suite
pytest tests/scientific/pipeline/test_full_pipeline_verification.py -v
```

---

## 🚀 Completed Scientific Engine Features (v0.3.0)

All scientific and mathematical components are fully implemented, verified, and benchmarked:

1. **RSSI Signal Generator** (`scientific/simulation/rssi_generator.py`): Simulates log-distance path loss.
2. **Noise Injection Model** (`scientific/simulation/noise_model.py`): Models shadow fading using standard normal distributions.
3. **Measurement Synthesizer** (`scientific/simulation/measurement_generator.py`): Produces synthetic measurements from scenarios.
4. **Non-Linear Least Squares Solver (NLLS)** (`scientific/pipeline/multilateration.py`): Performs trilateration.
5. **Quality-Weighted Centroid Fallback** (`scientific/pipeline/weighted_centroid.py`): Multi-factor quality-weighted centroid estimation incorporating RSSI, coordinate validity, tower density, and temporal freshness metrics.
6. **Movement & Handover Reconstruction** (`scientific/pipeline/movement.py`): Reconstructs chronological movement events, detects cell-sector CGI handovers, calculates travel kinematics (speed, bearing, distance, dwell time), and flags implausible travel velocities (>350 km/h).
7. **Kalman Position Tracker & Path Smoothing** (`scientific/pipeline/kalman_tracker.py`): Performs 2D constant-velocity smoothing with anomaly dampening and handover preservation.
8. **GDOP & Covariance Confidence Estimator** (`scientific/pipeline/confidence.py`): Evaluates geometric errors and 1-sigma error ellipses.
9. **Evidence Synthesis & Cryptographic Tamper-Proofing** (`scientific/pipeline/evidence.py`): Generates audit evidence packets with deterministic SHA-256 tamper-evident hashes.
10. **End-to-End Pipeline Orchestrator** (`scientific/pipeline/runner.py`): Orchestrates simulation, validation, localization, tracking, evidence, and confidence.
11. **Pipeline Validation Benchmarks** (`scientific/pipeline/benchmarks.py`): Coordinate accuracy, validation pass rate, tower resolution, Kalman improvement, and per-operator unknown tower metrics.
12. **Calibrated Benchmark Thresholds** (`scientific/pipeline/benchmark_thresholds.py`): Empirically-calibrated acceptance criteria derived from real operator datasets.
13. **Heatmap Calculation Engine** (`scientific/pipeline/heatmap.py`): Spatial grid-based aggregation with normalized density, dwell time, confidence, and handover scores.
14. **Case Comparison Analysis** (`scientific/pipeline/case_comparison.py`): Spatial overlap, velocity trends, and similarity metrics across investigation cases.
15. **Report Formatter** (`scientific/pipeline/report_formatter.py`): Structured, neutral-language report data components for PDF exports.
16. **Investigation Summary Generator** (`scientific/pipeline/summary_generator.py`): Professional-grade narrative generation with Section 3F neutral terminology enforcement.
17. **Real Operator Dataset Pipeline Test Suite** (`tests/scientific/pipeline/test_operator_pipeline.py`): Zero-exception pipeline runs across Airtel, BSNL, Jio, and Vi.
18. **Full Pipeline Verification Suite** (`tests/scientific/pipeline/test_full_pipeline_verification.py`): Benchmark compliance, hash determinism, and confidence bounds verification.
19. **Curated Demo Dataset** (`datasets/demo/`): Representative CDR records from all four operators for platform demonstration.

