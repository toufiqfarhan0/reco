"""Task Specification schema for decomposed user goals."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskSpecification(BaseModel):
    """Structured specification decomposed from a high-level user goal."""

    goal: str = Field(description="The primary natural language task goal")
    domain: str = Field(default="data_analysis", description="Identified domain category")
    required_capabilities: List[str] = Field(
        default_factory=list,
        description="List of capability keys required to achieve the goal"
    )
    input_schema: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "dataset": {
                    "type": "array",
                    "items": {"type": "object"}
                }
            },
            "required": ["dataset"]
        },
        description="JSON Schema specifying valid inputs"
    )
    output_schema: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "summary": {"type": "object"},
                "distributions": {"type": "object"},
                "anomalies": {"type": "array"}
            },
            "required": ["distributions", "anomalies"]
        },
        description="JSON Schema specifying valid output structure"
    )
    latency_budget_ms: Optional[float] = Field(
        default=5000.0,
        description="Maximum allowed wall-clock latency in milliseconds"
    )
    cost_budget_usd: Optional[float] = Field(
        default=0.05,
        description="Maximum allowed cost budget in USD"
    )
    evaluation_criteria: List[str] = Field(
        default_factory=lambda: ["accuracy", "reliability", "latency", "cost"],
        description="Metrics and criteria to evaluate against"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Auxiliary context, tags, or execution parameters"
    )

    def has_capability(self, capability: str) -> bool:
        """Check if a specific capability is required."""
        return capability.lower() in [c.lower() for c in self.required_capabilities]
