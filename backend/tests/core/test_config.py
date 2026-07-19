import os
import sys
import importlib
from unittest import mock


def test_default_settings():
    # Patch environment to ensure defaults are loaded
    with mock.patch.dict(os.environ, {}, clear=True):
        if "app.core.config" in sys.modules:
            importlib.reload(sys.modules["app.core.config"])
        from app.core.config import Settings

        settings = Settings()
        assert settings.app_name == "Asterion"
        assert settings.app_version == "0.2.0"
        assert settings.api_prefix == "/api/v1"
        assert settings.database_url == "sqlite:///./asterion.db"
        assert settings.log_level == "INFO"
        assert settings.debug is False
        assert settings.cors_origins == ["*"]


def test_override_settings():
    # Patch environment with custom variables
    custom_env = {
        "APP_NAME": "TestApp",
        "APP_VERSION": "2.0.0",
        "API_PREFIX": "/api/v2",
        "DATABASE_URL": "sqlite:///./test.db",
        "LOG_LEVEL": "DEBUG",
        "DEBUG": "True",
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:8000",
    }
    with mock.patch.dict(os.environ, custom_env, clear=True):
        if "app.core.config" in sys.modules:
            importlib.reload(sys.modules["app.core.config"])
        from app.core.config import Settings

        settings = Settings()
        assert settings.app_name == "TestApp"
        assert settings.app_version == "2.0.0"
        assert settings.api_prefix == "/api/v2"
        assert settings.database_url == "sqlite:///./test.db"
        assert settings.log_level == "DEBUG"
        assert settings.debug is True
        assert settings.cors_origins == [
            "http://localhost:3000",
            "http://localhost:8000",
        ]
