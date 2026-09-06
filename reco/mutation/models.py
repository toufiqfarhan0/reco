"""Data models for candidate mutations, agent version candidates, and optimization outcomes."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field

from reco.db.models import AgentVersionRecord, ImprovementRecord
from reco.diagnostics.models import RootCauseDiagnosis
from reco.diagnostics.taxonomy import MutationType
from reco.engine.generator import ArchitectureValidationResult
from reco.engine.models import GraphDefinition
from reco.evaluators.comparison import PromotionAssessment, ScorecardComparison
from reco.evaluators.scorecard import Scorecard


class CandidateEvaluationRecord(BaseModel):
    """Evaluation record of a single mutation candidate within an optimization generation."""
    candidate_id: UUID = Field(default_factory=uuid4)
    name: str = Field(default="Candidate A", description="Human-readable candidate label (e.g. Candidate A, B, C)")
    mutation_type: str = Field(..., description="Type of mutation applied")
    target: str = Field(..., description="Target node, edge, or graph element")
    proposed_change: Dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(default="")
    diagnostics_source_ids: List[UUID] = Field(default_factory=list)
    scorecard: Optional[Scorecard] = None
    comparison: Optional[ScorecardComparison] = None
    status: str = Field(default="pending", description="'selected', 'rejected', 'invalid', 'tradeoff'")
    rejection_reason: Optional[str] = None
    is_valid: bool = Field(default=True)
    fingerprint: Optional[str] = None
    model_calls: int = Field(default=0)
    tool_calls: int = Field(default=0)
    tokens_in: int = Field(default=0)
    tokens_out: int = Field(default=0)
    cost_usd: float = Field(default=0.0)
    latency_ms: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MutationCandidate(BaseModel):
    """Declarative specification of a candidate mutation to be applied to an agent graph."""
    candidate_id: UUID = Field(default_factory=uuid4)
    mutation_type: MutationType = Field(..., description="Target architectural mutation axis")
    target: str = Field(..., description="Target node ID, edge identifier, tool name, or graph property")
    proposed_change: Dict[str, Any] = Field(default_factory=dict, description="Concrete payload of structural or prompt changes")
    rationale: str = Field(..., description="Diagnostic justification grounding this mutation")
    source_diagnosis_ids: List[UUID] = Field(default_factory=list, description="IDs of source diagnoses motivating this mutation")
    expected_effect: str = Field(..., description="Anticipated performance, cost, speed, or accuracy improvement")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in mutation efficacy")
    risk_level: str = Field(default="low", description="'low', 'medium', 'high'")
    parent_version_id: Optional[UUID] = Field(default=None, description="Identifier of the version being mutated")
    is_valid: bool = Field(default=True, description="Whether static validation succeeded on this candidate")
    mutated_graph: Optional[GraphDefinition] = Field(default=None, description="Materialized graph after mutation")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentVersionCandidate(BaseModel):
    """An immutable candidate agent architecture snapshot produced by applying a MutationCandidate."""
    candidate_id: UUID = Field(default_factory=uuid4)
    parent_version_id: UUID = Field(..., description="Immutable parent version ID (e.g., V0)")
    version_number: int = Field(..., ge=0, description="Incremented version index (e.g., 1)")
    graph: GraphDefinition = Field(..., description="Mutated agent architecture graph definition")
    mutation: MutationCandidate = Field(..., description="The applied candidate mutation")
    validation_result: Optional[ArchitectureValidationResult] = None
    is_valid: bool = Field(default=False, description="True if static pre-flight validation succeeded")
    rejection_reason: Optional[str] = Field(default=None, description="Explicit failure reason if validation failed")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_agent_version_record(self, experiment_id: UUID, status: str = "draft") -> AgentVersionRecord:
        """Create an immutable AgentVersionRecord for database persistence."""
        prompts = {
            node_id: node.system_prompt
            for node_id, node in self.graph.nodes.items()
        }
        tools_set = set()
        for node in self.graph.nodes.values():
            for tool_name in node.tools:
                tools_set.add(tool_name)

        return AgentVersionRecord(
            id=self.candidate_id,
            experiment_id=experiment_id,
            version_number=self.version_number,
            architecture=self.graph.model_dump(mode="json"),
            prompts=prompts,
            tools=sorted(list(tools_set)),
            memory_config={},
            model_config_data={"generation": "mutation_engine", "mutation_type": self.mutation.mutation_type.value},
            parent_version_id=self.parent_version_id,
            mutation_summary=f"[{self.mutation.mutation_type.value}] on '{self.mutation.target}': {self.mutation.rationale}",
            status=status,  # type: ignore
            created_at=self.created_at,
        )


class OptimizationConfig(BaseModel):
    """Configuration controls and safety boundaries for autonomous multi-generation optimization."""
    max_generations: int = Field(default=3, ge=1, le=10, description="Maximum number of evolutionary generations")
    max_candidates_per_generation: int = Field(default=3, ge=1, le=3, description="Candidates synthesized per generation (max 3)")
    max_candidate_benchmark_cases: int = Field(default=36, ge=1, description="Maximum total candidate benchmark test case evaluations allowed per generation")
    max_total_model_calls: Optional[int] = Field(default=None, ge=1, description="Global ceiling on model invocations across all runs")
    max_total_cost_usd: Optional[float] = Field(default=None, ge=0.0, description="Global monetary spend ceiling")
    stop_on_no_improvement: bool = Field(default=True, description="Stop evolution immediately if no candidate improves current parent")
    detect_cycles: bool = Field(default=True, description="Detect and reject repeated architecture states and mutation cycles")
    run_held_out_at_termination: bool = Field(default=True, description="Run held-out split evaluation at final termination for promotion gate")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class OptimizationGeneration(BaseModel):
    """Immutable audit record of a single evolutionary generation transition."""
    generation_number: int = Field(..., ge=0, description="Generation index (e.g. 1, 2, ...)")
    parent_version_id: UUID = Field(..., description="ID of the parent agent version for this generation")
    candidate_version_ids: List[UUID] = Field(default_factory=list, description="IDs of all candidates evaluated in this round")
    selected_version_id: Optional[UUID] = Field(default=None, description="Chosen winner version ID, or None if no candidate selected")
    optimization_scorecard: Optional[Scorecard] = Field(default=None, description="Scorecard of the selected candidate or parent")
    diagnoses: List[RootCauseDiagnosis] = Field(default_factory=list, description="Diagnoses extracted from parent's optimization failures")
    mutations: List[MutationCandidate] = Field(default_factory=list, description="Mutation proposals synthesized for this round")
    candidates: List[CandidateEvaluationRecord] = Field(default_factory=list, description="Structured record of all candidates evaluated in this generation")
    comparison: Optional[Any] = Field(default=None, description="Scorecard comparison of selected candidate against parent")
    decision: str = Field(default="pending", description="'selected', 'no_improvement', 'repeated_architecture', 'no_candidates', 'tradeoff'")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class OptimizationResult(BaseModel):
    """Complete outcome of multi-generation autonomous optimization."""
    experiment_id: UUID = Field(default_factory=uuid4)
    initial_version_id: Optional[UUID] = Field(default=None, description="Starting agent version ID (e.g. V0)")
    final_version_id: Optional[UUID] = Field(default=None, description="Winning or final agent version ID")
    generations: List[OptimizationGeneration] = Field(default_factory=list, description="Audit trail of all generation iterations")
    termination_reason: str = Field(default="completed", description="Reason for stopping evolution")
    optimization_history: List[Dict[str, Any]] = Field(default_factory=list, description="Chronological timeline of generation transitions")
    held_out_result: Optional[Scorecard] = Field(default=None, description="Final held-out split scorecard (evaluated ONLY at gate)")
    final_promotion_assessment: Optional[PromotionAssessment] = Field(default=None, description="Promotion assessment on held-out split")
    
    # Telemetry and Resource Accounting
    total_model_calls: int = Field(default=0, description="Total LLM model calls consumed across all runs")
    total_tool_calls: int = Field(default=0, description="Total tool calls executed across all runs")
    total_tokens_in: int = Field(default=0, description="Total prompt tokens consumed")
    total_tokens_out: int = Field(default=0, description="Total completion tokens consumed")
    total_cost_usd: float = Field(default=0.0, description="Total dollar cost incurred across all runs")

    # Multi-Candidate Evaluations
    candidate_evaluations: List[CandidateEvaluationRecord] = Field(default_factory=list, description="Full candidate evaluations across generations")

    # Backward-compatible fields for single-step MutationEngine compatibility
    parent_version_id: Optional[UUID] = Field(default=None)
    candidates_generated: int = Field(default=0)
    candidates_evaluated: int = Field(default=0)
    candidates: List[AgentVersionCandidate] = Field(default_factory=list)
    best_candidate: Optional[AgentVersionCandidate] = Field(default=None)
    promotion_assessment: Optional[PromotionAssessment] = Field(default=None)
    improvement_record: Optional[ImprovementRecord] = None
    baseline_scorecard: Optional[Scorecard] = None
    optimization_scorecard: Optional[Scorecard] = None
    held_out_scorecard: Optional[Scorecard] = Field(default=None)
    summary: str = Field(default="", description="Human-readable optimization outcome narrative")

    # Neatlogs Cloud Observability Telemetry
    trace_id: Optional[str] = Field(default=None, description="Neatlogs 32-character hex trace ID")
    neatlogs_trace_url: Optional[str] = Field(default=None, description="Direct URL to inspect live trace on Neatlogs Cloud")

    model_config = ConfigDict(arbitrary_types_allowed=True)

