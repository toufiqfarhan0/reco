"""Billing and monetization service integrating Dodo Payments with Supabase persistence (Step 27)."""

import json
from typing import Any, Dict, Mapping, Optional
from reco.config import Settings, get_settings
from reco.db.supabase_adapter import SupabasePersistenceService, default_supabase_service
from reco.logging import get_logger
from reco.billing.models import (
    FREE_LIMITS,
    PRO_LIMITS,
    PlanTier,
    SubscriptionStatus,
    UserEntitlement,
)

logger = get_logger("billing.service")

try:
    from dodopayments import DodoPayments
except ImportError:
    DodoPayments = None  # type: ignore


class BillingService:
    """Core billing service providing entitlement gating, checkout sessions, and webhook handling."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        supabase_service: Optional[SupabasePersistenceService] = None,
    ):
        self.settings = settings or get_settings()
        self.supabase = supabase_service or default_supabase_service
        self._dodo_client = None
        self._local_subscriptions: Dict[str, Dict[str, Any]] = {}
        self._local_webhook_events: set = set()

    def get_dodo_client(self) -> Optional[DodoPayments]:
        """Return initialized DodoPayments client or None if unconfigured."""
        if self._dodo_client is not None:
            return self._dodo_client

        if not DodoPayments:
            logger.warning("dodopayments package not installed.")
            return None

        if not self.settings.dodo_api_key:
            logger.warning("DODO_PAYMENTS_API_KEY is not configured.")
            return None

        env = "test_mode" if "test" in (self.settings.dodo_environment or "").lower() else "live_mode"
        self._dodo_client = DodoPayments(
            bearer_token=self.settings.dodo_api_key,
            environment=env,
            webhook_key=self.settings.dodo_webhook_secret or None,
        )
        return self._dodo_client

    def get_user_entitlement(
        self, user_id: str, token: Optional[str] = None
    ) -> UserEntitlement:
        """Derive authoritative user entitlement and limits from Supabase/Dodo state."""
        if not user_id:
            return UserEntitlement(
                user_id="",
                plan=PlanTier.FREE,
                status=SubscriptionStatus.FREE,
                limits=FREE_LIMITS,
            )

        try:
            # 1. Check local in-memory fallback first (useful for testing and fast hits)
            sub = self._local_subscriptions.get(user_id)

            # 2. Query Supabase subscriptions table
            if not sub and self.supabase:
                sub = self.supabase.get_user_subscription(user_id, token)

            if sub:
                status_raw = (sub.get("status") or "free").lower()
                plan_raw = (sub.get("plan") or "FREE").upper()

                if status_raw == "active" and plan_raw == "PRO":
                    return UserEntitlement(
                        user_id=user_id,
                        plan=PlanTier.PRO,
                        status=SubscriptionStatus.ACTIVE,
                        limits=PRO_LIMITS,
                        dodo_customer_id=sub.get("dodo_customer_id"),
                        dodo_subscription_id=sub.get("dodo_subscription_id"),
                        product_id=sub.get("product_id") or self.settings.dodo_product_id,
                        current_period_end=sub.get("current_period_end"),
                    )
                else:
                    # Inactive, on_hold, cancelled, or expired Pro subscription
                    norm_status = SubscriptionStatus.FREE
                    try:
                        norm_status = SubscriptionStatus(status_raw)
                    except ValueError:
                        pass

                    return UserEntitlement(
                        user_id=user_id,
                        plan=PlanTier.FREE,
                        status=norm_status,
                        limits=FREE_LIMITS,
                        dodo_customer_id=sub.get("dodo_customer_id"),
                        dodo_subscription_id=sub.get("dodo_subscription_id"),
                        product_id=sub.get("product_id"),
                    )

        except Exception as e:
            logger.warning(f"Error resolving entitlement for user '{user_id}': {e}. Falling back to FREE.")
            return UserEntitlement(
                user_id=user_id,
                plan=PlanTier.FREE,
                status=SubscriptionStatus.FREE,
                limits=FREE_LIMITS,
                is_fallback=True,
            )

        # Default fallback for users with no prior billing record
        return UserEntitlement(
            user_id=user_id,
            plan=PlanTier.FREE,
            status=SubscriptionStatus.FREE,
            limits=FREE_LIMITS,
        )

    def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        user_name: Optional[str] = None,
        return_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a server-side Dodo hosted checkout session tied to authenticated user."""
        if not user_id or not user_email:
            raise ValueError("user_id and user_email are required to create a checkout session.")

        client = self.get_dodo_client()
        if not client:
            raise RuntimeError("Payment gateway temporarily unavailable (Dodo client not configured).")

        product_id = self.settings.dodo_product_id or "pdt_0Nmvzbo4wJETkRyCMAEPt"
        fallback_return_url = return_url or "http://localhost:5173/console?checkout=success"

        try:
            session = client.checkout_sessions.create(
                product_cart=[{"product_id": product_id, "quantity": 1}],
                customer={
                    "email": user_email,
                    "name": user_name or user_email.split("@")[0],
                },
                billing_currency="USD",
                billing_address={
                    "country": "US",
                    "zipcode": "90210",
                },
                minimal_address=True,
                metadata={"user_id": user_id},
                return_url=fallback_return_url,
            )
            return {
                "checkout_url": session.checkout_url,
                "session_id": session.session_id,
            }
        except Exception as e:
            logger.error(f"Failed to create Dodo checkout session: {e}")
            raise RuntimeError("Payment gateway temporarily unavailable. Please try again later.") from e

    def verify_and_process_webhook(
        self, raw_body: bytes, headers: Mapping[str, str]
    ) -> Dict[str, Any]:
        """Verify cryptographic HMAC signature, ensure idempotency, and update subscription state."""
        # 1. Normalize headers (case-insensitive)
        hdr_map = {k.lower(): v for k, v in headers.items()}
        webhook_id = hdr_map.get("webhook-id")
        webhook_signature = hdr_map.get("webhook-signature")
        webhook_timestamp = hdr_map.get("webhook-timestamp")

        if not webhook_id or not webhook_signature or not webhook_timestamp:
            raise ValueError("Missing required Dodo webhook headers: webhook-id, webhook-signature, webhook-timestamp")

        # 2. Check idempotency: if already processed, return immediately with 200
        if webhook_id in self._local_webhook_events:
            return {"status": "already_processed", "webhook_id": webhook_id}

        if self.supabase and self.supabase.is_webhook_processed(webhook_id):
            self._local_webhook_events.add(webhook_id)
            return {"status": "already_processed", "webhook_id": webhook_id}

        # 3. Cryptographic signature verification using official SDK / standardwebhooks
        payload_str = raw_body.decode("utf-8")
        signing_secret = self.settings.dodo_webhook_secret

        if not signing_secret:
            raise ValueError("Server Dodo webhook signing secret is not configured.")

        client = self.get_dodo_client()
        try:
            if client:
                client.webhooks.unwrap(
                    payload_str,
                    headers={
                        "webhook-id": webhook_id,
                        "webhook-signature": webhook_signature,
                        "webhook-timestamp": webhook_timestamp,
                    },
                    key=signing_secret,
                )
            else:
                # Direct standardwebhooks fallback if client is uninitialized
                from standardwebhooks import Webhook
                Webhook(signing_secret).verify(
                    payload_str,
                    {
                        "webhook-id": webhook_id,
                        "webhook-signature": webhook_signature,
                        "webhook-timestamp": webhook_timestamp,
                    },
                )
        except Exception as exc:
            logger.warning(f"Webhook signature verification failed for webhook-id {webhook_id}: {exc}")
            raise ValueError(f"Invalid webhook signature: {exc}") from exc

        # 4. Parse payload safely
        try:
            parsed = json.loads(payload_str)
        except Exception as e:
            raise ValueError(f"Malformed JSON payload: {e}") from e

        event_type = parsed.get("type", "")
        data = parsed.get("data", {})
        metadata = data.get("metadata") or {}
        user_id = metadata.get("user_id")

        # Fallback user identification via customer email if metadata is absent
        customer = data.get("customer") or {}
        dodo_customer_id = customer.get("customer_id")
        dodo_sub_id = data.get("subscription_id") or data.get("payment_id")
        product_id = data.get("product_id") or self.settings.dodo_product_id

        # 5. Process lifecycle event transitions
        target_plan = PlanTier.FREE
        target_status = SubscriptionStatus.FREE

        if event_type in ("subscription.active", "subscription.renewed", "subscription.updated"):
            sub_status = (data.get("status") or "active").lower()
            if sub_status == "active":
                target_plan = PlanTier.PRO
                target_status = SubscriptionStatus.ACTIVE
            elif sub_status in ("on_hold", "past_due"):
                target_plan = PlanTier.FREE
                target_status = SubscriptionStatus.ON_HOLD
            elif sub_status == "cancelled":
                target_plan = PlanTier.FREE
                target_status = SubscriptionStatus.CANCELLED
            elif sub_status in ("expired", "failed"):
                target_plan = PlanTier.FREE
                target_status = SubscriptionStatus.EXPIRED

        elif event_type == "payment.succeeded":
            # Direct payment success for Pro product activates Pro tier
            target_plan = PlanTier.PRO
            target_status = SubscriptionStatus.ACTIVE

        elif event_type == "subscription.cancelled":
            target_plan = PlanTier.FREE
            target_status = SubscriptionStatus.CANCELLED

        elif event_type in ("subscription.expired", "subscription.failed", "payment.failed"):
            target_plan = PlanTier.FREE
            target_status = SubscriptionStatus.EXPIRED if event_type == "subscription.expired" else SubscriptionStatus.FAILED

        elif event_type == "subscription.on_hold":
            target_plan = PlanTier.FREE
            target_status = SubscriptionStatus.ON_HOLD

        # 6. Update user's persistent billing state
        if user_id:
            # Update local memory
            sub_record = {
                "user_id": user_id,
                "plan": target_plan.value,
                "status": target_status.value,
                "product_id": product_id,
                "dodo_customer_id": dodo_customer_id,
                "dodo_subscription_id": dodo_sub_id,
                "current_period_end": data.get("next_billing_date"),
            }
            self._local_subscriptions[user_id] = sub_record

            # Persist to Supabase
            if self.supabase:
                try:
                    self.supabase.upsert_subscription(
                        user_id=user_id,
                        plan=target_plan.value,
                        status=target_status.value,
                        product_id=product_id,
                        dodo_customer_id=dodo_customer_id,
                        dodo_subscription_id=dodo_sub_id,
                        current_period_end=data.get("next_billing_date"),
                    )
                except Exception as pe:
                    logger.warning(f"Failed to persist subscription to Supabase: {pe}")

        # 7. Record idempotency record
        self._local_webhook_events.add(webhook_id)
        if self.supabase:
            try:
                self.supabase.record_webhook_event(
                    webhook_id=webhook_id,
                    event_type=event_type,
                    payload={"type": event_type, "user_id": user_id, "status": target_status.value},
                )
            except Exception as pe:
                logger.warning(f"Failed to record webhook event to Supabase: {pe}")

        return {
            "status": "processed",
            "event_type": event_type,
            "webhook_id": webhook_id,
            "user_id": user_id,
            "plan": target_plan.value,
        }


# Global billing service instance
default_billing_service = BillingService()
