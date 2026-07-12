# 🏁 Week 1 Sprint Review & Database Validation Demo Guide

This guide outlines the demo script, verification steps, and key deliverables for the **Asterion Week 1 – Foundation Sprint** review.

---

## 1. Sprint Review Agenda

1. **Architecture & Project Layout Overview**: Show the decoupled structure of the scientific engine (`scientific/`) and the FastAPI backend + React frontend.
2. **Database Integrity & Validation Demo**: Run the validation script showing SQL constraints, model rules, and model relationship cascade behaviors.
3. **End-to-End User Flow**: Demonstrate Case Creation, Scenario association, navigation, and state rendering in the browser.
4. **Code Quality & Testing Metrics**: Show passing test suites and automated check validation.

---

## 2. Key Accomplishments (v0.1.0 Foundation Release)

- **Decoupled Scientific Package**: Established the core domain classes for Towers, Measurements, and Scenarios with standalone physical validators.
- **FastAPI Backend (Repository-Service-Router)**:
  - SQLite database integration.
  - Automatic Alembic migrations (`initial_migration`, `add_scenario_id_to_case`, and the new `add_towers_table`).
  - Standardized JSON responses and global exception filters.
  - Console logging middleware tracing request durations.
- **Vite React Frontend**:
  - Dashboard layout, responsive side navigation, and dark/light theme toggle.
  - CRUD panels for Cases and Scenarios integrated with backend endpoints via Axios and TanStack Query.
  - UI state feedback (Sonner notification toasts, skeleton screens, error boundaries).
- **Docker Compose Integration**: Single-command container deployment for frontend, backend, and health monitoring.
- **Unified Test Suite**: 323 passing unit and integration tests.

---

## 3. Database Validation Demo

The database schema and constraint behaviors are validated by the demo script: `scripts/db_demo.py`. 

### Running the Demo
To execute the database validation suite:
```bash
python scripts/db_demo.py
```

### What is Validated
1. **Schema Creation**: Instantiates the SQLite schema using the actual ORM models (`Case`, `Scenario`, `Tower`).
2. **Model Persistence**: Verifies that valid Case, Scenario, and Tower objects can be inserted and receive auto-populated fields (IDs, timestamps).
3. **Database Constraints**:
   - Attempts to insert a **Case without a title** -> Blocked by database `IntegrityError` (NOT NULL constraint).
   - Attempts to insert a **Tower without a name** -> Blocked by database `IntegrityError` (NOT NULL constraint).
4. **Relationship Integrity (Cascading behavior)**:
   - Associates a Case to a Scenario.
   - Deletes the Scenario record.
   - Verifies the Case's `scenario_id` is automatically set to `NULL` (`ondelete="SET NULL"` constraint) rather than deleting the case or throwing a foreign key violation.

---

## 4. End-to-End Application Demo (Docker-first)

Follow these steps to demonstrate the unified platform interface:

### 1. Launch the Stack
```bash
docker compose up --build
```

### 2. Verify Backend Docs (Swagger)
- Open [http://localhost:8000/docs](http://localhost:8000/docs).
- Show standard endpoints for `/api/v1/cases` and `/api/v1/scenarios`.
- Show that request/response schemas correspond to standard wrappers (`{"success": true, "data": ...}`).

### 3. Verify Frontend Dashboard
- Open [http://localhost:3000](http://localhost:3000).
- **Navigation**: Click between **Dashboard**, **Cases**, **Scenarios**, and **Settings**.
- **Case CRUD**: Create a case, see success toast, see case appear in list, then delete it.
- **Scenario CRUD**: Create a scenario and view the card.
- **Theme persistence**: Toggle dark mode, refresh, and verify it stays in dark mode.

---

## 5. Engineering Quality & Testing Status

Verify the quality gates pass successfully before checking out of Week 1:

```bash
# Run backend tests
backend\.venv\Scripts\pytest

# Run code styling formats
backend\.venv\Scripts\ruff check scientific --fix
backend\.venv\Scripts\black --check scientific

# Run frontend lint and build
cd frontend
npm run lint
npm run build
```

All 323 tests across the project must return a green status:
- Decoupled Scientific components: **271 tests**
- Database ORM validation: **12 tests**
- Backend Routers and Middleware: **22 tests**
- Core infrastructure and Exception filters: **18 tests**
