"""Deterministic test suite for Milestone 8: Generic Multi-Dimensional Evaluator & Scorecard.

Covers:
- Scorecard domain models & range validation
- Raw vs normalized metrics
- Multi-dimensional comparisons (Accuracy, Reliability, Cost, Latency)
- Dominance rules (strictly_better, strictly_worse, tradeoff, equivalent)
- Deterministic human-readable improvement summary
- Promotion assessment & policy configurations
- Optimization and Held-out split awareness
- Cross-domain compatibility (generic research benchmark mock)
- Reconciliation benchmark integration (V0 baseline scorecard)
- Persistence roundtrip with BenchmarkRunRecord
- FastAPI /scorecard/compare endpoint
"""

import asyncio
from uuid import uuid4
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from reco.api.app import app
from reco.benchmarks.reconciliation import (
    ReconciliationBenchmark,
    create_reconciliation_baseline_graph,
)
from reco.core.interfaces import BenchmarkRunResult
from reco.db.models import BenchmarkRunRecord
from reco.evaluators import (
    ComparisonPolicy,
    DimensionDelta,
    NormalizedMetrics,
    PromotionAssessment,
    Scorecard,
    ScorecardComparison,
    assess_promotion,
    compare_scorecards,
    format_improvement_summary,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def baseline_scorecard() -> Scorecard:
    """Standard baseline scorecard (V0)."""
    return Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        agent_version_id=uuid4(),
        experiment_id=uuid4(),
        split="optimization",
        accuracy=0.7500,
        reliability=1.0000,
        total_cost_usd=0.006900,
        avg_cost_usd=0.000575,
        cost_type="simulated_mock",
        total_latency_ms=1200,
        avg_latency_ms=100,
        p50_latency_ms=95,
        p95_latency_ms=130,
        total_cases=12,
        passed_cases=8,
        failed_cases=4,
        execution_metadata={"generation_method": "manual_baseline"},
    )


# ---------------------------------------------------------------------------
# PART 1: MODELS (1 - 3)
# ---------------------------------------------------------------------------

def test_1_scorecard_validation(baseline_scorecard: Scorecard):
    """Test 1: Valid scorecard instantiates and validates all field constraints."""
    assert baseline_scorecard.benchmark_name == "reconciliation"
    assert baseline_scorecard.accuracy == 0.7500
    assert baseline_scorecard.reliability == 1.0000
    assert baseline_scorecard.total_cases == 12
    assert baseline_scorecard.passed_cases == 8
    assert baseline_scorecard.failed_cases == 4


def test_2_invalid_metric_ranges_rejected():
    """Test 2: Invalid metric values (e.g. accuracy > 1.0 or negative costs) are rejected."""
    # Accuracy > 1.0
    with pytest.raises(ValidationError):
        Scorecard(
            benchmark_name="test",
            benchmark_version="v1",
            split="optimization",
            accuracy=1.25,  # Invalid
            reliability=1.0,
            total_cases=10,
            passed_cases=10,
            failed_cases=0,
        )

    # Reliability < 0.0
    with pytest.raises(ValidationError):
        Scorecard(
            benchmark_name="test",
            benchmark_version="v1",
            split="optimization",
            accuracy=0.8,
            reliability=-0.1,  # Invalid
            total_cases=10,
            passed_cases=10,
            failed_cases=0,
        )

    # Negative latency
    with pytest.raises(ValidationError):
        Scorecard(
            benchmark_name="test",
            benchmark_version="v1",
            split="optimization",
            accuracy=0.8,
            reliability=1.0,
            total_latency_ms=-50,  # Invalid
            total_cases=10,
            passed_cases=10,
            failed_cases=0,
        )

    # passed_cases > total_cases
    with pytest.raises(ValueError, match="passed_cases .* cannot exceed total_cases"):
        Scorecard(
            benchmark_name="test",
            benchmark_version="v1",
            split="optimization",
            accuracy=0.8,
            reliability=1.0,
            total_cases=10,
            passed_cases=15,  # Invalid
            failed_cases=0,
        )


