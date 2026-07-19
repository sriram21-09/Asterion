"""
Docker Compose Structural Validation Tests
===========================================

Validates the docker-compose.yml file is parseable and structurally
correct without actually building or starting containers.

This test can run in CI environments that may not have Docker installed.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import yaml
import pytest

COMPOSE_PATH = ROOT / "docker-compose.yml"


@pytest.fixture(scope="module")
def compose_config():
    """Parse and return the docker-compose.yml as a dict."""
    assert COMPOSE_PATH.exists(), f"docker-compose.yml not found at {COMPOSE_PATH}"
    with open(COMPOSE_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestDockerComposeStructure:
    """Validate docker-compose.yml structure and configuration."""

    def test_compose_file_is_valid_yaml(self, compose_config):
        """docker-compose.yml parses without errors."""
        assert compose_config is not None
        assert isinstance(compose_config, dict)

    def test_services_defined(self, compose_config):
        """services key exists and is a dict."""
        assert "services" in compose_config
        assert isinstance(compose_config["services"], dict)

    def test_backend_service_exists(self, compose_config):
        """backend service is defined."""
        assert "backend" in compose_config["services"]

    def test_frontend_service_exists(self, compose_config):
        """frontend service is defined."""
        assert "frontend" in compose_config["services"]

    def test_backend_port_mapping(self, compose_config):
        """backend exposes port 8000."""
        backend = compose_config["services"]["backend"]
        assert "ports" in backend
        port_found = any("8000" in str(p) for p in backend["ports"])
        assert port_found, "Backend must expose port 8000"

    def test_frontend_port_mapping(self, compose_config):
        """frontend exposes port 3000."""
        frontend = compose_config["services"]["frontend"]
        assert "ports" in frontend
        port_found = any("3000" in str(p) for p in frontend["ports"])
        assert port_found, "Frontend must expose port 3000"

    def test_backend_healthcheck_defined(self, compose_config):
        """backend has a healthcheck configuration."""
        backend = compose_config["services"]["backend"]
        assert "healthcheck" in backend
        hc = backend["healthcheck"]
        assert "test" in hc
        assert "interval" in hc
        assert "timeout" in hc
        assert "retries" in hc

    def test_backend_volumes_mount_datasets(self, compose_config):
        """backend mounts the datasets directory."""
        backend = compose_config["services"]["backend"]
        assert "volumes" in backend
        volumes_str = " ".join(str(v) for v in backend["volumes"])
        assert (
            "datasets" in volumes_str
        ), "Backend must mount datasets directory for scenario configs"

    def test_backend_volumes_mount_scientific(self, compose_config):
        """backend mounts the scientific directory."""
        backend = compose_config["services"]["backend"]
        volumes_str = " ".join(str(v) for v in backend["volumes"])
        assert (
            "scientific" in volumes_str
        ), "Backend must mount scientific directory for solver code"

    def test_frontend_depends_on_backend(self, compose_config):
        """frontend depends_on backend with service_healthy condition."""
        frontend = compose_config["services"]["frontend"]
        assert "depends_on" in frontend
        deps = frontend["depends_on"]

        if isinstance(deps, dict):
            assert "backend" in deps
            assert deps["backend"].get("condition") == "service_healthy"
        elif isinstance(deps, list):
            assert "backend" in deps

    def test_backend_dockerfile_path(self, compose_config):
        """backend build points to correct Dockerfile."""
        backend = compose_config["services"]["backend"]
        assert "build" in backend
        build_cfg = backend["build"]
        assert "dockerfile" in build_cfg
        assert "Dockerfile.backend" in build_cfg["dockerfile"]

    def test_frontend_dockerfile_path(self, compose_config):
        """frontend build points to correct Dockerfile."""
        frontend = compose_config["services"]["frontend"]
        assert "build" in frontend
        build_cfg = frontend["build"]
        assert "dockerfile" in build_cfg
        assert "Dockerfile.frontend" in build_cfg["dockerfile"]

    def test_backend_restart_policy(self, compose_config):
        """backend has a restart policy configured."""
        backend = compose_config["services"]["backend"]
        assert "restart" in backend
        assert backend["restart"] in ("always", "unless-stopped", "on-failure")

    def test_frontend_restart_policy(self, compose_config):
        """frontend has a restart policy configured."""
        frontend = compose_config["services"]["frontend"]
        assert "restart" in frontend
        assert frontend["restart"] in ("always", "unless-stopped", "on-failure")

    def test_dockerfile_backend_exists(self):
        """docker/Dockerfile.backend exists on disk."""
        dockerfile = ROOT / "docker" / "Dockerfile.backend"
        assert dockerfile.exists(), f"Dockerfile.backend not found at {dockerfile}"

    def test_dockerfile_frontend_exists(self):
        """docker/Dockerfile.frontend exists on disk."""
        dockerfile = ROOT / "docker" / "Dockerfile.frontend"
        assert dockerfile.exists(), f"Dockerfile.frontend not found at {dockerfile}"
