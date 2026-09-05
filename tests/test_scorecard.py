"""Comprehensive test suite for 4-Axis Scorecard Engine, Pareto Dominance, and Baseline V0."""

import pytest
from reco.benchmarks.base import BenchmarkCase, BenchmarkSplit, BenchmarkSuite
from reco.benchmarks.reconciliation.dataset import get_reconciliation_benchmark_suite
from reco.core.goal_analyzer import GoalAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import NodeStatus, NodeType
from reco.engine.runtime import AgentRuntime
from reco.evaluators.scorecard import (
    CaseEvaluationResult,
    Scorecard,
    ScorecardComparison,
    ScorecardEvaluator,
    run_v0_benchmark,
)
from reco.tools.registry import ToolDefinition, ToolRegistry


def test_scorecard_initialization_and_4_canonical_axes():
    """Verify Scorecard fields and formatting for Accuracy, Reliability, Cost, and Speed."""
    scorecard = Scorecard(
        name="TestAgent_V1",
        split="optimization",
        total_cases=6,
        accurate_cases=5,
        reliable_cases=6,
        accuracy=5 / 6,
        reliability=1.0,
        cost_usd=0.0015,
        latency_ms=125.40,
        avg_latency_ms=20.90,
        latency_s=0.1254,
        case_results=[]
    )

    # 1. Accuracy axis
    assert pytest.approx(scorecard.accuracy, 0.001) == 0.8333
    # 2. Reliability axis
    assert scorecard.reliability == 1.0
    # 3. Cost axis
    assert scorecard.cost_usd == 0.0015
    # 4. Speed / Latency axis
    assert scorecard.latency_ms == 125.40
    assert scorecard.latency_s == 0.1254
    assert scorecard.avg_latency_ms == 20.90

    # Test summary dictionary export
    summary = scorecard.summary_dict()
    assert summary["accuracy"] == 0.8333
    assert summary["reliability"] == 1.0
    assert summary["cost_usd"] == 0.0015
    assert summary["latency_ms"] == 125.40

    # Test markdown report rendering
    md = scorecard.to_markdown()
    assert "### 4-Axis Scorecard: TestAgent_V1" in md
    assert "1. Accuracy" in md
    assert "2. Reliability" in md
    assert "3. Cost" in md
    assert "4. Speed" in md
    assert "83.3%" in md
    assert "100.0%" in md
    assert "$0.0015" in md


