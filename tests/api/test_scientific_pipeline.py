"""
E2E Scientific Pipeline Integration Tests
==========================================

Comprehensive test suite verifying that all backend API endpoints run
in sequence as a coherent scientific pipeline:

  Scenario → Case → Simulation → Localization → Tracking → Confidence → Evidence

Also validates:
  - Database wipe/seed routines work correctly
  - Swagger/OpenAPI documentation is accessible and complete
  - Pipeline is idempotent on measurement regeneration

Deliverable: tests/api/test_scientific_pipeline.py (Issue #53)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

import pytest


# ---------------------------------------------------------------------------
# 1. E2E Scientific Pipeline — Sequential Endpoint Tests
# ---------------------------------------------------------------------------


class TestScientificPipelineE2E:
    """Verify all backend endpoints run in correct sequence."""

    def test_health_endpoint(self, client):
        """GET /api/v1/health returns 200 with healthy status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "asterion-api"

    def test_root_endpoint(self, client):
        """GET / returns 200 with online status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"

    def test_step1_create_scenario(self, client):
        """POST /api/v1/scenarios/ creates a scenario successfully."""
        response = client.post(
            "/api/v1/scenarios/",
            json={
                "name": "Pipeline Scenario",
                "description": "Test scenario for E2E pipeline",
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "Pipeline Scenario"
        assert "id" in data

    def test_step2_create_case_linked_to_scenario(self, client):
        """POST /api/v1/cases/ creates a case linked to scenario."""
        # Create scenario first
        scn = client.post("/api/v1/scenarios/", json={"name": "Case Link Scenario"})
        scn_id = scn.json()["data"]["id"]

        response = client.post(
            "/api/v1/cases/",
            json={
                "title": "Pipeline Case",
                "description": "Case for E2E pipeline test",
                "scenario_id": scn_id,
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["title"] == "Pipeline Case"
        assert data["scenario_id"] == scn_id

    def test_step3_generate_measurements(self, client, seed_scenario_and_case):
        """POST /api/v1/simulation/generate generates synthetic measurements."""
        scenario_id, case_id = seed_scenario_and_case
        case_code = f"CASE-{case_id:03d}"

        response = client.post(
            f"/api/v1/simulation/generate?case_code={case_code}",
            json={
                "algorithm": "multilateration",
                "max_iterations": 100,
                "convergence_threshold_m": 1.0,
                "measurement_count": 3,
                "enable_noise": True,
                "random_seed": 42,
            },
        )
        assert response.status_code == 200, f"Simulation failed: {response.json()}"
        data = response.json()
        assert data["success"] is True
        measurements = data["data"]
        assert len(measurements) >= 3, (
            f"Expected >= 3 measurements, got {len(measurements)}"
        )

    def test_step4_run_localization(self, client, seed_scenario_and_case):
        """POST /api/v1/localization/run runs multilateration solver."""
        scenario_id, case_id = seed_scenario_and_case
        case_code = f"CASE-{case_id:03d}"

        # Generate measurements first
        client.post(
            f"/api/v1/simulation/generate?case_code={case_code}",
            json={
                "algorithm": "multilateration",
                "max_iterations": 100,
                "convergence_threshold_m": 1.0,
                "measurement_count": 3,
                "enable_noise": True,
                "random_seed": 42,
            },
        )

        # Run localization
        response = client.post(f"/api/v1/localization/run?case_code={case_code}")
        assert response.status_code == 200, f"Localization failed: {response.json()}"
        data = response.json()["data"]
        assert "estimated_latitude" in data
        assert "estimated_longitude" in data
        assert "algorithm" in data
        assert data["signals_used"] >= 1

    def test_step5_run_tracking(self, client, seed_scenario_and_case):
        """POST /api/v1/tracking/run runs Kalman-smoothed tracking."""
        scenario_id, case_id = seed_scenario_and_case
        case_code = f"CASE-{case_id:03d}"

        # Generate measurements (multiple timestamps for tracking)
        client.post(
            f"/api/v1/simulation/generate?case_code={case_code}",
            json={
                "algorithm": "multilateration",
                "max_iterations": 100,
                "convergence_threshold_m": 1.0,
                "measurement_count": 3,
                "enable_noise": True,
                "random_seed": 42,
            },
        )
        # Run localization (creates multiple localization results)
        client.post(f"/api/v1/localization/run?case_code={case_code}")

        # Run tracking
        response = client.post(f"/api/v1/tracking/run?case_code={case_code}")
        assert response.status_code == 200, f"Tracking failed: {response.json()}"
        data = response.json()["data"]
        assert "total_steps" in data
        assert data["total_steps"] >= 2
        assert "path" in data
        assert len(data["path"]) >= 2
        assert "distance_km" in data
        assert "avg_velocity_kmh" in data

    def test_step6_run_confidence(self, client, seed_scenario_and_case):
        """POST /api/v1/confidence/run runs GDOP confidence analysis."""
        scenario_id, case_id = seed_scenario_and_case
        case_code = f"CASE-{case_id:03d}"

        # Pipeline prerequisite: generate + localize
        client.post(
            f"/api/v1/simulation/generate?case_code={case_code}",
            json={
                "algorithm": "multilateration",
                "max_iterations": 100,
                "convergence_threshold_m": 1.0,
                "measurement_count": 3,
                "enable_noise": True,
                "random_seed": 42,
            },
        )
        client.post(f"/api/v1/localization/run?case_code={case_code}")

        # Run confidence
        response = client.post(f"/api/v1/confidence/run?case_code={case_code}")
        assert response.status_code == 200, f"Confidence failed: {response.json()}"
        data = response.json()["data"]
        assert "confidence_score" in data
        assert 0.0 <= data["confidence_score"] <= 1.0
        assert "confidence_level" in data
        assert data["confidence_level"] in ("low", "medium", "high")
        assert "gdop" in data
        assert "method" in data

    def test_step7_get_evidence(self, client, seed_scenario_and_case):
        """GET /api/v1/evidence/{case_code} retrieves audit evidence packet."""
        scenario_id, case_id = seed_scenario_and_case
        case_code = f"CASE-{case_id:03d}"

        # Pipeline prerequisite: generate + localize + confidence
        client.post(
            f"/api/v1/simulation/generate?case_code={case_code}",
            json={
                "algorithm": "multilateration",
                "max_iterations": 100,
                "convergence_threshold_m": 1.0,
                "measurement_count": 3,
                "enable_noise": True,
                "random_seed": 42,
            },
        )
        client.post(f"/api/v1/localization/run?case_code={case_code}")
        client.post(f"/api/v1/confidence/run?case_code={case_code}")

        # Get evidence
        response = client.get(f"/api/v1/evidence/{case_code}")
        assert response.status_code == 200, f"Evidence failed: {response.json()}"
        data = response.json()["data"]
        assert data["case_code"] == case_code.upper()
        assert "summary" in data
        assert "towers" in data
        assert "accepted_measurement_ids" in data
        assert "rejections" in data

    def test_full_pipeline_sequential(self, client):
        """Run the complete pipeline end-to-end in a single test."""
        # Step 1: Create scenario
        scn_res = client.post(
            "/api/v1/scenarios/",
            json={
                "name": "Full Pipeline Scenario",
                "description": "Complete E2E run",
            },
        )
        assert scn_res.status_code == 201
        scenario_id = scn_res.json()["data"]["id"]

        # Step 2: Create case
        case_res = client.post(
            "/api/v1/cases/",
            json={
                "title": "Full Pipeline Case",
                "description": "Complete E2E case",
                "scenario_id": scenario_id,
            },
        )
        assert case_res.status_code == 201
        case_id = case_res.json()["data"]["id"]
        case_code = f"CASE-{case_id:03d}"

        # Step 3: Generate measurements
        sim_res = client.post(
            f"/api/v1/simulation/generate?case_code={case_code}",
            json={
                "algorithm": "multilateration",
                "max_iterations": 100,
                "convergence_threshold_m": 1.0,
                "measurement_count": 3,
                "enable_noise": True,
                "random_seed": 42,
            },
        )
        assert sim_res.status_code == 200
        measurements = sim_res.json()["data"]
        assert len(measurements) >= 3

        # Step 4: Run localization
        loc_res = client.post(f"/api/v1/localization/run?case_code={case_code}")
        assert loc_res.status_code == 200
        loc_data = loc_res.json()["data"]
        assert loc_data["estimated_latitude"] is not None
        assert loc_data["estimated_longitude"] is not None

        # Step 5: Run tracking (requires >= 2 localization results)
        track_res = client.post(f"/api/v1/tracking/run?case_code={case_code}")
        assert track_res.status_code == 200
        track_data = track_res.json()["data"]
        assert track_data["total_steps"] >= 2

        # Step 6: Run confidence
        conf_res = client.post(f"/api/v1/confidence/run?case_code={case_code}")
        assert conf_res.status_code == 200
        conf_data = conf_res.json()["data"]
        assert 0.0 <= conf_data["confidence_score"] <= 1.0

        # Step 7: Get evidence
        evi_res = client.get(f"/api/v1/evidence/{case_code}")
        assert evi_res.status_code == 200
        evi_data = evi_res.json()["data"]
        assert evi_data["case_code"] == case_code.upper()
        assert len(evi_data["towers"]) >= 1

        # Cross-validate: confidence data should be present in evidence
        assert evi_data["confidence"] is not None
        assert evi_data["confidence"]["confidence_score"] == pytest.approx(
            conf_data["confidence_score"], abs=0.001
        )


# ---------------------------------------------------------------------------
# 2. Database Wipe/Seed Routine Tests
# ---------------------------------------------------------------------------


class TestDatabaseWipeSeed:
    """Verify that the in-memory database wipe/seed cycle works correctly."""

    def test_clean_slate_after_wipe(self, client):
        """Each test starts with an empty database (no leftover data)."""
        response = client.get("/api/v1/scenarios/")
        assert response.status_code == 200
        assert response.json()["data"] == []

        response = client.get("/api/v1/cases/")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_seed_creates_expected_records(self, client, seed_scenario_and_case):
        """seed_scenario_and_case fixture inserts exactly 1 scenario + 1 case."""
        scenario_id, case_id = seed_scenario_and_case

        # Check scenario exists
        scn_res = client.get(f"/api/v1/scenarios/{scenario_id}")
        assert scn_res.status_code == 200
        assert scn_res.json()["data"]["name"] == "Urban 3-Tower Test"

        # Check case exists and is linked
        case_res = client.get(f"/api/v1/cases/{case_id}")
        assert case_res.status_code == 200
        assert case_res.json()["data"]["scenario_id"] == scenario_id

    def test_isolation_between_tests(self, client):
        """Data from previous tests does not leak into this test."""
        # This test runs after test_seed_creates_expected_records
        # but should start with empty tables due to per-function fixture
        scenarios = client.get("/api/v1/scenarios/").json()["data"]
        cases = client.get("/api/v1/cases/").json()["data"]
        assert len(scenarios) == 0, "Scenario data leaked between tests"
        assert len(cases) == 0, "Case data leaked between tests"

    def test_pipeline_idempotent_on_regenerate(self, client, seed_scenario_and_case):
        """Running simulation twice replaces old measurements (idempotent)."""
        scenario_id, case_id = seed_scenario_and_case
        case_code = f"CASE-{case_id:03d}"

        sim_payload = {
            "algorithm": "multilateration",
            "max_iterations": 100,
            "convergence_threshold_m": 1.0,
            "measurement_count": 3,
            "enable_noise": True,
            "random_seed": 42,
        }

        # First run
        res1 = client.post(
            f"/api/v1/simulation/generate?case_code={case_code}",
            json=sim_payload,
        )
        assert res1.status_code == 200
        count1 = len(res1.json()["data"])

        # Second run — should replace, not double
        sim_payload["random_seed"] = 99
        res2 = client.post(
            f"/api/v1/simulation/generate?case_code={case_code}",
            json=sim_payload,
        )
        assert res2.status_code == 200
        count2 = len(res2.json()["data"])

        # Counts should be the same (old measurements were deleted before insertion)
        assert count1 == count2


# ---------------------------------------------------------------------------
# 3. Swagger / OpenAPI Documentation Tests
# ---------------------------------------------------------------------------


class TestSwaggerDocs:
    """Validate Swagger documentation is accessible and covers all endpoints."""

    def test_openapi_schema_accessible(self, client):
        """GET /openapi.json returns valid JSON schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "info" in schema

    def test_openapi_paths_contain_all_endpoints(self, client):
        """All 8 API route prefixes appear in the OpenAPI schema."""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]
        path_keys = " ".join(paths.keys())

        expected_prefixes = [
            "/api/v1/scenarios",
            "/api/v1/cases",
            "/api/v1/simulation",
            "/api/v1/measurements",
            "/api/v1/localization",
            "/api/v1/tracking",
            "/api/v1/confidence",
            "/api/v1/evidence",
        ]
        for prefix in expected_prefixes:
            assert prefix in path_keys, (
                f"Missing endpoint prefix in OpenAPI schema: {prefix}"
            )

    def test_docs_page_accessible(self, client):
        """GET /docs returns the Swagger UI page."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_page_accessible(self, client):
        """GET /redoc returns the ReDoc documentation page."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_has_app_metadata(self, client):
        """OpenAPI schema includes app title and version."""
        response = client.get("/openapi.json")
        schema = response.json()
        info = schema["info"]
        assert "title" in info
        assert "version" in info
        assert len(info["title"]) > 0


