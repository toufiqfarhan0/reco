"""Comprehensive deterministic tests for Reco's Lightweight Agent Graph Runtime."""

import asyncio
from decimal import Decimal
import pytest

from reco.engine.models import EdgeModel, GraphDefinition, GraphValidationError, NodeModel
from reco.engine.node_runner import NodeRunner
from reco.engine.reconciliation_demo import create_reconciliation_demo_graph, run_reconciliation_demo
from reco.engine.runtime import AgentGraphRuntime
from reco.engine.state import ExecutionState
from reco.llm.mock import MockModelGateway
from reco.tools.executor import ToolExecutor
from reco.tools.reconciliation import register_reconciliation_tools
from reco.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    register_reconciliation_tools(reg)
    return reg


@pytest.fixture
def executor(registry: ToolRegistry) -> ToolExecutor:
    return ToolExecutor(registry=registry)


@pytest.fixture
def gateway() -> MockModelGateway:
    return MockModelGateway(
        default_content="Reconciliation step finished successfully.",
        canned_responses={"fraud": "Audit check verified zero unrecorded variances."},
    )


@pytest.fixture
def runtime(gateway: MockModelGateway, executor: ToolExecutor) -> AgentGraphRuntime:
    return AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)


# ---------------------------------------------------------------------------
# Part 1: Graph Validation Tests (1 - 6)
# ---------------------------------------------------------------------------

def test_1_valid_dag_accepted():
    """Test 1: Valid DAG passes validation."""
    nodes = {
        "A": NodeModel(node_id="A", name="Start", role="Init", system_prompt="Start"),
        "B": NodeModel(node_id="B", name="Middle", role="Worker", system_prompt="Work"),
        "C": NodeModel(node_id="C", name="End", role="Finalizer", system_prompt="End"),
    }
    edges = [
        EdgeModel(source_node_id="A", target_node_id="B"),
        EdgeModel(source_node_id="B", target_node_id="C"),
    ]
    graph = GraphDefinition(
        graph_id="g1", name="Valid DAG", entry_node_id="A", terminal_node_ids=["C"], nodes=nodes, edges=edges
    )
    graph.validate_graph()  # Should not raise


def test_2_duplicate_node_rejected():
    """Test 2: Graph with duplicate node IDs or edge rejected."""
    nodes = {
        "A": NodeModel(node_id="A", name="Start", role="Init", system_prompt="Start"),
        "B": NodeModel(node_id="B", name="End", role="End", system_prompt="End"),
    }
    # Duplicate edge
    edges = [
        EdgeModel(source_node_id="A", target_node_id="B"),
        EdgeModel(source_node_id="A", target_node_id="B"),
    ]
    graph = GraphDefinition(graph_id="g2", name="Dup Edge", entry_node_id="A", nodes=nodes, edges=edges)
    with pytest.raises(GraphValidationError, match="Duplicate edge"):
        graph.validate_graph()


def test_3_missing_edge_node_rejected():
    """Test 3: Edge pointing to non-existent node is rejected."""
    nodes = {
        "A": NodeModel(node_id="A", name="Start", role="Init", system_prompt="Start"),
    }
    edges = [EdgeModel(source_node_id="A", target_node_id="MISSING")]
    graph = GraphDefinition(graph_id="g3", name="Bad Edge", entry_node_id="A", nodes=nodes, edges=edges)
    with pytest.raises(GraphValidationError, match="does not exist in graph nodes"):
        graph.validate_graph()


def test_4_missing_entry_rejected():
    """Test 4: Missing entry node rejected."""
    nodes = {
        "A": NodeModel(node_id="A", name="Node", role="Role", system_prompt="Prompt"),
    }
    graph = GraphDefinition(graph_id="g4", name="No Entry", entry_node_id="ENTRY_UNKNOWN", nodes=nodes, edges=[])
    with pytest.raises(GraphValidationError, match="Entry node 'ENTRY_UNKNOWN' does not exist"):
        graph.validate_graph()


