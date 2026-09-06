"""Lightweight deterministic DAG execution engine for agent architectures."""

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from reco.core.interfaces import ModelGateway
from reco.engine.models import GraphDefinition, GraphValidationError
from reco.engine.node_runner import NodeRunner
from reco.engine.state import ExecutionState
from reco.logging import get_logger
from reco.tools.executor import ToolExecutor

logger = get_logger("engine.runtime")


class AgentGraphRuntime:
    """Orchestrates deterministic topological execution of an AgentGraphDefinition."""

    def __init__(
        self,
        model_gateway: Optional[ModelGateway] = None,
        tool_executor: Optional[ToolExecutor] = None,
    ):
        if model_gateway is None:
            from reco.llm.mock import MockModelGateway
            model_gateway = MockModelGateway()
        if tool_executor is None:
            from reco.tools.registry import default_tool_registry
            tool_executor = ToolExecutor(registry=default_tool_registry)
        self.model_gateway = model_gateway
        self.tool_executor = tool_executor
        self.node_runner = NodeRunner(model_gateway=model_gateway, tool_executor=tool_executor)

    def _topological_sort(self, graph: GraphDefinition) -> list:
        """Helper returning the topological order of node_ids in graph."""
        nodes = graph.get_topological_order()
        return [n.node_id if hasattr(n, "node_id") else n for n in nodes]

    async def run(
        self,
        graph: GraphDefinition,
        inputs: Dict[str, Any],
        goal: str = "",
        experiment_id: Optional[str] = None,
        agent_version_id: Optional[str] = None,
    ) -> ExecutionState:
        """Execute the agent graph deterministically according to topological node order."""
        start_time = time.perf_counter()

        # Initialize execution state
        state = ExecutionState(
            goal=goal,
            inputs=inputs,
            experiment_id=experiment_id,
            agent_version_id=agent_version_id,
            status="running",
            metadata={"graph_id": graph.graph_id, "graph_name": graph.name},
        )

        # 1. Topological Validation and Scheduling
        try:
            execution_order = graph.get_topological_order()
        except GraphValidationError as val_err:
            state.record_error(
                node_id=graph.entry_node_id,
                error_message=f"Graph validation error: {val_err}",
                error_type="GRAPH_VALIDATION_ERROR",
                fatal=True,
            )
            state.completed_at = datetime.now(timezone.utc)
            state.latency_ms = int((time.perf_counter() - start_time) * 1000)
            return state

        logger.info(
            f"Starting graph '{graph.name}' ({len(execution_order)} nodes in topological order)"
        )

        # 2. Sequential Node Execution
        for node in execution_order:
            state.current_node_id = node.node_id
            logger.debug(f"Executing node: {node.node_id} ({node.name})")

            result = await self.node_runner.run_node(node, state)

            # Record telemetry
            state.record_usage(
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                cost=result.cost_usd,
                duration_ms=result.duration_ms,
            )

            # Handle Node Failure (Downstream Blocking)
            if not result.success:
                logger.error(f"Node '{node.node_id}' failed: {result.error}")
                state.record_error(
                    node_id=node.node_id,
                    error_message=result.error or "Node execution failed",
                    error_type="NODE_FAILURE",
                    fatal=True,
                )
                # Block downstream execution
                break

            # Record successful node output
            state.update_node_output(
                node_id=node.node_id,
                output=result.output,
                output_key=node.output_key,
                duration_ms=result.duration_ms,
                metadata=result.metadata,
            )

        # 3. Finalize State
        if state.status == "running":
            state.status = "completed"

        state.completed_at = datetime.now(timezone.utc)
        state.latency_ms = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            f"Graph '{graph.name}' finished with status '{state.status}' in {state.latency_ms}ms "
            f"(Tokens: {state.tokens_input} in / {state.tokens_output} out, Cost: ${state.cost_usd})"
        )

        return state
