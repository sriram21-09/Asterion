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
- [x] **Dinesh (Frontend):**
  - [x] Define TypeScript types for Simulation outputs and parameters
  - [x] Create API service client layer for `/simulation/generate`
  - [x] Implement Zustand state stores for simulated measurements
  - [x] Create static placeholder UI tables for measurements list

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
- [x] **Dinesh (Frontend):**
  - [x] Implement Axios client queries for validate API
  - [x] Create validation status panel displaying audit metrics

---

## 📅 Day 3: Localization Engine (Core NLLS)
- [x] **Chaitanya (Scientific):**
  - [x] Implement initial position estimation logic (e.g., using signal-strength weighted calculations) to provide starting guesses for NLLS optimization
  - [x] Implement NLLS Multilateration solver using `scipy.optimize.least_squares` (`scientific/pipeline/multilateration.py`)
  - [x] Write mathematical unit tests verifying geometry convergence on prepared validation scenarios
- [x] **Sriram (Project Lead):**
  - [x] Create `localization_results` ORM model (with `case_id` relation) and migrations
  - [x] Implement `LocalizationRepository` and `LocalizationService`
  - [x] Create endpoint `POST /localization/run` returning coordinates and computation timing
- [x] **Dinesh (Frontend):**
  - [x] Add API services client to call `/localization/run`
  - [x] Implement a static placeholder Localization Result Card detailing metrics

---

## 📅 Day 4: Tracking Engine (Kalman Filter)
- [x] **Chaitanya (Scientific):**
  - [x] Implement Constant-Velocity 2D Kalman Filter tracker (`scientific/pipeline/kalman_tracker.py`)
  - [x] Write unit tests verifying tracking path convergence and noise smoothing
- [x] **Sriram (Project Lead):**
  - [x] Create `tracking_results` ORM model (linking to `cases` and `localization_results.id`) and migrations
  - [x] Implement `TrackingRepository` and `TrackingService`
  - [x] Create API route `POST /tracking/run` returning path tracking arrays
- [x] **Dinesh (Frontend):**
  - [x] Implement API client layers for tracking execution
  - [x] Create a static path coordinate list table showing smoothed track steps

---

## 📅 Day 5: Confidence & Evidence Engines
- [x] **Chaitanya (Scientific):**
  - [x] Implement GDOP-based geometric analysis and covariance-derived uncertainty calculations in `scientific/pipeline/confidence.py`
  - [x] Implement audit evidence builder inside `scientific/pipeline/evidence.py`
  - [x] Test confidence bounds on collinear vs. equilateral geometries
  - [x] Verify project roadmap/plan for upcoming reporting tasks (PDF, etc.)
- [x] **Sriram (Project Lead):**
  - [x] Create `confidence_results` database schema (linking to `cases` and `localization_results.id`) and migrations
  - [x] Implement repository layers and services for confidence and case evidence retrieval
  - [x] Create routes `POST /confidence/run` and `GET /evidence/{case_id}`
  - [x] Enhance `backend/seed_db.py` to insert synthetic `Tower`, `Measurement`, `LocalizationResult`, `TrackingResult`, and `ConfidenceResult` records.
  - [x] Run `seed_db.py` to populate database.
- [x] **Dinesh (Frontend):**
  - [x] Implement API client layers for confidence and evidence
  - [x] Create a static Confidence Badge Card showing level, score, and error ellipses
  - [x] Create a static Evidence Summary Card showing accepted vs. rejected lists
  - [x] Update `frontend/src/pages/EvidenceExplorer.tsx` to fetch real evidence data instead of using `MOCK_EVIDENCE_RUNS`.
  - [x] Update `frontend/src/pages/InvestigationDashboard.tsx` to fetch real tracking data instead of using mock timeline events.
  - [x] Update `frontend/src/pages/Reports.tsx` to reflect real metrics and handle placeholders based on the roadmap.

---

## 📅 Day 6: Pipeline Integration & E2E Testing
- [x] **Chaitanya (Scientific):**
  - [x] Create the central runner script `scientific/pipeline/runner.py` connecting the modules
  - [x] Benchmark execution time (ensuring performance runs within HLD performance targets: <2s for localization on the demo dataset)
  - [x] Add pipeline runner integration tests
- [x] **Sriram (Project Lead):**
  - [x] Run complete database persistence test suites
  - [x] Perform Docker stack smoke testing (`docker compose up --build`)
  - [x] Verify integrated endpoint orchestration in GitHub CI
- [x] **Dinesh (Frontend):**
  - [x] Interconnect stores and wire components to sequencially trigger actual API pipelines
  - [x] Verify loading, warning, and error components render properly

---

## 📅 Day 7: Stabilization, Review & Release
- [x] **Sriram (Project Lead):**
  - [x] Resolve P0/P1 bugs and perform test validations
  - [x] Update Swagger descriptions, example payloads, and CHANGELOG.md
  - [x] Merge branches and tag version release `v0.2.0` on main
- [x] **Chaitanya (Scientific):**
  - [x] Update standalone scientific package documentation
  - [x] Ensure all automated unit and integration tests pass cleanly (zero exceptions across Airtel, BSNL, Jio, Vi operator files)
- [x] **Dinesh (Frontend):**
  - [x] Run production builds and verify types compile
  - [x] Update frontend structure documentation