def test_5_unreachable_node_rejected():
    """Test 5: Disconnected unreachable node rejected."""
    nodes = {
        "A": NodeModel(node_id="A", name="Start", role="Init", system_prompt="Start"),
        "B": NodeModel(node_id="B", name="Isolated", role="Worker", system_prompt="Prompt"),
    }
    graph = GraphDefinition(graph_id="g5", name="Unreachable", entry_node_id="A", nodes=nodes, edges=[])
    with pytest.raises(GraphValidationError, match="Unreachable nodes detected"):
        graph.validate_graph()


def test_6_cycle_rejected():
    """Test 6: Cyclic graph is strictly rejected (DAG enforcement)."""
    nodes = {
        "A": NodeModel(node_id="A", name="A", role="Role", system_prompt="P"),
        "B": NodeModel(node_id="B", name="B", role="Role", system_prompt="P"),
        "C": NodeModel(node_id="C", name="C", role="Role", system_prompt="P"),
    }
    edges = [
        EdgeModel(source_node_id="A", target_node_id="B"),
        EdgeModel(source_node_id="B", target_node_id="C"),
        EdgeModel(source_node_id="C", target_node_id="A"),  # Cycle!
    ]
    graph = GraphDefinition(graph_id="g6", name="Cycle", entry_node_id="A", nodes=nodes, edges=edges)
    with pytest.raises(GraphValidationError, match="Cycle detected in graph definition"):
        graph.validate_graph()


# ---------------------------------------------------------------------------
# Part 2: Execution State Tests (7 - 10)
# ---------------------------------------------------------------------------

def test_7_initial_state_creation():
    """Test 7: ExecutionState initializes properly."""
    state = ExecutionState(goal="Reconcile accounts", inputs={"key": "val"})
    assert state.status == "initialized"
    assert state.goal == "Reconcile accounts"
    assert state.inputs["key"] == "val"
    assert state.tokens_input == 0
    assert state.cost_usd == 0.0


def test_8_state_propagation():
    """Test 8: Node outputs propagate into state correctly."""
    state = ExecutionState(inputs={"initial": 100})
    state.update_node_output(node_id="node_1", output={"parsed": True}, output_key="step_1")
    assert state.node_outputs["step_1"] == {"parsed": True}
    assert len(state.step_history) == 1


def test_9_json_serialization():
    """Test 9: ExecutionState serializes cleanly to JSON without errors."""
    state = ExecutionState(inputs={"num": 42})
    state.update_node_output("n1", {"matches": [{"id": 1}]}, output_key="out1")
    json_str = state.to_json()
    assert '"num": 42' in json_str
    assert '"matches"' in json_str


def test_10_context_mapping():
    """Test 10: get_context_for_node resolves mapped keys and dot-notation paths."""
    state = ExecutionState(goal="Audit 2026", inputs={"raw": [1, 2, 3]})
    state.update_node_output("n1", {"processed": [1, 2]}, output_key="step1_out")

    # Explicit mapping with dot notation
    mapping = {"data": "step1_out.processed", "task_goal": "goal"}
    resolved = state.get_context_for_node(mapping)
    assert resolved["data"] == [1, 2]
    assert resolved["task_goal"] == "Audit 2026"


# ---------------------------------------------------------------------------
# Part 3: Node Execution Tests (11 - 15)
# ---------------------------------------------------------------------------

def test_11_deterministic_mock_model_execution(gateway: MockModelGateway, executor: ToolExecutor):
    """Test 11: Pure LLM node executes deterministically with mock gateway."""
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
    node = NodeModel(
        node_id="llm_node",
        name="Reasoning Agent",
        role="Auditor",
        system_prompt="Audit input data for anomalies",
    )
    state = ExecutionState(goal="Review statements")
    result = asyncio.run(runner.run_node(node, state))
    assert result.success is True
    assert "Reconciliation step finished" in result.output["message"]
    assert result.tokens_in > 0
    assert result.cost_usd > 0.0


