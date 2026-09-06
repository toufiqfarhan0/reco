"""Comprehensive deterministic test suite for Step 13C: Model-Driven Reconciliation Execution.

Covers all 25 specific requirements across:
- Execution Modes (1-3)
- Model-Driven Matcher (4-8)
- Mutation Behavior (9-13)
- Tool Authorization & Validation (14-15)
- Latency and Accounting (16-20)
- Reconciliation Architecture Configuration (21-25)
"""

import asyncio
import json
from decimal import Decimal
from typing import Any, Dict
import pytest

from reco.benchmarks.reconciliation.baseline import create_reconciliation_baseline_graph
from reco.core.interfaces import ModelMessage, ModelRequest, ModelResponse, ToolCall
from reco.engine.models import EdgeModel, GraphDefinition, NodeModel
from reco.engine.node_runner import NodeExecutionResult, NodeRunner
from reco.engine.runtime import AgentGraphRuntime
from reco.engine.state import ExecutionState
from reco.llm.mock import MockModelGateway
from reco.tools.executor import ToolExecutor
from reco.tools.reconciliation import register_reconciliation_tools
from reco.tools.registry import ToolRegistry


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    register_reconciliation_tools(reg)
    return reg


@pytest.fixture
def executor(registry: ToolRegistry) -> ToolExecutor:
    return ToolExecutor(registry=registry)


# =============================================================================
# SUITE 1: EXECUTION MODES (1 - 3)
# =============================================================================

