"""VerifierNodeMutator operator injecting dedicated verification and guardrail nodes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from reco.diagnostics.taxonomy import FailureDiagnostic
from reco.engine.models import AgentArchitecture, EdgeSpec, NodeSpec, NodeType
from reco.mutation.mutators.base import BaseMutator


class VerifierNodeMutator(BaseMutator):
    """Injects a dedicated verification/guardrail node prior to output, or strengthens existing verifier."""

    name = "VerifierNodeMutator"

    def mutate(
        self,
        architecture: AgentArchitecture,
        diagnostic: Optional[FailureDiagnostic] = None,
        node_id: str = "verifier_node",
        strict_mode: bool = True,
        **kwargs: Any
    ) -> AgentArchitecture:
        """Inject or upgrade verification guardrail node in the architecture DAG.

        Args:
            architecture: Target AgentArchitecture.
            diagnostic: FailureDiagnostic informing the mutation.
            node_id: Desired ID for the injected verifier node.
            strict_mode: Whether to enable strict guardrail verification rules.

        Returns:
            Mutated AgentArchitecture with guaranteed verifier guardrails.
        """
        arch = self.clone_architecture(architecture)

        # 1. Check if a verifier node already exists
        existing_verifiers = [n for n in arch.nodes if n.type == NodeType.VERIFIER]

        if existing_verifiers:
            # Strengthen existing verifier node
            for v_node in existing_verifiers:
                v_node.config["strict_mode"] = strict_mode
                v_node.config["assert_reconciliation_integrity"] = True
                v_node.config["validate_discrepancy_counts"] = True
                v_node.config["tolerance_abs"] = 1e-3
                v_node.config["guardrail_enhanced"] = True
            return arch

        # 2. If missing, inject a dedicated verifier node before output_node
        output_node = None
        for n in arch.nodes:
            if n.type == NodeType.OUTPUT:
                output_node = n
                break

        if not output_node:
            output_node = NodeSpec(
                id="output_node",
                type=NodeType.OUTPUT,
                name="Structured Result Delivery",
                dependencies=[node_id]
            )
            arch.nodes.append(output_node)

        # Identify current parents of output_node
        current_parents = arch.get_parents(output_node.id)
        parent_ids = [p.id for p in current_parents] if current_parents else ["reasoning_node"]

        # If reasoning_node exists in graph, ensure it's a dependency of verifier
        if "reasoning_node" in [n.id for n in arch.nodes] and "reasoning_node" not in parent_ids:
            parent_ids.append("reasoning_node")

        # Create new verifier node
        verifier_node = NodeSpec(
            id=node_id,
            type=NodeType.VERIFIER,
            name="Output Guardrail & Discrepancy Verifier",
            config={
                "strict_mode": strict_mode,
                "assert_reconciliation_integrity": True,
                "validate_discrepancy_counts": True,
                "latency_budget_ms": arch.task_spec.latency_budget_ms,
                "cost_budget_usd": arch.task_spec.cost_budget_usd,
                "guardrail_enhanced": True
            },
            dependencies=parent_ids
        )
        arch.nodes.append(verifier_node)

        # Rewire edges: remove direct edges into output_node from upstream, route them to verifier
        new_edges: List[EdgeSpec] = []
        for edge in arch.edges:
            if edge.target == output_node.id:
                # Upstream connects to verifier instead
                new_edges.append(EdgeSpec(source=edge.source, target=node_id))
            else:
                new_edges.append(edge)

        # Connect verifier to output_node
        new_edges.append(EdgeSpec(source=node_id, target=output_node.id))
        arch.edges = new_edges

        # Update output_node dependencies to only depend on verifier
        output_node.dependencies = [node_id]

        return arch
