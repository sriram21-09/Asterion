"""
Asterion Scientific Engine
==========================

Standalone scientific computation package for telecom localization,
multilateration, Kalman tracking, confidence estimation, and
evidence-based signal analysis.

This package is decoupled from the FastAPI backend and can be
imported independently for research, simulation, and validation.

Submodules
-----------
- ``scientific.config``      — Simulation & validation configuration.
- ``scientific.constants``   — Physical, RF, and geodesy constants.
- ``scientific.logger``      — Console logging helper.
- ``scientific.models``      — Pydantic data models.
- ``scientific.validation``  — Domain validators.
- ``scientific.simulation``  — (Week 2) Simulation pipeline.
- ``scientific.pipeline``    — (Week 2) End-to-end pipeline runner.
"""

__version__ = "0.1.0"
