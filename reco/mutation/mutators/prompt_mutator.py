"""PromptMutator operator injecting domain constraints, few-shot hints, and formatting rules."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from reco.diagnostics.taxonomy import FailureCategory, FailureDiagnostic
from reco.engine.models import AgentArchitecture, NodeType
from reco.mutation.mutators.base import BaseMutator


class PromptMutator(BaseMutator):
    """Injects domain constraints, few-shot hints, or formatting instructions learned from errors."""

    name = "PromptMutator"

    def mutate(
        self,
        architecture: AgentArchitecture,
        diagnostic: Optional[FailureDiagnostic] = None,
        constraints: Optional[List[str]] = None,
        formatting_rules: Optional[Dict[str, Any]] = None,
        few_shot_examples: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> AgentArchitecture:
        """Inject domain constraints, hints, or schema instructions into reasoning and output nodes.

        Args:
            architecture: Target architecture.
            diagnostic: FailureDiagnostic informing the prompt updates.
            constraints: Explicit domain rules to inject.
            formatting_rules: Specific output formatting requirements.
            few_shot_examples: Sample inputs/outputs to guide reasoning.

        Returns:
            Mutated AgentArchitecture.
        """
        arch = self.clone_architecture(architecture)

        # 1. Gather hints to inject based on diagnostic
        injected_constraints = list(constraints or [])
        injected_formatting = dict(formatting_rules or {})
        injected_examples = list(few_shot_examples or [])

        if diagnostic:
            if diagnostic.category == FailureCategory.TOOL_PARAMETER_ERROR:
                injected_constraints.append(
                    f"Parameter constraint: Tool '{diagnostic.target_node_id}' requires strict parameter schemas."
                )
                if diagnostic.metadata.get("error"):
                    injected_constraints.append(f"Avoid parameter violation: {diagnostic.metadata['error']}")

            elif diagnostic.category == FailureCategory.SCHEMA_VIOLATION:
                missing = diagnostic.metadata.get("missing_keys", [])
                injected_formatting["required_keys"] = [
                    "matched_ids", "unmatched_source_ids", "unmatched_target_ids",
                    "discrepancy_ids", "duplicate_ids", "matched_count", "status"
                ]
                injected_formatting["enforce_strict_keys"] = True
                if missing:
                    injected_formatting["explicitly_include"] = missing

            elif diagnostic.category == FailureCategory.PROMPT_AMBIGUITY:
                injected_constraints.extend([
                    "Synthesize observations for all processed transaction sets.",
                    "Explicitly verify 1:1 ID and amount correspondences before marking status.",
                    "Distinguish between unilateral missing records and amount variances."
                ])

            elif diagnostic.category == FailureCategory.CONTEXT_OVERFLOW:
                injected_constraints.append(
                    "Context management: Truncate intermediate debug logs and keep summary objects concise."
                )

        # 2. Mutate Reasoning Nodes
        for node in arch.nodes:
            if node.type == NodeType.REASONING:
                current_constraints = node.config.get("domain_constraints", [])
                node.config["domain_constraints"] = list(set(current_constraints + injected_constraints))

                if injected_examples:
                    node.config["few_shot_hints"] = injected_examples

                node.config["prompt_enhanced"] = True

        # 3. Mutate Output Node formatting instructions
        for node in arch.nodes:
            if node.type == NodeType.OUTPUT:
                current_rules = node.config.get("formatting_instructions", {})
                current_rules.update(injected_formatting)
                node.config["formatting_instructions"] = current_rules
                node.config["schema_enforced"] = True

        # 4. If target_node_id specified in diagnostic, inject parameter hints
        if diagnostic and diagnostic.target_node_id:
            try:
                target_node = arch.get_node(diagnostic.target_node_id)
                target_node.config["parameter_hints"] = {
                    "learned_remedy": diagnostic.remedy_suggestion,
                    "target_schema": "strictly_validate_inputs"
                }
            except KeyError:
                pass

        return arch
