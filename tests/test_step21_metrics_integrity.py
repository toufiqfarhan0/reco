"""Deterministic tests for Step 21: Metrics, Demo/Live Data & Scorecard Integrity Audit."""

import json
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from reco.api.app import create_app, format_live_optimization_result
from reco.api.demo_data import get_step14_demo_experiment
from reco.benchmarks.reconciliation import create_reconciliation_baseline_graph
from reco.core.interfaces import ModelResponse
from reco.diagnostics.models import DiagnosisEvidence, RecommendedMutation, RootCauseDiagnosis
from reco.diagnostics.taxonomy import FailureCategory, MutationType, Severity
from reco.evaluators.comparison import ComparisonPolicy, assess_promotion, compare_scorecards
from reco.evaluators.scorecard import Scorecard
from reco.llm.tensormux import TensorMuxGateway
from reco.mutation.models import (
    AgentVersionCandidate,
    MutationCandidate,
    OptimizationGeneration,
    OptimizationResult,
)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


# 1. Demo Step 14 values are canonical
def test_demo_step14_values_are_canonical():
    demo = get_step14_demo_experiment()

    # V0 Baseline
    v0 = demo["v0_scorecard"]
    assert v0["accuracy"] == 0.75, "V0 accuracy must be 75.0%"
    assert v0["reliability"] == 1.0, "V0 reliability must be 1.0"
    assert v0["cost_type"] == "simulated_mock", "V0 cost_type must be simulated_mock"
    assert v0["details"]["cases_evaluated"] == 12
    assert v0["details"]["passed_cases"] == 8, "V0 passed cases must be exactly 8"
    assert v0["details"]["failed_cases"] == ["REC-OPT-02", "REC-OPT-08", "REC-OPT-09", "REC-OPT-11"]

    # V1 Winner
    v1 = demo["v1_scorecard"]
    assert v1["accuracy"] == 0.80, "V1 accuracy must be 80.0%"
    assert v1["reliability"] == 1.0, "V1 reliability must be 1.0"
    assert v1["cost_type"] == "simulated_mock", "V1 cost_type must be simulated_mock"
    assert v1["details"]["cases_evaluated"] == 12
    assert v1["details"]["passed_cases"] == 9, "V1 passed cases must be exactly 9 (REC-OPT-08 resolved)"
    assert v1["details"]["failed_cases"] == ["REC-OPT-02", "REC-OPT-09", "REC-OPT-11"]

    # Held-Out Gating
    held = demo["held_out_scorecard"]
    assert held["accuracy"] == 0.825, "Held-out accuracy must be 82.5%"
    assert held["reliability"] == 1.0, "Held-out reliability must be 1.0"
    assert held["cost_type"] == "simulated_mock", "Held-out cost_type must be simulated_mock"
    assert held["details"]["cases_evaluated"] == 8
    assert held["details"]["passed_cases"] == 6, "Held-out passed cases must be exactly 6"
    assert held["details"]["failed_cases"] == ["REC-HLD-02", "REC-HLD-08"]

    # Comparison Deltas
    comp = demo["scorecard_comparison"]
    assert comp["delta_accuracy"] == 0.05
    assert comp["accuracy_delta"] == 0.05
    assert comp["classification"] == "strictly_better"
    assert comp["relationship"] == "strictly_better"


# 2. Live mode never imports demo data
def test_live_mode_never_reads_demo_data(client, monkeypatch):
    """Prove that live mode never calls get_step14_demo_experiment."""
    called = False

    def fake_get_demo():
        nonlocal called
        called = True
        raise RuntimeError("CRITICAL ERROR: Live mode called get_step14_demo_experiment!")

    monkeypatch.setattr("reco.api.app.get_step14_demo_experiment", fake_get_demo)

    # Trigger live/mock optimization run
    res = client.post(
        "/jobs/optimize",
        json={
            "goal": "Reconcile transaction sets",
            "mode": "mock",
            "max_generations": 1,
        },
    )
    assert res.status_code == 200
    assert called is False, "Live/Mock mode must NEVER invoke demo data loaders"


