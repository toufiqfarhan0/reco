"""Comprehensive unit tests for the Architecture Generator V0 (Milestone 6)."""

import json
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from reco.api.app import app
from reco.core.goal_analyzer import GoalAnalyzer
from reco.core.task_spec import (
    Capability,
    EvaluatorSpecification,
    Subtask,
    TaskSpecification,
    ToolRecommendation,
)
from reco.engine.generator import (
    ArchitectureGenerator,
    ArchitectureQualityScore,
    ArchitectureValidationResult,
    MAX_EDGE_COUNT,
    MAX_GRAPH_DEPTH,
    MAX_NODE_COUNT,
    MAX_TOOLS_PER_NODE,
)
from reco.engine.models import EdgeModel, GraphDefinition, GraphValidationError, NodeModel
from reco.engine.runtime import AgentGraphRuntime
from reco.llm.mock import MockModelGateway
from reco.tools.executor import ToolExecutor
from reco.tools.reconciliation import register_reconciliation_tools
from reco.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def recon_registry() -> ToolRegistry:
    """Registry loaded with the standard reconciliation toolpack."""
    reg = ToolRegistry()
    register_reconciliation_tools(reg)
    return reg


@pytest.fixture
def recon_catalog(recon_registry: ToolRegistry):
    """Standardized reconciliation tool catalog schema list."""
    return recon_registry.list_schemas()


