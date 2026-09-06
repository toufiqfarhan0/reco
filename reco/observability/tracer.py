"""Neatlogs observability tracer adapter and workflow execution tracing for Reco.

Provides hierarchical structured telemetry, agent execution spans, and optimization traces.
Strict architectural invariant: Observability failures must NEVER crash
agent execution, benchmark evaluation, or alter scorecard outcomes.
"""

from contextlib import contextmanager
from contextvars import ContextVar, Token
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
import re
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union
from uuid import UUID, uuid4

from reco.config import get_settings
from reco.core.interfaces import Tracer

if TYPE_CHECKING:
    from reco.optimization.events import OptimizationEvent, OptimizationEventType

logger = logging.getLogger("reco.observability.neatlogs")

# Sensitive key patterns that must never be sent in telemetry payloads
SENSITIVE_KEY_PATTERNS = re.compile(
    r"(?:key|secret|token|password|auth|credential|bearer|private)",
    re.IGNORECASE,
)

# Protected held-out dataset attributes that must never leak to telemetry
HELD_OUT_PROTECTED_KEYS = {
    "bank_records",
    "ledger_entries",
    "ground_truth",
    "expected_outcome",
    "expected_matches",
    "expected_discrepancies",
    "records",
    "entries",
    "discrepancies",
    "rule_violations",
    "input_data",
}

DEFAULT_INGEST_ENDPOINT = "https://ingest.neatlogs.com/v1/traces"

# ContextVar for hierarchical trace nesting across sync/async calls
_active_span_var: ContextVar[Optional["SpanContext"]] = ContextVar("active_span_var", default=None)
_global_tracer: Optional["NeatlogsTracer"] = None


def normalize_neatlogs_endpoint(url: Optional[str]) -> str:
    """Normalize a base URL or endpoint into the OTLP traces endpoint."""
    raw = (url or "").strip().rstrip("/")
    if not raw or "api.neatlogs.com" in raw:
        return DEFAULT_INGEST_ENDPOINT
    if raw.endswith("/v1/traces"):
        return raw
    return f"{raw}/v1/traces"


def compute_prompt_hash(prompt: Optional[str]) -> str:
    """Compute a deterministic short SHA-256 hash of a prompt for privacy."""
    if not prompt:
        return "empty"
    return hashlib.sha256(str(prompt).encode("utf-8")).hexdigest()[:16]


ALLOWED_METRIC_KEYS = {
    "tokens_in",
    "tokens_out",
    "total_tokens",
    "prompt_tokens",
    "completion_tokens",
    "token_count_delta",
    "token_count",
    "duration_ms",
    "latency_ms",
    "cost_usd",
}


def sanitize_attributes(
    attrs: Optional[Dict[str, Any]],
    is_held_out: bool = False,
) -> Dict[str, Any]:
    """Sanitize attributes dictionary to prevent secret or sensitive data leakage.

    If is_held_out is True, all ground-truth and raw benchmark data are purged.
    """
    if not attrs:
        return {}
    clean: Dict[str, Any] = {}
    for k, v in attrs.items():
        k_str = str(k)
        if k_str not in ALLOWED_METRIC_KEYS and SENSITIVE_KEY_PATTERNS.search(k_str):
            continue
        if is_held_out and k_str in HELD_OUT_PROTECTED_KEYS:
            continue
        v_str = str(v)
        # Prevent accidental secret pattern leaks in values
        if "sk-" in v_str or "v8_" in v_str or "Bearer " in v_str:
            continue
        # Truncate overly long values
        if isinstance(v, (int, float, bool)):
            clean[k_str] = v
        elif isinstance(v, (str, UUID)):
            clean[k_str] = str(v)[:500]
        elif isinstance(v, (list, dict)):
            clean[k_str] = str(v)[:500]
        else:
            clean[k_str] = v_str[:500]
    return clean


