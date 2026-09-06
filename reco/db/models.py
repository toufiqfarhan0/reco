"""Data models and exception definitions for Supabase PostgreSQL persistence (Track 1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ImmutabilityError(Exception):
    """Raised when an operation attempts to overwrite or modify an immutable historical record."""


class UserIsolationError(Exception):
    """Raised when an operation violates multi-tenant user isolation boundaries."""


class AuthenticationError(Exception):
    """Raised when GoTrue JWT verification fails or Authorization header is invalid."""


class ExperimentRecord(BaseModel):
    """Persisted record representing an autonomous optimization session."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(description="GoTrue authenticated user UUID")
    name: str = Field(description="Experiment label")
    domain: str = Field(default="financial_reconciliation")
    status: str = Field(default="running")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ArchitectureRecord(BaseModel):
    """Persisted record representing an immutable DAG agent architecture."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique architecture ID (e.g., Agent_Reconciliation_V0)")
    experiment_id: str = Field(description="Associated experiment UUID")
    user_id: str = Field(description="GoTrue authenticated user UUID")
    name: str = Field(description="Human-readable architecture name")
    generation: int = Field(default=0, description="Mutation lineage generation (0 = baseline)")
    definition: Dict[str, Any] = Field(description="Serialized nodes, edges, task_spec, complexity")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BenchmarkRunRecord(BaseModel):
    """Immutable evaluation scorecard of an architecture on a specific benchmark partition."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = Field(description="Associated experiment UUID")
    architecture_id: str = Field(description="Target architecture ID evaluated")
    user_id: str = Field(description="GoTrue authenticated user UUID")
    split: str = Field(description="Benchmark partition ('optimization', 'held-out', 'full')")
    total_cases: int = Field(default=0)
    passed_cases: int = Field(default=0)
    failed_cases: int = Field(default=0)
    accuracy: float = Field(default=0.0)
    reliability: float = Field(default=0.0)
    latency_ms: float = Field(default=0.0)
    cost_usd: float = Field(default=0.0)
    case_results: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EvaluationRecord(BaseModel):
    """Immutable side-by-side Pareto comparison between baseline and candidate variants."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = Field(description="Associated experiment UUID")
    user_id: str = Field(description="GoTrue authenticated user UUID")
    baseline_architecture_id: str = Field(description="Baseline architecture ID")
    candidate_architecture_id: str = Field(description="Mutated candidate architecture ID")
    comparison: Dict[str, Any] = Field(description="ScorecardComparison metrics and badges")
    verdict: str = Field(description="Outcome verdict: PARETO_DOMINANT, TRADEOFF, REGRESSION, NEUTRAL")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MutationRecord(BaseModel):
    """Immutable record of an architectural mutation applied between generations."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = Field(description="Associated experiment UUID")
    user_id: str = Field(description="GoTrue authenticated user UUID")
    parent_architecture_id: str = Field(description="Parent architecture ID")
    child_architecture_id: str = Field(description="Mutated child architecture ID")
    generation: int = Field(description="Target generation number")
    mutator_name: str = Field(description="Name of applied mutator operator")
    diagnostic_category: Optional[str] = Field(default=None, description="Diagnosed failure category addressed")
    mutation_diff: Dict[str, Any] = Field(description="Structured diff and visual diff")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TraceRecord(BaseModel):
    """Persisted record of an end-to-end Neatlogs distributed execution trace."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Neatlogs trace ID (e.g., tr_neat_xxx)")
    experiment_id: str = Field(description="Associated experiment UUID")
    architecture_id: Optional[str] = Field(default=None)
    user_id: str = Field(description="GoTrue authenticated user UUID")
    status: str = Field(default="success")
    total_duration_ms: float = Field(default=0.0)
    total_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    spans: List[Dict[str, Any]] = Field(default_factory=list)
    deep_link_url: Optional[str] = Field(default=None)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserEntitlementRecord(BaseModel):
    """Persisted record representing a user's subscription entitlement tier."""

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(description="GoTrue authenticated user UUID")
    tier: str = Field(default="free", description="Entitlement tier: 'free' or 'pro'")
    status: str = Field(default="none", description="Status: 'active', 'cancelled', 'expired', 'none'")
    is_pro: bool = Field(default=False, description="Whether user has active Pro access")
    customer_id: Optional[str] = Field(default=None, description="Dodo Payments customer ID")
    subscription_id: Optional[str] = Field(default=None, description="Dodo Payments subscription ID")
    payment_id: Optional[str] = Field(default=None, description="Last successful payment ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = Field(default=None)

