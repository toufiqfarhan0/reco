"""ToolMutator safely modifies tool bindings on agent nodes with anti-fabrication guards."""

from typing import Any, Optional
from reco.diagnostics.taxonomy import MutationType
from reco.engine.models import GraphDefinition
from reco.mutation.models import MutationCandidate
from reco.mutation.mutators.base import BaseMutator
from reco.tools.registry import ToolRegistry


class ToolMutator(BaseMutator):
    """Mutates node tool assignments (TOOL_ADD, TOOL_REMOVE, TOOL_REORDER)."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry

    def can_handle(self, mutation: MutationCandidate) -> bool:
        return mutation.mutation_type in [
            MutationType.TOOL_ADD,
            MutationType.TOOL_REMOVE,
            MutationType.TOOL_REORDER,
        ]

    def apply(self, graph: GraphDefinition, mutation: MutationCandidate) -> GraphDefinition:
        new_graph = self.clone_graph(graph)
        target_node_id = mutation.target

        if target_node_id not in new_graph.nodes:
            raise ValueError(f"Target node '{target_node_id}' does not exist in graph nodes.")

        node = new_graph.nodes[target_node_id]
        proposed = mutation.proposed_change

        if mutation.mutation_type == MutationType.TOOL_ADD:
            tool_name = proposed.get("tool_name") or proposed.get("tool")
            if not tool_name:
                raise ValueError("TOOL_ADD mutation payload must specify 'tool_name'.")

            # Anti-fabrication check: tool must exist in registry if registry is provided
            if self.tool_registry and not self.tool_registry.has(tool_name):
                raise ValueError(
                    f"Cannot add tool '{tool_name}': Tool is not registered in ToolRegistry. "
                    "Fabricated tools are strictly rejected."
                )

            if tool_name not in node.tools:
                node.tools.append(tool_name)

        elif mutation.mutation_type == MutationType.TOOL_REMOVE:
            tool_name = proposed.get("tool_name") or proposed.get("tool")
            if not tool_name:
                raise ValueError("TOOL_REMOVE mutation payload must specify 'tool_name'.")
            if tool_name in node.tools:
                node.tools.remove(tool_name)

        elif mutation.mutation_type == MutationType.TOOL_REORDER:
            tools_order = proposed.get("tools") or proposed.get("order")
            if not tools_order or not isinstance(tools_order, list):
                raise ValueError("TOOL_REORDER mutation payload must specify a list in 'tools'.")
            # All tools in new order must already be assigned or registered
            node.tools = [t for t in tools_order if t in node.tools]

        return new_graph
