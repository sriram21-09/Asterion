# Asterion Week 3 & Week 4 Master Execution Plan

**Document Version:** 1.0 (CTO Approved)
**Project State:** Architecture Frozen
**Target Release:** Asterion v1.0
**Timeline:** 14 Days

---

## 1. Executive Summary & Goals
This document serves as the single source of truth for the technical execution of Asterion v1.0 during Week 3 and Week 4. The project is shifting from a simulator-driven coordinate estimator to a production-quality, explainable telecom investigation platform that processes real multi-operator datasets.

### Primary Objectives
*   Build a robust, multi-operator CDR parser and normalization engine.
*   Implement validation, tower intelligence, and movement reconstruction layers designed for the real dataset constraints.
*   Create a professional-grade Leaflet-based interactive dashboard, heatmap, and timeline.
*   Generate verified and reproducible investigation reports in PDF format.
*   Validate the scientific pipeline using systematic metrics and reference benchmarks.

---

## 2. Feature Prioritization (Three-Tiered Scope)

To manage schedule risk and ensure the timely delivery of a high-quality product, features are prioritized into three distinct tiers. The team must focus on completing Tier 1 before proceeding to Tier 2, and treat Tier 3 as strictly optional stretch items.

```
┌────────────────────────────────────────────────────────┐
│ TIER 1: MUST HAVE (Core Investigation Workflow)        │
│ ── CDR Import & Parsers (Airtel, Jio, BSNL, Vi)        │
│ ── Normalization Layer & Unified Database Schema       │
│ ── CDR Validation Service                              │
│ ── Tower Intelligence (Three Confidence Levels)        │
│ ── Movement Reconstruction (Handover-Aware)            │
│ ── Dashboard Layout, Leaflet Map & Timeline             │
│ ── PDF Report Generation with Full Metadata            │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ TIER 2: SHOULD HAVE (Explainability & Analytics)       │
│ ── Probability Heatmap (Configurable Normalized Weights)│
│ ── Confidence Visualization & Error Ellipses           │
│ ── Evidence Explorer with SHA-256 Reproducibility      │
│ ── Scientific Pipeline Validation Benchmarks            │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ TIER 3: NICE TO HAVE (Stretch Goals - Optional)        │
│ ── Case Comparison Panel                               │
│ ── Advanced Multi-case Analytics & Cross-Reference     │
│ ── UI Micro-animations & Interactive Sound Transitions │
└────────────────────────────────────────────────────────┘
```

---

## 3. Core Architectural Adaptations

### A. Tower Intelligence (Three Confidence Levels)
Jio and Vi operator files do not contain explicit latitude/longitude coordinates. To handle this without introducing false geographical assumptions, the Tower Intelligence engine classifies tower positions into three strict categories:
1.  **Known Coordinates:** Coordinates parsed directly from columns inside Airtel and BSNL files (Confidence Value = 1.0).
2.  **Estimated Coordinates:** Coordinates resolved from secondary lookups (Confidence Value = 0.6).
3.  **Unknown Coordinates:** Jio and Vi towers with unresolved coordinates. They are recorded in the database with `latitude = null` and `longitude = null` (Confidence Value = 0.2). No cross-operator matching of Cell IDs will be performed.

### B. Handover-Aware Movement Reconstruction
Mobile devices transition between cellular sectors and frequencies without physical device movement. The movement reconstruction module implements **Handover Detection**:
*   If consecutive records switch Cell IDs but resolve to identical coordinates (same site, different sectors), the event is flagged as a `handover` event.
*   The physical travel distance and speed calculation for that step is set to `0.0`.
*   Consecutive records with impossibly high velocities (e.g. >350 km/h) are flagged as potential network roaming or handover noise.

### C. Quality-Weighted Localization
The weighted centroid algorithm will calculate device position by weighting towers based on:
$$\text{Weight} = \text{Norm}(\text{Validation Score}) + \text{Coordinate Availability} + \text{Timestamp Completeness} + \text{Tower Confidence}$$
Where:
*   *Validation Score* = $1.0$ if valid, $0.5$ if warnings, $0.0$ if errors.
*   *Coordinate Availability* = $1.0$ if Known, $0.6$ if Estimated, $0.2$ if Unknown (matching tower confidence values).
*   *Timestamp Completeness* = $1.0$ if fully formed, $0.5$ if missing seconds, $0.0$ if invalid.
*   *Tower Confidence* = Confidence level assigned by the Lookup Service (1.0 for Known, 0.6 for Estimated, 0.2 for Unknown).
Record count will **not** be used as a primary location weight.

