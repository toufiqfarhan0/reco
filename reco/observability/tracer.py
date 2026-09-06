"""Neatlogs Distributed Tracer for Autonomous Agent System (Track 1).

Implements end-to-end hierarchical distributed tracing across agent runs:
optimization_run -> generation_N -> candidate_eval -> node_execution -> tool_invocation.

Features:
- Non-blocking, fault-tolerant telemetry exporter connecting to https://ingest.neatlogs.com.
- Full span metadata capture: start/end timestamps, duration, status, model parameters,
  token usage, tool arguments, and outputs.
- Fault containment: If Neatlogs ingest fails or times out, core agent execution proceeds
  completely uninterrupted ($0 failure impact).
- Deep-link generation to inspect execution traces in the Neatlogs UI (https://app.neatlogs.com/traces/<trace_id>).
- In-memory trace buffer for instant inspection, frontend hydration, and deterministic verification.
"""

from __future__ import annotations

from contextlib import contextmanager
import contextvars
from datetime import datetime, timezone
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
import httpx
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# Default Constants
DEFAULT_NEATLOGS_INGEST_URL = "https://ingest.neatlogs.com"
DEFAULT_NEATLOGS_APP_URL = "https://app.neatlogs.com"


class NeatlogsSpan(BaseModel):
    """Encapsulates a single telemetry span in the distributed execution graph."""

    model_config = ConfigDict(extra="ignore")

    span_id: str = Field(
        default_factory=lambda: f"sp_{uuid.uuid4().hex[:12]}",
        description="Unique span identifier"
    )
    trace_id: str = Field(description="Trace ID this span belongs to")
    parent_span_id: Optional[str] = Field(
        default=None,
        description="Parent span ID establishing hierarchical lineage"
    )
    name: str = Field(description="Human-readable span label")
    kind: str = Field(
        default="node_execution",
        description="Span kind: optimization_run, generation_N, candidate_eval, node_execution, tool_invocation, etc."
    )
    status: str = Field(default="ok", description="Status outcome: 'ok', 'error', or 'warn'")
    start_time: float = Field(
        default_factory=time.time,
        description="Unix epoch start timestamp (seconds)"
    )
    end_time: Optional[float] = Field(default=None, description="Unix epoch end timestamp (seconds)")
    start_offset_ms: float = Field(
        default=0.0,
        description="Start offset in milliseconds relative to root trace start"
    )
    duration_ms: float = Field(default=0.0, description="Span duration in milliseconds")
    tokens: int = Field(default=0, description="Total tokens consumed during this span")
    cost_usd: float = Field(default=0.0, description="Inference cost in USD for this span")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key-value metadata (model params, tool args, outputs, etc.)"
    )
    error: Optional[str] = Field(default=None, description="Error detail if status is 'error'")

    def set_attribute(self, key: str, value: Any) -> NeatlogsSpan:
        """Add or update an attribute entry."""
        self.attributes[key] = value
        return self

    def set_attributes(self, attrs: Dict[str, Any]) -> NeatlogsSpan:
        """Merge a dictionary of attributes into this span."""
        self.attributes.update(attrs)
        return self

    def set_tokens(self, tokens: int) -> NeatlogsSpan:
        """Set token consumption count."""
        self.tokens = max(0, int(tokens))
        return self

    def set_cost(self, cost_usd: float) -> NeatlogsSpan:
        """Set USD cost."""
        self.cost_usd = max(0.0, float(cost_usd))
        return self

    def set_status(self, status: str, error: Optional[str] = None) -> NeatlogsSpan:
        """Update span status and error message."""
        self.status = status
        if error:
            self.error = str(error)
            self.attributes["error"] = str(error)
        return self

    def end(self, status: Optional[str] = None, error: Optional[str] = None) -> None:
        """Finalize the span duration and status."""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration_ms = max(0.0, round((self.end_time - self.start_time) * 1000.0, 3))
        if status:
            self.status = status
        if error:
            self.error = str(error)
            self.attributes["error"] = str(error)

    def to_frontend_dict(self) -> Dict[str, Any]:
        """Serialize span to frontend-compatible format (matching NeatlogsSpan in TypeScript)."""
        # Map kind to valid frontend types: "dag" | "node" | "tool" | "verifier" | "llm"
        kind_mapping = {
            "optimization_run": "dag",
            "generation_N": "dag",
            "candidate_eval": "dag",
            "node_execution": "node",
            "tool_invocation": "tool",
            "verifier_invocation": "verifier",
            "llm_inference": "llm",
        }
        fe_kind = kind_mapping.get(self.kind, self.kind if self.kind in {"dag", "node", "tool", "verifier", "llm"} else "node")

        return {
            "span_id": self.span_id,
            "name": self.name,
            "kind": fe_kind,
            "status": self.status,
            "start_offset_ms": round(self.start_offset_ms, 1),
            "duration_ms": round(self.duration_ms, 1),
            "tokens": self.tokens,
            "cost_usd": round(self.cost_usd, 6),
            "attributes": self.attributes,
        }


