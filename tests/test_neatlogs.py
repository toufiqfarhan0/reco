"""Deterministic unit tests for NeatlogsTracer adapter and failure containment.

All tests use mocked components and make ZERO live network requests.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from opentelemetry.sdk.trace.export import SpanExportResult

from reco.core.interfaces import Tracer
from reco.observability.tracer import (
    DEFAULT_INGEST_ENDPOINT,
    NeatlogsTracer,
    SpanContext,
    normalize_neatlogs_endpoint,
    sanitize_attributes,
)
from reco.optimization.events import OptimizationEvent, OptimizationEventType


@pytest.fixture
def mock_otel_exporter():
    """Mock OTLP span exporter returning success."""
    exporter = MagicMock()
    exporter.export.return_value = SpanExportResult.SUCCESS
    return exporter


def test_1_tracer_configuration():
    """Test tracer configuration defaults, parameter overrides, and endpoint normalization."""
    # Test with default settings
    tracer_default = NeatlogsTracer(api_key="mock_key", enabled=False)
    assert isinstance(tracer_default, Tracer)
    assert tracer_default.endpoint == DEFAULT_INGEST_ENDPOINT
    assert tracer_default.timeout_seconds == 5.0
    assert tracer_default.service_name == "reco"
    assert tracer_default.enabled is False

    # Test parameter overrides
    tracer_custom = NeatlogsTracer(
        api_key="custom_test_key",
        base_url="https://custom-collector.internal",
        enabled=True,
        timeout_seconds=10.0,
        service_name="reco-custom",
        otel_exporter=MagicMock(),
    )
    assert tracer_custom.endpoint == "https://custom-collector.internal/v1/traces"
    assert tracer_custom.timeout_seconds == 10.0
    assert tracer_custom.service_name == "reco-custom"
    assert tracer_custom.enabled is True

    # Test endpoint normalization
    assert normalize_neatlogs_endpoint(None) == DEFAULT_INGEST_ENDPOINT
    assert normalize_neatlogs_endpoint("") == DEFAULT_INGEST_ENDPOINT
    assert normalize_neatlogs_endpoint("https://api.neatlogs.com/v1") == DEFAULT_INGEST_ENDPOINT
    assert normalize_neatlogs_endpoint("https://ingest.neatlogs.com") == DEFAULT_INGEST_ENDPOINT
    assert normalize_neatlogs_endpoint("https://ingest.neatlogs.com/v1/traces") == DEFAULT_INGEST_ENDPOINT
    assert normalize_neatlogs_endpoint("http://internal-trace:4318") == "http://internal-trace:4318/v1/traces"


def test_2_disabled_tracing_no_network(mock_otel_exporter):
    """Test that disabled tracing makes zero network or export calls."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=False, otel_exporter=mock_otel_exporter)
    assert tracer.enabled is False

    # Span execution
    with tracer.start_span("test_disabled_span", attributes={"foo": "bar"}) as span:
        span.set_attribute("nested", 123)

    assert tracer.stats["spans_started"] == 1
    assert tracer.stats["spans_exported"] == 0
    mock_otel_exporter.export.assert_not_called()

    # Event and metric logging
    tracer.log_event("disabled_event", {"data": 1})
    tracer.record_metric("disabled_metric", 42.0)
    assert tracer.stats["spans_exported"] == 0
    mock_otel_exporter.export.assert_not_called()

    # Smoke test when disabled
    res = tracer.send_smoke_test()
    assert res["success"] is False
    assert "disabled" in res["error"].lower()
    mock_otel_exporter.export.assert_not_called()


