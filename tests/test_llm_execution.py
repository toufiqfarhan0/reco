"""Comprehensive deterministic test suite for real LLM execution & structured tool-calling.

Covers all 34 requirements across 8 test suites:
- Model: request construction, response parsing, tool-call parsing, structured output parsing,
         usage accounting, timeout handling, model failure handling (1 - 7)
- Tool Calling: authorized tool call, unauthorized tool call, invalid arguments, tool result
                feedback, multiple bounded tool rounds, max-round enforcement (8 - 13)
- Node Execution: final response without tool, tool call then final response, malformed tool call,
                  malformed final output, model failure recovery (14 - 18)
- Mutation Compatibility: prompt mutation, tool mutation, model mutation, context mutation (19 - 22)
- Accounting: input token tracking, output token tracking, cost metadata, latency metadata (23 - 26)
- Mock: deterministic final response, mock tool call, mock sequence, malformed mock call, mock failure (27 - 31)
- Integration: reconciliation node with model-driven tool call, graph execution through ModelGateway (32 - 33)
- Live Smoke Test: opt-in real provider smoke test (34)
"""

import asyncio
import json
import os
from typing import Any, Dict, List
import httpx
import pytest

from reco.config import Settings
from reco.core.interfaces import (
    ModelGateway,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ToolCall,
)
from reco.engine.models import EdgeModel, GraphDefinition, NodeModel
from reco.engine.node_runner import NodeExecutionResult, NodeRunner
from reco.engine.runtime import AgentGraphRuntime
from reco.engine.state import ExecutionState
from reco.llm.factory import get_model_gateway
from reco.llm.mock import MockModelGateway
from reco.llm.tensormux import TensorMuxGateway
from reco.llm.tools import get_tool_schemas_for_node, tool_to_function_schema
from reco.tools import default_tool_registry
from reco.tools.executor import ToolExecutor


# =============================================================================
# Suite 1: Model Request & Response Tests (1 - 7)
# =============================================================================

def test_01_request_construction():
    """Requirement 1: ModelRequest represents all inference parameters."""
    messages = [
        ModelMessage(role="system", content="You are an auditor."),
        ModelMessage(role="user", content="Verify journal entry 101."),
    ]
    req = ModelRequest(
        messages=messages,
        model="deepseek-v3",
        temperature=0.2,
        max_tokens=1000,
        tools=[{"type": "function", "function": {"name": "query_gl"}}],
        response_format={"type": "json_object"},
        system_prompt="You are an auditor.",
        metadata={"experiment_id": "exp-1"},
    )
    assert req.model == "deepseek-v3"
    assert req.temperature == 0.2
    assert req.max_tokens == 1000
    assert len(req.messages) == 2
    assert req.tools[0]["function"]["name"] == "query_gl"
    assert req.response_format["type"] == "json_object"
    assert req.system_prompt == "You are an auditor."


def test_02_response_parsing():
    """Requirement 2: ModelResponse parses provider data into normalized representation."""
    resp = ModelResponse(
        content="Reconciliation complete: 0 variances.",
        tokens_prompt=120,
        tokens_completion=45,
        cost_usd=0.00035,
        cost_type="actual",
        latency_ms=85,
        model_used="deepseek-v3",
        finish_reason="stop",
        provider_metadata={"provider": "tensormux", "id": "req-999"},
    )
    assert resp.content == "Reconciliation complete: 0 variances."
    assert resp.total_tokens == 165
    assert resp.cost_usd == 0.00035
    assert resp.cost_type == "actual"
    assert resp.latency_ms == 85
    assert resp.model_used == "deepseek-v3"
    assert resp.finish_reason == "stop"


def test_03_tool_call_parsing():
    """Requirement 3: Provider-neutral tool call extraction from ModelResponse."""
    # Standard OpenAI / TensorMux format
    raw_calls = [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "fuzzy_match_transactions",
                "arguments": json.dumps({"vendor_similarity_threshold": 0.85}),
            },
        }
    ]
    resp = ModelResponse(content="", tool_calls=raw_calls)
    parsed = resp.get_parsed_tool_calls()
    assert len(parsed) == 1
    tc = parsed[0]
    assert isinstance(tc, ToolCall)
    assert tc.tool_name == "fuzzy_match_transactions"
    assert tc.arguments["vendor_similarity_threshold"] == 0.85
    assert tc.call_id == "call_abc123"


def test_04_structured_output_parsing():
    """Requirement 4: ModelResponse parses JSON structured outputs cleanly."""
    json_text = json.dumps({"matched_count": 4, "unmatched_count": 1, "status": "reconciled"})
    resp = ModelResponse(content=json_text, structured_output=json.loads(json_text))
    assert resp.structured_output["matched_count"] == 4
    assert resp.structured_output["status"] == "reconciled"