### D. Configurable Heatmap scoring
The probability heatmap will use normalized inputs rather than hardcoded weight matrices. The score for cell location $j$ is:
$$S_j = w_1 \cdot \text{Norm}(\text{Density}_j) + w_2 \cdot \text{Norm}(\text{DwellTime}_j) + w_3 \cdot \text{Norm}(\text{Confidence}_j) + w_4 \cdot \text{Norm}(\text{Transitions}_j)$$
Weights $w_1, w_2, w_3, w_4$ are defined in a backend config file/default settings to simplify frontend development and prioritize core views.

### E. Reproducibility Evidence Records
To guarantee auditability, `evidence_records` store the following fields:
*   `algorithm_version`: Version string of the active solver (e.g. `v1.0.0-centroid`).
*   `scientific_module`: Python path (e.g., `scientific.pipeline.weighted_centroid`).
*   `input_record_ids`: JSON list of the normalized `cdr_records` IDs.
*   `parameters`: JSON map of optimization parameters (e.g., weights, thresholds).
*   `reproducibility_hash`: A SHA-256 hash of the string concatenated from `input_record_ids`, `algorithm_version`, and `parameters_json`.

### F. Terminology Standards
To maintain professional investigation compliance, all narrative summaries and interface text will use strictly neutral language:
*   **Approved Terms:** `the analyzed device`, `the observed device`, `the target identifier`, `the analyzed subscriber`.
*   **Prohibited Terms:** `the suspect`, `the criminal`, `the perpetrator`, `guilty party`.

---

## 4. Measurable Success Metrics (KPIs)

### Engineering KPIs
1.  **Import Success:** 100% of supported Airtel, Jio, BSNL, and Vi CDR files import without schema crashes.
2.  **Normalization Quality:** Automatically normalize all records that pass schema validation to the unified database schema.
3.  **Pipeline Stability:** End-to-end processing completes with 0 server-side unhandled exceptions.
4.  **API Success Rate:** ≥99% success rate during functional testing.
5.  **Test Coverage:** ≥80% code coverage for all newly added backend and scientific modules.

### Scientific KPIs
1.  **Validation Coverage:** Malformed records are tagged and written to validation reports with 100% detection rate.
2.  **Tower Provenance Transparency:** Tower resolution metadata correctly reports coordinate sources (Known/Estimated/Unknown) for all resolved Cell IDs.
3.  **Bounded Confidence:** Computed confidence scores remain bounded within the $[0, 1]$ interval.
4.  **Chronological Ordering:** Reconstructed movement path vectors verify strict chronological ordering of timestamps.

### UX KPIs
1.  **Load Times:** Main dashboard view loads in < 3 seconds on the maximum dataset (~10,000 records).
2.  **Interactive Responsiveness:** Filtering, searching, and panning on Leaflet layers execute without layout freezes.
3.  **PDF Completeness:** PDF reports generate successfully, containing the full metadata header block, validation results, and evidence summaries.

---

## 5. Week 3 Sprint: Data Pipeline & Normalization Layer

### Day 1: CDR Import Base & Parsers (Airtel & BSNL)
*   **Dev 1 (Backend):**
    *   Create migrations for `import_jobs` and `cdr_records` schemas.
    *   Implement base `CDRImportService` interface.
    *   Build parser for Airtel CSV (parses comma-separated entries, splits coordinates on slash `21.29669/72.8915`).
    *   Build parser for BSNL CSV (extracts coordinates embedded in BTS string `Lat-22.39711; Long-88.43938`).
    *   Create `/api/v1/import/upload` upload endpoint.
*   **Dev 2 (Scientific):**
    *   Build CDR Validation Rules (verifies timestamp formats, duplicate detection, and coordinate bounds checking).
    *   Create basic unit tests for validators.
*   **Dev 3 (Frontend):**
    *   Create Import UI page.
    *   Build drag-and-drop file uploader with operator auto-detection.
*   **Git Branch:** `feat/week3-day1-cdr-import`

### Day 2: Jio & Vi Parsers & Normalization
*   **Dev 1 (Backend):**
    *   Build Jio parser (skips 18 header metadata lines, parses hex Cell ID).
    *   Build Vi parser (skips 7 header lines, parses date in `DD-MM-YYYY` format).
    *   Integrate normalization mapping layer converting all inputs to unified `cdr_records` table.