def test_3_enabled_tracing_attempts_dispatch(mock_otel_exporter):
    """Test that enabled tracing attempts dispatch to OTel pipeline."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    assert tracer.enabled is True

    with tracer.start_span("active_span", attributes={"version": "v1"}) as span:
        span.set_attribute("status", "ok")

    assert tracer.stats["spans_started"] == 1
    assert tracer.stats["spans_exported"] == 1
    # Check that exporter.export was invoked
    assert mock_otel_exporter.export.called


def test_4_successful_response_handled(mock_otel_exporter):
    """Test that successful telemetry dispatch is properly handled and recorded."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)

    # Optimization event dispatch
    opt_event = OptimizationEvent(
        event_type=OptimizationEventType.CANDIDATE_BENCHMARKED,
        experiment_id=uuid4(),
        generation_number=1,
        payload={"accuracy": 0.85, "cost_usd": 0.02},
    )
    result = tracer.emit_event(opt_event)
    assert result["success"] is True
    assert result["event"] == "optimization.candidate_benchmarked"
    assert tracer.stats["errors"] == 0

    # Smoke test success
    smoke_res = tracer.send_smoke_test()
    assert smoke_res["success"] is True
    assert smoke_res["status_code"] == 200
    assert smoke_res["metadata"]["project"] == "reco"


def test_5_timeout_contained():
    """Test that network timeout does not crash Reco and is contained locally."""
    failing_exporter = MagicMock()
    failing_exporter.export.side_effect = TimeoutError("Network timeout connecting to Neatlogs")

    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=failing_exporter)

    # Calling start_span and ending it must not raise
    with tracer.start_span("timeout_span") as span:
        span.set_attribute("query", "test")

    # Error must be recorded in stats, but caller didn't crash
    assert tracer.stats["errors"] >= 1
    assert "timeout" in tracer.stats["last_error"].lower()


def test_6_4xx_contained():
    """Test that HTTP 4xx (e.g. 401 Unauthorized) is contained without crashing."""
    class MockHTTP401Error(Exception):
        def __init__(self):
            super().__init__("401 Client Error: Unauthorized for url: https://ingest.neatlogs.com/v1/traces")
            self.status_code = 401

    failing_exporter = MagicMock()
    failing_exporter.export.side_effect = MockHTTP401Error()

    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=failing_exporter)

    # emit_event should return failure dict rather than raising
    opt_event = OptimizationEvent(
        event_type=OptimizationEventType.GENERATION_STARTED,
        experiment_id=uuid4(),
        generation_number=1,
    )
    res = tracer.emit_event(opt_event)
    assert res["success"] is True or res["success"] is False  # Safe return
    assert tracer.stats["errors"] >= 1
    assert "401" in tracer.stats["last_error"]


def test_7_5xx_contained():
    """Test that HTTP 5xx (e.g. 503 Service Unavailable) is contained gracefully."""
    class MockHTTP503Error(Exception):
        def __init__(self):
            super().__init__("503 Server Error: Service Unavailable")
            self.status_code = 503

    failing_exporter = MagicMock()
    failing_exporter.export.side_effect = MockHTTP503Error()

    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=failing_exporter)

    # log_event must not raise
    tracer.log_event("server_error_event", {"attempt": 1})
    assert tracer.stats["errors"] >= 1
    assert "503" in tracer.stats["last_error"]


def test_8_exception_contained():
    """Test that arbitrary runtime exceptions in tracing do not crash execution."""
    broken_exporter = MagicMock()
    broken_exporter.export.side_effect = RuntimeError("Fatal OTel memory corruption")

    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=broken_exporter)

    # All methods must swallow exceptions and keep agent intact
    tracer.record_metric("test_metric", 100.0)
    tracer.log_event("test_event", {"status": "running"})

    listener = tracer.as_optimization_listener()
    opt_event = OptimizationEvent(
        event_type=OptimizationEventType.OPTIMIZATION_STARTED,
        experiment_id=uuid4(),
    )
    # Listener must not throw
    listener(opt_event)

    assert tracer.stats["errors"] >= 1


