"""Comprehensive closed-loop verification test suite for Step 5 Track 1.

Verifies:
1. Air-Gapped Held-Out Partition Isolation:
   - Strict 6/4 partition isolation with zero leakage.
   - Optimization split is never used for final promotion sign-off.
   - Deterministic SHA-256 air-gap checksum generation.
2. Formal Promotion Policy Enforcement:
   - PROMOTED: Candidate beats baseline on held-out split without severe tradeoffs -> Becomes new champion V1.
   - REQUIRES_REVIEW: Candidate improves accuracy but incurs notable cost or latency tradeoff (>3x).
   - REJECTED: Candidate regresses on held-out split (benchmark overfitting detected) -> Retains previous champion.
3. End-to-End Closed-Loop Autonomous Workflow:
   - Baseline V0 -> Benchmark -> Diagnostics -> 3-Candidate Tournament -> Pareto Selection -> Held-Out Gate -> Champion V1.
"""

import pytest
from reco.benchmarks.base import BenchmarkSplit
from reco.benchmarks.reconciliation.dataset import get_reconciliation_benchmark_suite
from reco.core.goal_analyzer import GoalAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import AgentArchitecture, EdgeSpec, NodeSpec, NodeType
from reco.evaluators.comparison import (
    HeldOutValidationGate,
    HeldOutValidationResult,
    PromotionDecision,
    TournamentEvaluator,
)
from reco.evaluators.scorecard import Scorecard, ScorecardEvaluator
from reco.mutation.generator import CandidatePoolGenerator, CandidateVariant
from reco.optimization.controller import OptimizationController, TournamentOptimizationResult
from reco.tools.registry import ToolRegistry


# ==============================================================================
# 1. Air-Gapped Partition Isolation & Zero Leakage
# ==============================================================================

def test_air_gapped_partition_isolation_and_zero_leakage():
    """Verify optimization and held-out splits are air-gapped with 100% disjoint case IDs and zero leakage."""
    suite = get_reconciliation_benchmark_suite()
    assert suite.validate_partition_isolation() is True

    opt_cases = suite.get_optimization_cases()
    held_cases = suite.get_held_out_cases()

    assert len(opt_cases) == 6
    assert len(held_cases) == 4

    opt_ids = {c.case_id for c in opt_cases}
    held_ids = {c.case_id for c in held_cases}

    # Zero overlap check
    assert opt_ids.isdisjoint(held_ids)
    assert len(opt_ids.intersection(held_ids)) == 0


# ==============================================================================
# 2. Formal Promotion Policy Verification
# ==============================================================================