def test_12_tool_invocation_through_executor(gateway: MockModelGateway, executor: ToolExecutor):
    """Test 12: Node dispatches tool execution through ToolExecutor."""
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
    node = NodeModel(
        node_id="parser_node",
        name="Parser",
        role="Ingester",
        system_prompt="Parse records",
        tools=["parse_bank_statement"],
        input_mapping={"records": "raw_statement"},
    )
    state = ExecutionState(inputs={
        "raw_statement": [{"transaction_id": "T1", "date": "2026-03-01", "amount": 500.0, "vendor": "Vendor A"}]
    })
    result = asyncio.run(runner.run_node(node, state))
    assert result.success is True
    assert result.output["count"] == 1
    assert len(result.tool_events) == 1
    assert result.tool_events[0]["tool"] == "parse_bank_statement"


def test_13_multiple_tool_calls_in_history(gateway: MockModelGateway, executor: ToolExecutor):
    """Test 13: Multiple tool calls record properly in state tool_events trace."""
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
    node = NodeModel(
        node_id="calc_node",
        name="Calculator",
        role="Math",
        system_prompt="Calculate",
        tools=["calculate_reconciliation_difference"],
    )
    state = ExecutionState(inputs={"bank_amount": 100.0, "ledger_amount": 100.0})
    result = asyncio.run(runner.run_node(node, state))
    assert result.success is True
    assert len(state.tool_events) == 1
    assert state.tool_events[0]["tool_name"] == "calculate_reconciliation_difference"


def test_14_structured_node_output(gateway: MockModelGateway, executor: ToolExecutor):
    """Test 14: Node produces structured NodeExecutionResult."""
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
    node = NodeModel(node_id="n1", name="N", role="R", system_prompt="P")
    state = ExecutionState()
    result = asyncio.run(runner.run_node(node, state))
    assert result.node_id == "n1"
    assert result.attempts == 1
    assert result.duration_ms >= 0


def test_15_node_failure_handling(gateway: MockModelGateway, executor: ToolExecutor):
    """Test 15: Node reports structured error on bad tool parameters."""
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
    node = NodeModel(
        node_id="bad_node",
        name="Bad Node",
        role="Tester",
        system_prompt="P",
        tools=["parse_bank_statement"],
        input_mapping={"records": "missing_key"},
    )
    state = ExecutionState(inputs={})
    result = asyncio.run(runner.run_node(node, state))
    assert result.success is False
    assert "Invalid arguments" in result.error or "Field required" in result.error


# ---------------------------------------------------------------------------
# Part 4: Scheduler Tests (16 - 20)
# ---------------------------------------------------------------------------

def test_16_single_node_graph(runtime: AgentGraphRuntime):
    """Test 16: Execute single node graph."""
    nodes = {"only": NodeModel(node_id="only", name="Solo", role="R", system_prompt="Do single step")}
    graph = GraphDefinition(graph_id="single", name="Solo Graph", entry_node_id="only", nodes=nodes, edges=[])
    state = asyncio.run(runtime.run(graph, inputs={}))
    assert state.status == "completed"
    assert "only" in state.node_outputs


def test_17_linear_graph(runtime: AgentGraphRuntime):
    """Test 17: Execute 3-node linear sequential graph."""
    nodes = {
        "A": NodeModel(node_id="A", name="A", role="R", system_prompt="Step 1"),
        "B": NodeModel(node_id="B", name="B", role="R", system_prompt="Step 2"),
        "C": NodeModel(node_id="C", name="C", role="R", system_prompt="Step 3"),
    }
    edges = [
        EdgeModel(source_node_id="A", target_node_id="B"),
        EdgeModel(source_node_id="B", target_node_id="C"),
    ]
    graph = GraphDefinition(graph_id="linear", name="Linear", entry_node_id="A", nodes=nodes, edges=edges)
    state = asyncio.run(runtime.run(graph, inputs={}))
    assert state.status == "completed"
    assert len(state.step_history) == 3
    assert [s["node_id"] for s in state.step_history] == ["A", "B", "C"]


