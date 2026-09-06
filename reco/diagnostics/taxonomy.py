"""Taxonomy of failure modes, mutation recommendations, severities, and failure sources."""

from enum import Enum


class FailureCategory(str, Enum):
    """Core taxonomy of diagnostic failure classifications for autonomous agent workflows."""
    TOOL_ARGUMENT_ERROR = "TOOL_ARGUMENT_ERROR"
    TOOL_RUNTIME_ERROR = "TOOL_RUNTIME_ERROR"
    ARITHMETIC_MISMATCH = "ARITHMETIC_MISMATCH"
    PREMATURE_TERMINATION = "PREMATURE_TERMINATION"
    HALLUCINATED_MATCH = "HALLUCINATED_MATCH"
    CONTEXT_OVERFLOW = "CONTEXT_OVERFLOW"
    MISSING_TOOL = "MISSING_TOOL"
    WRONG_TOOL_SELECTION = "WRONG_TOOL_SELECTION"
    MISSING_VERIFICATION = "MISSING_VERIFICATION"
    OUTPUT_SCHEMA_ERROR = "OUTPUT_SCHEMA_ERROR"
    MODEL_FAILURE = "MODEL_FAILURE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    UNCRITICAL_EVIDENCE_ACCEPTANCE = "UNCRITICAL_EVIDENCE_ACCEPTANCE"
    PROMPT_DEFECT = "PROMPT_DEFECT"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


class MutationType(str, Enum):
    """Structured mutation recommendation types for future optimization."""
    PROMPT_CHANGE = "PROMPT_CHANGE"
    TOOL_ADD = "TOOL_ADD"
    TOOL_REMOVE = "TOOL_REMOVE"
    TOOL_REORDER = "TOOL_REORDER"
    TOPOLOGY_CHANGE = "TOPOLOGY_CHANGE"
    ADD_VERIFIER = "ADD_VERIFIER"
    MEMORY_CHANGE = "MEMORY_CHANGE"
    MODEL_CHANGE = "MODEL_CHANGE"
    ROUTING_CHANGE = "ROUTING_CHANGE"
    CONTEXT_CHANGE = "CONTEXT_CHANGE"
    RETRY_POLICY_CHANGE = "RETRY_POLICY_CHANGE"


class Severity(str, Enum):
    """Severity ratings matching database persistence constraints."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FailureSource(str, Enum):
    """Identifies the architectural layer or lifecycle stage where the failure originated."""
    GOAL_ANALYSIS = "goal_analysis"
    ARCHITECTURE_GENERATION = "architecture_generation"
    NODE_EXECUTION = "node_execution"
    TOOL_INVOCATION = "tool_invocation"
    MODEL_INVOCATION = "model_invocation"
    STATE_PROPAGATION = "state_propagation"
    EVALUATION = "evaluation"
