"""Domain models for billing, subscriptions, entitlements, and usage limits (Step 27)."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PlanTier(str, Enum):
    """Available Reco subscription tiers."""
    FREE = "FREE"
    PRO = "PRO"


class SubscriptionStatus(str, Enum):
    """Normalized subscription lifecycle status."""
    FREE = "free"
    PENDING = "pending"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


class UsageLimits(BaseModel):
    """Configuration-driven usage limits per subscription tier."""
    max_optimization_runs: int = Field(..., description="Max optimization jobs allowed")
    max_candidates: int = Field(..., description="Max candidate architectures per generation")
    max_generations: int = Field(..., description="Max evolutionary hill-climbing generations allowed")


# Default limit policies
FREE_LIMITS = UsageLimits(
    max_optimization_runs=3,
    max_candidates=2,
    max_generations=1,
)

PRO_LIMITS = UsageLimits(
    max_optimization_runs=100,
    max_candidates=5,
    max_generations=5,
)


class UserEntitlement(BaseModel):
    """Stable internal representation of a user's entitlement and limits."""
    user_id: str
    plan: PlanTier = PlanTier.FREE
    status: SubscriptionStatus = SubscriptionStatus.FREE
    limits: UsageLimits = Field(default_factory=lambda: FREE_LIMITS)
    is_fallback: bool = Field(default=False, description="True if derived via fallback due to gateway/DB error")
    dodo_customer_id: Optional[str] = None
    dodo_subscription_id: Optional[str] = None
    product_id: Optional[str] = None
    current_period_end: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Response returned when a Dodo hosted checkout session is generated."""
    checkout_url: str
    session_id: str


class WebhookProcessResponse(BaseModel):
    """Response returned after webhook event processing."""
    status: str
    event_type: Optional[str] = None
    webhook_id: Optional[str] = None
    detail: Optional[str] = None