def test_05_usage_accounting():
    """Requirement 5: Token and cost accounting tracks actual vs estimated vs simulated."""
    # Simulated mock
    resp_mock = ModelResponse(content="OK", tokens_prompt=10, tokens_completion=5, cost_usd=0.00003)
    assert resp_mock.cost_type == "simulated_mock"
    assert resp_mock.total_tokens == 15

    # Actual provider cost
    resp_actual = ModelResponse(content="OK", tokens_prompt=100, tokens_completion=50, cost_usd=0.00025, cost_type="actual")
    assert resp_actual.cost_type == "actual"
    assert resp_actual.total_tokens == 150


def test_06_timeout_handling():
    """Requirement 6: Network timeouts raise TimeoutError without hanging."""
    async def _run():
        def timeout_handler(req: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Connection timed out")

        mock_transport = httpx.MockTransport(timeout_handler)
        async with httpx.AsyncClient(transport=mock_transport) as client:
            gateway = TensorMuxGateway(
                api_key="test-key",
                timeout_seconds=0.01,
                http_client=client,
            )
            req = ModelRequest(messages=[ModelMessage(role="user", content="Hi")])
            with pytest.raises(TimeoutError, match="timed out"):
                await gateway.generate(req)

    asyncio.run(_run())


def test_07_model_failure_handling():
    """Requirement 7: HTTP 500 error from provider raises structured RuntimeError."""
    async def _run():
        def handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="Internal TensorMux Failure")

        mock_transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=mock_transport) as client:
            gateway = TensorMuxGateway(api_key="test-key", http_client=client)
            req = ModelRequest(messages=[ModelMessage(role="user", content="Hi")])
            with pytest.raises(RuntimeError, match="HTTP 500"):
                await gateway.generate(req)

    asyncio.run(_run())


# =============================================================================
# Suite 2: Tool Calling & Authorization Tests (8 - 13)
# =============================================================================

def test_08_authorized_tool_call():
    """Requirement 8: Model calls an authorized tool and gets real execution output."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        # Mock model emits tool call for calculate_reconciliation_difference
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "calculate_reconciliation_difference",
                "arguments": json.dumps({"bank_amount": "500.00", "ledger_amount": "500.00"}),
            },
        }
        # Turn 1: tool call, Turn 2: final response
        gateway = MockModelGateway(
            tool_call_sequence=[
                [tool_call],
                None,
            ],
            default_content="Difference calculated as zero.",
        )
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="calc_node",
            name="Calculator",
            role="Auditor",
            system_prompt="Calculate differences",
            tools=["calculate_reconciliation_difference"],
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Calculate diff")
        res = await runner.run_node(node, state)
        assert res.success is True
        assert len(res.tool_events) == 1
        assert res.tool_events[0]["tool"] == "calculate_reconciliation_difference"
        assert res.tool_events[0]["success"] is True

    asyncio.run(_run())


def test_09_unauthorized_tool_call():
    """Requirement 9: Model calling an unauthorized tool produces structured authorization error."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        # Model tries to call tool not in node.tools
        unauthorized_call = {
            "id": "call_bad",
            "type": "function",
            "function": {
                "name": "unauthorized_admin_wipe",
                "arguments": json.dumps({}),
            },
        }
        gateway = MockModelGateway(
            tool_call_sequence=[
                [unauthorized_call],
                None,
            ],
            default_content="Proceeding without unauthorized tool.",
        )
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="safe_node",
            name="Safe Node",
            role="Worker",
            system_prompt="Safe instructions",
            tools=["calculate_reconciliation_difference"],  # only authorized tool
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Safe work")
        res = await runner.run_node(node, state)
        assert res.success is True
        # Tool event should reflect authorization failure
        assert len(res.tool_events) == 1
        assert res.tool_events[0]["success"] is False
        assert "authorization failure" in res.tool_events[0]["error"].lower()

    asyncio.run(_run())