class SpanContext:
    """Hierarchical span context manager conforming to Reco execution tracing."""

    def __init__(
        self,
        name: str,
        tracer: "NeatlogsTracer",
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional["SpanContext"] = None,
    ):
        self.span_id: str = str(uuid4())
        self.name = name
        self.tracer = tracer
        self.parent = parent
        self.attributes: Dict[str, Any] = sanitize_attributes(attributes)
        self.attributes["span_id"] = self.span_id
        if self.parent:
            self.attributes["parent_span"] = self.parent.name
            self.attributes["parent_span_id"] = getattr(self.parent, "span_id", None)
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.duration_ms: int = 0
        self.is_active: bool = True
        self._otel_span = None
        self._token: Optional[Token] = None
        self._otel_token = None

    def set_attribute(self, key: str, value: Any) -> "SpanContext":
        """Set a single attribute safely."""
        sanitized = sanitize_attributes({key: value})
        if sanitized:
            self.attributes.update(sanitized)
            if self._otel_span is not None and hasattr(self._otel_span, "set_attribute"):
                try:
                    for sk, sv in sanitized.items():
                        self._otel_span.set_attribute(sk, sv)
                except Exception:
                    pass
        return self

    def end(self) -> None:
        """End the span, calculate latency, export telemetry, and record in trace history."""
        if not self.is_active:
            return
        self.is_active = False
        self.end_time = time.time()
        self.duration_ms = int((self.end_time - self.start_time) * 1000)
        if "duration_ms" not in self.attributes:
            self.attributes["duration_ms"] = self.duration_ms

        if self._otel_span is not None:
            try:
                self._otel_span.end()
            except Exception as exc:
                logger.warning("Failed to end OTel span: %s", exc)
                self.tracer.stats["errors"] += 1

        # Reset active ContextVar token if set
        if self._token is not None:
            try:
                _active_span_var.reset(self._token)
            except Exception:
                pass
            self._token = None

        # Record span in internal trace history
        self.tracer.record_span_history({
            "span_id": self.span_id,
            "parent_span_id": getattr(self.parent, "span_id", None),
            "name": self.name,
            "duration_ms": self.attributes.get("duration_ms", self.duration_ms),
            "parent_span": self.parent.name if self.parent else None,
            "attributes": dict(self.attributes),
            "timestamp": self.start_time,
        })


    def __enter__(self) -> "SpanContext":
        if self._token is None:
            self._token = _active_span_var.set(self)
        if self.tracer.enabled and self.tracer._tracer is not None and self._otel_span is None:
            try:
                import opentelemetry.trace as otel_trace
                ctx = None
                if self.parent and self.parent._otel_span:
                    ctx = otel_trace.set_span_in_context(self.parent._otel_span)
                self._otel_span = self.tracer._tracer.start_span(self.name, context=ctx)
                for k, v in self.attributes.items():
                    self._otel_span.set_attribute(k, v)
                self.tracer.stats["spans_exported"] += 1
            except Exception as exc:
                logger.warning("Neatlogs start_span error contained: %s", exc)
                self.tracer.stats["errors"] += 1
                self.tracer.stats["last_error"] = str(exc)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.attributes["status"] = "error"
            self.attributes["error.type"] = exc_type.__name__
            self.attributes["error.message"] = str(exc_val)[:200]
        else:
            if "status" not in self.attributes:
                self.attributes["status"] = "ok"

        self.end()


from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExportResult


class SafeSpanProcessor(SimpleSpanProcessor):
    """Span processor that intercepts exporter failures and safely tracks them in tracer stats."""

    def __init__(self, span_exporter: Any, tracer: "NeatlogsTracer"):
        super().__init__(span_exporter)
        self.tracer = tracer

    def on_end(self, span: Any) -> None:
        try:
            res = self.span_exporter.export((span,))
            if res == SpanExportResult.FAILURE:
                self.tracer.stats["errors"] += 1
                self.tracer.stats["last_error"] = "OTLP export returned failure"
        except Exception as exc:
            self.tracer.stats["errors"] += 1
            self.tracer.stats["last_error"] = str(exc)
            logger.warning("Telemetry export failure contained: %s", exc)


