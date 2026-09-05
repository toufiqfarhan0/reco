"""Execution state management with immutable step transitions and telemetry."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from reco.engine.models import NodeStatus, NodeType


class NodeExecutionRecord(BaseModel):
    """Detailed telemetry and execution log for a single node run."""

    node_id: str = Field(description="Executed node ID")
    node_type: NodeType = Field(description="Architectural node type")
    status: NodeStatus = Field(description="Outcome status of the node run")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Inputs provided to the node")
    output: Any = Field(default=None, description="Output payload produced by the node")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    start_time: float = Field(default=0.0, description="Start timestamp (perf_counter)")
    end_time: float = Field(default=0.0, description="End timestamp (perf_counter)")
    latency_ms: float = Field(default=0.0, description="Execution wall-clock latency in milliseconds")


class AgentState(BaseModel):
    """Execution state container managing immutable step transitions."""

    data: Dict[str, Any] = Field(default_factory=dict, description="Current global artifact data store")
    node_records: Dict[str, NodeExecutionRecord] = Field(
        default_factory=dict,
        description="Node execution records indexed by node_id"
    )
    step: int = Field(default=0, description="Current execution sequence step counter")
    history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Immutable record of state snapshots across steps"
    )

    def set_node_output(
        self,
        node_id: str,
        record: NodeExecutionRecord,
        output: Any
    ) -> AgentState:
        """Record node completion, update state data, and append snapshot to history."""
        self.node_records[node_id] = record
        self.data[node_id] = output
        self.step += 1

        # Save an immutable snapshot of state data at this step
        self.history.append({
            "step": self.step,
            "node_id": node_id,
            "status": record.status.value,
            "latency_ms": record.latency_ms,
            "data_snapshot": copy.deepcopy(self.data)
        })
        return self

    def get_output(self, node_id: str) -> Any:
        """Retrieve output produced by a specific upstream node."""
        return self.data.get(node_id)

    def get_record(self, node_id: str) -> Optional[NodeExecutionRecord]:
        """Retrieve telemetry record for a node."""
        return self.node_records.get(node_id)

    def snapshot(self) -> Dict[str, Any]:
        """Return a deepcopy of the current state."""
        return copy.deepcopy(self.model_dump())
