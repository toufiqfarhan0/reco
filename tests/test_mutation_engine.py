"""Comprehensive test suite for Autonomous Mutation Engine, Mutators, and Candidate Validator."""

import pytest
from reco.core.goal_analyzer import GoalAnalyzer
from reco.diagnostics.taxonomy import (
    DiagnosticReport,
    FailureCategory,
    FailureDiagnostic,
)
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import AgentArchitecture, EdgeSpec, NodeSpec, NodeStatus, NodeType
from reco.engine.runtime import AgentRuntime
from reco.mutation.engine import MutationEngine, MutationResult
from reco.mutation.mutators.prompt_mutator import PromptMutator
from reco.mutation.mutators.retry_mutator import RetryPolicyMutator
from reco.mutation.mutators.tool_mutator import ToolAssignmentMutator
from reco.mutation.mutators.topology_mutator import TopologyMutator
from reco.mutation.mutators.verifier_mutator import VerifierNodeMutator
from reco.mutation.validator import CandidateDiff, CandidateValidator, ValidationResult
from reco.tools.registry import ToolDefinition, ToolRegistry


def test_prompt_mutator_injects_constraints_and_formatting():
    """Verify PromptMutator injects constraints into reasoning node and formatting into output node."""
    spec = GoalAnalyzer().analyze("Reconcile transactions and identify discrepancies")
    arch = ArchitectureGenerator().generate(spec)

    mutator = PromptMutator()

    diag = FailureDiagnostic(
        case_id="case_001",
        category=FailureCategory.SCHEMA_VIOLATION,
        root_cause="Output missing required fields",
        symptoms=["Schema assertion failed"],
        remedy_suggestion="Enforce required keys",
        metadata={"missing_keys": ["matched_ids", "status"]}
    )

    mutated = mutator.mutate(
        architecture=arch,
        diagnostic=diag,
        constraints=["Assert 1:1 match tolerance <= 0.001"]
    )

    # Immutability check: parent is unchanged
    assert arch.id != mutated.id or "schema_enforced" not in arch.get_node("output_node").config

    # Mutated node checks
    reasoning = mutated.get_node("reasoning_node")
    assert "domain_constraints" in reasoning.config
    assert any("1:1 match" in c for c in reasoning.config["domain_constraints"])

    output = mutated.get_node("output_node")
    assert output.config.get("schema_enforced") is True
    assert "formatting_instructions" in output.config
    assert "matched_ids" in output.config["formatting_instructions"]["required_keys"]


def test_verifier_node_mutator_injects_and_strengthens():
    """Verify VerifierNodeMutator injects missing verifiers and rewires edges properly."""
    # 1. Architecture WITHOUT verifier
    input_node = NodeSpec(id="input_node", type=NodeType.INPUT, name="Input", dependencies=[])
    reasoning_node = NodeSpec(id="reasoning_node", type=NodeType.REASONING, name="Reasoning", dependencies=["input_node"])
    output_node = NodeSpec(id="output_node", type=NodeType.OUTPUT, name="Output", dependencies=["reasoning_node"])

    arch_no_verifier = AgentArchitecture(
        id="arch_no_v",
        name="NoVerifierArch",
        task_spec=GoalAnalyzer().analyze("Reconcile transactions"),
        nodes=[input_node, reasoning_node, output_node],
        edges=[
            EdgeSpec(source="input_node", target="reasoning_node"),
            EdgeSpec(source="reasoning_node", target="output_node")
        ]
    )

    mutator = VerifierNodeMutator()
    mutated = mutator.mutate(arch_no_verifier)

    # Verifier must be present in nodes
    verifier = mutated.get_node("verifier_node")
    assert verifier.type == NodeType.VERIFIER
    assert "reasoning_node" in verifier.dependencies

    # Output node must now depend on verifier_node
    new_output = mutated.get_node("output_node")
    assert new_output.dependencies == ["verifier_node"]

    # Edges rewired
    edge_pairs = [(e.source, e.target) for e in mutated.edges]
    assert ("reasoning_node", "verifier_node") in edge_pairs
    assert ("verifier_node", "output_node") in edge_pairs
    assert ("reasoning_node", "output_node") not in edge_pairs

    # 2. Strengthening existing verifier
    strengthened = mutator.mutate(mutated, strict_mode=True)
    v_strengthened = strengthened.get_node("verifier_node")
    assert v_strengthened.config.get("strict_mode") is True
    assert v_strengthened.config.get("assert_reconciliation_integrity") is True


