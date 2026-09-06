"""Deterministic verification of Step 25 canonical evidence and metrics consistency.

Validates:
1. Canonical reconciliation numbers (75% -> 80% -> 82.5%)
2. Canonical anomaly detection numbers (80% -> 100% -> 66.7%, REVIEW)
3. Canonical research comparison numbers (100% -> 100% -> 100%, PROMOTE)
4. Cross-domain table consistency across artifacts and surfaces
5. Demo endpoint values match canonical values exactly
6. Frontend contracts (ScorecardView, HeldOutValidationView, etc.) receive exact API values
7. No conflicting stale reconciliation metrics in active documentation
8. Anomaly detection promotion decision strictly remains REVIEW
9. Research comparison promotion decision strictly remains PROMOTE
10. Held-out validation metrics remain isolated from optimization metrics
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from reco.api.app import create_app
from reco.api.demo_data import (
    get_demo_experiment,
    get_step14_demo_experiment,
    get_anomaly_demo_experiment,
    get_research_demo_experiment,
)


@pytest.fixture
def canonical_evidence():
    artifact_path = Path("scratch/step25_canonical_evidence.json")
    assert artifact_path.exists(), f"Missing canonical evidence artifact: {artifact_path}"
    with open(artifact_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_1_canonical_reconciliation_numbers(canonical_evidence):
    """1. Ensure canonical reconciliation metrics match Step 14 verified ground truth."""
    table = canonical_evidence["cross_domain_canonical_table"]
    reco = next(row for row in table if row["domain"] == "reconciliation")

    assert reco["v0_accuracy"] == 0.75
    assert reco["v1_accuracy"] == 0.80
    assert reco["accuracy_delta"] == 0.05
    assert reco["held_out_accuracy"] == 0.825
    assert reco["reliability"] == 1.0
    assert reco["cost_delta_usd"] == pytest.approx(-0.007404, abs=1e-5)
    assert reco["cost_delta_percentage"] == pytest.approx(-10.38, abs=0.1)
    assert reco["latency_delta_ms"] == pytest.approx(-127143.0, abs=10)
    assert reco["latency_delta_percentage"] == pytest.approx(-20.54, abs=0.1)
    assert reco["promotion_decision"] == "PROMOTE"
    assert "a1755c16" in reco["provenance_experiment_id"]


def test_2_canonical_anomaly_numbers(canonical_evidence):
    """2. Ensure canonical anomaly detection metrics match Step 24 verified real run."""
    table = canonical_evidence["cross_domain_canonical_table"]
    anom = next(row for row in table if row["domain"] == "anomaly_detection")

    assert anom["v0_accuracy"] == 0.80
    assert anom["v1_accuracy"] == 1.00
    assert anom["accuracy_delta"] == 0.20
    assert anom["held_out_accuracy"] == pytest.approx(0.6667, abs=1e-3)
    assert anom["reliability"] == 1.0
    assert anom["cost_delta_usd"] == pytest.approx(0.003647, abs=1e-5)
    assert anom["cost_delta_percentage"] == pytest.approx(30.56, abs=0.1)
    assert anom["latency_delta_ms"] == 0.0
    assert anom["promotion_decision"] == "REVIEW"


def test_3_canonical_research_numbers(canonical_evidence):
    """3. Ensure canonical research comparison metrics match Step 24 verified real run."""
    table = canonical_evidence["cross_domain_canonical_table"]
    res = next(row for row in table if row["domain"] == "research_comparison")

    assert res["v0_accuracy"] == 1.00
    assert res["v1_accuracy"] == 1.00
    assert res["accuracy_delta"] == 0.0
    assert res["held_out_accuracy"] == 1.00
    assert res["reliability"] == 1.0
    assert res["cost_delta_usd"] == pytest.approx(-0.001604, abs=1e-5)
    assert res["cost_delta_percentage"] == pytest.approx(-9.83, abs=0.1)
    assert res["latency_delta_ms"] == pytest.approx(-10389.0, abs=10)
    assert res["latency_delta_percentage"] == pytest.approx(-14.75, abs=0.1)
    assert res["promotion_decision"] == "PROMOTE"


def test_4_cross_domain_table_consistency(canonical_evidence):
    """4. Ensure cross_domain_comparison_table in Step 24 json matches Step 25 canonical values."""
    step24_path = Path("scratch/step24_cross_domain_real_provider.json")
    assert step24_path.exists(), "Missing step24 artifact"
    with open(step24_path, "r", encoding="utf-8") as f:
        step24_data = json.load(f)

    step24_table = {r["domain"]: r for r in step24_data["cross_domain_comparison_table"]}
    step25_table = {r["domain"]: r for r in canonical_evidence["cross_domain_canonical_table"]}

    # All three domains present
    assert set(step24_table.keys()) == {"reconciliation", "anomaly_detection", "research_comparison"}
    assert set(step25_table.keys()) == {"reconciliation", "anomaly_detection", "research_comparison"}

    for domain in ["reconciliation", "anomaly_detection", "research_comparison"]:
        r24 = step24_table[domain]
        r25 = step25_table[domain]
        assert r24["v0_accuracy"] == r25["v0_accuracy"]
        assert r24["v1_accuracy"] == r25["v1_accuracy"]
        assert r24["held_out_accuracy"] == pytest.approx(r25["held_out_accuracy"], abs=1e-3)
        assert r24["cost_delta"] == pytest.approx(r25["cost_delta_usd"], abs=1e-5)
        assert r24["promotion"].upper() == r25["promotion_decision"].upper()


def test_5_demo_values_equal_canonical_values(canonical_evidence, client):
    """5. Ensure demo data and /experiments/demo API return exactly the canonical numbers."""
    domains = ["reconciliation", "anomaly_detection", "research_comparison"]
    for d in domains:
        resp = client.get(f"/experiments/demo?domain={d}")
        assert resp.status_code == 200, f"Failed GET /experiments/demo?domain={d}"
        data = resp.json()

        canonical_row = next(r for r in canonical_evidence["cross_domain_canonical_table"] if r["domain"] == d)

        assert data["v0_scorecard"]["accuracy"] == canonical_row["v0_accuracy"]
        assert data["v1_scorecard"]["accuracy"] == canonical_row["v1_accuracy"]
        assert data["held_out_scorecard"]["accuracy"] == pytest.approx(canonical_row["held_out_accuracy"], abs=1e-3)
        assert data["promotion_assessment"]["decision"].upper() == canonical_row["promotion_decision"].upper()


def test_6_frontend_contracts_receive_authoritative_metrics(client):
    """6. Ensure demo payloads provide all fields required by frontend views."""
    for domain in ["reconciliation", "anomaly_detection", "research_comparison"]:
        resp = client.get(f"/experiments/demo?domain={domain}")
        assert resp.status_code == 200
        payload = resp.json()

        # ScorecardView contracts
        assert "v0_scorecard" in payload
        assert "v1_scorecard" in payload
        assert "scorecard_comparison" in payload
        assert "cost_type" in payload["v0_scorecard"]
        assert "cost_type" in payload["v1_scorecard"]
        assert "accuracy" in payload["v0_scorecard"]
        assert "accuracy" in payload["v1_scorecard"]
        assert "reliability" in payload["v0_scorecard"]
        assert "reliability" in payload["v1_scorecard"]

        # HeldOutValidationView contracts
        assert "held_out_scorecard" in payload
        assert "benchmark_summary" in payload
        assert "promotion_assessment" in payload
        assert "optimization_cases" in payload["benchmark_summary"]
        assert "held_out_cases" in payload["benchmark_summary"]
        assert "decision" in payload["promotion_assessment"]

        # EvolutionTimeline and CandidateComparison contracts
        assert "evolution_timeline" in payload
        assert len(payload["evolution_timeline"]) >= 2
        assert "candidates" in payload
        assert len(payload["candidates"]) >= 2


def test_7_no_conflicting_current_metrics():
    """7. Ensure no conflicting reconciliation numbers (0.50, 0.83, 1.00) remain in current documentation."""
    docs_file = Path("docs/RECO_MULTI_DOMAIN.md")
    assert docs_file.exists()
    content = docs_file.read_text(encoding="utf-8")

    # The erroneous combination from Step 24 must not appear in any active table
    assert "0.50 (6/12)" not in content, "Stale 0.50 (6/12) found in docs/RECO_MULTI_DOMAIN.md"
    assert "0.83 (10/12)" not in content, "Stale 0.83 (10/12) found in docs/RECO_MULTI_DOMAIN.md"
    assert "1.00 (8/8)" not in content, "Stale 1.00 (8/8) found in docs/RECO_MULTI_DOMAIN.md"

    # Canonical values must appear
    assert "75.00% (9/12)" in content
    assert "80.00% (10/12)" in content
    assert "82.50% (7/8)" in content


def test_8_anomaly_promotion_remains_review(client):
    """8. Ensure Anomaly Detection promotion decision is strictly REVIEW and never falsely promoted."""
    exp = get_anomaly_demo_experiment()
    assert exp["promotion_assessment"]["decision"] == "REVIEW"
    assert exp["promotion_assessment"]["gate_passed"] is False

    # Check via API endpoint
    resp = client.get("/experiments/demo?domain=anomaly_detection")
    data = resp.json()
    assert data["promotion_assessment"]["decision"] == "REVIEW"
    assert data["promotion_assessment"]["gate_passed"] is False

    # Verify reason cites held-out tradeoff
    reasons = " ".join(data["promotion_assessment"]["reasons"])
    assert "tradeoff" in reasons.lower() or "review" in reasons.lower()


def test_9_research_promotion_remains_promote(client):
    """9. Ensure Research Comparison promotion decision is strictly PROMOTE."""
    exp = get_research_demo_experiment()
    assert exp["promotion_assessment"]["decision"] == "PROMOTE"
    assert exp["promotion_assessment"]["gate_passed"] is True

    # Check via API endpoint
    resp = client.get("/experiments/demo?domain=research_comparison")
    data = resp.json()
    assert data["promotion_assessment"]["decision"] == "PROMOTE"
    assert data["promotion_assessment"]["gate_passed"] is True


def test_10_held_out_metrics_remain_separate(client):
    """10. Ensure held-out metrics remain strictly isolated from optimization metrics for all domains."""
    for domain in ["reconciliation", "anomaly_detection", "research_comparison"]:
        resp = client.get(f"/experiments/demo?domain={domain}")
        data = resp.json()

        v0_opt = data["v0_scorecard"]
        v1_opt = data["v1_scorecard"]
        held_out = data["held_out_scorecard"]
        summary = data["benchmark_summary"]

        # Case counts must match split policy
        assert v0_opt["details"]["cases_evaluated"] == summary["optimization_cases"]
        assert held_out["details"]["cases_evaluated"] == summary["held_out_cases"]
        assert summary["optimization_cases"] > 0
        assert summary["held_out_cases"] > 0

        # Optimization and held-out scores must be distinct objects
        assert held_out is not v1_opt
        assert held_out is not v0_opt
