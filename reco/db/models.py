"""Pydantic data models for Reco persistence entities."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field


class ExperimentRecord(BaseModel):
    """Database model for a Reco engineering experiment."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    goal: str
    domain: str = "reconciliation"
    status: Literal["running", "completed", "failed", "paused"] = "running"
    current_best_version_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolRecord(BaseModel):
    """Database model for an available domain tool."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentVersionRecord(BaseModel):
    """Database model for an immutable agent architecture snapshot."""
    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    version_number: int = Field(..., ge=0)
    architecture: Dict[str, Any] = Field(default_factory=dict)
    prompts: Dict[str, Any] = Field(default_factory=dict)
    tools: List[str] = Field(default_factory=list)
    memory_config: Dict[str, Any] = Field(default_factory=dict)
    model_config_data: Dict[str, Any] = Field(default_factory=dict, alias="model_config")
    parent_version_id: Optional[UUID] = None
    mutation_summary: Optional[str] = None
    status: Literal["draft", "evaluated", "promoted", "rejected"] = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)


class BenchmarkCaseRecord(BaseModel):
    """Database model for a deterministic benchmark scenario."""
    id: UUID = Field(default_factory=uuid4)
    benchmark_name: str = "reconciliation"
    case_code: str
    split: Literal["optimization", "held_out"]
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    input_data: Dict[str, Any]
    ground_truth: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BenchmarkRunRecord(BaseModel):
    """Database model for an aggregate benchmark run evaluation."""
    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    agent_version_id: UUID
    benchmark_name: str = "reconciliation"
    split: Literal["optimization", "held_out", "full"]
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    reliability: float = Field(default=0.0, ge=0.0, le=1.0)
    total_cost_usd: float = 0.0
    latency_ms: int = 0
    status: Literal["running", "completed", "failed"] = "completed"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CaseExecutionRecord(BaseModel):
    """Database model for a case-level execution trace and result."""
    id: UUID = Field(default_factory=uuid4)
    benchmark_run_id: UUID
    benchmark_case_id: UUID
    agent_version_id: UUID
    output: Dict[str, Any] = Field(default_factory=dict)
    expected: Optional[Dict[str, Any]] = None
    success: bool = False
    accuracy_score: float = Field(default=0.0, ge=0.0, le=1.0)
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    tool_events: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FailureDiagnosisRecord(BaseModel):
    """Database model for a failure mode analysis record."""
    id: UUID = Field(default_factory=uuid4)
    case_execution_id: UUID
    category: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    root_cause: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    recommended_mutations: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ImprovementRecord(BaseModel):
    """Database model for version mutation lineage and comparison."""
    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    parent_version_id: Optional[UUID] = None
    candidate_version_id: UUID
    mutation_type: str
    mutation_description: str
    rationale: str
    metrics_before: Dict[str, Any] = Field(default_factory=dict)
    metrics_after: Dict[str, Any] = Field(default_factory=dict)
    accepted: bool = False
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
