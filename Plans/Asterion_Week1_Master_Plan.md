# 📘 Asterion Engineering Handbook
## Week 1 – Foundation Sprint — Master Plan (Revised)

**Version:** 1.1 (Revised per CTO Review)
**Sprint:** Week 1 – Foundation Sprint
**Team:** Sriram (Backend Lead / Integration Lead), Chaitanya (Scientific Engineer), Dinesh (Frontend Lead)

> **Revision note:** This version incorporates the CTO review refinements: rebalanced workload, trimmed documentation scope, added time estimates, a testing strategy, an API contract freeze policy, a daily stand-up, documentation ownership, and a deferred `Towers` model. Structural elements the review said to keep unchanged (sprint sequence, architecture, tech stack, Git workflow, Docker-first approach, daily acceptance criteria, integration gates, role separation) are preserved as-is.

---

## Table of Contents

1. [Sprint Overview](#sprint-overview)
2. [Team Standards & Ways of Working](#team-standards--ways-of-working)
3. [Day 2 — Database & Dashboard Foundation](#day-2--database--dashboard-foundation)
4. [Day 3 — API Foundation & Case Management](#day-3--api-foundation--case-management)
5. [Day 4 — Scenario Management & Application Workflow](#day-4--scenario-management--application-workflow)
6. [Day 5 — Project Infrastructure, Logging & Production Readiness](#day-5--project-infrastructure-logging--production-readiness)
7. [Day 6 — Integration Day](#day-6--integration-day)
8. [Day 7 — Review & Stabilization](#day-7--review--stabilization)
9. [Foundation Release](#foundation-release)
10. [Week 2 Readiness Gate](#week-2-readiness-gate)
11. [Sprint Summary & CTO Final Assessment](#sprint-summary--cto-final-assessment)

---

## Sprint Overview

Week 1 is the **Foundation Sprint** for Asterion. The architecture builds up day by day:

```
Day 1: Environment
   ↓
Day 2: Database (Cases, Scenarios)
   ↓
Day 3: Case CRUD
   ↓
Day 4: Scenario CRUD
   ↓
Day 5: Infrastructure, Logging & Quality
   ↓
Day 6: Integration (+ Towers model)
   ↓
Day 7: Stabilization & Release
```

By the end of the sprint, the team ships **Asterion v0.1 – Foundation Release**, and is authorized to begin **Week 2 – Scientific Engine Sprint**.

### Dependency Graph

Tasks flow strictly downward — no layer should be started before the one above it is working:

```
Database
   ↓
ORM Models
   ↓
Repository
   ↓
Service
   ↓
API (Router)
   ↓
Frontend Integration
```

Scenario and Case features each move through this full chain independently, in a **vertical slice** rather than building all backend first, then all frontend.

### Revised Workload Balance

The original plan concentrated too much of Chaitanya's time in documentation (~15–20% of total workload). This revision shifts some backend testing and shared validation work into the Scientific track, for a more even split and better Week 2 preparation:

| Developer | Focus | Adjusted Share |
|---|---|---|
| Sriram | Backend, Integration, DevOps | ~40% |
| Dinesh | Frontend, UI, API integration | ~35% |
| Chaitanya | Scientific data models (trimmed docs) + backend test/validation support | ~25% |

---

## Team Standards & Ways of Working

These standards apply across all seven days and are **new for this revision**.

### Daily Stand-up (15 minutes, every morning)

Fixed agenda:
1. What did you finish yesterday?
2. What will you do today?
3. Are you blocked?
4. Do you need another developer?

Keep it short — this is a sync, not a design meeting.

### Coding Standards

- **Max function length:** ~40 lines (split if longer)
- **Max file length:** ~300 lines (split into modules if longer)
- **Naming conventions:** `snake_case` for Python, `camelCase` for TypeScript/JS, `PascalCase` for React components and Pydantic/ORM classes
- **Import order:** standard library → third-party → local/project imports, each group alphabetized

### Testing Strategy

| Item | Standard |
|---|---|
| Backend framework | `pytest` |
| Frontend framework | `vitest` (or project-approved equivalent) |
| Minimum coverage (Week 1) | Core CRUD paths + error paths — no formal % target yet, but every endpoint needs at least one happy-path and one failure-path test |
| Who writes tests | Feature owner writes tests for their own feature before opening a PR |
| Test naming | `test_<unit>_<condition>_<expected_result>` (e.g. `test_create_case_missing_title_returns_422`) |
| Test directory layout | Backend: `tests/api/`, `tests/database/`; Frontend: colocated `*.test.tsx` or a `__tests__/` folder per component |

### API Contract Freeze

**After Day 3, the `/api/v1` contract (Case endpoints) is frozen for Week 1** — only bug fixes are allowed, no breaking changes to request/response shapes. The same freeze applies to Scenario endpoints after Day 4. This keeps frontend and backend synchronized and prevents late-week churn.

### Issue Priority Levels

| Priority | Meaning | Response |
|---|---|---|
| P0 | Breaks the build or blocks the whole team | Fix immediately, drop other work |
| P1 | Breaks a feature or a demo path | Fix same day |
| P2 | Non-blocking bug or missing polish | Fix before Day 7 |
| P3 | Nice-to-have / cosmetic | Backlog for Week 2+ |

### Documentation Ownership

Shared ownership becomes no one's responsibility — each document has one primary owner:

| Document | Owner |
|---|---|
| README | Sriram |
| API Docs (Swagger) | Sriram |
| Scientific Docs | Chaitanya |
| UI Docs | Dinesh |
| CHANGELOG | Sriram |

### Branch Hygiene

After every merge into `develop`, delete the merged feature branch. Keep the repository tidy — no stale branches accumulating over the week.

### Merge Order (Revised)

The original merge order was `Scientific → Frontend → Backend`. Since the frontend depends on backend APIs, the corrected order is:

```
Scientific → Backend → Frontend → Integration/Smoke Test
```

This corrected order applies to all integration workflows for the rest of this document.

---

## Day 2 — Database & Dashboard Foundation

**Theme:** Database Foundation & Frontend Framework

### Objectives
The goal of Day 2 is to establish the persistent data layer and complete the frontend application framework. No business logic yet.

By the end of Day 2:
- Database is fully configured
- Alembic works
- First database models exist (Cases and Scenarios only — see revision note below)
- Dashboard layout is complete
- Backend communicates with SQLite
- Frontend structure is ready for API integration

> **Revision note:** The original plan created a `Towers` model on Day 2, but Towers are unused until Week 2. To reduce unnecessary Week 1 work and testing surface, **Towers is deferred to Day 6**. Day 2 now only creates `Cases` and `Scenarios`.

### Architecture Progress
```
Day 1: Repository → Environment → Docker → Health API → Frontend Skeleton
Day 2: Database → Models (Cases, Scenarios) → Migrations → Dashboard Framework
```

### Deliverables

**Backend**
- SQLAlchemy configured
- Alembic initialized
- SQLite connected
- Base Model
- Cases Model
- Scenarios Model

**Frontend**
- Complete Dashboard Layout
- Responsive Sidebar
- Header
- Theme
- Navigation
- Placeholder Pages

**Scientific**
- Scientific data models
- Dataset schema
- Measurement documentation

### Dependencies (Pre-Day 2 Check)
Before beginning Day 2, verify:
```
docker compose up → Backend Starts → Frontend Starts → Swagger Opens
```
If any step fails, fix Day 1 before continuing.

---

### 👨‍💻 Sriram — Backend Lead

| Task | Description | Est. Time |
|---|---|---|
| 1. Database Package | Create `backend/app/database/` with `base.py`, `session.py`, `engine.py` to centralize database management | 30 min |
| 2. Database Configuration | Configure SQLite, environment variables, connection string, session factory. Requirements: singleton engine, SQLAlchemy 2.x, typed session | 45 min |
| 3. Alembic Initialization | Create `alembic/`, `versions/`, `env.py`; configure SQLAlchemy metadata and migration path; verify `alembic revision --autogenerate` and `alembic upgrade head` work | 45 min |
| 4. Base ORM Model | Create `Base` model with common fields: `id`, `created_at`, `updated_at`, shared by every table | 20 min |
| 5. Create Models | **Cases** (id, title, description, status, created_at, updated_at); **Scenarios** (id, name, description, created_at) | 40 min |
| 6. Pydantic Schemas | Create `CaseCreate`, `CaseResponse`, `ScenarioCreate` | 30 min |
| 7. Database Test | Create `tests/database/`; verify database connection, table creation, migration success | 30 min |

**Deliverables:** Database connected · Migrations working · ORM ready
**Estimated total:** ~4 hours

### 👨‍🔬 Chaitanya — Scientific Engineer

**Goal:** Design scientific data structures. No algorithms. (Documentation scope trimmed ~35% versus the original plan — keep each doc to essentials.)

| Task | Description | Est. Time |
|---|---|---|
| 1. Scientific Models | Create `tower.py`, `measurement.py`, `scenario.py`, `result.py` inside `scientific/models/` | 40 min |
| 2. Dataset Schema | Define Tower, Measurement, Scenario, LocalizationResult, ConfidenceResult — concise field lists, not prose essays | 30 min |
| 3. Measurement Format | Document required fields with one example: `{"tower_id":"T001","timestamp":"ISO8601","rssi":-72}` — no implementation | 15 min |
| 4. Folder Preparation | Create `simulation/`, `validation/`, `pipeline/` — structure only | 10 min |
| 5. Backend Test Support (new) | Pair with Sriram to write 2–3 database tests for Cases/Scenarios models | 45 min |

**Deliverables:** Scientific architecture frozen · Contributed to backend test coverage
**Estimated total:** ~2.3 hours (freed-up time reallocated to shared testing support)

### 👨‍💻 Dinesh — Frontend Lead

| Task | Description | Est. Time |
|---|---|---|
| 1. Complete Sidebar | Dashboard, Cases, Scenarios, Reports, Settings | 30 min |
| 2. Header | Responsive; includes Project Name, Navigation, Theme Switch, User Placeholder (static only) | 30 min |
| 3. Main Layout | Finalize Sidebar → Header → Content Area | 30 min |
| 4. Pages | Dashboard, Cases, Scenarios, Reports, Settings, 404 — each with placeholder content | 45 min |
| 5. Install Leaflet | No maps yet — only verify installation | 10 min |
| 6. State Management | Initialize Zustand stores: Theme, Navigation, Application Settings | 30 min |
| 7. TanStack Query | Initialize Provider and Query Client — no API integration yet | 20 min |

**Deliverables:** Complete frontend framework.
**Estimated total:** ~3.25 hours

### Repository Status (Expected)
```
backend/  → database/, models/, schemas/
frontend/ → pages/, layouts/, stores/, hooks/
```

### Git Commits

**Sriram**
- `feat(database): initialize SQLAlchemy`
- `feat(database): configure Alembic`
- `feat(models): add initial ORM models`

**Chaitanya**
- `feat(scientific): create data models`
- `docs(scientific): define dataset schema`
- `test(database): add case/scenario model tests`

**Dinesh**
- `feat(ui): complete dashboard layout`
- `feat(state): initialize Zustand`
- `feat(query): configure TanStack Query`

### Integration Plan (Revised Merge Order)
```
Scientific → Backend → Frontend → Database Migration → Smoke Test
```

### Smoke Tests

**Backend:** SQLite connects · Alembic works · Tables created
**Frontend:** Navigation works · Sidebar responsive · Pages render
**Scientific:** Models documented · Structure committed

### Expected Repository
```
backend/     → database/, models/, schemas/
frontend/    → layouts/, pages/, stores/
scientific/  → models/, simulation/, validation/
```

### End-of-Day Review Questions
- Can migrations run?
- Can database create tables?
- Does dashboard load?
- Can navigation switch pages?
- Does Docker still work?
- Is documentation updated?

### Acceptance Criteria

| Requirement | Status |
|---|---|
| SQLite connected | ✅ |
| SQLAlchemy configured | ✅ |
| Alembic initialized | ✅ |
| ORM models created (Cases, Scenarios) | ✅ |
| Pydantic schemas created | ✅ |
| Dashboard layout completed | ✅ |
| Sidebar responsive | ✅ |
| Zustand initialized | ✅ |
| TanStack Query configured | ✅ |
| Scientific data models documented | ✅ |
| Docker passes smoke test | ✅ |
| PRs merged into develop, branches deleted | ✅ |

### Day 2 Exit Gate
The team may proceed to Day 3 only if:
1. Database migrations execute successfully from a clean clone.
2. The backend starts with the database connected.
3. The frontend renders the full application shell (sidebar, header, pages).
4. The scientific package contains documented data models and folder structure.
5. Docker Compose still launches the complete stack without manual intervention.
6. CI remains green after all merges.

---

## Day 3 — API Foundation & Case Management

**Theme:** API Foundation & First End-to-End Feature

### Objectives
Day 3 marks the first vertical slice of Asterion — one fully functional workflow instead of isolated backend/frontend features:
```
User → Frontend Form → REST API → Service Layer → Database → Response → Frontend Update
```

### Architecture Progress
```
Day 1: Environment → Day 2: Database → Day 3: REST API → Service Layer → Case CRUD → Frontend Integration
```

### Deliverables

**Backend:** API Versioning · Repository Layer · Service Layer · Case CRUD APIs · Swagger Documentation
**Frontend:** Cases Page · Case List · Create Case Form · API Integration · Notifications
**Scientific:** Validation Interface · API Contract Review · Data Flow Documentation

### Feature Scope
Only implement:
- `GET /health`
- `POST /cases`
- `GET /cases`
- `DELETE /cases`

Do **NOT** implement: Update Case · Scenario CRUD · Localization · Reports

> **Note on repository pattern:** The `Router → Service → Repository → ORM` layering is kept as-is for this revision because it matches the team's learning goals. If the schedule slips, the **Repository** layer is the first thing to simplify (services can call the ORM directly as a fallback).

---

### 👨‍💻 Sriram — Backend Lead

| Task | Description | Est. Time |
|---|---|---|
| 1. API Folder Structure | `backend/app/api/`, `api/v1/`, `routers/`, `services/`, `repositories/` | 20 min |
| 2. Repository Layer | Implement `CaseRepository`: create, get, list, delete case. Communicates only with SQLAlchemy — no business logic | 45 min |
| 3. Service Layer | Implement `CaseService`: validate requests, call repository, handle errors, return response models. No SQL inside services | 45 min |
| 4. API Router | Create `cases.py` with `GET /health`, `POST /cases`, `GET /cases`, `DELETE /cases/{id}` | 40 min |
| 5. Swagger Documentation | Every endpoint must include summary, description, tags, response models, error responses — presentation-ready | 30 min |
| 6. Global Exception Handling | Create `exception_handlers.py`; standardize error format: `{"success": false, "error": {"code": "...", "message": "..."}}` | 30 min |
| 7. Logging | Every request logs endpoint, method, status, duration | 20 min |
| 8. Unit Tests | Create `tests/api/`; test create/list/delete case | 40 min |

**Deliverables:** Working REST API · Swagger complete · Repository & Service layers implemented
**Estimated total:** ~4.5 hours

### 👨‍🔬 Chaitanya — Scientific Engineer

Day 3 continues scientific preparation, trimmed and rebalanced with shared validation work.

| Task | Description | Est. Time |
|---|---|---|
| 1. Validation Package | Create `scientific/validation/validators.py` — interfaces only | 20 min |
| 2. Measurement Interface | Document expected Measurement, Tower, Scenario objects — no algorithms, keep to a single concise reference | 20 min |
| 3. Scientific API Contracts | Review future APIs (`POST /simulation/generate`, `POST /measurements/validate`, `POST /localization/run`) for consistency with backend conventions | 20 min |
| 4. Dataset Sample (trimmed) | Create **one** consolidated `datasets/sample/sample_dataset.json` covering towers, measurements, and scenarios — replaces three separate sample files | 20 min |
| 5. Shared Validation Helpers (new) | Write basic input-validation utility functions (e.g. RSSI range check, coordinate bounds check) in `backend/app/shared/validation.py` for reuse by both backend and scientific code | 45 min |

**Deliverables:** Scientific interfaces documented · Shared validation helpers contributed
**Estimated total:** ~2 hours

### 👨‍💻 Dinesh — Frontend Lead

| Task | Description | Est. Time |
|---|---|---|
| 1. Cases Page | Create `pages/Cases.tsx` | 20 min |
| 2. Components | `CaseCard`, `CaseForm`, `CaseTable`, `EmptyState` | 45 min |
| 3. Axios Client | Create `services/apiClient.ts` — base URL, timeout, error interceptor | 30 min |
| 4. Case Service | Create `caseService.ts`: `getCases()`, `createCase()`, `deleteCase()` | 30 min |
| 5. TanStack Query | `useCases()`, `useCreateCase()`, `useDeleteCase()` | 30 min |
| 6. Case Creation Form | Fields: Title, Description — required-field validation only | 25 min |
| 7. Toast Notifications | Success, Error, Loading | 20 min |
| 8. Loading States | Spinner, Empty State, Error State | 25 min |

**Deliverables:** Complete Case Management UI.
**Estimated total:** ~3.75 hours

### Repository Structure (Expected)
```
backend/  → api/, repositories/, services/, shared/
frontend/ → pages/, components/, services/, hooks/
```

### Git Commits

**Sriram**
- `feat(api): implement case CRUD endpoints`
- `feat(service): add case service layer`
- `test(api): add case endpoint tests`

**Chaitanya**
- `docs(scientific): define validation pipeline`
- `feat(dataset): add consolidated sample dataset`
- `feat(shared): add shared validation helpers`

**Dinesh**
- `feat(cases): create case management page`
- `feat(api): integrate backend case service`
- `feat(ui): add loading and notification states`

### Integration Workflow (Revised Merge Order)
```
Scientific → Backend → Frontend → End-to-End Test
```

### End-to-End Test Scenario
```
Open Dashboard → Navigate to Cases → Create Case → Submit →
Backend Stores → Database Updated → Frontend Refreshes → Case Appears
```

### Smoke Test Checklist
**Backend:** FastAPI starts · Swagger available · CRUD endpoints work
**Frontend:** Cases page loads · API requests succeed · Errors handled
**Database:** Case inserted · Case listed · Case deleted
**Docker:** Still builds successfully

### Acceptance Criteria

| Requirement | Status |
|---|---|
| Repository layer implemented | ✅ |
| Service layer implemented | ✅ |
| Health endpoint working | ✅ |
| POST /cases working | ✅ |
| GET /cases working | ✅ |
| DELETE /cases working | ✅ |
| Swagger updated | ✅ |
| Cases page completed | ✅ |
| Axios configured | ✅ |
| TanStack Query integrated | ✅ |
| Notifications implemented | ✅ |
| Unit tests passing | ✅ |
| Docker smoke test passing | ✅ |
| PRs merged into develop, branches deleted | ✅ |

### Day 3 Exit Gate
Before moving to Day 4, all of the following must be true:
1. The complete Case Management workflow works from the browser.
2. Backend APIs are documented in Swagger.
3. The frontend communicates successfully with the backend using the shared API client.
4. Case records persist in SQLite.
5. Unit tests pass.
6. Docker Compose launches the integrated application.
7. CI passes after merging to develop.

> ### 🔒 API Contract Freeze (effective from this point)
> As of the end of Day 3, the `/api/v1` Case endpoints (`GET /health`, `POST /cases`, `GET /cases`, `DELETE /cases/{id}`) are **frozen** — request/response shapes cannot change except for bug fixes. Any change requires a documented exception agreed by Sriram and Dinesh.

### 📊 Week 1 Progress After Day 3

| Area | Progress |
|---|---|
| Repository & DevOps | 100% |
| Docker Environment | 100% |
| Backend Foundation | 90% |
| Database Foundation | 100% |
| Frontend Foundation | 80% |
| Case Management | 100% |
| Scenario Management | 0% |
| Scientific Foundation | 40% |
| CI/CD | 90% |
| Documentation | 60% |

**Overall Week 1 Progress: ~50% Complete**

---

## Day 4 — Scenario Management & Application Workflow

**Theme:** Scenario Management & Second End-to-End Feature

### Objectives
Day 4 extends the platform with Scenario Management, the second complete feature after Case Management, connecting the application workflow:
```
Case → Scenario → (Week 2) Simulation → Localization
```

At the end of Day 4, users should be able to:
- Create a Case
- Create a Scenario
- View Scenarios
- Delete Scenarios
- Associate Scenarios with Cases (basic relationship only)

No simulation or localization is implemented yet.

### Architecture Progress
```
Day 1: Environment → Day 2: Database → Day 3: Case CRUD → Day 4: Scenario CRUD → Application Workflow
```

### Deliverables

**Backend:** Scenario Model · Scenario Repository · Scenario Service · Scenario CRUD API
**Frontend:** Scenario Page · Scenario Form · Scenario List · Navigation Updates
**Scientific:** Scenario Configuration Schema · Tower Configuration Structure (documentation only — `Towers` implementation itself waits until Day 6)

### APIs to Implement
- `POST /scenarios`
- `GET /scenarios`
- `DELETE /scenarios/{id}`

Do not implement: Scenario Update · Scenario Execution · Measurement Generation

---

### 👨‍💻 Sriram — Backend Lead

| Task | Description | Est. Time |
|---|---|---|
| 1. Scenario ORM Model | `backend/app/models/scenario.py` — fields: id, name, description, created_at, updated_at | 20 min |
| 2. Repository | `ScenarioRepository`: `create()`, `get()`, `list()`, `delete()` | 30 min |
| 3. Service | `ScenarioService`: input validation, business rules, error handling | 30 min |
| 4. Scenario Router | `api/v1/scenarios.py`: `POST /scenarios`, `GET /scenarios`, `DELETE /scenarios/{id}` | 30 min |
| 5. Swagger Documentation | Summary, description, example requests, example responses | 25 min |
| 6. Relationship Preparation | Prepare foreign key relationship Case → Scenario (schema only, no workflow) | 20 min |
| 7. Unit Tests | Create/list/delete scenario tests | 30 min |

**Deliverables:** Scenario CRUD working · Swagger updated · Tests passing
**Estimated total:** ~3 hours

### 👨‍🔬 Chaitanya — Scientific Engineer

Still no algorithm implementation. Focus: designing future simulation inputs — trimmed to essentials.

| Task | Description | Est. Time |
|---|---|---|
| 1. Scenario Configuration Model | `scenario_config.py` documenting Scenario Name → Tower Layout → Noise Level → Measurement Count → Expected Device Position | 25 min |
| 2. Tower Schema (documentation only) | Documentation for tower_id, latitude, longitude, sector, coverage_radius — implementation deferred to Day 6 | 15 min |
| 3. Scenario Example (trimmed) | Create **one** well-structured `datasets/sample/scenario_example.json` — replaces the original three separate files (urban/highway/campus) | 20 min |
| 4. Backend Test Support (new) | Pair with Sriram on 1–2 scenario repository/service tests | 30 min |

**Deliverables:** Scientific input architecture completed · Contributed to scenario test coverage
**Estimated total:** ~1.5 hours

### 👨‍💻 Dinesh — Frontend Lead

| Task | Description | Est. Time |
|---|---|---|
| 1. Scenario Page | `pages/Scenarios.tsx` | 20 min |
| 2. Scenario Components | `ScenarioCard`, `ScenarioTable`, `ScenarioForm`, `EmptyState` | 40 min |
| 3. Scenario Service | `services/scenarioService.ts`: `createScenario()`, `getScenarios()`, `deleteScenario()` | 25 min |
| 4. TanStack Query Hooks | `useScenarios()`, `useCreateScenario()`, `useDeleteScenario()` | 25 min |
| 5. Scenario Form | Fields: Name, Description — required fields only | 20 min |
| 6. Dashboard Update (trimmed) | Add cards: Cases, Scenarios — keep placeholder stats minimal, skip elaborate placeholder statistics | 20 min |
| 7. Navigation Polish | Highlight active route, improve responsive behavior | 20 min |

**Deliverables:** Scenario Management UI completed.
**Estimated total:** ~2.5 hours

### Repository Structure (Expected)
```
backend/
  models/scenario.py
  repositories/scenario_repository.py
  services/scenario_service.py
  api/v1/scenarios.py

frontend/
  pages/Scenarios.tsx
  components/ScenarioCard.tsx, ScenarioForm.tsx, ScenarioTable.tsx
  services/scenarioService.ts
```

### Git Commits

**Sriram**
- `feat(scenarios): implement scenario CRUD API`
- `feat(service): add scenario service`
- `test(api): add scenario endpoint tests`

**Chaitanya**
- `docs(scientific): define scenario configuration`
- `feat(dataset): add scenario example`
- `test(api): add scenario test support`

**Dinesh**
- `feat(scenarios): create scenario management page`
- `feat(ui): add dashboard statistics cards`
- `feat(router): improve navigation experience`

### Integration Workflow (Revised Merge Order)
```
Scientific → Backend → Frontend → End-to-End Test
```

### End-to-End Test Scenario
```
Open Dashboard → Navigate to Cases → Create Case → Navigate to Scenarios →
Create Scenario → Scenario Saved → Scenario Listed → Delete Scenario → Refresh List
```

### Smoke Test Checklist
**Backend:** Scenario CRUD APIs respond correctly · Swagger documentation updated · Unit tests pass
**Frontend:** Scenario page loads · Form validation works · List refreshes after create/delete
**Database:** Scenario records persist · Foreign key preparation verified
**Docker:** Full stack launches successfully

### Acceptance Criteria

| Requirement | Status |
|---|---|
| Scenario ORM model completed | ✅ |
| Scenario repository implemented | ✅ |
| Scenario service implemented | ✅ |
| POST /scenarios working | ✅ |
| GET /scenarios working | ✅ |
| DELETE /scenarios working | ✅ |
| Swagger updated | ✅ |
| Scenario page completed | ✅ |
| API integration working | ✅ |
| Dashboard updated | ✅ |
| Scientific scenario schema documented | ✅ |
| Unit tests passing | ✅ |
| Docker smoke test passing | ✅ |
| PRs merged into develop, branches deleted | ✅ |

### Day 4 Exit Gate
Before moving to Day 5:
1. Case Management and Scenario Management are both fully functional.
2. Backend and frontend communicate successfully for both modules.
3. Database stores Cases and Scenarios correctly.
4. Docker Compose launches without issues.
5. CI pipeline remains green.
6. Scientific documentation for future simulation inputs is complete.

> ### 🔒 API Contract Freeze (extended)
> As of the end of Day 4, the Scenario endpoints (`POST /scenarios`, `GET /scenarios`, `DELETE /scenarios/{id}`) join the Case endpoints under the freeze policy — no breaking changes except bug fixes.

### 📊 Week 1 Progress After Day 4

| Area | Progress |
|---|---|
| Repository & DevOps | 100% |
| Docker Environment | 100% |
| Backend Foundation | 100% |
| Database Foundation | 100% |
| Frontend Foundation | 90% |
| Case Management | 100% |
| Scenario Management | 100% |
| Scientific Foundation | 60% |
| CI/CD | 95% |
| Documentation | 75% |

**Overall Week 1 Progress: ~70% Complete**

---

## Day 5 — Project Infrastructure, Logging & Production Readiness

**Theme:** Production Infrastructure & Engineering Quality

### Objectives
Days 1–4 focused on building features. Day 5 focuses on making those features production-quality — reliability, maintainability, observability, developer experience.

By the end of Day 5:
- Configuration is centralized.
- Logging is standardized.
- Error handling is consistent.
- Environment variables are configured.
- Frontend handles loading and error states gracefully.
- CI pipeline validates quality automatically.

No new business features are added today.

> **Revision note:** Per CTO review, **file logging and GZip compression are removed from Week 1 scope** — console logging is sufficient for now, and both can be added later if needed without architectural impact.

### Architecture Progress
```
Day 1: Environment → Day 2: Database → Day 3: Case CRUD → Day 4: Scenario CRUD →
Day 5: Infrastructure / Logging / Configuration / Quality
```

### Deliverables

**Backend:** Centralized Configuration · Logging Framework (console only) · Global Exception Handler · Standard Response Model · Environment Variables · API Middleware
**Frontend:** Notification System · Loading Components · Error Pages · Reusable UI States
**Scientific:** Logging Interfaces · Configuration Structure · Scientific Constants
**DevOps:** CI Improvements · Pre-commit Hooks · Code Quality Automation

---

### 👨‍💻 Sriram — Backend Lead

| Task | Description | Est. Time |
|---|---|---|
| 1. Centralize Configuration | `backend/app/core/config.py`, `settings.py` — includes app name, version, debug mode, database URL, API prefix, logging level. Everything from environment variables | 40 min |
| 2. Environment Variables | Create `.env.example`: `APP_NAME=Asterion`, `APP_VERSION=1.0.0`, `API_PREFIX=/api/v1`, `DATABASE_URL=sqlite:///asterion.db`, `LOG_LEVEL=INFO`, `DEBUG=False`. Never commit a real `.env` | 15 min |
| 3. Logging System (console only) | `backend/app/core/logging.py` — console logging, timestamp, log level, optional request ID. File logging deferred. Example: `2026-07-06 10:12:03 INFO GET /api/v1/cases 200 OK` | 30 min |
| 4. Global Exception Handling | Centralize all errors; never expose stack traces. Format: `{"success": false, "error": {"code": "CASE_NOT_FOUND", "message": "Requested case does not exist."}}` | 30 min |
| 5. Response Models | Standard success: `{"success": true, "message": "Operation completed.", "data": {}}`; standard error: `{"success": false, "error": {}}` — no inconsistent responses | 30 min |
| 6. Middleware (trimmed) | Request Logging, Response Timing, CORS. GZip compression removed from Week 1 scope | 30 min |
| 7. Backend Tests | Verify Exception Handler, Response Models, Logging, Environment Variables | 30 min |

**Deliverables:** Backend infrastructure production-ready.
**Estimated total:** ~3.25 hours

### 👨‍🔬 Chaitanya — Scientific Engineer

No algorithms today — focus on engineering support, trimmed documentation.

| Task | Description | Est. Time |
|---|---|---|
| 1. Scientific Configuration | `scientific/config.py` — noise limits, RSSI ranges, future solver parameters, simulation defaults | 25 min |
| 2. Scientific Constants | `constants.py` — `MIN_RSSI`, `MAX_RSSI`, `DEFAULT_NOISE`, `MAX_TOWERS` | 15 min |
| 3. Scientific Logging | Prepare `scientific/logger.py` for future localization logging (console only, matching backend approach) | 15 min |
| 4. Backend Support (new) | Pair with Sriram to verify environment variable and configuration tests | 30 min |

**Deliverables:** Scientific infrastructure complete · Contributed to configuration test coverage
**Estimated total:** ~1.4 hours

### 👨‍💻 Dinesh — Frontend Lead

| Task | Description | Est. Time |
|---|---|---|
| 1. Notification System | Install Sonner (or project-approved equivalent) — Success, Error, Warning, Loading | 30 min |
| 2. Loading Components | `LoadingSpinner`, `LoadingPage`, `SkeletonCard` — reusable only | 30 min |
| 3. Error Components | `ErrorPage`, `ErrorCard`, `NotFoundPage` | 25 min |
| 4. Global Theme | Improve Dark Mode, Light Mode, Theme Persistence | 30 min |
| 5. Layout Polish | Sidebar animation, responsive spacing, mobile behavior, navigation consistency | 30 min |
| 6. Reusable UI Components | `Button`, `Input`, `Card`, `Modal`, `Badge` — built using shadcn/ui | 40 min |
| 7. Frontend Testing | Verify loading states, error handling, navigation, responsive layout | 30 min |

**Deliverables:** Professional frontend experience.
**Estimated total:** ~3.4 hours

### Repository Structure (Expected)
```
backend/
  core/config.py, logging.py
  middleware/
  exceptions/

frontend/
  components/ui/, feedback/
  layouts/

scientific/
  config.py, constants.py, logger.py
```

### Git Commits

**Sriram**
- `feat(core): centralize application configuration`
- `feat(logging): add structured console logging`
- `refactor(api): standardize API responses`
- `test(core): add configuration tests`

**Chaitanya**
- `feat(scientific): add scientific configuration`
- `test(core): verify environment/config tests`

**Dinesh**
- `feat(ui): add loading components`
- `feat(theme): improve dark mode`
- `feat(feedback): add notification system`

### Integration Workflow (Revised Merge Order)
```
Scientific → Backend → Frontend → CI Validation → Smoke Test
```

### Smoke Test
**Backend:** Configuration loads · Logs generated · Errors formatted correctly
**Frontend:** Notifications work · Loading screens display · Error pages render
**Scientific:** Configuration imports correctly
**Docker:** Entire stack launches successfully
**CI:** All checks pass

### Code Quality Checklist
**Backend:** Ruff passes · Black passes · Type hints complete
**Frontend:** TypeScript compile passes · ESLint passes · Build succeeds
**Documentation:** README updated if configuration changed

### Acceptance Criteria

| Requirement | Status |
|---|---|
| Centralized configuration | ✅ |
| Environment variables configured | ✅ |
| Structured console logging implemented | ✅ |
| Global exception handling | ✅ |
| Standard response models | ✅ |
| Middleware configured (Request Logging, Timing, CORS) | ✅ |
| Notification system | ✅ |
| Loading components | ✅ |
| Error pages | ✅ |
| Theme persistence | ✅ |
| Scientific configuration documented | ✅ |
| CI pipeline passing | ✅ |
| Docker smoke test passing | ✅ |
| PRs merged into develop, branches deleted | ✅ |

### Day 5 Exit Gate
The team proceeds to Day 6 only if:
1. All APIs return standardized responses.
2. Logging works across the backend.
3. Environment configuration is centralized.
4. Frontend gracefully handles loading and error states.
5. Code quality checks pass automatically.
6. Docker Compose starts the application without warnings.
7. CI remains green after integration.

### 📊 Week 1 Progress After Day 5

| Area | Progress |
|---|---|
| Repository & DevOps | 100% |
| Docker Environment | 100% |
| Backend Foundation | 100% |
| Database Foundation | 100% |
| Frontend Foundation | 100% |
| Case Management | 100% |
| Scenario Management | 100% |
| Scientific Foundation | 75% |
| Infrastructure & Quality | 100% |
| CI/CD | 100% |
| Documentation | 85% |

**Overall Week 1 Progress: ~85% Complete**

### 🔍 Quality Gate Checklist (must pass before any merge into `develop`)

- ✅ Ruff formatting
- ✅ Black formatting
- ✅ TypeScript build
- ✅ Backend unit tests
- ✅ Frontend build
- ✅ Docker Compose validation
- ✅ No merge conflicts

This is the point where Asterion transitions from "it works" to "it is engineered correctly," preventing technical debt from accumulating before Week 2.

---

## Day 6 — Integration Day

**Theme:** Integration, Quality Assurance & Foundation Release (Part 1)

### Sprint Objectives (Days 6–7)
Days 1–5 focused on building. Days 6 and 7 focus on making everything work together.

- No new features (with one deliberate exception: the deferred `Towers` model, see below).
- No architecture changes.
- Only: Integration · Bug fixing · Testing · Documentation · Release

### Architecture Status
```
Repository → Docker → Backend → Database → Frontend → Integration → Testing → Release
```

### Goal
Produce the first complete end-to-end working version of Asterion.

### Deliverables

**Backend:** All APIs integrated · Error handling verified · Logging verified · **`Towers` ORM model added (deferred from Day 2)**
**Frontend:** Backend connected · CRUD working · Navigation complete
**Scientific:** Foundation imported correctly · Folder structure finalized
**DevOps:** Docker validated · CI passing

### Integration Order (Revised Merge Order)
```
Database → Backend → Frontend → Docker → CI → End-to-End Test
```
Never integrate frontend before backend APIs are verified.

---

### 👨‍💻 Sriram — Integration Lead

| Task | Description | Est. Time |
|---|---|---|
| 1. Merge Branches | Merge latest branches into `develop`; verify merge conflicts resolved and build successful; **delete merged feature branches** | 30 min |
| 2. Backend Integration | Verify Database Session, Services, Repository Layer, Routers all connect correctly | 40 min |
| 3. Towers Model (deferred from Day 2) | Add `Towers` ORM model (id, tower_name, latitude, longitude, sector, created_at) now that Week 2 is imminent and the need is concrete | 30 min |
| 4. Swagger Validation | Every endpoint must appear correctly, contain examples, have response models and descriptions | 25 min |
| 5. Docker Validation | Verify `docker compose up --build` works from a clean clone and fresh database | 30 min |
| 6. CI Validation | GitHub Actions must pass Ruff, Black, Tests, Build | 20 min |
| 7. Integration Tests | Verify Health API → Case CRUD → Scenario CRUD → SQLite Persistence | 30 min |

**Deliverables:** Backend fully integrated, including Towers model.
**Estimated total:** ~3.4 hours

### 👨‍🔬 Chaitanya — Scientific Engineer

Week 1 ends with the scientific foundation complete.

| Task | Description | Est. Time |
|---|---|---|
| 1. Review Scientific Structure | Verify `simulation/`, `validation/`, `models/`, `pipeline/`, `config/` exist | 15 min |
| 2. Validate Dataset Structure | Verify `datasets/sample/`, `raw/`, `processed/` exist | 15 min |
| 3. Review Documentation | README updated, scientific roadmap complete, Week 2 prerequisites documented | 25 min |
| 4. Prepare Week 2 Checklist | Document modules to implement: Simulator, RSSI Generator, Noise Model, Validation Engine | 20 min |
| 5. Towers Test Support (new) | Write 1–2 tests for the new Towers model alongside Sriram | 25 min |

**Deliverables:** Scientific foundation frozen · Contributed to Towers test coverage
**Estimated total:** ~1.7 hours

### 👨‍💻 Dinesh — Frontend Lead

| Task | Description | Est. Time |
|---|---|---|
| 1. Backend Connection | Connect Dashboard → Cases → Scenarios to backend | 30 min |
| 2. Navigation Testing | Verify every page loads correctly | 20 min |
| 3. Responsive Testing | Desktop, Tablet, Mobile | 25 min |
| 4. UI Polish | Minor improvements only — no redesign | 25 min |
| 5. Loading & Error Testing | Disconnect backend; verify Error Pages, Notifications, Loading States | 25 min |

**Deliverables:** Frontend completely integrated.
**Estimated total:** ~2 hours

### End-to-End Test Plan
```
Start Docker → Open Browser → Dashboard Loads → Create Case → Case Saved →
Create Scenario → Scenario Saved → Refresh → Data Persists →
Delete Scenario → Delete Case → Application Stable
```

### Integration Checklist
**Backend:** FastAPI starts · SQLite connects · Health endpoint works · CRUD APIs respond · Swagger available · Towers model present
**Frontend:** Dashboard loads · Sidebar works · Navigation works · CRUD UI works · Notifications display
**Docker:** Builds successfully · No container crashes · Logs clean
**CI:** Workflow passes · No lint failures · No formatting failures

### Day 6 Acceptance Criteria

| Requirement | Status |
|---|---|
| Backend integrated | ✅ |
| Frontend integrated | ✅ |
| Database integrated | ✅ |
| CRUD working | ✅ |
| Towers model added | ✅ |
| Docker validated | ✅ |
| Swagger validated | ✅ |
| CI passing | ✅ |
| End-to-end workflow working | ✅ |
| Merged feature branches deleted | ✅ |

---

## Day 7 — Review & Stabilization

### Goal
Transform the working system into a release-quality foundation.

### Morning Session

**Bug Fixing** — Fix issues by priority:

| Priority | Meaning |
|---|---|
| P0 | Breaks the build or blocks the whole team — fix immediately |
| P1 | Breaks a feature or the demo path — fix same day |
| P2 | Non-blocking bug or missing polish — fix before end of day |
| P3 | Cosmetic / nice-to-have — defer to Week 2+ |

**Code Cleanup** — Remove unused imports, dead code, console logs, temporary files. Run:
```
ruff check .
black .
npm run build
```

**Documentation Review** — Owners update their assigned docs (see [Documentation Ownership](#documentation-ownership)): `README.md` (Sriram), `CHANGELOG.md` (Sriram), `CONTRIBUTING.md`, `SECURITY.md`; verify installation instructions.

### Afternoon Session

**Sprint Review** — Demonstrate Dashboard, Health API, Case CRUD, Scenario CRUD, Docker, Swagger.

**Architecture Review** — Verify repository still follows:
```
Frontend → API → Service → Repository → Database
```
No shortcuts introduced.

**Repository Review** — Check Folder Structure, Branch History, Commit Messages, PR History, CI Status. Everything should be professional. Confirm all merged feature branches have been deleted.

**Merge Final Branches** — Merge all remaining feature branches → `develop` → `main`. Tag `v0.1.0`.

### Release Checklist (new — before tagging `v0.1.0`)

- [ ] Clean clone builds successfully
- [ ] Docker build succeeds
- [ ] All smoke tests pass
- [ ] CI is green
- [ ] README verified against a fresh setup
- [ ] Version number updated (`APP_VERSION`, `package.json`, etc.)
- [ ] CHANGELOG updated
- [ ] All merged feature branches deleted

---

## Foundation Release

**Release Name:** Asterion v0.1 — Foundation Release

### Release Notes

**Completed**
- Repository setup
- Backend foundation
- Frontend foundation
- Database (Cases, Scenarios, Towers)
- Docker
- Swagger
- Case CRUD
- Scenario CRUD
- Documentation
- CI/CD
- Scientific structure

**Deferred to Week 2**
- Simulator
- Localization
- RSSI
- Kalman Filter
- Confidence Engine
- Reports

### Sprint Retrospective
Each developer answers:
- What went well?
- What slowed us down?
- What should improve next week?
- Any blockers?
- Lessons learned?

Document everything.

### Week 1 Completion Checklist

**Repository:** README complete · License present · Documentation updated
**Backend:** FastAPI running · Swagger complete · CRUD working
**Database:** SQLite connected · Alembic migrations working · Towers model present
**Frontend:** Dashboard complete · Navigation complete · API integration complete
**DevOps:** Docker builds · CI passes · GitHub Actions working
**Scientific:** Architecture complete · Dataset structure ready · Documentation complete

### Final Sprint Acceptance Criteria

Week 1 is complete only if:

| Requirement | Status |
|---|---|
| GitHub Repository Ready | ✅ |
| Docker Compose Works | ✅ |
| FastAPI Running | ✅ |
| React Running | ✅ |
| SQLite Connected | ✅ |
| Alembic Working | ✅ |
| Case CRUD Complete | ✅ |
| Scenario CRUD Complete | ✅ |
| Towers Model Added | ✅ |
| Swagger Ready | ✅ |
| Dashboard Skeleton Complete | ✅ |
| CI Passing | ✅ |
| Documentation Updated | ✅ |
| End-to-End Demo Working | ✅ |
| Release Tagged | ✅ |

---

## Week 2 Readiness Gate

The team must not begin Week 2 until every item below is verified.

**Engineering:** Docker works on all three developer machines · Clean clone builds successfully · CI passes consistently
**Backend:** APIs stable · Response models standardized · Logging working · Towers model ready for Week 2 simulation work
**Frontend:** API integration stable · Layout finalized · Error handling verified
**Scientific:** Folder structure frozen · Dataset schema approved · Documentation complete
**Documentation:** README complete · Setup guide tested by another team member · CHANGELOG updated

### Sprint Metrics

| Metric | Target | Achieved |
|---|---|---|
| Planned Days | 7 | ✅ |
| Core Features | 2 | ✅ |
| CI Passing | 100% | ✅ |
| Docker Reliability | 100% | ✅ |
| Documentation Coverage | >90% | ✅ |
| Critical Bugs | 0 | ✅ |

---

## Sprint Summary & CTO Final Assessment

### Foundation Sprint Summary

**Completed**
- ✅ Engineering Workspace established
- ✅ Development environment standardized
- ✅ Repository professionally structured
- ✅ Dockerized application
- ✅ FastAPI backend operational
- ✅ React frontend operational
- ✅ SQLite integrated
- ✅ API documentation available
- ✅ Case Management complete
- ✅ Scenario Management complete
- ✅ Towers model added (deferred to Day 6 as planned)
- ✅ CI/CD operational
- ✅ Scientific foundation prepared

**Deferred to Week 2**
- Measurement Simulator
- RSSI Generation
- Noise Model
- Validation Engine
- Localization Engine (NLLS)
- Scientific Unit Tests (beyond the basic model/config tests added this week)

### CTO Final Assessment

**Sprint Status:** FOUNDATION SPRINT — SUCCESSFULLY COMPLETED

| Category | Status |
|---|---|
| Engineering Foundation | ✅ Ready |
| Architecture Stability | ✅ Stable |
| Repository Quality | ✅ Professional |
| Team Synchronization | ✅ Ready (daily stand-ups in place) |
| Scientific Sprint | ✅ Authorized |

### Authorization

- **Project:** Asterion
- **Sprint:** Week 1 – Foundation Sprint
- **Status:** APPROVED
- **Version:** v0.1.0 – Foundation Release

The team is authorized to begin **Week 2 – Scientific Engine Sprint**, shifting focus from infrastructure to the scientific core of Asterion: simulation engine, measurement generation, localization algorithms, tracking, and confidence analysis.

---

*🏁 End of Week 1 Master Plan (Revised)*
