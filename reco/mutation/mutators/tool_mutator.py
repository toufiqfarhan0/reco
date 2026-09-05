"""ToolAssignmentMutator operator attaching or replacing tools from ToolRegistry."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from reco.diagnostics.taxonomy import FailureDiagnostic
from reco.engine.models import AgentArchitecture, EdgeSpec, NodeSpec, NodeType
from reco.mutation.mutators.base import BaseMutator
from reco.tools.registry import ToolRegistry


class ToolAssignmentMutator(BaseMutator):
    """Attaches or replaces tools from ToolRegistry based on diagnostic recommendations."""

    name = "ToolAssignmentMutator"

    def mutate(
        self,
        architecture: AgentArchitecture,
        diagnostic: Optional[FailureDiagnostic] = None,
        target_tool: Optional[str] = None,
        replace_tool: Optional[str] = None,
        **kwargs: Any
    ) -> AgentArchitecture:
        """Attach or replace a tool in the architecture DAG.

        Args:
            architecture: Target AgentArchitecture.
            diagnostic: FailureDiagnostic recommending tool assignment.
            target_tool: Tool name to assign (must exist in ToolRegistry).
            replace_tool: Tool name to replace (if replacing an existing tool).

        Raises:
            ValueError: If target_tool is not registered in ToolRegistry.

        Returns:
            Mutated AgentArchitecture.
        """
        arch = self.clone_architecture(architecture)

        # 1. Resolve tool to attach / replace
        tool_to_use = target_tool
        tool_to_replace = replace_tool

        if diagnostic:
            # Check diagnostic remedy or metadata
            if not tool_to_use:
                if "smart_reconcile" in diagnostic.remedy_suggestion.lower():
                    tool_to_use = "smart_reconcile"
                    tool_to_replace = tool_to_replace or "exact_reconcile"
                elif "exact_reconcile" in diagnostic.remedy_suggestion.lower():
                    tool_to_use = "exact_reconcile"

        # Default fallback if reconciliation task and no tool specified
        if not tool_to_use:
            tool_to_use = "smart_reconcile"

        # 2. Strict Tool Registry Validation: Reject hallucinated tools!
        if not self.tool_registry.has(tool_to_use):
            raise ValueError(
                f"Cannot assign hallucinated tool '{tool_to_use}': not registered in ToolRegistry."
            )

        tool_def = self.tool_registry.get(tool_to_use)

        # 3. Strategy A: Replace an existing tool node
        replaced = False
        for node in arch.nodes:
            if node.type == NodeType.TOOL:
                should_replace = False
                if tool_to_replace and node.tool_name == tool_to_replace:
                    should_replace = True
                elif diagnostic and diagnostic.target_node_id == node.id:
                    should_replace = True
                elif tool_to_replace is None and node.tool_name != tool_to_use and "reconcile" in tool_to_use:
                    # Upgrade older reconcile tool
                    if node.tool_name and "reconcile" in node.tool_name:
                        should_replace = True

                if should_replace:
                    old_id = node.id
                    new_id = f"tool_{tool_def.name}"
                    
                    # If new_id already exists in the graph, remove the redundant old node
                    if any(other.id == new_id for other in arch.nodes if other is not node):
                        arch.nodes = [n for n in arch.nodes if n.id != old_id]
                        arch.edges = [e for e in arch.edges if e.source != old_id and e.target != old_id]
                        for other_node in arch.nodes:
                            other_node.dependencies = [
                                d for d in other_node.dependencies if d != old_id
                            ]
                        replaced = True
                        break

                    node.id = new_id
                    node.name = f"Tool: {tool_def.name}"
                    node.tool_name = tool_def.name
                    node.config["parameters_schema"] = tool_def.parameters
                    node.config["upgraded_from"] = old_id

                    # Update all edges referencing old_id
                    for e in arch.edges:
                        if e.source == old_id:
                            e.source = new_id
                        if e.target == old_id:
                            e.target = new_id

                    # Update downstream dependencies referencing old_id
                    for other_node in arch.nodes:
                        if old_id in other_node.dependencies:
                            other_node.dependencies = [
                                new_id if d == old_id else d for d in other_node.dependencies
                            ]

                    replaced = True
                    break

        # Deduplicate edges
        seen_edges = set()
        unique_edges = []
        for e in arch.edges:
            pair = (e.source, e.target)
            if pair not in seen_edges:
                seen_edges.add(pair)
                unique_edges.append(e)
        arch.edges = unique_edges

        # Deduplicate nodes
        seen_nodes = set()
        unique_nodes = []
        for n in arch.nodes:
            if n.id not in seen_nodes:
                seen_nodes.add(n.id)
                unique_nodes.append(n)
        arch.nodes = unique_nodes

        if replaced:
            return arch

        # 4. Strategy B: Attach new tool node to graph
        new_node_id = f"tool_{tool_def.name}"

        # If already present, don't duplicate
        if any(n.id == new_node_id for n in arch.nodes):
            return arch

        new_tool_node = NodeSpec(
            id=new_node_id,
            type=NodeType.TOOL,
            name=f"Tool: {tool_def.name}",
            tool_name=tool_def.name,
            config={"parameters_schema": tool_def.parameters},
            dependencies=["input_node"]
        )
        arch.nodes.append(new_tool_node)

        # Wire: input_node -> new_tool_node
        arch.edges.append(EdgeSpec(source="input_node", target=new_node_id))

        # Wire to reasoning_node or verifier_node or output_node
        target_downstream = None
        for cand in ("reasoning_node", "verifier_node", "output_node"):
            if any(n.id == cand for n in arch.nodes):
                target_downstream = cand
                break

        if target_downstream:
            arch.edges.append(EdgeSpec(source=new_node_id, target=target_downstream))
            downstream_node = arch.get_node(target_downstream)
            if new_node_id not in downstream_node.dependencies:
                downstream_node.dependencies.append(new_node_id)

        return arch
