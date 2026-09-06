"""RetryPolicyMutator operator attaching exponential backoff and retry policies to brittle nodes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from reco.diagnostics.taxonomy import FailureDiagnostic
from reco.engine.models import AgentArchitecture, NodeType
from reco.mutation.mutators.base import BaseMutator


class RetryPolicyMutator(BaseMutator):
    """Attaches retry/backoff policies to brittle nodes to prevent transient failures."""

    name = "RetryPolicyMutator"

    def mutate(
        self,
        architecture: AgentArchitecture,
        diagnostic: Optional[FailureDiagnostic] = None,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        target_node_id: Optional[str] = None,
        **kwargs: Any
    ) -> AgentArchitecture:
        """Attach retry policies to target or brittle nodes.

        Args:
            architecture: Target AgentArchitecture.
            diagnostic: FailureDiagnostic identifying brittle node.
            max_retries: Maximum execution attempts.
            backoff_factor: Multiplier for exponential backoff delay.
            target_node_id: Explicit node ID to apply retry policy to.

        Returns:
            Mutated AgentArchitecture.
        """
        arch = self.clone_architecture(architecture)

        policy = {
            "max_retries": max_retries,
            "backoff_factor": backoff_factor,
            "retry_on": ["TimeoutError", "RuntimeError", "ConnectionError", "Exception"],
            "enabled": True
        }

        target_id = target_node_id or (diagnostic.target_node_id if diagnostic else None)

        applied = False
        if target_id:
            try:
                node = arch.get_node(target_id)
                node.config["retry_policy"] = policy
                applied = True
            except KeyError:
                pass

        # If no specific node was found, apply to all tool nodes
        if not applied:
            for node in arch.nodes:
                if node.type in (NodeType.TOOL, NodeType.REASONING):
                    node.config["retry_policy"] = policy

        return arch
