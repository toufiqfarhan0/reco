"""Centralized configuration management for Reco using Pydantic Settings."""

from functools import lru_cache
from typing import Literal
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading and validation."""

    # Application Core
    app_name: str = "Reco — Autonomous Agent Engineering System"
    app_version: str = "0.1.0"
    hackathon_track: str = "Automated Agent Engineering"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000

    # Database (Supabase PostgreSQL)
    supabase_url: str = Field(
        default="",
        validation_alias=AliasChoices("supabase_url", "NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_URL"),
        description="Supabase project URL",
    )
    supabase_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "supabase_key",
            "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
            "SUPABASE_ANON_KEY",
            "SUPABASE_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
        ),
        description="Supabase anon, publishable, or service-role key",
    )

    # LLM Gateway
    llm_provider: str = Field(default="mock", description="Active LLM gateway (mock, tensormux, litellm, openai)")
    llm_model: str = Field(default="glm-4-7-flash", description="Default model identifier")

    # TensorMux Inference Gateway (Optional)
    tensormux_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("tensormux_api_key", "TENSORMUX_API_KEY"),
        description="TensorMux API Key",
    )
    tensormux_base_url: str = Field(
        default="https://api.tensormux.com/v1",
        validation_alias=AliasChoices("tensormux_base_url", "TENSORMUX_BASE_URL"),
        description="TensorMux endpoint",
    )

    # Neatlogs Observability (Optional)
    observability_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("observability_enabled", "OBSERVABILITY_ENABLED"),
        description="Whether Neatlogs tracing is active",
    )
    neatlogs_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("neatlogs_api_key", "NEATLOGS_API_KEY"),
        description="Neatlogs API Key",
    )
    neatlogs_base_url: str = Field(
        default="https://ingest.neatlogs.com",
        validation_alias=AliasChoices("neatlogs_base_url", "NEATLOGS_BASE_URL"),
        description="Neatlogs API endpoint",
    )
    neatlogs_timeout_seconds: float = Field(default=5.0, description="Neatlogs HTTP timeout in seconds")

    # Dodo Payments Billing (Step 27)
    billing_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("billing_enabled", "BILLING_ENABLED"),
        description="Whether Dodo Payments billing is enforced",
    )
    dodo_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("dodo_api_key", "DODO_PAYMENTS_API_KEY", "DODO_API_KEY"),
        description="Dodo Payments secret key",
    )
    dodo_webhook_secret: str = Field(
        default="",
        validation_alias=AliasChoices(
            "dodo_webhook_secret",
            "DODO_PAYMENTS_WEBHOOK_KEY",
            "DODO_WEBHOOK_SECRET",
            "DODO_PAYMENTS_WEBHOOK_SECRET",
        ),
        description="Dodo Payments webhook secret",
    )
    dodo_environment: str = Field(
        default="test_mode",
        validation_alias=AliasChoices("dodo_environment", "DODO_PAYMENTS_ENVIRONMENT", "DODO_ENVIRONMENT"),
        description="Dodo Payments environment ('test_mode' or 'live_mode')",
    )
    dodo_product_id: str = Field(
        default="pdt_0Nmvzbo4wJETkRyCMAEPt",
        validation_alias=AliasChoices("dodo_product_id", "DODO_PAYMENTS_PRODUCT_ID", "DODO_PRODUCT_ID"),
        description="Existing Reco Pro product ID",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def OBSERVABILITY_ENABLED(self) -> bool:
        return self.observability_enabled



@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
