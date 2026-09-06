"""ContextMutator modifies node input mapping and output key projections."""

from reco.diagnostics.taxonomy import MutationType
from reco.engine.models import GraphDefinition
from reco.mutation.models import MutationCandidate
from reco.mutation.mutators.base import BaseMutator


class ContextMutator(BaseMutator):
    """Mutates node input mappings and output keys to prevent context overflow or missing state."""

    def can_handle(self, mutation: MutationCandidate) -> bool:
        return mutation.mutation_type == MutationType.CONTEXT_CHANGE

    def apply(self, graph: GraphDefinition, mutation: MutationCandidate) -> GraphDefinition:
        new_graph = self.clone_graph(graph)
        target_node_id = mutation.target

        if target_node_id not in new_graph.nodes:
            raise ValueError(f"Target node '{target_node_id}' does not exist in graph nodes.")

        node = new_graph.nodes[target_node_id]
        proposed = mutation.proposed_change

        if "input_mapping" in proposed:
            mapping = proposed["input_mapping"]
            if not isinstance(mapping, dict):
                raise ValueError("Context mutation 'input_mapping' must be a dictionary.")
            if proposed.get("merge", False):
                node.input_mapping.update(mapping)
            else:
                node.input_mapping = mapping

        if "output_key" in proposed:
            node.output_key = proposed["output_key"]

        return new_graph
