# Task: Database & Model Foundation (Day 2)

## Objective
Establish the database connection, configure Alembic, create Base ORM models, Cases and Scenarios models, and Pydantic schemas.

## Tasks
- [x] Create Database Package (`backend/app/database/base.py`, `session.py`, `engine.py`)
- [x] Configure database settings, SQLite connection string, and session factory
- [x] Initialize Alembic (`alembic/`, `env.py`, `versions/`) and verify autogenerate migrations
- [x] Create Base ORM Model with common fields (`id`, `created_at`, `updated_at`)
- [x] Create Cases and Scenarios ORM Models
- [x] Create `CaseCreate`, `CaseResponse`, `ScenarioCreate` Pydantic Schemas
- [x] Create database connection and model tests in `tests/database/`

## Deliverables
- [x] `backend/app/database/` (engine, session, base)
- [x] `alembic/` configurations and migrations
- [x] `backend/app/models/` (case and scenario models)
- [x] `backend/app/schemas/` (Pydantic schemas)
- [x] `tests/database/` (database and model tests)

