"""TopologyMutator operator adding conditional branches, ensemble paths, or rewiring edges."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from reco.diagnostics.taxonomy import FailureDiagnostic
from reco.engine.models import AgentArchitecture, EdgeSpec, NodeSpec, NodeType
from reco.mutation.mutators.base import BaseMutator


class TopologyMutator(BaseMutator):
    """Adds conditional branches, parallel ensemble paths, or repairs edge wiring."""

    name = "TopologyMutator"

    def mutate(
        self,
        architecture: AgentArchitecture,
        diagnostic: Optional[FailureDiagnostic] = None,
        branch_type: str = "ensemble_path",
        **kwargs: Any
    ) -> AgentArchitecture:
        """Mutate graph topology to introduce parallel ensemble processing or branch routes.

        Args:
            architecture: Target AgentArchitecture.
            diagnostic: FailureDiagnostic informing the topology change.
            branch_type: Type of topological alteration ('ensemble_path', 'parallel_tool', or 'repair_routing').

        Returns:
            Mutated AgentArchitecture.
        """
        arch = self.clone_architecture(architecture)
        node_ids = {n.id for n in arch.nodes}

        # 1. Repair Routing if broken dependency detected
        if branch_type == "repair_routing" or (diagnostic and diagnostic.category.value == "routing_misdirect"):
            # Ensure input_node connects to all tools, and all tools connect to reasoning/output
            tool_nodes = [n for n in arch.nodes if n.type == NodeType.TOOL]
            existing_edges = {(e.source, e.target) for e in arch.edges}

            for tn in tool_nodes:
                if ("input_node", tn.id) not in existing_edges:
                    arch.edges.append(EdgeSpec(source="input_node", target=tn.id))
                    if "input_node" not in tn.dependencies:
                        tn.dependencies.append("input_node")

                if "reasoning_node" in node_ids:
                    if (tn.id, "reasoning_node") not in existing_edges:
                        arch.edges.append(EdgeSpec(source=tn.id, target="reasoning_node"))
                        rn = arch.get_node("reasoning_node")
                        if tn.id not in rn.dependencies:
                            rn.dependencies.append(tn.id)

            return arch

        # 2. Add Ensemble Branch: Secondary reasoning / ensemble synthesis node
        ensemble_id = "reasoning_ensemble_node"
        if ensemble_id not in node_ids and "reasoning_node" in node_ids:
            primary_reasoning = arch.get_node("reasoning_node")

            ensemble_node = NodeSpec(
                id=ensemble_id,
                type=NodeType.REASONING,
                name="Ensemble Secondary Reasoner",
                config={
                    "strategy": "cross_validation_ensemble",
                    "domain": arch.task_spec.domain,
                    "ensemble_role": "secondary_validator"
                },
                dependencies=list(primary_reasoning.dependencies)
            )
            arch.nodes.append(ensemble_node)

            # Connect upstream dependencies to ensemble node
            for dep in primary_reasoning.dependencies:
                arch.edges.append(EdgeSpec(source=dep, target=ensemble_id))

            # Connect ensemble node downstream (to verifier or output)
            downstream = "verifier_node" if "verifier_node" in node_ids else "output_node"
            if downstream in node_ids:
                arch.edges.append(EdgeSpec(source=ensemble_id, target=downstream))
                ds_node = arch.get_node(downstream)
                if ensemble_id not in ds_node.dependencies:
                    ds_node.dependencies.append(ensemble_id)

        return arch
