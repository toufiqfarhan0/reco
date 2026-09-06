"""Factory for instantiating ModelGateway adapters based on configuration."""

from typing import Any, Optional
from reco.config import Settings, get_settings
from reco.core.interfaces import ModelGateway
from reco.llm.mock import MockModelGateway
from reco.llm.tensormux import TensorMuxGateway


def get_model_gateway(
    provider: Optional[str] = None,
    settings: Optional[Settings] = None,
    **kwargs: Any,
) -> ModelGateway:
    """Instantiate a ModelGateway adapter according to the requested or configured provider.

    Default is 'mock' for offline, deterministic execution.
    """
    app_settings = settings or get_settings()
    active_provider = (provider or app_settings.llm_provider).lower()

    if active_provider == "tensormux":
        return TensorMuxGateway(
            api_key=kwargs.get("api_key", app_settings.tensormux_api_key),
            base_url=kwargs.get("base_url", app_settings.tensormux_base_url),
            default_model=kwargs.get("default_model", app_settings.llm_model),
            timeout_seconds=kwargs.get("timeout_seconds", 30.0),
            http_client=kwargs.get("http_client"),
        )
    elif active_provider == "mock":
        return MockModelGateway(**kwargs)
    else:
        # Fallback to mock for unknown provider to maintain safety
        return MockModelGateway(**kwargs)