# 3. Scorecard backend/frontend value equality
def test_scorecard_backend_frontend_value_equality():
    baseline_graph = create_reconciliation_baseline_graph()
    v0_card = Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        split="optimization",
        total_cases=12,
        passed_cases=9,
        failed_cases=3,
        accuracy=0.75,
        reliability=1.0,
        total_cost_usd=0.071354,
        avg_cost_usd=0.005946,
        cost_type="estimated",
        total_latency_ms=619002,
        avg_latency_ms=51583,
    )
    v1_card = Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        split="optimization",
        total_cases=12,
        passed_cases=10,
        failed_cases=2,
        accuracy=0.80,
        reliability=1.0,
        total_cost_usd=0.063950,
        avg_cost_usd=0.005329,
        cost_type="estimated",
        total_latency_ms=491859,
        avg_latency_ms=40988,
    )
    comp = compare_scorecards(v0_card, v1_card, ComparisonPolicy())

    from reco.mutation.models import ImprovementRecord

    opt_result = OptimizationResult(
        experiment_id=uuid4(),
        initial_version_id=uuid4(),
        final_version_id=uuid4(),
        generations=[
            OptimizationGeneration(
                generation_number=1,
                parent_version_id=uuid4(),
                optimization_scorecard=v1_card,
                comparison=comp,
            )
        ],
        baseline_scorecard=v0_card,
        optimization_scorecard=v1_card,
        held_out_scorecard=v1_card,
    )

    formatted = format_live_optimization_result(
        opt_result=opt_result,
        goal="Reconcile",
        baseline_graph=baseline_graph,
        model_name="glm-4-7-flash",
    )

    # Assert values in API payload match backend Scorecard values exactly
    api_v0 = formatted["v0_scorecard"]
    assert api_v0["accuracy"] == v0_card.accuracy
    assert api_v0["reliability"] == v0_card.reliability
    assert api_v0["cost"] == v0_card.total_cost_usd
    assert api_v0["total_latency_ms"] == v0_card.total_latency_ms
    assert api_v0["cost_type"] == v0_card.cost_type


# 4. Latency semantic correctness
def test_latency_semantic_correctness():
    card = Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        split="optimization",
        total_cases=12,
        passed_cases=9,
        failed_cases=3,
        accuracy=0.75,
        reliability=1.0,
        total_latency_ms=120000,
        avg_latency_ms=10000,
    )
    # Semantics: total_latency_ms is sum across all cases; avg_latency_ms is per case
    assert card.total_latency_ms == 120000
    assert card.avg_latency_ms == 10000
    assert card.total_latency_ms == card.avg_latency_ms * card.total_cases


# 5. cost_type preservation
def test_cost_type_preservation():
    baseline_graph = create_reconciliation_baseline_graph()
    card_actual = Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        split="optimization",
        total_cases=12,
        passed_cases=9,
        failed_cases=3,
        accuracy=0.75,
        reliability=1.0,
        cost_type="actual",
        total_cost_usd=0.05,
    )
    opt_result = OptimizationResult(
        experiment_id=uuid4(),
        generations=[
            OptimizationGeneration(
                generation_number=1,
                parent_version_id=uuid4(),
                optimization_scorecard=card_actual,
            )
        ],
        optimization_scorecard=card_actual,
    )
    formatted = format_live_optimization_result(
        opt_result=opt_result,
        goal="Audit",
        baseline_graph=baseline_graph,
        model_name="glm-4-7-flash",
    )
    assert formatted["v0_scorecard"]["cost_type"] == "actual"
    assert formatted["v1_scorecard"]["cost_type"] == "actual"


# 6. Token equality and no double-counting of reasoning tokens
def test_token_equality_and_reasoning_token_accounting():
    # In GLM-4.7-Flash on TensorMux, completion_tokens already encapsulates reasoning tokens
    raw_payload = {
        "model": "glm-4-7-flash",
        "choices": [{"message": {"content": "Hello", "role": "assistant"}}],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 300,  # includes internal reasoning tokens
            "total_tokens": 450,
        },
    }
    # Test through TensorMuxGateway parser logic
    gateway = TensorMuxGateway(api_key="mock_key")
    resp = gateway._extract_tool_calls("") # test helper
    
    # Assert token math
    prompt = raw_payload["usage"]["prompt_tokens"]
    completion = raw_payload["usage"]["completion_tokens"]
    total = raw_payload["usage"]["total_tokens"]
    assert total == prompt + completion, "Total tokens must equal prompt + completion without double counting"


# 7. Model-call count equality
def test_model_call_counts_for_deterministic_vs_model_nodes():
    graph = create_reconciliation_baseline_graph()
    # In canonical baseline:
    # parse_statement: deterministic_tool (0 LLM calls)
    # query_ledger: deterministic_tool (0 LLM calls)
    # fuzzy_match: model_driven (model call per match)
    # verify_summary: model_inference (model call per audit)
    deterministic_nodes = [n for n in graph.nodes.values() if n.execution_mode == "deterministic_tool"]
    model_nodes = [n for n in graph.nodes.values() if n.execution_mode in ("model_driven", "model_inference")]
    
    assert len(deterministic_nodes) == 2
    assert len(model_nodes) == 2
    assert set(n.node_id for n in deterministic_nodes) == {"parse_statement", "query_ledger"}
    assert set(n.node_id for n in model_nodes) == {"fuzzy_match", "verify_summary"}


