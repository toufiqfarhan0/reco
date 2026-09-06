"""Multi-Candidate Pool Generator for Autonomous Agent Engineering (Track 1).

Synthesizes competing architectural candidate variants per optimization cycle:
- Candidate A (Prompt Specialist): Targeted prompt refinement with edge-case instructions and few-shot formatting hints.
- Candidate B (Verifier Specialist): Injects verification and schema-conformance guardrails.
- Candidate C (Topology / Tool Specialist): Restructures graph topology or assigns specialized analytical tools.

All candidates are strictly validated with CandidateValidator to eliminate hallucinated tools and broken DAGs.
"""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from reco.diagnostics.taxonomy import DiagnosticReport, FailureCategory, FailureDiagnostic
from reco.engine.models import AgentArchitecture, EdgeSpec, NodeSpec, NodeType
from reco.evaluators.scorecard import Scorecard
from reco.mutation.mutators.prompt_mutator import PromptMutator
from reco.mutation.mutators.tool_mutator import ToolAssignmentMutator
from reco.mutation.mutators.topology_mutator import TopologyMutator
from reco.mutation.mutators.verifier_mutator import VerifierNodeMutator
from reco.mutation.validator import CandidateDiff, CandidateValidator, ValidationResult
from reco.tools.registry import ToolRegistry


