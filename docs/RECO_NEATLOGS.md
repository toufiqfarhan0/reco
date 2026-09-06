# Reco — Neatlogs Observability Adapter & Live Smoke Test (Step 15B)

## 1. Executive Summary

This document describes the design, configuration, failure containment, and live smoke test verification of the **Neatlogs Observability Adapter** (`NeatlogsTracer`) for Reco.

Neatlogs provides execution tracing and telemetry for AI agent workflows. In accordance with Reco's architectural boundaries:
- Neatlogs is strictly an **observability layer**.
- It is **NOT** the source of truth for benchmark metrics, agent state, or candidate promotion.
- It is **NOT** required for Reco core execution.
- If Neatlogs is unreachable, rate-limited, timed out, or returning 4xx/5xx errors, **Reco continues operating normally without disruption**.

---

## 2. Tracer Architecture & Abstraction

`NeatlogsTracer` is located in [`reco/observability/tracer.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/observability/tracer.py) and implements the abstract `Tracer` interface defined in [`reco/core/interfaces.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/core/interfaces.py):

```python
class Tracer(ABC):
    @abstractmethod
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Any:
        """Begin an execution trace span."""
        pass

    @abstractmethod
    def log_event(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Log a telemetry event."""
        pass

    @abstractmethod
    def record_metric(self, name: str, value: float, unit: str = "count") -> None:
        """Record an analytical metric."""
        pass
```

### Key Components

1. **`NeatlogsTracer`**: Manages OTLP span export to Neatlogs. Configured with bounded timeouts and lazy OpenTelemetry provider initialization.
2. **`SpanContext`**: Lightweight context manager wrapping trace spans. Records duration, status, and custom attributes. Ends spans cleanly on block exit.
3. **`SafeSpanProcessor`**: Intercepts OTLP exporter results. When network errors occur (timeout, HTTP 4xx, HTTP 5xx, socket crash), errors are recorded in internal tracer telemetry stats and warnings logged locally, completely isolating the caller from exceptions.
4. **Optimization Event Integration**: Reuses `reco.optimization.events.OptimizationEvent` directly via `emit_event(event)` and `as_optimization_listener()`, avoiding duplicate event models.
5. **Secret Sanitization**: `sanitize_attributes()` strips all keys and values containing sensitive strings (`api_key`, `secret`, `token`, `password`, `auth`, `sk-`, `v8_`, etc.) prior to export.

---

## 3. Configuration & Enable/Disable Behavior

