"""Tests for Reco API endpoints."""

from fastapi.testclient import TestClient
from reco import __track__, __version__


def test_health_endpoint(client: TestClient):
    """Verify /health returns 200 and expected status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "reco"
    assert data["environment"] == "test"
    assert data["version"] == __version__
    assert "integrations" in data
    assert isinstance(data["integrations"], dict)
    assert data["integrations"]["supabase"] is False
    assert data["integrations"]["tensormux"] is False
    assert data["integrations"]["neatlogs"] is False
    assert data["integrations"]["dodo"] is False


def test_version_endpoint(client: TestClient):
    """Verify /version returns 200, version, and hackathon track metadata."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == __version__
    assert data["track"] == __track__
    assert "Reco" in data["app_name"]


def test_tools_endpoint(client: TestClient):
    """Verify /tools returns available registered tools with schema metadata."""
    response = client.get("/tools")
    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    assert len(tools) > 0
    names = [t["name"] for t in tools]
    assert "parse_bank_statement" in names
    assert "query_general_ledger" in names
    assert "fuzzy_match_transactions" in names
    for t in tools:
        assert "name" in t
        assert "description" in t
        assert "deterministic" in t
        assert "risk_level" in t


def test_experiments_demo_endpoint(client: TestClient):
    """Verify /experiments/demo returns authentic Step 14 optimization data."""
    response = client.get("/experiments/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["experiment_id"] == "exp_step14_real_opt_001"
    assert data["status"] == "completed"
    assert data["active_model"] == "glm-4-7-flash"
    assert data["v0_scorecard"]["accuracy"] == 0.75
    assert data["v1_scorecard"]["accuracy"] == 0.80
    assert data["held_out_scorecard"]["accuracy"] == 0.825
    assert data["promotion_assessment"]["decision"] == "PROMOTE"
    assert len(data["diagnoses"]) >= 1
    assert len(data["mutations"]) >= 1
    assert data["neatlogs"]["available"] is True


def test_agent_run_endpoint(client: TestClient):
    """Verify /agent/run executes a graph on inputs."""
    payload = {
        "inputs": {
            "bank_records": [{"transaction_id": "TX101", "date": "2026-03-01", "amount": 250.00, "vendor": "Stripe"}],
            "ledger_entries": [{"entry_id": "GL101", "date": "2026-03-01", "amount": 250.00, "vendor": "Stripe"}],
        },
        "goal": "Reconcile transactions",
        "provider": "mock",
    }
    response = client.post("/agent/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "completed"
    assert "parse_statement" in data["execution_order"]


def test_jobs_optimize_lifecycle(client: TestClient):
    """Verify /jobs/optimize creates and tracks an asynchronous demo job."""
    payload = {
        "goal": "Reconcile banking transactions",
        "mode": "demo",
    }
    response = client.post("/jobs/optimize", json=payload)
    assert response.status_code == 200
    job_data = response.json()
    assert "job_id" in job_data
    job_id = job_data["job_id"]

    # Poll status
    status_resp = client.get(f"/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ["pending", "running", "completed"]

