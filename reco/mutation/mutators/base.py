"""Abstract Base Mutator for DAG architecture transformation."""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from reco.diagnostics.taxonomy import FailureDiagnostic
from reco.engine.models import AgentArchitecture
from reco.tools.registry import ToolRegistry


class BaseMutator(ABC):
    """Abstract base class for targeted architectural DAG mutation operators."""

    name: str = "base_mutator"

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry or ToolRegistry.create_reconciliation_default()

    @abstractmethod
    def mutate(
        self,
        architecture: AgentArchitecture,
        diagnostic: Optional[FailureDiagnostic] = None,
        **kwargs: Any
    ) -> AgentArchitecture:
        """Apply targeted mutation operator to an architecture DAG.

        Args:
            architecture: Parent AgentArchitecture to mutate.
            diagnostic: Optional FailureDiagnostic driving this mutation.
            kwargs: Additional mutation parameters.

        Returns:
            Mutated clone of the AgentArchitecture.
        """
        raise NotImplementedError

    @staticmethod
    def clone_architecture(architecture: AgentArchitecture) -> AgentArchitecture:
        """Deepcopy architecture to ensure immutability of parent graph."""
        return copy.deepcopy(architecture)
