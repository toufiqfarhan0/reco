"""Core interfaces, protocols, and data exchange models for Reco.

These define the abstract boundaries of the agent engineering engine, ensuring
zero tight coupling to specific external providers (TensorMux, Neatlogs, Dodo, etc.).
"""

from abc import ABC, abstractmethod
import json
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Data Exchange Models (Pydantic v2)
# ---------------------------------------------------------------------------

class ToolResult(BaseModel):
    """Standard output returned by any tool execution."""
    success: bool
    data: Optional[Any] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    duration_ms: int = 0
    tool_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.output is None and self.data is not None:
            self.output = self.data
        elif self.data is None and self.output is not None:
            self.data = self.output
        if self.duration_ms == 0 and self.execution_time_ms != 0:
            self.duration_ms = self.execution_time_ms
        elif self.execution_time_ms == 0 and self.duration_ms != 0:
            self.execution_time_ms = self.duration_ms


class ToolCall(BaseModel):
    """Provider-neutral representation of a structured tool invocation request."""
    tool_name: str = Field(..., description="Machine name of the target tool in ToolRegistry")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Parsed arguments dictionary")
    call_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique invocation identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelMessage(BaseModel):
    """Normalized chat message for LLM interactions."""
    role: str = Field(..., description="Message role: system, user, assistant, or tool")
    content: str = Field(default="", description="Text content of the message")
    tool_calls: Optional[List[Union[ToolCall, Dict[str, Any]]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class ModelRequest(BaseModel):
    """Standardized request to any inference backend."""
    messages: List[ModelMessage]
    model: Optional[str] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    response_format: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    """Standardized response from any inference backend."""
    content: str = ""
    tool_calls: Optional[List[Union[ToolCall, Dict[str, Any]]]] = None
    structured_output: Optional[Dict[str, Any]] = None
    tokens_prompt: int = 0
    tokens_completion: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    cost_type: str = "simulated_mock"  # "actual", "estimated", "simulated_mock"
    latency_ms: int = 0
    model_used: str = ""
    finish_reason: Optional[str] = None
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.total_tokens == 0 and (self.tokens_prompt or self.tokens_completion):
            self.total_tokens = self.tokens_prompt + self.tokens_completion

    def get_parsed_tool_calls(self) -> List[ToolCall]:
        """Normalize tool_calls into strongly typed ToolCall objects."""
        if not self.tool_calls:
            return []
        parsed: List[ToolCall] = []
        for tc in self.tool_calls:
            if isinstance(tc, ToolCall):
                parsed.append(tc)
            elif isinstance(tc, dict):
                if "function" in tc and isinstance(tc["function"], dict):
                    fn = tc["function"]
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {"raw_args": args}
                    parsed.append(
                        ToolCall(
                            tool_name=fn.get("name", ""),
                            arguments=args if isinstance(args, dict) else {},
                            call_id=str(tc.get("id", str(uuid4()))),
                            metadata=tc.get("metadata", {}),
                        )
                    )
                else:
                    tool_name = tc.get("tool_name") or tc.get("name") or ""
                    args = tc.get("arguments") or tc.get("args") or {}
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {"raw_args": args}
                    parsed.append(
                        ToolCall(
                            tool_name=tool_name,
                            arguments=args if isinstance(args, dict) else {},
                            call_id=str(tc.get("call_id") or tc.get("id") or str(uuid4())),
                            metadata=tc.get("metadata", {}),
                        )
                    )
        return parsed


class EvaluationResult(BaseModel):
    """Quantitative score produced by an Evaluator."""
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Accuracy score (0.0 to 1.0)")
    reliability: float = Field(..., ge=0.0, le=1.0, description="Schema/invariant validity (0.0 to 1.0)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed sub-scores and failure reasons")
    passed: bool = Field(default=False)


class BenchmarkCase(BaseModel):
    """A single input/ground-truth test scenario."""
    case_code: str
    split: str = Field(..., description="'optimization' or 'held_out'")
    input_data: Dict[str, Any]
    ground_truth: Dict[str, Any]


class BenchmarkRunResult(BaseModel):
    """Aggregate evaluation metrics for an agent version across benchmark cases."""
    split: str
    accuracy: float
    reliability: float
    total_cost_usd: float
    avg_latency_ms: int
    cases_passed: int
    cases_total: int
    case_results: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Core Engine Interfaces (Abstract Base Classes)
# ---------------------------------------------------------------------------

class Tool(ABC):
    """Abstract interface for tools available to synthesized agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique machine name for tool dispatching."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human/LLM description of tool capabilities."""
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """JSON Schema defining required arguments."""
        pass

    @property
    def output_schema(self) -> Optional[Dict[str, Any]]:
        """Optional JSON Schema defining the tool's return structure."""
        return None

    @property
    def deterministic(self) -> bool:
        """Whether repeated execution with identical arguments yields identical output."""
        return True

    @property
    def side_effect(self) -> bool:
        """Whether the tool alters external state (e.g., posting journal entries)."""
        return False

    @property
    def risk_level(self) -> str:
        """Operational risk rating ('low', 'medium', 'high')."""
        return "low"

    @property
    def category(self) -> str:
        """Functional categorization (e.g., 'reconciliation', 'extraction', 'math')."""
        return "general"

    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate arguments against tool constraints. Default passes through."""
        return arguments

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        """Execute the tool deterministically with provided parameters."""
        pass


class Agent(ABC):
    """Abstract interface for an individual specialized agent node."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent node name."""
        pass

    @property
    @abstractmethod
    def role(self) -> str:
        """Agent role or specialization."""
        pass

    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent node against the current workflow state."""
        pass


class ModelGateway(ABC):
    """Abstract provider-agnostic inference gateway interface."""

    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Invoke LLM inference and return standardized response with cost and latency."""
        pass


class Evaluator(ABC):
    """Abstract interface for domain-specific benchmark evaluation."""

    @abstractmethod
    def evaluate(self, actual_output: Dict[str, Any], ground_truth: Dict[str, Any]) -> EvaluationResult:
        """Score actual output against ground truth deterministically without hallucinated metrics."""
        pass


class Benchmark(ABC):
    """Abstract interface for a domain benchmark suite."""

    @abstractmethod
    def load_cases(self, split: Optional[str] = None) -> List[BenchmarkCase]:
        """Load benchmark scenarios for a designated split ('optimization' or 'held_out')."""
        pass

    @abstractmethod
    async def evaluate_run(self, agent: Agent, split: str) -> BenchmarkRunResult:
        """Execute the agent against benchmark cases and return aggregated scorecards."""
        pass


class Tracer(ABC):
    """Abstract observability and telemetry interface (e.g., Neatlogs adapter)."""

    @abstractmethod
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Any:
        """Begin an execution trace span."""
        pass

    @abstractmethod
    def log_event(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Log a telemetry event."""
        pass

    @abstractmethod
    def record_metric(self, name: str, value: float, unit: str = "count") -> None:
        """Record an analytical metric."""
        pass


class BillingProvider(ABC):
    """Abstract monetization/usage provider interface (e.g., Dodo Payments adapter)."""

    @abstractmethod
    async def check_access(self, identifier: str) -> bool:
        """Verify whether an entity has sufficient credits/subscription status."""
        pass

    @abstractmethod
    async def record_usage(self, identifier: str, units: int, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Record consumed usage units or run charges."""
        pass
