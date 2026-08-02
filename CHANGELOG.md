# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-02

### Added
- **Complete End-to-End Scientific Pipeline**: Fully automated data flow from CDR upload to movement reconstruction, localization, evidence synthesis, and report generation.
- **Unified CDR Importer**: Robust parsing logic for multiple telecom operators (Airtel, BSNL, Jio, Vi) with automatic vendor detection.
- **Validation Engine Enhancements**: Comprehensive sanity, format, and physical validation constraints applied directly to raw CDR records.
- **Tower Resolution Module**: Automatic tower lookup and centroid fallback resolution to handle missing or sparse tower datasets.
- **Movement Reconstruction**: Generation of movement events, segment categorization (stationary, moving), and spatial path smoothing.
- **Summary & Report Generation**: Aggregated dashboard statistics and downloadable HTML/PDF report formatter exposing localization evidence.
- **E-Rakshak Test Datasets**: Standardized operator test suites integrated into the benchmark script (`verify_pipeline.py`) for automated CI accuracy checks.

### Changed
- **Backend Optimization**: Extensive query profiling, lazy loading, database indexing improvements, and API endpoint cleanup (removed unused mocks).
- **Docker Compose Production Build**: Finalized multi-stage container build process ensuring fully functional out-of-the-box deployment.

### Fixed
- Stabilized Kalman filter initialization against short measurement bursts.
- Resolved timestamp timezone inconsistencies during SQLite loading.
- Optimized multilateration bounds avoiding unconstrained search explosions.

## [0.2.0] - 2026-07-19

### Added
- **Measurement Simulator**: Full RSSI signal generation implementing log-distance path loss, noise models, and synthetic measurement batch generators.
- **Validation REST API**: Business logic and sanity validators for measurement batches.
- **NLLS Multilateration Solver**: Non-Linear Least Squares trilateration algorithm to compute device estimated coordinate positions.
- **Weighted Centroid Fallback**: Centroid estimation algorithm as a fallback when insufficient cell towers are available.
- **Kalman Position Tracker**: 2D constant-velocity state filter to smooth calculated localization track paths.
- **Confidence Engine**: Dilution of Precision (GDOP) and covariance error ellipse calculation modules.
- **Evidence Engine**: Audit log evidence packets compiling validation rejections and tracking metrics.
- **Pipeline Orchestrator**: Central pipeline runner executing simulations-to-evidence flows.
- **Centralized Pipeline Coordinator Store**: Central frontend Zustand store (`pipelineCoordinator`) orchestrating step execution, UI states, logs, and visualization variables.
- **E2E Integration Tests**: Comprehensive pipeline and algorithm tests asserting E2E flow correctness with 180 additional tests.

### Fixed
- Import resolution bugs in scientific validators (`validators.py`).
- Enhanced Swagger/OpenAPI specifications with example payloads, detailed field descriptions, and documented HTTP error codes.

## [0.1.0] - 2026-07-12

### Added
- Decoupled Scientific computation engine (`scientific/`) containing physical/RF constants, frozen configurations, and Pydantic schemas (Towers, Measurements, Scenarios).
- Standalone validator package ensuring coordinates, frequency bands, and measurement relationships conform to physics.
- FastAPI backend implementing the Repository-Service-Router pattern.
- Database schemas for Cases, Scenarios, and Towers utilizing SQLAlchemy with automated Alembic migrations.
- Global exception filters, centralized JSON wrappers, and duration-logging middleware.
- React frontend featuring a responsive dashboard shell, dark mode persistence, and CRUD interfaces for Cases and Scenarios.
- Docker Compose orchestrating the multi-service deployment.
- High-coverage test suite containing 323 passing tests across backend, database, api, and scientific package modules.
- Database validation demo script (`scripts/db_demo.py`) and review guides.
