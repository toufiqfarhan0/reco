"""Comprehensive test suite for Step 5 Track 1: Multi-Candidate Exploration & Pareto Dominance Selection.

Verifies:
1. Multi-Candidate Pool Generation (`reco/mutation/generator.py`):
   - Candidate A (Prompt Specialist): Targeted prompt refinement with edge-case instructions & few-shot formatting.
   - Candidate B (Verifier Specialist): Dedicated verification and schema-conformance guardrail injection.
   - Candidate C (Topology / Tool Specialist): Graph restructuring and specialized analytical tools assignment.
   - Strict DAG validation: CandidateValidator enforcement rejecting broken graphs and hallucinated tools.
2. Tournament Evaluation & Pareto Selection (`reco/evaluators/comparison.py`):
   - 4-axis scorecard evaluation (Accuracy, Reliability, Cost, Latency) across competing candidates.
   - Multi-dimensional Pareto dominance and frontier identification.
   - Automatic tournament winner selection maximizing accuracy without catastrophic regressions.
"""

import pytest
from reco.benchmarks.base import BenchmarkSplit
from reco.benchmarks.reconciliation.dataset import get_reconciliation_benchmark_suite
from reco.core.goal_analyzer import GoalAnalyzer
from reco.diagnostics.analyzer import FailureAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import AgentArchitecture, EdgeSpec, NodeSpec, NodeType
from reco.evaluators.comparison import (
    TournamentEvaluator,
    TournamentResult,
    compute_pareto_frontier,
    is_pareto_dominant_pair,
    select_tournament_winner,
)
from reco.evaluators.scorecard import Scorecard, ScorecardEvaluator
from reco.mutation.generator import CandidatePool, CandidatePoolGenerator, CandidateVariant
from reco.mutation.validator import CandidateValidator
from reco.tools.registry import ToolRegistry


# ==============================================================================
# 1. Multi-Candidate Pool Generation & Specialist Verification
# ==============================================================================

