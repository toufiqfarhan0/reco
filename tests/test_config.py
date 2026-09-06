"""Tests for Reco configuration loading and validation."""

import pytest
from pydantic import ValidationError
from reco.config import Settings, get_settings


def test_default_settings():
    """Verify default development configuration."""
    settings = Settings(_env_file=None)
    assert settings.app_env in ["development", "staging", "production", "test"]
    assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert settings.llm_provider == "mock"
    assert settings.billing_enabled is True
    assert settings.observability_enabled is True
    assert settings.port == 8000



def test_settings_cached_singleton():
    """Verify get_settings returns consistent cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_custom_settings_override():
    """Verify explicit settings instantiation overrides defaults."""
    custom = Settings(
        app_env="production",
        log_level="ERROR",
        llm_provider="tensormux",
        billing_enabled=True,
    )
    assert custom.app_env == "production"
    assert custom.log_level == "ERROR"
    assert custom.llm_provider == "tensormux"
    assert custom.billing_enabled is True


def test_aliases_for_billing_and_observability():
    """Verify uppercase and lowercase alias parsing for billing and observability flags."""
    cfg1 = Settings(_env_file=None, BILLING_ENABLED="false", OBSERVABILITY_ENABLED="false")
    assert cfg1.billing_enabled is False
    assert cfg1.observability_enabled is False

    cfg2 = Settings(_env_file=None, billing_enabled=True, observability_enabled=True)
    assert cfg2.billing_enabled is True
    assert cfg2.observability_enabled is True



def test_invalid_env_validation():
    """Verify invalid app_env raises Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        Settings(app_env="invalid_environment")  # type: ignore


def test_invalid_log_level_validation():
    """Verify invalid log_level raises Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        Settings(log_level="VERBOSE")  # type: ignore