*   **Dev 2 (Scientific):**
    *   Build `CDRValidationService` to generate validation reports and calculate overall data quality scores.
*   **Dev 3 (Frontend):**
    *   Create Import Status panel showing upload list, record counts, and parsing success states.
*   **Git Branch:** `feat/week3-day2-normalization`

### Day 3: Tower Intelligence Engine
*   **Dev 1 (Backend):**
    *   Build `TowerIntelligenceService`.
    *   Implement lookup table matching Cell Global ID (CGI) to coordinates.
    *   Enforce 3 confidence categories: Known, Estimated, Unknown.
*   **Dev 2 (Scientific):**
    *   Implement tower density calculation and lookup fallbacks (exact match to MCC-MNC-LAC-CI, falling back to prefix if coordinates are missing).
*   **Dev 3 (Frontend):**
    *   Build Tower Registry Explorer view.
    *   Integrate tower marker layer on Leaflet map.
*   **Git Branch:** `feat/week3-day3-tower-intelligence`

### Day 4: Handover-Aware Movement Reconstruction
*   **Dev 1 (Backend):**
    *   Build `MovementReconstructionService`.
    *   Implement chronologically sorted movement event generation with `handover` filtering.
    *   Populate `movement_events` table.
*   **Dev 2 (Scientific):**
    *   Implement speed and distance algorithms. Tag records as `handover` when coordinates do not change but Cell IDs do.
*   **Dev 3 (Frontend):**
    *   Build Movement Timeline component in UI.
    *   Draw the device travel polyline on the Leaflet map.
*   **Git Branch:** `feat/week3-day4-movement-reconstruction`

### Day 5: Location Intelligence Integration
*   **Dev 1 (Backend):**
    *   Create `DashboardService` aggregation endpoints.
    *   API endpoint: `GET /api/v1/dashboard/{case_id}/summary`.
*   **Dev 2 (Scientific):**
    *   Adapt weighted centroid algorithm to use normalized quality and validation scores as weights.
    *   Integrate Kalman tracker to smooth computed movement paths.
*   **Dev 3 (Frontend):**
    *   Add Leaflet Layer controls to toggle tower markers, smoothed Kalman path, and confidence circles.
*   **Git Branch:** `feat/week3-day5-location-intelligence`

### Day 6: Reproducible Evidence Engine & APIs
*   **Dev 1 (Backend):**
    *   Build `EvidenceGenerationService` implementing SHA-256 reproducibility hashing.
    *   Create routes `GET /api/v1/evidence/{case_id}` and `GET /api/v1/evidence/{case_id}/audit`.
*   **Dev 2 (Scientific):**
    *   Write integration test suites verifying end-to-end pipeline run from CSV input to location tracking.
*   **Dev 3 (Frontend):**
    *   Build Evidence Explorer card list with details panel displaying solver versions and reproducibility hashes.
*   **Git Branch:** `feat/week3-day6-evidence-api`

### Day 7: Week 3 Stabilization & PR Review
*   **Dev 1 (Backend):** Database migration cleanup, API route testing, index creation on `cdr_records` for queries.
*   **Dev 2 (Scientific):** Finalize scientific unit tests. Verify 0 exceptions are thrown during pipeline runs on all operator files.
*   **Dev 3 (Frontend):** Fix UI alignment, handle pagination for large datasets, clear TypeScript compiler warnings.
*   **Git Branch:** Keep `develop` active, merge feature branches to `develop` only. Do not merge to `main` halfway.

---

## 6. Week 4 Sprint: Analytics, Reports & Release

### Day 8: Case Details & Global Search
*   **Dev 1 (Backend):**
    *   Implement Global Search API `/api/v1/search?q=...` querying IMEI, IMSI, MSISDN, Cell ID, and Tower ID.
*   **Dev 2 (Scientific):**
    *   Implement template-based neutral summary text generator (observed device, target identifier, etc.).
*   **Dev 3 (Frontend):**
    *   Build Global Search bar on main dashboard header.
    *   Create Case Details overview statistics grid.
    *   Build "Investigation Health" status card on the dashboard to track pipeline status (Imported, Validated, Towers Resolved, Movement Reconstructed, Localization Complete, Confidence Generated, Evidence Logged, Report Ready).
*   **Git Branch:** `feat/week4-day8-dashboard`

### Day 9: Heatmap & Timeline Filtering
*   **Dev 1 (Backend):**
    *   Build `/api/v1/dashboard/{case_id}/heatmap` API supporting configurable weight settings.