Centralized configuration is defined in [`reco/config.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/config.py) and loaded via environment variables:

| Environment Variable | Default | Purpose |
|---|---|---|
| `OBSERVABILITY_ENABLED` | `false` | Master toggle for Neatlogs tracing |
| `NEATLOGS_API_KEY` | `""` | Project API key for authentication |
| `NEATLOGS_BASE_URL` | `https://ingest.neatlogs.com` | Base URL or OTLP traces endpoint |

### Endpoint Normalization

The adapter automatically normalizes base URLs into valid OTLP ingestion endpoints:
- `https://ingest.neatlogs.com` $\to$ `https://ingest.neatlogs.com/v1/traces`
- `https://api.neatlogs.com/v1` $\to$ `https://ingest.neatlogs.com/v1/traces` (auto-redirected from placeholder)
- Custom collectors (e.g. `http://localhost:4318`) $\to$ `http://localhost:4318/v1/traces`

### Enable / Disable Semantics

- **`OBSERVABILITY_ENABLED=false` (Default)**:
  Zero outbound network requests are made. Methods execute locally, updating in-memory counters without initiating HTTP connections.
- **`OBSERVABILITY_ENABLED=true`**:
  Initializes the OTLP export pipeline using `NEATLOGS_API_KEY` and exports completed spans to the target endpoint.
- **Missing API Key**:
  If `OBSERVABILITY_ENABLED=true` but `NEATLOGS_API_KEY` is empty, export is automatically and safely disabled.

---

## 4. Telemetry Event & Span Payload Shape

The live smoke test transmits a single, minimal, non-sensitive span:

```json
{
  "name": "neatlogs_connection_test",
  "attributes": {
    "project": "reco",
    "environment": "smoke_test",
    "event": "neatlogs_connection_test",
    "status": "ok",
    "duration_ms": 0
  }
}
```

### Safety Policy
- **Included**: High-level workflow names, execution status, elapsed latencies, generation IDs.
- **Strictly Excluded**: Benchmark ground truth, raw customer transactions, financial account numbers, passwords, API keys, and environment variables.

---

## 5. Failure Containment & Resilience

Observability must be 100% resilient. We tested and verified that each of the following failure modes is safely contained:

| Failure Mode | Injected Simulation | Tracer Behavior | Impact on Reco Core |
|---|---|---|---|
| **Network Timeout** | `TimeoutError` in exporter | Caught by `SafeSpanProcessor`, logged locally | Zero crash; agent continues |
| **HTTP 4xx (Unauthorized)** | `MockHTTP401Error` | Caught by `SafeSpanProcessor`, logged locally | Zero crash; agent continues |
| **HTTP 5xx (Unavailable)** | `MockHTTP503Error` | Caught by `SafeSpanProcessor`, logged locally | Zero crash; agent continues |
| **Memory / Runtime Crash** | `RuntimeError` in exporter | Intercepted in try/except block | Zero crash; agent continues |

---

## 6. Live Smoke Test Result

Executed via [`scripts/run_neatlogs_smoke_test.py`](file:///c:/Users/toufi/Desktop/test-ao/scripts/run_neatlogs_smoke_test.py) with `OBSERVABILITY_ENABLED=true`:

```text
==================================================
RECO — STEP 15B: NEATLOGS LIVE SMOKE TEST
==================================================
Service Name: reco
Base URL: https://ingest.neatlogs.com
Observability Enabled: True (forced for smoke test)
Key Configured: [REDACTED]
--------------------------------------------------
Target OTLP Endpoint: https://ingest.neatlogs.com/v1/traces
Sending live smoke test span...
--------------------------------------------------
HTTP Result Status: 200
Success: True
Roundtrip Latency: 1115 ms
Tracer Stats: {
  "spans_started": 1,
  "spans_exported": 1,
  "events_logged": 0,
  "metrics_recorded": 0,
  "errors": 0,
  "last_error": null
}
Payload Attributes Sent: {
  "project": "reco",
  "environment": "smoke_test",
  "event": "neatlogs_connection_test",
  "status": "ok"
}
==================================================
[SUCCESS] Neatlogs live smoke test passed cleanly!
```

---

---

## 7. Step 16: Full Hierarchical Workflow Integration

Step 16 connects `NeatlogsTracer` throughout the entire Reco autonomous optimization loop, instrumenting every level from top-level experiment orchestration down to individual LLM prompts, tool executions, and promotion gate evaluations.

### 7.1 Architecture & Scope
Observability remains strictly best-effort and non-intrusive:
- **Default State**: `OBSERVABILITY_ENABLED=false` (zero network calls, near-zero overhead).
- **Failure Containment**: All tracing calls are wrapped in `try/except Exception: pass` and guarded by `SafeSpanProcessor`. Telemetry errors can never abort an experiment or invalidate scorecards.
- **Privacy & Redaction**:
  - Raw prompt text is never sent over the wire; deterministic 16-character SHA-256 hashes (`compute_prompt_hash`) are logged instead.
  - Held-out test split evaluations strictly purge protected ground truth (`expected_matches`, `expected_discrepancies`, `target_solution`, `bank_records`, etc.).
  - Sensitive patterns (`key`, `secret`, `token`, `password`, `auth`) are redacted, while whitelisted performance metrics (`tokens_in`, `tokens_out`, `duration_ms`, `cost_usd`) pass through safely.

### 7.2 Trace Hierarchy (ASCII Tree)

```text
optimization_run (WORKFLOW)
  │
  ├── generation_0 (CHAIN)
  │     ├── baseline_benchmark (EVALUATOR)
  │     │     └── benchmark_run.optimization (EVALUATOR)
  │     │           ├── benchmark_case.REC-OPT-01 (TASK)
  │     │           │     ├── node_execution.load_transactions (CHAIN)
  │     │           │     │     └── tool_invocation.parse_bank_statement (TOOL)
  │     │           │     ├── node_execution.reconcile (CHAIN)
  │     │           │     │     ├── model_invocation (LLM) [tokens, cost, latency]
  │     │           │     │     └── tool_invocation.match_exact_amounts (TOOL)
  │     │           │     └── node_execution.generate_report (CHAIN)
  │     │           └── benchmark_case.REC-OPT-02 (TASK) [failure detected]
  │     │                 └── ...
  │     └── failure_diagnosis (EVALUATOR) [taxonomy, confidence, root_cause]
  │
  ├── generation_1 (CHAIN)
  │     ├── candidate_mutation (GUARDRAIL) [mutation_type, prompt_hash_delta]
  │     ├── candidate_benchmark.cand_v1 (EVALUATOR)
  │     │     └── benchmark_run.optimization (EVALUATOR)
  │     │           └── benchmark_case.REC-OPT-02 (TASK) [now passing]
  │     └── promotion_gate (GUARDRAIL / EVALUATOR)
  │           ├── benchmark_run.held_out (EVALUATOR) [isolated test split]
  │           │     └── benchmark_case.REC-HLD-01 (TASK) [privacy-purged]
  │           └── promotion_assessed (EVALUATOR) [composite delta, promoted=True]
  │
  └── optimization_completed (WORKFLOW summary)
```

### 7.3 Span Semantics & Attributes

| Span Level | Span Kind | Key Attributes Recorded | Privacy / Redaction Policy |
|---|---|---|---|
| `optimization_run` | `WORKFLOW` | `experiment_id`, `track`, `strategy`, `max_generations` | Safe execution metadata only |
| `generation_{N}` | `CHAIN` | `generation_number`, `parent_version_id`, `experiment_id` | Safe execution metadata only |
| `benchmark_run.{split}` | `EVALUATOR` | `split` (`optimization` or `held_out`), `case_count` | Categorical split descriptor |
| `benchmark_case.{code}` | `TASK` | `case_code`, `passed`, `f1_score`, `split` | Ground truth strictly purged on `held_out` split |
| `node_execution.{id}` | `CHAIN` | `node_id`, `node_type`, `status`, `duration_ms` | Node identifiers only |
| `model_invocation` | `LLM` | `model`, `tokens_in`, `tokens_out`, `cost_usd`, `latency_ms` | Exempt from sensitive filters via `ALLOWED_METRIC_KEYS` |
| `tool_invocation.{name}`| `TOOL` | `tool_name`, `success`, `duration_ms` | Arguments sanitized, secrets stripped |
| `failure_diagnosis` | `EVALUATOR` | `failure_type`, `root_cause_node`, `confidence` | Structured diagnostic taxonomy |
| `candidate_mutation` | `GUARDRAIL` | `mutation_type`, `parent_hash`, `new_hash` | Raw prompts SHA-256 hashed to 16 characters |
| `promotion_gate` | `GUARDRAIL` | `status`, `candidate_id`, `delta_f1`, `promoted` | Metric deltas only |

---

## 8. Verification & Test Coverage

Full test suite verification results:
- **`tests/test_neatlogs.py`**: **27 passed** in ~7s (100% pass rate covering all Step 16 requirements).
- **Full Project Regression**: **428 total tests passed** (427 passed, 1 skipped).
- **Live Demo Trace Ingestion**: Executed via [`scripts/generate_neatlogs_demo_trace.py`](file:///c:/Users/toufi/Desktop/test-ao/scripts/generate_neatlogs_demo_trace.py), generating a 29-span end-to-end hierarchy saved to `scratch/neatlogs_trace_demo.json` and ingested into Neatlogs via `POST https://ingest.neatlogs.com/v1/trace` with HTTP Status `200 OK` (Trace ID: `61c273c72a4b23569433b329a461478e`, Latency: 883 ms).

---

## 9. Next Milestones

- Step 17: Monetization & Billing Layer (Dodo Payments) integration.