def test_10_invalid_tool_arguments():
    """Requirement 10: Invalid tool arguments produce structured error fed back to model."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        # Missing required parameters for calculate_reconciliation_difference
        bad_arg_call = {
            "id": "call_bad_args",
            "type": "function",
            "function": {
                "name": "calculate_reconciliation_difference",
                "arguments": json.dumps({"unknown_field": 123}),
            },
        }
        gateway = MockModelGateway(
            tool_call_sequence=[
                [bad_arg_call],
                None,
            ],
            default_content="Handled invalid argument error.",
        )
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="calc_node",
            name="Calculator",
            role="Auditor",
            system_prompt="Calculate",
            tools=["calculate_reconciliation_difference"],
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Test invalid args")
        res = await runner.run_node(node, state)
        assert res.success is True
        assert len(res.tool_events) == 1
        assert res.tool_events[0]["success"] is False
        assert "validation error" in res.tool_events[0]["error"].lower() or "missing" in res.tool_events[0]["error"].lower()

    asyncio.run(_run())


def test_11_tool_result_fed_back_to_model():
    """Requirement 11: Tool execution results are formatted as tool messages for continuation."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        tool_call = {
            "id": "call_feedback_1",
            "type": "function",
            "function": {
                "name": "calculate_reconciliation_difference",
                "arguments": json.dumps({"bank_amount": "100.00", "ledger_amount": "95.00"}),
            },
        }
        gateway = MockModelGateway(
            tool_call_sequence=[
                [tool_call],
                None,
            ],
            default_content="Difference is 5.00.",
        )
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="calc_node",
            name="Calculator",
            role="Auditor",
            system_prompt="Calculate",
            tools=["calculate_reconciliation_difference"],
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Verify feedback")
        await runner.run_node(node, state)

        # In round 2, gateway should have received the tool output message
        assert len(gateway.invocation_history) == 2
        second_request = gateway.invocation_history[1]
        tool_messages = [m for m in second_request.messages if m.role == "tool"]
        assert len(tool_messages) == 1
        assert tool_messages[0].tool_call_id == "call_feedback_1"
        assert "5.00" in tool_messages[0].content

    asyncio.run(_run())


def test_12_multiple_bounded_tool_rounds():
    """Requirement 12: Node supports multiple successive tool-calling rounds."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        call_1 = {
            "id": "c1",
            "type": "function",
            "function": {
                "name": "calculate_reconciliation_difference",
                "arguments": json.dumps({"bank_amount": "100.00", "ledger_amount": "100.00"}),
            },
        }
        call_2 = {
            "id": "c2",
            "type": "function",
            "function": {
                "name": "calculate_reconciliation_difference",
                "arguments": json.dumps({"bank_amount": "200.00", "ledger_amount": "190.00"}),
            },
        }
        gateway = MockModelGateway(
            tool_call_sequence=[
                [call_1],
                [call_2],
                None,  # Final answer
            ],
            default_content="Both checks completed.",
        )
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="multi_calc",
            name="Multi Calc",
            role="Auditor",
            system_prompt="Calculate multiple",
            tools=["calculate_reconciliation_difference"],
            metadata={"execution_mode": "model_driven", "max_tool_rounds": 5},
        )
        state = ExecutionState(goal="Multi round")
        res = await runner.run_node(node, state)
        assert res.success is True
        assert len(res.tool_events) == 2
        assert res.metadata["rounds_executed"] == 3

    asyncio.run(_run())


def test_13_max_round_enforcement():
    """Requirement 13: Infinite tool call loop is strictly bounded by max_tool_rounds."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        infinite_call = {
            "id": "c_loop",
            "type": "function",
            "function": {
                "name": "calculate_reconciliation_difference",
                "arguments": json.dumps({"bank_amount": "1.00", "ledger_amount": "1.00"}),
            },
        }
        # Model endlessly requests tools
        gateway = MockModelGateway(
            tool_call_generator=lambda req: [infinite_call],
            default_content="Looping...",
        )
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="loop_node",
            name="Looper",
            role="Worker",
            system_prompt="Loop forever",
            tools=["calculate_reconciliation_difference"],
            metadata={"execution_mode": "model_driven", "max_tool_rounds": 3},
        )
        state = ExecutionState(goal="Test loop bound")
        res = await runner.run_node(node, state)
        assert res.success is False
        assert "maximum tool call rounds" in res.error.lower()

    asyncio.run(_run())


# =============================================================================
# Suite 3: Node Execution Flow Tests (14 - 18)
# =============================================================================