def test_multi_candidate_pool_synthesis_and_specialists():
    """Verify CandidatePoolGenerator synthesizes 3 competing specialist variants (A, B, C) from diagnostics."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()

    # Step 1: Synthesize Baseline V0 with exact_reconcile
    spec = GoalAnalyzer().analyze("Reconcile financial transactions and detect discrepancies")
    baseline = ArchitectureGenerator(tool_registry=registry).generate(spec, architecture_name="Agent_Reconciliation_V0")

    # Step 2: Evaluate on optimization split and diagnose failures
    evaluator = ScorecardEvaluator()
    base_sc = evaluator.evaluate(baseline, suite, split=BenchmarkSplit.OPTIMIZATION)
    analyzer = FailureAnalyzer(tool_registry=registry)
    diag_report = analyzer.analyze_scorecard(base_sc, suite, baseline)

    assert diag_report.failed_cases > 0, "Baseline should have diagnosed failures on format variations"

    # Step 3: Synthesize 3-Candidate Exploration Pool
    generator = CandidatePoolGenerator(tool_registry=registry)
    pool = generator.generate_pool(baseline, diag_report)

    assert isinstance(pool, CandidatePool)
    assert len(pool) == 3

    cand_a = pool.get_candidate("A")
    cand_b = pool.get_candidate("B")
    cand_c = pool.get_candidate("C")

    assert cand_a is not None
    assert cand_b is not None
    assert cand_c is not None

    # Verify Candidate A: Prompt Specialist
    assert cand_a.specialist_type == "prompt"
    assert "PromptMutator" in cand_a.applied_mutators
    assert cand_a.targeted_node == "reasoning_node"
    assert cand_a.validation_result.is_valid is True
    assert cand_a.prompt_diff is not None
    assert "reasoning_node" in cand_a.prompt_diff["mutated"]

    # Verify Candidate B: Verifier Specialist
    assert cand_b.specialist_type == "verifier"
    assert "VerifierNodeMutator" in cand_b.applied_mutators
    assert cand_b.validation_result.is_valid is True
    # Must contain a dedicated verifier node
    node_types_b = {n.type for n in cand_b.architecture.nodes}
    assert NodeType.VERIFIER in node_types_b
    assert any("verifier" in n.id for n in cand_b.architecture.nodes)

    # Verify Candidate C: Topology / Tool Specialist
    assert cand_c.specialist_type == "topology_tool"
    assert "ToolAssignmentMutator" in cand_c.applied_mutators
    assert cand_c.validation_result.is_valid is True
    # Must have assigned smart_reconcile
    tool_names_c = {n.tool_name for n in cand_c.architecture.nodes if n.type == NodeType.TOOL}
    assert "smart_reconcile" in tool_names_c


def test_candidate_validator_strictly_enforced_on_pool():
    """Verify CandidateValidator guarantees acyclicity, reachability, and rejects hallucinated tools."""
    registry = ToolRegistry.create_reconciliation_default()
    validator = CandidateValidator(tool_registry=registry)
    spec = GoalAnalyzer().analyze("Reconcile financial transactions")

    # Candidate with a hallucinated tool must be rejected by validator
    hallucinated_arch = AgentArchitecture(
        id="hallucinated_arch",
        name="Hallucinated DAG",
        task_spec=spec,
        nodes=[
            NodeSpec(id="input_node", type=NodeType.INPUT, name="Input", dependencies=[]),
            NodeSpec(id="tool_fake", type=NodeType.TOOL, tool_name="imaginary_quantum_reconcile", name="Fake Tool", dependencies=["input_node"]),
            NodeSpec(id="output_node", type=NodeType.OUTPUT, name="Output", dependencies=["tool_fake"]),
        ],
        edges=[
            EdgeSpec(source="input_node", target="tool_fake"),
            EdgeSpec(source="tool_fake", target="output_node"),
        ]
    )
    val_hallucinated = validator.validate(hallucinated_arch)
    assert val_hallucinated.is_valid is False
    assert any("Hallucinated tool rejected" in err for err in val_hallucinated.errors)

    # Broken cyclic graph must be rejected
    cyclic_arch = AgentArchitecture(
        id="cyclic_arch",
        name="Cyclic DAG",
        task_spec=spec,
        nodes=[
            NodeSpec(id="input_node", type=NodeType.INPUT, name="Input", dependencies=[]),
            NodeSpec(id="node_a", type=NodeType.REASONING, name="A", dependencies=["input_node", "node_b"]),
            NodeSpec(id="node_b", type=NodeType.REASONING, name="B", dependencies=["node_a"]),
            NodeSpec(id="output_node", type=NodeType.OUTPUT, name="Output", dependencies=["node_b"]),
        ],
        edges=[
            EdgeSpec(source="input_node", target="node_a"),
            EdgeSpec(source="node_a", target="node_b"),
            EdgeSpec(source="node_b", target="node_a"),
            EdgeSpec(source="node_b", target="output_node"),
        ]
    )
    val_cyclic = validator.validate(cyclic_arch)
    assert val_cyclic.is_valid is False
    assert any("Acyclicity contract violated" in err for err in val_cyclic.errors)


def test_candidate_pool_structural_diffs():
    """Verify each candidate in the pool exhibits distinct architectural diffs against the parent baseline."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()

    spec = GoalAnalyzer().analyze("Reconcile financial ledger transactions")
    baseline = ArchitectureGenerator(tool_registry=registry).generate(spec, architecture_name="Baseline_V0")

    evaluator = ScorecardEvaluator()
    base_sc = evaluator.evaluate(baseline, suite, split=BenchmarkSplit.OPTIMIZATION)
    analyzer = FailureAnalyzer(tool_registry=registry)
    diag_report = analyzer.analyze_scorecard(base_sc, suite, baseline)

    generator = CandidatePoolGenerator(tool_registry=registry)
    pool = generator.generate_pool(baseline, diag_report)

    for cand in pool:
        assert cand.diff is not None
        assert cand.diff.has_changes() is True
        md = cand.diff.to_markdown()
        assert "Architectural Diff" in md


# ==============================================================================
# 2. Tournament Evaluation & 4-Axis Scorecards
# ==============================================================================