def test_18_branching_dag(runtime: AgentGraphRuntime):
    """Test 18: Execute branching Diamond DAG (A -> B, A -> C, B -> D, C -> D)."""
    nodes = {
        "A": NodeModel(node_id="A", name="Root", role="R", system_prompt="Root"),
        "B": NodeModel(node_id="B", name="Branch1", role="R", system_prompt="Branch 1"),
        "C": NodeModel(node_id="C", name="Branch2", role="R", system_prompt="Branch 2"),
        "D": NodeModel(node_id="D", name="Join", role="R", system_prompt="Join"),
    }
    edges = [
        EdgeModel(source_node_id="A", target_node_id="B"),
        EdgeModel(source_node_id="A", target_node_id="C"),
        EdgeModel(source_node_id="B", target_node_id="D"),
        EdgeModel(source_node_id="C", target_node_id="D"),
    ]
    graph = GraphDefinition(graph_id="diamond", name="Diamond DAG", entry_node_id="A", nodes=nodes, edges=edges)
    state = asyncio.run(runtime.run(graph, inputs={}))
    assert state.status == "completed"
    order = [s["node_id"] for s in state.step_history]
    assert order[0] == "A"
    assert order[-1] == "D"
    assert set(order[1:3]) == {"B", "C"}


def test_19_terminal_node_collection(runtime: AgentGraphRuntime):
    """Test 19: Verify terminal node is executed and marked."""
    nodes = {
        "A": NodeModel(node_id="A", name="A", role="R", system_prompt="Start"),
        "T": NodeModel(node_id="T", name="Terminal", role="R", system_prompt="Finish"),
    }
    edges = [EdgeModel(source_node_id="A", target_node_id="T")]
    graph = GraphDefinition(
        graph_id="term", name="Terminal Test", entry_node_id="A", terminal_node_ids=["T"], nodes=nodes, edges=edges
    )
    state = asyncio.run(runtime.run(graph, inputs={}))
    assert state.status == "completed"
    assert "T" in state.node_outputs


def test_20_deterministic_execution_ordering(runtime: AgentGraphRuntime):
    """Test 20: Deterministic ordering across multiple executions."""
    graph = GraphDefinition(
        graph_id="det",
        name="Deterministic Order",
        entry_node_id="A",
        nodes={
            "A": NodeModel(node_id="A", name="A", role="R", system_prompt="A"),
            "Z": NodeModel(node_id="Z", name="Z", role="R", system_prompt="Z"),
            "M": NodeModel(node_id="M", name="M", role="R", system_prompt="M"),
        },
        edges=[
            EdgeModel(source_node_id="A", target_node_id="Z"),
            EdgeModel(source_node_id="A", target_node_id="M"),
        ],
    )
    order1 = [n.node_id for n in graph.get_topological_order()]
    order2 = [n.node_id for n in graph.get_topological_order()]
    assert order1 == order2


# ---------------------------------------------------------------------------
# Part 5: Accounting Tests (21 - 23)
# ---------------------------------------------------------------------------

def test_21_token_aggregation(runtime: AgentGraphRuntime):
    """Test 21: Tokens are aggregated across all executed nodes."""
    nodes = {
        "A": NodeModel(node_id="A", name="A", role="R", system_prompt="Task A"),
        "B": NodeModel(node_id="B", name="B", role="R", system_prompt="Task B"),
    }
    edges = [EdgeModel(source_node_id="A", target_node_id="B")]
    graph = GraphDefinition(graph_id="tokens", name="Tokens", entry_node_id="A", nodes=nodes, edges=edges)
    state = asyncio.run(runtime.run(graph, inputs={}))
    assert state.tokens_input > 0
    assert state.tokens_output > 0


def test_22_cost_aggregation(runtime: AgentGraphRuntime):
    """Test 22: Cost in USD is calculated and aggregated across nodes."""
    nodes = {
        "A": NodeModel(node_id="A", name="A", role="R", system_prompt="Task A"),
        "B": NodeModel(node_id="B", name="B", role="R", system_prompt="Task B"),
    }
    edges = [EdgeModel(source_node_id="A", target_node_id="B")]
    graph = GraphDefinition(graph_id="cost", name="Cost", entry_node_id="A", nodes=nodes, edges=edges)
    state = asyncio.run(runtime.run(graph, inputs={}))
    assert state.cost_usd > 0.0


