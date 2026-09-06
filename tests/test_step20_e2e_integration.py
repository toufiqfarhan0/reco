"""Deterministic regression tests for Step 20 E2E integration fixes."""

import pytest
from uuid import uuid4
from reco.api.app import format_live_optimization_result, create_app
from reco.benchmarks.reconciliation import create_reconciliation_baseline_graph
from reco.evaluators.comparison import ComparisonPolicy, compare_scorecards
from reco.evaluators.scorecard import Scorecard
from reco.diagnostics.models import RootCauseDiagnosis, DiagnosisEvidence, RecommendedMutation
from reco.diagnostics.taxonomy import FailureCategory, Severity, MutationType
from reco.mutation.models import (
    AgentVersionCandidate,
    MutationCandidate,
    OptimizationGeneration,
    OptimizationResult,
)
from fastapi.testclient import TestClient


def test_format_live_optimization_result_dual_deltas_and_classification():
    """Verify format_live_optimization_result provides dual delta keys and uppercase decision."""
    baseline_graph = create_reconciliation_baseline_graph()
    
    # Create mock scorecards
    v0_card = Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        split="optimization",
        total_cases=12,
        passed_cases=9,
        failed_cases=3,
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
        passed_cases=10,
        failed_cases=2,
        accuracy=0.80,
        reliability=1.0,
        total_cost_usd=0.06,
        total_latency_ms=40000,
    )
    comp = compare_scorecards(v0_card, v1_card, ComparisonPolicy())

    # Create mock diagnosis
    diag = RootCauseDiagnosis(
        failure_category=FailureCategory.HALLUCINATED_MATCH,
        severity=Severity.HIGH,
        failed_node_id="fuzzy_match",
        symptom="Incorrect match found",
        summary="Vendor mismatch",
        root_cause="Missing strict vendor validation",
        confidence=0.90,
        evidence=[
            DiagnosisEvidence(source="tool_event", observed="Acme Corp", expected="Acme Inc")
        ],
        recommended_mutations=[
            RecommendedMutation(
                mutation_type=MutationType.PROMPT_CHANGE,
                target="fuzzy_match",
                rationale="Require vendor match",
                expected_effect="Eliminate hallucinated match",
                confidence=0.90,
            )
        ],
        metadata={"case_code": "REC-OPT-08"},
    )

    # Create mock mutation candidate
    mut = MutationCandidate(
        candidate_id=uuid4(),
        parent_version_id=uuid4(),
        mutation_type=MutationType.PROMPT_CHANGE,
        target="fuzzy_match",
        rationale="Enforce vendor token match in prompt",
        expected_effect="Eliminate hallucinated match",
        confidence=0.90,
        proposed_change={"proposed_diff": "Require strict vendor match"},
    )

    gen = OptimizationGeneration(
        generation_number=1,
        parent_version_id=uuid4(),
        candidate_version_ids=[mut.candidate_id],
        selected_version_id=mut.candidate_id,
        optimization_scorecard=v1_card,
        diagnoses=[diag],
        mutations=[mut],
        comparison=comp,
        decision="selected",
    )

    opt_result = OptimizationResult(
        experiment_id=uuid4(),
        initial_version_id=uuid4(),
        final_version_id=mut.candidate_id,
        generations=[gen],
        termination_reason="max_generations_reached",
        optimization_scorecard=v1_card,
        held_out_scorecard=v1_card,
    )

    res = format_live_optimization_result(
        opt_result=opt_result,
        goal="Reconcile accounts",
        baseline_graph=baseline_graph,
        model_name="glm-4-7-flash",
    )

    # 1. Verify dual scorecard comparison deltas
    score_comp = res["scorecard_comparison"]
    assert "delta_accuracy" in score_comp
    assert "accuracy_delta" in score_comp
    assert "delta_cost" in score_comp
    assert "cost_delta" in score_comp
    assert "delta_latency" in score_comp
    assert "latency_delta" in score_comp
    assert "classification" in score_comp
    assert "relationship" in score_comp
    assert score_comp["delta_accuracy"] == 0.05
    assert score_comp["classification"] == "strictly_better"

    # 2. Verify Diagnosis contract
    diagnoses = res["diagnoses"]
    assert len(diagnoses) == 1
    d = diagnoses[0]
    assert d["case_code"] == "REC-OPT-08"
    assert d["category"].lower() == "hallucinated_match"
    assert d["severity"] == "HIGH"
    assert d["failed_node"] == "fuzzy_match"
    assert d["recommended_mutation"].lower() == "prompt_change"
    assert "tool_event" in d["evidence"]

    # 3. Verify Mutation contract
    mutations = res["mutations"]
    assert len(mutations) == 1
    m = mutations[0]
    assert m["parent_version"] == "V0"
    assert m["child_version"] == "V1"
    assert m["mutation_type"].lower() == "prompt_change"
    assert m["target_node"] == "fuzzy_match"
    assert "before" in m["diff"]
    assert "after" in m["diff"]

    # 4. Verify Promotion Decision
    promo = res["promotion_assessment"]
    assert promo["decision"] in ("PROMOTE", "REJECT", "REVIEW")
    assert promo["decision"].isupper()


def test_api_run_agent_returns_run_id_and_model_calls():
    """Verify /agent/run endpoint returns run_id, model_calls, and latency."""
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/agent/run",
        json={
            "inputs": {
                "bank_records": [
                    {"transaction_id": "TX1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "vendor": "Acme"}
                ],
                "ledger_entries": [
                    {"entry_id": "GL1", "date": "2026-03-01", "amount": "100.00", "currency": "USD", "account": "Cash", "vendor": "Acme"}
                ],
            },
            "goal": "Reconcile test",
            "provider": "mock",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["run_id"].startswith("run_")
    assert "model_calls" in data
    assert "latency_ms" in data
    assert data["success"] is True
    assert data["status"] == "completed"


def test_api_analyze_goal_returns_valid_task_specification():
    """Verify /analyze-goal returns complete TaskSpecification."""
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/analyze-goal",
        json={
            "goal": "Analyze this dataset and identify unusual records.",
        },
    )
    assert response.status_code == 200
    spec = response.json()
    assert spec["original_goal"] == "Analyze this dataset and identify unusual records."
    assert "normalized_goal" in spec
    assert "required_capabilities" in spec
    assert len(spec["required_capabilities"]) > 0
    assert "expected_outputs" in spec


def test_api_generate_architecture_returns_graph_and_validation():
    """Verify /generate-architecture produces valid DAG without Gemma references."""
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/generate-architecture",
        json={
            "goal": "Analyze this dataset and identify unusual records.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    graph = data["graph"]
    validation = data["validation"]
    assert validation["valid"] is True
    assert len(graph["nodes"]) >= 2
    assert len(graph["edges"]) >= 1

    # Ensure zero gemma references
    graph_str = str(graph).lower()
    assert "gemma" not in graph_str
