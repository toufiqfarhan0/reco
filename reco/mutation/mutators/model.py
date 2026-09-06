"""ModelMutator updates node model configuration behind the ModelGateway abstraction."""

from reco.diagnostics.taxonomy import MutationType
from reco.engine.models import GraphDefinition
from reco.mutation.models import MutationCandidate
from reco.mutation.mutators.base import BaseMutator


class ModelMutator(BaseMutator):
    """Mutates node model assignment and inference parameters."""

    def can_handle(self, mutation: MutationCandidate) -> bool:
        return mutation.mutation_type == MutationType.MODEL_CHANGE

    def apply(self, graph: GraphDefinition, mutation: MutationCandidate) -> GraphDefinition:
        new_graph = self.clone_graph(graph)
        target_node_id = mutation.target

        if target_node_id not in new_graph.nodes:
            raise ValueError(f"Target node '{target_node_id}' does not exist in graph nodes.")

        node = new_graph.nodes[target_node_id]
        proposed = mutation.proposed_change

        model_config = proposed.get("model_config") or proposed
        if not isinstance(model_config, dict):
            raise ValueError("Model mutation payload must be a dictionary.")

        # Update node model_config_data
        node.model_config_data.update(model_config)
        return new_graph
