"""Tests for FastAPI Web Application & SPA Static Serving (Track 1).

Verifies:
1. Health check endpoints (GET /health and GET /api/health).
2. Monetization endpoints (POST /billing/checkout, /billing/portal, /billing/webhook).
3. Static SPA serving and fallback routing:
   - Root (/) serves index.html.
   - Static assets (/assets/..., /style.css) are served with correct contents.
   - Client-side routes (e.g. /stages/build, /stages/run) fallback to index.html.
   - Missing API endpoints (/api/invalid, /billing/invalid) return 404 JSON, NOT index.html.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Dict
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import standardwebhooks

from reco.api.app import app, configure_spa_mount, get_billing_service, set_billing_service
from reco.billing.service import BillingService
from reco.db.repository import InMemoryRepository


TEST_WEBHOOK_SECRET = "whsec_" + base64.b64encode(b"dodo_test_secret_key_32_bytes_!").decode("ascii")


def _make_headers(secret: str, payload_str: str, msg_id: str = "msg_api_001") -> Dict[str, str]:
    ts = datetime.now(timezone.utc)
    wh = standardwebhooks.Webhook(secret)
    sig = wh.sign(msg_id, ts, payload_str)
    return {
        "webhook-id": msg_id,
        "webhook-timestamp": str(int(ts.timestamp())),
        "webhook-signature": sig,
    }


@pytest.fixture
def client():
    # Setup test billing service
    repo = InMemoryRepository()
    mock_client = MagicMock()
    mock_session = MagicMock()
    mock_session.session_id = "cs_api_test_123"
    mock_session.checkout_url = "https://test.dodopayments.com/checkout/cs_api_test_123"
    mock_client.checkout_sessions.create.return_value = mock_session

    mock_portal = MagicMock()
    mock_portal.link = "https://test.dodopayments.com/portal/cus_test_123"
    mock_client.customers.customer_portal.create.return_value = mock_portal

    test_service = BillingService(
        api_key="dodo_api_test_key",
        webhook_secret=TEST_WEBHOOK_SECRET,
        environment="test_mode",
        repository=repo,
        client=mock_client,
    )
    set_billing_service(test_service)

    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoints(client):
    """Verify GET /health and GET /api/health return 200 with service info."""
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "ok"
    assert r1.json()["service"] == "reco"

    r2 = client.get("/api/health")
    assert r2.status_code == 200
    assert r2.json()["status"] == "ok"


def test_billing_checkout_endpoint(client):
    """Verify POST /billing/checkout dispatches to BillingService."""
    payload = {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "email": "agent-user@example.com",
        "return_url": "https://app.reco.ai/billing/success",
    }
    resp = client.post("/billing/checkout", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "cs_api_test_123"
    assert "https://test.dodopayments.com/checkout" in data["checkout_url"]


def test_billing_portal_endpoint(client):
    """Verify POST /billing/portal dispatches to BillingService."""
    payload = {
        "customer_id": "cus_test_123",
        "return_url": "https://app.reco.ai/billing/portal",
    }
    resp = client.post("/billing/portal", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "https://test.dodopayments.com/portal" in data["portal_url"]


def test_billing_webhook_endpoint(client):
    """Verify POST /billing/webhook ingests and verifies authentic HMAC webhooks."""
    payload = {
        "type": "payment.succeeded",
        "data": {
            "payment_id": "pay_test_001",
            "customer": {"customer_id": "cus_test_001", "email": "user@example.com"},
            "metadata": {"user_id": "00000000-0000-0000-0000-000000000001"},
            "total_amount": 900,
            "currency": "USD",
        },
    }
    payload_str = json.dumps(payload)
    headers = _make_headers(TEST_WEBHOOK_SECRET, payload_str)
    headers["content-type"] = "application/json"

    resp = client.post("/billing/webhook", content=payload_str, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["received"] is True
    assert resp.json()["event"] == "payment.succeeded"


def test_spa_static_files_and_fallback():
    """Verify SPA static file serving and fallback routing to index.html."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        index_file = tmp_path / "index.html"
        index_file.write_text("<!DOCTYPE html><html><body>Reco Console SPA</body></html>")

        asset_file = tmp_path / "app.css"
        asset_file.write_text("body { background: #000; }")

        test_app = FastAPI()

        @test_app.get("/api/data")
        def get_data():
            return {"data": 123}

        # Mount SPA
        assert configure_spa_mount(test_app, dist_dir=tmp_path) is True

        client = TestClient(test_app)

        # 1. Root serves index.html
        root_resp = client.get("/")
        assert root_resp.status_code == 200
        assert "Reco Console SPA" in root_resp.text

        # 2. Static asset is served directly
        asset_resp = client.get("/app.css")
        assert asset_resp.status_code == 200
        assert "background: #000" in asset_resp.text

        # 3. Client-side SPA routes fallback to index.html
        spa_route_resp = client.get("/stages/understand")
        assert spa_route_resp.status_code == 200
        assert "Reco Console SPA" in spa_route_resp.text

        # 4. API endpoints still work
        api_resp = client.get("/api/data")
        assert api_resp.status_code == 200
        assert api_resp.json() == {"data": 123}

        # 5. Missing API endpoints return 404 JSON, NOT index.html
        api_missing = client.get("/api/nonexistent")
        assert api_missing.status_code == 404
        assert "Reco Console SPA" not in api_missing.text


def test_live_app_serving_built_frontend():
    """Verify live app instance serves actual built frontend/dist when present."""
    repo_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if not (repo_dist / "index.html").is_file():
        pytest.skip("frontend/dist/index.html not yet built")

    configure_spa_mount(app)
    with TestClient(app) as test_client:
        # Root route
        res_root = test_client.get("/")
        assert res_root.status_code == 200
        assert "Reco — Autonomous Agent Engineering System" in res_root.text

        # Client route fallback
        res_stage = test_client.get("/stages/validate")
        assert res_stage.status_code == 200
        assert "Reco — Autonomous Agent Engineering System" in res_stage.text

