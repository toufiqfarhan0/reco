"""VerifierMutator inserts a specialized auditor / verifier node into the workflow DAG."""

from typing import Any, Dict
from reco.diagnostics.taxonomy import MutationType
from reco.engine.models import EdgeModel, GraphDefinition, NodeModel
from reco.mutation.models import MutationCandidate
from reco.mutation.mutators.base import BaseMutator


class VerifierMutator(BaseMutator):
    """Inserts an independent verification or auditing node to gate proposed workflow outputs."""

    def can_handle(self, mutation: MutationCandidate) -> bool:
        return mutation.mutation_type == MutationType.ADD_VERIFIER

    def apply(self, graph: GraphDefinition, mutation: MutationCandidate) -> GraphDefinition:
        new_graph = self.clone_graph(graph)
        target_node_id = mutation.target
        proposed = mutation.proposed_change

        if target_node_id not in new_graph.nodes:
            raise ValueError(f"Target node '{target_node_id}' does not exist in graph nodes.")

        target_node = new_graph.nodes[target_node_id]
        verifier_id = proposed.get("node_id") or f"{target_node_id}_verifier"

        if verifier_id in new_graph.nodes:
            raise ValueError(f"Verifier node '{verifier_id}' already exists in graph.")

        role = proposed.get("role", "Auditor")
        system_prompt = proposed.get(
            "system_prompt",
            f"Perform independent audit and verification of outputs from '{target_node_id}'. "
            "Flag discrepancies, validate entity identities, and ensure output schema integrity.",
        )
        tools = proposed.get("tools", [])

        # Default input mapping inherits target node output
        output_key = target_node.output_key or target_node_id
        input_mapping = proposed.get("input_mapping", {output_key: output_key})

        verifier_node = NodeModel(
            node_id=verifier_id,
            name=proposed.get("name", f"{target_node.name} Auditor"),
            role=role,
            system_prompt=system_prompt,
            tools=tools,
            input_mapping=input_mapping,
            output_key=f"verified_{output_key}",
            metadata={"stage": "verification", "generated_by": "VerifierMutator"},
        )
        new_graph.nodes[verifier_id] = verifier_node

        # Rewire:
        # If target_node was terminal, verifier becomes terminal
        # Inbound edge: target_node -> verifier
        new_graph.edges.append(EdgeModel(source_node_id=target_node_id, target_node_id=verifier_id))

        if target_node_id in new_graph.terminal_node_ids:
            new_graph.terminal_node_ids = [t for t in new_graph.terminal_node_ids if t != target_node_id]
            new_graph.terminal_node_ids.append(verifier_id)
        else:
            # If target_node had outbound edges, rewire them from verifier
            old_successors = [e.target_node_id for e in new_graph.edges if e.source_node_id == target_node_id and e.target_node_id != verifier_id]
            new_graph.edges = [
                e for e in new_graph.edges
                if not (e.source_node_id == target_node_id and e.target_node_id in old_successors)
            ]
            for succ in old_successors:
                new_graph.edges.append(EdgeModel(source_node_id=verifier_id, target_node_id=succ))

        return new_graph