# ---------------------------------------------------------------------------
# 4. Error Handling & Edge Case Tests
# ---------------------------------------------------------------------------


class TestPipelineErrorHandling:
    """Verify pipeline endpoints return proper errors for invalid inputs."""

    def test_localization_without_measurements_fails(
        self, client, seed_scenario_and_case
    ):
        """Localization with no measurements returns 400."""
        _, case_id = seed_scenario_and_case
        case_code = f"CASE-{case_id:03d}"

        response = client.post(f"/api/v1/localization/run?case_code={case_code}")
        assert response.status_code in (400, 422)

    def test_tracking_without_localization_fails(self, client, seed_scenario_and_case):
        """Tracking with no localization results returns 400."""
        _, case_id = seed_scenario_and_case
        case_code = f"CASE-{case_id:03d}"

        response = client.post(f"/api/v1/tracking/run?case_code={case_code}")
        assert response.status_code in (400, 422)

    def test_confidence_without_measurements_fails(
        self, client, seed_scenario_and_case
    ):
        """Confidence with no measurements returns 400."""
        _, case_id = seed_scenario_and_case
        case_code = f"CASE-{case_id:03d}"

        response = client.post(f"/api/v1/confidence/run?case_code={case_code}")
        assert response.status_code in (400, 422)

    def test_evidence_without_measurements_fails(self, client, seed_scenario_and_case):
        """Evidence with no measurements returns 400."""
        _, case_id = seed_scenario_and_case
        case_code = f"CASE-{case_id:03d}"

        response = client.get(f"/api/v1/evidence/{case_code}")
        assert response.status_code in (400, 422)

    def test_simulation_invalid_case_code_fails(self, client):
        """Simulation with non-existent case code returns error."""
        response = client.post(
            "/api/v1/simulation/generate?case_code=CASE-999",
            json={
                "algorithm": "multilateration",
                "max_iterations": 100,
                "convergence_threshold_m": 1.0,
                "measurement_count": 1,
                "enable_noise": False,
                "random_seed": 1,
            },
        )
        assert response.status_code in (400, 404)

    def test_case_without_scenario_cannot_simulate(self, client):
        """A case with no scenario_id cannot generate measurements."""
        # Create case without scenario
        case_res = client.post(
            "/api/v1/cases/",
            json={"title": "Orphan Case"},
        )
        assert case_res.status_code == 201
        case_id = case_res.json()["data"]["id"]
        case_code = f"CASE-{case_id:03d}"

        response = client.post(
            f"/api/v1/simulation/generate?case_code={case_code}",
            json={
                "algorithm": "multilateration",
                "max_iterations": 100,
                "convergence_threshold_m": 1.0,
                "measurement_count": 1,
                "enable_noise": False,
                "random_seed": 1,
            },
        )
        assert response.status_code in (400, 422)
