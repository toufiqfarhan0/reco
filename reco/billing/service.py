"""Dodo Payments Billing Service, Webhook Verification & Reco Pro Entitlement Gating (Track 1).

Features:
- Dodo Payments hosted Checkout Sessions generation (POST /billing/checkout).
- Product tier: "Reco Pro" subscription ($9.00/month, $900 cents/mo).
- Hosted Customer Portal session generation (POST /billing/portal).
- Authentic HMAC webhook verification using standardwebhooks.Webhook(secret) (POST /billing/webhook).
- Anti-replay freshness check & 400 Bad Request rejection on forged/missing signature headers.
- Multi-event ingestion: payment.succeeded, subscription.active, subscription.cancelled, subscription.renewed.
- Strict Decoupling: Payment gateway timeout or network drops NEVER block core agent DAG synthesis or local benchmarks.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
import threading
from typing import Any, Dict, Optional, Tuple, Union
import uuid

import httpx
from pydantic import ValidationError

try:
    import standardwebhooks
    STANDARD_WEBHOOKS_AVAILABLE = True
except ImportError:
    STANDARD_WEBHOOKS_AVAILABLE = False
    standardwebhooks = None  # type: ignore

try:
    from dodopayments import DodoPayments
    DODO_SDK_AVAILABLE = True
except ImportError:
    DODO_SDK_AVAILABLE = False
    DodoPayments = None  # type: ignore

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
from reco.db.models import UserEntitlementRecord
from reco.db.repository import ExperimentRepository, InMemoryRepository
from reco.db.supabase import get_repository

logger = logging.getLogger(__name__)

# Known placeholder substrings in sample config files
PLACEHOLDER_SUBSTRINGS = (
    "your_dodo_api_key_here",
    "whsec_your_dodo_webhook_secret_here",
    "your_api_key_here",
    "<your-",
)


def _is_placeholder_credential(val: Optional[str]) -> bool:
    """Return True if credential is empty, unset, or an unconfigured placeholder."""
    if not val or not val.strip():
        return True
    return any(p in val.lower() for p in PLACEHOLDER_SUBSTRINGS)


class BillingService:
    """Enterprise monetization and entitlement service integrated with Dodo Payments."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        environment: str = "test_mode",
        pro_product_id: Optional[str] = None,
        repository: Optional[ExperimentRepository] = None,
        client: Optional[Any] = None,
        http_client: Optional[httpx.Client] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize the Dodo Payments billing service.

        Args:
            api_key: Dodo Payments API key (defaults to DODO_PAYMENTS_API_KEY env).
            webhook_secret: Dodo Payments webhook signing secret (defaults to DODO_WEBHOOK_SECRET
                            or DODO_PAYMENTS_WEBHOOK_KEY env).
            environment: "test_mode" or "live_mode" (defaults to test_mode for safety).
            pro_product_id: Dodo product ID for Reco Pro tier (defaults to DODO_PRO_PRODUCT_ID or 'pdt_reco_pro').
            repository: Multi-tenant database repository for user entitlement persistence.
            client: Injected DodoPayments client (e.g. for testing with mock transport).
            http_client: Custom httpx.Client passed to DodoPayments SDK.
            base_url: Custom base URL override (e.g. for testing).
        """
        self.api_key = api_key or os.getenv("DODO_PAYMENTS_API_KEY")
        self.webhook_secret = (
            webhook_secret
            or os.getenv("DODO_WEBHOOK_SECRET")
            or os.getenv("DODO_PAYMENTS_WEBHOOK_KEY")
        )
        self.environment = environment or os.getenv("DODO_PAYMENTS_ENVIRONMENT", "test_mode")
        self.pro_product_id = pro_product_id or os.getenv("DODO_PRO_PRODUCT_ID", DEFAULT_PRO_PRODUCT_ID)
        self.repository = repository or get_repository()
        self.base_url = base_url

        # In-memory lock & idempotency cache for webhooks
        self._lock = threading.RLock()
        self._processed_webhook_ids: set[str] = set()

        # Initialize DodoPayments SDK client
        if client is not None:
            self.client = client
        elif self.api_key and not _is_placeholder_credential(self.api_key) and DODO_SDK_AVAILABLE:
            init_kwargs: Dict[str, Any] = {
                "bearer_token": self.api_key,
                "environment": self.environment if self.environment in ("test_mode", "live_mode") else "test_mode",
            }
            if self.webhook_secret and not _is_placeholder_credential(self.webhook_secret):
                init_kwargs["webhook_key"] = self.webhook_secret
            if http_client is not None:
                init_kwargs["http_client"] = http_client
            if base_url is not None:
                init_kwargs["base_url"] = base_url
            self.client = DodoPayments(**init_kwargs)
        else:
            self.client = None

    # ==========================================================================
    # 1. Hosted Checkout Sessions (POST /billing/checkout)
    # ==========================================================================

    def create_checkout_session(
        self,
        request: Union[CheckoutRequest, Dict[str, Any]],
    ) -> CheckoutResponse:
        """Create a hosted Checkout Session on Dodo Payments for Reco Pro.

        Args:
            request: CheckoutRequest model or dict with {user_id, email, return_url}.

        Returns:
            CheckoutResponse containing redirect checkout_url and session_id.

        Raises:
            PaymentGatewayError: If payment gateway times out or encounters network failure.
            ValueError: If required request parameters are invalid.
        """
        if isinstance(request, dict):
            try:
                req = CheckoutRequest(**request)
            except ValidationError as exc:
                raise ValueError(f"Invalid checkout request payload: {exc}") from exc
        else:
            req = request

        # If live/test Dodo SDK client is present
        if self.client is not None and hasattr(self.client, "checkout_sessions"):
            try:
                session = self.client.checkout_sessions.create(
                    product_cart=[
                        {
                            "product_id": req.product_id,
                            "quantity": req.quantity,
                        }
                    ],
                    customer={
                        "email": req.email,
                    },
                    return_url=req.return_url,
                    metadata={
                        "user_id": req.user_id,
                        **req.metadata,
                    },
                )
                session_id = getattr(session, "session_id", None) or getattr(session, "id", f"cs_{uuid.uuid4().hex[:12]}")
                checkout_url = getattr(session, "checkout_url", None) or f"https://test.dodopayments.com/checkout/{session_id}"

                return CheckoutResponse(
                    session_id=str(session_id),
                    checkout_url=str(checkout_url),
                    product_id=req.product_id,
                    user_id=req.user_id,
                    status="pending",
                )
            except Exception as exc:
                logger.error("Dodo Payments checkout session creation failed: %s", exc)
                raise PaymentGatewayError(f"Payment gateway error while creating checkout session: {exc}") from exc

        # Graceful fallback for local development or mock mode without live gateway
        session_id = f"cs_reco_{uuid.uuid4().hex[:16]}"
        base = "https://test.dodopayments.com" if self.environment == "test_mode" else "https://live.dodopayments.com"
        checkout_url = f"{base}/checkout/{session_id}?return_url={req.return_url}"

        return CheckoutResponse(
            session_id=session_id,
            checkout_url=checkout_url,
            product_id=req.product_id,
            user_id=req.user_id,
            status="pending",
        )

    # ==========================================================================
    # 2. Customer Portal Sessions (POST /billing/portal)
    # ==========================================================================

    def create_portal_session(
        self,
        request: Union[PortalRequest, Dict[str, Any]],
    ) -> PortalResponse:
        """Create a hosted Customer Portal session for subscription self-management.

        Args:
            request: PortalRequest model or dict with {user_id} or {customer_id}, and optional return_url.

        Returns:
            PortalResponse with authenticated portal_url.

        Raises:
            PaymentGatewayError: If payment gateway times out or encounters network failure.
            BillingError: If user has no associated customer ID.
        """
        if isinstance(request, dict):
            try:
                req = PortalRequest(**request)
            except ValidationError as exc:
                raise ValueError(f"Invalid portal request payload: {exc}") from exc
        else:
            req = request

        customer_id = req.customer_id
        if not customer_id and req.user_id:
            entitlement = self.repository.get_user_entitlement(req.user_id)
            if entitlement and entitlement.customer_id:
                customer_id = entitlement.customer_id
            elif req.user_id in ("usr_demo", "demo_user") or req.user_id.startswith("usr_demo"):
                customer_id = f"cus_demo_{req.user_id}"

        if not customer_id:
            raise BillingError(
                f"Cannot create customer portal: No Dodo Payments customer ID found for user '{req.user_id}'."
            )

        if self.client is not None and hasattr(self.client, "customers") and hasattr(self.client.customers, "customer_portal"):
            try:
                portal_kwargs: Dict[str, Any] = {}
                if req.return_url:
                    portal_kwargs["return_url"] = req.return_url
                portal_session = self.client.customers.customer_portal.create(
                    customer_id,
                    **portal_kwargs,
                )
                portal_url = getattr(portal_session, "link", None) or getattr(portal_session, "portal_url", None)
                if not portal_url and isinstance(portal_session, dict):
                    portal_url = portal_session.get("link") or portal_session.get("portal_url")

                return PortalResponse(
                    portal_url=str(portal_url or f"https://test.dodopayments.com/portal/{customer_id}"),
                    customer_id=customer_id,
                )
            except Exception as exc:
                logger.error("Dodo Payments customer portal creation failed: %s", exc)
                raise PaymentGatewayError(f"Payment gateway error while creating portal session: {exc}") from exc

        # Graceful fallback URL
        base = "https://test.dodopayments.com" if self.environment == "test_mode" else "https://live.dodopayments.com"
        portal_url = f"{base}/portal/{customer_id}"
        if req.return_url:
            portal_url += f"?return_url={req.return_url}"

        return PortalResponse(
            portal_url=portal_url,
            customer_id=customer_id,
        )

    # ==========================================================================
    # 3. Webhook Ingestion & HMAC Verification (POST /billing/webhook)
    # ==========================================================================

    def handle_webhook(
        self,
        headers: Dict[str, str],
        payload: Union[str, bytes],
    ) -> WebhookResult:
        """Verify HMAC signature via standardwebhooks and process payment/subscription events.

        Args:
            headers: HTTP request headers containing webhook-id, webhook-signature, webhook-timestamp.
            payload: Exact raw request body (str or bytes).

        Returns:
            WebhookResult indicating outcome and entitlement update.

        Raises:
            WebhookVerificationError: If HMAC signature is missing, forged, or expired.
        """
        if not STANDARD_WEBHOOKS_AVAILABLE or standardwebhooks is None:
            raise WebhookVerificationError(
                "standardwebhooks package is required for webhook signature verification. "
                "Install with 'pip install standardwebhooks'."
            )

        if not self.webhook_secret or _is_placeholder_credential(self.webhook_secret):
            raise WebhookVerificationError(
                "Webhook verification failed: Dodo Payments webhook secret (DODO_WEBHOOK_SECRET) is unconfigured."
            )

        # Normalize headers to lowercase
        norm_headers = {k.lower(): str(v) for k, v in headers.items()}
        webhook_id = norm_headers.get("webhook-id")
        signature = norm_headers.get("webhook-signature")
        timestamp = norm_headers.get("webhook-timestamp")

        if not webhook_id or not signature or not timestamp:
            raise WebhookVerificationError(
                "Missing required webhook headers. Expected 'webhook-id', 'webhook-signature', and 'webhook-timestamp'."
            )

        # HMAC Verification via standardwebhooks
        try:
            wh = standardwebhooks.Webhook(self.webhook_secret)
            body_bytes = payload if isinstance(payload, bytes) else payload.encode("utf-8")
            verified_payload = wh.verify(body_bytes, norm_headers, json_parse=True)
        except Exception as exc:
            raise WebhookVerificationError(f"Cryptographic webhook signature verification failed: {exc}") from exc

        if not isinstance(verified_payload, dict):
            try:
                verified_payload = json.loads(payload)
            except Exception as exc:
                raise WebhookVerificationError(f"Malformed JSON in webhook body: {exc}") from exc

        # Deduplication check for idempotency
        with self._lock:
            if webhook_id in self._processed_webhook_ids:
                logger.info("Ignoring duplicate webhook delivery: %s", webhook_id)
                return WebhookResult(
                    status="ok",
                    event_type=verified_payload.get("type", "unknown"),
                    event_id=webhook_id,
                    entitlement_updated=False,
                    message="Duplicate webhook delivery already processed.",
                )

        event_type = verified_payload.get("type", "")
        data = verified_payload.get("data", {})

        # Resolve user_id from metadata or customer record
        user_id = (
            data.get("metadata", {}).get("user_id")
            or data.get("customer", {}).get("metadata", {}).get("user_id")
        )
        customer_id = data.get("customer", {}).get("customer_id") or data.get("customer_id")
        subscription_id = data.get("subscription_id")
        payment_id = data.get("payment_id")

        # If user_id wasn't in metadata, attempt resolution via customer_id lookup
        if not user_id and customer_id:
            # Check if any existing entitlement matches this customer_id
            user_id = self._find_user_by_customer_id(customer_id)

        entitlement_updated = False
        message = ""

        # Event Dispatcher
        if event_type == "payment.succeeded":
            # For one-time purchases or subscription initial invoices
            if user_id:
                self._update_user_entitlement(
                    user_id=user_id,
                    tier=SubscriptionTier.PRO.value,
                    status=SubscriptionStatus.ACTIVE.value,
                    is_pro=True,
                    customer_id=customer_id,
                    payment_id=payment_id,
                    subscription_id=subscription_id,
                    metadata={"last_payment_event": event_type, "amount": data.get("total_amount")},
                )
                entitlement_updated = True
                message = f"User '{user_id}' upgraded to Reco Pro via payment.succeeded."

        elif event_type == "subscription.active":
            # Primary event granting subscription access
            if user_id:
                self._update_user_entitlement(
                    user_id=user_id,
                    tier=SubscriptionTier.PRO.value,
                    status=SubscriptionStatus.ACTIVE.value,
                    is_pro=True,
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    payment_id=payment_id,
                    metadata={"subscription_product": data.get("product_id")},
                )
                entitlement_updated = True
                message = f"User '{user_id}' activated Reco Pro subscription '{subscription_id}'."

        elif event_type == "subscription.renewed":
            # Renewal event keeping subscription active
            if user_id:
                self._update_user_entitlement(
                    user_id=user_id,
                    tier=SubscriptionTier.PRO.value,
                    status=SubscriptionStatus.ACTIVE.value,
                    is_pro=True,
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    metadata={"renewed_at": datetime.now(timezone.utc).isoformat()},
                )
                entitlement_updated = True
                message = f"User '{user_id}' renewed Reco Pro subscription."

        elif event_type == "subscription.cancelled":
            # Cancellation event
            if user_id:
                cancel_at_next_billing = bool(data.get("cancel_at_next_billing_date", False))
                next_billing_date = data.get("next_billing_date")

                if cancel_at_next_billing and next_billing_date:
                    # Retain Pro access until period end
                    self._update_user_entitlement(
                        user_id=user_id,
                        tier=SubscriptionTier.PRO.value,
                        status=SubscriptionStatus.CANCELLED.value,
                        is_pro=True,
                        customer_id=customer_id,
                        subscription_id=subscription_id,
                        expires_at=str(next_billing_date),
                        metadata={"cancel_at_next_billing_date": True},
                    )
                    message = f"User '{user_id}' scheduled cancellation at {next_billing_date}."
                else:
                    # Immediate cancellation
                    self._update_user_entitlement(
                        user_id=user_id,
                        tier=SubscriptionTier.FREE.value,
                        status=SubscriptionStatus.CANCELLED.value,
                        is_pro=False,
                        customer_id=customer_id,
                        subscription_id=subscription_id,
                        metadata={"immediate_cancellation": True},
                    )
                    message = f"User '{user_id}' cancelled Reco Pro immediately."
                entitlement_updated = True

        else:
            message = f"Acknowledged event type '{event_type}' with no entitlement modifications."

        # Mark webhook as processed for idempotency
        with self._lock:
            self._processed_webhook_ids.add(webhook_id)

        return WebhookResult(
            status="ok",
            event_type=event_type,
            event_id=webhook_id,
            user_id=user_id,
            entitlement_updated=entitlement_updated,
            message=message,
        )

    # ==========================================================================
    # 4. HTTP Request Dispatcher (POST /billing/checkout, portal, webhook)
    # ==========================================================================

    def handle_http_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Union[str, bytes],
    ) -> Tuple[int, Dict[str, Any]]:
        """Dispatch HTTP requests to appropriate billing handlers.

        Args:
            method: HTTP method (e.g. 'POST').
            path: Target URI path (e.g. '/billing/checkout', '/billing/portal', '/billing/webhook').
            headers: HTTP request headers dictionary.
            body: Request body (string or raw bytes).

        Returns:
            Tuple of (status_code: int, response_json: dict).
        """
        method_upper = method.upper()
        clean_path = path.rstrip("/").lower()
        if not clean_path.startswith("/"):
            clean_path = "/" + clean_path

        # Route 1: POST /billing/checkout
        if clean_path in ("/billing/checkout", "/checkout") and method_upper == "POST":
            try:
                body_dict = json.loads(body) if isinstance(body, (str, bytes)) else dict(body)
                response = self.create_checkout_session(body_dict)
                return 200, response.model_dump()
            except (ValueError, ValidationError) as exc:
                return 400, {"error": "Invalid request", "detail": str(exc)}
            except PaymentGatewayError as exc:
                return 503, {"error": "Payment gateway unavailable", "detail": str(exc)}
            except Exception as exc:
                logger.error("Unhandled checkout error: %s", exc)
                return 500, {"error": "Internal billing error", "detail": str(exc)}

        # Route 2: POST /billing/portal
        if clean_path in ("/billing/portal", "/portal") and method_upper == "POST":
            try:
                body_dict = json.loads(body) if isinstance(body, (str, bytes)) else dict(body)
                response = self.create_portal_session(body_dict)
                return 200, response.model_dump()
            except (ValueError, ValidationError, BillingError) as exc:
                return 400, {"error": "Bad request", "detail": str(exc)}
            except PaymentGatewayError as exc:
                return 503, {"error": "Payment gateway unavailable", "detail": str(exc)}
            except Exception as exc:
                logger.error("Unhandled portal error: %s", exc)
                return 500, {"error": "Internal billing error", "detail": str(exc)}

        # Route 3: POST /billing/webhook
        if clean_path in ("/billing/webhook", "/webhook") and method_upper == "POST":
            try:
                result = self.handle_webhook(headers=headers, payload=body)
                return 200, {
                    "received": True,
                    "event": result.event_type,
                    "status": result.status,
                    "user_id": result.user_id,
                    "entitlement_updated": result.entitlement_updated,
                }
            except WebhookVerificationError as exc:
                logger.warning("Webhook verification failed: %s", exc)
                return 400, {"error": "Invalid webhook signature", "detail": str(exc)}
            except Exception as exc:
                logger.error("Webhook processing error: %s", exc)
                return 500, {"error": "Internal error", "detail": str(exc)}

        return 404, {"error": f"Endpoint not found: {method_upper} {path}"}

    # ==========================================================================
    # 5. Entitlement Gating & Strict Decoupling Guarantees
    # ==========================================================================

    def get_user_entitlement(self, user_id: str) -> UserEntitlementRecord:
        """Fetch current user entitlement record from repository, defaulting to Free tier.

        Zero external network requests to Dodo Payments are made.
        """
        try:
            record = self.repository.get_user_entitlement(user_id)
            if record:
                return record
        except Exception as exc:
            logger.warning("Failed to fetch entitlement for user '%s': %s", user_id, exc)

        # Default fallback is Free tier
        return UserEntitlementRecord(
            user_id=user_id,
            tier=SubscriptionTier.FREE.value,
            status=SubscriptionStatus.NONE.value,
            is_pro=False,
        )

    def is_pro_user(self, user_id: str) -> bool:
        """Check if a user has an active Reco Pro subscription.

        Strictly Decoupled: NEVER makes remote API calls to Dodo Payments.
        """
        entitlement = self.get_user_entitlement(user_id)
        if not entitlement.is_pro:
            return False

        # If expires_at is set, verify it hasn't lapsed
        if entitlement.expires_at:
            try:
                exp_dt = datetime.fromisoformat(entitlement.expires_at.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > exp_dt:
                    return False
            except Exception:
                pass

        return entitlement.tier == SubscriptionTier.PRO.value

    def require_pro_entitlement(self, user_id: str, feature_name: str = "Reco Pro") -> None:
        """Guard method raising EntitlementGatingError if the user is not on Reco Pro."""
        if not self.is_pro_user(user_id):
            raise EntitlementGatingError(
                f"Feature '{feature_name}' requires an active Reco Pro subscription ($9.00/month). "
                f"Upgrade at /billing/checkout."
            )

    # ==========================================================================
    # Private Helpers
    # ==========================================================================

    def _find_user_by_customer_id(self, customer_id: str) -> Optional[str]:
        """Search repository for user associated with a given Dodo customer ID."""
        if isinstance(self.repository, InMemoryRepository):
            for uid, ent in self.repository._entitlements.items():
                if ent.customer_id == customer_id:
                    return uid
        return None

    def _update_user_entitlement(
        self,
        user_id: str,
        tier: str,
        status: str,
        is_pro: bool,
        customer_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UserEntitlementRecord:
        """Create or update a UserEntitlementRecord in the database."""
        now = datetime.now(timezone.utc).isoformat()
        existing = self.repository.get_user_entitlement(user_id)

        record = UserEntitlementRecord(
            user_id=user_id,
            tier=tier,
            status=status,
            is_pro=is_pro,
            customer_id=customer_id or (existing.customer_id if existing else None),
            subscription_id=subscription_id or (existing.subscription_id if existing else None),
            payment_id=payment_id or (existing.payment_id if existing else None),
            created_at=existing.created_at if existing else now,
            updated_at=now,
            expires_at=expires_at or (existing.expires_at if existing else None),
            metadata={**(existing.metadata if existing else {}), **(metadata or {})},
        )
        return self.repository.save_user_entitlement(record)
