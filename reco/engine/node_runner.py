"""Node execution dispatcher for typed DAG components."""

from __future__ import annotations

import time
import traceback
from typing import Any, Dict, Optional, Tuple

from reco.engine.models import NodeSpec, NodeStatus, NodeType
from reco.engine.state import AgentState, NodeExecutionRecord
from reco.tools.executor import ToolExecutor
from reco.tools.registry import ToolRegistry


class NodeRunner:
    """Executes typed DAG nodes, manages dependency inputs, and records execution telemetry."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        tool_executor: Optional[ToolExecutor] = None
    ):
        self.tool_registry = tool_registry or ToolRegistry.create_default()
        self.tool_executor = tool_executor or ToolExecutor()

    def run_node(
        self,
        node: NodeSpec,
        state: AgentState,
        initial_inputs: Dict[str, Any]
    ) -> Tuple[NodeExecutionRecord, Any]:
        """Execute a single node against current state and return record + output payload.

        Args:
            node: The NodeSpec to execute.
            state: Current AgentState.
            initial_inputs: Original task input arguments.

        Returns:
            Tuple of (NodeExecutionRecord, output_payload).
        """
        start_time = time.perf_counter()
        inputs = self._resolve_inputs(node, state, initial_inputs)

        try:
            if node.type == NodeType.INPUT:
                output = self._execute_input_node(node, inputs)
            elif node.type == NodeType.TOOL:
                output = self._execute_tool_node(node, inputs)
            elif node.type == NodeType.REASONING:
                output = self._execute_reasoning_node(node, inputs, state)
            elif node.type == NodeType.VERIFIER:
                output = self._execute_verifier_node(node, inputs, state)
            elif node.type == NodeType.OUTPUT:
                output = self._execute_output_node(node, inputs, state)
            else:
                raise ValueError(f"Unsupported node type: {node.type}")

            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000.0

            record = NodeExecutionRecord(
                node_id=node.id,
                node_type=node.type,
                status=NodeStatus.COMPLETED,
                inputs=inputs,
                output=output,
                error=None,
                start_time=start_time,
                end_time=end_time,
                latency_ms=round(latency_ms, 3)
            )
            return record, output

        except Exception as exc:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000.0
            error_msg = f"{type(exc).__name__}: {str(exc)}\n{traceback.format_exc()}"

            record = NodeExecutionRecord(
                node_id=node.id,
                node_type=node.type,
                status=NodeStatus.FAILED,
                inputs=inputs,
                output=None,
                error=error_msg,
                start_time=start_time,
                end_time=end_time,
                latency_ms=round(latency_ms, 3)
            )
            return record, None

    def _resolve_inputs(
        self,
        node: NodeSpec,
        state: AgentState,
        initial_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate inputs from upstream dependencies or initial input payload."""
        resolved: Dict[str, Any] = {}

        if node.type == NodeType.INPUT:
            return initial_inputs

        # Collect outputs from declared dependencies
        for dep_id in node.dependencies:
            dep_out = state.get_output(dep_id)
            resolved[dep_id] = dep_out

            # Flatten dataset key if available from input node
            if dep_id == "input_node" and isinstance(dep_out, dict):
                for k, v in dep_out.items():
                    resolved[k] = v

        return resolved

    def _execute_input_node(self, node: NodeSpec, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate raw input payload."""
        return inputs

    def _execute_tool_node(self, node: NodeSpec, inputs: Dict[str, Any]) -> Any:
        """Execute registered tool using ToolExecutor."""
        if not node.tool_name:
            raise ValueError(f"Tool node '{node.id}' missing 'tool_name'")

        tool = self.tool_registry.get(node.tool_name)

        # Prepare tool input parameters
        tool_inputs: Dict[str, Any] = {}
        for k, v in inputs.items():
            if k != "input_node":
                tool_inputs[k] = v
            elif isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    tool_inputs[sub_k] = sub_v

        # Fallback: check nested dictionaries in inputs
        for val in inputs.values():
            if isinstance(val, dict):
                for sub_k, sub_v in val.items():
                    if sub_k not in tool_inputs:
                        tool_inputs[sub_k] = sub_v

        # Pass any additional node config parameters
        for k, v in node.config.items():
            if k not in ["parameters_schema"]:
                tool_inputs[k] = v

        result = self.tool_executor.execute(tool, tool_inputs)
        if not result.success:
            raise RuntimeError(f"Tool '{node.tool_name}' failed: {result.error}")

        return result.output

    def _execute_reasoning_node(
        self,
        node: NodeSpec,
        inputs: Dict[str, Any],
        state: AgentState
    ) -> Dict[str, Any]:
        """Synthesize findings across upstream analytical tools."""
        # Find tool outputs from upstream dependencies
        summary = None
        distributions = None
        anomalies = []

        for dep_id in node.dependencies:
            out = state.get_output(dep_id)
            if not isinstance(out, dict):
                continue
            if "row_count" in out:
                summary = out
            if "columns" in out and "record_count" in out:
                distributions = out["columns"]
            if "anomalies" in out:
                anomalies = out["anomalies"]

        # Synthesize analytical insights
        observations = []
        if summary:
            observations.append(
                f"Dataset contains {summary['row_count']} records across {len(summary['column_names'])} columns."
            )
        if distributions:
            cols_analyzed = list(distributions.keys())
            observations.append(
                f"Computed distribution statistics for {len(cols_analyzed)} numeric features: {', '.join(cols_analyzed)}."
            )
        if anomalies is not None:
            anomaly_count = len(anomalies)
            if anomaly_count > 0:
                observations.append(
                    f"Detected {anomaly_count} anomalous records exceeding statistical deviation thresholds."
                )
            else:
                observations.append("No statistical anomalies detected within the specified deviation threshold.")

        return {
            "synthesis_summary": " | ".join(observations),
            "observations": observations,
            "anomaly_count": len(anomalies) if anomalies else 0,
            "features_analyzed": list(distributions.keys()) if distributions else [],
            "status": "reasoning_complete"
        }

    def _execute_verifier_node(
        self,
        node: NodeSpec,
        inputs: Dict[str, Any],
        state: AgentState
    ) -> Dict[str, Any]:
        """Validate reasoning and output constraints against task specifications."""
        checks = []
        issues = []

        # 1. Verify upstream reasoning completed
        reasoning_out = state.get_output("reasoning_node")
        if reasoning_out and reasoning_out.get("status") == "reasoning_complete":
            checks.append({"check": "reasoning_node_status", "passed": True})
        else:
            checks.append({"check": "reasoning_node_status", "passed": False})
            issues.append("Upstream reasoning did not produce a complete status.")

        # 2. Verify anomalies are valid if anomaly detection tool was executed
        if state.get_output("tool_detect_anomalies"):
            anom_out = state.get_output("tool_detect_anomalies")
            if isinstance(anom_out, dict) and "anomalies" in anom_out:
                checks.append({
                    "check": "anomaly_data_structure",
                    "passed": True,
                    "count": len(anom_out["anomalies"])
                })
            else:
                checks.append({"check": "anomaly_data_structure", "passed": False})
                issues.append("Anomaly detection output did not conform to expected schema.")

        # 3. Check latency so far
        total_latency_ms = sum(rec.latency_ms for rec in state.node_records.values())
        budget_ms = node.config.get("latency_budget_ms") or 5000.0
        within_budget = total_latency_ms <= budget_ms
        checks.append({
            "check": "latency_budget",
            "passed": within_budget,
            "elapsed_ms": round(total_latency_ms, 2),
            "budget_ms": budget_ms
        })
        if not within_budget:
            issues.append(f"Cumulative latency ({total_latency_ms:.2f}ms) exceeded budget ({budget_ms}ms).")

        verified = len(issues) == 0
        return {
            "verified": verified,
            "checks": checks,
            "issues": issues,
            "cumulative_latency_ms": round(total_latency_ms, 2)
        }

    def _execute_output_node(
        self,
        node: NodeSpec,
        inputs: Dict[str, Any],
        state: AgentState
    ) -> Dict[str, Any]:
        """Package final structured output conforming to task specification."""
        summary = None
        distributions = {}
        anomalies = []

        for dep_id, out in state.data.items():
            if isinstance(out, dict):
                if "row_count" in out:
                    summary = out
                if "columns" in out and "record_count" in out:
                    distributions = out["columns"]
                if "anomalies" in out:
                    anomalies = out["anomalies"]

        reasoning = state.get_output("reasoning_node")
        verification = state.get_output("verifier_node")

        output_payload: Dict[str, Any] = {
            "summary": summary or {},
            "distributions": distributions,
            "anomalies": anomalies,
            "reasoning": reasoning or {},
            "verification": verification or {"verified": False}
        }

        # Also merge domain/tool outputs (e.g., reconciliation, analysis)
        for dep_id, out in state.data.items():
            if dep_id.startswith("tool_") and isinstance(out, dict):
                for k, v in out.items():
                    if k not in output_payload:
                        output_payload[k] = v

        return output_payload
