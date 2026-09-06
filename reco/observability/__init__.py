"""Observability, execution tracing, and telemetry (Neatlogs adapter)."""

from reco.observability.tracer import (
    DEFAULT_INGEST_ENDPOINT,
    HELD_OUT_PROTECTED_KEYS,
    NeatlogsTracer,
    SpanContext,
    compute_prompt_hash,
    get_tracer,
    normalize_neatlogs_endpoint,
    sanitize_attributes,
    set_global_tracer,
)

__all__ = [
    "DEFAULT_INGEST_ENDPOINT",
    "HELD_OUT_PROTECTED_KEYS",
    "NeatlogsTracer",
    "SpanContext",
    "compute_prompt_hash",
    "get_tracer",
    "normalize_neatlogs_endpoint",
    "sanitize_attributes",
    "set_global_tracer",
]
