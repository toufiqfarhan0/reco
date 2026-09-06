"""MutationEngine coordinates candidate generation, static validation, benchmark execution, and promotion."""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from reco.benchmarks.reconciliation.benchmark import ReconciliationBenchmark
from reco.core.interfaces import ModelGateway
from reco.core.task_spec import TaskSpecification
from reco.db.models import AgentVersionRecord, ImprovementRecord
from reco.db.repositories import (
    AgentVersionRepository,
    BenchmarkRunRepository,
    FailureDiagnosisRepository,
    ImprovementRepository,
)
from reco.diagnostics.analyzer import FailureAnalyzer
from reco.diagnostics.models import FailureCluster, RootCauseDiagnosis
from reco.engine.models import GraphDefinition
from reco.evaluators.comparison import (
    ComparisonPolicy,
    PromotionAssessment,
    ScorecardComparison,
    assess_promotion,
    compare_scorecards,
)
from reco.evaluators.scorecard import Scorecard
from reco.logging import get_logger
from reco.mutation.generator import CandidateGenerator
from reco.mutation.models import AgentVersionCandidate, MutationCandidate, MutationType, OptimizationResult
from reco.mutation.mutators import (
    BaseMutator,
    ContextMutator,
    ModelMutator,
    PromptMutator,
    RetryPolicyMutator,
    RoutingMutator,
    ToolMutator,
    TopologyMutator,
    VerifierMutator,
)
from reco.mutation.validation import CandidateValidator
from reco.tools.registry import ToolRegistry, default_tool_registry

logger = get_logger("mutation.engine")


