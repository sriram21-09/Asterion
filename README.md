# Asterion

Explainable Telecom Localization & Investigation Support Platform built for E-Rakshak 2026. An open-source investigation and research workspace demonstrating scientific multilateration, Kalman tracking, confidence estimation, and evidence-based telecom localization using React, FastAPI, and Python.

## Project Structure

```text
Asterion/
├── .github/            # GitHub Actions CI/CD workflows
│   └── workflows/ci.yml # Continuous Integration checks
├── backend/            # FastAPI Python backend
│   ├── app/            # Application logic
│   │   └── main.py     # FastAPI entry point & routers
│   ├── data/           # Persistent SQLite database folder
│   ├── .env.example    # Backend environment template
│   └── requirements.txt# Backend Python dependencies
├── datasets/           # Sample and test datasets
│   └── sample/         # Consolidated sample datasets (JSON)
├── frontend/           # React + TypeScript + Vite frontend
│   ├── src/            # Frontend application source
│   │   ├── layouts/    # UI Shell (DashboardLayout)
│   │   ├── lib/        # Utility helpers (cn classname merger)
│   │   ├── pages/      # Skeleton pages (Dashboard, Cases, Scenarios, etc.)
│   │   ├── App.tsx     # Client-side router configuration
│   │   ├── main.tsx    # React application entrypoint
│   │   └── index.css   # Main stylesheet (Tailwind CSS v4)
│   ├── index.html      # Main HTML document
│   ├── tsconfig.json   # TypeScript configuration
│   ├── vite.config.ts  # Vite configuration (Tailwind v4, path aliases)
│   ├── .env.example    # Frontend environment template
│   └── package.json    # Frontend dependencies and scripts
├── scientific/         # Standalone scientific computation engine
│   ├── config.py       # Simulation, validation, environment configuration
│   ├── constants.py    # Physical, RF, geodesy constants & helpers
│   ├── logger.py       # Console logging helper
│   ├── models/         # Pydantic data models (Tower, Measurement, Scenario, etc.)
│   ├── validation/     # Domain validators (Measurement, Tower, Scenario)
│   ├── simulation/     # (Week 2) RSSI generation & noise models
│   └── pipeline/       # (Week 2) End-to-end localization pipeline
├── tests/              # pytest test suite (271 tests)
├── docker/             # Docker configuration files
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docs/               # System documentation & architectural reviews
├── Plans/              # Sprint plans & checklists
└── docker-compose.yml  # Multi-container Docker Compose setup with Healthchecks
```

---

## Getting Started

### Prerequisites

Ensure you have the following installed:
* [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
* [Node.js v20+](https://nodejs.org/)
* [Python 3.11+](https://www.python.org/)

---

### Local Development Setup

#### 1. Backend Setup
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```
3. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
5. Run the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
   The backend API will be available at [http://localhost:8000](http://localhost:8000). Swagger API documentation is accessible at [http://localhost:8000/docs](http://localhost:8000/docs).

#### 2. Frontend Setup
1. Navigate to the frontend folder:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at [http://localhost:3000](http://localhost:3000).

---

### Running with Docker Compose

To launch the entire platform stack in unified containers, run:

```bash
docker compose up --build
```

The services will configure automatically:
* **FastAPI Backend**: [http://localhost:8000](http://localhost:8000) (with automatic health check validating the DB connectivity)
* **Vite React Frontend**: [http://localhost:3000](http://localhost:3000) (routes traffic to backend endpoints)

---

## Continuous Integration (CI)

The repository uses GitHub Actions (`.github/workflows/ci.yml`) to validate code quality automatically on every pull request to `main`:
1. **Backend Checks**: Installs dependencies and runs unit tests using `pytest`.
2. **Frontend Checks**: Validates TypeScript compilation and lint checks using `oxlint`.
