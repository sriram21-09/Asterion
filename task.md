# 📘 Week 2 Task Tracker — Scientific Engine Sprint

This tracker outlines the day-by-day developer tasks for Sriram (Project Lead / Backend), Chaitanya (Scientific Engineer), and Dinesh (Frontend Lead) to implement and integrate the core scientific core.

---

## 📅 Day 1: Measurement Simulator
- [x] **Chaitanya (Scientific):**
  - [x] Implement RSSI Signal Generator (`scientific/simulation/rssi_generator.py`)
  - [x] Implement Noise Model with Gaussian and shadow fading (`scientific/simulation/noise_model.py`)
  - [x] Implement Measurement Synthesizer (`scientific/simulation/measurement_generator.py`)
  - [x] Write pytest unit tests for simulation modules
- [x] **Sriram (Project Lead):**
  - [x] Create `backend/app/models/measurement.py` database schema
  - [x] Run Alembic migrations to create `measurements` table
  - [x] Implement `MeasurementRepository` and `MeasurementService`
  - [x] Create `POST /simulation/generate` API router skeleton
  - [x] Write database and API endpoint unit tests
- [ ] **Dinesh (Frontend):**
  - [ ] Define TypeScript types for Simulation outputs and parameters
  - [ ] Create API service client layer for `/simulation/generate`
  - [ ] Implement Zustand state stores for simulated measurements
  - [ ] Create static placeholder UI tables for measurements list

---

## 📅 Day 2: Measurement Validation Engine
- [x] **Chaitanya (Scientific):**
  - [x] Expand coordinate, RSSI, and timing advance validators in `validators.py`
  - [x] Add WGS84 bounding checking rules
  - [x] Write unit tests checking out-of-bounds inputs and duplicates
- [x] **Sriram (Project Lead):**
  - [x] Create API endpoint `POST /measurements/validate`
  - [x] Integrate validators into backend service layer
  - [x] Write validation router unit tests
- [ ] **Dinesh (Frontend):**
  - [ ] Implement Axios client queries for validate API
  - [ ] Create validation status panel displaying audit metrics

---

## 📅 Day 3: Localization Engine (Core NLLS)
- [ ] **Chaitanya (Scientific):**
  - [ ] Implement initial position estimation logic (e.g., using signal-strength weighted calculations) to provide starting guesses for NLLS optimization
  - [ ] Implement NLLS Multilateration solver using `scipy.optimize.least_squares` (`scientific/pipeline/multilateration.py`)
  - [ ] Write mathematical unit tests verifying geometry convergence on prepared validation scenarios
- [ ] **Sriram (Project Lead):**
  - [ ] Create `localization_results` ORM model (with `case_id` relation) and migrations
  - [ ] Implement `LocalizationRepository` and `LocalizationService`
  - [ ] Create endpoint `POST /localization/run` returning coordinates and computation timing
- [ ] **Dinesh (Frontend):**
  - [ ] Add API services client to call `/localization/run`
  - [ ] Implement a static placeholder Localization Result Card detailing metrics

---

## 📅 Day 4: Tracking Engine (Kalman Filter)
- [ ] **Chaitanya (Scientific):**
  - [ ] Implement Constant-Velocity 2D Kalman Filter tracker (`scientific/pipeline/kalman_tracker.py`)
  - [ ] Write unit tests verifying tracking path convergence and noise smoothing
- [ ] **Sriram (Project Lead):**
  - [ ] Create `tracking_results` ORM model (linking to `cases` and `localization_results.id`) and migrations
  - [ ] Implement `TrackingRepository` and `TrackingService`
  - [ ] Create API route `POST /tracking/run` returning path tracking arrays
- [ ] **Dinesh (Frontend):**
  - [ ] Implement API client layers for tracking execution
  - [ ] Create a static path coordinate list table showing smoothed track steps

---

## 📅 Day 5: Confidence & Evidence Engines
- [ ] **Chaitanya (Scientific):**
  - [ ] Implement GDOP-based geometric analysis and covariance-derived uncertainty calculations in `scientific/pipeline/confidence.py`
  - [ ] Implement audit evidence builder inside `scientific/pipeline/evidence.py`
  - [ ] Test confidence bounds on collinear vs. equilateral geometries
- [ ] **Sriram (Project Lead):**
  - [ ] Create `confidence_results` database schema (linking to `cases` and `localization_results.id`) and migrations
  - [ ] Implement repository layers and services for confidence and case evidence retrieval
  - [ ] Create routes `POST /confidence/run` and `GET /evidence/{case_id}`
- [ ] **Dinesh (Frontend):**
  - [ ] Implement API client layers for confidence and evidence
  - [ ] Create a static Confidence Badge Card showing level, score, and error ellipses
  - [ ] Create a static Evidence Summary Card showing accepted vs. rejected lists

---

## 📅 Day 6: Pipeline Integration & E2E Testing
- [ ] **Chaitanya (Scientific):**
  - [ ] Create the central runner script `scientific/pipeline/runner.py` connecting the modules
  - [ ] Benchmark execution time (ensuring performance runs within HLD performance targets: <2s for localization on the demo dataset)
  - [ ] Add pipeline runner integration tests
- [ ] **Sriram (Project Lead):**
  - [ ] Run complete database persistence test suites
  - [ ] Perform Docker stack smoke testing (`docker compose up --build`)
  - [ ] Verify integrated endpoint orchestration in GitHub CI
- [ ] **Dinesh (Frontend):**
  - [ ] Interconnect stores and wire components to sequencially trigger actual API pipelines
  - [ ] Verify loading, warning, and error components render properly

---

## 📅 Day 7: Stabilization, Review & Release
- [ ] **Sriram (Project Lead):**
  - [ ] Resolve P0/P1 bugs and perform test validations
  - [ ] Update Swagger descriptions, example payloads, and CHANGELOG.md
  - [ ] Merge branches and tag version release `v0.2.0` on main
- [ ] **Chaitanya (Scientific):**
  - [ ] Update standalone scientific package documentation
  - [ ] Ensure all automated unit and integration tests pass cleanly
- [ ] **Dinesh (Frontend):**
  - [ ] Run production builds and verify types compile
  - [ ] Update frontend structure documentation