def test_3_raw_vs_normalized_preservation(baseline_scorecard: Scorecard):
    """Test 3: Normalized metrics are computed without losing or modifying raw units."""
    norm = baseline_scorecard.compute_normalized(cost_max_ref=0.002, latency_max_ref=200)

    # Normalized scores exist
    assert isinstance(norm, NormalizedMetrics)
    assert 0.0 <= norm.accuracy_norm <= 1.0
    assert 0.0 <= norm.reliability_norm <= 1.0
    assert 0.0 <= norm.cost_norm <= 1.0
    assert 0.0 <= norm.speed_norm <= 1.0

    # Raw metrics remain unchanged with exact units
    assert baseline_scorecard.accuracy == 0.7500
    assert baseline_scorecard.total_cost_usd == 0.006900
    assert baseline_scorecard.avg_latency_ms == 100


# ---------------------------------------------------------------------------
# PART 2: METRICS REPRESENTATION (4 - 7)
# ---------------------------------------------------------------------------

def test_4_accuracy_representation(baseline_scorecard: Scorecard):
    """Test 4: Accuracy represents the evaluator-supplied domain score."""
    assert baseline_scorecard.accuracy == 0.7500
    assert isinstance(baseline_scorecard.accuracy, float)


def test_5_reliability_calculation(baseline_scorecard: Scorecard):
    """Test 5: Reliability represents crash-free completion rate separate from accuracy."""
    assert baseline_scorecard.reliability == 1.0000
    assert baseline_scorecard.passed_cases == 8
    assert baseline_scorecard.total_cases == 12
    # Even though only 8/12 cases passed accuracy threshold, 12/12 completed without crash (reliability = 1.0)


def test_6_cost_representation(baseline_scorecard: Scorecard):
    """Test 6: Cost captures both total and average in USD, and labels mock vs actual."""
    assert baseline_scorecard.total_cost_usd == 0.006900
    assert baseline_scorecard.avg_cost_usd == 0.000575
    assert baseline_scorecard.cost_type == "simulated_mock"


def test_7_latency_representation(baseline_scorecard: Scorecard):
    """Test 7: Latency represents duration in milliseconds and preserves percentiles."""
    assert baseline_scorecard.total_latency_ms == 1200
    assert baseline_scorecard.avg_latency_ms == 100
    assert baseline_scorecard.p50_latency_ms == 95
    assert baseline_scorecard.p95_latency_ms == 130


# ---------------------------------------------------------------------------
# PART 3: COMPARISON & DELTAS (8 - 15)
# ---------------------------------------------------------------------------

def test_8_improved_accuracy(baseline_scorecard: Scorecard):
    """Test 8: Detects improved accuracy (higher is better)."""
    candidate = baseline_scorecard.model_copy(deep=True)
    candidate.accuracy = 0.8500

    cmp = compare_scorecards(baseline_scorecard, candidate)
    assert cmp.accuracy_delta == pytest.approx(0.1000)
    assert "accuracy" in cmp.improved_dimensions
    assert cmp.relationship == "strictly_better"


def test_9_improved_reliability(baseline_scorecard: Scorecard):
    """Test 9: Detects improved reliability (higher is better)."""
    base = baseline_scorecard.model_copy(deep=True)
    base.reliability = 0.8000
    candidate = baseline_scorecard.model_copy(deep=True)
    candidate.reliability = 1.0000

    cmp = compare_scorecards(base, candidate)
    assert cmp.reliability_delta == pytest.approx(0.2000)
    assert "reliability" in cmp.improved_dimensions
    assert cmp.relationship == "strictly_better"


def test_10_reduced_cost(baseline_scorecard: Scorecard):
    """Test 10: Detects reduced cost (lower is better)."""
    candidate = baseline_scorecard.model_copy(deep=True)
    candidate.avg_cost_usd = 0.000400
    candidate.total_cost_usd = 0.004800

    cmp = compare_scorecards(baseline_scorecard, candidate)
    assert cmp.cost_delta < 0  # Negative delta = lower cost
    assert "cost" in cmp.improved_dimensions
    assert cmp.relationship == "strictly_better"


def test_11_reduced_latency(baseline_scorecard: Scorecard):
    """Test 11: Detects reduced latency / improved speed (lower is better)."""
    candidate = baseline_scorecard.model_copy(deep=True)
    candidate.avg_latency_ms = 75
    candidate.total_latency_ms = 900

    cmp = compare_scorecards(baseline_scorecard, candidate)
    assert cmp.latency_delta < 0  # Negative delta = faster
    assert "speed" in cmp.improved_dimensions
    assert cmp.relationship == "strictly_better"


