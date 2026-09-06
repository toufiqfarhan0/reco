"""PromptMutator applies targeted system prompt modifications with strict traceability."""

from reco.diagnostics.taxonomy import MutationType
from reco.engine.models import GraphDefinition
from reco.mutation.models import MutationCandidate
from reco.mutation.mutators.base import BaseMutator


class PromptMutator(BaseMutator):
    """Safely updates or patches node system prompts without modifying the original graph."""

    def can_handle(self, mutation: MutationCandidate) -> bool:
        return mutation.mutation_type == MutationType.PROMPT_CHANGE

    def apply(self, graph: GraphDefinition, mutation: MutationCandidate) -> GraphDefinition:
        new_graph = self.clone_graph(graph)
        target_node_id = mutation.target

        if target_node_id not in new_graph.nodes:
            raise ValueError(f"Target node '{target_node_id}' does not exist in graph nodes.")

        node = new_graph.nodes[target_node_id]
        old_prompt = node.system_prompt
        proposed = mutation.proposed_change

        if "new_prompt" in proposed:
            new_prompt = proposed["new_prompt"]
        elif "append" in proposed:
            new_prompt = f"{old_prompt.strip()}\n\n[Optimization Directive]: {proposed['append'].strip()}"
        elif "instructions" in proposed:
            new_prompt = f"{old_prompt.strip()}\n\n[Optimization Directive]: {proposed['instructions'].strip()}"
        elif "patch" in proposed:
            new_prompt = f"{old_prompt.strip()}\n\n[Patch]: {proposed['patch'].strip()}"
        else:
            # If proposed_change doesn't have explicit text, use rationale as guidance directive
            new_prompt = f"{old_prompt.strip()}\n\n[Optimization Guidance]: {mutation.rationale.strip()}"

        node.system_prompt = new_prompt
        # Record traceability metadata on the node
        node.metadata["prompt_mutation_audit"] = {
            "old_prompt": old_prompt,
            "new_prompt": new_prompt,
            "rationale": mutation.rationale,
            "source_diagnoses": [str(d) for d in mutation.source_diagnosis_ids],
        }

        return new_graph