class NeatlogsTrace(BaseModel):
    """Represents a complete distributed trace across hierarchical spans."""

    model_config = ConfigDict(extra="ignore")

    trace_id: str = Field(
        default_factory=lambda: f"tr_neat_{uuid.uuid4().hex[:12]}",
        description="Unique distributed trace identifier"
    )
    architecture_id: Optional[str] = Field(
        default=None,
        description="Architecture or candidate evaluated during trace"
    )
    status: str = Field(default="success", description="Overall outcome: 'success', 'warning', or 'error'")
    total_duration_ms: float = Field(default=0.0, description="Total wall-clock duration in milliseconds")
    total_tokens: int = Field(default=0, description="Sum of tokens across all child spans")
    total_cost_usd: float = Field(default=0.0, description="Sum of cost across all child spans")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO timestamp of trace initiation"
    )
    spans: List[NeatlogsSpan] = Field(default_factory=list, description="Ordered child spans in this trace")
    deep_link: str = Field(default="", description="Neatlogs UI inspect link")

    def add_span(self, span: NeatlogsSpan) -> None:
        """Append a span and update running trace aggregates."""
        self.spans.append(span)
        self.total_tokens += span.tokens
        self.total_cost_usd = round(self.total_cost_usd + span.cost_usd, 6)
        if span.status == "error":
            self.status = "error"
        elif span.status == "warn" and self.status != "error":
            self.status = "warning"

    def finalize(self, base_url: str = DEFAULT_NEATLOGS_APP_URL) -> NeatlogsTrace:
        """Compute final duration, totals, deep link, and preserve strict chronological span order."""
        if not self.deep_link:
            self.deep_link = f"{base_url.rstrip('/')}/traces/{self.trace_id}"
        if self.spans:
            # Sort spans chronologically so root span is first and child spans follow execution order
            self.spans.sort(key=lambda s: (s.start_time, s.start_offset_ms))
            start = min(s.start_time for s in self.spans)
            end = max((s.end_time or s.start_time) for s in self.spans)
            self.total_duration_ms = max(0.0, round((end - start) * 1000.0, 2))
            self.total_tokens = sum(s.tokens for s in self.spans)
            self.total_cost_usd = round(sum(s.cost_usd for s in self.spans), 6)
            if any(s.status == "error" for s in self.spans):
                self.status = "error"
        return self

    def to_frontend_dict(self) -> Dict[str, Any]:
        """Serialize trace to match frontend NeatlogsTrace specification."""
        self.finalize()
        return {
            "trace_id": self.trace_id,
            "architecture_id": self.architecture_id or "Agent_Execution",
            "status": self.status,
            "total_duration_ms": round(self.total_duration_ms, 1),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "timestamp": self.timestamp,
            "spans": [s.to_frontend_dict() for s in self.spans],
        }