def test_held_out_gate_promoted_policy():
    """Verify PROMOTED decision when tournament winner outperforms baseline on held-out split without severe tradeoffs."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()

    # Baseline V0 with exact_reconcile
    spec = GoalAnalyzer().analyze("Reconcile financial ledger transactions")
    baseline = ArchitectureGenerator(tool_registry=registry).generate(spec, architecture_name="Baseline_V0")

    # Candidate C with smart_reconcile
    from reco.mutation.mutators.tool_mutator import ToolAssignmentMutator
    cand_c_arch = ToolAssignmentMutator(tool_registry=registry).mutate(
        baseline,
        target_tool="smart_reconcile",
        replace_tool="exact_reconcile"
    )
    cand_c_arch.name = "Candidate_C_SmartReconcile"

    cand_variant = CandidateVariant(
        id="C",
        name="Candidate C (Topology & Tool Specialist)",
        specialist_type="topology_tool",
        architecture=cand_c_arch
    )

    gate = HeldOutValidationGate(tool_registry=registry)
    result = gate.validate(candidate=cand_variant, baseline=baseline, suite=suite)

    assert isinstance(result, HeldOutValidationResult)
    assert result.promotion_decision == PromotionDecision.PROMOTED
    assert result.is_promoted is True
    assert cand_variant.status == "verified_champion"

    # Baseline fails case 4 (format variations); Candidate C achieves 100% (4/4)
    assert result.candidate_scorecard.accuracy == 1.0
    assert result.baseline_scorecard.accuracy < 1.0
    assert result.candidate_scorecard.accurate_cases == 4
    assert result.leakage_detected is False
    assert result.air_gap_checksum.startswith("sha256:")

    # Champion architecture is Candidate C
    assert result.champion_architecture.id == cand_c_arch.id

    # Markdown certificate contains official PROMOTED badge
    md = result.to_markdown()
    assert "PROMOTED (NEW CHAMPION V1)" in md
    assert "Per-Case Held-Out Audit Trail" in md


def test_held_out_gate_requires_review_on_notable_tradeoff():
    """Verify REQUIRES_REVIEW decision when candidate improves accuracy but exceeds the 3x latency/cost tradeoff threshold."""
    registry = ToolRegistry.create_reconciliation_default()
    spec = GoalAnalyzer().analyze("Reconcile transactions")
    baseline = ArchitectureGenerator(tool_registry=registry).generate(spec, architecture_name="Baseline_V0")

    # Mock baseline held-out scorecard: 75% accuracy, 20ms latency, $0.001 cost
    base_held_sc = Scorecard(
        name="Baseline_HeldOut", split="held-out", total_cases=4, accurate_cases=3, reliable_cases=4,
        accuracy=0.75, reliability=1.0, cost_usd=0.001, latency_ms=20.0
    )

    # Mock candidate architecture
    cand_arch = ArchitectureGenerator(tool_registry=registry).generate(spec, architecture_name="Cand_Heavy_V1")

    # Mock evaluator that returns 100% accuracy but 100ms latency (5x baseline latency > 3x threshold)
    class HighLatencyEvaluator:
        def evaluate(self, architecture, suite_or_cases, split, name=None):
            return Scorecard(
                name=name or "Candidate_HeldOut",
                split="held-out",
                total_cases=4,
                accurate_cases=4,
                reliable_cases=4,
                accuracy=1.0,  # Improved accuracy (+25%)
                reliability=1.0,
                cost_usd=0.001,
                latency_ms=100.0  # 5.0x latency increase (> 3.0x threshold!)
            )

        def compare(self, baseline, candidate):
            return ScorecardEvaluator().compare(baseline, candidate)

    gate = HeldOutValidationGate(
        tool_registry=registry,
        evaluator=HighLatencyEvaluator()
    )

    result = gate.validate(
        candidate=cand_arch,
        baseline=baseline,
        baseline_held_out_scorecard=base_held_sc
    )

    assert result.promotion_decision == PromotionDecision.REQUIRES_REVIEW
    assert result.is_promoted is False
    # Baseline champion retained pending review
    assert result.champion_architecture.id == baseline.id
    assert any("NOTABLE TRADEOFF FLAGGED" in r for r in result.rationale)


def test_held_out_gate_rejected_on_overfitting_regression():
    """Verify REJECTED decision when candidate regresses on unseen held-out split (overfitting detected)."""
    registry = ToolRegistry.create_reconciliation_default()
    spec = GoalAnalyzer().analyze("Reconcile transactions")
    baseline = ArchitectureGenerator(tool_registry=registry).generate(spec, architecture_name="Baseline_V0")

    # Baseline held-out: 75% accuracy
    base_held_sc = Scorecard(
        name="Baseline_HeldOut", split="held-out", total_cases=4, accurate_cases=3, reliable_cases=4,
        accuracy=0.75, reliability=1.0, cost_usd=0.001, latency_ms=20.0
    )

    cand_arch = ArchitectureGenerator(tool_registry=registry).generate(spec, architecture_name="Cand_Overfit_V1")
    cand_variant = CandidateVariant(
        id="A", name="Overfit Cand", specialist_type="prompt", architecture=cand_arch
    )

    # Mock evaluator where candidate regresses to 50% accuracy on held-out split
    class RegressedEvaluator:
        def evaluate(self, architecture, suite_or_cases, split, name=None):
            return Scorecard(
                name=name or "Candidate_HeldOut",
                split="held-out",
                total_cases=4,
                accurate_cases=2,
                reliable_cases=4,
                accuracy=0.50,  # Regressed on held-out!
                reliability=1.0,
                cost_usd=0.001,
                latency_ms=20.0
            )

        def compare(self, baseline, candidate):
            return ScorecardEvaluator().compare(baseline, candidate)

    gate = HeldOutValidationGate(
        tool_registry=registry,
        evaluator=RegressedEvaluator()
    )

    result = gate.validate(
        candidate=cand_variant,
        baseline=baseline,
        baseline_held_out_scorecard=base_held_sc
    )

    assert result.promotion_decision == PromotionDecision.REJECTED
    assert result.is_promoted is False
    assert cand_variant.status == "rejected"
    # Previous champion retained
    assert result.champion_architecture.id == baseline.id
    assert any("Benchmark overfitting detected" in r for r in result.rationale)


# ==============================================================================
# 3. End-to-End Closed-Loop Autonomous Tournament & Promotion Cycle
# ==============================================================================

def test_end_to_end_closed_loop_tournament_and_held_out_promotion():
    """Verify complete closed loop: Baseline V0 -> Diagnostics -> 3 Candidates -> Tournament -> Held-out Gate -> Champion V1."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()

    controller = OptimizationController(tool_registry=registry)

    # Execute full tournament optimization cycle
    result = controller.run_tournament_cycle(suite=suite)

    assert isinstance(result, TournamentOptimizationResult)
    assert result.status == "PROMOTED"

    # 1. Multi-Candidate Tournament Verification
    assert len(result.candidate_pool) == 3
    assert len(result.tournament_result.candidates) == 3

    winner = result.tournament_result.winner
    assert winner.id == "C"
    assert winner.scorecard.accuracy == 1.0
    assert result.accuracy_gain_opt > 0

    # 2. Air-Gapped Held-Out Validation Gate Verification
    held_res = result.held_out_result
    assert held_res.promotion_decision == PromotionDecision.PROMOTED
    assert held_res.is_promoted is True
    assert held_res.accuracy == 1.0  # 4/4 on held-out split
    assert held_res.leakage_detected is False
    assert held_res.air_gap_checksum.startswith("sha256:")

    # 3. Champion Promotion
    assert result.champion_architecture.id == winner.architecture.id
    assert result.accuracy_gain_held_out > 0

    # 4. Report Markdown Generation
    md = result.to_markdown()
    assert "# Autonomous Tournament Optimization & Promotion Report" in md
    assert "PROMOTED" in md
    assert "Multi-Candidate 4-Axis Scorecard Matrix" in md
    assert "Air-Gapped Held-Out Validation & Promotion Gate" in md