def test_12_mixed_tradeoff(baseline_scorecard: Scorecard):
    """Test 12: Detects Pareto tradeoff (accuracy improved but cost increased)."""
    candidate = baseline_scorecard.model_copy(deep=True)
    candidate.accuracy = 0.9000  # Improved
    candidate.avg_cost_usd = 0.000800  # Regressed (higher cost)

    cmp = compare_scorecards(baseline_scorecard, candidate)
    assert "accuracy" in cmp.improved_dimensions
    assert "cost" in cmp.regressed_dimensions
    assert cmp.relationship == "tradeoff"


def test_13_regression(baseline_scorecard: Scorecard):
    """Test 13: Detects strictly worse candidate (accuracy dropped, cost increased)."""
    candidate = baseline_scorecard.model_copy(deep=True)
    candidate.accuracy = 0.6000  # Regressed
    candidate.avg_cost_usd = 0.000800  # Regressed

    cmp = compare_scorecards(baseline_scorecard, candidate)
    assert cmp.relationship == "strictly_worse"
    assert len(cmp.regressed_dimensions) >= 2


def test_14_equivalent_versions(baseline_scorecard: Scorecard):
    """Test 14: Detects equivalent scorecards with zero delta or within noise epsilon."""
    candidate = baseline_scorecard.model_copy(deep=True)
    cmp = compare_scorecards(baseline_scorecard, candidate)
    assert cmp.relationship == "equivalent"
    assert len(cmp.improved_dimensions) == 0
    assert len(cmp.regressed_dimensions) == 0


def test_15_delta_calculations(baseline_scorecard: Scorecard):
    """Test 15: Exact delta and relative percentage computations."""
    candidate = baseline_scorecard.model_copy(deep=True)
    candidate.accuracy = 0.8250
    candidate.avg_latency_ms = 80

    cmp = compare_scorecards(baseline_scorecard, candidate)
    assert cmp.accuracy_delta == pytest.approx(0.0750, abs=1e-4)
    assert cmp.relative_changes["accuracy_pct"] == pytest.approx(10.0, abs=0.1)
    assert cmp.latency_delta == -20
    assert cmp.relative_changes["speed_pct"] == pytest.approx(-20.0, abs=0.1)


# ---------------------------------------------------------------------------
# PART 4: HUMAN-READABLE SUMMARY (16 - 17)
# ---------------------------------------------------------------------------

def test_16_deterministic_summary(baseline_scorecard: Scorecard):
    """Test 16: Summary is generated deterministically without LLM intervention."""
    candidate = baseline_scorecard.model_copy(deep=True)
    candidate.accuracy = 0.8740
    candidate.avg_cost_usd = 0.000397
    candidate.avg_latency_ms = 78

    cmp = compare_scorecards(baseline_scorecard, candidate)
    summary = format_improvement_summary(cmp)

    assert "Accuracy improved by +12.4 percentage points" in summary
    assert "average cost decreased by 31.0%" in summary
    assert "average latency decreased by 22.0%" in summary


def test_17_percentage_point_direction_correctness(baseline_scorecard: Scorecard):
    """Test 17: Accuracy/reliability use percentage points ('pp'), cost/latency use relative %."""
    candidate = baseline_scorecard.model_copy(deep=True)
    candidate.accuracy = 0.7000  # Regressed by 5 pp
    candidate.avg_latency_ms = 120  # Regressed by 20%

    cmp = compare_scorecards(baseline_scorecard, candidate)
    summary = format_improvement_summary(cmp)

    assert "Accuracy regressed by -5.0 percentage points" in summary
    assert "average latency increased by 20.0%" in summary


# ---------------------------------------------------------------------------
# PART 5: PROMOTION ASSESSMENT (18 - 21)
# ---------------------------------------------------------------------------

def test_18_promote_assessment_on_held_out(baseline_scorecard: Scorecard):
    """Test 18: Strictly better candidate on held-out split receives 'promote' decision."""
    base = baseline_scorecard.model_copy(deep=True)
    base.split = "held_out"
    cand = baseline_scorecard.model_copy(deep=True)
    cand.split = "held_out"
    cand.accuracy = 0.8750
    cand.avg_latency_ms = 85

    assessment = assess_promotion(base, cand)
    assert assessment.decision == "promote"
    assert assessment.held_out_required is False
    assert len(assessment.reasons) > 0
    assert "strict multi-dimensional dominance" in assessment.reasons[0]