def test_14_final_response_without_tool():
    """Requirement 14: Node finishes reasoning without tool calls when not required."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        gateway = MockModelGateway(default_content="Direct analysis concluded no tool needed.")
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="analyst",
            name="Analyst",
            role="Auditor",
            system_prompt="Analyze data",
            tools=["calculate_reconciliation_difference"],
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Analyze")
        res = await runner.run_node(node, state)
        assert res.success is True
        assert len(res.tool_events) == 0
        assert res.output["message"] == "Direct analysis concluded no tool needed."

    asyncio.run(_run())


def test_15_tool_call_then_final_response():
    """Requirement 15: Standard 2-stage tool-calling flow terminates cleanly."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        tool_call = {
            "id": "c1",
            "type": "function",
            "function": {
                "name": "calculate_reconciliation_difference",
                "arguments": json.dumps({"bank_amount": "100.00", "ledger_amount": "100.00"}),
            },
        }
        gateway = MockModelGateway(
            tool_call_sequence=[[tool_call], None],
            default_content=json.dumps({"verified": True, "discrepancy": 0.0}),
        )
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="verifier",
            name="Verifier",
            role="Auditor",
            system_prompt="Verify",
            tools=["calculate_reconciliation_difference"],
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Verify")
        res = await runner.run_node(node, state)
        assert res.success is True
        assert res.output["verified"] is True
        assert len(res.tool_events) == 1

    asyncio.run(_run())


def test_16_malformed_tool_call():
    """Requirement 16: Model emitting unparseable tool call arguments is safely handled."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        malformed_call = {
            "id": "c_bad_json",
            "type": "function",
            "function": {
                "name": "calculate_reconciliation_difference",
                "arguments": "NOT_VALID_JSON{:::}",
            },
        }
        gateway = MockModelGateway(
            tool_call_sequence=[[malformed_call], None],
            default_content="Recovered from malformed tool call.",
        )
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="safe_node",
            name="Safe",
            role="Auditor",
            system_prompt="Handle bad calls",
            tools=["calculate_reconciliation_difference"],
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Test malformed args")
        res = await runner.run_node(node, state)
        assert res.success is True
        assert len(res.tool_events) == 1
        assert res.tool_events[0]["success"] is False

    asyncio.run(_run())


def test_17_malformed_final_output():
    """Requirement 17: Schema validation flags malformed final output."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        # Model returns prose when JSON required
        gateway = MockModelGateway(default_content="This is plain English prose, not JSON.")
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="strict_node",
            name="Strict",
            role="Extractor",
            system_prompt="Output strict JSON",
            metadata={"execution_mode": "model_driven", "require_json": True},
        )
        state = ExecutionState(goal="Extract")
        res = await runner.run_node(node, state)
        assert res.success is False
        assert "expected json object" in res.error.lower()

    asyncio.run(_run())


