"""Agent Graph Runtime for executing synthesized DAGs in strict topological order."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from reco.engine.models import AgentArchitecture, NodeStatus, NodeType
from reco.engine.node_runner import NodeRunner
from reco.engine.state import AgentState, NodeExecutionRecord
from reco.tools.executor import ToolExecutor
from reco.tools.registry import ToolRegistry


class ExecutionResult(BaseModel):
    """Encapsulated execution outcome of an AgentArchitecture run."""

    architecture_id: str = Field(description="ID of the executed architecture")
    task_goal: str = Field(description="Natural language goal executed")
    status: NodeStatus = Field(description="Overall execution status")
    final_output: Any = Field(default=None, description="Final payload from output_node")
    node_records: Dict[str, NodeExecutionRecord] = Field(
        default_factory=dict,
        description="Execution records per node"
    )
    execution_order: List[str] = Field(
        default_factory=list,
        description="Topological node execution sequence"
    )
    total_latency_ms: float = Field(default=0.0, description="Total wall-clock runtime in milliseconds")
    quality_score: float = Field(default=0.0, description="Architectural quality score")
    error: Optional[str] = Field(default=None, description="Error detail if execution failed")


class AgentRuntime:
    """Executes synthesized AgentArchitecture DAGs in strict topological sequence."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        tool_executor: Optional[ToolExecutor] = None,
        node_runner: Optional[NodeRunner] = None
    ):
        self.tool_registry = tool_registry or ToolRegistry.create_default()
        self.tool_executor = tool_executor or ToolExecutor()
        self.node_runner = node_runner or NodeRunner(
            tool_registry=self.tool_registry,
            tool_executor=self.tool_executor
        )

    def execute(
        self,
        architecture: AgentArchitecture,
        initial_inputs: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute all nodes in the architecture DAG following topological order.

        Args:
            architecture: The AgentArchitecture to execute.
            initial_inputs: Input data payload matching task_spec.input_schema.

        Returns:
            ExecutionResult containing telemetry, step records, and final output.
        """
        start_time = time.perf_counter()

        # 1. Validate graph integrity and compute topological ordering
        try:
            architecture.validate_graph()
            execution_order = architecture.topological_sort()
        except Exception as exc:
            total_elapsed = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                architecture_id=architecture.id,
                task_goal=architecture.task_spec.goal,
                status=NodeStatus.FAILED,
                final_output=None,
                node_records={},
                execution_order=[],
                total_latency_ms=round(total_elapsed, 3),
                quality_score=0.0,
                error=f"Graph validation error: {str(exc)}"
            )

        # 2. Initialize execution state
        state = AgentState()
        overall_status = NodeStatus.COMPLETED
        runtime_error = None
        failed_nodes: set[str] = set()

        # 3. Execute nodes in strict sequence
        for node_id in execution_order:
            node = architecture.get_node(node_id)

            # Check if any upstream dependency has failed
            has_failed_dep = any(dep in failed_nodes for dep in node.dependencies)
            if has_failed_dep:
                record = NodeExecutionRecord(
                    node_id=node.id,
                    node_type=node.type,
                    status=NodeStatus.SKIPPED,
                    inputs={},
                    output=None,
                    error="Skipped due to upstream node failure",
                    start_time=time.perf_counter(),
                    end_time=time.perf_counter(),
                    latency_ms=0.0
                )
                state.set_node_output(node.id, record, None)
                failed_nodes.add(node.id)
                continue

            # Run node
            record, output = self.node_runner.run_node(node, state, initial_inputs)
            state.set_node_output(node.id, record, output)

            if record.status == NodeStatus.FAILED:
                failed_nodes.add(node.id)
                overall_status = NodeStatus.FAILED
                runtime_error = f"Node '{node.id}' ({node.type.value}) failed: {record.error}"

        total_elapsed = (time.perf_counter() - start_time) * 1000.0
        final_output = state.get_output("output_node")
        complexity = architecture.complexity_metrics()

        return ExecutionResult(
            architecture_id=architecture.id,
            task_goal=architecture.task_spec.goal,
            status=overall_status,
            final_output=final_output,
            node_records=state.node_records,
            execution_order=execution_order,
            total_latency_ms=round(total_elapsed, 3),
            quality_score=complexity.get("quality_score", 0.0),
            error=runtime_error
        )
