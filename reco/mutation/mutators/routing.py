"""RoutingMutator updates transition conditions and dynamic routing policies."""

from reco.diagnostics.taxonomy import MutationType
from reco.engine.models import GraphDefinition
from reco.mutation.models import MutationCandidate
from reco.mutation.mutators.base import BaseMutator


class RoutingMutator(BaseMutator):
    """Mutates workflow routing conditions and transition policies."""

    def can_handle(self, mutation: MutationCandidate) -> bool:
        return mutation.mutation_type == MutationType.ROUTING_CHANGE

    def apply(self, graph: GraphDefinition, mutation: MutationCandidate) -> GraphDefinition:
        new_graph = self.clone_graph(graph)
        proposed = mutation.proposed_change

        source = proposed.get("source") or mutation.target
        target = proposed.get("target")
        new_condition = proposed.get("condition")

        matching_edges = [
            e for e in new_graph.edges
            if e.source_node_id == source and (target is None or e.target_node_id == target)
        ]

        if not matching_edges:
            raise ValueError(f"No matching edge found originating from '{source}' to apply routing change.")

        for edge in matching_edges:
            edge.condition = new_condition

        return new_graph