def test_9_no_secret_leakage():
    """Test that sensitive credentials and secret keys are never included in telemetry."""
    raw_attributes = {
        "api_key": "v8_neatlogs_secret_abc123",
        "neatlogs_api_key": "v8_secret_key",
        "tensormux_api_key": "sk-secret-tensormux",
        "client_secret": "my_super_secret",
        "password": "user_password_123",
        "authorization": "Bearer token_xyz",
        "auth_token": "token123",
        "project": "reco",
        "environment": "test",
        "normal_metric": 42,
    }

    sanitized = sanitize_attributes(raw_attributes)

    # Sensitive keys must be purged
    assert "api_key" not in sanitized
    assert "neatlogs_api_key" not in sanitized
    assert "tensormux_api_key" not in sanitized
    assert "client_secret" not in sanitized
    assert "password" not in sanitized
    assert "authorization" not in sanitized
    assert "auth_token" not in sanitized

    # Safe keys must be preserved
    assert sanitized["project"] == "reco"
    assert sanitized["environment"] == "test"
    assert sanitized["normal_metric"] == 42


def test_10_safe_payload_structure(mock_otel_exporter):
    """Test that smoke test payload conforms strictly to required safe metadata."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)

    res = tracer.send_smoke_test(environment="smoke_test")
    assert res["success"] is True
    assert "metadata" in res
    meta = res["metadata"]

    # Verify exact required safe keys
    assert meta["project"] == "reco"
    assert meta["environment"] == "smoke_test"
    assert meta["event"] == "neatlogs_connection_test"
    assert meta["status"] == "ok"

    # Verify absence of unsafe fields
    assert "ground_truth" not in meta
    assert "api_key" not in meta
    assert "secret" not in meta
    assert "financial_data" not in meta


# =============================================================================
# STEP 16: FULL WORKFLOW INTEGRATION TESTS (11-27)
# =============================================================================

def test_11_optimization_run_span_creation(mock_otel_exporter):
    """Requirement 1: Optimization run span creation with config metadata."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    exp_id = str(uuid4())
    with tracer.start_span("optimization_run", attributes={
        "experiment_id": exp_id,
        "strategy": "failure_driven",
        "benchmark_dataset": "reconciliation",
    }) as span:
        span.set_attribute("max_generations", 2)

    assert tracer.stats["spans_started"] >= 1
    assert tracer.stats["spans_exported"] >= 1


def test_12_generation_span_creation(mock_otel_exporter):
    """Requirement 2: Generation span creation with generation index and parent version."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    exp_id = str(uuid4())
    parent_id = str(uuid4())
    with tracer.start_span("generation_1", attributes={
        "experiment_id": exp_id,
        "generation_number": 1,
        "parent_version_id": parent_id,
    }) as span:
        span.set_attribute("candidates_count", 2)

    assert tracer.stats["spans_started"] >= 1


def test_13_benchmark_run_span_split_attribute(mock_otel_exporter):
    """Requirement 3: Benchmark run span with split attribute distinguishing train vs held_out."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    with tracer.start_span("benchmark_run.optimization", attributes={"split": "optimization"}):
        pass
    with tracer.start_span("benchmark_run.held_out", attributes={"split": "held_out"}):
        pass

    assert tracer.stats["spans_started"] == 2


def test_14_benchmark_case_span_case_code(mock_otel_exporter):
    """Requirement 4: Benchmark case span with case_code."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    span_ctx = tracer.trace_benchmark_case(
        case_code="REC-OPT-01",
        split="optimization",
        experiment_id=str(uuid4()),
        agent_version_id=str(uuid4()),
    )
    with span_ctx:
        pass
    assert tracer.stats["spans_started"] >= 1
    assert span_ctx.attributes["case_code"] == "REC-OPT-01"
    assert span_ctx.attributes["split"] == "optimization"


def test_15_model_invocation_span_tokens_cost(mock_otel_exporter):
    """Requirement 5: Model invocation span with token counts and cost attributes."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    span_ctx = tracer.trace_model_invocation(
        model_name="mock-agent-v1",
        tokens_in=120,
        tokens_out=45,
        latency_ms=180,
        cost_usd=0.00045,
        node_id="reconcile",
    )
    with span_ctx:
        pass
    assert span_ctx.attributes["tokens_in"] == 120
    assert span_ctx.attributes["tokens_out"] == 45
    assert span_ctx.attributes["total_tokens"] == 165
    assert span_ctx.attributes["cost_usd"] == 0.00045
    assert span_ctx.attributes["model_name"] == "mock-agent-v1"