class NeatlogsTracer(Tracer):
    """Neatlogs observability tracer adapter.

    Conforms to `reco.core.interfaces.Tracer`.
    Guarantees strict failure containment and no global coupling.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout_seconds: float = 5.0,
        service_name: str = "reco",
        otel_exporter: Optional[Any] = None,
    ):
        settings = get_settings()

        # Resolve enabled flag: explicit arg takes precedence, then settings
        if enabled is not None:
            self.enabled: bool = bool(enabled)
        else:
            self.enabled = bool(settings.observability_enabled)

        # Resolve credentials
        self.api_key: str = (api_key if api_key is not None else settings.neatlogs_api_key) or ""
        if not self.api_key:
            # If no API key is provided, disable network export safely
            self.enabled = False

        self.base_url: str = (base_url if base_url is not None else settings.neatlogs_base_url) or ""
        self.endpoint: str = normalize_neatlogs_endpoint(self.base_url)
        self.timeout_seconds: float = max(0.5, float(timeout_seconds))
        self.service_name: str = service_name

        # Internal telemetry statistics
        self.stats: Dict[str, Any] = {
            "spans_started": 0,
            "spans_exported": 0,
            "events_logged": 0,
            "metrics_recorded": 0,
            "errors": 0,
            "last_error": None,
        }

        # In-memory recorded spans history for inspection and demo generation
        self.recorded_spans: List[Dict[str, Any]] = []

        # Lazy OpenTelemetry provider setup
        self._otel_exporter = otel_exporter
        self._provider = None
        self._tracer = None

        if self.enabled:
            self._init_otel_pipeline()

    def _init_otel_pipeline(self) -> None:
        """Initialize OpenTelemetry tracer pipeline with failure containment."""
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider

            resource = Resource.create({"service.name": self.service_name})
            self._provider = TracerProvider(resource=resource)

            if self._otel_exporter is not None:
                exporter = self._otel_exporter
            else:
                exporter = OTLPSpanExporter(
                    endpoint=self.endpoint,
                    headers={"x-api-key": self.api_key},
                    timeout=int(self.timeout_seconds),
                )

            self._provider.add_span_processor(SafeSpanProcessor(exporter, tracer=self))
            self._tracer = self._provider.get_tracer(self.service_name)
        except Exception as exc:
            logger.warning("Neatlogs OTel pipeline initialization failed: %s", exc)
            self.stats["errors"] += 1
            self.stats["last_error"] = str(exc)
            self._tracer = None

    def record_span_history(self, span_data: Dict[str, Any]) -> None:
        """Record span metadata in internal circular buffer (capped at 500)."""
        if len(self.recorded_spans) >= 500:
            self.recorded_spans.pop(0)
        self.recorded_spans.append(span_data)

    def get_recorded_spans(self) -> List[Dict[str, Any]]:
        """Return a copy of all recorded spans."""
        return list(self.recorded_spans)

    def clear_recorded_spans(self) -> None:
        """Clear recorded spans buffer."""
        self.recorded_spans.clear()

    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> SpanContext:
        """Begin an execution trace span with automatic hierarchy tracking."""
        self.stats["spans_started"] += 1
        parent = _active_span_var.get()
        return SpanContext(name=name, tracer=self, attributes=attributes, parent=parent)

    def start_active_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> SpanContext:
        """Start a span and activate it in context immediately until .end() is called."""
        span_ctx = self.start_span(name=name, attributes=attributes)
        span_ctx.__enter__()
        return span_ctx

    def log_event(
        self,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a telemetry event conforming to Tracer.log_event."""
        self.stats["events_logged"] += 1
        attrs = sanitize_attributes(payload)
        attrs["event_name"] = event_name

        try:
            with self.start_span(f"event.{event_name}", attributes=attrs):
                pass
        except Exception as exc:
            logger.warning("Neatlogs log_event error contained: %s", exc)
            self.stats["errors"] += 1
            self.stats["last_error"] = str(exc)

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "count",
    ) -> None:
        """Record an analytical metric conforming to Tracer.record_metric."""
        self.stats["metrics_recorded"] += 1
        attrs = {
            "metric.name": name,
            "metric.value": float(value),
            "metric.unit": unit,
        }
        try:
            with self.start_span(f"metric.{name}", attributes=attrs):
                pass
        except Exception as exc:
            logger.warning("Neatlogs record_metric error contained: %s", exc)
            self.stats["errors"] += 1
            self.stats["last_error"] = str(exc)

    def emit_event(
        self,
        event: Union[Any, Dict[str, Any], str],
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Emit a structured event to Neatlogs.

        Reuses `reco.optimization.events.OptimizationEvent` where practical.
        """
        is_opt_event = False
        try:
            from reco.optimization.events import OptimizationEvent
            is_opt_event = isinstance(event, OptimizationEvent)
        except Exception:
            is_opt_event = hasattr(event, "event_type") and hasattr(event, "experiment_id")

        if is_opt_event:
            span_name = f"optimization.{event.event_type.value}"
            attrs: Dict[str, Any] = {
                "project": "reco",
                "event_id": str(event.event_id),
                "event_type": event.event_type.value,
                "experiment_id": str(event.experiment_id),
            }
            if event.generation_number is not None:
                attrs["generation_number"] = event.generation_number
            if event.parent_version_id is not None:
                attrs["parent_version_id"] = str(event.parent_version_id)
            if event.candidate_id is not None:
                attrs["candidate_id"] = str(event.candidate_id)
            if event.payload:
                safe_payload = sanitize_attributes(event.payload)
                for pk, pv in safe_payload.items():
                    attrs[f"payload.{pk}"] = pv
        elif isinstance(event, dict):
            span_name = str(event.get("event", "reco_event"))
            attrs = sanitize_attributes(event)
        else:
            span_name = str(event)
            attrs = sanitize_attributes(payload)

        try:
            with self.start_span(span_name, attributes=attrs) as span:
                return {
                    "success": True,
                    "event": span_name,
                    "duration_ms": span.duration_ms,
                    "attributes": attrs,
                }
        except Exception as exc:
            logger.warning("Neatlogs emit_event error contained: %s", exc)
            self.stats["errors"] += 1
            self.stats["last_error"] = str(exc)
            return {"success": False, "error": str(exc), "event": span_name}

    def as_optimization_listener(self) -> Callable[[Any], None]:
        """Return an event listener callback for OptimizationEventDispatcher."""
        def _listener(event: Any) -> None:
            self.emit_event(event)

        return _listener

    def send_smoke_test(
        self,
        environment: str = "smoke_test",
    ) -> Dict[str, Any]:
        """Send exactly ONE small test span to Neatlogs for live smoke testing."""
        if not self.enabled:
            return {
                "success": False,
                "error": "Observability is disabled (OBSERVABILITY_ENABLED=false)",
                "status_code": 0,
                "latency_ms": 0,
            }

        safe_metadata = {
            "project": "reco",
            "environment": environment,
            "event": "neatlogs_connection_test",
            "status": "ok",
        }

        t0 = time.time()
        try:
            with self.start_span("neatlogs_connection_test", attributes=safe_metadata) as span:
                pass
            latency_ms = int((time.time() - t0) * 1000)
            return {
                "success": True,
                "status_code": 200,
                "latency_ms": latency_ms,
                "endpoint": self.endpoint,
                "metadata": safe_metadata,
            }
        except Exception as exc:
            latency_ms = int((time.time() - t0) * 1000)
            logger.warning("Live smoke test error contained: %s", exc)
            self.stats["errors"] += 1
            self.stats["last_error"] = str(exc)
            return {
                "success": False,
                "error": str(exc),
                "status_code": getattr(exc, "status_code", 500),
                "latency_ms": latency_ms,
                "endpoint": self.endpoint,
            }

    def send_structured_trace(
        self,
        trace_data: Dict[str, Any],
        endpoint_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a structured nested JSON trace to Neatlogs (POST /v1/trace).

        Guarantees strict failure containment.
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Observability disabled (OBSERVABILITY_ENABLED=false)",
                "status_code": 0,
            }
        url = endpoint_url or "https://ingest.neatlogs.com/v1/trace"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "x-api-key": self.api_key,
        }
        try:
            import requests
            r = requests.post(url, headers=headers, json=trace_data, timeout=self.timeout_seconds)
            if r.status_code == 200:
                res_data = r.json()
                spans_cnt = res_data.get("spans", 1)
                self.stats["spans_exported"] += spans_cnt
                return {
                    "success": True,
                    "status_code": 200,
                    "trace_id": res_data.get("trace_id"),
                    "spans": spans_cnt,
                }
            else:
                self.stats["errors"] += 1
                self.stats["last_error"] = f"HTTP {r.status_code}: {r.text[:200]}"
                return {
                    "success": False,
                    "status_code": r.status_code,
                    "error": r.text[:200],
                }
        except Exception as exc:
            logger.warning("Neatlogs send_structured_trace error contained: %s", exc)
            self.stats["errors"] += 1
            self.stats["last_error"] = str(exc)
            return {
                "success": False,
                "status_code": getattr(exc, "status_code", 0),
                "error": str(exc),
            }

    def build_trace_hierarchy_from_spans(self, root_name: str = "optimization_run") -> Dict[str, Any]:
        """Convert recorded flat spans into a nested tree conforming to Neatlogs JSON schema."""
        spans = list(self.recorded_spans)
        if not spans:
            return {"name": root_name, "project": self.service_name, "children": []}

        # Index spans by parent_span_id
        by_parent_id: Dict[Optional[str], List[Dict[str, Any]]] = {}
        visited: set = set()
        for s in spans:
            parent_id = s.get("parent_span_id")
            by_parent_id.setdefault(parent_id, []).append(s)

        def _build_node(s: Dict[str, Any]) -> Dict[str, Any]:
            s_id = s.get("span_id")
            if s_id and s_id in visited:
                return {}
            if s_id:
                visited.add(s_id)

            node_name = s.get("name", "span")
            node: Dict[str, Any] = {
                "name": node_name,
                "duration_ms": s.get("duration_ms", 0),
                "attributes": sanitize_attributes(s.get("attributes", {})),
            }
            # Infer span kind for Neatlogs
            if "model_invocation" in node_name:
                node["kind"] = "LLM"
                if "model_name" in node["attributes"]:
                    node["model"] = node["attributes"]["model_name"]
            elif "tool_invocation" in node_name or "tool" in node_name:
                node["kind"] = "TOOL"
                if "tool_name" in node["attributes"]:
                    node["tool_name"] = node["attributes"]["tool_name"]
            elif "benchmark" in node_name or "eval" in node_name:
                node["kind"] = "EVALUATOR"
            elif "guardrail" in node_name or "promotion" in node_name or "comparison" in node_name:
                node["kind"] = "GUARDRAIL"
            elif "generation" in node_name:
                node["kind"] = "CHAIN"
            else:
                node["kind"] = "TASK"

            child_spans = by_parent_id.get(s_id, [])
            if child_spans:
                node["children"] = [
                    _build_node(c) for c in child_spans
                    if not c.get("span_id") or c.get("span_id") not in visited
                ]
            return node

        roots = by_parent_id.get(None, [])
        if roots:
            root_node = _build_node(roots[0])
            root_node["project"] = self.service_name
            if len(roots) > 1:
                root_node.setdefault("children", []).extend([
                    _build_node(r) for r in roots[1:]
                    if not r.get("span_id") or r.get("span_id") not in visited
                ])
            return root_node
        else:
            return {
                "name": root_name,
                "project": self.service_name,
                "children": [_build_node(s) for s in spans[:30]],
            }

    def trace_model_invocation(
        self,
        model_name: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        latency_ms: int = 0,
        cost_usd: float = 0.0,
        experiment_id: str = "",
        agent_version_id: str = "",
        node_id: str = "",
        status: str = "ok",
    ) -> SpanContext:
        """Trace a model invocation span safely."""
        attrs = {
            "model_name": model_name,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "total_tokens": tokens_in + tokens_out,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "experiment_id": experiment_id,
            "agent_version_id": agent_version_id,
            "node_id": node_id,
            "status": status,
        }
        return self.start_span("model_invocation", attributes=attrs)

    def trace_tool_invocation(
        self,
        tool_name: str,
        duration_ms: int = 0,
        success: bool = True,
        experiment_id: str = "",
        agent_version_id: str = "",
        node_id: str = "",
    ) -> SpanContext:
        """Trace a tool invocation span safely."""
        attrs = {
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
            "experiment_id": experiment_id,
            "agent_version_id": agent_version_id,
            "node_id": node_id,
            "status": "ok" if success else "error",
        }
        return self.start_span(f"tool_invocation.{tool_name}", attributes=attrs)

    def trace_node_execution(
        self,
        node_id: str,
        execution_mode: str = "deterministic_tool",
        experiment_id: str = "",
        agent_version_id: str = "",
    ) -> SpanContext:
        """Trace a node execution span safely."""
        attrs = {
            "node_id": node_id,
            "execution_mode": execution_mode,
            "experiment_id": experiment_id,
            "agent_version_id": agent_version_id,
        }
        return self.start_span(f"node_execution.{node_id}", attributes=attrs)

    def trace_benchmark_case(
        self,
        case_code: str,
        split: str,
        experiment_id: str = "",
        agent_version_id: str = "",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> SpanContext:
        """Trace a single benchmark case evaluation with held-out privacy protection."""
        is_held_out = (split.lower() == "held_out")
        attrs = {
            "case_code": case_code,
            "split": split,
            "is_held_out": is_held_out,
            "experiment_id": experiment_id,
            "agent_version_id": agent_version_id,
        }
        if attributes:
            safe_extra = sanitize_attributes(attributes, is_held_out=is_held_out)
            attrs.update(safe_extra)
        return self.start_span(f"benchmark_case.{case_code}", attributes=attrs)

    def trace_failure_diagnosis(
        self,
        diagnosis_id: str,
        category: str,
        severity: str,
        failed_node: str,
        confidence: float,
        case_code: str = "",
        experiment_id: str = "",
        generation_number: Optional[int] = None,
        agent_version_id: str = "",
    ) -> None:
        """Log a failure diagnosis event without raw case contents."""
        payload = {
            "diagnosis_id": diagnosis_id,
            "category": category,
            "severity": severity,
            "failed_node": failed_node,
            "confidence": confidence,
            "case_code": case_code,
            "experiment_id": experiment_id,
            "generation_number": generation_number,
            "agent_version_id": agent_version_id,
        }
        self.log_event("diagnosis_created", payload=payload)

    def trace_mutation(
        self,
        candidate_id: str,
        parent_version_id: str,
        mutation_type: str,
        target: str,
        prompt_hash: str = "",
        change_summary: str = "",
        token_count_delta: int = 0,
        experiment_id: str = "",
        generation_number: Optional[int] = None,
        prompt_text: Optional[str] = None,
    ) -> None:
        """Log a candidate mutation event using prompt hash rather than full prompt."""
        if not prompt_hash and prompt_text:
            prompt_hash = compute_prompt_hash(prompt_text)
        payload = {
            "candidate_id": candidate_id,
            "parent_version_id": parent_version_id,
            "mutation_type": mutation_type,
            "target": target,
            "prompt_hash": prompt_hash,
            "change_summary": change_summary,
            "token_count_delta": token_count_delta,
            "experiment_id": experiment_id,
            "generation_number": generation_number,
        }
        self.log_event("candidate_generated", payload=payload)

    def trace_candidate_generated(
        self,
        candidate_id: str,
        parent_version_id: str,
        mutation_type: str,
        target: str,
        generation: Optional[int] = None,
        experiment_id: str = "",
        prompt_text: Optional[str] = None,
    ) -> None:
        """Trace candidate generation with prompt hash (no raw prompt leak)."""
        prompt_hash = compute_prompt_hash(prompt_text) if prompt_text else ""
        payload = {
            "candidate_id": candidate_id,
            "parent_version_id": parent_version_id,
            "mutation_type": mutation_type,
            "target": target,
            "prompt_hash": prompt_hash,
            "generation": generation,
            "experiment_id": experiment_id,
        }
        self.log_event("candidate_generated", payload=payload)

    def trace_candidate_benchmarked(
        self,
        candidate_id: str,
        parent_version_id: str,
        generation: Optional[int] = None,
        accuracy: float = 0.0,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
        relationship: str = "equivalent",
        experiment_id: str = "",
    ) -> None:
        """Trace candidate benchmark outcome."""
        payload = {
            "candidate_id": candidate_id,
            "parent_version_id": parent_version_id,
            "generation": generation,
            "accuracy": accuracy,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "relationship": relationship,
            "experiment_id": experiment_id,
        }
        self.log_event("candidate_benchmarked", payload=payload)

    def trace_candidate_selected(
        self,
        candidate_id: str,
        parent_version_id: str,
        generation: Optional[int] = None,
        mutation_type: str = "",
        accuracy_delta: float = 0.0,
        experiment_id: str = "",
    ) -> None:
        """Trace selection of winning candidate."""
        payload = {
            "candidate_id": candidate_id,
            "parent_version_id": parent_version_id,
            "generation": generation,
            "mutation_type": mutation_type,
            "accuracy_delta": accuracy_delta,
            "experiment_id": experiment_id,
        }
        self.log_event("candidate_selected", payload=payload)

    def trace_candidate_rejected(
        self,
        candidate_id: str,
        parent_version_id: str,
        generation: Optional[int] = None,
        reason: str = "",
        experiment_id: str = "",
    ) -> None:
        """Trace rejection of non-winning or invalid candidate."""
        payload = {
            "candidate_id": candidate_id,
            "parent_version_id": parent_version_id,
            "generation": generation,
            "reason": reason,
            "experiment_id": experiment_id,
        }
        self.log_event("candidate_rejected", payload=payload)

    def trace_promotion(
        self,
        experiment_id: str,
        parent_version_id: str,
        final_version_id: str,
        decision: str,
        promoted: bool,
        accuracy_delta: float = 0.0,
        cost_delta: float = 0.0,
        latency_delta: int = 0,
        reliability_delta: float = 0.0,
        improved_dimensions: Optional[List[str]] = None,
        regressed_dimensions: Optional[List[str]] = None,
    ) -> None:
        """Log a promotion assessment event."""
        payload = {
            "experiment_id": experiment_id,
            "parent_version_id": parent_version_id,
            "final_version_id": final_version_id,
            "decision": decision,
            "promoted": promoted,
            "accuracy_delta": accuracy_delta,
            "cost_delta": cost_delta,
            "latency_delta": latency_delta,
            "reliability_delta": reliability_delta,
            "improved_dimensions": improved_dimensions or [],
            "regressed_dimensions": regressed_dimensions or [],
        }
        self.log_event("promotion_assessed", payload=payload)

    def export_trace_demo(self, output_path: str) -> None:
        """Export safe demo trace JSON artifact."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        hierarchy = self.build_trace_hierarchy_from_spans()
        demo_payload = {
            "project": "reco",
            "track": "Track 1 — Automated Agent Engineering",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_spans": len(self.recorded_spans),
            "stats": dict(self.stats),
            "trace_tree": hierarchy,
            "spans": self.get_recorded_spans(),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(demo_payload, f, indent=2)


def get_tracer() -> NeatlogsTracer:
    """Get the active global NeatlogsTracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = NeatlogsTracer()
    return _global_tracer


def set_global_tracer(tracer: Optional[NeatlogsTracer]) -> None:
    """Override or reset the active global NeatlogsTracer instance."""
    global _global_tracer
    _global_tracer = tracer
