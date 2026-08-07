# Asterion v1.0.0 Stable

This is the **v1.0.0 Stable** release of Asterion, marking a major milestone for the Explainable Telecom Localization & Investigation Support Platform. 

Asterion has transitioned from a hackathon concept into a stable, production-quality research prototype with a deterministic scientific pipeline and enterprise-grade release engineering.

## Overview
Asterion v1.0.0 provides a fully deterministic platform for parsing Call Data Records (CDRs), estimating missing geospatial data via log-distance path loss, generating spatial intersections (trilateration), and providing detailed provenance-tracked investigation reports.

## Major Features
- **Scientific Localization Engine**: Core algorithms that use established geometric and RF propagation principles to locate devices.
- **Measurement Augmentation**: Disclosed estimation of missing GPS coordinates using Cell Global Identity (CGI) centroids and signal strength logic.
- **Provenance Tracking**: Strict auditing of all datasets to guarantee that the scientific lineage of every measurement is explainable.
- **PDF Investigation Reports**: Generation of court-ready PDF exports complete with visualizations, evidence hashes, and deterministic outputs.
- **Environment Parity**: 100% execution behavior match between Local Development and Docker Compose instances.
- **Disaster Recovery**: Automated `.db` recovery mechanisms to ensure continued system availability.
- **Alembic Database Migrations**: Centralized schema management.

## Scientific Principles
Asterion abides by the philosophy: *"Prefer Unknown over inventing certainty."*
- All measurements are explicitly flagged as either `REAL` or `SIMULATED`.
- Outputs are fully deterministic: supplying the identical CDR CSV to Asterion v1.0 will always yield the precise same bounds, coordinates, and confidences.

## Docker Support
Deploy Asterion deterministically using the built-in `docker-compose.yml`. Both frontend (`npm ci`) and backend (`requirements-lock.txt`) utilize strictly locked dependency trees.

## Known Limitations
- Vector map export in PDF reports requires active internet connectivity. Offline maps are unsupported without pre-caching.
- Large CSV files (>500,000 rows) may take several minutes to process due to memory constraints on typical consumer hardware.

## Breaking Changes
- **None**: This is the initial stable release. The API contract (OpenAPI schemas and formats) is now frozen for the v1 line.

---
**Checksums** (example):
* `docker-compose.yml`: `sha256-...`
* `asterion-v1.0.0.tar.gz`: `sha256-...`