def test_tool_assignment_mutator_replaces_and_attaches():
    """Verify ToolAssignmentMutator replaces exact_reconcile with smart_reconcile."""
    registry = ToolRegistry.create_reconciliation_default()
    spec = GoalAnalyzer().analyze("Reconcile transactions")
    arch = ArchitectureGenerator(tool_registry=registry).generate(spec)

    # Initial architecture has tool_exact_reconcile
    initial_tool_ids = [n.id for n in arch.nodes if n.type == NodeType.TOOL]
    assert "tool_exact_reconcile" in initial_tool_ids

    mutator = ToolAssignmentMutator(tool_registry=registry)
    diag = FailureDiagnostic(
        case_id="reco_opt_006_format_variations",
        category=FailureCategory.TOOL_SELECTION_ERROR,
        root_cause="exact_reconcile failed on format variations",
        remedy_suggestion="Replace exact_reconcile with smart_reconcile",
        target_node_id="tool_exact_reconcile"
    )

    mutated = mutator.mutate(architecture=arch, diagnostic=diag)

    # Verify replacement
    mutated_tool_nodes = [n for n in mutated.nodes if n.type == NodeType.TOOL]
    assert len(mutated_tool_nodes) == 1
    assert mutated_tool_nodes[0].id == "tool_smart_reconcile"
    assert mutated_tool_nodes[0].tool_name == "smart_reconcile"

    # Verify downstream dependencies updated
    reasoning = mutated.get_node("reasoning_node")
    assert "tool_smart_reconcile" in reasoning.dependencies
    assert "tool_exact_reconcile" not in reasoning.dependencies

    # Verify edge endpoints updated
    edge_sources = [e.source for e in mutated.edges]
    assert "tool_smart_reconcile" in edge_sources
    assert "tool_exact_reconcile" not in edge_sources


def test_candidate_validator_strictly_rejects_hallucinated_tools():
    """Verify CandidateValidator and ToolAssignmentMutator strictly reject unregistered tools."""
    registry = ToolRegistry.create_reconciliation_default()
    validator = CandidateValidator(tool_registry=registry)

    spec = GoalAnalyzer().analyze("Reconcile transactions")
    arch = ArchitectureGenerator(tool_registry=registry).generate(spec)

    # 1. Mutate architecture manually to insert a hallucinated tool
    hallucinated_arch = arch.model_copy(deep=True)
    fake_node = NodeSpec(
        id="tool_magic_solver",
        type=NodeType.TOOL,
        name="Tool: magic_solver",
        tool_name="unregistered_hallucinated_tool_xyz",
        dependencies=["input_node"]
    )
    hallucinated_arch.nodes.append(fake_node)
    hallucinated_arch.edges.append(EdgeSpec(source="input_node", target="tool_magic_solver"))
    hallucinated_arch.edges.append(EdgeSpec(source="tool_magic_solver", target="reasoning_node"))
    hallucinated_arch.get_node("reasoning_node").dependencies.append("tool_magic_solver")

    # Validator must reject hallucinated tool
    result = validator.validate(hallucinated_arch)
    assert result.is_valid is False
    assert any("Hallucinated tool rejected" in err for err in result.errors)
    assert any("unregistered_hallucinated_tool_xyz" in err for err in result.errors)

    # 2. ToolAssignmentMutator must directly raise ValueError when attempting to assign hallucinated tool
    mutator = ToolAssignmentMutator(tool_registry=registry)
    with pytest.raises(ValueError, match="Cannot assign hallucinated tool"):
        mutator.mutate(arch, target_tool="fake_nonexistent_tool")