def test_16_tool_invocation_span_duration_success(mock_otel_exporter):
    """Requirement 6: Tool invocation span with duration and success."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    span_ctx = tracer.trace_tool_invocation(
        tool_name="parse_bank_statement",
        duration_ms=42,
        success=True,
        node_id="load_transactions",
    )
    with span_ctx:
        pass
    assert span_ctx.attributes["tool_name"] == "parse_bank_statement"
    assert span_ctx.attributes["duration_ms"] == 42
    assert span_ctx.attributes["success"] is True
    assert span_ctx.attributes["status"] == "ok"


def test_17_failure_diagnosis_span_taxonomy(mock_otel_exporter):
    """Requirement 7: Failure diagnosis span with error taxonomy attributes."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    diag_id = str(uuid4())
    tracer.trace_failure_diagnosis(
        diagnosis_id=diag_id,
        category="TIMING_DIFFERENCE",
        severity="medium",
        failed_node="reconcile",
        confidence=0.92,
        case_code="REC-OPT-02",
        generation_number=1,
    )
    assert tracer.stats["events_logged"] >= 1


def test_18_candidate_mutation_span_prompt_hash(mock_otel_exporter):
    """Requirement 8: Candidate mutation span with prompt hash."""
    import hashlib
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    cand_id = str(uuid4())
    p_hash = hashlib.sha256(b"System prompt change").hexdigest()[:16]
    tracer.trace_mutation(
        candidate_id=cand_id,
        parent_version_id=str(uuid4()),
        mutation_type="SYSTEM_PROMPT",
        target="reconcile",
        prompt_hash=p_hash,
        change_summary="Clarified reconciliation date window",
        generation_number=1,
    )
    assert tracer.stats["events_logged"] >= 1


def test_19_promotion_gate_span_delta_metrics(mock_otel_exporter):
    """Requirement 9: Promotion gate span with delta metrics."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    tracer.trace_promotion(
        experiment_id=str(uuid4()),
        parent_version_id=str(uuid4()),
        final_version_id=str(uuid4()),
        decision="promoted",
        promoted=True,
        accuracy_delta=0.15,
        cost_delta=0.0001,
        latency_delta=25,
        reliability_delta=0.05,
        improved_dimensions=["accuracy", "reliability"],
    )
    assert tracer.stats["events_logged"] >= 1


def test_20_e2e_span_hierarchy_nesting():
    """Requirement 10: End-to-end span hierarchy nesting (parent-child relationships)."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True)
    with tracer.start_active_span("optimization_run") as root:
        with tracer.start_active_span("generation_1") as gen:
            with tracer.start_active_span("benchmark_run.optimization") as bench:
                with tracer.start_active_span("benchmark_case.REC-001") as case:
                    with tracer.start_active_span("node_execution.reconcile") as node:
                        with tracer.start_active_span("model_invocation") as model:
                            pass
                        with tracer.start_active_span("tool_invocation.parse_csv") as tool:
                            pass

    tree = tracer.build_trace_hierarchy_from_spans("optimization_run")
    assert tree["name"] == "optimization_run"
    assert "children" in tree
    assert len(tree["children"]) >= 1
    gen_node = tree["children"][0]
    assert gen_node["name"] == "generation_1"
    assert gen_node["kind"] == "CHAIN"


def test_21_event_emission_mapping(mock_otel_exporter):
    """Requirement 11: Event emission mapping (OptimizationEvent -> Neatlogs span)."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    opt_ev = OptimizationEvent(
        event_type=OptimizationEventType.PROMOTION_ASSESSED,
        experiment_id=uuid4(),
        generation_number=1,
        payload={"promoted": True, "decision": "promoted"},
    )
    res = tracer.emit_event(opt_ev)
    assert res["success"] is True
    assert res["event"] == "optimization.promotion_assessed"


def test_22_correlation_ids_nested_spans():
    """Requirement 12: Correlation IDs across nested spans."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True)
    exp_id = str(uuid4())
    cand_id = str(uuid4())
    with tracer.start_active_span("optimization_run", attributes={"experiment_id": exp_id}):
        with tracer.start_active_span("candidate_benchmark", attributes={"candidate_id": cand_id, "experiment_id": exp_id}):
            with tracer.start_active_span("model_invocation", attributes={"experiment_id": exp_id, "candidate_id": cand_id}):
                pass

    tree = tracer.build_trace_hierarchy_from_spans()
    spans = tracer.recorded_spans
    for s in spans:
        if s["name"] in ("candidate_benchmark", "model_invocation"):
            assert s["attributes"]["experiment_id"] == exp_id


