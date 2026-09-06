"""Core domain models and interfaces for Reco."""

from reco.core.interfaces import (
    Agent,
    Benchmark,
    BenchmarkCase,
    BenchmarkRunResult,
    BillingProvider,
    EvaluationResult,
    Evaluator,
    ModelGateway,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    Tool,
    ToolResult,
    Tracer,
)
from reco.core.task_spec import (
    Capability,
    EvaluatorSpecification,
    Subtask,
    TaskSpecification,
    ToolRecommendation,
)
from reco.core.goal_analyzer import (
    GoalAnalyzer,
    normalize_goal,
)

__all__ = [
    "Agent",
    "Benchmark",
    "BenchmarkCase",
    "BenchmarkRunResult",
    "BillingProvider",
    "EvaluationResult",
    "Evaluator",
    "ModelGateway",
    "ModelMessage",
    "ModelRequest",
    "ModelResponse",
    "Tool",
    "ToolResult",
    "Tracer",
    # Task spec & Goal analyzer
    "Capability",
    "EvaluatorSpecification",
    "Subtask",
    "TaskSpecification",
    "ToolRecommendation",
    "GoalAnalyzer",
    "normalize_goal",
]

