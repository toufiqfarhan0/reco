"""Pytest fixtures for Reco tests."""

import pytest
from fastapi.testclient import TestClient

from reco.api.app import create_app
from reco.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Provide clean isolated test settings."""
    return Settings(
        _env_file=None,
        app_env="test",
        log_level="WARNING",
        supabase_url="",
        supabase_key="",
        llm_provider="mock",
        llm_model="mock-v1",
        tensormux_api_key="",
        billing_enabled=False,
        observability_enabled=False,
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    """Provide FastAPI TestClient configured for testing."""
    test_app = create_app(settings=test_settings)
    with TestClient(test_app) as test_client:
        yield test_client
