"""Tests for Neatlogs Distributed Tracing & Observability (Track 1).

Verifies:
1. Non-blocking, fault-tolerant telemetry exporter connecting to https://ingest.neatlogs.com.
2. 5-Tier Hierarchical spans:
   optimization_run -> generation_N -> candidate_eval -> node_execution -> tool_invocation.
3. Full metadata capture: timestamps, duration, status, model parameters, tokens, cost, tool arguments, and outputs.
4. Absolute fault containment ($0 failure impact on agent execution).
5. Direct deep-link URL generation (https://app.neatlogs.com/traces/<trace_id>).
6. Frontend dictionary compatibility matching Next.js visual console expectations.
"""

import os
import time
from unittest.mock import MagicMock, patch
import httpx
import pytest

from reco.observability.tracer import (
    DEFAULT_NEATLOGS_APP_URL,
    DEFAULT_NEATLOGS_INGEST_URL,
    NeatlogsSpan,
    NeatlogsTrace,
    NeatlogsTracer,
    get_tracer,
)


def test_tracer_initialization_defaults_and_env():
    """Verify tracer correctly handles default endpoints and environment variable overrides."""
    tracer = NeatlogsTracer(api_key="neat_test_key_123")
    assert tracer.api_key == "neat_test_key_123"
    assert tracer.ingest_url == DEFAULT_NEATLOGS_INGEST_URL
    assert tracer.app_url == DEFAULT_NEATLOGS_APP_URL
    assert tracer.enabled is True

    # Test environment variable overrides
    with patch.dict(
        os.environ,
        {
            "NEATLOGS_API_KEY": "env_api_key_456",
            "NEATLOGS_INGEST_URL": "https://custom.ingest.neatlogs.com/",
            "NEATLOGS_APP_URL": "https://custom.app.neatlogs.com/",
        },
    ):
        env_tracer = NeatlogsTracer()
        assert env_tracer.api_key == "env_api_key_456"
        assert env_tracer.ingest_url == "https://custom.ingest.neatlogs.com"
        assert env_tracer.app_url == "https://custom.app.neatlogs.com"


def test_deep_link_generation():
    """Verify deep-link URLs correctly format to inspect execution traces in Neatlogs UI."""
    tracer = NeatlogsTracer(app_url="https://app.neatlogs.com")
    trace_id = "tr_neat_abc123def456"
    url = tracer.get_trace_url(trace_id)
    assert url == f"https://app.neatlogs.com/traces/{trace_id}"

    # Verify trace object automatically generates deep_link
    with tracer.start_trace(trace_id=trace_id) as trace:
        pass

    assert trace.deep_link == f"https://app.neatlogs.com/traces/{trace_id}"


