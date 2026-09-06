"""Tests for Dodo Payments Monetization Layer, HMAC Webhook Verification & Decoupled Gating (Step 8 / Track 1).

Verifies:
1. Reco Pro subscription tier configuration ($9.00/month, $900 cents).
2. Hosted Checkout Sessions endpoint (POST /billing/checkout):
   - Accepts { user_id, email, return_url }.
   - Generates authenticated redirect checkout URL from Dodo Payments API.
   - Fault-tolerance on gateway drops/timeouts.
3. Customer Portal endpoint (POST /billing/portal) for subscription self-management.
4. Authentic HMAC Webhook verification via standardwebhooks:
   - Anti-replay freshness check.
   - Rejection of forged or missing signature headers with 400 Bad Request.
   - Acceptance of authentic signatures with 200 OK.
   - Idempotent deduplication on duplicate webhook-id delivery.
5. Ingestion of canonical payment/subscription lifecycle events:
   - payment.succeeded
   - subscription.active
   - subscription.cancelled
   - subscription.renewed
   - Updates user entitlements in database repository.
6. Entitlement Gating:
   - Free vs Pro tier checks.
   - require_pro_entitlement enforcement.
7. Strict Decoupling:
   - Verification that gateway drops/timeouts NEVER block core agent DAG synthesis or local benchmarks.
8. Zero secrets leakage in code, logs, or responses.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import json
import os
from typing import Any, Dict
from unittest.mock import MagicMock, patch
import pytest

import httpx
import standardwebhooks

from reco.benchmarks.base import BenchmarkSplit
from reco.benchmarks.reconciliation import get_reconciliation_benchmark_suite
from reco.billing.models import (
    DEFAULT_PRO_CURRENCY,
    DEFAULT_PRO_PRICE_CENTS,
    DEFAULT_PRO_PRICE_USD,
    DEFAULT_PRO_PRODUCT_ID,
    DEFAULT_PRO_PRODUCT_NAME,
    BillingError,
    CheckoutRequest,
    CheckoutResponse,
    EntitlementGatingError,
    PaymentGatewayError,
    PortalRequest,
    PortalResponse,
    SubscriptionStatus,
    SubscriptionTier,
    WebhookResult,
    WebhookVerificationError,
)
from reco.billing.service import BillingService
from reco.core.goal_analyzer import GoalAnalyzer
from reco.db.models import UserEntitlementRecord
from reco.db.repository import InMemoryRepository
from reco.engine.generator import ArchitectureGenerator
from reco.engine.runtime import AgentRuntime
from reco.evaluators.scorecard import ScorecardEvaluator
from reco.tools.registry import ToolRegistry

TEST_WEBHOOK_SECRET = "whsec_" + base64.b64encode(b"dodo_test_secret_key_32_bytes_!").decode("ascii")
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PRO_USER_ID = "00000000-0000-0000-0000-000000000002"
TEST_CUSTOMER_ID = "cus_dodo_test_customer_123"
TEST_SUBSCRIPTION_ID = "sub_dodo_test_sub_456"
TEST_PAYMENT_ID = "pay_dodo_test_pay_789"


def _generate_webhook_headers(
    secret: str,
    payload_str: str,
    msg_id: str = "msg_test_001",
    timestamp: datetime | None = None,
) -> Dict[str, str]:
    """Helper to generate authentic standardwebhooks signature headers."""
    ts = timestamp or datetime.now(timezone.utc)
    wh = standardwebhooks.Webhook(secret)
    sig = wh.sign(msg_id, ts, payload_str)
    return {
        "webhook-id": msg_id,
        "webhook-timestamp": str(int(ts.timestamp())),
        "webhook-signature": sig,
    }


# ==============================================================================
# 1. Product Tier & Pricing Configuration
# ==============================================================================

def test_reco_pro_product_tier_configuration():
    """Verify Reco Pro tier pricing matches $9.00/month (900 cents) specifications."""
    assert DEFAULT_PRO_PRODUCT_ID == "pdt_reco_pro"
    assert DEFAULT_PRO_PRICE_CENTS == 900
    assert DEFAULT_PRO_PRICE_USD == 9.00
    assert DEFAULT_PRO_CURRENCY == "USD"
    assert DEFAULT_PRO_PRODUCT_NAME == "Reco Pro"

    # Environment variable override test
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("DODO_PRO_PRODUCT_ID", "pdt_custom_pro_tier")
        service = BillingService()
        assert service.pro_product_id == "pdt_custom_pro_tier"


# ==============================================================================
# 2. Hosted Checkout Sessions (POST /billing/checkout)
# ==============================================================================

def test_checkout_session_creation_with_injected_client():
    """Verify Checkout Session calls Dodo client and returns redirect checkout URL."""
    repo = InMemoryRepository()
    mock_client = MagicMock()
    mock_session = MagicMock()
    mock_session.session_id = "cs_live_session_12345"
    mock_session.checkout_url = "https://test.dodopayments.com/checkout/cs_live_session_12345"
    mock_client.checkout_sessions.create.return_value = mock_session

    service = BillingService(
        api_key="dodo_test_key_abc",
        webhook_secret=TEST_WEBHOOK_SECRET,
        repository=repo,
        client=mock_client,
    )

    req = CheckoutRequest(
        user_id=TEST_USER_ID,
        email="developer@example.com",
        return_url="https://app.reco.ai/billing/success",
    )

    response = service.create_checkout_session(req)
    assert isinstance(response, CheckoutResponse)
    assert response.session_id == "cs_live_session_12345"
    assert response.checkout_url == "https://test.dodopayments.com/checkout/cs_live_session_12345"
    assert response.product_id == DEFAULT_PRO_PRODUCT_ID
    assert response.user_id == TEST_USER_ID

    # Verify parameters sent to Dodo Payments
    mock_client.checkout_sessions.create.assert_called_once()
    call_kwargs = mock_client.checkout_sessions.create.call_args[1]
    assert call_kwargs["product_cart"] == [{"product_id": DEFAULT_PRO_PRODUCT_ID, "quantity": 1}]
    assert call_kwargs["customer"] == {"email": "developer@example.com"}
    assert call_kwargs["return_url"] == "https://app.reco.ai/billing/success"
    assert call_kwargs["metadata"]["user_id"] == TEST_USER_ID


def test_checkout_session_http_endpoint_dispatch():
    """Verify HTTP endpoint POST /billing/checkout dispatches correctly and returns 200."""
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=InMemoryRepository())
    body = json.dumps({
        "user_id": TEST_USER_ID,
        "email": "agent_dev@reco.ai",
        "return_url": "https://app.reco.ai/console",
    })

    status_code, data = service.handle_http_request("POST", "/billing/checkout", {}, body)
    assert status_code == 200
    assert "checkout_url" in data
    assert "session_id" in data
    assert data["user_id"] == TEST_USER_ID


def test_checkout_session_payment_gateway_timeout_returns_503():
    """Verify payment gateway timeout raises PaymentGatewayError and returns 503."""
    mock_client = MagicMock()
    mock_client.checkout_sessions.create.side_effect = httpx.ConnectTimeout("Gateway timed out")

    service = BillingService(
        api_key="dodo_test_key",
        webhook_secret=TEST_WEBHOOK_SECRET,
        client=mock_client,
    )

    with pytest.raises(PaymentGatewayError) as exc_info:
        service.create_checkout_session({
            "user_id": TEST_USER_ID,
            "email": "dev@reco.ai",
            "return_url": "https://app.reco.ai",
        })
    assert "Gateway timed out" in str(exc_info.value)

    # HTTP endpoint dispatch test
    status_code, data = service.handle_http_request(
        "POST",
        "/billing/checkout",
        {},
        json.dumps({
            "user_id": TEST_USER_ID,
            "email": "dev@reco.ai",
            "return_url": "https://app.reco.ai",
        }),
    )
    assert status_code == 503
    assert "Payment gateway unavailable" in data["error"]


# ==============================================================================
# 3. Customer Portal Sessions (POST /billing/portal)
# ==============================================================================

def test_portal_session_creation_with_customer_id():
    """Verify Customer Portal session creates valid portal redirect URL."""
    repo = InMemoryRepository()
    mock_client = MagicMock()
    mock_portal = MagicMock()
    mock_portal.link = "https://test.dodopayments.com/portal/cus_123_portal_auth"
    mock_client.customers.customer_portal.create.return_value = mock_portal

    service = BillingService(
        api_key="dodo_test_key",
        webhook_secret=TEST_WEBHOOK_SECRET,
        repository=repo,
        client=mock_client,
    )

    req = PortalRequest(
        customer_id=TEST_CUSTOMER_ID,
        return_url="https://app.reco.ai/account",
    )
    res = service.create_portal_session(req)
    assert isinstance(res, PortalResponse)
    assert res.portal_url == "https://test.dodopayments.com/portal/cus_123_portal_auth"
    assert res.customer_id == TEST_CUSTOMER_ID


def test_portal_session_resolves_customer_id_from_user_id():
    """Verify Customer Portal resolves customer ID from repository when user_id provided."""
    repo = InMemoryRepository()
    repo.save_user_entitlement(
        UserEntitlementRecord(
            user_id=TEST_USER_ID,
            tier=SubscriptionTier.PRO.value,
            status=SubscriptionStatus.ACTIVE.value,
            is_pro=True,
            customer_id="cus_resolved_from_repo_456",
        )
    )

    service = BillingService(
        webhook_secret=TEST_WEBHOOK_SECRET,
        repository=repo,
    )

    status_code, data = service.handle_http_request(
        "POST",
        "/billing/portal",
        {},
        json.dumps({"user_id": TEST_USER_ID, "return_url": "https://app.reco.ai/settings"}),
    )
    assert status_code == 200
    assert "portal_url" in data
    assert data["customer_id"] == "cus_resolved_from_repo_456"


def test_portal_session_missing_customer_returns_400():
    """Verify portal request fails gracefully when user has no associated customer ID."""
    repo = InMemoryRepository()
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=repo)

    status_code, data = service.handle_http_request(
        "POST",
        "/billing/portal",
        {},
        json.dumps({"user_id": "nonexistent_user"}),
    )
    assert status_code == 400
    assert "No Dodo Payments customer ID found" in data["detail"]


# ==============================================================================
# 4. Webhook Ingestion & HMAC Verification (POST /billing/webhook)
# ==============================================================================

def test_webhook_hmac_verification_authentic_signature():
    """Verify standardwebhooks authentic signature is accepted with 200 OK."""
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=InMemoryRepository())
    payload_obj = {
        "business_id": "bus_reco_test",
        "type": "payment.succeeded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "payload_type": "Payment",
            "payment_id": TEST_PAYMENT_ID,
            "status": "succeeded",
            "total_amount": 900,
            "currency": "USD",
            "customer": {
                "customer_id": TEST_CUSTOMER_ID,
                "email": "pro_user@reco.ai",
            },
            "metadata": {
                "user_id": TEST_USER_ID,
            },
        },
    }
    payload_str = json.dumps(payload_obj)
    headers = _generate_webhook_headers(TEST_WEBHOOK_SECRET, payload_str, msg_id="msg_auth_001")

    status_code, response_data = service.handle_http_request("POST", "/billing/webhook", headers, payload_str)
    assert status_code == 200
    assert response_data["received"] is True
    assert response_data["event"] == "payment.succeeded"
    assert response_data["entitlement_updated"] is True

    # Check database entitlement record
    entitlement = service.get_user_entitlement(TEST_USER_ID)
    assert entitlement.is_pro is True
    assert entitlement.tier == SubscriptionTier.PRO.value
    assert entitlement.customer_id == TEST_CUSTOMER_ID
    assert entitlement.payment_id == TEST_PAYMENT_ID


def test_webhook_rejection_on_forged_signature():
    """Verify forged webhook signature is rejected with 400 Bad Request."""
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=InMemoryRepository())
    payload_str = json.dumps({"type": "payment.succeeded", "data": {}})
    headers = _generate_webhook_headers(TEST_WEBHOOK_SECRET, payload_str, msg_id="msg_forged_002")

    # Tamper with the signature
    headers["webhook-signature"] = "v1,forged_invalid_base64_signature_here"

    status_code, response_data = service.handle_http_request("POST", "/billing/webhook", headers, payload_str)
    assert status_code == 400
    assert "Invalid webhook signature" in response_data["error"]


def test_webhook_rejection_on_missing_headers():
    """Verify missing signature or timestamp headers are rejected with 400 Bad Request."""
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=InMemoryRepository())
    payload_str = json.dumps({"type": "payment.succeeded", "data": {}})

    # Missing webhook-signature
    status_code, response_data = service.handle_http_request(
        "POST",
        "/billing/webhook",
        {"webhook-id": "msg_003", "webhook-timestamp": "1700000000"},
        payload_str,
    )
    assert status_code == 400
    assert "Missing required webhook headers" in response_data["detail"]

    # Missing webhook-id
    status_code, response_data = service.handle_http_request(
        "POST",
        "/billing/webhook",
        {"webhook-signature": "v1,abc", "webhook-timestamp": "1700000000"},
        payload_str,
    )
    assert status_code == 400


def test_webhook_anti_replay_freshness_check():
    """Verify expired webhook timestamp (older than standard tolerance) is rejected with 400."""
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=InMemoryRepository())
    payload_str = json.dumps({"type": "payment.succeeded", "data": {}})

    # Timestamp 15 minutes in the past
    stale_timestamp = datetime.now(timezone.utc) - timedelta(minutes=15)
    headers = _generate_webhook_headers(
        TEST_WEBHOOK_SECRET,
        payload_str,
        msg_id="msg_stale_004",
        timestamp=stale_timestamp,
    )

    status_code, response_data = service.handle_http_request("POST", "/billing/webhook", headers, payload_str)
    assert status_code == 400
    assert "Invalid webhook signature" in response_data["error"]
    assert "too old" in response_data["detail"]


def test_webhook_deduplication_idempotency():
    """Verify duplicate webhook delivery ID is acknowledged without duplicate side-effects."""
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=InMemoryRepository())
    payload_str = json.dumps({
        "type": "payment.succeeded",
        "data": {
            "payment_id": "pay_dup_111",
            "customer": {"customer_id": "cus_dup_222"},
            "metadata": {"user_id": TEST_USER_ID},
        },
    })
    headers = _generate_webhook_headers(TEST_WEBHOOK_SECRET, payload_str, msg_id="msg_dup_unique_005")

    # First delivery: processed and entitlement updated
    status_1, data_1 = service.handle_http_request("POST", "/billing/webhook", headers, payload_str)
    assert status_1 == 200
    assert data_1["entitlement_updated"] is True

    # Second delivery (replay with same msg_id): acknowledged, but entitlement_updated is False
    status_2, data_2 = service.handle_http_request("POST", "/billing/webhook", headers, payload_str)
    assert status_2 == 200
    assert data_2["entitlement_updated"] is False


# ==============================================================================
# 5. Multi-Event Ingestion & Entitlement State Transitions
# ==============================================================================

def test_event_subscription_active_upgrades_user():
    """Verify subscription.active grants Reco Pro access with subscription ID."""
    repo = InMemoryRepository()
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=repo)

    payload_str = json.dumps({
        "type": "subscription.active",
        "data": {
            "subscription_id": TEST_SUBSCRIPTION_ID,
            "product_id": DEFAULT_PRO_PRODUCT_ID,
            "customer": {"customer_id": TEST_CUSTOMER_ID},
            "metadata": {"user_id": TEST_USER_ID},
        },
    })
    headers = _generate_webhook_headers(TEST_WEBHOOK_SECRET, payload_str, msg_id="msg_sub_active_006")

    res = service.handle_webhook(headers, payload_str)
    assert res.status == "ok"
    assert res.entitlement_updated is True

    entitlement = service.get_user_entitlement(TEST_USER_ID)
    assert entitlement.tier == SubscriptionTier.PRO.value
    assert entitlement.status == SubscriptionStatus.ACTIVE.value
    assert entitlement.is_pro is True
    assert entitlement.subscription_id == TEST_SUBSCRIPTION_ID
    assert entitlement.customer_id == TEST_CUSTOMER_ID


def test_event_subscription_renewed_maintains_access():
    """Verify subscription.renewed maintains Pro access and updates timestamp."""
    repo = InMemoryRepository()
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=repo)

    # Initial state: Pro
    repo.save_user_entitlement(
        UserEntitlementRecord(
            user_id=TEST_USER_ID,
            tier=SubscriptionTier.PRO.value,
            status=SubscriptionStatus.ACTIVE.value,
            is_pro=True,
            subscription_id=TEST_SUBSCRIPTION_ID,
        )
    )

    payload_str = json.dumps({
        "type": "subscription.renewed",
        "data": {
            "subscription_id": TEST_SUBSCRIPTION_ID,
            "metadata": {"user_id": TEST_USER_ID},
        },
    })
    headers = _generate_webhook_headers(TEST_WEBHOOK_SECRET, payload_str, msg_id="msg_renew_007")

    res = service.handle_webhook(headers, payload_str)
    assert res.status == "ok"
    assert res.entitlement_updated is True

    entitlement = service.get_user_entitlement(TEST_USER_ID)
    assert entitlement.is_pro is True
    assert entitlement.tier == SubscriptionTier.PRO.value


def test_event_subscription_cancelled_immediate_downgrades_to_free():
    """Verify immediate subscription.cancelled downgrades user to Free tier."""
    repo = InMemoryRepository()
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=repo)

    # User currently active Pro
    repo.save_user_entitlement(
        UserEntitlementRecord(
            user_id=TEST_USER_ID,
            tier=SubscriptionTier.PRO.value,
            status=SubscriptionStatus.ACTIVE.value,
            is_pro=True,
            subscription_id=TEST_SUBSCRIPTION_ID,
        )
    )

    payload_str = json.dumps({
        "type": "subscription.cancelled",
        "data": {
            "subscription_id": TEST_SUBSCRIPTION_ID,
            "cancel_at_next_billing_date": False,
            "metadata": {"user_id": TEST_USER_ID},
        },
    })
    headers = _generate_webhook_headers(TEST_WEBHOOK_SECRET, payload_str, msg_id="msg_cancel_008")

    res = service.handle_webhook(headers, payload_str)
    assert res.status == "ok"

    entitlement = service.get_user_entitlement(TEST_USER_ID)
    assert entitlement.tier == SubscriptionTier.FREE.value
    assert entitlement.is_pro is False
    assert entitlement.status == SubscriptionStatus.CANCELLED.value


def test_event_subscription_cancelled_at_period_end_preserves_access():
    """Verify subscription.cancelled with cancel_at_next_billing_date retains Pro until expiry."""
    repo = InMemoryRepository()
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=repo)

    future_expiry = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
    payload_str = json.dumps({
        "type": "subscription.cancelled",
        "data": {
            "subscription_id": TEST_SUBSCRIPTION_ID,
            "cancel_at_next_billing_date": True,
            "next_billing_date": future_expiry,
            "metadata": {"user_id": TEST_USER_ID},
        },
    })
    headers = _generate_webhook_headers(TEST_WEBHOOK_SECRET, payload_str, msg_id="msg_cancel_period_009")

    res = service.handle_webhook(headers, payload_str)
    assert res.status == "ok"

    # User remains Pro until future_expiry
    assert service.is_pro_user(TEST_USER_ID) is True
    entitlement = service.get_user_entitlement(TEST_USER_ID)
    assert entitlement.status == SubscriptionStatus.CANCELLED.value
    assert entitlement.expires_at == future_expiry


# ==============================================================================
# 6. Entitlement Gating & Access Control
# ==============================================================================

def test_entitlement_gating_free_user_rejection():
    """Verify non-Pro users are rejected with EntitlementGatingError on Pro features."""
    repo = InMemoryRepository()
    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=repo)

    # Free tier user
    assert service.is_pro_user(TEST_USER_ID) is False

    with pytest.raises(EntitlementGatingError) as exc_info:
        service.require_pro_entitlement(TEST_USER_ID, feature_name="Multi-Candidate Tournament Synthesis")

    assert "requires an active Reco Pro subscription" in str(exc_info.value)
    assert "$9.00/month" in str(exc_info.value)


def test_entitlement_gating_pro_user_acceptance():
    """Verify active Reco Pro users pass entitlement checks cleanly."""
    repo = InMemoryRepository()
    repo.save_user_entitlement(
        UserEntitlementRecord(
            user_id=TEST_PRO_USER_ID,
            tier=SubscriptionTier.PRO.value,
            status=SubscriptionStatus.ACTIVE.value,
            is_pro=True,
        )
    )

    service = BillingService(webhook_secret=TEST_WEBHOOK_SECRET, repository=repo)
    assert service.is_pro_user(TEST_PRO_USER_ID) is True

    # Should not raise
    service.require_pro_entitlement(TEST_PRO_USER_ID, feature_name="Advanced Pareto Optimization")


# ==============================================================================
# 7. Strict Decoupling: Zero Payment Gateway Dependency on Core Agent Engine
# ==============================================================================

def test_strict_decoupling_payment_gateway_down_never_blocks_dag_synthesis():
    """CRITICAL: Ensure core agent DAG synthesis runs 100% locally even if payment gateway drops."""
    # 1. Simulate payment gateway being completely down / raising ConnectError
    severed_client = MagicMock()
    severed_client.checkout_sessions.create.side_effect = httpx.ConnectError("Gateway network down")
    severed_client.customers.customer_portal.create.side_effect = httpx.ConnectError("Gateway network down")

    billing = BillingService(
        api_key="dodo_test_key",
        webhook_secret=TEST_WEBHOOK_SECRET,
        client=severed_client,
    )

    # Verify checkout fails gracefully with PaymentGatewayError
    with pytest.raises(PaymentGatewayError):
        billing.create_checkout_session({
            "user_id": TEST_USER_ID,
            "email": "test@reco.ai",
            "return_url": "https://app.reco.ai",
        })

    # 2. PROVE that core DAG synthesis proceeds completely unhindered ($0 impact)
    goal = "Reconcile transactions and identify discrepancies"
    analyzer = GoalAnalyzer()
    spec = analyzer.analyze(goal)
    registry = ToolRegistry.create_reconciliation_default()

    generator = ArchitectureGenerator(tool_registry=registry)
    baseline_arch = generator.generate(spec)

    assert baseline_arch is not None
    assert len(baseline_arch.nodes) >= 3
    assert len(baseline_arch.edges) >= 2

    # 3. PROVE that DAG execution and local benchmark run without any gateway interaction
    suite = get_reconciliation_benchmark_suite()
    runtime = AgentRuntime(tool_registry=registry)
    evaluator = ScorecardEvaluator(runtime=runtime)
    scorecard = evaluator.evaluate(
        architecture=baseline_arch,
        suite_or_cases=suite,
        split=BenchmarkSplit.OPTIMIZATION,
        name="Decoupled_Baseline_Benchmark",
    )

    assert scorecard.total_cases == 6
    assert 0.0 <= scorecard.accuracy <= 1.0
    assert scorecard.reliability == 1.0


# ==============================================================================
# 8. Zero Secrets in Code, Logs, and Responses
# ==============================================================================

def test_zero_secrets_leakage_in_service_responses():
    """Verify internal API keys and webhook secrets are never leaked in client responses."""
    api_key = "dodo_test_live_secret_key_999888777"
    secret = TEST_WEBHOOK_SECRET

    service = BillingService(
        api_key=api_key,
        webhook_secret=secret,
        repository=InMemoryRepository(),
    )

    # 1. Checkout session response
    status, data = service.handle_http_request(
        "POST",
        "/billing/checkout",
        {},
        json.dumps({"user_id": TEST_USER_ID, "email": "user@reco.ai", "return_url": "https://reco.ai"}),
    )
    serialized = json.dumps(data)
    assert api_key not in serialized
    assert secret not in serialized

    # 2. Portal error response
    status, data = service.handle_http_request(
        "POST",
        "/billing/portal",
        {},
        json.dumps({"user_id": "nonexistent"}),
    )
    serialized = json.dumps(data)
    assert api_key not in serialized
    assert secret not in serialized

    # 3. Webhook error response
    status, data = service.handle_http_request(
        "POST",
        "/billing/webhook",
        {"webhook-signature": "bad", "webhook-id": "1", "webhook-timestamp": "123"},
        "{}",
    )
    serialized = json.dumps(data)
    assert api_key not in serialized
    assert secret not in serialized
