"""Data models, request/response structures, and exceptions for Dodo Payments Monetization (Track 1)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import os
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

# Constants & Default Pricing
DEFAULT_PRO_PRODUCT_ID = "pdt_reco_pro"
DEFAULT_PRO_PRICE_CENTS = 900  # $9.00 / month
DEFAULT_PRO_PRICE_USD = 9.00
DEFAULT_PRO_PRODUCT_NAME = "Reco Pro"
DEFAULT_PRO_CURRENCY = "USD"


class SubscriptionTier(str, Enum):
    """User entitlement tiers."""
    FREE = "free"
    PRO = "pro"


class SubscriptionStatus(str, Enum):
    """Lifecycle statuses for subscriptions and entitlements."""
    NONE = "none"
    PENDING = "pending"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


# ==============================================================================
# Domain Exceptions
# ==============================================================================

class BillingError(Exception):
    """Base exception for billing and monetization failures."""


class WebhookVerificationError(BillingError):
    """Raised when HMAC signature verification fails (forged, missing, or expired)."""


class PaymentGatewayError(BillingError):
    """Raised when external payment provider (Dodo Payments) times out or errors."""


class EntitlementGatingError(BillingError):
    """Raised when a non-Pro user attempts to access a Pro-gated feature."""


# ==============================================================================
# Request / Response Models
# ==============================================================================

class CheckoutRequest(BaseModel):
    """Request payload to initiate a hosted Dodo Payments Checkout Session."""

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(description="GoTrue authenticated user UUID")
    email: str = Field(description="Customer billing email address")
    return_url: str = Field(description="URL to redirect user after payment completion")
    product_id: str = Field(
        default_factory=lambda: os.getenv("DODO_PRO_PRODUCT_ID", DEFAULT_PRO_PRODUCT_ID),
        description="Target Dodo Payments product ID (defaults to Reco Pro)"
    )
    quantity: int = Field(default=1, ge=1, description="Product quantity")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata tags")


class CheckoutResponse(BaseModel):
    """Response returned upon generating a Dodo Checkout Session."""

    model_config = ConfigDict(extra="ignore")

    session_id: str = Field(description="Dodo Checkout Session ID")
    checkout_url: str = Field(description="Hosted checkout redirect URL")
    product_id: str = Field(description="Purchased product ID")
    user_id: str = Field(description="Target user ID")
    status: str = Field(default="pending", description="Session state")


class PortalRequest(BaseModel):
    """Request payload to initiate a hosted Customer Portal session."""

    model_config = ConfigDict(extra="ignore")

    user_id: Optional[str] = Field(default=None, description="User UUID to resolve customer ID")
    customer_id: Optional[str] = Field(default=None, description="Direct Dodo customer ID (cus_xxx)")
    return_url: Optional[str] = Field(default=None, description="URL to return to from portal")


class PortalResponse(BaseModel):
    """Response returned upon creating a Customer Portal session."""

    model_config = ConfigDict(extra="ignore")

    portal_url: str = Field(description="Authenticated Customer Portal URL")
    customer_id: str = Field(description="Target customer ID")


class WebhookResult(BaseModel):
    """Result of processing an incoming Dodo Payments webhook."""

    model_config = ConfigDict(extra="ignore")

    status: str = Field(default="ok", description="'ok' or 'ignored'")
    event_type: str = Field(description="Incoming event type (e.g. payment.succeeded)")
    event_id: Optional[str] = Field(default=None, description="Dodo webhook delivery ID")
    user_id: Optional[str] = Field(default=None, description="Affected user UUID")
    entitlement_updated: bool = Field(default=False, description="Whether database record was updated")
    message: Optional[str] = Field(default=None, description="Outcome description or detail")


class UserEntitlement(BaseModel):
    """Persisted record representing a user's subscription entitlement state."""

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(description="GoTrue authenticated user UUID")
    tier: str = Field(default=SubscriptionTier.FREE.value, description="Subscription tier ('free' or 'pro')")
    status: str = Field(default=SubscriptionStatus.NONE.value, description="Lifecycle status")
    is_pro: bool = Field(default=False, description="Computed flag indicating active Pro entitlement")
    customer_id: Optional[str] = Field(default=None, description="Associated Dodo customer ID (cus_xxx)")
    subscription_id: Optional[str] = Field(default=None, description="Associated Dodo subscription ID (sub_xxx)")
    payment_id: Optional[str] = Field(default=None, description="Last successful payment ID (pay_xxx)")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = Field(default=None, description="Expiration ISO timestamp if cancelled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary subscription metadata")