def test_5_tier_hierarchical_spans_lineage_and_parent_ids():
    """Verify 5-tier span hierarchy: optimization_run -> generation_N -> candidate_eval -> node_execution -> tool_invocation."""
    tracer = NeatlogsTracer(async_export=False)

    with tracer.trace_optimization_run(
        name="autonomous_optimization_run",
        architecture_id="Agent_Reconciliation_V0",
        domain="financial_reconciliation",
    ) as root_trace:

        # Tier 1: optimization_run root span
        root_span = tracer.current_span
        assert root_span is not None
        assert root_span.kind == "optimization_run"
        assert root_span.parent_span_id is None

        # Tier 2: generation_N
        with tracer.trace_generation(generation=0) as gen_span:
            assert gen_span.kind == "generation_N"
            assert gen_span.name == "generation_0"
            assert gen_span.parent_span_id == root_span.span_id

            # Tier 3: candidate_eval
            with tracer.trace_candidate_eval(
                candidate_name="Candidate_V0_Baseline",
                split="optimization",
            ) as eval_span:
                assert eval_span.kind == "candidate_eval"
                assert eval_span.name == "candidate_eval:Candidate_V0_Baseline"
                assert eval_span.parent_span_id == gen_span.span_id

                # Tier 4: node_execution
                with tracer.trace_node_execution(
                    node_id="tool_node_exact_reconcile",
                    node_type="tool_node",
                ) as node_span:
                    assert node_span.kind == "node_execution"
                    assert node_span.name == "node_execution:tool_node_exact_reconcile"
                    assert node_span.parent_span_id == eval_span.span_id

                    # Tier 5: tool_invocation
                    with tracer.trace_tool_invocation(
                        tool_name="exact_reconcile",
                        record_count=100,
                    ) as tool_span:
                        assert tool_span.kind == "tool_invocation"
                        assert tool_span.name == "tool_invocation:exact_reconcile"
                        assert tool_span.parent_span_id == node_span.span_id
                        tool_span.set_attribute("matches_found", 98)

    # Verify complete lineage in trace buffer
    assert len(root_trace.spans) == 5
    spans_by_kind = {s.kind: s for s in root_trace.spans}

    assert "optimization_run" in spans_by_kind
    assert "generation_N" in spans_by_kind
    assert "candidate_eval" in spans_by_kind
    assert "node_execution" in spans_by_kind
    assert "tool_invocation" in spans_by_kind

    assert spans_by_kind["generation_N"].parent_span_id == spans_by_kind["optimization_run"].span_id
    assert spans_by_kind["candidate_eval"].parent_span_id == spans_by_kind["generation_N"].span_id
    assert spans_by_kind["node_execution"].parent_span_id == spans_by_kind["candidate_eval"].span_id
    assert spans_by_kind["tool_invocation"].parent_span_id == spans_by_kind["node_execution"].span_id

    # Verify strict chronological order: root span is first, deepest child is last
    assert root_trace.spans[0].kind == "optimization_run"
    assert root_trace.spans[1].kind == "generation_N"
    assert root_trace.spans[2].kind == "candidate_eval"
    assert root_trace.spans[3].kind == "node_execution"
    assert root_trace.spans[4].kind == "tool_invocation"

    # Verify all share identical trace_id
    for s in root_trace.spans:
        assert s.trace_id == root_trace.trace_id
        assert s.duration_ms >= 0.0
        assert s.status == "ok"


def test_span_metadata_capture_and_aggregation():
    """Verify capture of model parameters, token accounting, costs, tool arguments, and outputs."""
    tracer = NeatlogsTracer(async_export=False)

    with tracer.start_trace(architecture_id="Agent_Anomaly_V1") as trace:
        # LLM inference span with token & cost metadata
        with tracer.span(
            name="reasoning_node_llm",
            kind="llm_inference",
            model="glm-4-7-flash",
            max_tokens=400,
            temperature=0.0,
        ) as llm_span:
            llm_span.set_tokens(350)
            llm_span.set_cost(0.0035)
            llm_span.set_attribute("reasoning_tokens", 85)

        # Tool node with arguments and output metadata
        with tracer.span(
            name="tool_detect_anomalies",
            kind="tool_invocation",
            tool_name="detect_anomalies",
        ) as tool_span:
            tool_span.set_attributes({
                "tool_arguments": {"threshold": 2.5, "metric": "amount"},
                "tool_output": {"anomalies_detected": 3, "outliers": ["tx_08"]},
                "status_code": 200,
            })

    # Verify trace aggregation
    assert trace.total_tokens == 350
    assert trace.total_cost_usd == 0.0035
    assert trace.status == "success"
    assert len(trace.spans) == 3  # root + llm + tool

    # Find LLM span and verify properties
    llm_sp = next(s for s in trace.spans if s.name == "reasoning_node_llm")
    assert llm_sp.attributes["model"] == "glm-4-7-flash"
    assert llm_sp.attributes["max_tokens"] == 400
    assert llm_sp.attributes["reasoning_tokens"] == 85
    assert llm_sp.tokens == 350
    assert llm_sp.cost_usd == 0.0035

    # Find Tool span and verify properties
    tool_sp = next(s for s in trace.spans if s.name == "tool_detect_anomalies")
    assert tool_sp.attributes["tool_arguments"]["threshold"] == 2.5
    assert tool_sp.attributes["tool_output"]["anomalies_detected"] == 3


