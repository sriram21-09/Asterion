# 🛰️ Asterion

> **An open-source, explainable telecom localization and investigation support platform for demonstrating scientific multilateration, movement tracking, and evidence-driven geospatial analysis.**

<p align="center">

![Status](https://img.shields.io/badge/Status-MVP%20Development-orange)
![Architecture](https://img.shields.io/badge/Architecture-Frozen-success)
![License](https://img.shields.io/badge/License-MIT-blue)
![Hackathon](https://img.shields.io/badge/Hackathon-E--Rakshak%202026-red)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/Frontend-React-61DAFB)
![Database](https://img.shields.io/badge/Database-SQLite-003B57)
![Scientific](https://img.shields.io/badge/Scientific-SciPy%20%7C%20NumPy-blueviolet)

</p>

---

## 📌 Project Overview

Asterion is an open-source investigation support platform designed to demonstrate how multiple telecom tower measurements can be scientifically combined to estimate a device's probable location.

Rather than treating localization as a black box, Asterion emphasizes **explainability** by showing how measurements contribute to localization, how uncertainty is calculated, and why the final estimated position was produced.

The project is being developed for **E-Rakshak 2026** and is intended to serve as both a hackathon-ready MVP and a long-term open-source educational platform.

---

# 🚨 Problem Statement

Telecommunication records often provide investigators with measurements from multiple nearby cellular towers.

While individual tower measurements indicate only broad coverage areas, investigations frequently require a more precise estimate of a device's probable location.

Current challenges include:

- Large search areas
- Measurement noise
- Difficulty interpreting multiple tower measurements
- Limited visibility into localization confidence
- Lack of transparent evidence supporting estimated locations

Asterion addresses these challenges by combining multiple telecom measurements using scientifically grounded localization techniques while maintaining complete transparency throughout the investigation workflow.

---

# 💡 Solution Overview

Asterion is designed as an **evidence-first investigation platform**.

Instead of simply producing an estimated location, the platform provides a complete workflow that:

- Organizes investigation cases
- Generates or imports telecom measurements
- Validates measurement quality
- Estimates probable device locations using multilateration
- Tracks movement over time
- Quantifies localization uncertainty
- Explains every localization result
- Produces investigation-ready reports

The objective is to support investigators through transparent decision support rather than automated decision making.

---

# 🎯 Key Objectives

The Version 1.0 MVP focuses on:

- Build an end-to-end investigation workflow
- Demonstrate explainable telecom multilateration
- Visualize estimated device locations
- Perform movement tracking
- Estimate localization confidence
- Generate investigation reports
- Deliver a modular and maintainable open-source platform
- Showcase professional software engineering practices

---

# 🏗️ Architecture Overview

Asterion follows a **Layered Modular Monolith Architecture**, allowing independent development of core subsystems while keeping deployment simple.

```text
                        ASTERION PLATFORM

+--------------------------------------------------------------+
|                     React Investigation UI                   |
+--------------------------▲-----------------------------------+
                           │ REST API
+--------------------------▼-----------------------------------+
|                     FastAPI Backend                          |
|                                                              |
|  +----------------+  +----------------+  +----------------+  |
|  | Case Manager   |  | Import Service |  | Report Service |  |
|  +----------------+  +----------------+  +----------------+  |
|                                                              |
|  +----------------+  +----------------+  +----------------+  |
|  | Validation     |  | Evidence       |  | API Layer      |  |
|  +----------------+  +----------------+  +----------------+  |
+--------------------------▲-----------------------------------+
                           │
+--------------------------▼-----------------------------------+
|              Scientific Computation Core                     |
|                                                              |
|  Simulator → NLLS → Kalman → Confidence → Evidence          |
+--------------------------▲-----------------------------------+
                           │
+--------------------------▼-----------------------------------+
|                     SQLite Database                          |
+--------------------------------------------------------------+
```

---

# 🧰 Technology Stack

| Layer | Technology |
|--------|------------|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Scientific Computing | NumPy, SciPy, FilterPy |
| Database | SQLite |
| Mapping | Leaflet + OpenStreetMap |
| DevOps | Docker, Docker Compose, GitHub Actions |

---

# 📁 Repository Structure

```text
Asterion/

├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── localization/
│   │   ├── simulation/
│   │   ├── tracking/
│   │   ├── confidence/
│   │   ├── reporting/
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── main.py
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── store/
│   │   └── App.tsx
│
├── datasets/
├── docker/
├── docs/
├── scripts/
├── .github/
├── README.md
└── docker-compose.yml
```

---

# 🚧 Current Development Status

> **Project Maturity:** Architecture Complete → MVP Development (Foundation Sprint)

| Component | Status | Notes |
|-----------|--------|-------|
| Project Vision | ✅ Complete | Project Charter finalized |
| Requirements | ✅ Complete | PRD and SRS finalized |
| Architecture | ✅ Complete | HLD, SDMS and API design frozen |
| Backend Foundation | 🚧 In Progress | Week 1 Sprint |
| Frontend Foundation | 🚧 In Progress | Dashboard skeleton under development |
| Database | 🚧 In Progress | Initial schema and migrations |
| Scientific Engine | 📅 Planned | Week 2 Sprint |
| Visualization | 📅 Planned | Week 3 Sprint |
| Report Generator | 📅 Planned | Week 3–4 Sprint |
| Testing | 📅 Planned | Final Sprint |
| Deployment | 📅 Planned | Docker Compose MVP |

> **Note:** The modules listed below represent the planned Version 1.0 architecture and should not be interpreted as fully implemented functionality.

---

# 🔄 Planned MVP Workflow

```text
Create Case
      │
      ▼
Load Scenario
      │
      ▼
Generate / Import Measurements
      │
      ▼
Validate Measurements
      │
      ▼
Estimate Device Location
      │
      ▼
Track Movement
      │
      ▼
Analyze Confidence
      │
      ▼
Review Evidence
      │
      ▼
Export Report
```

---

# 🧩 Planned Core Modules (Version 1.0)

The following modules define the planned architecture for Version 1.0:

- 📁 Case Manager
- 📂 Scenario Manager
- 📡 Measurement Simulator
- ✅ Measurement Validation Engine
- 📍 Localization Engine (NLLS)
- 📈 Tracking Engine (Kalman Filter)
- 🎯 Confidence Engine
- 🧾 Evidence Engine
- 🗺️ Visualization Engine
- 📄 Report Generator

---

# 🚀 Getting Started

> **Current Status:** Project foundation is under active development.

## Prerequisites

Install the following software:

- Git
- Python 3.12+
- Node.js 20+
- Docker Desktop (recommended)
- SQLite (optional for inspection)

---

## Clone the Repository

```bash
git clone https://github.com/<your-username>/Asterion.git
cd Asterion
```

---

## Backend

Backend setup instructions will be documented as the FastAPI foundation is completed.

---

## Frontend

Frontend setup instructions will be added during the Foundation Sprint.

---

## Docker

Docker Compose support is planned as part of the MVP foundation.

---

# 🛣️ Development Roadmap

## Sprint 1 — Foundation

- Repository Setup
- Docker Environment
- Case Management CRUD
- Database Foundation
- Dashboard Skeleton

---

## Sprint 2 — Scientific Engine

- Measurement Validation
- NLLS Localization
- Kalman Tracking
- Confidence Estimation

---

## Sprint 3 — Visualization & Integration

- Interactive Map
- Evidence Panel
- Report Generation
- Frontend Integration

---

## Sprint 4 — Testing & Release

- Testing
- Performance Validation
- Documentation
- Demo Preparation
- Version 1.0 Release

---

# 🤝 Contributing

Contributions will be welcomed once the project foundation is stabilized.

Development workflow:

1. Fork the repository
2. Create a feature branch
3. Follow project coding standards
4. Submit a Pull Request

### Branch Naming

```text
feature/<feature-name>

bugfix/<issue-name>

docs/<documentation>

refactor/<module-name>
```

### Coding Standards

- Type-safe code
- Modular architecture
- Single Responsibility Principle
- Clear commit messages
- Document public APIs
- Write tests where applicable

---

# 📚 Documentation

Project documentation is organized under the `docs/` directory.

Planned documentation includes:

- 🏗️ Architecture
- 🔌 API Specification
- 🗄️ Database Design
- 📅 Sprint Plans
- 📘 Engineering Guide

---

