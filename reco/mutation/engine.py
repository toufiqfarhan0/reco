"""Autonomous Mutation Engine orchestrating targeted DAG mutations and candidate validation."""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from reco.diagnostics.taxonomy import DiagnosticReport, FailureCategory, FailureDiagnostic
from reco.engine.models import AgentArchitecture
from reco.mutation.mutators.base import BaseMutator
from reco.mutation.mutators.prompt_mutator import PromptMutator
from reco.mutation.mutators.retry_mutator import RetryPolicyMutator
from reco.mutation.mutators.tool_mutator import ToolAssignmentMutator
from reco.mutation.mutators.topology_mutator import TopologyMutator
from reco.mutation.mutators.verifier_mutator import VerifierNodeMutator
from reco.mutation.validator import CandidateDiff, CandidateValidator, ValidationResult
from reco.tools.registry import ToolRegistry


class MutationResult(BaseModel):
    """Outcome of a DAG architecture mutation cycle."""

    success: bool = Field(description="True if mutation succeeded and passed validation")
    candidate_architecture: Optional[AgentArchitecture] = Field(
        default=None,
        description="The mutated and validated candidate architecture"
    )
    diff: Optional[CandidateDiff] = Field(default=None, description="Visual and structural mutation delta")
    applied_mutators: List[str] = Field(default_factory=list, description="Names of mutator operators executed")
    validation_result: Optional[ValidationResult] = Field(
        default=None,
        description="Candidate structural validation report"
    )
    error: Optional[str] = Field(default=None, description="Error detail if mutation failed")