def test_19_reject_assessment_on_regression(baseline_scorecard: Scorecard):
    """Test 19: Regressed candidate receives 'reject' decision."""
    cand = baseline_scorecard.model_copy(deep=True)
    cand.accuracy = 0.6000
    cand.reliability = 0.8000

    assessment = assess_promotion(baseline_scorecard, cand)
    assert assessment.decision == "reject"
    assert "Reliability regressed" in assessment.reasons[0]


def test_20_review_tradeoff_assessment(baseline_scorecard: Scorecard):
    """Test 20: Candidate with mixed tradeoffs receives 'review' decision under strict policy."""
    base = baseline_scorecard.model_copy(deep=True)
    base.split = "held_out"
    cand = baseline_scorecard.model_copy(deep=True)
    cand.split = "held_out"
    cand.accuracy = 0.9000  # Better
    cand.avg_cost_usd = 0.000900  # Worse cost (+56%)

    strict_policy = ComparisonPolicy(allow_tradeoffs=False)
    assessment = assess_promotion(base, cand, policy=strict_policy)
    assert assessment.decision == "review"
    assert "Tradeoff" in assessment.reasons[0]


def test_21_permissive_tradeoff_policy(baseline_scorecard: Scorecard):
    """Test 21: Configurable policy allows acceptable tradeoffs to be promoted."""
    base = baseline_scorecard.model_copy(deep=True)
    base.split = "held_out"
    cand = baseline_scorecard.model_copy(deep=True)
    cand.split = "held_out"
    cand.accuracy = 0.9000  # Better (+15%)
    cand.avg_cost_usd = 0.000600  # Slightly worse cost (+4.3%)

    # Policy allows up to 10% cost increase if accuracy gains >= 0.05
    permissive_policy = ComparisonPolicy(
        allow_tradeoffs=True,
        min_accuracy_gain=0.05,
        max_acceptable_cost_increase_pct=10.0,
    )
    assessment = assess_promotion(base, cand, policy=permissive_policy)
    assert assessment.decision == "promote"
    assert "acceptable tradeoff policy" in assessment.reasons[0]


# ---------------------------------------------------------------------------
# PART 6: SPLIT AWARENESS (22 - 23)
# ---------------------------------------------------------------------------

def test_22_optimization_split_requires_held_out(baseline_scorecard: Scorecard):
    """Test 22: Strictly better candidate on optimization split returns review and flags held_out_required."""
    cand = baseline_scorecard.model_copy(deep=True)
    cand.accuracy = 0.9000
    cand.split = "optimization"

    assessment = assess_promotion(baseline_scorecard, cand)
    assert assessment.held_out_required is True
    assert assessment.decision == "review"
    assert "held-out evaluation is required" in assessment.reasons[0].lower()


def test_23_held_out_split_preserved():
    """Test 23: Held-out split is explicitly tagged and does not require another held-out run."""
    card = Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        split="held_out",
        accuracy=0.85,
        reliability=1.0,
        total_cases=8,
        passed_cases=7,
        failed_cases=1,
    )
    assert card.split == "held_out"


# ---------------------------------------------------------------------------
# PART 7: CROSS-DOMAIN COMPATIBILITY (24 - 25)
# ---------------------------------------------------------------------------

def test_24_generic_research_mock_benchmark():
    """Test 24: Scorecard and comparison operate seamlessly on a non-finance research benchmark."""
    res_base = Scorecard(
        benchmark_name="academic_research_eval",
        benchmark_version="research-v1",
        split="optimization",
        accuracy=0.6800,
        reliability=0.9000,
        total_cost_usd=0.015000,
        avg_cost_usd=0.001500,
        cost_type="actual",
        total_latency_ms=5000,
        avg_latency_ms=500,
        total_cases=10,
        passed_cases=7,
        failed_cases=3,
        execution_metadata={"topic": "quantum_computing"},
    )
    res_cand = res_base.model_copy(deep=True)
    res_cand.accuracy = 0.8200
    res_cand.reliability = 1.0000
    res_cand.avg_cost_usd = 0.001200
    res_cand.avg_latency_ms = 450

    cmp = compare_scorecards(res_base, res_cand)
    assert cmp.benchmark_name == "academic_research_eval"
    assert cmp.relationship == "strictly_better"
    assert cmp.improved_dimensions == ["accuracy", "reliability", "cost", "speed"]


