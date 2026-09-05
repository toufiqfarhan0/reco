"""DAG Architecture Generator for synthesizing specialized agent graphs."""

from __future__ import annotations

import uuid
from typing import List, Optional
from reco.core.task_spec import TaskSpecification
from reco.engine.models import (
    AgentArchitecture,
    EdgeSpec,
    NodeSpec,
    NodeType,
)
from reco.tools.registry import ToolDefinition, ToolRegistry


class ArchitectureGenerator:
    """Dynamically generates specialized Agent Architecture DAGs tailored to task specifications."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry or ToolRegistry.create_default()

    def generate(
        self,
        task_spec: TaskSpecification,
        architecture_name: Optional[str] = None
    ) -> AgentArchitecture:
        """Synthesize an AgentArchitecture DAG matching task capabilities and available tools.

        Args:
            task_spec: The structured task specification.
            architecture_name: Optional custom architecture name.

        Returns:
            Validated AgentArchitecture instance with typed nodes and edges.
        """
        arch_id = f"arch_{uuid.uuid4().hex[:8]}"
        name = architecture_name or f"Agent_{task_spec.domain.title()}_V0"

        nodes: List[NodeSpec] = []
        edges: List[EdgeSpec] = []

        # 1. Input Node: Ingests raw task payload
        input_node = NodeSpec(
            id="input_node",
            type=NodeType.INPUT,
            name="Task Input Ingestion",
            config={"schema": task_spec.input_schema},
            dependencies=[]
        )
        nodes.append(input_node)

        # 2. Tool Nodes: Selected based on task capabilities
        selected_tools = self._select_tools_for_task(task_spec)
        tool_node_ids = []

        for tool in selected_tools:
            node_id = f"tool_{tool.name}"
            tool_node = NodeSpec(
                id=node_id,
                type=NodeType.TOOL,
                name=f"Tool: {tool.name}",
                tool_name=tool.name,
                config={"parameters_schema": tool.parameters},
                dependencies=["input_node"]
            )
            nodes.append(tool_node)
            tool_node_ids.append(node_id)
            edges.append(EdgeSpec(source="input_node", target=node_id))

        # Fallback if no specific tools matched: create general analytical tool nodes
        if not tool_node_ids and task_spec.domain == "data_analysis":
            fallback_tool = self.tool_registry.get("tabular_summary")
            node_id = f"tool_{fallback_tool.name}"
            tool_node = NodeSpec(
                id=node_id,
                type=NodeType.TOOL,
                name=f"Tool: {fallback_tool.name}",
                tool_name=fallback_tool.name,
                config={"parameters_schema": fallback_tool.parameters},
                dependencies=["input_node"]
            )
            nodes.append(tool_node)
            tool_node_ids.append(node_id)
            edges.append(EdgeSpec(source="input_node", target=node_id))

        # 3. Reasoning Node: Synthesizes tool outputs and correlates findings
        upstream_for_reasoning = tool_node_ids if tool_node_ids else ["input_node"]
        reasoning_node = NodeSpec(
            id="reasoning_node",
            type=NodeType.REASONING,
            name="Domain Synthesis & Reasoning",
            config={
                "domain": task_spec.domain,
                "strategy": "analytical_correlation"
            },
            dependencies=upstream_for_reasoning
        )
        nodes.append(reasoning_node)
        for uid in upstream_for_reasoning:
            edges.append(EdgeSpec(source=uid, target="reasoning_node"))

        # 4. Verifier Node: Verifies output validity against task criteria & schema
        verifier_node = NodeSpec(
            id="verifier_node",
            type=NodeType.VERIFIER,
            name="Output & Quality Verifier",
            config={
                "output_schema": task_spec.output_schema,
                "latency_budget_ms": task_spec.latency_budget_ms,
                "cost_budget_usd": task_spec.cost_budget_usd,
                "criteria": task_spec.evaluation_criteria
            },
            dependencies=["reasoning_node"]
        )
        nodes.append(verifier_node)
        edges.append(EdgeSpec(source="reasoning_node", target="verifier_node"))

        # 5. Output Node: Formats final response payload
        output_node = NodeSpec(
            id="output_node",
            type=NodeType.OUTPUT,
            name="Structured Result Delivery",
            config={"schema": task_spec.output_schema},
            dependencies=["verifier_node"]
        )
        nodes.append(output_node)
        edges.append(EdgeSpec(source="verifier_node", target="output_node"))

        arch = AgentArchitecture(
            id=arch_id,
            name=name,
            task_spec=task_spec,
            nodes=nodes,
            edges=edges,
            metadata={
                "tool_count": len(selected_tools),
                "generated_nodes": len(nodes)
            }
        )

        # Validate graph integrity and acyclicity
        arch.validate_graph()

        return arch

    def _select_tools_for_task(self, task_spec: TaskSpecification) -> List[ToolDefinition]:
        """Match required task capabilities against available tools in the registry."""
        selected: List[ToolDefinition] = []
        seen_names = set()

        for capability in task_spec.required_capabilities:
            matching_tools = self.tool_registry.find_by_capability(capability)
            for tool in matching_tools:
                if tool.name not in seen_names:
                    selected.append(tool)
                    seen_names.add(tool.name)

        return selected
