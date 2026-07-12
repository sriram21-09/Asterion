# 📘 Week 2 — Scientific Engine Development Checklist

**Sprint:** Week 2 – Scientific Engine Sprint
**Role:** Chaitanya (Scientific Engineer)
**Prerequisite:** Week 1 Foundation Sprint ✅ (271 tests passing)

---

## Sprint Objective

Implement the core scientific computation pipeline: signal simulation, localization algorithms, tracking, and confidence estimation. By the end of Week 2, the `scientific/` package should accept a `ScenarioConfig`, generate synthetic measurements, solve for device position, and return a `LocalizationResult` + `ConfidenceResult`.

```
ScenarioConfig → RSSI Generator → Noise Injection → Solver (NLLS) → Kalman Filter → Confidence → Results
```

---

## Module 1: RSSI Signal Generator

**Location:** `scientific/simulation/rssi_generator.py`

- [ ] Implement log-distance path-loss model: `PL(d) = PL(d₀) + 10·n·log₁₀(d/d₀)`
- [ ] Use `PropagationDefaults` from `ScenarioConfig` for environment-specific parameters
- [ ] Compute tower-to-device distance using `haversine_distance_m()` from `constants.py`
- [ ] Generate RSSI = `transmit_power_dbm - PL(d)` for each tower
- [ ] Handle edge cases: zero distance, device outside coverage radius
- [ ] Unit tests: known distance → expected RSSI, environment presets, edge cases

**Estimated time:** 2–3 hours

---

## Module 2: Noise Model

**Location:** `scientific/simulation/noise_model.py`

- [ ] Implement Gaussian (AWGN) noise injection: `rssi_noisy = rssi_clean + N(0, σ²)`
- [ ] Implement log-normal shadow fading: `rssi_faded = rssi_clean + N(0, σ_shadow²)`
- [ ] Support reproducible noise via `random_seed` from `SimulationParameters`
- [ ] Implement `enable_noise` toggle from `SimulationParameters`
- [ ] Support combined noise model: shadow fading + thermal noise
- [ ] Clamp noisy RSSI to valid range `[-150, 0]` dBm
- [ ] Unit tests: noise statistics, reproducibility with seed, noise-off bypass

**Estimated time:** 1.5–2 hours

---

## Module 3: Measurement Synthesizer

**Location:** `scientific/simulation/measurement_generator.py`

- [ ] Orchestrate RSSI generator + noise model per tower
- [ ] Generate `measurement_count` snapshots per tower (from `SimulationParameters`)
- [ ] Produce a list of `Measurement` objects with realistic timestamps, tower_ids
- [ ] Include uncertainty estimation per measurement
- [ ] Compute timing advance estimate from distance (`distance / TA_RESOLUTION_M`)
- [ ] Unit tests: correct measurement count, valid model output, timestamp ordering

**Estimated time:** 1.5–2 hours

---

## Module 4: Multilateration Solver (NLLS)

**Location:** `scientific/pipeline/multilateration.py`

- [ ] Implement Non-Linear Least Squares (NLLS) multilateration
- [ ] Convert RSSI to estimated distances using inverse path-loss model
- [ ] Set up cost function: `residual = estimated_distance - model_distance`
- [ ] Use `scipy.optimize.least_squares` (Levenberg-Marquardt) for solver
- [ ] Initial guess: weighted centroid of tower positions (by signal strength)
- [ ] Respect `max_iterations` and `convergence_threshold_m` from `SimulationParameters`
- [ ] Return `LocalizationResult` with estimated lat/lon, computation time, signals used
- [ ] Compute `error_m` if ground-truth is provided in `ScenarioConfig`
- [ ] Unit tests: known geometry → expected position, convergence, error bounds

**Estimated time:** 3–4 hours

---

## Module 5: Weighted Centroid Fallback

**Location:** `scientific/pipeline/weighted_centroid.py`

- [ ] Implement signal-strength-weighted centroid: `pos = Σ(w_i · pos_i) / Σ(w_i)`
- [ ] Weight function: `w_i = 10^(rssi_i / 10)` (linear power weighting)
- [ ] Use as initial guess for NLLS solver
- [ ] Use as standalone fallback when NLLS fails to converge
- [ ] Return `LocalizationResult` with `algorithm="weighted_centroid"`
- [ ] Unit tests: symmetric geometry → center position, dominant tower pulls toward it

**Estimated time:** 1–1.5 hours

---

## Module 6: Kalman Filter Tracker

**Location:** `scientific/pipeline/kalman_tracker.py`

