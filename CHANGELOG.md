# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