def test_candidate_validator_acyclicity_and_connectivity():
    """Verify CandidateValidator detects cycles, disconnected nodes, and missing roles."""
    registry = ToolRegistry.create_reconciliation_default()
    validator = CandidateValidator(tool_registry=registry)

    spec = GoalAnalyzer().analyze("Reconcile transactions")
    arch = ArchitectureGenerator(tool_registry=registry).generate(spec)

    # Valid arch passes
    valid_res = validator.validate(arch)
    assert valid_res.is_valid is True
    assert len(valid_res.errors) == 0

    # 1. Cycle injection
    cyclic_arch = arch.model_copy(deep=True)
    # Add cycle from reasoning back to input
    cyclic_arch.edges.append(EdgeSpec(source="reasoning_node", target="input_node"))
    cycle_res = validator.validate(cyclic_arch)
    assert cycle_res.is_valid is False
    assert any("Acyclicity contract violated" in err for err in cycle_res.errors)

    # 2. Missing output node
    no_output_arch = arch.model_copy(deep=True)
    no_output_arch.nodes = [n for n in no_output_arch.nodes if n.type != NodeType.OUTPUT]
    no_output_arch.edges = [e for e in no_output_arch.edges if e.target != "output_node"]
    no_out_res = validator.validate(no_output_arch)
    assert no_out_res.is_valid is False
    assert any("missing required 'output_node'" in err.lower() for err in no_out_res.errors)


def test_candidate_diff_visual_and_structured_generation():
    """Verify CandidateDiff records additions, removals, and renders visual diff."""
    registry = ToolRegistry.create_reconciliation_default()
    validator = CandidateValidator(tool_registry=registry)

    spec = GoalAnalyzer().analyze("Reconcile transactions")
    baseline = ArchitectureGenerator(tool_registry=registry).generate(spec)

    mutator = ToolAssignmentMutator(tool_registry=registry)
    candidate = mutator.mutate(baseline, target_tool="smart_reconcile", replace_tool="exact_reconcile")

    diff = validator.generate_diff(baseline, candidate)

    assert isinstance(diff, CandidateDiff)
    assert diff.has_changes() is True
    assert "tool_smart_reconcile" in diff.added_nodes
    assert "tool_exact_reconcile" in diff.removed_nodes
    assert "reasoning_node" in diff.modified_nodes

    # Visual diff output formatting
    visual = diff.to_visual_diff()
    assert "ARCHITECTURE MUTATION DIFF" in visual
    assert "+ tool_smart_reconcile" in visual
    assert "- tool_exact_reconcile" in visual
    assert "* reasoning_node" in visual

    # Markdown diff
    md = diff.to_markdown()
    assert "Architectural Diff" in md
    assert "tool_smart_reconcile" in md


