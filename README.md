<p align="center">
  <h1 align="center">🛰️ Asterion</h1>
  <p align="center">
    <strong>Open-source telecom localization platform for explainable digital investigations.</strong>
  </p>
  <p align="center">
    Built for <strong>E-Rakshak 2026</strong> · Surat City Police · SVNIT Surat · NEXUS
  </p>
</p>

<p align="center">

![Version](https://img.shields.io/badge/Version-0.1.0-blue?style=flat-square)
![Status](https://img.shields.io/badge/Status-MVP%20Development-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-323%20Passing-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?style=flat-square&logo=typescript&logoColor=white)

</p>

---

## Table of Contents

- [Project Overview](#-project-overview)
- [Problem Statement](#-problem-statement)
- [Solution Overview](#-solution-overview)
- [Architecture](#%EF%B8%8F-architecture)
- [Technology Stack](#-technology-stack)
- [Repository Structure](#-repository-structure)
- [Current Development Status](#-current-development-status)
- [Getting Started](#-getting-started)
- [API Reference](#-api-reference)
- [Scientific Engine](#-scientific-engine)
- [Testing](#-testing)
- [Development Roadmap](#%EF%B8%8F-development-roadmap)
- [Contributing](#-contributing)
- [Team](#-team)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)

---

## 📌 Project Overview

Asterion is an open-source investigation support platform that demonstrates how multiple cellular tower measurements can be scientifically combined to estimate a device's probable location.

Rather than treating localization as a black box, Asterion emphasizes **explainability** — showing exactly how measurements contribute to localization, how uncertainty is quantified, and why the final estimated position was produced.

The platform is being developed for **E-Rakshak 2026**, a cybersecurity and digital investigation hackathon organized by the Surat City Police, Sardar Vallabhbhai National Institute of Technology (SVNIT) Surat, and NEXUS. The hackathon focuses on solving real-world law enforcement and cybercrime challenges through technology.

Asterion is designed to serve both as a hackathon-ready MVP and a long-term open-source educational and research platform.

### Who Is This For?

| Audience | Value |
|----------|-------|
| **Law Enforcement** | Transparent, evidence-backed location estimation for digital investigations |
| **Researchers** | Modular scientific engine for studying multilateration algorithms |
| **Students** | Educational platform demonstrating RF signal processing and geospatial analysis |
| **Developers** | Clean, well-documented codebase following modern engineering practices |

---

## 🚨 Problem Statement

Telecommunication records often provide investigators with signal measurements from multiple nearby cellular towers. While individual tower measurements indicate only broad coverage areas, investigations frequently require a more precise estimate of a device's probable location.

**Current challenges in telecom-based localization:**

| Challenge | Description |
|-----------|-------------|
| **Large search areas** | Single tower coverage areas span hundreds of meters to several kilometers |
| **Measurement noise** | Signal strength varies due to fading, multipath, and environmental factors |
| **Interpretation complexity** | Combining measurements from multiple towers requires domain expertise |
| **Confidence opacity** | Investigators lack visibility into how reliable an estimated location is |
| **Evidence gaps** | No transparent audit trail explaining why a location was estimated |

Asterion addresses these challenges by combining multiple telecom measurements using scientifically grounded localization techniques while maintaining complete transparency throughout the investigation workflow.

---

## 💡 Solution Overview

Asterion is designed as an **evidence-first investigation platform**. Instead of simply producing a coordinate on a map, the platform provides a complete investigation workflow with full explainability.

```text
┌─────────────┐     ┌────────────────┐     ┌──────────────────┐     ┌────────────────┐
│ Create Case │────▶│ Load / Import  │────▶│ Validate         │────▶│ Estimate       │
│             │     │ Measurements   │     │ Measurements     │     │ Location (NLLS)│
└─────────────┘     └────────────────┘     └──────────────────┘     └───────┬────────┘
                                                                            │
┌─────────────┐     ┌────────────────┐     ┌──────────────────┐            │
│ Export      │◀────│ Review         │◀────│ Analyze          │◀───────────┘
│ Report      │     │ Evidence       │     │ Confidence       │
└─────────────┘     └────────────────┘     └──────────────────┘
```

**Core capabilities (Version 1.0 target):**

- **Case Management** — Organize investigation cases with metadata and status tracking
- **Measurement Generation** — Simulate or import telecom signal measurements
- **Measurement Validation** — Reject corrupt or out-of-range measurements with detailed error reporting
- **Multilateration (NLLS)** — Estimate device position using Non-Linear Least Squares optimization
- **Movement Tracking** — Smooth sequential position estimates using a 2D Kalman Filter
- **Confidence Estimation** — Quantify localization reliability using GDOP and covariance analysis
- **Evidence Packaging** — Generate audit trails mapping every input to every output
- **Report Generation** — Produce investigation-ready summary reports

> **Design Principle:** Asterion supports investigators through _transparent decision support_ rather than automated decision making. Every result includes the mathematical reasoning behind it.

---

## 🏗️ Architecture

Asterion follows a **Layered Modular Monolith Architecture**, allowing independent development of core subsystems while keeping deployment simple for the MVP phase.

```text
┌──────────────────────────────────────────────────────────────────┐
│                    React Investigation UI                        │
│           Dashboard · Cases · Scenarios · Reports                │
└──────────────────────────────▲───────────────────────────────────┘
                               │ REST API (JSON)
┌──────────────────────────────▼───────────────────────────────────┐
│                       FastAPI Backend                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Case Manager │  │ Scenario Svc │  │ Exception Handlers   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Repositories │  │ Middleware   │  │ Response Wrappers    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────────────────────────▲───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│               Scientific Computation Core                        │
│                                                                  │
│   Constants · Config · Models · Validators                       │
│   Simulator → NLLS → Kalman → Confidence → Evidence              │
└──────────────────────────────▲───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│                     SQLite Database                               │
│         Cases · Scenarios · Towers · Measurements                │
│         Localization Results · Tracking · Confidence              │
└──────────────────────────────────────────────────────────────────┘
```

**Key architectural decisions:**

- **Repository-Service-Router pattern** — Clean separation between data access, business logic, and HTTP concerns
- **Decoupled Scientific Engine** — The `scientific/` package operates independently of FastAPI and can be used in notebooks, scripts, or batch pipelines
- **Frozen configuration** — All scientific parameters use immutable dataclasses to prevent side effects
- **Business identifier strategy** — APIs expose human-readable codes (`CASE-001`, `SCN-001`) instead of raw database IDs

---

## 🧰 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 19, TypeScript 6, Vite 8 | Single-page investigation dashboard |
| **Styling** | Tailwind CSS 4 | Responsive design with dark mode support |
| **State Management** | Zustand | Lightweight client-side state |
| **Routing** | React Router 7 | Client-side page navigation |
| **Data Fetching** | TanStack React Query, Axios | Server state management and HTTP client |
| **Mapping** | Leaflet + React-Leaflet | Interactive geospatial visualization |
| **Backend** | FastAPI, Uvicorn | High-performance async REST API |
| **ORM** | SQLAlchemy 2, Alembic | Database models and migrations |
| **Validation** | Pydantic v2 | Request/response schema validation |
| **Scientific** | NumPy, SciPy | Numerical computation and optimization |
| **Database** | SQLite | Lightweight embedded database |
| **Containerization** | Docker, Docker Compose | Multi-service orchestration |
| **CI/CD** | GitHub Actions | Automated testing and linting |
| **Linting** | Ruff, Black (Python) · OxLint (TypeScript) | Code quality enforcement |

---

## 📁 Repository Structure

```text
Asterion/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/routers/     # REST API route handlers
│   │   ├── core/               # Application configuration
│   │   ├── database/           # Database session and base model registration
│   │   ├── exceptions/         # Global exception handlers
│   │   ├── middleware/         # Request logging and timing middleware
│   │   ├── models/             # SQLAlchemy ORM models (Case, Scenario, Tower)
│   │   ├── repositories/      # Data access layer
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic layer
│   │   └── shared/             # Shared utilities
│   ├── alembic/                # Database migration scripts
│   ├── tests/                  # Backend unit and integration tests
│   ├── main.py                 # Application entry point
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variable template
│
├── frontend/                   # React + TypeScript + Vite frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── cases/          # Case management components
│   │   │   ├── layout/         # Header, Sidebar shell
│   │   │   ├── scenarios/      # Scenario management components
│   │   │   └── ui/             # Button, Badge, Loading, Dialog, etc.
│   │   ├── hooks/              # Custom React hooks
│   │   ├── layouts/            # Dashboard layout shell
│   │   ├── lib/                # Utility helpers
│   │   ├── pages/              # Route-level page components
│   │   ├── services/           # Axios API client layer
│   │   ├── stores/             # Zustand state management
│   │   └── types/              # TypeScript type definitions
│   ├── package.json            # Node.js dependencies
│   └── .env.example            # Frontend environment template
│
├── scientific/                 # Standalone scientific computation engine
│   ├── config.py               # Frozen simulation & validation thresholds
│   ├── constants.py            # Physical, RF, geodesy, and cellular constants
│   ├── logger.py               # Standardized logging wrapper
│   ├── models/                 # Pydantic data models (Tower, Measurement, Scenario)
│   ├── validation/             # Domain validators (coordinates, RSSI, TA, RF)
│   ├── simulation/             # Signal propagation and noise generation (Week 2)
│   └── pipeline/               # Localization solver pipeline (Week 2)
│
├── datasets/                   # Sample and test datasets
│   └── sample/                 # Bangalore-area sample scenarios (JSON)
│
├── docker/                     # Dockerfiles for backend and frontend
├── docker-compose.yml          # Multi-service orchestration
├── scripts/                    # Utility and demo scripts
├── tests/                      # Cross-module integration tests
├── docs/                       # Project documentation
├── Plans/                      # Sprint planning documents
├── automation/                 # Sprint automation engine and configs
│
├── .github/workflows/ci.yml    # GitHub Actions CI pipeline
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── CODE_OF_CONDUCT.md          # Community standards
├── SECURITY.md                 # Vulnerability reporting policy
└── LICENSE                     # MIT License
```

---

## 📊 Current Development Status

> **Project Maturity:** MVP Development — Foundation Sprint (Week 1) Complete

> **Current Version:** `v0.1.0` — Foundation Release ([Changelog](CHANGELOG.md))

### Implementation Status Matrix

| Component | Status | Details |
|-----------|--------|---------|
| **Project Vision & Requirements** | ✅ Complete | Project charter, PRD, and SRS finalized |
| **Architecture Design** | ✅ Complete | HLD, system design, and API contracts frozen |
| **Backend Foundation** | ✅ Complete | FastAPI app with Repository-Service-Router pattern |
| **Case Management API** | ✅ Complete | Full CRUD endpoints for investigation cases |
| **Scenario Management API** | ✅ Complete | Full CRUD endpoints for localization scenarios |
| **Tower Management** | ✅ Complete | ORM model, migrations, and database storage |
| **Database Foundation** | ✅ Complete | SQLAlchemy models, Alembic migrations, SQLite |
| **Global Error Handling** | ✅ Complete | Centralized exception filters and JSON response wrappers |
| **Request Logging** | ✅ Complete | Duration-logging middleware for all API requests |
| **Frontend Dashboard** | ✅ Complete | Responsive shell with sidebar, header, dark mode |
| **Cases UI** | ✅ Complete | CRUD interface for case management |
| **Scenarios UI** | ✅ Complete | CRUD interface for scenario management |
| **Scientific Package** | ✅ Complete | Constants, config, models, validators — fully decoupled |
| **CI/CD Pipeline** | ✅ Complete | GitHub Actions running backend tests + frontend lint/build |
| **Docker Environment** | ✅ Complete | Docker Compose with health checks for both services |
| **Test Suite** | ✅ Complete | 323 passing tests across all modules |
| **Measurement Simulator** | 📅 Planned | Week 2 — RSSI signal generation and noise models |
| **Measurement Validation API** | 📅 Planned | Week 2 — REST endpoint for measurement validation |
| **Localization Engine (NLLS)** | 📅 Planned | Week 2 — Non-Linear Least Squares multilateration |
| **Tracking Engine (Kalman)** | 📅 Planned | Week 2 — 2D constant-velocity Kalman Filter |
| **Confidence Engine** | 📅 Planned | Week 2 — GDOP and covariance error ellipses |
| **Evidence Engine** | 📅 Planned | Week 2 — Audit trail and rejection matrices |
| **Pipeline Runner** | 📅 Planned | Week 2 — End-to-end orchestration |
| **Interactive Map** | 📅 Planned | Week 3 — Leaflet geospatial visualization |
| **Report Generator** | 📅 Planned | Week 3–4 — Investigation report export |
| **Performance Testing** | 📅 Planned | Week 4 — Benchmark and optimization |

### Screenshots

> 📸 **Screenshots will be added as the frontend matures.** The current dashboard includes a responsive dark-mode shell with sidebar navigation, case management CRUD, scenario management CRUD, and system status cards.

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Git** | Any recent version | Repository cloning |
| **Python** | 3.11+ | Backend and scientific engine |
| **Node.js** | 20+ | Frontend build tooling |
| **Docker Desktop** | Latest (optional) | Containerized deployment |

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/sriram21-09/Asterion.git
cd Asterion

# Start all services
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/v1/health |

### Option 2: Manual Setup

<details>
<summary><strong>Backend Setup</strong></summary>

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`.

</details>

<details>
<summary><strong>Frontend Setup</strong></summary>

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`.

</details>

### Environment Variables

<details>
<summary><strong>Backend (.env)</strong></summary>

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Asterion` | Application display name |
| `APP_VERSION` | `0.1.0` | Current version |
| `API_PREFIX` | `/api/v1` | API route prefix |
| `DATABASE_URL` | `sqlite:///./asterion.db` | SQLite database path |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `DEBUG` | `False` | Debug mode toggle |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

</details>

<details>
<summary><strong>Frontend (.env)</strong></summary>

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Backend API base URL |

</details>

---

## 📡 API Reference

The backend exposes a versioned REST API at `/api/v1`. Interactive documentation is available via Swagger UI at `/docs` when the server is running.

### Implemented Endpoints (v0.1.0)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service status and version |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/cases` | List all investigation cases |
| `POST` | `/api/v1/cases` | Create a new case |
| `GET` | `/api/v1/cases/{id}` | Get case by ID |
| `PUT` | `/api/v1/cases/{id}` | Update a case |
| `DELETE` | `/api/v1/cases/{id}` | Delete a case |
| `GET` | `/api/v1/scenarios` | List all scenarios |
| `POST` | `/api/v1/scenarios` | Create a new scenario |
| `GET` | `/api/v1/scenarios/{id}` | Get scenario by ID |
| `PUT` | `/api/v1/scenarios/{id}` | Update a scenario |
| `DELETE` | `/api/v1/scenarios/{id}` | Delete a scenario |
| `POST` | `/api/localize` | Weighted centroid localization (skeleton) |

### Planned Endpoints (Week 2)

| Method | Endpoint | Sprint |
|--------|----------|--------|
| `POST` | `/api/v1/simulation/generate` | Week 2 Day 1 |
| `POST` | `/api/v1/measurements/validate` | Week 2 Day 2 |
| `POST` | `/api/v1/localization/run` | Week 2 Day 3 |
| `POST` | `/api/v1/tracking/run` | Week 2 Day 4 |
| `POST` | `/api/v1/confidence/run` | Week 2 Day 5 |
| `GET` | `/api/v1/evidence/{case_id}` | Week 2 Day 5 |

> All API responses follow a standardized `APIResponse` wrapper with `success`, `data`, and `error` fields.

---

## 🔬 Scientific Engine

The `scientific/` package is a **standalone, decoupled Python package** for telecom localization computation. It has no dependency on FastAPI or the database and can be imported independently in notebooks, research scripts, or batch pipelines.

### Package Overview

| Module | Purpose |
|--------|---------|
| `constants.py` | Physical constants (speed of light, Boltzmann), WGS84 geodesy, Haversine distance, cellular frequency bands, RSSI quality tiers, timing advance resolution |
| `config.py` | Frozen dataclasses: `SimulationConfig`, `ValidationThresholds`, `EnvironmentConfig` with propagation presets for urban/suburban/rural/highway |
| `logger.py` | Idempotent console logging wrapper using standard library `logging` |
| `models/` | Pydantic v2 schemas: `Tower`, `Measurement`, `Scenario`, `ScenarioConfig`, `LocalizationResult`, `ConfidenceResult` |
| `validation/` | Domain validators: coordinate bounds, RSSI plausibility, TA↔RSSI consistency, referential integrity |

### Quick Example

```python
from scientific.models.tower import Tower
from scientific.models.measurement import Measurement
from scientific.models.scenario import Scenario
from scientific.validation.validators import ScenarioValidator

# Define a cell tower
tower = Tower(
    tower_id="T001",
    latitude=12.9716,
    longitude=77.5946,
    transmit_power_dbm=43.0,
    antenna_height_m=30.0,
    coverage_radius_m=1000.0,
    frequency_mhz=1800.0,
)

# Define a measurement
measurement = Measurement(
    tower_id="T001",
    timestamp="2026-07-12T10:00:00Z",
    rssi=-75.0,
    timing_advance=2,
)

# Create and validate a scenario
scenario = Scenario(
    scenario_id="S001",
    name="Bangalore Core Test",
    towers=[tower],
    measurements=[measurement],
)

validator = ScenarioValidator()
result = validator.validate(scenario)
print(f"Valid: {result.is_valid}")  # Valid: True
```

### Week 2 Scientific Pipeline (Planned)

```text
ScenarioConfig
     │
     ▼
RSSI Signal Generator ─── Log-distance path-loss model
     │
     ▼
Noise Model ────────────── AWGN + shadow fading
     │
     ▼
Measurement Synthesizer
     │
     ▼
Validation Engine ──────── Coordinate, RF, temporal checks
     │
     ▼
NLLS Multilateration ───── scipy.optimize.least_squares
     │
     ▼
Kalman Tracker ─────────── 2D constant-velocity state estimation
     │
     ▼
Confidence Engine ──────── GDOP + covariance error ellipses
     │
     ▼
Evidence Generator ─────── Audit trail and rejection matrices
```

For detailed documentation, see [`scientific/README.md`](scientific/README.md).

---

## 🧪 Testing

The project maintains a comprehensive test suite with **323 passing tests** across all modules.

### Test Distribution

| Test Module | Tests | Scope |
|-------------|-------|-------|
| `tests/test_day3_deliverables.py` | 85 | Pydantic models, scenarios, measurements, validators |
| `tests/test_day5_deliverables.py` | 86 | Scientific config, constants, logger |
| `tests/test_day4_deliverables.py` | 57 | ScenarioConfig, tower placement, propagation defaults |
| `tests/test_tower_model.py` | 43 | Tower model construction, boundaries, serialization |
| `tests/api/` | 22 | Case CRUD and Scenario CRUD endpoint tests |
| `tests/database/` | 12 | Database model validation (Cases, Scenarios, Towers) |
| `backend/tests/` | 18 | Core config, logging, exception handling, middleware |

### Running Tests

```bash
# Run all tests from the project root
cd backend
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_day3_deliverables.py
```

### Code Quality

```bash
# Python linting and formatting
ruff check .
black .

# Frontend linting and type checking
cd frontend
npm run lint
npm run build
```

---

## 🗺️ Development Roadmap

### Sprint 1 — Foundation ✅ Complete

> **Released as v0.1.0** · [View Changelog](CHANGELOG.md)

- [x] Repository setup with project documentation
- [x] Docker Compose environment with health checks
- [x] FastAPI backend with Repository-Service-Router pattern
- [x] Case Management CRUD (API + UI)
- [x] Scenario Management CRUD (API + UI)
- [x] Tower ORM model and database migrations
- [x] Scientific package: constants, config, models, validators
- [x] React dashboard shell with dark mode
- [x] Global exception handling and logging middleware
- [x] GitHub Actions CI pipeline
- [x] 323 automated tests passing

---

### Sprint 2 — Scientific Engine 📅 In Planning

> **Target:** v0.2.0 · 7-day sprint

- [ ] Measurement Simulator (RSSI generation, noise models)
- [ ] Measurement Validation REST API
- [ ] NLLS Multilateration Solver (scipy)
- [ ] 2D Kalman Filter Tracker
- [ ] GDOP Confidence Estimator
- [ ] Evidence Audit Engine
- [ ] End-to-End Pipeline Runner
- [ ] Frontend API client integration

---

### Sprint 3 — Visualization & Integration 📅 Planned

- [ ] Interactive Leaflet map with tower/device markers
- [ ] Evidence panel and confidence visualization
- [ ] Report generation system
- [ ] Full frontend integration with live backend data

---

### Sprint 4 — Testing & Release 📅 Planned

- [ ] Performance benchmarking (< 2s localization target)
- [ ] End-to-end integration tests
- [ ] Documentation finalization
- [ ] Demo preparation
- [ ] Version 1.0 release

---

## 🤝 Contributing

Contributions are welcome once the project foundation stabilizes. See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Start

```bash
# Fork and clone
git clone https://github.com/<your-username>/Asterion.git
cd Asterion

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes, run tests, commit
pytest
git commit -m "feat(module): description of change"

# Push and open a Pull Request
git push origin feature/your-feature-name
```

### Branch Naming Convention

| Prefix | Usage |
|--------|-------|
| `feature/` | New functionality |
| `bugfix/` | Bug fixes |
| `docs/` | Documentation updates |
| `refactor/` | Code restructuring |

### Coding Standards

**Python (Backend & Scientific)**
- PEP 8 with type hints
- Formatted with `black` and `ruff`
- Descriptive docstrings on public functions
- Max function length: ~40 lines

**TypeScript (Frontend)**
- Functional components with hooks
- Formatted with OxLint
- Clean state management with Zustand
- Semantic JSX

---

## 👥 Team

| Name | Role | GitHub |
|------|------|--------|
| **Sriram Kasukurthi** | Project Lead / Backend Lead | [@sriram21-09](https://github.com/sriram21-09) |
| **Chaitanya** | Scientific Engineer | [@Chaitanya0806](https://github.com/Chaitanya0806) |
| **Dinesh** | Frontend Lead | [@kdineshveera](https://github.com/kdineshveera) |

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

```
MIT License · Copyright (c) 2026 Kasukurthi Sriram
```

---

## 🙏 Acknowledgements

- **E-Rakshak 2026** — Cybersecurity and digital investigation hackathon
- **Surat City Police** — Hackathon organizing body
- **SVNIT Surat** — Academic partner
- **NEXUS** — Hackathon partner
- **OpenStreetMap** — Geospatial tile data
- The open-source communities behind FastAPI, React, NumPy, SciPy, SQLAlchemy, and Leaflet

---

<p align="center">
  <sub>Built with transparency in mind · Asterion v0.1.0</sub>
</p>
