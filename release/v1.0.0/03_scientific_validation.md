# Asterion v1.0 Scientific Validation & Determinism

## Executive Summary
This document summarizes the scientific validation checks performed as part of the v1.0 Stabilization Sprint (Phase 10). The goal of Asterion is to provide explainable, deterministic, and verifiable telecom localization.

## 1. Output Determinism

### 1.1 Algorithmic Determinism
A full codebase audit verified that no stochastic processes, non-deterministic heuristics, or unseeded pseudo-random number generators (PRNGs) are used during the scientific derivation of:
- Cellular Trilateration (`localization_service`)
- Sector-based Area Estimation (`localization_service`)
- Path Loss Estimation (`import_service`)
- Spatio-temporal Movement Scoring (`movement_service`)

Given the exact same input CDR dataset and Tower definitions, Asterion v1.0 is guaranteed to produce **identical outputs, confidences, and bounding boxes** on every execution, across all environments (Local, Docker, CI/CD).

### 1.2 Mathematical Correctness
The localization engine relies on established geometric and RF propagation principles:
- **Haversine Distance**: Utilized across all distance calculations to account for Earth's curvature.
- **Log-Distance Path Loss**: Employed to convert signal strength (RSSI) into distance estimates where explicit GPS or Timing Advance data is missing.
- **Centroid Computation**: Calculated via standard geometric center of mass over valid intersecting areas.

## 2. Regression Testing

### 2.1 Standardized Datasets
As part of Phase 8, standardized regression datasets (`jio_complete.csv`, `airtel_complete.csv`) have been added to `datasets/regression/`. These serve as the ground-truth inputs for all future scientific acceptance tests.

### 2.2 Validation Protocol
For all major releases (including v1.0), the application must parse these datasets and produce identical spatio-temporal artifacts (coordinates, bounds, confidence scores). The CI/CD pipeline enforces this determinism.

## Conclusion
Asterion v1.0 meets the stringent requirements for scientific integrity, output determinism, and explainability required for legal and investigative telecom analysis.
