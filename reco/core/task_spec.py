"""Strongly typed TaskSpecification and decomposition models for Reco."""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class Capability(str, Enum):
    """Controlled, domain-neutral taxonomy of agent capabilities."""
    RETRIEVAL = "retrieval"
    STRUCTURED_LOOKUP = "structured_lookup"
    CALCULATION = "calculation"
    COMPARISON = "comparison"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    TRANSFORMATION = "transformation"
    REASONING = "reasoning"
    VERIFICATION = "verification"
    SUMMARIZATION = "summarization"
    ANOMALY_DETECTION = "anomaly_detection"
    EVIDENCE_COLLECTION = "evidence_collection"
    DECISION_MAKING = "decision_making"


class ToolRecommendation(BaseModel):
    """Structured suggestion of an available tool with relevance rationale."""
    tool_name: str = Field(..., description="Machine name of an existing tool in the catalog")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance rating from 0.0 to 1.0")
    reason: str = Field(..., description="Explanation of why this tool is recommended")
    required: bool = Field(default=False, description="Whether this tool is essential for goal completion")
    confidence: float = Field(default=0.80, ge=0.0, le=1.0, description="Confidence in the recommendation")

    model_config = ConfigDict(extra="ignore")


class EvaluatorSpecification(BaseModel):
    """Benchmark or evaluator criteria the synthesized workflow must satisfy."""
    required_output_properties: List[str] = Field(default_factory=list, description="Mandatory output dictionary keys")
    correctness_criteria: List[str] = Field(default_factory=list, description="Rules determining task success")
    constraint_checks: List[str] = Field(default_factory=list, description="Forbidden states or boundary invariants")
    evidence_requirements: List[str] = Field(default_factory=list, description="Evidence or rationale required in output")
    threshold_conditions: Dict[str, float] = Field(default_factory=dict, description="Target metrics (accuracy, etc.)")

    model_config = ConfigDict(extra="ignore")


class Subtask(BaseModel):
    """A granular functional unit in the decomposed task execution plan."""
    id: str = Field(..., description="Unique subtask identifier within the specification (e.g., 'subtask_1')")
    description: str = Field(..., description="Summary of work to be performed")
    objective: str = Field(..., description="Target outcome or deliverable of this subtask")
    required_capabilities: List[Capability] = Field(
        default_factory=list,
        description="Capabilities required to execute this subtask",
    )
    preferred_tools: List[str] = Field(
        default_factory=list,
        description="Names of tools from the catalog recommended for this subtask",
    )
    expected_input: Dict[str, Any] = Field(default_factory=dict, description="Expected input fields and types")
    expected_output: Dict[str, Any] = Field(default_factory=dict, description="Expected output structure")
    verification_needed: bool = Field(default=False, description="Whether this step requires verification/audit")
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of prior subtask IDs that must complete before this subtask",
    )

    model_config = ConfigDict(extra="ignore")


class TaskSpecification(BaseModel):
    """Machine-readable, domain-agnostic task specification consumed by the Architecture Generator."""
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    original_goal: str = Field(..., description="Verbatim raw user goal")
    normalized_goal: str = Field(..., description="Cleaned, normalized goal statement")
    domain: str = Field(default="general", description="Informational domain tag ('finance', 'research', 'data', 'coding', 'general')")
    objective: str = Field(..., description="Core actionable deliverable")
    subtasks: List[Subtask] = Field(default_factory=list, description="Ordered functional subtasks")
    required_capabilities: List[Capability] = Field(default_factory=list, description="All required capabilities")
    available_tool_ids: List[str] = Field(default_factory=list, description="All tool names provided in the catalog")
    suggested_tool_bindings: List[ToolRecommendation] = Field(
        default_factory=list,
        description="Recommended tool bindings (must be a subset of available_tool_ids)",
    )
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Expected workflow input schemas")
    expected_outputs: Dict[str, Any] = Field(default_factory=dict, description="Target workflow output schemas")
    constraints: List[str] = Field(default_factory=list, description="Behavioral, format, or budget constraints")
    verification_requirements: List[str] = Field(default_factory=list, description="Validation or sanity check rules")
    risk_level: Literal["low", "medium", "high"] = Field(default="low", description="Operational risk level")
    side_effect_requirements: bool = Field(default=False, description="Whether the goal requires external state mutations")
    ambiguity_flags: List[str] = Field(default_factory=list, description="Detected underspecifications or missing parameters")
    requires_clarification: bool = Field(default=False, description="Whether execution should pause for clarification")
    confidence: float = Field(default=0.80, ge=0.0, le=1.0, description="Heuristic confidence score of the analysis")
    evaluator_requirements: Optional[EvaluatorSpecification] = None
    required_tools: List[str] = Field(default_factory=list, description="Explicit list of mandatory tool names")
    requires_verification: bool = Field(default=False, description="Whether this task mandates an audit/verification step")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")

    @property
    def evaluator(self) -> Optional[EvaluatorSpecification]:
        """Convenience accessor matching evaluator_requirements."""
        return self.evaluator_requirements

    def validate_tool_integrity(self) -> None:
        """Enforce that every suggested tool actually exists in available_tool_ids."""
        available_set = set(self.available_tool_ids)
        for binding in self.suggested_tool_bindings:
            if binding.tool_name not in available_set:
                raise ValueError(
                    f"Fabricated tool detected: '{binding.tool_name}' is not in available_tool_ids: {self.available_tool_ids}"
                )
        for subtask in self.subtasks:
            for tool in subtask.preferred_tools:
                if tool not in available_set:
                    raise ValueError(
                        f"Subtask '{subtask.id}' references tool '{tool}' which is not in available_tool_ids."
                    )