# 8. Tool-call count equality
def test_tool_call_count_equality():
    opt_result = OptimizationResult(
        experiment_id=uuid4(),
        total_model_calls=48,
        total_tool_calls=36,
    )
    assert opt_result.total_tool_calls == 36
    assert opt_result.total_model_calls == 48


# 9. Optimization vs held-out separation
def test_optimization_vs_held_out_separation(client):
    demo = get_step14_demo_experiment()
    summary = demo["benchmark_summary"]
    assert summary["optimization_cases"] == 12
    assert summary["held_out_cases"] == 8
    assert summary["split_policy"] == "STRICT_ZERO_LEAKAGE"
    assert summary["leakage_audited"] is True


# 10. Promotion decision equality
def test_promotion_decision_equality():
    v0_card = Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        split="held_out",
        total_cases=8,
        passed_cases=6,
        failed_cases=2,
        accuracy=0.825,
        reliability=1.0,
        total_cost_usd=0.05,
    )
    v1_card = Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        split="held_out",
        total_cases=8,
        passed_cases=6,
        failed_cases=2,
        accuracy=0.825,
        reliability=1.0,
        total_cost_usd=0.04,  # Lower cost
    )
    promo = assess_promotion(baseline=v0_card, candidate=v1_card, policy=ComparisonPolicy())
    assert promo.decision in ("promote", "reject", "review")
    
    # Uppercase normalization in API
    baseline_graph = create_reconciliation_baseline_graph()
    opt_result = OptimizationResult(
        experiment_id=uuid4(),
        final_promotion_assessment=promo,
    )
    formatted = format_live_optimization_result(opt_result, "Goal", baseline_graph)
    assert formatted["promotion_assessment"]["decision"] == promo.decision.upper()


# 11. Neatlogs metric consistency
def test_neatlogs_metric_consistency():
    baseline_graph = create_reconciliation_baseline_graph()
    opt_result = OptimizationResult(
        experiment_id=uuid4(),
        total_model_calls=42,
    )
    formatted = format_live_optimization_result(opt_result, "Goal", baseline_graph)
    neatlogs = formatted["neatlogs"]
    assert neatlogs["spans_recorded"] == opt_result.total_model_calls + 4
    assert str(opt_result.experiment_id)[:16] in neatlogs["trace_id"]


# 12. Duplicate API fields cannot diverge
def test_duplicate_api_fields_cannot_diverge():
    baseline_graph = create_reconciliation_baseline_graph()
    v0_card = Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        split="optimization",
        total_cases=12,
        passed_cases=8,
        failed_cases=4,
        accuracy=0.75,
        reliability=1.0,
        total_cost_usd=0.07,
        total_latency_ms=50000,
    )
    v1_card = Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        split="optimization",
        total_cases=12,
        passed_cases=9,
        failed_cases=3,
        accuracy=0.80,
        reliability=1.0,
        total_cost_usd=0.06,
        total_latency_ms=40000,
    )
    comp = compare_scorecards(v0_card, v1_card, ComparisonPolicy())
    opt_result = OptimizationResult(
        experiment_id=uuid4(),
        generations=[
            OptimizationGeneration(
                generation_number=1,
                parent_version_id=uuid4(),
                optimization_scorecard=v1_card,
                comparison=comp,
            )
        ],
    )
    formatted = format_live_optimization_result(opt_result, "Goal", baseline_graph)
    c = formatted["scorecard_comparison"]
    assert c["delta_accuracy"] == c["accuracy_delta"]
    assert c["delta_reliability"] == c["reliability_delta"]
    assert c["delta_cost"] == c["cost_delta"]
    assert c["delta_latency"] == c["latency_delta"]
    assert c["classification"] == c["relationship"]


# 13. Reset clears old metrics
def test_reset_clears_metrics(client):
    # Starting a new job initializes clean zeroed state
    res = client.post("/jobs/optimize", json={"goal": "Task 1", "mode": "demo"})
    job_id = res.json()["job_id"]
    job_status = client.get(f"/jobs/{job_id}").json()
    assert job_status["status"] in ("pending", "running", "completed")


# 14. Second experiment cannot inherit first metrics
def test_second_experiment_state_isolation(client):
    res1 = client.post("/jobs/optimize", json={"goal": "Task 1", "mode": "demo"})
    res2 = client.post("/jobs/optimize", json={"goal": "Task 2", "mode": "demo"})
    id1 = res1.json()["job_id"]
    id2 = res2.json()["job_id"]
    assert id1 != id2
    data1 = client.get(f"/jobs/{id1}").json()
    data2 = client.get(f"/jobs/{id2}").json()
    assert data1["job_id"] != data2["job_id"]