def test_span_error_containment_and_status_marking():
    """Verify that unhandled exceptions inside a span mark the span as 'error' with attributes."""
    tracer = NeatlogsTracer(async_export=False)

    with pytest.raises(ValueError, match="Synthetic test failure"):
        with tracer.start_trace() as trace:
            with tracer.span(name="failing_node", kind="node_execution"):
                raise ValueError("Synthetic test failure")

    # Verify trace recorded error span
    assert len(tracer.exported_spans) >= 1
    err_span = next(s for s in tracer.exported_spans if s.name == "failing_node")
    assert err_span.status == "error"
    assert "Synthetic test failure" in str(err_span.error)
    assert err_span.attributes["error"] == "Synthetic test failure"


def test_fault_containment_on_ingest_failure_zero_impact():
    """Verify $0 failure impact: when Neatlogs ingest fails or times out, core agent continues uninterrupted."""
    # Mock an HTTP client that raises ConnectionRefused or returns HTTP 500
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.ConnectError("Connection refused by Neatlogs ingest endpoint")

    tracer = NeatlogsTracer(
        api_key="neat_key_fail_test",
        ingest_url="https://ingest.neatlogs.com",
        async_export=False,
        http_client=mock_client,
    )

    # Core execution must NOT raise an exception when ingest fails
    completed = False
    try:
        with tracer.start_trace(architecture_id="Agent_Zero_Failure_Impact") as trace:
            with tracer.span("critical_node", kind="node_execution") as sp:
                sp.set_attribute("important_payload", 42)
        completed = True
    except Exception as exc:
        pytest.fail(f"Fault containment breached! Exception propagated to agent: {exc}")

    assert completed is True
    # The trace was still recorded locally in memory
    assert len(tracer.exported_traces) == 1
    assert tracer.exported_traces[0].architecture_id == "Agent_Zero_Failure_Impact"


def test_fault_containment_on_http_500_status():
    """Verify HTTP 500 internal server error from ingest endpoint does not disrupt execution."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_resp

    tracer = NeatlogsTracer(
        api_key="neat_key_500_test",
        async_export=False,
        http_client=mock_client,
    )

    # Run agent trace
    with tracer.start_trace(architecture_id="Agent_HTTP_500_Test") as trace:
        with tracer.span("step_1"):
            pass

    assert len(tracer.exported_traces) == 1


def test_non_blocking_async_export_and_flush():
    """Verify non-blocking background thread pool exporter and flush mechanism."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_client.post.return_value = mock_resp

    tracer = NeatlogsTracer(
        api_key="neat_async_test_key",
        async_export=True,
        http_client=mock_client,
    )

    with tracer.start_trace(architecture_id="Agent_Async_Trace") as trace:
        with tracer.span("async_step"):
            pass

    # Flush all background worker tasks
    tracer.flush(timeout=3.0)

    # Verify background HTTP POST was executed
    assert mock_client.post.called
    endpoint_called = mock_client.post.call_args[0][0]
    assert endpoint_called == f"{DEFAULT_NEATLOGS_INGEST_URL}/v1/traces"

    tracer.shutdown(wait=True)


def test_frontend_compatibility_dictionary_structure():
    """Verify exported trace dictionary precisely matches frontend NeatlogsTrace TypeScript specifications."""
    tracer = NeatlogsTracer(async_export=False)

    with tracer.start_trace(architecture_id="Agent_Reconciliation_V2_Candidate_C") as trace:
        with tracer.span(
            name="Node: Transaction Ingestion",
            kind="node_execution",
            records_loaded=4,
            source="gateway_export.csv",
        ):
            pass

        with tracer.span(
            name="Tool: smart_reconcile",
            kind="tool_invocation",
            casing_normalized=True,
            whitespace_stripped=True,
        ):
            pass

    fe_dict = trace.to_frontend_dict()

    # Validate top-level keys
    assert "trace_id" in fe_dict
    assert "architecture_id" in fe_dict
    assert "status" in fe_dict
    assert "total_duration_ms" in fe_dict
    assert "total_tokens" in fe_dict
    assert "total_cost_usd" in fe_dict
    assert "timestamp" in fe_dict
    assert "spans" in fe_dict

    # Validate span items match NeatlogsSpan interface
    for sp in fe_dict["spans"]:
        assert "span_id" in sp
        assert "name" in sp
        assert "kind" in sp
        assert sp["kind"] in {"dag", "node", "tool", "verifier", "llm"}
        assert "status" in sp
        assert "start_offset_ms" in sp
        assert "duration_ms" in sp
        assert "attributes" in sp
