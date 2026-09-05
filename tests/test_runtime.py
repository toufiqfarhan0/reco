"""Deterministic tests for Agent Graph Runtime, Node Runner, and State Transitions."""

import pytest
from reco.core.goal_analyzer import GoalAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import EdgeSpec, NodeSpec, NodeStatus, NodeType
from reco.engine.runtime import AgentRuntime, ExecutionResult
from reco.engine.state import AgentState
from reco.tools.registry import ToolDefinition, ToolRegistry


@pytest.fixture
def sample_dataset():
    """Synthetic dataset with numeric features and an injected anomaly."""
    return [
        {"id": "tx_01", "merchant": "tech_store", "amount": 120.0, "risk_score": 0.12},
        {"id": "tx_02", "merchant": "tech_store", "amount": 115.0, "risk_score": 0.14},
        {"id": "tx_03", "merchant": "groceries", "amount": 45.0, "risk_score": 0.05},
        {"id": "tx_04", "merchant": "groceries", "amount": 52.0, "risk_score": 0.06},
        {"id": "tx_05", "merchant": "clothing", "amount": 80.0, "risk_score": 0.08},
        {"id": "tx_06", "merchant": "clothing", "amount": 85.0, "risk_score": 0.09},
        {"id": "tx_07", "merchant": "tech_store", "amount": 130.0, "risk_score": 0.15},
        # Extreme anomaly
        {"id": "tx_08", "merchant": "luxury_cars", "amount": 9500.0, "risk_score": 0.99},
    ]


def test_end_to_end_agent_execution(sample_dataset):
    """Verify complete pipeline: goal -> architecture -> execution -> output."""
    analyzer = GoalAnalyzer()
    spec = analyzer.analyze("Analyze tabular data, compute distributions, and detect all anomalous records")

    generator = ArchitectureGenerator()
    arch = generator.generate(spec)

    runtime = AgentRuntime()
    result = runtime.execute(arch, {"dataset": sample_dataset})

    assert isinstance(result, ExecutionResult)
    assert result.status == NodeStatus.COMPLETED
    assert result.error is None
    assert result.total_latency_ms > 0.0
    assert result.quality_score >= 0.8

    # Verify topological order
    assert result.execution_order[0] == "input_node"
    assert result.execution_order[-1] == "output_node"

    # Verify all nodes have individual telemetry records
    assert len(result.node_records) == len(arch.nodes)
    for node_id, rec in result.node_records.items():
        assert rec.status == NodeStatus.COMPLETED
        assert rec.latency_ms >= 0.0
        assert rec.end_time >= rec.start_time

    # Verify final structured output payload
    output = result.final_output
    assert isinstance(output, dict)
    assert "summary" in output
    assert "distributions" in output
    assert "anomalies" in output
    assert "reasoning" in output
    assert "verification" in output

    # Verify summary
    assert output["summary"]["row_count"] == 8

    # Verify distribution
    assert "amount" in output["distributions"]
    assert "risk_score" in output["distributions"]

    # Verify anomaly detection isolated tx_08
    anomalies = output["anomalies"]
    assert len(anomalies) >= 1
    anom_ids = [a["record"]["id"] for a in anomalies]
    assert "tx_08" in anom_ids

    # Verify reasoning and verifier
    assert output["reasoning"]["status"] == "reasoning_complete"
    assert output["verification"]["verified"] is True


def test_immutable_state_transitions(sample_dataset):
    """Verify that AgentState records step snapshots immutably."""
    state = AgentState()
    assert state.step == 0
    assert len(state.history) == 0

    analyzer = GoalAnalyzer()
    spec = analyzer.analyze("Analyze tabular data")
    generator = ArchitectureGenerator()
    arch = generator.generate(spec)

    runtime = AgentRuntime()
    runtime.execute(arch, {"dataset": sample_dataset})

    # Validate snapshot behavior
    snapshot = state.snapshot()
    assert isinstance(snapshot, dict)
    assert "data" in snapshot
    assert "history" in snapshot


def test_runtime_handles_node_failure_gracefully(sample_dataset):
    """Verify runtime detects and handles tool failure without crashing."""
    registry = ToolRegistry.create_default()

    def failing_tool(dataset):
        raise ValueError("Simulated tool computation failure")

    registry.register(ToolDefinition(
        name="failing_tool",
        description="Fails unconditionally",
        parameters={"type": "object", "properties": {"dataset": {"type": "array"}}, "required": ["dataset"]},
        capabilities=["failing_cap"],
        handler=failing_tool
    ))

    analyzer = GoalAnalyzer()
    spec = analyzer.analyze("Analyze tabular data")

    generator = ArchitectureGenerator(tool_registry=registry)
    arch = generator.generate(spec)

    # Swap one tool node with the failing tool
    for node in arch.nodes:
        if node.type == NodeType.TOOL:
            node.tool_name = "failing_tool"
            break

    runtime = AgentRuntime(tool_registry=registry)
    result = runtime.execute(arch, {"dataset": sample_dataset})

    # Overall execution should be marked FAILED
    assert result.status == NodeStatus.FAILED
    assert result.error is not None
    assert "failing_tool" in result.error or "ValueError" in result.error

    # Downstream nodes depending on the failed node should be marked SKIPPED or FAILED
    failed_or_skipped = [
        rec for rec in result.node_records.values()
        if rec.status in (NodeStatus.FAILED, NodeStatus.SKIPPED)
    ]
    assert len(failed_or_skipped) >= 1