class MutationEngine:
    """Consumes failure diagnoses and creates verified, benchmarked candidate agent versions."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        model_gateway: Optional[ModelGateway] = None,
        agent_version_repo: Optional[AgentVersionRepository] = None,
        improvement_repo: Optional[ImprovementRepository] = None,
        failure_diagnosis_repo: Optional[FailureDiagnosisRepository] = None,
        benchmark_run_repo: Optional[BenchmarkRunRepository] = None,
    ):
        self.tool_registry = tool_registry or default_tool_registry
        self.model_gateway = model_gateway
        self.agent_version_repo = agent_version_repo
        self.improvement_repo = improvement_repo
        self.failure_diagnosis_repo = failure_diagnosis_repo
        self.benchmark_run_repo = benchmark_run_repo

        # Initialize modular mutator suite
        self.mutators: List[BaseMutator] = [
            PromptMutator(),
            ToolMutator(tool_registry=self.tool_registry),
            TopologyMutator(),
            VerifierMutator(),
            ModelMutator(),
            RoutingMutator(),
            ContextMutator(),
            RetryPolicyMutator(),
        ]

        self.validator = CandidateValidator(tool_registry=self.tool_registry)
        self.candidate_generator = CandidateGenerator(tool_registry=self.tool_registry)
        self.failure_analyzer = FailureAnalyzer(
            model_gateway=self.model_gateway,
            tool_registry=self.tool_registry,
        )

    def generate_candidates(
        self,
        graph: GraphDefinition,
        diagnoses: List[RootCauseDiagnosis],
        task_specification: Optional[TaskSpecification] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        parent_version_id: Optional[UUID] = None,
        max_candidates: int = 3,
        clusters: Optional[List[FailureCluster]] = None,
    ) -> List[MutationCandidate]:
        """Synthesize candidate mutations guided by failure analysis."""
        candidates = self.candidate_generator.generate(
            agent_graph=graph,
            diagnoses=diagnoses,
            task_specification=task_specification,
            available_tools=available_tools,
            parent_version_id=parent_version_id,
            max_candidates=max_candidates,
            clusters=clusters,
        )
        try:
            from reco.observability.tracer import compute_prompt_hash, get_tracer
            tracer = get_tracer()
            for cand in candidates:
                prompt_str = cand.parameters.get("system_prompt") or cand.parameters.get("prompt_patch") or ""
                prompt_h = compute_prompt_hash(prompt_str) if prompt_str else ""
                tracer.trace_mutation(
                    candidate_id=str(cand.candidate_id),
                    parent_version_id=str(parent_version_id or ""),
                    mutation_type=cand.mutation_type.value if hasattr(cand.mutation_type, "value") else str(cand.mutation_type),
                    target=cand.target,
                    prompt_hash=prompt_h,
                    change_summary=cand.rationale[:200] if cand.rationale else "",
                )
        except Exception:
            pass
        return candidates

    async def generate_candidate(
        self,
        parent_graph: GraphDefinition,
        diagnosis: RootCauseDiagnosis,
        generation: int = 1,
        candidate_idx: int = 0,
        available_tools: Optional[List[Any]] = None,
    ) -> MutationCandidate:
        """Generate and apply a single mutation candidate from a failure diagnosis."""
        tools_list = available_tools
        if tools_list and hasattr(tools_list[0], "name"):
            tools_list = [
                {"name": t.name, "description": t.description, "parameters_schema": t.parameters_schema}
                for t in tools_list
            ]
        filtered_diagnoses = [d for d in [diagnosis] if d is not None]
        cands = self.generate_candidates(
            graph=parent_graph,
            diagnoses=filtered_diagnoses,
            available_tools=tools_list,
            max_candidates=1,
        )
        if not cands:
            target_node = (diagnosis.failed_node if diagnosis else None) or list(parent_graph.nodes.keys())[0]
            rationale = (diagnosis.root_cause if diagnosis else None) or "Address diagnostic failure"
            cand = MutationCandidate(
                mutation_type=MutationType.PROMPT_CHANGE,
                target=target_node,
                proposed_change={"system_prompt": parent_graph.nodes[target_node].system_prompt + "\n\nCRITICAL: Verify edge cases, distribution thresholds, and constraints."},
                rationale=rationale,
                expected_effect="Eliminates false decisions",
                confidence=0.9,
            )
        else:
            cand = cands[0]

        agent_cand = self.apply_mutation(
            graph=parent_graph,
            mutation=cand,
            version_number=generation,
            available_tools=tools_list,
        )
        cand.mutated_graph = agent_cand.graph
        cand.is_valid = agent_cand.is_valid
        return cand

    def apply_mutation(
        self,
        graph: GraphDefinition,
        mutation: MutationCandidate,
        parent_version_id: Optional[UUID] = None,
        version_number: int = 1,
        task_spec: Optional[TaskSpecification] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentVersionCandidate:
        """Apply a mutation to a fresh immutable copy of the graph and run static validation."""
        target_mutator = next((m for m in self.mutators if m.can_handle(mutation)), None)
        if not target_mutator:
            candidate = AgentVersionCandidate(
                candidate_id=mutation.candidate_id,
                parent_version_id=parent_version_id or uuid4(),
                version_number=version_number,
                graph=graph,
                mutation=mutation,
                is_valid=False,
                rejection_reason=f"No mutator registered for mutation type '{mutation.mutation_type.value}'.",
            )
            return candidate

        try:
            mutated_graph = target_mutator.apply(graph, mutation)
            # Update graph metadata to reflect candidate mutation
            mutated_graph.metadata["parent_version_id"] = str(parent_version_id) if parent_version_id else None
            mutated_graph.metadata["version_number"] = version_number
            mutated_graph.metadata["applied_mutation"] = mutation.model_dump(mode="json")
        except Exception as exc:
            candidate = AgentVersionCandidate(
                candidate_id=mutation.candidate_id,
                parent_version_id=parent_version_id or uuid4(),
                version_number=version_number,
                graph=graph,
                mutation=mutation,
                is_valid=False,
                rejection_reason=f"Mutation application error: {exc}",
            )
            return candidate

        candidate = AgentVersionCandidate(
            candidate_id=mutation.candidate_id,
            parent_version_id=parent_version_id or uuid4(),
            version_number=version_number,
            graph=mutated_graph,
            mutation=mutation,
        )

        # Run static pre-flight validation
        self.validator.validate(candidate, task_spec=task_spec, available_tools=available_tools)
        return candidate

    async def optimize(
        self,
        graph: GraphDefinition,
        benchmark: Optional[Any] = None,
        task_specification: Optional[TaskSpecification] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        experiment_id: Optional[UUID] = None,
        parent_version_id: Optional[UUID] = None,
        policy: Optional[ComparisonPolicy] = None,
        max_candidates: int = 3,
        run_held_out: bool = True,
        baseline_scorecard: Optional[Scorecard] = None,
    ) -> OptimizationResult:
        """Execute the complete optimization loop: Execute -> Evaluate -> Diagnose -> Mutate -> Re-run -> Compare -> Promote."""
        exp_id = experiment_id or uuid4()
        parent_id = parent_version_id or uuid4()
        active_bench = benchmark or ReconciliationBenchmark(
            benchmark_run_repo=self.benchmark_run_repo,
        )
        active_policy = policy or ComparisonPolicy()

        # Step 1: Run optimization benchmark on baseline V0 if scorecard not provided
        if baseline_scorecard is None:
            baseline_run = await active_bench.run_benchmark(
                graph=graph,
                split="optimization",
                experiment_id=exp_id,
                agent_version_id=parent_id,
                persist=False,
            )
            baseline_card = baseline_run.to_scorecard()
            case_results = baseline_run.case_results
        else:
            baseline_card = baseline_scorecard
            # Still run optimization cases to collect failure traces for FailureAnalyzer
            baseline_run = await active_bench.run_benchmark(
                graph=graph,
                split="optimization",
                persist=False,
            )
            case_results = baseline_run.case_results

        # Step 2: Diagnose failed optimization cases
        diagnoses: List[RootCauseDiagnosis] = []
        for case_res in case_results:
            if not case_res.success:
                diag = self.failure_analyzer.analyze(
                    execution_record=case_res,
                    task_specification=task_specification,
                    architecture=graph,
                    benchmark_context={
                        "benchmark_name": baseline_card.benchmark_name,
                        "case_code": case_res.case_code,
                        "ground_truth": case_res.expected_outcome,
                    },
                    scorecard_metrics={
                        "accuracy": baseline_card.accuracy,
                        "reliability": baseline_card.reliability,
                    },
                )
                diagnoses.append(diag)

        # Step 3: Cluster diagnoses
        clusters = self.failure_analyzer.cluster_failures(diagnoses) if diagnoses else []

        # Step 4: Generate candidate mutations (STRICTLY using optimization diagnoses)
        candidates_meta = self.generate_candidates(
            graph=graph,
            diagnoses=diagnoses,
            task_specification=task_specification,
            available_tools=available_tools,
            parent_version_id=parent_id,
            max_candidates=max_candidates,
            clusters=clusters,
        )

        evaluated_candidates: List[AgentVersionCandidate] = []
        best_candidate: Optional[AgentVersionCandidate] = None
        best_cand_card: Optional[Scorecard] = None
        best_cand_comparison: Optional[ScorecardComparison] = None
        highest_accuracy = baseline_card.accuracy

        # Step 5: Apply mutations and evaluate on optimization split
        for idx, cand_meta in enumerate(candidates_meta, start=1):
            version_cand = self.apply_mutation(
                graph=graph,
                mutation=cand_meta,
                parent_version_id=parent_id,
                version_number=idx,
                task_spec=task_specification,
                available_tools=available_tools,
            )
            evaluated_candidates.append(version_cand)

            if not version_cand.is_valid:
                logger.info(f"Candidate {version_cand.candidate_id} failed static validation: {version_cand.rejection_reason}")
                continue

            # Run on optimization split
            cand_run = await active_bench.run_benchmark(
                graph=version_cand.graph,
                split="optimization",
                experiment_id=exp_id,
                agent_version_id=version_cand.candidate_id,
                persist=False,
            )
            cand_card = cand_run.to_scorecard()
            version_cand.metadata["optimization_scorecard"] = cand_card.model_dump(mode="json")

            # Compare with baseline
            comparison = compare_scorecards(baseline_card, cand_card, active_policy)
            version_cand.metadata["optimization_comparison"] = comparison.model_dump(mode="json")

            # Check if this candidate is an improvement
            is_better = (
                comparison.relationship in ["strictly_better", "tradeoff"]
                and cand_card.accuracy >= highest_accuracy
                and cand_card.reliability >= baseline_card.reliability
            )

            if best_candidate is None:
                best_candidate = version_cand
                best_cand_card = cand_card
                best_cand_comparison = comparison
                highest_accuracy = cand_card.accuracy
            elif cand_card.accuracy > highest_accuracy:
                highest_accuracy = cand_card.accuracy
                best_candidate = version_cand
                best_cand_card = cand_card
                best_cand_comparison = comparison
            elif is_better:
                best_candidate = version_cand
                best_cand_card = cand_card
                best_cand_comparison = comparison

        # Step 6: Held-Out Evaluation (if eligible and requested)
        promotion_assessment: Optional[PromotionAssessment] = None
        held_out_card: Optional[Scorecard] = None

        if best_candidate and best_candidate.is_valid and run_held_out:
            # Run baseline on held_out split
            base_held_run = await active_bench.run_benchmark(
                graph=graph,
                split="held_out",
                persist=False,
            )
            base_held_card = base_held_run.to_scorecard()

            # Run candidate on held_out split
            cand_held_run = await active_bench.run_benchmark(
                graph=best_candidate.graph,
                split="held_out",
                experiment_id=exp_id,
                agent_version_id=best_candidate.candidate_id,
                persist=False,
            )
            held_out_card = cand_held_run.to_scorecard()
            best_candidate.metadata["held_out_scorecard"] = held_out_card.model_dump(mode="json")

            # Perform Promotion Assessment on held-out split
            promotion_assessment = assess_promotion(
                baseline=base_held_card,
                candidate=held_out_card,
                policy=active_policy,
            )
            best_candidate.metadata["promotion_assessment"] = promotion_assessment.model_dump(mode="json")

        # Step 7: Create Improvement Record
        improvement_rec: Optional[ImprovementRecord] = None
        if best_candidate and best_cand_card:
            accepted = (promotion_assessment.decision == "promote") if promotion_assessment else False
            rejection_reason = (
                "; ".join(promotion_assessment.reasons)
                if promotion_assessment and promotion_assessment.decision != "promote"
                else None
            )

            improvement_rec = ImprovementRecord(
                id=uuid4(),
                experiment_id=exp_id,
                parent_version_id=parent_id,
                candidate_version_id=best_candidate.candidate_id,
                mutation_type=best_candidate.mutation.mutation_type.value,
                mutation_description=best_candidate.mutation.rationale,
                rationale=best_candidate.mutation.rationale,
                metrics_before=baseline_card.model_dump(mode="json"),
                metrics_after=best_cand_card.model_dump(mode="json"),
                accepted=accepted,
                rejection_reason=rejection_reason,
            )

            # Persist if repositories are provided
            if self.agent_version_repo:
                cand_status = "promoted" if accepted else "rejected"
                await self.agent_version_repo.create(
                    best_candidate.to_agent_version_record(experiment_id=exp_id, status=cand_status)
                )

            if self.improvement_repo:
                await self.improvement_repo.create(improvement_rec)

        summary_text = (
            f"Optimization generated {len(candidates_meta)} candidates. "
            f"Best candidate '{best_candidate.candidate_id if best_candidate else 'None'}' "
            f"mutation: {best_candidate.mutation.mutation_type.value if best_candidate else 'None'}. "
            f"Promotion decision: {promotion_assessment.decision if promotion_assessment else 'not_evaluated'}."
        )

        return OptimizationResult(
            experiment_id=exp_id,
            parent_version_id=parent_id,
            candidates_generated=len(candidates_meta),
            candidates_evaluated=len([c for c in evaluated_candidates if c.is_valid]),
            candidates=evaluated_candidates,
            best_candidate=best_candidate,
            promotion_assessment=promotion_assessment,
            improvement_record=improvement_rec,
            optimization_scorecard=best_cand_card,
            held_out_scorecard=held_out_card,
            summary=summary_text,
        )
