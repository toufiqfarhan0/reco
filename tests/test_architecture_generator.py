"""Deterministic tests for DAG Architecture Generator and Graph Models."""

import pytest
from reco.core.goal_analyzer import GoalAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import (
    AgentArchitecture,
    EdgeSpec,
    NodeSpec,
    NodeType,
)
from reco.tools.registry import ToolRegistry


@pytest.fixture
def sample_task_spec():
    analyzer = GoalAnalyzer()
    return analyzer.analyze(
        "Analyze tabular data, compute distributions, and detect all anomalous records"
    )


def test_architecture_generation_structure(sample_task_spec):
    """Verify that synthesized architecture has all required node types in DAG."""
    generator = ArchitectureGenerator()
    arch = generator.generate(sample_task_spec)

    assert isinstance(arch, AgentArchitecture)
    assert len(arch.nodes) >= 5
    assert len(arch.edges) >= 4

    # Verify presence of all 5 architectural node types
    node_types = {n.type for n in arch.nodes}
    assert NodeType.INPUT in node_types
    assert NodeType.TOOL in node_types
    assert NodeType.REASONING in node_types
    assert NodeType.VERIFIER in node_types
    assert NodeType.OUTPUT in node_types

    # Verify specific tool nodes were included
    tool_names = {n.tool_name for n in arch.nodes if n.type == NodeType.TOOL}
    assert "compute_distributions" in tool_names or "detect_anomalies" in tool_names or "tabular_summary" in tool_names


def test_topological_sort_and_acyclicity(sample_task_spec):
    """Verify topological execution sequence and acyclic property."""
    generator = ArchitectureGenerator()
    arch = generator.generate(sample_task_spec)

    assert arch.is_acyclic() is True
    order = arch.topological_sort()
    assert len(order) == len(arch.nodes)

    # Input node must always be first
    assert order[0] == "input_node"
    # Output node must always be last
    assert order[-1] == "output_node"

    # Verifier must execute before output
    assert order.index("verifier_node") < order.index("output_node")
    # Reasoning must execute before verifier
    assert order.index("reasoning_node") < order.index("verifier_node")


def test_cycle_detection(sample_task_spec):
    """Verify that cyclic graph dependencies are detected and raise ValueError."""
    generator = ArchitectureGenerator()
    arch = generator.generate(sample_task_spec)

    # Artificially inject a cycle: output_node -> input_node
    arch.edges.append(EdgeSpec(source="output_node", target="input_node"))

    assert arch.is_acyclic() is False
    with pytest.raises(ValueError, match="Cyclic dependency detected"):
        arch.topological_sort()

    with pytest.raises(ValueError, match="Cyclic dependency detected"):
        arch.validate_graph()


def test_nonexistent_node_edge_validation(sample_task_spec):
    """Verify that edges pointing to nonexistent nodes are caught."""
    generator = ArchitectureGenerator()
    arch = generator.generate(sample_task_spec)

    # Inject edge with bogus destination
    arch.edges.append(EdgeSpec(source="input_node", target="ghost_node_999"))

    with pytest.raises(ValueError, match="does not exist in graph"):
        arch.validate_graph()


def test_architectural_complexity_metrics(sample_task_spec):
    """Verify complexity and quality metric calculations."""
    generator = ArchitectureGenerator()
    arch = generator.generate(sample_task_spec)

    metrics = arch.complexity_metrics()

    assert "node_count" in metrics
    assert "edge_count" in metrics
    assert "edge_density" in metrics
    assert "quality_score" in metrics

    assert metrics["node_count"] == len(arch.nodes)
    assert metrics["edge_count"] == len(arch.edges)
    assert metrics["edge_density"] > 0.0
    assert metrics["has_verifier"] is True
    assert metrics["has_reasoning"] is True
    assert metrics["quality_score"] >= 0.8
