# Testing

Asterion maintains a rigorous test suite focusing on scientific algorithm integrity, boundary validation, error handling, and API conformance.

## Testing Framework

- **Framework:** `pytest`
- **Configuration:** `pytest.ini` in the repository root sets the `PYTHONPATH` correctly for backend module discovery.
- **Coverage:** Tests span the `backend` FastApi service and the core `scientific` engine.

## Current Test Status

The verified test count on the final submission commit is **933 / 933 tests passing**.

**Latest Run Details:**
- **Total Tests:** 933
- **Passed:** 933
- **Failed:** 0
- **Skipped:** 0

## Running the Tests

To reproduce the test results locally, simply clone the repository and run pytest from the root directory.

```bash
# 1. Activate the backend virtual environment
# Windows
.\backend\.venv\Scripts\activate
# Unix
source backend/.venv/bin/activate

# 2. Run the test suite
pytest
```

## Test Organization

The tests are organized into the following categories within the `tests/` directory:

- `api/`: Endpoint validation, route authorization, and HTTP status code correctness.
- `database/`: Repository logic, ORM behavior, and database constraint checks.
- `scientific/`: Core mathematical verifications including:
  - NLLS multilateration convergence bounds
  - Quality-Weighted Centroid fallback testing
  - Kalman filter chronological drift prevention
  - GDOP confidence calculations
- `core/`: Logging, configuration, and middleware validations.
- `integration/`: End-to-end data pipelines from CDR ingestion to evidence hashing.