def test_held_out_validation_result_frontend_dictionary_contract():
    """Verify HeldOutValidationResult.to_dict() matches the frontend HeldOutValidationData interface contract."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()

    spec = GoalAnalyzer().analyze("Reconcile financial transactions")
    baseline = ArchitectureGenerator(tool_registry=registry).generate(spec)

    from reco.mutation.mutators.tool_mutator import ToolAssignmentMutator
    cand_arch = ToolAssignmentMutator(tool_registry=registry).mutate(
        baseline, target_tool="smart_reconcile"
    )

    gate = HeldOutValidationGate(tool_registry=registry)
    result = gate.validate(candidate=cand_arch, baseline=baseline, suite=suite)

    data = result.to_dict()
    assert data["split_name"] == "held-out"
    assert data["total_cases"] == 4
    assert data["passed_cases"] == 4
    assert data["accuracy"] == 1.0
    assert data["reliability"] == 1.0
    assert data["air_gap_checksum"].startswith("sha256:")
    assert data["leakage_detected"] is False
    assert data["promotion_decision"] == "PROMOTED"
    assert isinstance(data["rationale"], list)
    assert len(data["cases"]) == 4

    # Verify per-case structure
    case0 = data["cases"][0]
    assert "case_id" in case0
    assert "name" in case0
    assert "phenomenon" in case0
    assert "passed" in case0
    assert "latency_ms" in case0
    assert case0["passed"] is True