*   **Dev 2 (Scientific):**
    *   Build heatmap calculation engine using normalized density, dwell, confidence, and transitions.
*   **Dev 3 (Frontend):**
    *   Integrate Leaflet Heatmap layer.
    *   Implement checkbox filters on the bottom timeline strip to toggle Import, Normalization, Calls, SMS, Movement, and Validation events.
*   **Git Branch:** `feat/week4-day9-heatmap-timeline`

### Day 10: Case Comparison (Tier 3 Stretch Goal)
*   **Dev 1 (Backend):** Build `/api/v1/cases/compare?ids=A,B` returning comparative metrics (overlapping towers, distance differences, confidence averages).
*   **Dev 2 (Scientific):** Write logic to calculate overlapping cell sectors and speed trends.
*   **Dev 3 (Frontend):** Build side-by-side Case Comparison view page with comparison graphs.
*   **Git Branch:** `feat/week4-day10-case-comparison`

### Day 11: PDF Investigation Reports
*   **Dev 1 (Backend):**
    *   Integrate ReportLab library.
    *   Design professional PDF report template including the required Investigation Metadata block.
*   **Dev 2 (Scientific):** Generate and format report tables, validation summaries, and static maps (avoid complex charts inside PDF).
*   **Dev 3 (Frontend):**
    *   Build Report Viewer page. Add "Generate Report" and "Download PDF" buttons.
*   **Git Branch:** `feat/week4-day11-reporting`

### Day 12: Pipeline Validation Benchmarks
*   **Dev 1 (Backend):**
    *   Implement `/api/v1/validation/benchmark` API.
*   **Dev 2 (Scientific):**
    *   Create benchmarking routines evaluating computed coordinates against known reference tower coordinates.
    *   Calculate validation pass rate, tower resolution rate, unknown tower percentage, and Kalman improvement factor.
*   **Dev 3 (Frontend):** Integrate Scientific Validation tab directly into the existing Case Details dashboard view displaying benchmark charts and validation metrics (saves page routing/standalone views).
*   **Git Branch:** `feat/week4-day12-validation-benchmarks`

### Day 13: Stabilization, Performance Optimization & Refactoring
*   **Dev 1 (Backend):** Query profiling. Add SQLite database indexes to optimize coordinate calculations. Clean up unused API skeleton endpoints.
*   **Dev 2 (Scientific):** Ensure absolute reproducibility of evidence generation hashes. Verify benchmark thresholds.
*   **Dev 3 (Frontend):** Implement lazy loading for Leaflet markers. Fix UI rendering lags. Clean up CSS transition delays.
*   **Git Branch:** `feat/week4-day13-optimization`

### Day 14: Demo Preparation & Final Release
*   **All Devs:**
    *   Run complete integration test suite.
    *   Finalize Docker container builds.
    *   Record 5-minute platform demo video.
    *   Tag repository version `v1.0.0` on `main` branch.
*   **Git Branch:** `release/v1.0.0` → merge to `main`

---

## 7. Folder & Code Structure

```
Asterion/
├── backend/
│   ├── app/
│   │   ├── api/v1/routers/
│   │   │   ├── import.py [NEW]
│   │   │   ├── dashboard.py [NEW]
│   │   │   ├── reports.py [NEW]
│   │   │   └── search.py [NEW]
│   │   ├── services/
│   │   │   ├── import_service.py [NEW]
│   │   │   ├── tower_service.py [NEW]
│   │   │   ├── movement_service.py [NEW]
│   │   │   └── report_service.py [NEW]
│   │   ├── models/
│   │   │   └── (new schemas for cdr_records, import_jobs, validation_reports, etc.)
│   │   └── database/
│   │       └── alembic/versions/ (new migration scripts)
├── scientific/
│   ├── pipeline/
│   │   ├── evidence.py (updated with SHA-256 hashes)
│   │   ├── weighted_centroid.py (updated with validation-based weights)
│   │   └── benchmarks.py [NEW]
│   └── validation/
│       └── validators.py (updated with CDR-specific validations)
└── frontend/
    └── src/
        ├── pages/
        │   ├── ImportPage.tsx [NEW]
        │   ├── InvestigationDashboard.tsx [NEW]
        │   ├── Reports.tsx [NEW]
        │   └── CaseComparison.tsx [NEW]
        └── components/
            ├── map/
            │   ├── LeafletMap.tsx [NEW]
            │   └── HeatmapLayer.tsx [NEW]
            └── timeline/
                └── TimelineStrip.tsx [NEW]
```
