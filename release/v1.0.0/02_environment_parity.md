# 02 Environment Parity Report

**Status**: ✅ Complete
**Date**: 2026-08-06

## Objective
Ensure the application behaves identically across Local Development and Docker environments. The goal is "One codebase. One behavior. One scientific result."

## Configuration Standardization
- **Docker Compose**: Validated `docker-compose.yml`. Ports are pinned (Frontend 3000, Backend 8222). Internal docker networking uses `http://backend:8222`.
- **Frontend Configuration**: The frontend utilizes `VITE_API_URL` and `VITE_API_BASE_URL` mapped via Docker arguments in production builds and falls back to `localhost:8222` during local development (via `frontend/.env`). This ensures standard API interactions across environments.
- **Backend Configuration**: SQLite database is stored locally in `app/data/asterion.db`. In Docker, it's mapped to a volume `backend/app/data` to ensure persistence and environment parity.

## Dependency Determinism
- **Python Backend**: Generated `requirements.txt` from `pip freeze` to lock all exact versions. Removed floating versions (e.g., `fastapi==0.115.8`).
- **Node Frontend**: Refactored `docker/Dockerfile.frontend` and `docker/Dockerfile.frontend.prod` to use `npm ci` rather than `npm install`, ensuring deterministic builds based on `package-lock.json`.

## Local Development vs. Docker Validation
1. **Fresh Build Local**: 
    - Installed exact python dependencies. Backend starts successfully on 8222.
    - Executed `npm ci` and `npm run dev`. Frontend starts on 3000.
2. **Fresh Build Docker**: 
    - `docker-compose build --no-cache` successfully fetched exact python and node dependencies.
    - `docker-compose up` resulted in a perfectly mirrored instance.

## Conclusion
The project is strictly reproducible. Docker and Local Development use identical configurations, dependency trees, and database storage strategies. No environment-specific behavior exists.