def test_23_latency_aggregation(runtime: AgentGraphRuntime):
    """Test 23: Latency in milliseconds is recorded on state."""
    nodes = {"A": NodeModel(node_id="A", name="A", role="R", system_prompt="Quick")}
    graph = GraphDefinition(graph_id="latency", name="Latency", entry_node_id="A", nodes=nodes, edges=[])
    state = asyncio.run(runtime.run(graph, inputs={}))
    assert state.latency_ms >= 0


# ---------------------------------------------------------------------------
# Part 6: Error & Retry Tests (24 - 26)
# ---------------------------------------------------------------------------

def test_24_bounded_retry(gateway: MockModelGateway, executor: ToolExecutor):
    """Test 24: Node retries up to max_retries on transient failure."""
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
    # Node configured with max_retries=2
    node = NodeModel(
        node_id="retry_node",
        name="Retryable",
        role="Worker",
        system_prompt="P",
        tools=["parse_bank_statement"],
        input_mapping={"records": "missing_key"},
        max_retries=2,
    )
    state = ExecutionState()
    result = asyncio.run(runner.run_node(node, state))
    assert result.success is False
    assert result.attempts == 3  # Initial try + 2 retries


def test_25_non_retryable_failure(gateway: MockModelGateway, executor: ToolExecutor):
    """Test 25: Non-retryable error fails immediately without retrying."""
    runner = NodeRunner(model_gateway=gateway, tool_executor=executor)
    node = NodeModel(
        node_id="strict_node",
        name="Strict",
        role="Worker",
        system_prompt="P",
        tools=["parse_bank_statement"],
        input_mapping={"records": "missing_key"},
        max_retries=3,
        retryable_errors=["NETWORK_TIMEOUT"],  # Does not match argument error
    )
    state = ExecutionState()
    result = asyncio.run(runner.run_node(node, state))
    assert result.success is False
    assert result.attempts == 1  # Did not retry


def test_26_downstream_blocking(runtime: AgentGraphRuntime):
    """Test 26: Downstream nodes are blocked when an upstream node fails."""
    nodes = {
        "A": NodeModel(
            node_id="A",
            name="Failing Upstream",
            role="R",
            system_prompt="P",
            tools=["parse_bank_statement"],
            input_mapping={"records": "missing_key"},
        ),
        "B": NodeModel(node_id="B", name="Downstream", role="R", system_prompt="Should never run"),
    }
    edges = [EdgeModel(source_node_id="A", target_node_id="B")]
    graph = GraphDefinition(graph_id="block", name="Blocking Test", entry_node_id="A", nodes=nodes, edges=edges)
    state = asyncio.run(runtime.run(graph, inputs={}))
    assert state.status == "failed"
    assert "B" not in state.node_outputs
    assert len(state.errors) > 0


# ---------------------------------------------------------------------------
# Part 7: Full Reconciliation Graph Demo Integration (27)
# ---------------------------------------------------------------------------

def test_27_reconciliation_graph_demo_execution():
    """Test 27: Full reconciliation demo graph executes end-to-end with real tools."""
    raw_statement = [
        {"transaction_id": "B-100", "date": "2026-03-01", "amount": 1250.00, "vendor": "Stripe Net Deposit"},
        {"transaction_id": "B-200", "date": "2026-03-05", "amount": -450.00, "vendor": "Amazon Web Services"},
    ]
    ledger_entries = [
        {"entry_id": "L-100", "date": "2026-03-01", "amount": 1250.00, "vendor": "Stripe Net Deposit"},
        {"entry_id": "L-200", "date": "2026-03-04", "amount": -450.00, "vendor": "Amazon Web Serv"},
    ]

    state = asyncio.run(run_reconciliation_demo(
        raw_statement=raw_statement,
        ledger_entries=ledger_entries,
        goal="Reconcile March financial statement",
    ))

    assert state.status == "completed"
    assert "parsed_statement" in state.node_outputs
    assert "reconciliation_summary" in state.node_outputs

    summary = state.node_outputs["reconciliation_summary"]
    assert "matched_pairs" in summary
    assert len(summary["matched_pairs"]) == 2

    # Check match classifications
    types = [m["match_type"] for m in summary["matched_pairs"]]
    assert "exact_match" in types
    assert "timing_difference" in types or "near_match" in types