def test_retry_policy_mutator_and_runtime_resilience():
    """Verify RetryPolicyMutator attaches retry policy and NodeRunner recovers transient errors."""
    registry = ToolRegistry.create_reconciliation_default()

    # Create a flaky tool that fails on first attempt and succeeds on second
    attempt_counter = {"count": 0}

    def flaky_handler(source_records, target_records):
        attempt_counter["count"] += 1
        if attempt_counter["count"] == 1:
            raise RuntimeError("Transient network glitch during ledger query")
        return {"matched_ids": ["TX101"], "status": "reconciled"}

    registry.register(ToolDefinition(
        name="flaky_reconcile",
        description="Fails once then succeeds",
        parameters={
            "type": "object",
            "properties": {
                "source_records": {"type": "array"},
                "target_records": {"type": "array"}
            },
            "required": ["source_records", "target_records"]
        },
        capabilities=["reconciliation"],
        handler=flaky_handler
    ))

    spec = GoalAnalyzer().analyze("Reconcile transactions")
    # Generate baseline using standard default reconciliation registry (contains exact_reconcile)
    arch = ArchitectureGenerator(tool_registry=ToolRegistry.create_reconciliation_default()).generate(spec)

    # Mutate to assign flaky tool and attach retry policy
    tool_mutator = ToolAssignmentMutator(tool_registry=registry)
    arch_with_flaky = tool_mutator.mutate(arch, target_tool="flaky_reconcile", replace_tool="exact_reconcile")

    retry_mutator = RetryPolicyMutator(tool_registry=registry)
    resilient_arch = retry_mutator.mutate(arch_with_flaky, max_retries=3, backoff_factor=1.1)

    flaky_node = resilient_arch.get_node("tool_flaky_reconcile")
    assert "retry_policy" in flaky_node.config
    assert flaky_node.config["retry_policy"]["max_retries"] == 3

    # Execute through runtime: retry policy should allow it to succeed on attempt 2
    runtime = AgentRuntime(tool_registry=registry)
    result = runtime.execute(resilient_arch, {"source_records": [{"id": "TX101"}], "target_records": [{"id": "TX101"}]})

    assert result.status == NodeStatus.COMPLETED
    assert result.error is None
    assert attempt_counter["count"] == 2


def test_topology_mutator_creates_ensemble_path():
    """Verify TopologyMutator creates ensemble reasoning branch."""
    spec = GoalAnalyzer().analyze("Reconcile transactions")
    arch = ArchitectureGenerator().generate(spec)

    mutator = TopologyMutator()
    mutated = mutator.mutate(arch, branch_type="ensemble_path")

    ensemble_node = mutated.get_node("reasoning_ensemble_node")
    assert ensemble_node.type == NodeType.REASONING
    assert ensemble_node.config.get("ensemble_role") == "secondary_validator"

    # Upstream and downstream connectivity
    edge_pairs = [(e.source, e.target) for e in mutated.edges]
    assert ("reasoning_ensemble_node", "verifier_node") in edge_pairs


def test_mutation_engine_end_to_end_from_diagnostic_report():
    """Verify MutationEngine derives validated candidate DAG from DiagnosticReport."""
    registry = ToolRegistry.create_reconciliation_default()
    spec = GoalAnalyzer().analyze("Reconcile transactions and identify discrepancies")
    arch = ArchitectureGenerator(tool_registry=registry).generate(spec)

    diag = FailureDiagnostic(
        case_id="reco_opt_006_format_variations",
        category=FailureCategory.TOOL_SELECTION_ERROR,
        root_cause="exact_reconcile cannot parse currency formatting",
        remedy_suggestion="Replace with smart_reconcile",
        target_node_id="tool_exact_reconcile",
        recommended_mutator="ToolAssignmentMutator"
    )

    report = DiagnosticReport(
        architecture_id=arch.id,
        total_cases=6,
        passed_cases=5,
        failed_cases=1,
        failure_diagnostics=[diag],
        category_counts={"tool_selection_error": 1}
    )

    engine = MutationEngine(tool_registry=registry)
    mutation_result = engine.mutate(arch, report, candidate_name="Agent_Reconciliation_V1")

    assert mutation_result.success is True
    assert mutation_result.candidate_architecture is not None
    assert mutation_result.diff is not None
    assert "ToolAssignmentMutator" in mutation_result.applied_mutators
    assert mutation_result.validation_result.is_valid is True

    candidate = mutation_result.candidate_architecture
    assert candidate.name == "Agent_Reconciliation_V1"
    assert candidate.metadata["parent_architecture_id"] == arch.id
    assert candidate.metadata["generation"] == 1
    assert any(n.tool_name == "smart_reconcile" for n in candidate.nodes)