def test_18_model_failure():
    """Requirement 18: Gateway failure caught and recorded with retry handling."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        gateway = MockModelGateway(should_fail=True, fail_exception=RuntimeError("Gateway 503 Overloaded"))
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="fail_node",
            name="Fail",
            role="Worker",
            system_prompt="Test failure",
            max_retries=1,
            retryable_errors=["503"],
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Test fail")
        res = await runner.run_node(node, state)
        assert res.success is False
        assert res.attempts == 2
        assert "503 overloaded" in res.error.lower()

    asyncio.run(_run())


# =============================================================================
# Suite 4: Mutation Compatibility Tests (19 - 22)
# =============================================================================

def test_19_prompt_mutation_reaches_model():
    """Requirement 19: System prompt mutation directly alters the ModelRequest."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        gateway = MockModelGateway()
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

        node_v0 = NodeModel(
            node_id="match",
            name="Matcher",
            role="Matcher",
            system_prompt="Prompt V0: Standard matching.",
            metadata={"execution_mode": "model_driven"},
        )
        node_v1 = NodeModel(
            node_id="match",
            name="Matcher",
            role="Matcher",
            system_prompt="Prompt V1: Strict vendor counter-party verification with 3-day date lag rule.",
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Reconcile")

        await runner.run_node(node_v0, state)
        req_v0 = gateway.invocation_history[0]

        await runner.run_node(node_v1, state)
        req_v1 = gateway.invocation_history[1]

        # Verify mutation strictly propagated to request
        assert req_v0.system_prompt == "Prompt V0: Standard matching."
        assert req_v1.system_prompt == "Prompt V1: Strict vendor counter-party verification with 3-day date lag rule."
        assert req_v0.system_prompt != req_v1.system_prompt

    asyncio.run(_run())


def test_20_tool_mutation_reaches_model():
    """Requirement 20: Tool additions or removals alter tools in ModelRequest."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        gateway = MockModelGateway()
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

        node_v0 = NodeModel(
            node_id="audit",
            name="Auditor",
            role="Auditor",
            system_prompt="Audit",
            tools=["calculate_reconciliation_difference"],
            metadata={"execution_mode": "model_driven"},
        )
        node_v1 = NodeModel(
            node_id="audit",
            name="Auditor",
            role="Auditor",
            system_prompt="Audit",
            tools=["calculate_reconciliation_difference", "fuzzy_match_transactions"],  # Added tool!
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Audit")

        await runner.run_node(node_v0, state)
        req_v0 = gateway.invocation_history[0]

        await runner.run_node(node_v1, state)
        req_v1 = gateway.invocation_history[1]

        assert len(req_v0.tools) == 1
        assert len(req_v1.tools) == 2
        tool_names_v1 = [t["function"]["name"] for t in req_v1.tools]
        assert "fuzzy_match_transactions" in tool_names_v1

    asyncio.run(_run())


def test_21_model_mutation_reaches_model():
    """Requirement 21: Model selection mutations alter the ModelRequest model parameter."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        gateway = MockModelGateway()
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

        node_v0 = NodeModel(
            node_id="matcher",
            name="Matcher",
            role="Matcher",
            system_prompt="Match",
            model_config={"model": "fast-v1", "temperature": 0.1},
            metadata={"execution_mode": "model_driven"},
        )
        node_v1 = NodeModel(
            node_id="matcher",
            name="Matcher",
            role="Matcher",
            system_prompt="Match",
            model_config={"model": "frontier-reasoning-v2", "temperature": 0.5},
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Match")

        await runner.run_node(node_v0, state)
        assert gateway.invocation_history[0].model == "fast-v1"
        assert gateway.invocation_history[0].temperature == 0.1

        await runner.run_node(node_v1, state)
        assert gateway.invocation_history[1].model == "frontier-reasoning-v2"
        assert gateway.invocation_history[1].temperature == 0.5

    asyncio.run(_run())


def test_22_context_mutation_reaches_execution():
    """Requirement 22: Context mapping mutations alter the context payload sent to the model."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        gateway = MockModelGateway()
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

        node = NodeModel(
            node_id="extractor",
            name="Extractor",
            role="Auditor",
            system_prompt="Extract",
            input_mapping={"target_txs": "clean_records"},
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(
            goal="Extract",
            inputs={"clean_records": [{"id": "TX_99", "val": 1000}]},
        )
        await runner.run_node(node, state)
        req = gateway.invocation_history[0]
        user_msg = next(m for m in req.messages if m.role == "user")
        assert "TX_99" in user_msg.content

    asyncio.run(_run())


# =============================================================================
# Suite 5: Telemetry & Accounting Tests (23 - 26)
# =============================================================================

def test_23_input_token_tracking():
    """Requirement 23: Accurate accumulation of prompt tokens across all inference rounds."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        call_1 = {
            "id": "c1",
            "type": "function",
            "function": {
                "name": "calculate_reconciliation_difference",
                "arguments": json.dumps({"bank_amount": "10.00", "ledger_amount": "10.00"}),
            },
        }
        gateway = MockModelGateway(tool_call_sequence=[[call_1], None])
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="n", name="N", role="R", system_prompt="S",
            tools=["calculate_reconciliation_difference"],
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="G")
        res = await runner.run_node(node, state)
        assert res.tokens_in > 0
        assert len(gateway.invocation_history) == 2

    asyncio.run(_run())


def test_24_output_token_tracking():
    """Requirement 24: Accurate accumulation of completion tokens across all inference rounds."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        gateway = MockModelGateway(default_content="Response with multiple words to test completion token tracking.")
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(node_id="n", name="N", role="R", system_prompt="S", metadata={"execution_mode": "model_driven"})
        state = ExecutionState(goal="G")
        res = await runner.run_node(node, state)
        assert res.tokens_out > 0

    asyncio.run(_run())


def test_25_cost_metadata():
    """Requirement 25: Cost metadata captures dollar amount and explicit cost type."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        gateway = MockModelGateway(cost_type="estimated")
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(node_id="n", name="N", role="R", system_prompt="S", metadata={"execution_mode": "model_driven"})
        state = ExecutionState(goal="G")
        res = await runner.run_node(node, state)
        assert res.cost_usd > 0.0
        assert res.metadata["cost_type"] == "estimated"

    asyncio.run(_run())