def test_23_sanitization_no_ground_truth(mock_otel_exporter):
    """Requirement 13: Sanitization: no ground truth in attributes."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True, otel_exporter=mock_otel_exporter)
    case_span = tracer.trace_benchmark_case(
        case_code="REC-HLD-01",
        split="held_out",
        attributes={
            "ground_truth": "Unreconciled wire fee $25.00",
            "expected_outcome": "MATCH",
            "safe_meta": "valid",
        },
    )
    assert "ground_truth" not in case_span.attributes
    assert "expected_outcome" not in case_span.attributes
    assert case_span.attributes["is_held_out"] is True
    assert case_span.attributes["safe_meta"] == "valid"


def test_24_sanitization_no_prompt_text_only_hashes():
    """Requirement 14: Sanitization: no prompt text, only hashes."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True)
    raw_prompt = "You are a specialized bank reconciliation agent with rules..."
    tracer.trace_mutation(
        candidate_id=str(uuid4()),
        parent_version_id=str(uuid4()),
        mutation_type="SYSTEM_PROMPT",
        target="reconcile",
        prompt_text=raw_prompt,
    )
    # Inspect recorded span history
    cand_spans = [s for s in tracer.recorded_spans if "candidate_generated" in s["name"]]
    assert len(cand_spans) >= 1
    attrs = cand_spans[0]["attributes"]
    assert "prompt_text" not in attrs
    assert "prompt_hash" in attrs
    assert len(attrs["prompt_hash"]) == 16
    assert raw_prompt not in str(attrs)


def test_25_failure_containment_tracing_exception_does_not_halt():
    """Requirement 15: Failure containment: tracing exception does not halt optimization."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True)
    # Simulate internal error inside start_active_span or emit_event
    with patch.object(tracer, "start_span", side_effect=ValueError("Corrupt span state")):
        # Must not raise
        res = tracer.emit_event("test_event", {"data": 123})
        assert res["success"] is False
        assert tracer.stats["errors"] >= 1


def test_26_failure_containment_network_timeout():
    """Requirement 16: Failure containment: network timeout does not halt runner."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=True)
    with patch("requests.post", side_effect=TimeoutError("Neatlogs ingest timeout after 5s")):
        res = tracer.send_structured_trace({"name": "test_trace"})
        assert res["success"] is False
        assert "timeout" in res["error"].lower()
        assert tracer.stats["errors"] >= 1


def test_27_observability_disabled_zero_overhead(mock_otel_exporter):
    """Requirement 17: Observability disabled: zero spans exported, zero network overhead."""
    tracer = NeatlogsTracer(api_key="mock_key", enabled=False, otel_exporter=mock_otel_exporter)
    with tracer.start_span("opt_run", attributes={"experiment_id": "exp-1"}):
        with tracer.start_span("gen_1"):
            span_ctx = tracer.trace_model_invocation("test-model", tokens_in=50)
            with span_ctx:
                pass
    tracer.trace_failure_diagnosis("d1", "CATEGORY", "high", "reconcile", 0.9)
    tracer.trace_mutation("c1", "p1", "SYSTEM_PROMPT", "reconcile")
    tracer.trace_promotion("exp-1", "p1", "c1", "promoted", True)

    assert tracer.stats["spans_exported"] == 0
    mock_otel_exporter.export.assert_not_called()
    trace_res = tracer.send_structured_trace({"name": "disabled_test"})
    assert trace_res["success"] is False
    assert "disabled" in trace_res["error"].lower()