@pytest.fixture
def api_client():
    """TestClient for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_task_spec():
    """Valid financial reconciliation TaskSpecification fixture."""
    return TaskSpecification(
        task_id="task_recon_001",
        original_goal="Reconcile bank transactions against general ledger and identify discrepancies",
        normalized_goal="Reconcile bank transactions against general ledger and identify discrepancies",
        domain="finance",
        objective="Reconcile bank transactions against general ledger",
        subtasks=[
            Subtask(
                id="subtask_1",
                description="Parse raw bank statements",
                objective="Normalize bank records",
                required_capabilities=[Capability.EXTRACTION, Capability.TRANSFORMATION],
                preferred_tools=["parse_bank_statement"],
                expected_input={"raw_statement": "list"},
                expected_output={"parsed_statement": "list"},
                dependencies=[],
            ),
            Subtask(
                id="subtask_2",
                description="Match transactions and calculate variances",
                objective="Detect matches and discrepancies",
                required_capabilities=[Capability.COMPARISON, Capability.CALCULATION],
                preferred_tools=["fuzzy_match_transactions", "calculate_reconciliation_difference"],
                expected_input={"parsed_statement": "list", "ledger_entries": "list"},
                expected_output={"reconciliation_summary": "dict"},
                dependencies=["subtask_1"],
            ),
            Subtask(
                id="subtask_3",
                description="Audit discrepancies and format report",
                objective="Verify consistency and constraints",
                required_capabilities=[Capability.VERIFICATION, Capability.REASONING],
                preferred_tools=[],
                expected_input={"reconciliation_summary": "dict"},
                expected_output={"verified_report": "dict"},
                verification_needed=True,
                dependencies=["subtask_2"],
            ),
        ],
        required_capabilities=[
            Capability.EXTRACTION,
            Capability.COMPARISON,
            Capability.CALCULATION,
            Capability.VERIFICATION,
            Capability.REASONING,
        ],
        available_tool_ids=[
            "parse_bank_statement",
            "query_general_ledger",
            "calculate_reconciliation_difference",
            "fuzzy_match_transactions",
        ],
        suggested_tool_bindings=[
            ToolRecommendation(tool_name="parse_bank_statement", relevance_score=0.95, reason="Parser"),
            ToolRecommendation(tool_name="fuzzy_match_transactions", relevance_score=0.90, reason="Matcher"),
            ToolRecommendation(tool_name="calculate_reconciliation_difference", relevance_score=0.85, reason="Calculator"),
        ],
        inputs={"raw_statement": {"type": "array"}, "ledger_entries": {"type": "array"}},

        expected_outputs={"reconciliation_summary": {"type": "object"}},
        constraints=["Preserve currency precision"],
        verification_requirements=["Arithmetic verification of variance"],
        risk_level="low",
        side_effect_requirements=False,
    )


# ---------------------------------------------------------------------------
# 1. ARCHITECTURE MODEL TESTS
# ---------------------------------------------------------------------------

def test_1_valid_architecture_parses():
    """1. Test that a well-formed GraphDefinition parses successfully."""
    nodes = {
        "n1": NodeModel(node_id="n1", name="Parser", role="Extractor", system_prompt="Parse input"),
        "n2": NodeModel(node_id="n2", name="Auditor", role="Auditor", system_prompt="Verify data"),
    }
    edges = [EdgeModel(source_node_id="n1", target_node_id="n2")]
    graph = GraphDefinition(
        graph_id="g1",
        name="Valid Graph",
        entry_node_id="n1",
        terminal_node_ids=["n2"],
        nodes=nodes,
        edges=edges,
    )
    assert graph.graph_id == "g1"
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    graph.validate_graph()


def test_2_malformed_architecture_rejected():
    """2. Test that missing required fields in GraphDefinition raises ValidationError."""
    with pytest.raises(ValidationError):
        GraphDefinition(name="Missing nodes and entry")


def test_3_node_ids_unique():
    """3. Test that duplicate node definitions in mapping are not allowed by model dict structure."""
    nodes = {
        "n1": NodeModel(node_id="n1", name="First", role="Worker", system_prompt="Prompt 1"),
    }
    # Nodes is a dict keyed by node_id, ensuring unique IDs per graph
    assert len(nodes) == 1
    assert "n1" in nodes


def test_4_edge_references_valid():
    """4. Test that edges referencing non-existent nodes are rejected."""
    nodes = {
        "n1": NodeModel(node_id="n1", name="Entry", role="Worker", system_prompt="Do work"),
    }
    edges = [EdgeModel(source_node_id="n1", target_node_id="n_nonexistent")]
    graph = GraphDefinition(
        graph_id="g_invalid_edge",
        name="Invalid Edge Graph",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
        edges=edges,
    )
    with pytest.raises(GraphValidationError, match="Edge target 'n_nonexistent' does not exist"):
        graph.validate_graph()


def test_5_entry_exists():
    """5. Test that missing entry node is rejected."""
    nodes = {
        "n1": NodeModel(node_id="n1", name="Node 1", role="Worker", system_prompt="Work"),
    }
    graph = GraphDefinition(
        graph_id="g_no_entry",
        name="Missing Entry Graph",
        entry_node_id="missing_entry",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    with pytest.raises(GraphValidationError, match="Entry node 'missing_entry' does not exist"):
        graph.validate_graph()


def test_6_terminal_exists():
    """6. Test that missing terminal node is rejected."""
    nodes = {
        "n1": NodeModel(node_id="n1", name="Node 1", role="Worker", system_prompt="Work"),
    }
    graph = GraphDefinition(
        graph_id="g_bad_term",
        name="Bad Terminal Graph",
        entry_node_id="n1",
        terminal_node_ids=["missing_terminal"],
        nodes=nodes,
    )
    with pytest.raises(GraphValidationError, match="Terminal node 'missing_terminal' does not exist"):
        graph.validate_graph()


# ---------------------------------------------------------------------------
# 2. GRAPH VALIDATION TESTS
# ---------------------------------------------------------------------------

def test_7_cycle_rejected():
    """7. Test that cyclic graphs are strictly rejected by Kahn's algorithm."""
    nodes = {
        "n1": NodeModel(node_id="n1", name="Node 1", role="Worker", system_prompt="Work"),
        "n2": NodeModel(node_id="n2", name="Node 2", role="Worker", system_prompt="Work"),
    }
    edges = [
        EdgeModel(source_node_id="n1", target_node_id="n2"),
        EdgeModel(source_node_id="n2", target_node_id="n1"),
    ]
    graph = GraphDefinition(
        graph_id="g_cycle",
        name="Cyclic Graph",
        entry_node_id="n1",
        terminal_node_ids=["n2"],
        nodes=nodes,
        edges=edges,
    )
    with pytest.raises(GraphValidationError, match="Cycle detected"):
        graph.validate_graph()


def test_8_unreachable_node_rejected():
    """8. Test that unreachable nodes from entry node are rejected."""
    nodes = {
        "n1": NodeModel(node_id="n1", name="Entry", role="Worker", system_prompt="Work"),
        "n2": NodeModel(node_id="n2", name="Island", role="Worker", system_prompt="Work"),
    }
    graph = GraphDefinition(
        graph_id="g_unreachable",
        name="Unreachable Graph",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
        edges=[],
    )
    with pytest.raises(GraphValidationError, match="Unreachable nodes detected"):
        graph.validate_graph()


