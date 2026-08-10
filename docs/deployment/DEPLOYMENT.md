# Deployment Guide

Asterion is designed to be easily deployed via Docker Compose, ensuring a zero-friction setup for hackathon reviewers and investigators.

## Prerequisites

- **Docker**: Latest stable version
- **Docker Compose**: V2 plugin

## Quick Start Deployment

Running the entire stack (Frontend, Backend, and Database) takes one command.

```bash
docker compose up --build
```

### Accessing the Services

- **Frontend Application**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8222](http://localhost:8222)
- **Interactive API Docs (Swagger)**: [http://localhost:8222/docs](http://localhost:8222/docs)

## Services Architecture

The `docker-compose.yml` orchestrates two primary containers:

1. **`backend`**
   - Built via `docker/backend.Dockerfile`.
   - Mounts the SQLite database as a volume to ensure investigation data persists across container restarts.
   - Runs `alembic upgrade head` on startup to ensure schema compatibility.

2. **`frontend`**
   - Built via `docker/frontend.Dockerfile`.
   - Runs the React 19 / Vite development server exposed on port 3000.

## Persistent Volumes

- `asterion_data`: Maps to `/app/data` inside the backend container to persist the `asterion.db` SQLite file.

## Troubleshooting

**Port Conflicts**
If port 3000 or 8222 is occupied, modify the mapping in `docker-compose.yml`:
```yaml
ports:
  - "NEW_PORT:3000"
```

**Clean Reset**
To completely wipe all investigation data and start fresh:
```bash
docker compose down -v
```
