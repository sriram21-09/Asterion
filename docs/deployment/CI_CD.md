# CI/CD Pipeline

Asterion maintains high codebase quality via GitHub Actions. 

## Automated Workflows

The primary workflow is located in `.github/workflows/ci.yml`.

### Triggers
- `push` to `main` branch.
- `pull_request` targeting `main`.

### Pipeline Stages

1. **Linting (Ruff)**:
   - Enforces strict PEP-8 compliance and line-length constraints across the backend and scientific engine.
2. **Testing (Pytest)**:
   - Executes the complete test suite (933 tests).
   - Validates scientific algorithms, API boundary constraints, and error handling.
3. **Frontend Build (Vite/TypeScript)**:
   - Validates TypeScript typing.
   - Ensures the React bundle compiles without errors.

## Release Readiness

As of the current submission commit, the CI/CD pipeline guarantees that the Asterion repository is fully buildable, testable, and compliant with standard engineering practices.
