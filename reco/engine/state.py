"""Explicit, serializable execution state for agent graph runs."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class ExecutionState(BaseModel):
    """Complete, serializable execution state of an agent graph workflow."""
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    experiment_id: Optional[str] = None
    agent_version_id: Optional[str] = None
    goal: str = Field(default="", description="Original user goal/specification")
    current_node_id: Optional[str] = None
    status: str = Field(default="initialized", description="'initialized', 'running', 'completed', 'failed'")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Initial workflow input data")
    node_outputs: Dict[str, Any] = Field(default_factory=dict, description="Accumulated node outputs by key")
    tool_events: List[Dict[str, Any]] = Field(default_factory=list, description="Audit trace of all tool calls")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Captured warnings and errors")
    step_history: List[Dict[str, Any]] = Field(default_factory=list, description="Chronological node step trace")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Telemetry and Accounting
    tokens_input: int = Field(default=0, ge=0)
    tokens_output: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)
    latency_ms: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def update_node_output(self, node_id: str, output: Any, output_key: Optional[str] = None, duration_ms: int = 0, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record the output of an executed node into the accumulated state."""
        key = output_key or node_id
        self.node_outputs[key] = output
        self.step_history.append({
            "node_id": node_id,
            "output_key": key,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
            "metadata": metadata or {},
        })

    def record_tool_event(self, node_id: str, tool_name: str, arguments: Dict[str, Any], result_data: Any, success: bool, duration_ms: int, error: Optional[str] = None) -> None:
        """Record an executed tool invocation event into the state trace."""
        self.tool_events.append({
            "node_id": node_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result_data,
            "success": success,
            "duration_ms": duration_ms,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_usage(self, tokens_in: int, tokens_out: int, cost: float, duration_ms: int = 0) -> None:
        """Aggregate token usage, estimated cost, and execution duration."""
        self.tokens_input += tokens_in
        self.tokens_output += tokens_out
        self.cost_usd = round(self.cost_usd + cost, 6)
        self.latency_ms += duration_ms

    def record_error(self, node_id: str, error_message: str, error_type: str = "NODE_EXECUTION_ERROR", fatal: bool = True) -> None:
        """Record an error in the execution state."""
        self.errors.append({
            "node_id": node_id,
            "error": error_message,
            "error_type": error_type,
            "fatal": fatal,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if fatal:
            self.status = "failed"

    def compact_context(self, max_items_per_list: int = 50) -> None:
        """Deterministic context compaction pruning overly verbose intermediate arrays."""
        for k, v in list(self.node_outputs.items()):
            if isinstance(v, list) and len(v) > max_items_per_list:
                self.node_outputs[k] = v[:max_items_per_list]
                self.metadata[f"compacted_{k}"] = f"Truncated from {len(v)} to {max_items_per_list} items"

    def get_context_for_node(self, input_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Construct the resolved input payload for a node based on its input_mapping."""
        if not input_mapping:
            # Default: combine initial inputs and all previous outputs
            ctx = dict(self.inputs)
            ctx.update(self.node_outputs)
            return ctx

        resolved: Dict[str, Any] = {}
        for target_arg, source_path in input_mapping.items():
            # Support dot notation (e.g., 'parsed_statement.transactions')
            parts = source_path.split(".")
            root_key = parts[0]

            val = None
            if root_key in self.node_outputs:
                val = self.node_outputs[root_key]
            elif root_key in self.inputs:
                val = self.inputs[root_key]
            elif root_key == "goal":
                val = self.goal

            # Drill down subkeys if dot notation was used
            if val is not None and len(parts) > 1:
                for subkey in parts[1:]:
                    if isinstance(val, dict) and subkey in val:
                        val = val[subkey]
                    else:
                        val = None
                        break

            if val is not None:
                resolved[target_arg] = val

        return resolved

    @property
    def outputs(self) -> Dict[str, Any]:
        """Convenience property returning the terminal node output or full dictionary."""
        if not self.node_outputs:
            return {}
        last_val = list(self.node_outputs.values())[-1]
        if isinstance(last_val, dict):
            return last_val
        return self.node_outputs

    def get_last_node_output(self) -> Any:
        """Return the output of the terminal or most recently executed node."""
        if not self.node_outputs:
            return None
        return list(self.node_outputs.values())[-1]

    def to_dict(self) -> Dict[str, Any]:
        """Return clean JSON-compatible dictionary representation."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return serialized JSON string."""
        return json.dumps(self.to_dict(), default=str)