def test_9_invalid_terminal_rejected():
    """9. Test that an unreachable terminal node is rejected."""
    nodes = {
        "n1": NodeModel(node_id="n1", name="Entry", role="Worker", system_prompt="Work"),
        "n2": NodeModel(node_id="n2", name="Unreachable Terminal", role="Worker", system_prompt="Work"),
    }
    graph = GraphDefinition(
        graph_id="g_unreach_term",
        name="Unreachable Terminal Graph",
        entry_node_id="n1",
        terminal_node_ids=["n2"],
        nodes=nodes,
        edges=[],
    )
    with pytest.raises(GraphValidationError):
        graph.validate_graph()


def test_10_invalid_tool_rejected(sample_task_spec, recon_catalog):
    """10. Test that assigning a tool not in catalog is flagged by validator."""
    generator = ArchitectureGenerator()
    nodes = {
        "n1": NodeModel(
            node_id="n1",
            name="Worker",
            role="Worker",
            system_prompt="Work",
            tools=["non_existent_tool_123"],
        )
    }
    graph = GraphDefinition(
        graph_id="g_bad_tool",
        name="Bad Tool Graph",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    res = generator.validate_architecture(graph, sample_task_spec, recon_catalog)
    assert res.valid is False
    assert res.tool_authorization_ok is False
    assert any("Unauthorized/fabricated tool" in e for e in res.errors)


def test_11_unauthorized_tool_rejected(sample_task_spec, recon_catalog):
    """11. Test that fabricated tools outside the supplied catalog fail validation."""
    generator = ArchitectureGenerator()
    nodes = {
        "n1": NodeModel(
            node_id="n1",
            name="Worker",
            role="Worker",
            system_prompt="Work",
            tools=["parse_bank_statement", "fabricated_magic_solver"],
        )
    }
    graph = GraphDefinition(
        graph_id="g_unauth",
        name="Unauthorized Tool Graph",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    res = generator.validate_architecture(graph, sample_task_spec, recon_catalog)
    assert res.valid is False
    assert any("fabricated_magic_solver" in e for e in res.errors)


# ---------------------------------------------------------------------------
# 3. CAPABILITY COVERAGE TESTS
# ---------------------------------------------------------------------------

def test_12_full_capability_coverage_detected(sample_task_spec, recon_catalog):
    """12. Test that a graph covering all required capabilities reports full coverage."""
    generator = ArchitectureGenerator()
    nodes = {
        "n1": NodeModel(
            node_id="n1",
            name="Extractor",
            role="Extractor",
            system_prompt="Parse statements",
            tools=["parse_bank_statement"],
            metadata={"capabilities": ["extraction", "transformation"]},
        ),
        "n2": NodeModel(
            node_id="n2",
            name="Matcher",
            role="Matcher",
            system_prompt="Match & calculate",
            tools=["fuzzy_match_transactions", "calculate_reconciliation_difference"],
            metadata={"capabilities": ["comparison", "calculation"]},
        ),

        "n3": NodeModel(
            node_id="n3",
            name="Auditor",
            role="Auditor",
            system_prompt="Audit and verify results",
            metadata={"capabilities": ["verification", "reasoning"]},
        ),
    }
    edges = [
        EdgeModel(source_node_id="n1", target_node_id="n2"),
        EdgeModel(source_node_id="n2", target_node_id="n3"),
    ]
    graph = GraphDefinition(
        graph_id="g_full_cov",
        name="Full Coverage Graph",
        entry_node_id="n1",
        terminal_node_ids=["n3"],
        nodes=nodes,
        edges=edges,
    )
    res = generator.validate_architecture(graph, sample_task_spec, recon_catalog)
    assert res.valid is True
    assert all(res.capability_coverage.values())


def test_13_missing_capability_detected(sample_task_spec, recon_catalog):
    """13. Test that missing required capabilities are flagged in warnings."""
    generator = ArchitectureGenerator()
    # Graph with only extractor (missing comparison, calculation, verification)
    nodes = {
        "n1": NodeModel(
            node_id="n1",
            name="Extractor Only",
            role="Extractor",
            system_prompt="Extract",
            tools=["parse_bank_statement"],
            metadata={"capabilities": ["extraction"]},
        )
    }
    graph = GraphDefinition(
        graph_id="g_missing_cap",
        name="Missing Cap Graph",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    res = generator.validate_architecture(graph, sample_task_spec, recon_catalog)
    assert res.capability_coverage["calculation"] is False
    assert any("Required capability 'calculation'" in w for w in res.warnings)


def test_14_multi_capability_node_handled_correctly(sample_task_spec, recon_catalog):
    """14. Test that a single node can satisfy multiple compatible capabilities."""
    generator = ArchitectureGenerator()
    nodes = {
        "n_combo": NodeModel(
            node_id="n_combo",
            name="Combined Processor",
            role="AuditorProcessor",
            system_prompt="Process and verify",
            tools=["parse_bank_statement", "fuzzy_match_transactions", "calculate_reconciliation_difference"],
            metadata={"capabilities": ["extraction", "comparison", "calculation", "verification", "reasoning"]},
        )

    }
    graph = GraphDefinition(
        graph_id="g_combo",
        name="Combo Graph",
        entry_node_id="n_combo",
        terminal_node_ids=["n_combo"],
        nodes=nodes,
    )
    res = generator.validate_architecture(graph, sample_task_spec, recon_catalog)
    assert res.valid is True
    assert all(res.capability_coverage.values())


# ---------------------------------------------------------------------------
# 4. TOOL ASSIGNMENT & RISK TESTS
# ---------------------------------------------------------------------------

def test_15_valid_tool_assignment(sample_task_spec, recon_catalog):
    """15. Test that tools assigned from catalog pass validation."""
    generator = ArchitectureGenerator()
    nodes = {
        "n1": NodeModel(
            node_id="n1",
            name="Parser",
            role="Extractor",
            system_prompt="Parse",
            tools=["parse_bank_statement"],
        )
    }
    graph = GraphDefinition(
        graph_id="g_valid_tools",
        name="Valid Tools",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    res = generator.validate_architecture(graph, sample_task_spec, recon_catalog)
    assert res.tool_authorization_ok is True


def test_16_fabricated_tool_rejected(sample_task_spec, recon_catalog):
    """16. Test that fabricated tools cause validation failure."""
    generator = ArchitectureGenerator()
    nodes = {
        "n1": NodeModel(
            node_id="n1",
            name="Parser",
            role="Extractor",
            system_prompt="Parse",
            tools=["non_existent_fake_tool"],
        )
    }
    graph = GraphDefinition(
        graph_id="g_fake_tool",
        name="Fake Tool",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    res = generator.validate_architecture(graph, sample_task_spec, recon_catalog)
    assert res.valid is False
    assert res.tool_authorization_ok is False


def test_17_tool_metadata_considered(sample_task_spec):
    """17. Test that tool metadata (risk level, side effects) is checked during validation."""
    custom_catalog = [
        {
            "name": "safe_reader",
            "description": "Read records safely",
            "side_effect": False,
            "risk_level": "low",
        },
        {
            "name": "dangerous_deleter",
            "description": "Deletes records permanently",
            "side_effect": True,
            "risk_level": "high",
        },
    ]
    generator = ArchitectureGenerator()
    nodes = {
        "n1": NodeModel(
            node_id="n1",
            name="Worker",
            role="Worker",
            system_prompt="Work",
            tools=["dangerous_deleter"],
        )
    }
    graph = GraphDefinition(
        graph_id="g_meta",
        name="Meta Check",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    # Read-only task spec
    res = generator.validate_architecture(graph, sample_task_spec, custom_catalog)
    assert "dangerous_deleter" in res.risk_checks["side_effect_tools"]
    assert "dangerous_deleter" in res.risk_checks["high_risk_tools"]
    assert res.risk_checks["read_only_aligned"] is False
    assert any("Read-only task assigned side-effect tools" in e for e in res.errors)


def test_18_side_effect_restrictions_enforced(sample_task_spec):
    """18. Test side-effect tools are rejected for read-only tasks."""
    custom_catalog = [
        {"name": "write_tool", "description": "Mutates database", "side_effect": True, "risk_level": "medium"}
    ]
    generator = ArchitectureGenerator()
    nodes = {
        "n1": NodeModel(node_id="n1", name="Writer", role="Writer", system_prompt="Write", tools=["write_tool"])
    }
    graph = GraphDefinition(
        graph_id="g_side_eff",
        name="Side Effect Graph",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    res = generator.validate_architecture(graph, sample_task_spec, custom_catalog)
    assert res.valid is False
    assert any("Read-only task assigned side-effect tools" in e for e in res.errors)


# ---------------------------------------------------------------------------
# 5. VERIFICATION NODE TESTS
# ---------------------------------------------------------------------------

def test_19_evaluator_verification_requirements_influence_architecture(recon_catalog):
    """19. Test evaluator correctness criteria trigger verification node presence."""
    task_spec = TaskSpecification(
        original_goal="Reconcile accounts",
        normalized_goal="Reconcile accounts",
        objective="Reconcile accounts",
        evaluator_requirements=EvaluatorSpecification(
            correctness_criteria=["Zero unexplained variance"],
            required_output_properties=["reconciliation_summary"],
        ),
    )
    generator = ArchitectureGenerator()
    # Graph without verifier
    nodes = {
        "n1": NodeModel(node_id="n1", name="Worker", role="Processor", system_prompt="Work")
    }
    graph = GraphDefinition(
        graph_id="g_no_verif",
        name="No Verif",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    res = generator.validate_architecture(graph, task_spec, recon_catalog)
    assert any("dedicated verifier node was found" in w for w in res.warnings)


def test_20_unnecessary_verifier_not_mandatory(recon_catalog):
    """20. Test that tasks without verification requirements do not warn if verifier is omitted."""
    task_spec = TaskSpecification(
        original_goal="Convert currency text to decimal",
        normalized_goal="Convert currency text to decimal",
        objective="Convert currency text",
        required_capabilities=[Capability.TRANSFORMATION],
        verification_requirements=[],
    )
    generator = ArchitectureGenerator()
    nodes = {
        "n1": NodeModel(
            node_id="n1",
            name="Converter",
            role="Transformer",
            system_prompt="Convert",
            metadata={"capabilities": ["transformation"]},
        )
    }
    graph = GraphDefinition(
        graph_id="g_simple_transform",
        name="Simple Transform",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    res = generator.validate_architecture(graph, task_spec, recon_catalog)
    assert not any("dedicated verifier node" in w for w in res.warnings)


# ---------------------------------------------------------------------------
# 6. RISK TESTS
# ---------------------------------------------------------------------------

def test_21_read_only_task_stays_read_only(sample_task_spec, recon_catalog):
    """21. Test that read-only task generated architecture does not authorize side-effect tools."""
    generator = ArchitectureGenerator()
    import asyncio
    graph = asyncio.run(generator.generate(sample_task_spec, available_tools=recon_catalog))
    val = generator.validate_architecture(graph, sample_task_spec, recon_catalog)
    assert val.risk_checks["read_only_aligned"] is True
    assert len(val.risk_checks["side_effect_tools"]) == 0


def test_22_state_changing_requirement_can_authorize_side_effect_tool():
    """22. Test that when goal explicitly requires state changes, side-effect tools are authorized."""
    task_spec = TaskSpecification(
        original_goal="Update ledger balances with adjustment entries",
        normalized_goal="Update ledger balances with adjustment entries",
        objective="Update ledger balances",
        side_effect_requirements=True,
        risk_level="medium",
    )
    catalog = [
        {"name": "post_journal_entry", "description": "Posts entry to GL", "side_effect": True, "risk_level": "medium"}
    ]
    generator = ArchitectureGenerator()
    nodes = {
        "n1": NodeModel(
            node_id="n1",
            name="Poster",
            role="Modifier",
            system_prompt="Post entry",
            tools=["post_journal_entry"],
        )
    }
    graph = GraphDefinition(
        graph_id="g_mut",
        name="Mutation Graph",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    val = generator.validate_architecture(graph, task_spec, catalog)
    assert val.valid is True
    assert val.risk_checks["read_only_aligned"] is True
    assert "post_journal_entry" in val.risk_checks["side_effect_tools"]


def test_23_high_risk_tool_handled_conservatively():
    """23. Test high-risk tool on low-risk task produces explicit warning."""
    task_spec = TaskSpecification(
        original_goal="Inspect records",
        normalized_goal="Inspect records",
        objective="Inspect records",
        risk_level="low",
    )
    catalog = [
        {"name": "delete_all", "description": "Deletes everything", "side_effect": True, "risk_level": "high"}
    ]
    generator = ArchitectureGenerator()
    nodes = {
        "n1": NodeModel(node_id="n1", name="Deleter", role="Deleter", system_prompt="Delete", tools=["delete_all"])
    }
    graph = GraphDefinition(
        graph_id="g_high_risk",
        name="High Risk Graph",
        entry_node_id="n1",
        terminal_node_ids=["n1"],
        nodes=nodes,
    )
    val = generator.validate_architecture(graph, task_spec, catalog)
    assert any("Low-risk task contains high-risk tools" in w for w in val.warnings)


# ---------------------------------------------------------------------------
# 7. LLM ANALYSIS & REPAIR TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_24_deterministic_mock_model_gateway_generation(sample_task_spec, recon_catalog):
    """24. Test architecture generation using MockModelGateway."""
    canned_graph = {
        "graph_id": "mock_generated_v0",
        "name": "Synthesized Mock Reconciliation Graph",
        "entry_node_id": "node_parser",
        "terminal_node_ids": ["node_auditor"],
        "nodes": {
            "node_parser": {
                "node_id": "node_parser",
                "name": "Statement Parser",
                "role": "IngestionSpecialist",
                "system_prompt": "Parse bank statement",
                "tools": ["parse_bank_statement"],
                "input_mapping": {"raw_statement": "raw_statement"},
                "output_key": "parsed_statement",
                "metadata": {"capabilities": ["extraction"]},
            },
            "node_auditor": {
                "node_id": "node_auditor",
                "name": "Auditor",
                "role": "Auditor",
                "system_prompt": "Match transactions and verify differences",
                "tools": ["fuzzy_match_transactions", "calculate_reconciliation_difference"],
                "input_mapping": {"bank_transactions": "parsed_statement"},

                "output_key": "reconciliation_summary",
                "metadata": {"capabilities": ["comparison", "calculation", "verification"]},
            },
        },
        "edges": [
            {"source_node_id": "node_parser", "target_node_id": "node_auditor"}
        ],
    }
    mock_gateway = MockModelGateway(default_content=json.dumps(canned_graph))
    generator = ArchitectureGenerator(model_gateway=mock_gateway)
    graph, val, qual = await generator.generate_with_validation(sample_task_spec, available_tools=recon_catalog)

    assert graph.graph_id == "mock_generated_v0"
    assert graph.metadata.get("generation_method") == "llm"
    assert val.valid is True
    assert qual.overall_score >= 0.80


@pytest.mark.anyio
async def test_25_structured_output_validation(sample_task_spec, recon_catalog):
    """25. Test that generated graph JSON is validated against strict Pydantic model."""
    valid_data = {
        "graph_id": "g_pydantic",
        "name": "Pydantic Valid",
        "entry_node_id": "n1",
        "terminal_node_ids": ["n1"],
        "nodes": {
            "n1": {
                "node_id": "n1",
                "name": "Sole Node",
                "role": "Worker",
                "system_prompt": "Do all work",
                "tools": [],
            }
        },
        "edges": [],
    }
    mock_gateway = MockModelGateway(default_content=f"```json\n{json.dumps(valid_data)}\n```")
    generator = ArchitectureGenerator(model_gateway=mock_gateway)
    graph = await generator.generate(sample_task_spec, available_tools=recon_catalog)
    assert graph.graph_id == "g_pydantic"


@pytest.mark.anyio
async def test_26_malformed_model_response(sample_task_spec, recon_catalog):
    """26. Test malformed model output triggers safe fallback or error."""
    broken_content = "Here is your graph: { invalid json"
    mock_gateway = MockModelGateway(default_content=broken_content)

    # When fallback_on_error=False, raises RuntimeError
    strict_gen = ArchitectureGenerator(model_gateway=mock_gateway, fallback_on_error=False)
    with pytest.raises(RuntimeError, match="Architecture generation failed"):
        await strict_gen.generate(sample_task_spec, available_tools=recon_catalog)

    # When fallback_on_error=True (default), falls back safely to deterministic generator
    safe_gen = ArchitectureGenerator(model_gateway=mock_gateway, fallback_on_error=True)
    graph = await safe_gen.generate(sample_task_spec, available_tools=recon_catalog)
    assert graph is not None
    assert graph.metadata.get("generation_method") == "fallback"
    assert "llm_generation_error" in graph.metadata


@pytest.mark.anyio
async def test_27_bounded_repair(sample_task_spec, recon_catalog):
    """27. Test bounded repair: initial malformed JSON is fixed on 1 retry."""
    repair_json = json.dumps({
        "graph_id": "repaired_graph_v0",
        "name": "Repaired Architecture",
        "entry_node_id": "node_1",
        "terminal_node_ids": ["node_1"],
        "nodes": {
            "node_1": {
                "node_id": "node_1",
                "name": "Primary Worker",
                "role": "Worker",
                "system_prompt": "Work",
                "tools": [],
            }
        },
        "edges": [],
    })
    mock_gateway = MockModelGateway(
        default_content="Malformed { unclosed json",
        canned_responses={"Fix the following text": repair_json},
    )
    generator = ArchitectureGenerator(model_gateway=mock_gateway)
    graph = await generator.generate(sample_task_spec, available_tools=recon_catalog)
    assert graph.graph_id == "repaired_graph_v0"
    assert graph.metadata.get("repaired") is True
    assert graph.metadata.get("generation_method") == "llm"


# ---------------------------------------------------------------------------
# 8. DETERMINISTIC FALLBACK TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_28_fallback_generation_without_llm(sample_task_spec, recon_catalog):
    """28. Test fallback generation without LLM creates valid GraphDefinition."""
    generator = ArchitectureGenerator(model_gateway=None)
    graph, val, qual = await generator.generate_with_validation(sample_task_spec, available_tools=recon_catalog)
    assert graph is not None
    assert graph.metadata.get("generation_method") == "fallback"
    assert val.valid is True
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2


@pytest.mark.anyio
async def test_29_fallback_never_invents_tools(sample_task_spec, recon_catalog):
    """29. Test that fallback only assigns tools that exist in the supplied catalog."""
    generator = ArchitectureGenerator(model_gateway=None)
    # Provide an empty catalog
    graph = await generator.generate(sample_task_spec, available_tools=[])
    for node in graph.nodes.values():
        assert len(node.tools) == 0


@pytest.mark.anyio
async def test_30_fallback_produces_executable_dag(sample_task_spec, recon_catalog):
    """30. Test that fallback graph passes topological validation and Kahn's algorithm."""
    generator = ArchitectureGenerator(model_gateway=None)
    graph = await generator.generate(sample_task_spec, available_tools=recon_catalog)
    graph.validate_graph()
    order = graph.get_topological_order()
    assert len(order) == len(graph.nodes)


# ---------------------------------------------------------------------------
# 9. QUALITY & COMPLEXITY METRICS TESTS
# ---------------------------------------------------------------------------

def test_31_architecture_quality_result(sample_task_spec, recon_catalog):
    """31. Test ArchitectureQualityScore fields and calculation."""
    generator = ArchitectureGenerator()
    import asyncio
    graph, val, qual = asyncio.run(
        generator.generate_with_validation(sample_task_spec, available_tools=recon_catalog)
    )
    assert 0.0 <= qual.overall_score <= 1.0
    assert 0.0 <= qual.capability_coverage_score <= 1.0
    assert 0.0 <= qual.tool_validity_score <= 1.0
    assert 0.0 <= qual.structural_efficiency_score <= 1.0
    assert 0.0 <= qual.risk_alignment_score <= 1.0


def test_32_capability_coverage_metrics(sample_task_spec, recon_catalog):
    """32. Test capability coverage scoring accurately reflects covered capabilities."""
    generator = ArchitectureGenerator()
    import asyncio
    _, val, qual = asyncio.run(
        generator.generate_with_validation(sample_task_spec, available_tools=recon_catalog)
    )
    assert qual.capability_coverage_score > 0.50
    assert "extraction" in val.capability_coverage


def test_33_graph_complexity_metrics(sample_task_spec, recon_catalog):
    """33. Test graph complexity boundaries and metric reporting."""
    generator = ArchitectureGenerator()
    # Create an excessively large graph to test boundary enforcement
    nodes = {
        f"node_{i}": NodeModel(node_id=f"node_{i}", name=f"Node {i}", role="Worker", system_prompt="Work")
        for i in range(MAX_NODE_COUNT + 2)
    }
    edges = [EdgeModel(source_node_id=f"node_{i}", target_node_id=f"node_{i+1}") for i in range(len(nodes) - 1)]
    graph = GraphDefinition(
        graph_id="g_bloat",
        name="Bloated Graph",
        entry_node_id="node_0",
        terminal_node_ids=[f"node_{len(nodes)-1}"],
        nodes=nodes,
        edges=edges,
    )
    val = generator.validate_architecture(graph, sample_task_spec, recon_catalog)
    assert val.valid is False
    assert any("exceeds maximum limit" in e for e in val.errors)


# ---------------------------------------------------------------------------
# 10. INTEGRATION & DEMONSTRATION TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_34_generated_graph_executes_using_existing_runtime(sample_task_spec, recon_registry):
    """34. Test generated graph executes successfully in AgentGraphRuntime."""
    generator = ArchitectureGenerator(model_gateway=None)
    catalog = recon_registry.list_schemas()
    graph = await generator.generate(sample_task_spec, available_tools=catalog)

    executor = ToolExecutor(registry=recon_registry)
    mock_gateway = MockModelGateway(default_content="Simulation step output")
    runtime = AgentGraphRuntime(model_gateway=mock_gateway, tool_executor=executor)

    inputs = {
        "raw_statement": [
            {"transaction_id": "TX-001", "date": "2026-03-01", "description": "WIRE TRANSFER FROM ACME", "amount": 1000.00, "vendor": "ACME"}
        ],
        "ledger_entries": [
            {"entry_id": "ledg_001", "date": "2026-03-01", "vendor": "ACME", "amount": 1000.00}
        ],
    }

    state = await runtime.run(graph=graph, inputs=inputs, goal=sample_task_spec.original_goal)
    assert state.status == "completed"
    assert state.latency_ms >= 0
    assert len(state.node_outputs) > 0


@pytest.mark.anyio
async def test_35_finance_reconciliation_goal_generates_executable_architecture(recon_registry):
    """35. Part 19: End-to-end finance reconciliation generation and execution."""
    goal_analyzer = GoalAnalyzer(tool_registry=recon_registry)
    task_spec = await goal_analyzer.analyze(
        "Reconcile these bank transactions against the general ledger and identify unexplained discrepancies."
    )
    assert task_spec.domain == "finance"

    generator = ArchitectureGenerator(tool_registry=recon_registry)
    graph, val, qual = await generator.generate_with_validation(task_spec)

    assert val.valid is True
    assert qual.overall_score >= 0.80

    executor = ToolExecutor(registry=recon_registry)
    mock_gateway = MockModelGateway()
    runtime = AgentGraphRuntime(model_gateway=mock_gateway, tool_executor=executor)

    inputs = {
        "bank_transactions": [{"transaction_id": "TX-100", "date": "2026-03-01", "description": "PAYMENT", "amount": 500.00, "vendor": "VENDOR"}],
        "general_ledger": [{"entry_id": "gl_1", "date": "2026-03-01", "vendor": "VENDOR", "amount": 500.00}],
    }

    state = await runtime.run(graph=graph, inputs=inputs, goal=task_spec.original_goal)
    assert state.status == "completed"
    assert len(state.node_outputs) == len(graph.nodes)



# ---------------------------------------------------------------------------
# 11. CROSS-DOMAIN SANITY CHECKS (PART 20)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_36_cross_domain_research_and_data_analysis():
    """36. Part 20: Research and data goals produce distinct, domain-appropriate architectures."""
    analyzer = GoalAnalyzer()
    generator = ArchitectureGenerator()

    # Research domain
    research_spec = await analyzer.analyze(
        "Compare three open-source observability platforms using public evidence."
    )
    research_graph, res_val, _ = await generator.generate_with_validation(research_spec)
    assert research_spec.domain == "research"
    assert res_val.valid is True

    # Data domain
    data_spec = await analyzer.analyze("Find anomalies in this CSV and explain likely causes.")
    data_graph, data_val, _ = await generator.generate_with_validation(data_spec)
    assert data_spec.domain == "data"
    assert data_val.valid is True

    # Validate architectures are structurally distinct and tailored
    assert research_graph.name != data_graph.name
    assert research_graph.graph_id != data_graph.graph_id
    assert Capability.COMPARISON in research_spec.required_capabilities
    assert Capability.ANOMALY_DETECTION in data_spec.required_capabilities


# ---------------------------------------------------------------------------
# 12. API ENDPOINT TESTS (PART 17)
# ---------------------------------------------------------------------------

def test_37_api_generate_architecture_endpoint(api_client, sample_task_spec, recon_catalog):
    """37. Part 17: Test POST /generate-architecture internal endpoint."""
    # Call with full TaskSpecification
    resp = api_client.post(
        "/generate-architecture",
        json={
            "task_spec": sample_task_spec.model_dump(mode="json"),
            "available_tools": recon_catalog,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "graph" in data
    assert "validation" in data
    assert "quality" in data
    assert data["validation"]["valid"] is True
    assert data["quality"]["overall_score"] > 0.70

    # Call with raw goal string
    resp_goal = api_client.post(
        "/generate-architecture",
        json={"goal": "Compare open-source databases for Python"},
    )
    assert resp_goal.status_code == 200
    assert resp_goal.json()["validation"]["valid"] is True

    # Empty payload rejected with 400
    resp_bad = api_client.post("/generate-architecture", json={})
    assert resp_bad.status_code == 400