def test_tournament_evaluator_4_axis_scorecards():
    """Verify TournamentEvaluator computes 4-axis empirical scorecards across all competing candidates."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()

    spec = GoalAnalyzer().analyze("Reconcile financial transactions and detect discrepancies")
    baseline = ArchitectureGenerator(tool_registry=registry).generate(spec, architecture_name="Baseline_V0")

    evaluator = ScorecardEvaluator()
    base_sc = evaluator.evaluate(baseline, suite, split=BenchmarkSplit.OPTIMIZATION)
    analyzer = FailureAnalyzer(tool_registry=registry)
    diag_report = analyzer.analyze_scorecard(base_sc, suite, baseline)

    pool = CandidatePoolGenerator(tool_registry=registry).generate_pool(baseline, diag_report)

    tournament = TournamentEvaluator()
    tourney_result = tournament.evaluate_tournament(
        baseline_architecture=baseline,
        candidates=pool,
        suite=suite,
        split=BenchmarkSplit.OPTIMIZATION
    )

    assert isinstance(tourney_result, TournamentResult)
    assert len(tourney_result.candidates) == 3

    # Verify each candidate scorecard matrix
    for cand in tourney_result.candidates:
        assert cand.scorecard is not None
        assert cand.scorecard.total_cases == 6
        assert 0.0 <= cand.scorecard.accuracy <= 1.0
        assert 0.0 <= cand.scorecard.reliability <= 1.0
        assert cand.scorecard.latency_ms > 0.0
        assert 0.0 <= cand.win_rate <= 100.0

    # Candidate C with smart_reconcile achieves 100% accuracy on optimization split
    cand_c = tourney_result.candidates[2]
    assert cand_c.id == "C"
    assert cand_c.scorecard.accuracy == 1.0
    assert cand_c.scorecard.accurate_cases == 6
    assert cand_c.win_rate == 100.0

    # Markdown rendering verification
    md = tourney_result.to_markdown()
    assert "# Multi-Candidate Tournament Evaluation Report" in md
    assert "Candidate C" in md
    assert "Scorecard Matrix" in md


# ==============================================================================
# 3. Pareto Dominance & Selection Functions
# ==============================================================================

def test_is_pareto_dominant_pair_logic():
    """Verify 4-axis Pareto dominance logic (Accuracy, Reliability, Cost, Latency)."""
    # Scorecard A strictly better on accuracy, equal on other 3 axes -> dominates B
    sc_a = Scorecard(
        name="A", split="optimization", total_cases=6, accurate_cases=6, reliable_cases=6,
        accuracy=1.0, reliability=1.0, cost_usd=0.001, latency_ms=50.0
    )
    sc_b = Scorecard(
        name="B", split="optimization", total_cases=6, accurate_cases=5, reliable_cases=6,
        accuracy=0.833, reliability=1.0, cost_usd=0.001, latency_ms=50.0
    )
    assert is_pareto_dominant_pair(sc_a, sc_b) is True
    assert is_pareto_dominant_pair(sc_b, sc_a) is False

    # Scorecard C is higher accuracy but higher latency -> Tradeoff, neither dominates
    sc_c = Scorecard(
        name="C", split="optimization", total_cases=6, accurate_cases=6, reliable_cases=6,
        accuracy=1.0, reliability=1.0, cost_usd=0.001, latency_ms=120.0
    )
    sc_d = Scorecard(
        name="D", split="optimization", total_cases=6, accurate_cases=5, reliable_cases=6,
        accuracy=0.833, reliability=1.0, cost_usd=0.001, latency_ms=30.0
    )
    assert is_pareto_dominant_pair(sc_c, sc_d) is False
    assert is_pareto_dominant_pair(sc_d, sc_c) is False


def test_compute_pareto_frontier_and_winner_selection():
    """Verify compute_pareto_frontier isolates non-dominated candidates and selects winner maximizing accuracy."""
    arch_dummy = ArchitectureGenerator().generate(
        GoalAnalyzer().analyze("Reconcile transactions"),
        architecture_name="Dummy"
    )

    # Variant 1: 83.3% accuracy, fast
    v1 = CandidateVariant(
        id="A", name="Cand A", specialist_type="prompt", architecture=arch_dummy,
        scorecard=Scorecard(
            name="A", split="opt", total_cases=6, accurate_cases=5, reliable_cases=6,
            accuracy=0.833, reliability=1.0, cost_usd=0.001, latency_ms=25.0
        )
    )
    # Variant 2: 83.3% accuracy, slower, more expensive -> dominated by V1
    v2 = CandidateVariant(
        id="B", name="Cand B", specialist_type="verifier", architecture=arch_dummy,
        scorecard=Scorecard(
            name="B", split="opt", total_cases=6, accurate_cases=5, reliable_cases=6,
            accuracy=0.833, reliability=1.0, cost_usd=0.002, latency_ms=45.0
        )
    )
    # Variant 3: 100.0% accuracy, slightly higher latency -> non-dominated
    v3 = CandidateVariant(
        id="C", name="Cand C", specialist_type="topology_tool", architecture=arch_dummy,
        scorecard=Scorecard(
            name="C", split="opt", total_cases=6, accurate_cases=6, reliable_cases=6,
            accuracy=1.0, reliability=1.0, cost_usd=0.001, latency_ms=35.0
        )
    )

    frontier = compute_pareto_frontier([v1, v2, v3])
    frontier_ids = {c.id for c in frontier}

    # V2 is strictly dominated by V1; V1 and V3 are non-dominated
    assert "B" not in frontier_ids
    assert "A" in frontier_ids
    assert "C" in frontier_ids

    # Automatic selection should pick V3 (maximizes accuracy at 1.0)
    winner = select_tournament_winner([v1, v2, v3])
    assert winner.id == "C"
    assert winner.scorecard.accuracy == 1.0


def test_tournament_winner_avoids_catastrophic_regressions():
    """Verify select_tournament_winner excludes candidates with catastrophic regressions (>5x latency/cost)."""
    arch_dummy = ArchitectureGenerator().generate(
        GoalAnalyzer().analyze("Reconcile transactions"),
        architecture_name="Dummy"
    )
    base_sc = Scorecard(
        name="Baseline", split="opt", total_cases=6, accurate_cases=5, reliable_cases=6,
        accuracy=0.833, reliability=1.0, cost_usd=0.001, latency_ms=30.0
    )

    # Candidate 1: 95% accuracy, reasonable latency (35ms)
    v1 = CandidateVariant(
        id="A", name="Cand A", specialist_type="prompt", architecture=arch_dummy,
        scorecard=Scorecard(
            name="A", split="opt", total_cases=6, accurate_cases=5, reliable_cases=6,
            accuracy=0.95, reliability=1.0, cost_usd=0.001, latency_ms=35.0
        )
    )
    # Candidate 2: 100% accuracy, but CATASTROPHIC latency (600ms = 20x baseline)
    v2 = CandidateVariant(
        id="B", name="Cand B", specialist_type="verifier", architecture=arch_dummy,
        scorecard=Scorecard(
            name="B", split="opt", total_cases=6, accurate_cases=6, reliable_cases=6,
            accuracy=1.0, reliability=1.0, cost_usd=0.001, latency_ms=600.0
        )
    )

    winner = select_tournament_winner([v1, v2], baseline_scorecard=base_sc)
    # V2 must be filtered out due to catastrophic latency explosion (>5x baseline)
    assert winner.id == "A"
    assert winner.scorecard.accuracy == 0.95


def test_candidate_variant_to_dict_frontend_compatibility():
    """Verify CandidateVariant.to_dict() matches the frontend UI Candidate data contract."""
    arch = ArchitectureGenerator().generate(
        GoalAnalyzer().analyze("Reconcile transactions"),
        architecture_name="Test"
    )
    cand = CandidateVariant(
        id="C",
        name="Candidate C (Topology & Tool Specialist)",
        specialist_type="topology_tool",
        tag="Gen 1 - Tool & Topology Specialist",
        generation=1,
        description="Tool mutation to smart_reconcile",
        architecture=arch,
        applied_mutators=["ToolAssignmentMutator"],
        targeted_node="tool_smart_reconcile",
        win_rate=100.0,
        status="pareto_dominant"
    )

    d = cand.to_dict()
    assert d["id"] == "C"
    assert d["name"] == "Candidate C (Topology & Tool Specialist)"
    assert d["tag"] == "Gen 1 - Tool & Topology Specialist"
    assert d["generation"] == 1
    assert d["mutator_applied"] == "ToolAssignmentMutator"
    assert d["targeted_node"] == "tool_smart_reconcile"
    assert d["win_rate"] == 100.0
    assert d["status"] == "pareto_dominant"
    assert "prompt_diff" in d
    assert "config_diff" in d