def test_scorecard_evaluator_on_optimization_split():
    """Verify ScorecardEvaluator executes all optimization split cases and collects telemetry."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()
    analyzer = GoalAnalyzer()
    spec = analyzer.analyze("Reconcile transactions and identify discrepancies")

    generator = ArchitectureGenerator(tool_registry=registry)
    arch = generator.generate(spec)

    runtime = AgentRuntime(tool_registry=registry)
    evaluator = ScorecardEvaluator(runtime=runtime)

    scorecard = evaluator.evaluate(
        architecture=arch,
        suite_or_cases=suite,
        split=BenchmarkSplit.OPTIMIZATION,
        name="Eval_Optimization_Run"
    )

    # Exactly 6 cases in optimization split
    assert scorecard.total_cases == 6
    assert scorecard.split == "optimization"
    assert len(scorecard.case_results) == 6

    # 4 Axes verification
    assert 0.0 <= scorecard.accuracy <= 1.0
    assert scorecard.reliability == 1.0  # Clean execution
    assert scorecard.cost_usd == 0.0    # Deterministic tool cost
    assert scorecard.latency_ms > 0.0   # Wall-clock time recorded

    # Verify per-case breakdown
    for cr in scorecard.case_results:
        assert isinstance(cr, CaseEvaluationResult)
        assert cr.split == "optimization"
        assert cr.is_reliable is True
        assert cr.latency_ms > 0.0
        assert cr.actual_output is not None


def test_scorecard_evaluator_reliability_accounting_on_failure():
    """Verify ScorecardEvaluator reflects runtime failures in Reliability metric."""
    suite = get_reconciliation_benchmark_suite()

    # Create a tool registry with a tool that fails on one case
    registry = ToolRegistry.create_default()

    def buggy_handler(source_records, target_records):
        if len(source_records) == 5 and len(target_records) == 5:
            raise RuntimeError("Injected database connection timeout during reconciliation")
        return {"matched_ids": []}

    registry.register(ToolDefinition(
        name="buggy_reconcile",
        description="Fails conditionally",
        parameters={
            "type": "object",
            "properties": {
                "source_records": {"type": "array"},
                "target_records": {"type": "array"}
            },
            "required": ["source_records", "target_records"]
        },
        capabilities=["reconciliation"],
        handler=buggy_handler
    ))

    analyzer = GoalAnalyzer()
    spec = analyzer.analyze("Reconcile financial transactions")
    generator = ArchitectureGenerator(tool_registry=registry)
    arch = generator.generate(spec)

    runtime = AgentRuntime(tool_registry=registry)
    evaluator = ScorecardEvaluator(runtime=runtime)

    scorecard = evaluator.evaluate(
        architecture=arch,
        suite_or_cases=suite,
        split=BenchmarkSplit.OPTIMIZATION
    )

    # Reliability must be strictly less than 1.0 due to injected failure
    assert scorecard.reliability < 1.0
    assert scorecard.reliable_cases < scorecard.total_cases
    failed_cases = [r for r in scorecard.case_results if not r.is_reliable]
    assert len(failed_cases) >= 1
    assert failed_cases[0].error is not None
    assert "Injected database connection timeout" in failed_cases[0].error


def test_scorecard_comparison_delta_badges():
    """Verify side-by-side ScorecardComparison calculates delta badges across all 4 axes."""
    baseline = Scorecard(
        name="Baseline_V0",
        split="optimization",
        total_cases=6,
        accurate_cases=1,
        reliable_cases=6,
        accuracy=0.1667,
        reliability=1.0,
        cost_usd=0.0050,
        latency_ms=100.0,
        avg_latency_ms=16.67,
        latency_s=0.100,
        case_results=[]
    )

    candidate = Scorecard(
        name="Candidate_V1",
        split="optimization",
        total_cases=6,
        accurate_cases=5,
        reliable_cases=6,
        accuracy=0.8333,
        reliability=1.0,
        cost_usd=0.0040,
        latency_ms=85.0,
        avg_latency_ms=14.17,
        latency_s=0.085,
        case_results=[]
    )

    evaluator = ScorecardEvaluator()
    comparison = evaluator.compare(baseline=baseline, candidate=candidate)

    # 1. Delta calculations
    assert pytest.approx(comparison.accuracy_delta, 0.001) == 0.6666
    assert comparison.reliability_delta == 0.0
    assert pytest.approx(comparison.cost_delta_usd, 0.0001) == -0.0010
    assert pytest.approx(comparison.latency_delta_ms, 0.01) == -15.00
    assert pytest.approx(comparison.latency_pct_delta, 0.1) == -15.0

    # 2. Delta badges
    assert "+66.7%" in comparison.accuracy_badge
    assert "+0.0%" in comparison.reliability_badge
    assert "-$0.0010" in comparison.cost_badge
    assert "-15.00ms (-15.0%)" in comparison.latency_badge

    # 3. Markdown comparison report
    md = comparison.to_markdown()
    assert "Scorecard Comparison: Candidate_V1 vs Baseline_V0" in md
    assert "PARETO_DOMINANT" in md
    assert "`+66.7%`" in md
    assert "`-$0.0010`" in md
    assert "`-15.00ms (-15.0%)`" in md


def test_pareto_dominance_detection():
    """Verify Pareto dominance is detected when candidate strictly improves without any regression."""
    baseline = Scorecard(
        name="Baseline",
        split="optimization",
        total_cases=6,
        accurate_cases=3,
        reliable_cases=6,
        accuracy=0.50,
        reliability=1.0,
        cost_usd=0.010,
        latency_ms=100.0,
        avg_latency_ms=16.67,
        latency_s=0.10,
        case_results=[]
    )

    # Strictly improved on Accuracy & Speed, equal on Reliability & Cost
    dominant_candidate = Scorecard(
        name="DominantCandidate",
        split="optimization",
        total_cases=6,
        accurate_cases=5,
        reliable_cases=6,
        accuracy=0.8333,
        reliability=1.0,
        cost_usd=0.010,
        latency_ms=80.0,
        avg_latency_ms=13.33,
        latency_s=0.08,
        case_results=[]
    )

    evaluator = ScorecardEvaluator()
    comp = evaluator.compare(baseline=baseline, candidate=dominant_candidate)

    assert comp.is_pareto_dominant is True
    assert comp.has_tradeoff is False
    assert comp.verdict == "PARETO_DOMINANT"

    # Neutral candidate (identical performance)
    neutral_candidate = Scorecard(
        name="NeutralCandidate",
        split="optimization",
        total_cases=6,
        accurate_cases=3,
        reliable_cases=6,
        accuracy=0.50,
        reliability=1.0,
        cost_usd=0.010,
        latency_ms=100.0,
        avg_latency_ms=16.67,
        latency_s=0.10,
        case_results=[]
    )
    comp_neutral = evaluator.compare(baseline=baseline, candidate=neutral_candidate)
    assert comp_neutral.is_pareto_dominant is False
    assert comp_neutral.has_tradeoff is False
    assert comp_neutral.verdict == "NEUTRAL"


def test_tradeoff_flagging():
    """Verify tradeoffs are detected when candidate improves one axis but regresses on another."""
    baseline = Scorecard(
        name="Baseline",
        split="optimization",
        total_cases=6,
        accurate_cases=3,
        reliable_cases=6,
        accuracy=0.50,
        reliability=1.0,
        cost_usd=0.005,
        latency_ms=100.0,
        avg_latency_ms=16.67,
        latency_s=0.10,
        case_results=[]
    )

    # Accuracy improved (+20%), but latency increased (+25.0ms / +25%)
    tradeoff_candidate = Scorecard(
        name="TradeoffCandidate",
        split="optimization",
        total_cases=6,
        accurate_cases=5,
        reliable_cases=6,
        accuracy=0.70,  # +20% accuracy
        reliability=1.0,
        cost_usd=0.005,
        latency_ms=125.0,  # +25% latency regression
        avg_latency_ms=20.83,
        latency_s=0.125,
        case_results=[]
    )

    evaluator = ScorecardEvaluator()
    comp = evaluator.compare(baseline=baseline, candidate=tradeoff_candidate)

    assert comp.is_pareto_dominant is False
    assert comp.has_tradeoff is True
    assert comp.verdict == "TRADEOFF"
    assert len(comp.tradeoffs) >= 1
    assert "accuracy" in comp.tradeoffs[0].lower()
    assert "latency" in comp.tradeoffs[0].lower()


def test_baseline_v0_benchmark_execution():
    """Run V0 baseline DAG through the optimization benchmark split and verify scorecard output."""
    v0_scorecard = run_v0_benchmark(split=BenchmarkSplit.OPTIMIZATION)

    assert isinstance(v0_scorecard, Scorecard)
    assert v0_scorecard.split == "optimization"
    assert v0_scorecard.total_cases == 6
    assert len(v0_scorecard.case_results) == 6

    # Verify execution was reliable (no crash in V0 graph)
    assert v0_scorecard.reliability == 1.0
    assert v0_scorecard.latency_ms > 0.0
    assert v0_scorecard.cost_usd == 0.0

    # Check that markdown table renders valid baseline documentation
    md = v0_scorecard.to_markdown()
    assert "V0_Baseline_Reconciliation" in md
    assert "OPTIMIZATION" in md
    assert "Ground-Truth Match Rate" in md
    assert "Error-Free Execution Rate" in md