def test_25_scorecard_independent_of_finance():
    """Test 25: Generic scorecard models contain zero financial field couplings."""
    # Ensure Scorecard model schema has no bank or ledger specific fields
    fields = set(Scorecard.model_fields.keys())
    finance_terms = {"bank", "ledger", "transaction", "entry", "reconciliation"}
    assert not any(any(term in f for term in finance_terms) for f in fields)


# ---------------------------------------------------------------------------
# PART 8: RECONCILIATION INTEGRATION (26 - 30)
# ---------------------------------------------------------------------------

def test_26_reconciliation_run_to_scorecard():
    """Test 26: Conversion from ReconciliationRunResult to generic Scorecard."""
    benchmark = ReconciliationBenchmark()
    graph = create_reconciliation_baseline_graph()
    run_result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))

    # Convert using to_scorecard method
    scorecard = run_result.to_scorecard()

    assert isinstance(scorecard, Scorecard)
    assert scorecard.benchmark_name == "reconciliation"
    assert scorecard.benchmark_version == "reconciliation-v1"
    assert scorecard.split == "optimization"
    assert scorecard.total_cases == 12
    assert scorecard.cost_type == "simulated_mock"


def test_27_v0_scorecard_accuracy():
    """Test 27: Validate V0 baseline scorecard accuracy on reconciliation benchmark."""
    benchmark = ReconciliationBenchmark()
    graph = create_reconciliation_baseline_graph()
    run_result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))
    card = run_result.to_scorecard()
    assert card.accuracy == pytest.approx(0.7500, abs=1e-3)


def test_28_v0_scorecard_reliability():
    """Test 28: Validate V0 baseline scorecard reliability (all 12 executed without crash)."""
    benchmark = ReconciliationBenchmark()
    graph = create_reconciliation_baseline_graph()
    run_result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))
    card = run_result.to_scorecard()
    assert card.reliability == 1.0000


def test_29_v0_scorecard_cost():
    """Test 29: Validate V0 baseline scorecard cost tracking."""
    benchmark = ReconciliationBenchmark()
    graph = create_reconciliation_baseline_graph()
    run_result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))
    card = run_result.to_scorecard()
    assert card.total_cost_usd >= 0.0
    assert card.avg_cost_usd >= 0.0
    assert card.cost_type == "simulated_mock"


def test_30_v0_scorecard_latency():
    """Test 30: Validate V0 baseline scorecard latency measurements."""
    benchmark = ReconciliationBenchmark()
    graph = create_reconciliation_baseline_graph()
    run_result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))
    card = run_result.to_scorecard()
    assert card.total_latency_ms >= 0
    assert card.avg_latency_ms >= 0


# ---------------------------------------------------------------------------
# PART 9: PERSISTENCE & API (31 - 32)
# ---------------------------------------------------------------------------

def test_31_persistence_roundtrip(baseline_scorecard: Scorecard):
    """Test 31: Scorecard converts to BenchmarkRunRecord and reconstitutes cleanly."""
    exp_id = uuid4()
    ver_id = uuid4()

    db_rec = baseline_scorecard.to_db_record(experiment_id=exp_id, agent_version_id=ver_id)
    assert isinstance(db_rec, BenchmarkRunRecord)
    assert db_rec.accuracy == baseline_scorecard.accuracy
    assert db_rec.reliability == baseline_scorecard.reliability

    # Reconstitute
    rehydrated = Scorecard.from_db_record(db_rec)
    assert rehydrated.benchmark_name == baseline_scorecard.benchmark_name
    assert rehydrated.accuracy == baseline_scorecard.accuracy
    assert rehydrated.reliability == baseline_scorecard.reliability
    assert rehydrated.total_cases == baseline_scorecard.total_cases


def test_32_api_scorecard_compare_endpoint(baseline_scorecard: Scorecard):
    """Test 32: POST /scorecard/compare returns valid comparison via FastAPI."""
    client = TestClient(app)
    cand = baseline_scorecard.model_copy(deep=True)
    cand.accuracy = 0.8800

    response = client.post(
        "/scorecard/compare",
        json={
            "baseline": baseline_scorecard.model_dump(mode="json"),
            "candidate": cand.model_dump(mode="json"),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["relationship"] == "strictly_better"
    assert "accuracy" in data["improved_dimensions"]
    assert "Accuracy improved by +13.0 percentage points" in data["summary"]