# Context variables for thread-local & async hierarchical context propagation
_current_trace_var: contextvars.ContextVar[Optional[NeatlogsTrace]] = contextvars.ContextVar(
    "_current_trace_var", default=None
)
_span_stack_var: contextvars.ContextVar[List[NeatlogsSpan]] = contextvars.ContextVar(
    "_span_stack_var", default=[]
)


class NeatlogsTracer:
    """Non-blocking, fault-tolerant distributed tracer for Reco agent engineering.

    Connects to Neatlogs ingestion endpoint (https://ingest.neatlogs.com) and provides
    hierarchical span scoping, fault containment ($0 failure impact), and deep links.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        ingest_url: Optional[str] = None,
        app_url: Optional[str] = None,
        enabled: bool = True,
        async_export: bool = True,
        http_client: Optional[httpx.Client] = None,
        max_workers: int = 2,
    ):
        self.api_key = api_key or os.getenv("NEATLOGS_API_KEY", "")
        self.ingest_url = (
            ingest_url or os.getenv("NEATLOGS_INGEST_URL", DEFAULT_NEATLOGS_INGEST_URL)
        ).rstrip("/")
        self.app_url = (
            app_url or os.getenv("NEATLOGS_APP_URL", DEFAULT_NEATLOGS_APP_URL)
        ).rstrip("/")
        self.enabled = enabled
        self.async_export = async_export

        # In-memory buffer of exported telemetry for inspection and testing
        self.exported_traces: List[NeatlogsTrace] = []
        self.exported_spans: List[NeatlogsSpan] = []
        self._lock = threading.Lock()

        # Background worker pool for non-blocking HTTP ingestion
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="neatlogs_exporter"
        )
        self._pending_futures: List[Future] = []
        self._custom_client = http_client

    def get_trace_url(self, trace_id: str) -> str:
        """Generate direct deep-link URL to inspect the execution trace in the Neatlogs UI."""
        return f"{self.app_url}/traces/{trace_id}"

    @property
    def current_trace(self) -> Optional[NeatlogsTrace]:
        """Return the currently active trace, if any."""
        return _current_trace_var.get()

    @property
    def current_span(self) -> Optional[NeatlogsSpan]:
        """Return the top-of-stack active span in the current context."""
        stack = _span_stack_var.get()
        return stack[-1] if stack else None

    @contextmanager
    def start_trace(
        self,
        trace_id: Optional[str] = None,
        architecture_id: Optional[str] = None,
        name: str = "optimization_run",
        kind: str = "optimization_run",
        **attributes: Any
    ) -> Generator[NeatlogsTrace, None, None]:
        """Start a new root distributed trace context."""
        new_trace = NeatlogsTrace(
            trace_id=trace_id or f"tr_neat_{uuid.uuid4().hex[:12]}",
            architecture_id=architecture_id,
            deep_link=f"{self.app_url}/traces/{trace_id or ''}"
        )
        new_trace.deep_link = self.get_trace_url(new_trace.trace_id)

        token_trace = _current_trace_var.set(new_trace)
        token_stack = _span_stack_var.set([])

        try:
            with self.span(name, kind=kind, **attributes):
                yield new_trace
        finally:
            new_trace.finalize(self.app_url)
            self._export_trace(new_trace)
            _current_trace_var.reset(token_trace)
            _span_stack_var.reset(token_stack)

    @contextmanager
    def span(
        self,
        name: str,
        kind: str = "node_execution",
        tokens: int = 0,
        cost_usd: float = 0.0,
        **attributes: Any
    ) -> Generator[NeatlogsSpan, None, None]:
        """Context manager for hierarchical spans.

        Automatically links parent_span_id, tracks wall-clock latency, catches exceptions
        for error classification, and records telemetry without blocking agent flow.
        """
        active_trace = _current_trace_var.get()
        is_ad_hoc_trace = False

        if active_trace is None:
            # Create an automatic ad-hoc trace for standalone span execution
            active_trace = NeatlogsTrace(
                trace_id=f"tr_neat_{uuid.uuid4().hex[:12]}",
                architecture_id=attributes.get("architecture_id")
            )
            active_trace.deep_link = self.get_trace_url(active_trace.trace_id)
            _current_trace_var.set(active_trace)
            _span_stack_var.set([])
            is_ad_hoc_trace = True

        stack = list(_span_stack_var.get())
        parent_span = stack[-1] if stack else None

        now = time.time()
        start_offset = (now - stack[0].start_time) * 1000.0 if stack else 0.0

        span = NeatlogsSpan(
            trace_id=active_trace.trace_id,
            parent_span_id=parent_span.span_id if parent_span else None,
            name=name,
            kind=kind,
            start_time=now,
            start_offset_ms=max(0.0, round(start_offset, 2)),
            tokens=tokens,
            cost_usd=cost_usd,
            attributes=dict(attributes)
        )

        stack.append(span)
        _span_stack_var.set(stack)

        # Register span in start order immediately so root is first and children follow
        active_trace.spans.append(span)

        try:
            yield span
            span.end(status=span.status or "ok")
        except Exception as exc:
            span.end(status="error", error=str(exc))
            raise
        finally:
            # Pop this span from stack
            cur_stack = list(_span_stack_var.get())
            if cur_stack and cur_stack[-1].span_id == span.span_id:
                cur_stack.pop()
                _span_stack_var.set(cur_stack)

            # Update trace running aggregates and export span
            active_trace.total_tokens += span.tokens
            active_trace.total_cost_usd = round(active_trace.total_cost_usd + span.cost_usd, 6)
            if span.status == "error":
                active_trace.status = "error"
            elif span.status == "warn" and active_trace.status != "error":
                active_trace.status = "warning"
            self._export_span(span)

            # If this was an ad-hoc trace that just emptied its stack, finalize & export trace
            if is_ad_hoc_trace and not cur_stack:
                active_trace.finalize(self.app_url)
                self._export_trace(active_trace)
                _current_trace_var.set(None)

    # -------------------------------------------------------------------------
    # Dedicated Hierarchical Helper Context Managers
    # optimization_run -> generation_N -> candidate_eval -> node_execution -> tool_invocation
    # -------------------------------------------------------------------------

    def trace_optimization_run(
        self,
        name: str = "optimization_run",
        architecture_id: Optional[str] = None,
        **attributes: Any
    ):
        """Tier 1: Top-level autonomous closed-loop optimization run."""
        return self.start_trace(
            architecture_id=architecture_id,
            name=name,
            kind="optimization_run",
            **attributes
        )

    def trace_generation(self, generation: int, **attributes: Any):
        """Tier 2: Mutation generation cycle (generation_N)."""
        return self.span(
            name=f"generation_{generation}",
            kind="generation_N",
            generation=generation,
            **attributes
        )

    def trace_candidate_eval(
        self,
        candidate_name: str,
        split: str = "optimization",
        **attributes: Any
    ):
        """Tier 3: Evaluation of candidate architecture on benchmark partition."""
        return self.span(
            name=f"candidate_eval:{candidate_name}",
            kind="candidate_eval",
            candidate_name=candidate_name,
            split=split,
            **attributes
        )

    def trace_node_execution(
        self,
        node_id: str,
        node_type: str = "node",
        **attributes: Any
    ):
        """Tier 4: DAG node execution step."""
        return self.span(
            name=f"node_execution:{node_id}",
            kind="node_execution",
            node_id=node_id,
            node_type=node_type,
            **attributes
        )

    def trace_tool_invocation(
        self,
        tool_name: str,
        **attributes: Any
    ):
        """Tier 5: Execution of an atomic tool within a tool node."""
        return self.span(
            name=f"tool_invocation:{tool_name}",
            kind="tool_invocation",
            tool_name=tool_name,
            **attributes
        )

    # -------------------------------------------------------------------------
    # Telemetry Exporter with Fault Containment ($0 Failure Impact)
    # -------------------------------------------------------------------------

    def _export_span(self, span: NeatlogsSpan) -> None:
        """Store span in memory buffer."""
        with self._lock:
            self.exported_spans.append(span)

    def _export_trace(self, trace: NeatlogsTrace) -> None:
        """Dispatch trace to Neatlogs ingest endpoint without blocking execution."""
        with self._lock:
            self.exported_traces.append(trace)

        if not self.enabled:
            return

        if not self.api_key and not self._custom_client:
            return

        payload = {
            "trace_id": trace.trace_id,
            "architecture_id": trace.architecture_id,
            "status": trace.status,
            "total_duration_ms": trace.total_duration_ms,
            "total_tokens": trace.total_tokens,
            "total_cost_usd": trace.total_cost_usd,
            "timestamp": trace.timestamp,
            "deep_link": trace.deep_link,
            "spans": [
                {
                    "span_id": s.span_id,
                    "parent_span_id": s.parent_span_id,
                    "name": s.name,
                    "kind": s.kind,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "tokens": s.tokens,
                    "cost_usd": s.cost_usd,
                    "attributes": s.attributes,
                    "error": s.error,
                }
                for s in trace.spans
            ]
        }

        if self.async_export:
            future = self._executor.submit(self._send_payload_with_fault_containment, payload)
            with self._lock:
                self._pending_futures.append(future)
        else:
            self._send_payload_with_fault_containment(payload)

    def _send_payload_with_fault_containment(self, payload: Dict[str, Any]) -> bool:
        """Send payload to https://ingest.neatlogs.com with absolute fault containment.

        Any HTTP error, connection failure, DNS resolution error, or timeout is caught
        and safely logged. Core agent execution proceeds completely uninterrupted.
        """
        endpoint = f"{self.ingest_url}/v1/traces"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Reco-Agent-Observability/0.1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            if self._custom_client:
                resp = self._custom_client.post(endpoint, json=payload, headers=headers, timeout=2.0)
            else:
                with httpx.Client(timeout=2.0) as client:
                    resp = client.post(endpoint, json=payload, headers=headers)

            if resp.status_code >= 400:
                logger.warning(
                    "Neatlogs ingest responded with status %d: %s (non-blocking, agent unaffected)",
                    resp.status_code,
                    resp.text[:120]
                )
                return False
            return True
        except Exception as exc:
            # Fault containment: $0 impact on agent runtime
            logger.debug(
                "Neatlogs ingest failed (%s: %s). Non-blocking fault containment active.",
                type(exc).__name__,
                str(exc)
            )
            return False

    def flush(self, timeout: float = 5.0) -> None:
        """Wait for all pending background ingestion tasks to complete."""
        with self._lock:
            futures = list(self._pending_futures)
            self._pending_futures.clear()

        for f in futures:
            try:
                f.result(timeout=timeout)
            except Exception:
                pass

    def shutdown(self, wait: bool = True) -> None:
        """Cleanly shutdown the exporter thread pool."""
        self.flush()
        self._executor.shutdown(wait=wait)


# Global singleton instance
_default_tracer: Optional[NeatlogsTracer] = None


def get_tracer(
    api_key: Optional[str] = None,
    ingest_url: Optional[str] = None,
    app_url: Optional[str] = None,
) -> NeatlogsTracer:
    """Obtain or initialize the global NeatlogsTracer singleton."""
    global _default_tracer
    if _default_tracer is None:
        _default_tracer = NeatlogsTracer(
            api_key=api_key,
            ingest_url=ingest_url,
            app_url=app_url
        )
    return _default_tracer