- [ ] Implement linear Kalman filter for 2D position tracking
- [ ] State vector: `[latitude, longitude, velocity_lat, velocity_lon]`
- [ ] Process model: constant velocity with process noise
- [ ] Measurement model: position estimates from multilateration
- [ ] Tune Q (process noise) and R (measurement noise) matrices
- [ ] Support sequential update with multiple time-stamped localization results
- [ ] Return smoothed `LocalizationResult` with `algorithm="kalman"`
- [ ] Unit tests: single update, multi-step tracking, convergence behavior

**Estimated time:** 3–4 hours

---

## Module 7: Confidence & GDOP Estimator

**Location:** `scientific/pipeline/confidence.py`

- [ ] Compute GDOP from tower geometry matrix: `H = [∂d/∂x, ∂d/∂y]`, `GDOP = √(trace((HᵀH)⁻¹))`
- [ ] Map GDOP to confidence score using `gdop_excellent`, `gdop_good`, `gdop_poor` thresholds
- [ ] Compute error ellipse parameters (semi-major, semi-minor, orientation) from covariance
- [ ] Classify `confidence_level` as "high", "medium", or "low"
- [ ] Return `ConfidenceResult` with all fields populated
- [ ] Unit tests: equilateral triangle → low GDOP, collinear towers → high GDOP

**Estimated time:** 2–3 hours

---

## Module 8: End-to-End Pipeline Runner

**Location:** `scientific/pipeline/runner.py`

- [ ] Accept `ScenarioConfig` as input
- [ ] Stage 1: Validate input using `ScenarioValidator`
- [ ] Stage 2: Generate synthetic measurements via measurement synthesizer
- [ ] Stage 3: Run localization algorithm (multilateration / weighted centroid / hybrid)
- [ ] Stage 4: Optionally apply Kalman filter for tracking
- [ ] Stage 5: Compute confidence via GDOP estimator
- [ ] Return `PipelineResult` (new model): `LocalizationResult` + `ConfidenceResult` + metadata
- [ ] Log each stage via `scientific.logger`
- [ ] Unit tests: full pipeline with sample scenario, expected accuracy bounds

**Estimated time:** 2–3 hours

---

## Module 9: Validation Engine Enhancements

**Location:** `scientific/validation/validators.py` (extend existing)

- [ ] Add `ResultValidator`: verify localization results are within scenario bounds
- [ ] Add cross-validation: compare result error against expected confidence level
- [ ] Add batch validation for multiple scenarios
- [ ] Unit tests for new validators

**Estimated time:** 1–1.5 hours

---

## Integration & Testing

- [ ] Run full test suite after each module implementation
- [ ] Create `tests/test_week2_pipeline.py` with end-to-end integration tests
- [ ] Verify pipeline produces results within documented accuracy bounds
- [ ] Verify all 4 algorithm types work: `multilateration`, `weighted_centroid`, `kalman`, `hybrid`
- [ ] Benchmark computation time (target: < 100ms per scenario for 3-4 towers)
- [ ] Test with all 3 scenario configs from `datasets/sample/scenario_example.json`

---

## Dependencies to Install

```
scipy          # NLLS solver (least_squares)
numpy          # Matrix operations, Kalman filter
```

Add to `requirements.txt` or `scientific/requirements.txt`.

---

## Week 2 Exit Criteria

| Requirement | Status |
|---|---|
| RSSI generator produces physically realistic values | ☐ |
| Noise model is reproducible with seed | ☐ |
| Multilateration achieves < 150m error on urban 3-tower scenario | ☐ |
| Kalman filter smooths position estimates over time | ☐ |
| GDOP correctly identifies poor vs. excellent tower geometry | ☐ |
| End-to-end pipeline runs from ScenarioConfig to results | ☐ |
| All Week 1 + Week 2 tests pass (target: 350+ tests) | ☐ |
| Scientific documentation updated with algorithm descriptions | ☐ |
| Pipeline integrated with backend API (if time allows) | ☐ |

---

## Recommended Implementation Order

```
Day 1: RSSI Generator + Noise Model (Modules 1–2)
Day 2: Measurement Synthesizer + Weighted Centroid (Modules 3, 5)
Day 3: Multilateration Solver (Module 4)
Day 4: Kalman Filter + Confidence Estimator (Modules 6–7)
Day 5: Pipeline Runner + Integration Tests (Modules 8–9)
```

---

*🔬 Asterion Scientific Engine — Week 2 Sprint Plan*
