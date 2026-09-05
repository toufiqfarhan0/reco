"""Comprehensive test suite for Closed-Loop Autonomous Optimization Controller."""

import pytest
from reco.benchmarks.base import BenchmarkSplit
from reco.benchmarks.reconciliation.dataset import get_reconciliation_benchmark_suite
from reco.core.goal_analyzer import GoalAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import NodeStatus
from reco.engine.runtime import AgentRuntime
from reco.evaluators.scorecard import ScorecardEvaluator
from reco.optimization.controller import (
    OptimizationController,
    OptimizationIteration,
    OptimizationResult,
)
from reco.tools.registry import ToolRegistry


def test_optimization_controller_full_cycle_on_reconciliation_benchmark():
    """Verify complete closed loop: Baseline V0 -> Benchmark -> Diagnostics -> Mutation -> Candidate V1.

    Demonstrates measurable empirical improvement from 83.3% (5/6) to 100.0% (6/6) on the optimization split.
    """
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()

    # Step 1: Synthesize Baseline V0 (contains exact_reconcile)
    spec = GoalAnalyzer().analyze("Reconcile financial transactions and identify discrepancies")
    generator = ArchitectureGenerator(tool_registry=registry)
    baseline_v0 = generator.generate(spec, architecture_name="Agent_Reconciliation_V0")

    controller = OptimizationController(tool_registry=registry)

    # Execute autonomous optimization cycle on optimization split
    result = controller.run_optimization_cycle(
        baseline_architecture=baseline_v0,
        suite=suite,
        split=BenchmarkSplit.OPTIMIZATION,
        max_iterations=1
    )

    assert isinstance(result, OptimizationResult)

    # 1. Verify Baseline Performance (5/6 passed, failed on format variations)
    assert result.baseline_scorecard.total_cases == 6
    assert result.baseline_scorecard.accurate_cases == 5
    assert pytest.approx(result.baseline_scorecard.accuracy, 0.001) == 0.8333
    assert result.baseline_scorecard.reliability == 1.0

    # 2. Verify Diagnosed Failure
    assert result.diagnostic_report.failed_cases == 1
    assert result.diagnostic_report.has_category("tool_selection_error")
    failed_diag = result.diagnostic_report.get_case_diagnostic("reco_opt_006_format_variations")
    assert failed_diag is not None
    assert "smart_reconcile" in failed_diag.remedy_suggestion.lower()

    # 3. Verify Candidate V1 Measurable Empirical Improvement
    assert result.candidate_scorecard.total_cases == 6
    assert result.candidate_scorecard.accurate_cases == 6
    assert result.candidate_scorecard.accuracy == 1.0
    assert result.candidate_scorecard.reliability == 1.0

    # 4. Metric Deltas & Pareto Dominance
    assert result.has_improved is True
    assert pytest.approx(result.accuracy_gain, 0.001) == 0.1667
    assert result.status == "OPTIMIZED"

    comparison = result.scorecard_comparison
    assert "+16.7%" in comparison.accuracy_badge
    assert comparison.verdict in ("PARETO_DOMINANT", "TRADEOFF")
    assert comparison.accuracy_delta > 0

    # 5. Candidate Structural Mutation Diff
    assert result.candidate_diff.has_changes() is True
    assert "tool_smart_reconcile" in result.candidate_diff.added_nodes
    assert "tool_exact_reconcile" in result.candidate_diff.removed_nodes

    # 6. Report Markdown Generation
    md = result.to_markdown()
    assert "# Autonomous Agent Optimization Report" in md
    assert "Agent_Reconciliation_V0" in md
    assert "tool_smart_reconcile" in md
    assert "+16.7%" in md