class MutationEngine:
    """Orchestrates targeted DAG mutations learned from diagnostic reports."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        validator: Optional[CandidateValidator] = None
    ):
        self.tool_registry = tool_registry or ToolRegistry.create_reconciliation_default()
        self.validator = validator or CandidateValidator(tool_registry=self.tool_registry)

        # Register standard mutators
        self.mutators: Dict[str, BaseMutator] = {
            "PromptMutator": PromptMutator(tool_registry=self.tool_registry),
            "VerifierNodeMutator": VerifierNodeMutator(tool_registry=self.tool_registry),
            "ToolAssignmentMutator": ToolAssignmentMutator(tool_registry=self.tool_registry),
            "TopologyMutator": TopologyMutator(tool_registry=self.tool_registry),
            "RetryPolicyMutator": RetryPolicyMutator(tool_registry=self.tool_registry),
        }

    def mutate(
        self,
        architecture: AgentArchitecture,
        diagnostic_report: DiagnosticReport,
        candidate_name: Optional[str] = None
    ) -> MutationResult:
        """Derive targeted mutations from failure diagnostics and produce a validated candidate DAG.

        Args:
            architecture: Baseline parent AgentArchitecture.
            diagnostic_report: Structured failure report from FailureAnalyzer.
            candidate_name: Optional descriptive label for the candidate.

        Returns:
            MutationResult containing candidate architecture and visual diff.
        """
        candidate = copy.deepcopy(architecture)
        applied_mutators: List[str] = []

        # If no failures diagnosed, return neutral result
        if not diagnostic_report.failure_diagnostics:
            diff = self.validator.generate_diff(architecture, candidate)
            val = self.validator.validate(candidate, tool_registry=self.tool_registry)
            return MutationResult(
                success=True,
                candidate_architecture=candidate,
                diff=diff,
                applied_mutators=[],
                validation_result=val
            )

        # 1. Determine priority mutators based on diagnostic report
        # Tool assignment is highest priority when tools are missing or inadequate
        mutators_to_run: List[tuple[str, FailureDiagnostic]] = []
        seen_mutators = set()

        # Priority order of resolution:
        priority_order = [
            FailureCategory.TOOL_SELECTION_ERROR,
            FailureCategory.ROUTING_MISDIRECT,
            FailureCategory.VERIFICATION_MISS,
            FailureCategory.SCHEMA_VIOLATION,
            FailureCategory.TOOL_PARAMETER_ERROR,
            FailureCategory.PROMPT_AMBIGUITY,
            FailureCategory.RETRY_EXHAUSTION,
            FailureCategory.TIMEOUT_EXCEEDED,
            FailureCategory.UNHANDLED_EXCEPTION,
            FailureCategory.STATE_CORRUPTION,
            FailureCategory.CONTEXT_OVERFLOW,
            FailureCategory.MODEL_CAPABILITY_LIMIT,
        ]

        # Select diagnostics following priority
        for cat in priority_order:
            cat_diags = diagnostic_report.get_by_category(cat)
            for diag in cat_diags:
                mutator_name = diag.recommended_mutator or "PromptMutator"
                if mutator_name not in seen_mutators:
                    mutators_to_run.append((mutator_name, diag))
                    seen_mutators.add(mutator_name)

        # Fallback if no specific mapping
        if not mutators_to_run:
            first_diag = diagnostic_report.failure_diagnostics[0]
            mutators_to_run.append((first_diag.recommended_mutator or "PromptMutator", first_diag))

        # 2. Execute selected mutation operators
        for mutator_name, diag in mutators_to_run:
            mutator = self.mutators.get(mutator_name)
            if not mutator:
                continue

            try:
                candidate = mutator.mutate(candidate, diagnostic=diag)
                applied_mutators.append(mutator_name)
            except Exception as exc:
                return MutationResult(
                    success=False,
                    candidate_architecture=None,
                    diff=None,
                    applied_mutators=applied_mutators,
                    validation_result=None,
                    error=f"Mutator '{mutator_name}' failed: {str(exc)}"
                )

        # 3. Update candidate identity and lineage metadata
        new_gen = architecture.metadata.get("generation", 0) + 1
        cid = f"cand_{uuid.uuid4().hex[:8]}"
        cname = candidate_name or f"{architecture.name.split('_V')[0]}_V{new_gen}"

        candidate.id = cid
        candidate.name = cname
        candidate.metadata["parent_architecture_id"] = architecture.id
        candidate.metadata["generation"] = new_gen
        candidate.metadata["applied_mutators"] = applied_mutators
        candidate.metadata["diagnosed_failure_count"] = len(diagnostic_report.failure_diagnostics)

        # 4. Strict Validation of Mutated Candidate
        val_result = self.validator.validate(candidate, tool_registry=self.tool_registry)
        if not val_result.is_valid:
            return MutationResult(
                success=False,
                candidate_architecture=candidate,
                diff=None,
                applied_mutators=applied_mutators,
                validation_result=val_result,
                error=f"Candidate validation failed: {'; '.join(val_result.errors)}"
            )

        # 5. Generate Visual Diff against parent architecture
        diff = self.validator.generate_diff(architecture, candidate)

        return MutationResult(
            success=True,
            candidate_architecture=candidate,
            diff=diff,
            applied_mutators=applied_mutators,
            validation_result=val_result
        )

    def mutate_with_operator(
        self,
        architecture: AgentArchitecture,
        operator_name: str,
        diagnostic: Optional[FailureDiagnostic] = None,
        candidate_name: Optional[str] = None,
        **kwargs: Any
    ) -> MutationResult:
        """Directly invoke a specific mutation operator by name."""
        mutator = self.mutators.get(operator_name)
        if not mutator:
            raise KeyError(f"Mutator '{operator_name}' not registered in MutationEngine.")

        candidate = copy.deepcopy(architecture)
        try:
            candidate = mutator.mutate(candidate, diagnostic=diagnostic, **kwargs)
        except Exception as exc:
            return MutationResult(
                success=False,
                candidate_architecture=None,
                diff=None,
                applied_mutators=[],
                error=f"Mutator '{operator_name}' execution error: {str(exc)}"
            )

        new_gen = architecture.metadata.get("generation", 0) + 1
        candidate.id = f"cand_{uuid.uuid4().hex[:8]}"
        candidate.name = candidate_name or f"{architecture.name}_Mutated"
        candidate.metadata["parent_architecture_id"] = architecture.id
        candidate.metadata["generation"] = new_gen
        candidate.metadata["applied_mutators"] = [operator_name]

        val_result = self.validator.validate(candidate, tool_registry=self.tool_registry)
        if not val_result.is_valid:
            return MutationResult(
                success=False,
                candidate_architecture=candidate,
                diff=None,
                applied_mutators=[operator_name],
                validation_result=val_result,
                error=f"Validation failed: {'; '.join(val_result.errors)}"
            )

        diff = self.validator.generate_diff(architecture, candidate)
        return MutationResult(
            success=True,
            candidate_architecture=candidate,
            diff=diff,
            applied_mutators=[operator_name],
            validation_result=val_result
        )