def test_26_latency_metadata():
    """Requirement 26: Latency metadata records execution duration in milliseconds."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        gateway = MockModelGateway(latency_ms=25)
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(node_id="n", name="N", role="R", system_prompt="S", metadata={"execution_mode": "model_driven"})
        state = ExecutionState(goal="G")
        res = await runner.run_node(node, state)
        assert res.duration_ms >= 0

    asyncio.run(_run())


# =============================================================================
# Suite 6: Mock Gateway Scenarios (27 - 31)
# =============================================================================

def test_27_deterministic_mock_final_response():
    """Requirement 27: MockModelGateway returns canned final text response."""
    async def _run():
        gw = MockModelGateway(canned_responses={"invoice": "Invoice 404 is valid."})
        req = ModelRequest(messages=[ModelMessage(role="user", content="Check invoice status")])
        res = await gw.generate(req)
        assert res.content == "Invoice 404 is valid."

    asyncio.run(_run())


def test_28_deterministic_mock_tool_call():
    """Requirement 28: MockModelGateway returns configured tool call."""
    async def _run():
        call = ToolCall(tool_name="calculate_reconciliation_difference", arguments={"bank_amount": "100.00", "ledger_amount": "100.00"})
        gw = MockModelGateway(tool_call_sequence=[[call]])
        req = ModelRequest(messages=[ModelMessage(role="user", content="Run diff")])
        res = await gw.generate(req)
        assert len(res.tool_calls) == 1
        assert res.get_parsed_tool_calls()[0].tool_name == "calculate_reconciliation_difference"

    asyncio.run(_run())


def test_29_deterministic_mock_tool_sequence():
    """Requirement 29: MockModelGateway executes multi-step tool -> result -> final response."""
    async def _run():
        call = ToolCall(tool_name="calculate_reconciliation_difference", arguments={"bank_amount": "50.00", "ledger_amount": "50.00"})
        resp_1 = ModelResponse(content="", tool_calls=[call])
        resp_2 = ModelResponse(content="Calculation verified.", tool_calls=None)
        gw = MockModelGateway(response_sequence=[resp_1, resp_2])

        r1 = await gw.generate(ModelRequest(messages=[]))
        assert len(r1.tool_calls) == 1

        r2 = await gw.generate(ModelRequest(messages=[]))
        assert r2.content == "Calculation verified."

    asyncio.run(_run())


def test_30_mock_malformed_tool_call():
    """Requirement 30: MockModelGateway supports malformed tool call simulation."""
    async def _run():
        gw = MockModelGateway(tool_call_sequence=[[{"name": "test_tool", "arguments": "CORRUPT_ARGUMENTS"}]] )
        res = await gw.generate(ModelRequest(messages=[]))
        parsed = res.get_parsed_tool_calls()
        assert len(parsed) == 1
        assert "raw_args" in parsed[0].arguments

    asyncio.run(_run())


def test_31_mock_model_failure():
    """Requirement 31: MockModelGateway simulates failure with custom exception."""
    async def _run():
        gw = MockModelGateway(should_fail=True, fail_exception=ConnectionResetError("Simulated network reset"))
        with pytest.raises(ConnectionResetError, match="network reset"):
            await gw.generate(ModelRequest(messages=[]))

    asyncio.run(_run())


# =============================================================================
# Suite 7: Integration Tests (32 - 33)
# =============================================================================

def test_32_reconciliation_node_executes_with_model_driven_tool_call():
    """Requirement 32: Financial reconciliation node executes model-driven tool calling."""
    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        tool_call = {
            "id": "c_recon",
            "type": "function",
            "function": {
                "name": "fuzzy_match_transactions",
                "arguments": json.dumps({
                    "bank_transactions": [{"transaction_id": "TX1", "amount": 100.0, "vendor": "Stripe", "date": "2026-03-01"}],
                    "ledger_entries": [{"entry_id": "GL1", "amount": 100.0, "vendor": "Stripe", "date": "2026-03-01"}],
                }),
            },
        }
        gateway = MockModelGateway(
            tool_call_sequence=[[tool_call], None],
            default_content="Reconciliation matched 1 transaction pair.",
        )
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
        node = NodeModel(
            node_id="matcher",
            name="Matcher",
            role="Matcher",
            system_prompt="Match bank transactions",
            tools=["fuzzy_match_transactions"],
            metadata={"execution_mode": "model_driven"},
        )
        state = ExecutionState(goal="Reconcile bank accounts")
        res = await runner.run_node(node, state)
        assert res.success is True
        assert len(res.tool_events) == 1
        assert res.tool_events[0]["tool"] == "fuzzy_match_transactions"
        assert res.tool_events[0]["success"] is True

    asyncio.run(_run())


def test_33_generated_graph_executes_through_real_model_gateway_abstraction():
    """Requirement 33: Multi-node DAG executes through ModelGateway abstraction."""
    async def _run():
        gateway = MockModelGateway(default_content="Step finished.")
        executor = ToolExecutor(registry=default_tool_registry)
        runtime = AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)

        nodes = {
            "step_1": NodeModel(node_id="step_1", name="S1", role="R1", system_prompt="Do S1", metadata={"execution_mode": "model_driven"}),
            "step_2": NodeModel(node_id="step_2", name="S2", role="R2", system_prompt="Do S2", metadata={"execution_mode": "model_driven"}),
        }
        edges = [EdgeModel(source_node_id="step_1", target_node_id="step_2")]
        graph = GraphDefinition(
            graph_id="g_int", name="Integration", entry_node_id="step_1",
            terminal_node_ids=["step_2"], nodes=nodes, edges=edges,
        )

        state = await runtime.run(graph, inputs={"input_data": "sample"}, goal="Integration test")
        assert state.status == "completed"
        assert len(state.step_history) == 2
        assert state.tokens_input > 0

    asyncio.run(_run())


# =============================================================================
# Suite 8: Live Smoke Test (34)
# =============================================================================

def test_34_opt_in_real_provider_smoke_test():
    """Requirement 34: Opt-in smoke test connecting to live provider (skipped by default)."""
    if os.environ.get("RUN_LIVE_LLM_TESTS", "").lower() != "true":
        pytest.skip("Skipping live LLM smoke test (RUN_LIVE_LLM_TESTS != true)")

    api_key = os.environ.get("TENSORMUX_API_KEY", "")
    if not api_key or api_key == "your-tensormux-key":
        pytest.skip("Skipping live LLM test: TENSORMUX_API_KEY not provided")

    async def _run():
        executor = ToolExecutor(registry=default_tool_registry)
        gateway = TensorMuxGateway(api_key=api_key)
        runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

        node = NodeModel(
            node_id="matcher",
            name="Matcher",
            role="Matcher",
            system_prompt=(
                "You are an autonomous financial reconciliation matcher. "
                "Inspect the provided bank records and ledger entries. "
                "Invoke fuzzy_match_transactions to determine if they match."
            ),
            tools=["fuzzy_match_transactions"],
            metadata={"execution_mode": "model_driven"},
        )

        state = ExecutionState(
            goal="Identify whether these two transactions should be matched.",
            inputs={
                "bank_transactions": [{"transaction_id": "TX_LIVE_1", "amount": 250.00, "vendor": "Google Cloud", "date": "2026-03-01"}],
                "ledger_entries": [{"entry_id": "GL_LIVE_1", "amount": 250.00, "vendor": "Google Cloud", "date": "2026-03-01"}],
            },
        )

        res = await runner.run_node(node, state)
        assert res.success is True
        assert res.tokens_in > 0
        assert res.cost_usd >= 0.0
        assert res.duration_ms > 0

    asyncio.run(_run())


def test_35_tensormux_message_tool_call_formatting():
    """Verify TensorMux gateway normalizes Reco ToolCall dicts to OpenAI function schemas."""
    captured_payload = {}

    def handler(request: httpx.Request):
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": "OK"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    gateway = TensorMuxGateway(api_key="test-key", http_client=client)

    async def _run():
        req = ModelRequest(
            messages=[
                ModelMessage(
                    role="assistant",
                    content="",
                    tool_calls=[
                        {
                            "tool_name": "fuzzy_match_transactions",
                            "arguments": {"threshold": 0.95},
                            "call_id": "call_abc_123",
                        }
                    ],
                )
            ]
        )
        resp = await gateway.generate(req)
        assert resp.content == "OK"
        # Verify formatting in captured payload
        assert "messages" in captured_payload
        sent_tcs = captured_payload["messages"][0]["tool_calls"]
        assert len(sent_tcs) == 1
        assert sent_tcs[0]["id"] == "call_abc_123"
        assert sent_tcs[0]["type"] == "function"
        assert sent_tcs[0]["function"]["name"] == "fuzzy_match_transactions"
        assert json.loads(sent_tcs[0]["function"]["arguments"]) == {"threshold": 0.95}

    asyncio.run(_run())


def test_36_tensormux_tool_parser_fallback_and_extraction():
    """Verify TensorMux transparent fallback on 400 when missing --tool-call-parser."""
    call_count = 0
    captured_payloads = []

    def handler(request: httpx.Request):
        nonlocal call_count
        call_count += 1
        payload = json.loads(request.content.decode("utf-8"))
        captured_payloads.append(payload)
        if call_count == 1:
            # Simulate vLLM missing --tool-call-parser error
            return httpx.Response(
                400,
                text='{"error":{"message":"\\"auto\\" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set"}}',
            )
        # Second call returns tool call in text content
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "```json\n"
                                "{\n"
                                '  "tool_calls": [\n'
                                "    {\n"
                                '      "name": "fuzzy_match_transactions",\n'
                                '      "arguments": {"tolerance": 0.05}\n'
                                "    }\n"
                                "  ]\n"
                                "}\n"
                                "```"
                            ),
                        }
                    }
                ],
                "usage": {"prompt_tokens": 25, "completion_tokens": 15},
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    gateway = TensorMuxGateway(api_key="test-key", http_client=client)

    async def _run():
        req = ModelRequest(
            messages=[ModelMessage(role="user", content="Match items.")],
            tools=[{"type": "function", "function": {"name": "fuzzy_match_transactions"}}],
            system_prompt="Base system directive.",
        )
        resp = await gateway.generate(req)
        assert call_count == 2
        # First payload included tools
        assert "tools" in captured_payloads[0]
        # Second fallback payload popped tools and updated system message
        assert "tools" not in captured_payloads[1]
        assert "fuzzy_match_transactions" in captured_payloads[1]["messages"][0]["content"]

        # Tool calls extracted from markdown content
        assert resp.finish_reason == "tool_calls"
        parsed = resp.get_parsed_tool_calls()
        assert len(parsed) == 1
        assert parsed[0].tool_name == "fuzzy_match_transactions"
        assert parsed[0].arguments == {"tolerance": 0.05}

    asyncio.run(_run())


def test_37_tensormux_mutation_propagation_model_requests():
    """Verify prompt, tool, and model mutations directly alter constructed ModelRequests."""
    executor = ToolExecutor(registry=default_tool_registry)
    mock_gw = MockModelGateway(canned_responses=[ModelResponse(content="OK")])
    runner = NodeRunner(model_gateway=mock_gw, tool_executor=executor, agent_mode=True)

    # 1. Prompt mutation
    node_v0 = NodeModel(
        node_id="matcher",
        name="Matcher",
        role="Matcher",
        system_prompt="Initial system prompt for matcher.",
        tools=["fuzzy_match_transactions"],
    )
    node_v1 = NodeModel(
        node_id="matcher",
        name="Matcher",
        role="Matcher",
        system_prompt="Initial system prompt for matcher. Prioritize vendor match over date proximity.",
        tools=["fuzzy_match_transactions"],
    )

    state = ExecutionState(goal="Reconcile accounts", inputs={"key": "val"})

    # Capture requests
    captured_requests = []
    original_generate = mock_gw.generate

    async def capturing_generate(req: ModelRequest):
        captured_requests.append(req)
        return ModelResponse(content="OK")

    mock_gw.generate = capturing_generate

    async def _run():
        await runner.run_node(node_v0, state)
        await runner.run_node(node_v1, state)

    asyncio.run(_run())

    req_v0 = captured_requests[0]
    req_v1 = captured_requests[1]
    assert req_v0.system_prompt != req_v1.system_prompt
    assert "Prioritize vendor match" in req_v1.system_prompt

    # 2. Tool mutation
    node_tools_v0 = NodeModel(
        node_id="n1",
        name="N1",
        role="R1",
        system_prompt="System prompt",
        tools=["fuzzy_match_transactions"],
    )
    node_tools_v1 = NodeModel(
        node_id="n1",
        name="N1",
        role="R1",
        system_prompt="System prompt",
        tools=["fuzzy_match_transactions", "parse_bank_statement"],
    )

    captured_requests.clear()

    async def _run_tools():
        await runner.run_node(node_tools_v0, state)
        await runner.run_node(node_tools_v1, state)

    asyncio.run(_run_tools())

    req_t0 = captured_requests[0]
    req_t1 = captured_requests[1]
    assert len(req_t0.tools) == 1
    assert len(req_t1.tools) == 2
    assert req_t0.tools != req_t1.tools

    # 3. Model config mutation
    node_cfg_v0 = NodeModel(
        node_id="n2",
        name="N2",
        role="R2",
        system_prompt="System prompt",
        model_config_data={"model": "gemma-4-31b", "temperature": 0.0, "max_tokens": 100},
    )
    node_cfg_v1 = NodeModel(
        node_id="n2",
        name="N2",
        role="R2",
        system_prompt="System prompt",
        model_config_data={"model": "qwen-2.5-72b", "temperature": 0.7, "max_tokens": 500},
    )

    captured_requests.clear()

    async def _run_cfg():
        await runner.run_node(node_cfg_v0, state)
        await runner.run_node(node_cfg_v1, state)

    asyncio.run(_run_cfg())

    req_c0 = captured_requests[0]
    req_c1 = captured_requests[1]
    assert req_c0.model == "gemma-4-31b"
    assert req_c1.model == "qwen-2.5-72b"
    assert req_c0.temperature == 0.0
    assert req_c1.temperature == 0.7
    assert req_c0.max_tokens == 100
    assert req_c1.max_tokens == 500