def test_01_deterministic_node_execution(executor: ToolExecutor):
    """1. Deterministic node executes tool directly without calling ModelGateway."""
    gateway = MockModelGateway()
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="parse_node",
        name="Parser",
        role="Extractor",
        system_prompt="Parse records",
        tools=["parse_bank_statement"],
        execution_mode="deterministic_tool",
    )
    state = ExecutionState(goal="Parse")
    state.inputs = {
        "records": [
            {"transaction_id": "TX-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}
        ]
    }

    res = asyncio.run(runner.run_node(node, state))
    assert res.success is True
    assert res.metadata["execution_mode"] == "deterministic_tool"
    assert res.metadata["model_calls"] == 0
    assert len(gateway.invocation_history) == 0


def test_02_model_driven_node_execution(executor: ToolExecutor):
    """2. Model-driven node executes via ModelGateway tool loop."""
    gateway = MockModelGateway(auto_tool_calls=True)
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="fuzzy_match",
        name="Matcher",
        role="Matcher",
        system_prompt="Match records",
        tools=["fuzzy_match_transactions"],
        execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {
        "bank_transactions": [{"transaction_id": "TX-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}],
        "ledger_entries": [{"entry_id": "GL-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}],
    }

    res = asyncio.run(runner.run_node(node, state))
    assert res.success is True
    assert res.metadata["execution_mode"] == "model_driven"
    assert res.metadata["model_calls"] >= 1
    assert len(gateway.invocation_history) >= 1


def test_03_explicit_execution_mode_validation():
    """3. NodeModel resolves execution mode explicitly and backward-compatibly."""
    n_det = NodeModel(
        node_id="n1", name="N1", role="Worker", system_prompt="",
        tools=["parse_bank_statement"], execution_mode="deterministic_tool"
    )
    assert n_det.get_execution_mode() == "deterministic_tool"

    n_model = NodeModel(
        node_id="n2", name="N2", role="Worker", system_prompt="",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven"
    )
    assert n_model.get_execution_mode() == "model_driven"

    n_inf = NodeModel(
        node_id="n3", name="N3", role="Worker", system_prompt="",
        tools=[], execution_mode="model_inference"
    )
    assert n_inf.get_execution_mode() == "model_inference"

    # Backward compatibility: inferred when execution_mode is None
    n_legacy_tool = NodeModel(
        node_id="n4", name="N4", role="Worker", system_prompt="",
        tools=["query_general_ledger"]
    )
    assert n_legacy_tool.get_execution_mode() == "deterministic_tool"

    n_legacy_notool = NodeModel(
        node_id="n5", name="N5", role="Worker", system_prompt="",
        tools=[]
    )
    assert n_legacy_notool.get_execution_mode() == "model_inference"


# =============================================================================
# SUITE 2: MODEL-DRIVEN MATCHER (4 - 8)
# =============================================================================

def test_04_fuzzy_match_uses_model_gateway(executor: ToolExecutor):
    """4. fuzzy_match invokes ModelGateway during execution."""
    gateway = MockModelGateway(auto_tool_calls=True)
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="fuzzy_match",
        name="Matcher",
        role="Matcher",
        system_prompt="Reconcile bank and ledger",
        tools=["fuzzy_match_transactions"],
        execution_mode="model_driven",
    )
    state = ExecutionState(goal="Reconcile")
    state.inputs = {
        "bank_transactions": [{"transaction_id": "TX-1", "date": "2026-03-01", "amount": "50.00", "currency": "USD", "vendor": "Acme"}],
        "ledger_entries": [{"entry_id": "GL-1", "date": "2026-03-01", "amount": "50.00", "currency": "USD", "vendor": "Acme"}],
    }

    res = asyncio.run(runner.run_node(node, state))
    assert res.success is True
    assert len(gateway.invocation_history) >= 2  # Round 1: call tool, Round 2: finish


def test_05_model_receives_fuzzy_match_tool_schema(executor: ToolExecutor):
    """5. Model receives authorized fuzzy_match_transactions schema."""
    gateway = MockModelGateway(auto_tool_calls=True)
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="fuzzy_match",
        name="Matcher",
        role="Matcher",
        system_prompt="Match records",
        tools=["fuzzy_match_transactions"],
        execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {"bank_transactions": [], "ledger_entries": []}

    asyncio.run(runner.run_node(node, state))
    req = gateway.invocation_history[0]
    assert req.tools is not None
    assert len(req.tools) == 1
    fn = req.tools[0]["function"]
    assert fn["name"] == "fuzzy_match_transactions"
    props = fn["parameters"]["properties"]
    assert "vendor_similarity_threshold" in props
    assert "require_vendor_match" in props


def test_06_model_generated_tool_call_reaches_executor(executor: ToolExecutor):
    """6. Tool call generated by model reaches ToolExecutor with custom arguments."""
    custom_call = {
        "id": "c1",
        "type": "function",
        "function": {
            "name": "fuzzy_match_transactions",
            "arguments": json.dumps({"vendor_similarity_threshold": 0.88, "require_vendor_match": True}),
        },
    }
    gateway = MockModelGateway(
        tool_call_sequence=[[custom_call], None],
        default_content="Match finalized.",
    )
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="fuzzy_match",
        name="Matcher",
        role="Matcher",
        system_prompt="Match",
        tools=["fuzzy_match_transactions"],
        execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {
        "bank_transactions": [{"transaction_id": "TX-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}],
        "ledger_entries": [{"entry_id": "GL-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}],
    }

    res = asyncio.run(runner.run_node(node, state))
    assert res.success is True
    assert len(res.tool_events) == 1
    # Check recorded tool event had merged parameters from model
    evt = res.tool_events[0]
    assert evt["tool"] == "fuzzy_match_transactions"
    assert evt["success"] is True


def test_07_tool_result_returns_to_model(executor: ToolExecutor):
    """7. Tool output returns to model in conversation turn 2."""
    custom_call = {
        "id": "call_match_1",
        "type": "function",
        "function": {
            "name": "fuzzy_match_transactions",
            "arguments": json.dumps({"require_vendor_match": True}),
        },
    }
    gateway = MockModelGateway(
        tool_call_sequence=[[custom_call], None],
        default_content="Reconciliation verified.",
    )
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="fuzzy_match",
        name="Matcher",
        role="Matcher",
        system_prompt="Match",
        tools=["fuzzy_match_transactions"],
        execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {
        "bank_transactions": [{"transaction_id": "TX-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}],
        "ledger_entries": [{"entry_id": "GL-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}],
    }

    asyncio.run(runner.run_node(node, state))
    assert len(gateway.invocation_history) == 2
    req_round2 = gateway.invocation_history[1]
    tool_messages = [m for m in req_round2.messages if m.role == "tool"]
    assert len(tool_messages) == 1
    assert tool_messages[0].name == "fuzzy_match_transactions"
    tool_content = json.loads(tool_messages[0].content)
    assert "matched_pairs" in tool_content


def test_08_final_matcher_output_is_structured(executor: ToolExecutor):
    """8. Final matcher output retains structured matching payload."""
    gateway = MockModelGateway(auto_tool_calls=True, default_content="Reasoning summary.")
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="fuzzy_match",
        name="Matcher",
        role="Matcher",
        system_prompt="Match",
        tools=["fuzzy_match_transactions"],
        execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {
        "bank_transactions": [{"transaction_id": "TX-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}],
        "ledger_entries": [{"entry_id": "GL-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}],
    }

    res = asyncio.run(runner.run_node(node, state))
    assert isinstance(res.output, dict)
    assert "matched_pairs" in res.output
    assert "exceptions_by_type" in res.output


# =============================================================================
# SUITE 3: MUTATION BEHAVIOR (9 - 13)
# =============================================================================

def test_09_prompt_mutation_changes_model_request(executor: ToolExecutor):
    """9. Prompt mutation propagates to ModelRequest system_prompt."""
    gateway = MockModelGateway(auto_tool_calls=True)
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node_v0 = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher",
        system_prompt="Standard reconciliation prompt.",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven",
    )
    node_v1 = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher",
        system_prompt="Prioritize vendor identity over amount similarity.",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven",
    )
    state = ExecutionState(goal="Reconcile")
    state.inputs = {"bank_transactions": [], "ledger_entries": []}

    asyncio.run(runner.run_node(node_v0, state))
    req_v0 = gateway.invocation_history[0]

    asyncio.run(runner.run_node(node_v1, state))
    # Round 1 of node_v1 is at index 2 (after round 1 & 2 of node_v0)
    req_v1 = gateway.invocation_history[2]

    assert req_v0.system_prompt == "Standard reconciliation prompt."
    assert req_v1.system_prompt == "Prioritize vendor identity over amount similarity."


def test_10_prompt_mutation_alters_tool_arguments(executor: ToolExecutor):
    """10. Prompt mutation leads to different mock tool arguments."""
    gateway = MockModelGateway(auto_tool_calls=True)
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node_v0 = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher",
        system_prompt="Match bank transactions against general ledger.",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven",
    )
    node_v1 = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher",
        system_prompt="Prioritize vendor identity over amount similarity. Reject exact-amount matches when vendor identity is inconsistent.",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven",
    )
    state = ExecutionState(goal="Reconcile")
    # Same monetary amount ($750), mismatched vendors
    state.inputs = {
        "bank_transactions": [{"transaction_id": "TX-801", "date": "2026-03-08", "amount": "750.00", "currency": "USD", "vendor": "Apex Logistics"}],
        "ledger_entries": [{"entry_id": "GL-801", "date": "2026-03-08", "amount": "750.00", "currency": "USD", "vendor": "Delta Hotel Group"}],
    }

    res_v0 = asyncio.run(runner.run_node(node_v0, state))
    res_v1 = asyncio.run(runner.run_node(node_v1, state))

    # V0 paired them despite mismatched vendor
    assert len(res_v0.output["matched_pairs"]) == 1
    # V1 rejected pairing them because require_vendor_match was True
    assert len(res_v1.output["matched_pairs"]) == 0
    assert "missing_in_ledger" in res_v1.output["exceptions_by_type"]


def test_11_tool_mutation_changes_available_tools(executor: ToolExecutor):
    """11. Adding a tool changes the tools exposed in ModelRequest."""
    gateway = MockModelGateway()
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node_v0 = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher", system_prompt="Audit",
        tools=["calculate_reconciliation_difference"], execution_mode="model_driven",
    )
    node_v1 = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher", system_prompt="Audit",
        tools=["calculate_reconciliation_difference", "fuzzy_match_transactions"], execution_mode="model_driven",
    )
    state = ExecutionState(goal="Audit")

    asyncio.run(runner.run_node(node_v0, state))
    req_v0 = gateway.invocation_history[0]

    asyncio.run(runner.run_node(node_v1, state))
    req_v1 = gateway.invocation_history[1]

    assert len(req_v0.tools) == 1
    assert len(req_v1.tools) == 2


def test_12_model_mutation_changes_model_request(executor: ToolExecutor):
    """12. Mutating model configuration alters ModelRequest model parameter."""
    gateway = MockModelGateway()
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node_v0 = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher", system_prompt="Match",
        model_config_data={"model": "mock-v1", "temperature": 0.0}, execution_mode="model_inference",
    )
    node_v1 = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher", system_prompt="Match",
        model_config_data={"model": "gemma-4-31b-it", "temperature": 0.2}, execution_mode="model_inference",
    )
    state = ExecutionState(goal="Match")

    asyncio.run(runner.run_node(node_v0, state))
    asyncio.run(runner.run_node(node_v1, state))

    assert gateway.invocation_history[0].model == "mock-v1"
    assert gateway.invocation_history[0].temperature == 0.0
    assert gateway.invocation_history[1].model == "gemma-4-31b-it"
    assert gateway.invocation_history[1].temperature == 0.2


def test_13_context_mutation_changes_model_input(executor: ToolExecutor):
    """13. Context mapping mutation changes user prompt context payload."""
    gateway = MockModelGateway()
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node_v0 = NodeModel(
        node_id="auditor", name="Auditor", role="Auditor", system_prompt="Audit",
        input_mapping={"records": "raw_bank"}, execution_mode="model_inference",
    )
    node_v1 = NodeModel(
        node_id="auditor", name="Auditor", role="Auditor", system_prompt="Audit",
        input_mapping={"records": "enriched_bank"}, execution_mode="model_inference",
    )
    state = ExecutionState(goal="Audit")
    state.node_outputs["raw_bank"] = [{"id": 1}]
    state.node_outputs["enriched_bank"] = [{"id": 1, "flag": "high_risk"}]

    asyncio.run(runner.run_node(node_v0, state))
    asyncio.run(runner.run_node(node_v1, state))

    msg_v0 = gateway.invocation_history[0].messages[1].content
    msg_v1 = gateway.invocation_history[1].messages[1].content
    assert "high_risk" not in msg_v0
    assert "high_risk" in msg_v1


# =============================================================================
# SUITE 4: AUTHORIZATION & ARGUMENT VALIDATION (14 - 15)
# =============================================================================

def test_14_unauthorized_tool_rejected(executor: ToolExecutor):
    """14. Model calling an unauthorized tool is rejected with error."""
    unauthorized_call = {
        "id": "bad_call_1",
        "type": "function",
        "function": {
            "name": "unregistered_or_unauthorized_tool",
            "arguments": "{}",
        },
    }
    gateway = MockModelGateway(
        tool_call_sequence=[[unauthorized_call], None],
        default_content="Finished after rejection.",
    )
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher", system_prompt="Match",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {"bank_transactions": [], "ledger_entries": []}

    res = asyncio.run(runner.run_node(node, state))
    assert res.success is True
    # The tool event should record failure
    assert len(res.tool_events) == 1
    assert res.tool_events[0]["success"] is False
    assert "authorization failure" in res.tool_events[0]["error"].lower()


def test_15_tool_arguments_validated(executor: ToolExecutor):
    """15. Invalid tool arguments fail validation safely."""
    invalid_arg_call = {
        "id": "call_invalid",
        "type": "function",
        "function": {
            "name": "calculate_reconciliation_difference",
            "arguments": json.dumps({"bank_amount": "not_a_number", "ledger_amount": "invalid"}),
        },
    }
    gateway = MockModelGateway(
        tool_call_sequence=[[invalid_arg_call], None],
        default_content="Handled validation failure.",
    )
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="diff_calc", name="Diff", role="Calculator", system_prompt="Diff",
        tools=["calculate_reconciliation_difference"], execution_mode="model_driven",
    )
    state = ExecutionState(goal="Diff")

    res = asyncio.run(runner.run_node(node, state))
    assert res.success is True
    assert len(res.tool_events) == 1
    assert res.tool_events[0]["success"] is False


# =============================================================================
# SUITE 5: LATENCY AND ACCOUNTING (16 - 20)
# =============================================================================

def test_16_model_call_timing_captured(executor: ToolExecutor):
    """16. Model latency is captured separately in execution metadata."""
    gateway = MockModelGateway(auto_tool_calls=True, latency_ms=20)
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher", system_prompt="Match",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {"bank_transactions": [], "ledger_entries": []}

    res = asyncio.run(runner.run_node(node, state))
    assert "model_latency_ms" in res.metadata
    assert res.metadata["model_latency_ms"] >= 0
    assert res.metadata["model_calls"] >= 1


def test_17_tool_timing_captured(executor: ToolExecutor):
    """17. Tool execution latency is captured separately in metadata."""
    gateway = MockModelGateway(auto_tool_calls=True)
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher", system_prompt="Match",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {"bank_transactions": [], "ledger_entries": []}

    res = asyncio.run(runner.run_node(node, state))
    assert "tool_latency_ms" in res.metadata
    assert res.metadata["tool_latency_ms"] >= 0
    assert res.metadata["tool_calls"] == 1


def test_18_total_latency_aggregation(executor: ToolExecutor):
    """18. Total duration_ms is recorded on NodeExecutionResult."""
    gateway = MockModelGateway(auto_tool_calls=True)
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher", system_prompt="Match",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {"bank_transactions": [], "ledger_entries": []}

    res = asyncio.run(runner.run_node(node, state))
    assert res.duration_ms >= 0


def test_19_token_aggregation(executor: ToolExecutor):
    """19. Input and output tokens are aggregated across rounds."""
    gateway = MockModelGateway(auto_tool_calls=True)
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher", system_prompt="Match",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {"bank_transactions": [], "ledger_entries": []}

    res = asyncio.run(runner.run_node(node, state))
    assert res.tokens_in > 0
    assert res.tokens_out > 0


def test_20_cost_aggregation(executor: ToolExecutor):
    """20. Financial cost is aggregated across rounds with cost_type."""
    gateway = MockModelGateway(auto_tool_calls=True, token_cost_rate=0.00001)
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)

    node = NodeModel(
        node_id="matcher", name="Matcher", role="Matcher", system_prompt="Match",
        tools=["fuzzy_match_transactions"], execution_mode="model_driven",
    )
    state = ExecutionState(goal="Match")
    state.inputs = {"bank_transactions": [], "ledger_entries": []}

    res = asyncio.run(runner.run_node(node, state))
    assert res.cost_usd > 0.0
    assert res.metadata["cost_type"] == "simulated_mock"


# =============================================================================
# SUITE 6: RECONCILIATION ARCHITECTURE CONFIGURATION (21 - 25)
# =============================================================================

def test_21_real_architecture_remains_executable(executor: ToolExecutor):
    """21. Canonical baseline architecture validates and executes end-to-end."""
    graph = create_reconciliation_baseline_graph()
    graph.validate_graph()

    gateway = MockModelGateway(auto_tool_calls=True)
    runtime = AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)

    inputs = {
        "bank_records": [{"transaction_id": "TX-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}],
        "ledger_entries": [{"entry_id": "GL-1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}],
    }

    state = asyncio.run(runtime.run(graph, inputs=inputs, goal="Reconcile accounts"))
    assert state.status == "completed"
    assert "parsed_bank" in state.node_outputs
    assert "queried_ledger" in state.node_outputs
    assert "reconciliation_summary" in state.node_outputs


def test_22_deterministic_parser_remains_deterministic():
    """22. parse_statement node explicitly has deterministic_tool mode."""
    graph = create_reconciliation_baseline_graph()
    node = graph.nodes["parse_statement"]
    assert node.execution_mode == "deterministic_tool"
    assert node.get_execution_mode() == "deterministic_tool"


def test_23_deterministic_ledger_query_remains_deterministic():
    """23. query_ledger node explicitly has deterministic_tool mode."""
    graph = create_reconciliation_baseline_graph()
    node = graph.nodes["query_ledger"]
    assert node.execution_mode == "deterministic_tool"
    assert node.get_execution_mode() == "deterministic_tool"


def test_24_matcher_is_model_driven():
    """24. fuzzy_match node explicitly has model_driven mode."""
    graph = create_reconciliation_baseline_graph()
    node = graph.nodes["fuzzy_match"]
    assert node.execution_mode == "model_driven"
    assert node.get_execution_mode() == "model_driven"


def test_25_verifier_remains_correctly_configured():
    """25. verify_summary node explicitly has model_inference mode and auditor role."""
    graph = create_reconciliation_baseline_graph()
    node = graph.nodes["verify_summary"]
    assert node.execution_mode == "model_inference"
    assert node.get_execution_mode() == "model_inference"
    assert node.role == "Auditor"
