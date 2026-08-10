# Database Schema

Asterion utilizes SQLite as a zero-configuration persistence layer for Hackathon portability, managed via SQLAlchemy ORM and Alembic migrations.

## Entity Overview

The system models the journey of data from raw import to final calculated trajectory.

1. **Case**: The core container for an investigation.
2. **Measurement**: A single processed CDR row mapping a device to a tower.
3. **Tower**: Known cellular tower infrastructure coordinates.
4. **LocalizationResult**: An algorithmically derived coordinate (NLLS or Centroid) for a specific measurement epoch.
5. **TrackingResult**: The Kalman-smoothed coordinate output.
6. **ConfidenceResult**: GDOP and error covariance metadata attached to a localization.
7. **MovementEvent**: Calculated speed, distance, and transition semantics between two sequential tracking results.

## Core Tables

### `cases`
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Internal ID |
| `case_code` | String | External identifier (e.g. `CASE-24A`) |
| `title` | String | User-facing name |
| `status` | String | `active`, `archived`, etc. |

### `measurements`
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Internal ID |
| `case_id` | Integer (FK) | Links to `cases.id` |
| `timestamp` | DateTime | Extracted from CDR |
| `rssi_dbm` | Float | Received Signal Strength |
| `latitude` | Float | Tower latitude |
| `longitude` | Float | Tower longitude |

### `localization_results`
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Internal ID |
| `case_id` | Integer (FK) | Links to `cases.id` |
| `algorithm` | String | `multilateration` or `weighted_centroid` |
| `estimated_latitude`| Float | Computed Y |
| `estimated_longitude`| Float | Computed X |

### `tracking_results`
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Internal ID |
| `case_id` | Integer (FK) | Links to `cases.id` |
| `smoothed_latitude` | Float | Kalman output Y |
| `smoothed_longitude`| Float | Kalman output X |

## Schema Management

Schema migrations are handled entirely via Alembic.

```bash
# Apply all pending migrations (run from backend directory)
alembic upgrade head
```
