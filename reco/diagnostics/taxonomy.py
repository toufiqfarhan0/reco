"""12-Category Failure Diagnostics Taxonomy and Structured Telemetry Models.

Provides deterministic classification of agent execution failures into root causes
distinct from intermediate symptoms, with targeted remediation suggestions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class FailureCategory(str, Enum):
    """The 12-Category Failure Diagnostics Taxonomy for Track 1 Agent Engineering."""

    PROMPT_AMBIGUITY = "prompt_ambiguity"
    TOOL_SELECTION_ERROR = "tool_selection_error"
    TOOL_PARAMETER_ERROR = "tool_parameter_error"
    SCHEMA_VIOLATION = "schema_violation"
    VERIFICATION_MISS = "verification_miss"
    ROUTING_MISDIRECT = "routing_misdirect"
    CONTEXT_OVERFLOW = "context_overflow"
    RETRY_EXHAUSTION = "retry_exhaustion"
    MODEL_CAPABILITY_LIMIT = "model_capability_limit"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    STATE_CORRUPTION = "state_corruption"
    UNHANDLED_EXCEPTION = "unhandled_exception"


CATEGORY_DESCRIPTIONS: Dict[FailureCategory, str] = {
    FailureCategory.PROMPT_AMBIGUITY: (
        "Node prompt or configuration lacks domain constraints, clear formatting directives, "
        "or sufficient context, leading to ambiguous deduction or malformed outputs."
    ),
    FailureCategory.TOOL_SELECTION_ERROR: (
        "Graph lacks an appropriate tool, chose an ineffective tool, or selected an under-capable "
        "tool variant unable to handle domain-specific inputs (e.g., format variations)."
    ),
    FailureCategory.TOOL_PARAMETER_ERROR: (
        "Tool invocation failed schema validation due to missing required arguments, wrong parameter "
        "types, or malformed input payload from upstream nodes."
    ),
    FailureCategory.SCHEMA_VIOLATION: (
        "Final or intermediate output payload failed to satisfy structural JSON schema contracts or "
        "omitted required ground-truth keys."
    ),
    FailureCategory.VERIFICATION_MISS: (
        "The verification guardrail approved an incorrect result, or no verification stage existed "
        "to intercept and flag discrepancy mismatches prior to output delivery."
    ),
    FailureCategory.ROUTING_MISDIRECT: (
        "DAG topological routing error, missing dependency edges, or disconnected node data flow "
        "bypassed critical processing or validation nodes."
    ),
    FailureCategory.CONTEXT_OVERFLOW: (
        "Intermediate memory state or input payload exceeded context token limits or byte size constraints."
    ),
    FailureCategory.RETRY_EXHAUSTION: (
        "Repeated node execution retries on a brittle or flaky operation exhausted the configured "
        "retry budget without recovery."
    ),
    FailureCategory.MODEL_CAPABILITY_LIMIT: (
        "Complex reasoning or multi-hop logic failure where the model or reasoning engine failed to "
        "synthesize subtle edge cases despite having valid tool outputs."
    ),
    FailureCategory.TIMEOUT_EXCEEDED: (
        "Total wall-clock latency or individual node runtime exceeded the maximum latency budget."
    ),
    FailureCategory.STATE_CORRUPTION: (
        "Execution state store suffered data corruption, lost intermediate step keys, or experienced "
        "an invalid state transition."
    ),
    FailureCategory.UNHANDLED_EXCEPTION: (
        "Uncaught runtime exception, syntax error, or unhandled system crash during node execution."
    ),
}

CATEGORY_DEFAULT_MUTATORS: Dict[FailureCategory, str] = {
    FailureCategory.PROMPT_AMBIGUITY: "PromptMutator",
    FailureCategory.TOOL_SELECTION_ERROR: "ToolAssignmentMutator",
    FailureCategory.TOOL_PARAMETER_ERROR: "PromptMutator",
    FailureCategory.SCHEMA_VIOLATION: "PromptMutator",
    FailureCategory.VERIFICATION_MISS: "VerifierNodeMutator",
    FailureCategory.ROUTING_MISDIRECT: "TopologyMutator",
    FailureCategory.CONTEXT_OVERFLOW: "PromptMutator",
    FailureCategory.RETRY_EXHAUSTION: "RetryPolicyMutator",
    FailureCategory.MODEL_CAPABILITY_LIMIT: "TopologyMutator",
    FailureCategory.TIMEOUT_EXCEEDED: "RetryPolicyMutator",
    FailureCategory.STATE_CORRUPTION: "TopologyMutator",
    FailureCategory.UNHANDLED_EXCEPTION: "RetryPolicyMutator",
}


class FailureDiagnostic(BaseModel):
    """Structured diagnostic isolating root cause from symptoms for a single failure."""

    case_id: str = Field(description="Identifier of the failed benchmark test case")
    category: FailureCategory = Field(description="Taxonomy classification of the failure root cause")
    root_cause: str = Field(description="Isolated underlying root cause explanation")
    symptoms: List[str] = Field(default_factory=list, description="Observable intermediate symptoms")
    remedy_suggestion: str = Field(description="Actionable remediation recommendation")
    target_node_id: Optional[str] = Field(default=None, description="Graph node associated with root cause")
    recommended_mutator: Optional[str] = Field(
        default=None,
        description="Name of the targeted mutation operator to resolve this failure"
    )
    confidence: float = Field(default=1.0, description="Diagnostic classification confidence (0.0 to 1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Auxiliary diagnostic telemetry")


class DiagnosticReport(BaseModel):
    """Aggregated failure diagnosis for an architecture across benchmark evaluation."""

    architecture_id: str = Field(description="Evaluated agent architecture identifier")
    total_cases: int = Field(description="Total number of evaluated benchmark test cases")
    passed_cases: int = Field(description="Number of passing benchmark test cases")
    failed_cases: int = Field(description="Number of failed benchmark test cases")
    failure_diagnostics: List[FailureDiagnostic] = Field(
        default_factory=list,
        description="List of isolated root-cause diagnostics for failed cases"
    )
    category_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Frequency count of failures per taxonomy category"
    )
    summary: str = Field(default="", description="Executive diagnostic summary")

    def has_category(self, category: Union[FailureCategory, str]) -> bool:
        """Check if any failed case was classified under the given category."""
        cat_val = category.value if isinstance(category, FailureCategory) else str(category).lower()
        return self.category_counts.get(cat_val, 0) > 0

    def get_by_category(self, category: Union[FailureCategory, str]) -> List[FailureDiagnostic]:
        """Retrieve all failure diagnostics matching a specific category."""
        cat_enum = category if isinstance(category, FailureCategory) else FailureCategory(category)
        return [d for d in self.failure_diagnostics if d.category == cat_enum]

    def get_case_diagnostic(self, case_id: str) -> Optional[FailureDiagnostic]:
        """Retrieve diagnostic for a specific test case ID."""
        for d in self.failure_diagnostics:
            if d.case_id == case_id:
                return d
        return None

    def to_markdown(self) -> str:
        """Render a markdown summary table of the diagnostic report."""
        lines = [
            f"### Failure Diagnostic Report: Architecture `{self.architecture_id}`",
            f"**Evaluation Summary:** {self.passed_cases}/{self.total_cases} passed, {self.failed_cases} failed.",
            "",
            "#### Root-Cause Category Distribution",
            "| Taxonomy Category | Failure Count | Recommended Mutator |",
            "| :--- | :--- | :--- |",
        ]

        if not self.category_counts:
            lines.append("| *(None - All tests passed)* | 0 | N/A |")
        else:
            for cat_str, count in sorted(self.category_counts.items(), key=lambda x: -x[1]):
                try:
                    cat_enum = FailureCategory(cat_str)
                    mutator = CATEGORY_DEFAULT_MUTATORS.get(cat_enum, "BaseMutator")
                except ValueError:
                    mutator = "N/A"
                lines.append(f"| `{cat_str}` | {count} | `{mutator}` |")

        lines.extend([
            "",
            "#### Case-by-Case Failure Diagnoses",
            "| Case ID | Category | Root Cause | Remedy Suggestion |",
            "| :--- | :--- | :--- | :--- |",
        ])

        if not self.failure_diagnostics:
            lines.append("| *(No failures detected)* | - | - | - |")
        else:
            for diag in self.failure_diagnostics:
                clean_cause = diag.root_cause.replace("\n", " ")[:80]
                clean_remedy = diag.remedy_suggestion.replace("\n", " ")[:80]
                lines.append(
                    f"| `{diag.case_id}` | `{diag.category.value}` | {clean_cause} | {clean_remedy} |"
                )

        lines.append("")
        return "\n".join(lines)
