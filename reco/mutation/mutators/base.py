"""Base abstract class for specialized architectural mutators."""

import copy
from abc import ABC, abstractmethod
from reco.engine.models import GraphDefinition
from reco.mutation.models import MutationCandidate


class BaseMutator(ABC):
    """Abstract base class for all structural and configuration mutators."""

    @abstractmethod
    def can_handle(self, mutation: MutationCandidate) -> bool:
        """Return True if this mutator handles the candidate's mutation type."""
        pass

    @abstractmethod
    def apply(self, graph: GraphDefinition, mutation: MutationCandidate) -> GraphDefinition:
        """Apply the candidate mutation to a deep copy of the graph definition.

        Must NEVER mutate the input graph in place.
        """
        pass

    def clone_graph(self, graph: GraphDefinition) -> GraphDefinition:
        """Safely create an isolated, deep copy of a GraphDefinition."""
        return GraphDefinition(**copy.deepcopy(graph.model_dump(mode="json")))
