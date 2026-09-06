"""RetryPolicyMutator updates node retry counts and retryable error filters within safe bounds."""

from reco.diagnostics.taxonomy import MutationType
from reco.engine.models import GraphDefinition
from reco.mutation.models import MutationCandidate
from reco.mutation.mutators.base import BaseMutator

MAX_PERMISSIBLE_RETRIES = 5


class RetryPolicyMutator(BaseMutator):
    """Mutates bounded retry count and retryable error conditions on nodes."""

    def can_handle(self, mutation: MutationCandidate) -> bool:
        return mutation.mutation_type == MutationType.RETRY_POLICY_CHANGE

    def apply(self, graph: GraphDefinition, mutation: MutationCandidate) -> GraphDefinition:
        new_graph = self.clone_graph(graph)
        target_node_id = mutation.target

        if target_node_id not in new_graph.nodes:
            raise ValueError(f"Target node '{target_node_id}' does not exist in graph nodes.")

        node = new_graph.nodes[target_node_id]
        proposed = mutation.proposed_change

        if "max_retries" in proposed:
            retries = int(proposed["max_retries"])
            if retries < 0 or retries > MAX_PERMISSIBLE_RETRIES:
                raise ValueError(
                    f"max_retries ({retries}) exceeds safe bounds [0, {MAX_PERMISSIBLE_RETRIES}]. "
                    "Infinite or excessive retries are forbidden."
                )
            node.max_retries = retries

        if "retryable_errors" in proposed:
            errors = proposed["retryable_errors"]
            if not isinstance(errors, list):
                raise ValueError("retryable_errors must be a list of error substrings.")
            node.retryable_errors = errors

        return new_graph
