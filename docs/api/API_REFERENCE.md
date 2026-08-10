# API Reference

Asterion provides a FastAPI-driven REST API, versioned under `/api/v1`.
For interactive documentation, start the backend and visit `http://localhost:8222/docs` for the Swagger UI.

## Key Workflow Endpoints

### 1. Data Ingestion
**`POST /api/v1/import`**
- **Purpose**: Parses telecom operator CDRs (Airtel, BSNL, Jio, Vi) and extracts network measurements.
- **Request**: `multipart/form-data` containing the `.csv` file and `case_id`.
- **Response**: `200 OK` with parsing statistics and measurement IDs.

### 2. Localization Pipeline
**`POST /api/v1/localization/run`**
- **Purpose**: Executes the scientific engine's NLLS and Quality-Weighted Centroid algorithms on a given case's measurements.
- **Request**: Query parameter `case_code`.
- **Response**: `200 OK` with estimated latitude, longitude, and confidence metrics.

### 3. Trajectory Tracking
**`POST /api/v1/tracking/run`**
- **Purpose**: Applies a 2D Kalman Filter over chronological localization estimates to smooth erratic multipath jumps.
- **Request**: Query parameter `case_code`.
- **Response**: `200 OK` with smoothed chronological path points.

### 4. Integrity and Evidence
**`GET /api/v1/evidence/{case_code}`**
- **Purpose**: Generates a tamper-evident audit packet with a SHA-256 hash.
- **Response**: `200 OK` with the complete cryptographic signature, execution timeline, and parameter manifest.

### 5. Report Generation
**`POST /api/v1/reports/{case_id}/generate`**
- **Purpose**: Compiles a human-readable investigation report summarizing the case, parameters, and findings.
- **Response**: `200 OK` with download link/metadata.