class CandidateVariant(BaseModel):
    """A competing candidate architecture synthesized for tournament exploration."""

    id: str = Field(description="Candidate identifier in tournament ('A', 'B', or 'C')")
    name: str = Field(description="Descriptive candidate architecture name")
    specialist_type: str = Field(description="Specialist role: 'prompt', 'verifier', or 'topology_tool'")
    tag: str = Field(default="", description="Generation or category badge label")
    generation: int = Field(default=1, description="Evolution generation number")
    description: str = Field(default="", description="Summary of architectural mutations applied")
    architecture: AgentArchitecture = Field(description="The validated mutated DAG architecture")
    applied_mutators: List[str] = Field(default_factory=list, description="Mutators executed")
    targeted_node: str = Field(default="", description="Primary target node modified")
    diff: Optional[CandidateDiff] = Field(default=None, description="Architectural diff against baseline")
    validation_result: Optional[ValidationResult] = Field(default=None, description="Structural validation report")
    scorecard: Optional[Scorecard] = Field(default=None, description="4-axis evaluated scorecard")
    win_rate: float = Field(default=0.0, description="Tournament win rate percentage (0.0 to 100.0)")
    status: str = Field(
        default="candidate",
        description="Candidate tournament status: 'candidate', 'pareto_dominant', 'verified_champion', or 'rejected'"
    )
    prompt_diff: Optional[Dict[str, str]] = Field(
        default=None,
        description="Side-by-side prompt modification delta (original vs mutated)"
    )
    config_diff: Optional[Dict[str, str]] = Field(
        default=None,
        description="Side-by-side configuration delta (original vs mutated)"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert CandidateVariant to dictionary structure matching the frontend UI model."""
        return {
            "id": self.id,
            "name": self.name,
            "tag": self.tag,
            "generation": self.generation,
            "description": self.description,
            "scorecard": self.scorecard.model_dump() if self.scorecard else None,
            "mutator_applied": ", ".join(self.applied_mutators) or "None",
            "targeted_node": self.targeted_node,
            "prompt_diff": self.prompt_diff or {"original": "", "mutated": ""},
            "config_diff": self.config_diff or {"original": "", "mutated": ""},
            "win_rate": round(self.win_rate, 1),
            "status": self.status,
        }


class CandidatePool(BaseModel):
    """Collection of competing candidate variants for tournament evaluation."""

    baseline_id: str = Field(description="ID of baseline parent architecture")
    candidates: List[CandidateVariant] = Field(default_factory=list, description="Pool of competing candidate variants")

    def get_candidate(self, candidate_id: str) -> Optional[CandidateVariant]:
        """Lookup candidate by tournament ID ('A', 'B', 'C')."""
        for cand in self.candidates:
            if cand.id.upper() == candidate_id.upper():
                return cand
        return None

    def __len__(self) -> int:
        return len(self.candidates)

    def __iter__(self):
        return iter(self.candidates)

    def __getitem__(self, idx: int) -> CandidateVariant:
        return self.candidates[idx]

    def to_markdown(self) -> str:
        """Render a markdown summary table of the candidate pool."""
        lines = [
            f"### Multi-Candidate Exploration Pool (Parent: `{self.baseline_id}`)",
            "",
            "| ID | Specialist Role | Mutators Applied | Targeted Node | Description | Valid |",
            "| :- | :--- | :--- | :--- | :--- | :-: |",
        ]
        for c in self.candidates:
            is_valid = "Yes" if (c.validation_result and c.validation_result.is_valid) else "No"
            muts = ", ".join(c.applied_mutators) or "None"
            lines.append(
                f"| **{c.id}** | {c.specialist_type.title()} | `{muts}` | `{c.targeted_node}` | {c.description} | {is_valid} |"
            )
        lines.append("")
        return "\n".join(lines)


class CandidatePoolGenerator:
    """Synthesizes diverse, competing candidate variants from failure diagnostics."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        validator: Optional[CandidateValidator] = None,
        prompt_mutator: Optional[PromptMutator] = None,
        verifier_mutator: Optional[VerifierNodeMutator] = None,
        tool_mutator: Optional[ToolAssignmentMutator] = None,
        topology_mutator: Optional[TopologyMutator] = None,
    ):
        self.tool_registry = tool_registry or ToolRegistry.create_reconciliation_default()
        self.validator = validator or CandidateValidator(tool_registry=self.tool_registry)
        self.prompt_mutator = prompt_mutator or PromptMutator(tool_registry=self.tool_registry)
        self.verifier_mutator = verifier_mutator or VerifierNodeMutator(tool_registry=self.tool_registry)
        self.tool_mutator = tool_mutator or ToolAssignmentMutator(tool_registry=self.tool_registry)
        self.topology_mutator = topology_mutator or TopologyMutator(tool_registry=self.tool_registry)

    def generate_pool(
        self,
        baseline_architecture: AgentArchitecture,
        diagnostic_report: DiagnosticReport
    ) -> CandidatePool:
        """Synthesize 3 competing candidate variants (A, B, C) and validate each against DAG integrity rules.

        Args:
            baseline_architecture: Parent baseline DAG architecture.
            diagnostic_report: Diagnostics from optimization split failure analysis.

        Returns:
            CandidatePool containing validated Candidate A, Candidate B, and Candidate C.

        Raises:
            ValueError: If any candidate fails structural validation or contains hallucinated tools.
        """
        # 1. Synthesize Candidate A (Prompt Specialist)
        cand_a = self._synthesize_candidate_a(baseline_architecture, diagnostic_report)

        # 2. Synthesize Candidate B (Verifier Specialist)
        cand_b = self._synthesize_candidate_b(baseline_architecture, diagnostic_report)

        # 3. Synthesize Candidate C (Topology / Tool Specialist)
        cand_c = self._synthesize_candidate_c(baseline_architecture, diagnostic_report)

        pool = CandidatePool(
            baseline_id=baseline_architecture.id,
            candidates=[cand_a, cand_b, cand_c]
        )

        return pool

    def generate(
        self,
        baseline_architecture: AgentArchitecture,
        diagnostic_report: DiagnosticReport
    ) -> CandidatePool:
        """Alias for generate_pool."""
        return self.generate_pool(baseline_architecture, diagnostic_report)

    def _synthesize_candidate_a(
        self,
        baseline: AgentArchitecture,
        diagnostic_report: DiagnosticReport
    ) -> CandidateVariant:
        """Synthesize Candidate A (Prompt Specialist).

        Targeted prompt refinement with edge-case instructions, schema constraints,
        and few-shot formatting hints.
        """
        arch = copy.deepcopy(baseline)
        arch.id = f"cand_A_{uuid.uuid4().hex[:6]}"
        arch.name = f"{baseline.name.split('_V')[0]}_Candidate_A_PromptSpecialist"
        arch.metadata["specialist_type"] = "prompt"
        arch.metadata["generation"] = 1

        # Formulate edge-case and domain constraints from diagnostics
        constraints = [
            "Handle casing variations: perform case-insensitive comparison for ID matches.",
            "Handle whitespace padding: strip leading and trailing whitespace from transaction keys.",
            "Handle currency formatting: parse currency symbols ($, EUR) and normalize amounts to float.",
            "Discrepancy isolation: isolate records with mismatched amounts into discrepancy_ids.",
            "Duplicate identification: flag multiple records sharing identical transaction keys in duplicate_ids.",
        ]

        formatting_rules = {
            "required_keys": [
                "matched_ids", "unmatched_source_ids", "unmatched_target_ids",
                "discrepancy_ids", "duplicate_ids", "matched_count", "status"
            ],
            "enforce_strict_keys": True,
            "edge_case_hints": ["strip_whitespace", "normalize_casing", "parse_currency_symbols"],
        }

        few_shot_hints = [
            {
                "input": {"id": "tx1003", "amount": "$1,250.00"},
                "normalized": {"id": "TX1003", "amount": 1250.0}
            }
        ]

        # First failure diagnostic if available
        first_diag = diagnostic_report.failure_diagnostics[0] if diagnostic_report.failure_diagnostics else None

        arch = self.prompt_mutator.mutate(
            arch,
            diagnostic=first_diag,
            constraints=constraints,
            formatting_rules=formatting_rules,
            few_shot_examples=few_shot_hints
        )

        # Strict validation
        val_res = self.validator.validate(arch, tool_registry=self.tool_registry)
        if not val_res.is_valid:
            raise ValueError(f"Candidate A validation failed: {'; '.join(val_res.errors)}")

        diff = self.validator.generate_diff(baseline, arch)

        original_prompt = "reasoning_node -> Standard transaction reconciliation prompt"
        mutated_prompt = (
            "reasoning_node -> Enhanced prompt with case-insensitivity, whitespace normalization, "
            "currency parsing ($1,250.00 -> 1250.0), and strict schema key enforcement."
        )

        return CandidateVariant(
            id="A",
            name="Candidate A (Prompt Specialist)",
            specialist_type="prompt",
            tag="Gen 1 - Prompt Specialist",
            generation=1,
            description="Targeted prompt refinement injecting domain constraints, edge-case normalization rules, and few-shot formatting hints.",
            architecture=arch,
            applied_mutators=["PromptMutator"],
            targeted_node="reasoning_node",
            diff=diff,
            validation_result=val_res,
            prompt_diff={"original": original_prompt, "mutated": mutated_prompt},
            config_diff={
                "original": "domain_constraints: []\nschema_enforced: false",
                "mutated": "+ domain_constraints: [normalize_casing, strip_whitespace, parse_currency]\n+ schema_enforced: true"
            }
        )

    def _synthesize_candidate_b(
        self,
        baseline: AgentArchitecture,
        diagnostic_report: DiagnosticReport
    ) -> CandidateVariant:
        """Synthesize Candidate B (Verifier Specialist).

        Injects dedicated verification and schema-conformance guardrails before output.
        """
        arch = copy.deepcopy(baseline)
        arch.id = f"cand_B_{uuid.uuid4().hex[:6]}"
        arch.name = f"{baseline.name.split('_V')[0]}_Candidate_B_VerifierSpecialist"
        arch.metadata["specialist_type"] = "verifier"
        arch.metadata["generation"] = 1

        first_diag = diagnostic_report.failure_diagnostics[0] if diagnostic_report.failure_diagnostics else None

        # Inject or upgrade dedicated verifier node
        arch = self.verifier_mutator.mutate(
            arch,
            diagnostic=first_diag,
            node_id="verifier_node",
            strict_mode=True
        )

        # Strengthen verifier node config with schema conformance
        for node in arch.nodes:
            if node.type == NodeType.VERIFIER:
                node.config["assert_reconciliation_integrity"] = True
                node.config["validate_discrepancy_counts"] = True
                node.config["enforce_schema"] = True
                node.config["required_keys"] = [
                    "matched_ids", "unmatched_source_ids", "unmatched_target_ids",
                    "discrepancy_ids", "duplicate_ids", "status"
                ]

        # Strict validation
        val_res = self.validator.validate(arch, tool_registry=self.tool_registry)
        if not val_res.is_valid:
            raise ValueError(f"Candidate B validation failed: {'; '.join(val_res.errors)}")

        diff = self.validator.generate_diff(baseline, arch)

        original_config = "nodes: [input_node, tool_reconcile, reasoning_node, output_node]"
        mutated_config = (
            "+ nodes: [input_node, tool_reconcile, reasoning_node, verifier_node, output_node]\n"
            "+ verifier_node: strict_mode=true, assert_reconciliation_integrity=true, validate_discrepancy_counts=true"
        )

        return CandidateVariant(
            id="B",
            name="Candidate B (Verifier Specialist)",
            specialist_type="verifier",
            tag="Gen 1 - Verifier Specialist",
            generation=1,
            description="Architectural mutation injecting dedicated verification node and schema-conformance guardrails.",
            architecture=arch,
            applied_mutators=["VerifierNodeMutator"],
            targeted_node="verifier_node",
            diff=diff,
            validation_result=val_res,
            prompt_diff={
                "original": "Direct output emission without verification",
                "mutated": "Interposed verifier node asserting discrepancy counts and output schema invariants"
            },
            config_diff={"original": original_config, "mutated": mutated_config}
        )

    def _synthesize_candidate_c(
        self,
        baseline: AgentArchitecture,
        diagnostic_report: DiagnosticReport
    ) -> CandidateVariant:
        """Synthesize Candidate C (Topology / Tool Specialist).

        Restructures graph topology and assigns specialized analytical tools
        (e.g., smart_reconcile for reconciliation, or domain tools).
        """
        arch = copy.deepcopy(baseline)
        arch.id = f"cand_C_{uuid.uuid4().hex[:6]}"
        arch.name = f"{baseline.name.split('_V')[0]}_Candidate_C_TopologyToolSpecialist"
        arch.metadata["specialist_type"] = "topology_tool"
        arch.metadata["generation"] = 1

        applied_mutators = []

        # Determine if baseline has an older tool to upgrade
        has_exact = any(n.tool_name == "exact_reconcile" for n in arch.nodes if n.type == NodeType.TOOL)
        domain = arch.task_spec.domain or "financial_reconciliation"

        if has_exact or "reconcil" in domain:
            # Upgrade exact_reconcile to smart_reconcile
            if self.tool_registry.has("smart_reconcile"):
                arch = self.tool_mutator.mutate(
                    arch,
                    target_tool="smart_reconcile",
                    replace_tool="exact_reconcile" if has_exact else None
                )
                applied_mutators.append("ToolAssignmentMutator")

        elif "anomaly" in domain:
            # Assign anomaly tools if available
            if self.tool_registry.has("check_threshold"):
                arch = self.tool_mutator.mutate(arch, target_tool="check_threshold")
                applied_mutators.append("ToolAssignmentMutator")

        elif "research" in domain:
            # Assign research tools if available
            if self.tool_registry.has("compare_metrics"):
                arch = self.tool_mutator.mutate(arch, target_tool="compare_metrics")
                applied_mutators.append("ToolAssignmentMutator")

        else:
            # Default fallback tool assignment
            if self.tool_registry.has("smart_reconcile"):
                arch = self.tool_mutator.mutate(arch, target_tool="smart_reconcile")
                applied_mutators.append("ToolAssignmentMutator")

        # Also optimize routing if needed
        arch = self.topology_mutator.mutate(arch, branch_type="repair_routing")
        if "TopologyMutator" not in applied_mutators:
            applied_mutators.append("TopologyMutator")

        # Strict validation
        val_res = self.validator.validate(arch, tool_registry=self.tool_registry)
        if not val_res.is_valid:
            raise ValueError(f"Candidate C validation failed: {'; '.join(val_res.errors)}")

        diff = self.validator.generate_diff(baseline, arch)

        targeted_node = "tool_smart_reconcile" if any(n.id == "tool_smart_reconcile" for n in arch.nodes) else "tool_node"

        original_config = "tool: exact_reconcile\nnormalizations: none"
        mutated_config = (
            "+ tool: smart_reconcile\n"
            "+ normalizations: [strip_whitespace, uppercase_casing, currency_symbol_parsing]"
        )

        return CandidateVariant(
            id="C",
            name="Candidate C (Topology & Tool Specialist)",
            specialist_type="topology_tool",
            tag="Gen 1 - Tool & Topology Specialist",
            generation=1,
            description="Structural mutation upgrading tool assignments to smart_reconcile and optimizing execution topology.",
            architecture=arch,
            applied_mutators=applied_mutators,
            targeted_node=targeted_node,
            diff=diff,
            validation_result=val_res,
            prompt_diff={
                "original": "tool: exact_reconcile (rigid equality matching)",
                "mutated": "tool: smart_reconcile (normalizes casing, strips whitespace, parses $ symbols)"
            },
            config_diff={"original": original_config, "mutated": mutated_config}
        )