def test_optimization_controller_from_zero_tool_baseline():
    """Verify closed loop discovers and attaches reconciliation tools when baseline has none."""
    suite = get_reconciliation_benchmark_suite()

    # Create baseline with default analytical registry (no reconciliation tools)
    spec = GoalAnalyzer().analyze("Reconcile financial ledger transactions")
    zero_tool_baseline = ArchitectureGenerator(tool_registry=ToolRegistry.create_default()).generate(
        spec, architecture_name="Agent_Unprepared_V0"
    )

    # Controller configured with full reconciliation capabilities
    reco_registry = ToolRegistry.create_reconciliation_default()
    controller = OptimizationController(tool_registry=reco_registry)

    result = controller.run_optimization_cycle(
        baseline_architecture=zero_tool_baseline,
        suite=suite,
        split=BenchmarkSplit.OPTIMIZATION,
        max_iterations=1
    )

    # Baseline has 0% accuracy
    assert result.baseline_scorecard.accuracy == 0.0

    # Candidate attached smart_reconcile and reaches 100% accuracy
    assert result.candidate_scorecard.accuracy == 1.0
    assert result.has_improved is True
    assert result.accuracy_gain == 1.0
    assert result.status == "OPTIMIZED"


def test_optimization_controller_convergence_when_already_perfect():
    """Verify controller recognizes already-perfect architecture and returns CONVERGED."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()

    # Pre-configure perfect candidate with smart_reconcile
    spec = GoalAnalyzer().analyze("Reconcile transactions")
    generator = ArchitectureGenerator(tool_registry=registry)
    baseline = generator.generate(spec)

    # Mutate to smart_reconcile so it's already 100%
    from reco.mutation.mutators.tool_mutator import ToolAssignmentMutator
    perfect_arch = ToolAssignmentMutator(tool_registry=registry).mutate(
        baseline, target_tool="smart_reconcile", replace_tool="exact_reconcile"
    )
    perfect_arch.name = "Agent_Already_Perfect_V0"

    controller = OptimizationController(tool_registry=registry)
    result = controller.run_optimization_cycle(
        baseline_architecture=perfect_arch,
        suite=suite,
        split=BenchmarkSplit.OPTIMIZATION
    )

    assert result.status == "CONVERGED"
    assert result.accuracy_gain == 0.0
    assert result.baseline_scorecard.accuracy == 1.0
    assert result.candidate_scorecard.accuracy == 1.0


def test_optimization_iteration_telemetry_tracking():
    """Verify individual optimization iterations record step-by-step diagnostics and mutations."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()

    spec = GoalAnalyzer().analyze("Reconcile transactions")
    baseline = ArchitectureGenerator(tool_registry=registry).generate(spec, architecture_name="Agent_V0")

    controller = OptimizationController(tool_registry=registry)
    result = controller.run_optimization_cycle(
        baseline_architecture=baseline,
        suite=suite,
        split=BenchmarkSplit.OPTIMIZATION,
        max_iterations=1
    )

    assert len(result.iterations) == 1
    it = result.iterations[0]
    assert isinstance(it, OptimizationIteration)
    assert it.iteration == 0
    assert it.architecture_name == "Agent_V0"
    assert it.diagnostic_report is not None
    assert it.mutation_result is not None
    assert it.mutation_result.success is True


def test_mutated_candidate_preserves_reliability_across_splits():
    """Verify candidate architecture retains 100% reliability and valid graph execution."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()

    spec = GoalAnalyzer().analyze("Reconcile transactions")
    baseline = ArchitectureGenerator(tool_registry=registry).generate(spec)

    controller = OptimizationController(tool_registry=registry)
    result = controller.run_optimization_cycle(
        baseline_architecture=baseline,
        suite=suite,
        split=BenchmarkSplit.OPTIMIZATION
    )

    candidate = result.candidate_architecture

    # Execute directly with runtime on held-out split to verify generalizability and reliability
    runtime = AgentRuntime(tool_registry=registry)
    held_cases = suite.get_held_out_cases()

    for case in held_cases:
        exec_res = runtime.execute(candidate, case.input_data)
        assert exec_res.status == NodeStatus.COMPLETED
        assert exec_res.error is None
        assert exec_res.total_latency_ms > 0.0
