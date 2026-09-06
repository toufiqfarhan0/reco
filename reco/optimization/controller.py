"""Multi-generation autonomous optimization controller."""

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
from reco.mutation.engine import MutationEngine
from reco.mutation.models import AgentVersionCandidate, MutationCandidate
from reco.observability.tracer import get_tracer
from reco.optimization.events import (
    OptimizationEvent,
    OptimizationEventDispatcher,
    OptimizationEventListener,
    OptimizationEventType,
)
from reco.optimization.history import HistoryTracker
from reco.optimization.models import (
    CandidateEvaluationRecord,
    OptimizationConfig,
    OptimizationGeneration,
    OptimizationResult,
)
from reco.tools.registry import ToolRegistry, default_tool_registry

logger = get_logger("optimization.controller")


class OptimizationController:
    """Orchestrates multi-generation autonomous optimization loops.
    
    Coordinates:
    V0 -> evaluate -> diagnose -> mutate -> V1 -> evaluate -> diagnose -> mutate -> V2 ... -> Held-Out Validation -> Promotion Gate
    """

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        model_gateway: Optional[ModelGateway] = None,
        mutation_engine: Optional[MutationEngine] = None,
        failure_analyzer: Optional[FailureAnalyzer] = None,
        agent_version_repo: Optional[AgentVersionRepository] = None,
        improvement_repo: Optional[ImprovementRepository] = None,
        failure_diagnosis_repo: Optional[FailureDiagnosisRepository] = None,
        benchmark_run_repo: Optional[BenchmarkRunRepository] = None,
        event_dispatcher: Optional[OptimizationEventDispatcher] = None,
        event_listeners: Optional[List[OptimizationEventListener]] = None,
    ):
        self.tool_registry = tool_registry or default_tool_registry
        self.model_gateway = model_gateway
        self.agent_version_repo = agent_version_repo
        self.improvement_repo = improvement_repo
        self.failure_diagnosis_repo = failure_diagnosis_repo
        self.benchmark_run_repo = benchmark_run_repo

        self.mutation_engine = mutation_engine or MutationEngine(
            tool_registry=self.tool_registry,
            model_gateway=self.model_gateway,
            agent_version_repo=self.agent_version_repo,
            improvement_repo=self.improvement_repo,
            failure_diagnosis_repo=self.failure_diagnosis_repo,
            benchmark_run_repo=self.benchmark_run_repo,
        )

        self.failure_analyzer = failure_analyzer or FailureAnalyzer(
            model_gateway=self.model_gateway,
            tool_registry=self.tool_registry,
        )

        self.event_dispatcher = event_dispatcher or OptimizationEventDispatcher(event_listeners)
        self.event_dispatcher.register(get_tracer().as_optimization_listener())
        self.history_tracker = HistoryTracker()

    def add_event_listener(self, listener: OptimizationEventListener) -> None:
        """Register an event listener."""
        self.event_dispatcher.register(listener)

    async def optimize(
        self,
        graph: GraphDefinition,
        benchmark: Optional[Any] = None,
        task_specification: Optional[TaskSpecification] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        experiment_id: Optional[UUID] = None,
        initial_version_id: Optional[UUID] = None,
        policy: Optional[ComparisonPolicy] = None,
        config: Optional[OptimizationConfig] = None,
        baseline_scorecard: Optional[Scorecard] = None,
    ) -> OptimizationResult:
        """Execute the multi-generation autonomous optimization controller."""
        exp_id = experiment_id or uuid4()
        init_id = initial_version_id or uuid4()
        cfg = config or OptimizationConfig()
        tracer = get_tracer()

        with tracer.start_span(
            "optimization_run",
            attributes={
                "experiment_id": str(exp_id),
                "initial_version_id": str(init_id),
                "max_generations": cfg.max_generations,
                "strategy": getattr(cfg, "strategy", "failure_driven"),
                "dataset": getattr(cfg, "benchmark_dataset", "reconciliation"),
            },
        ):
            res = await self._run_optimization_loop(
                graph=graph,
                benchmark=benchmark,
                task_specification=task_specification,
                available_tools=available_tools,
                exp_id=exp_id,
                init_id=init_id,
                policy=policy,
                cfg=cfg,
                baseline_scorecard=baseline_scorecard,
            )
            try:
                import os
                os.makedirs("scratch", exist_ok=True)
                tracer.export_trace_demo(os.path.join("scratch", "neatlogs_trace_demo.json"))
                if tracer.enabled:
                    tracer.send_structured_trace(tracer.build_trace_hierarchy_from_spans())
            except Exception as e:
                logger.warning("Neatlogs trace export/send contained: %s", e)
            return res

    async def _run_optimization_loop(
        self,
        graph: GraphDefinition,
        benchmark: Optional[Any],
        task_specification: Optional[TaskSpecification],
        available_tools: Optional[List[Dict[str, Any]]],
        exp_id: UUID,
        init_id: UUID,
        policy: Optional[ComparisonPolicy],
        cfg: OptimizationConfig,
        baseline_scorecard: Optional[Scorecard],
    ) -> OptimizationResult:
        active_policy = policy or ComparisonPolicy()
        active_bench = benchmark or ReconciliationBenchmark(
            benchmark_run_repo=self.benchmark_run_repo,
        )

        # Reset history tracker for clean experiment state
        self.history_tracker = HistoryTracker()

        # Emit optimization started
        self.event_dispatcher.emit(OptimizationEvent(
            event_type=OptimizationEventType.OPTIMIZATION_STARTED,
            experiment_id=exp_id,
            parent_version_id=init_id,
            payload={"config": cfg.model_dump(mode="json"), "initial_version_id": str(init_id)},
        ))

        # Track resource expenditures
        total_model_calls = 0
        total_tool_calls = 0
        total_tokens_in = 0
        total_tokens_out = 0
        total_cost_usd = 0.0

        tracer = get_tracer()

        # Step 0: Benchmark initial architecture (V0) on optimization split
        current_graph = graph
        current_version_id = init_id
        
        # Register initial graph
        self.history_tracker.record_graph(current_graph, current_version_id)

        with tracer.start_span(
            "generation_0",
            attributes={
                "experiment_id": str(exp_id),
                "generation_number": 0,
                "parent_version_id": str(init_id),
            },
        ):
            if baseline_scorecard is None:
                v0_run = await active_bench.run_benchmark(
                    graph=current_graph,
                    split="optimization",
                    experiment_id=exp_id,
                    agent_version_id=current_version_id,
                    persist=False,
                )
                current_scorecard = v0_run.to_scorecard()
                current_case_results = v0_run.case_results
                total_tokens_in += sum(c.tokens_in for c in v0_run.case_results)
                total_tokens_out += sum(c.tokens_out for c in v0_run.case_results)
                total_cost_usd += v0_run.total_cost_usd
                total_model_calls += sum(len(c.tool_events) + 1 for c in v0_run.case_results)
                total_tool_calls += sum(len(c.tool_events) for c in v0_run.case_results)
            else:
                current_scorecard = baseline_scorecard
                v0_run = await active_bench.run_benchmark(
                    graph=current_graph,
                    split="optimization",
                    persist=False,
                )
                current_case_results = v0_run.case_results
                total_tokens_in += sum(c.tokens_in for c in v0_run.case_results)
                total_tokens_out += sum(c.tokens_out for c in v0_run.case_results)
                total_cost_usd += v0_run.total_cost_usd
                total_model_calls += sum(len(c.tool_events) + 1 for c in v0_run.case_results)
                total_tool_calls += sum(len(c.tool_events) for c in v0_run.case_results)

        initial_v0_scorecard = current_scorecard

        # Record initial baseline version record
        if self.agent_version_repo is not None:
            v0_rec = AgentVersionRecord(
                id=current_version_id,
                experiment_id=exp_id,
                version_number=0,
                architecture=current_graph.model_dump(mode="json"),
                prompts={n_id: n.system_prompt for n_id, n in current_graph.nodes.items()},
                tools=sorted(list({t for n in current_graph.nodes.values() for t in n.tools})),
                memory_config={},
                model_config_data={},
                parent_version_id=None,
                mutation_summary="Initial V0 baseline architecture",
                status="promoted",  # type: ignore
            )
            await self.agent_version_repo.create(v0_rec)

        generations: List[OptimizationGeneration] = []
        all_evaluated_candidates: List[AgentVersionCandidate] = []
        all_candidate_evaluations: List[CandidateEvaluationRecord] = []
        all_improvements: List[ImprovementRecord] = []
        best_candidate_overall: Optional[AgentVersionCandidate] = None
        termination_reason = "completed"

        # Record generation 0 in history timeline
        self.history_tracker.add_timeline_entry({
            "generation": 0,
            "version_id": str(current_version_id),
            "scorecard": current_scorecard.model_dump(mode="json"),
            "status": "baseline",
        })

        # Main Multi-Generation Evolution Loop
        for gen_num in range(1, cfg.max_generations + 1):
            logger.info(f"Starting optimization generation {gen_num} (parent: {current_version_id})")

            # Budget / Limit Checks
            if cfg.max_total_model_calls and total_model_calls >= cfg.max_total_model_calls:
                termination_reason = "model_call_budget_exceeded"
                logger.warning(f"Optimization halted: model call ceiling ({cfg.max_total_model_calls}) reached.")
                break

            if cfg.max_total_cost_usd and total_cost_usd >= cfg.max_total_cost_usd:
                termination_reason = "cost_budget_exceeded"
                logger.warning(f"Optimization halted: cost ceiling (${cfg.max_total_cost_usd}) reached.")
                break

            gen_span = tracer.start_active_span(
                f"generation_{gen_num}",
                attributes={
                    "experiment_id": str(exp_id),
                    "generation_number": gen_num,
                    "parent_version_id": str(current_version_id),
                },
            )

            self.event_dispatcher.emit(OptimizationEvent(
                event_type=OptimizationEventType.GENERATION_STARTED,
                experiment_id=exp_id,
                generation_number=gen_num,
                parent_version_id=current_version_id,
                payload={"scorecard": current_scorecard.model_dump(mode="json")},
            ))

            # Step 1: Diagnose failures from CURRENT parent's optimization results only
            failed_cases = [c for c in current_case_results if not c.success]
            if not failed_cases:
                termination_reason = "convergence_reached"
                logger.info(f"Generation {gen_num}: 100% accuracy reached on optimization split. Converged.")
                gen_span.end()
                break

            diagnoses: List[RootCauseDiagnosis] = []
            for case_res in failed_cases:
                diag = self.failure_analyzer.analyze(
                    execution_record=case_res,
                    task_specification=task_specification,
                    architecture=current_graph,
                    benchmark_context={
                        "benchmark_name": current_scorecard.benchmark_name,
                        "case_code": case_res.case_code,
                        "ground_truth": case_res.expected_outcome,
                    },
                    scorecard_metrics={
                        "accuracy": current_scorecard.accuracy,
                        "reliability": current_scorecard.reliability,
                    },
                )
                diagnoses.append(diag)
                if self.failure_diagnosis_repo is not None:
                    await self.failure_diagnosis_repo.create(diag.to_db_record(exp_id, current_version_id))

            clusters = self.failure_analyzer.cluster_failures(diagnoses) if diagnoses else []

            # Step 2: Generate candidate mutations targeting current parent's failures
            candidates_meta = self.mutation_engine.generate_candidates(
                graph=current_graph,
                diagnoses=diagnoses,
                task_specification=task_specification,
                available_tools=available_tools,
                parent_version_id=current_version_id,
                max_candidates=cfg.max_candidates_per_generation,
                clusters=clusters,
            )

            if not candidates_meta:
                termination_reason = "no_viable_candidates"
                logger.info(f"Generation {gen_num}: no candidate mutations synthesized.")
                generations.append(OptimizationGeneration(
                    generation_number=gen_num,
                    parent_version_id=current_version_id,
                    candidate_version_ids=[],
                    selected_version_id=None,
                    optimization_scorecard=current_scorecard,
                    diagnoses=diagnoses,
                    mutations=[],
                    decision="no_candidates",
                    metadata={"reason": "Candidate generator returned no candidates"},
                ))
                gen_span.end()
                break

            for cand in candidates_meta:
                self.event_dispatcher.emit(OptimizationEvent(
                    event_type=OptimizationEventType.CANDIDATE_GENERATED,
                    experiment_id=exp_id,
                    generation_number=gen_num,
                    parent_version_id=current_version_id,
                    candidate_id=cand.candidate_id,
                    payload={"mutation": cand.model_dump(mode="json")},
                ))

            # Step 3: Apply mutations, validate, deduplicate, and benchmark candidates
            gen_evaluated_candidates: List[AgentVersionCandidate] = []
            gen_candidate_records: List[CandidateEvaluationRecord] = []
            cand_scorecards: Dict[UUID, Scorecard] = {}
            cand_comparisons: Dict[UUID, ScorecardComparison] = {}
            cand_runs: Dict[UUID, Any] = {}
            seen_fingerprints_this_gen: Set[str] = set()
            gen_benchmark_cases_evaluated = 0
            max_cases_allowed = getattr(cfg, "max_candidate_benchmark_cases", 36)

            for idx, cand_meta in enumerate(candidates_meta, start=1):
                cand_label = f"Candidate {chr(64 + idx)}" if idx <= 26 else f"Candidate {idx}"

                # Budget enforcement (Part 14)
                if gen_benchmark_cases_evaluated + 12 > max_cases_allowed:
                    logger.warning(f"Candidate {cand_label} exceeded benchmark budget ({max_cases_allowed} cases). Skipping.")
                    cand_obj = AgentVersionCandidate(
                        candidate_id=cand_meta.candidate_id,
                        parent_version_id=current_version_id,
                        version_number=gen_num,
                        graph=current_graph,
                        mutation=cand_meta,
                        is_valid=False,
                        rejection_reason="candidate_case_budget_exceeded",
                    )
                    gen_evaluated_candidates.append(cand_obj)
                    all_evaluated_candidates.append(cand_obj)
                    rec = CandidateEvaluationRecord(
                        candidate_id=cand_meta.candidate_id,
                        name=cand_label,
                        mutation_type=cand_meta.mutation_type.value,
                        target=cand_meta.target,
                        proposed_change=cand_meta.proposed_change,
                        rationale=cand_meta.rationale,
                        diagnostics_source_ids=cand_meta.source_diagnosis_ids,
                        is_valid=False,
                        status="rejected",
                        rejection_reason="candidate_case_budget_exceeded",
                    )
                    gen_candidate_records.append(rec)
                    all_candidate_evaluations.append(rec)
                    self.event_dispatcher.emit(OptimizationEvent(
                        event_type=OptimizationEventType.CANDIDATE_REJECTED,
                        experiment_id=exp_id,
                        generation_number=gen_num,
                        parent_version_id=current_version_id,
                        candidate_id=cand_meta.candidate_id,
                        payload={"reason": "candidate_case_budget_exceeded"},
                    ))
                    continue

                # Cycle / repeated mutation check
                if cfg.detect_cycles and self.history_tracker.is_repeated_mutation(current_version_id, cand_meta):
                    logger.info(f"Skipping candidate mutation {cand_meta.candidate_id}: duplicate mutation on parent.")
                    cand_obj = AgentVersionCandidate(
                        candidate_id=cand_meta.candidate_id,
                        parent_version_id=current_version_id,
                        version_number=gen_num,
                        graph=current_graph,
                        mutation=cand_meta,
                        is_valid=False,
                        rejection_reason="repeated_mutation_detected",
                    )
                    gen_evaluated_candidates.append(cand_obj)
                    all_evaluated_candidates.append(cand_obj)
                    rec = CandidateEvaluationRecord(
                        candidate_id=cand_meta.candidate_id,
                        name=cand_label,
                        mutation_type=cand_meta.mutation_type.value,
                        target=cand_meta.target,
                        proposed_change=cand_meta.proposed_change,
                        rationale=cand_meta.rationale,
                        diagnostics_source_ids=cand_meta.source_diagnosis_ids,
                        is_valid=False,
                        status="invalid",
                        rejection_reason="repeated_mutation_detected",
                    )
                    gen_candidate_records.append(rec)
                    all_candidate_evaluations.append(rec)
                    self.event_dispatcher.emit(OptimizationEvent(
                        event_type=OptimizationEventType.CANDIDATE_REJECTED,
                        experiment_id=exp_id,
                        generation_number=gen_num,
                        parent_version_id=current_version_id,
                        candidate_id=cand_meta.candidate_id,
                        payload={"reason": "repeated_mutation_detected"},
                    ))
                    continue

                version_cand = self.mutation_engine.apply_mutation(
                    graph=current_graph,
                    mutation=cand_meta,
                    parent_version_id=current_version_id,
                    version_number=gen_num,
                    task_spec=task_specification,
                    available_tools=available_tools,
                )

                # Architecture fingerprinting and deduplication (Part 9)
                from reco.optimization.history import compute_graph_fingerprint
                cand_fp = compute_graph_fingerprint(version_cand.graph)

                if cand_fp in seen_fingerprints_this_gen:
                    version_cand.is_valid = False
                    version_cand.rejection_reason = "duplicate_candidate_architecture"
                elif cfg.detect_cycles and self.history_tracker.is_repeated_architecture(version_cand.graph):
                    version_cand.is_valid = False
                    version_cand.rejection_reason = "repeated_architecture_detected"
                else:
                    seen_fingerprints_this_gen.add(cand_fp)

                gen_evaluated_candidates.append(version_cand)
                all_evaluated_candidates.append(version_cand)

                cand_rec = CandidateEvaluationRecord(
                    candidate_id=version_cand.candidate_id,
                    name=cand_label,
                    mutation_type=cand_meta.mutation_type.value,
                    target=cand_meta.target,
                    proposed_change=cand_meta.proposed_change,
                    rationale=cand_meta.rationale,
                    diagnostics_source_ids=cand_meta.source_diagnosis_ids,
                    is_valid=version_cand.is_valid,
                    status="pending" if version_cand.is_valid else "invalid",
                    rejection_reason=version_cand.rejection_reason if not version_cand.is_valid else None,
                    fingerprint=cand_fp,
                )
                gen_candidate_records.append(cand_rec)
                all_candidate_evaluations.append(cand_rec)

                # Part 4: Invalid candidates do NOT consume benchmark budget
                if not version_cand.is_valid:
                    self.event_dispatcher.emit(OptimizationEvent(
                        event_type=OptimizationEventType.CANDIDATE_REJECTED,
                        experiment_id=exp_id,
                        generation_number=gen_num,
                        parent_version_id=current_version_id,
                        candidate_id=version_cand.candidate_id,
                        payload={"reason": version_cand.rejection_reason},
                    ))
                    continue

                self.event_dispatcher.emit(OptimizationEvent(
                    event_type=OptimizationEventType.CANDIDATE_VALIDATED,
                    experiment_id=exp_id,
                    generation_number=gen_num,
                    parent_version_id=current_version_id,
                    candidate_id=version_cand.candidate_id,
                ))

                # Benchmark candidate on OPTIMIZATION split only (12 cases)
                with tracer.start_span(
                    f"candidate_benchmark.{cand_meta.candidate_id}",
                    attributes={
                        "candidate_id": str(cand_meta.candidate_id),
                        "candidate_name": cand_label,
                        "split": "optimization",
                        "parent_version_id": str(current_version_id),
                    },
                ) as cand_span:
                    cand_run = await active_bench.run_benchmark(
                        graph=version_cand.graph,
                        split="optimization",
                        experiment_id=exp_id,
                        agent_version_id=version_cand.candidate_id,
                        persist=False,
                    )
                    gen_benchmark_cases_evaluated += len(cand_run.case_results)
                    cand_runs[version_cand.candidate_id] = cand_run
                    cand_card = cand_run.to_scorecard()
                    cand_scorecards[version_cand.candidate_id] = cand_card

                    # Accounting
                    c_tokens_in = sum(c.tokens_in for c in cand_run.case_results)
                    c_tokens_out = sum(c.tokens_out for c in cand_run.case_results)
                    c_model_calls = sum(len(c.tool_events) + 1 for c in cand_run.case_results)
                    c_tool_calls = sum(len(c.tool_events) for c in cand_run.case_results)

                    total_tokens_in += c_tokens_in
                    total_tokens_out += c_tokens_out
                    total_cost_usd += cand_run.total_cost_usd
                    total_model_calls += c_model_calls
                    total_tool_calls += c_tool_calls

                    # Compare with current parent
                    comparison = compare_scorecards(current_scorecard, cand_card, active_policy)
                    cand_comparisons[version_cand.candidate_id] = comparison
                    version_cand.metadata["optimization_scorecard"] = cand_card.model_dump(mode="json")
                    version_cand.metadata["comparison"] = comparison.model_dump(mode="json")

                    cand_rec.scorecard = cand_card
                    cand_rec.comparison = comparison
                    cand_rec.model_calls = c_model_calls
                    cand_rec.tool_calls = c_tool_calls
                    cand_rec.tokens_in = c_tokens_in
                    cand_rec.tokens_out = c_tokens_out
                    cand_rec.cost_usd = cand_card.total_cost_usd
                    cand_rec.latency_ms = cand_card.total_latency_ms

                    cand_span.set_attribute("accuracy", cand_card.accuracy)
                    cand_span.set_attribute("cost_usd", cand_card.total_cost_usd)
                    cand_span.set_attribute("relationship", comparison.relationship)

                self.event_dispatcher.emit(OptimizationEvent(
                    event_type=OptimizationEventType.CANDIDATE_BENCHMARKED,
                    experiment_id=exp_id,
                    generation_number=gen_num,
                    parent_version_id=current_version_id,
                    candidate_id=version_cand.candidate_id,
                    payload={"scorecard": cand_card.model_dump(mode="json"), "relationship": comparison.relationship},
                ))

            # Step 4: Candidate Selection Policy (Part 7 & Part 8)
            selected_cand: Optional[AgentVersionCandidate] = None
            selected_card: Optional[Scorecard] = None
            selected_comp: Optional[ScorecardComparison] = None
            selected_rec: Optional[CandidateEvaluationRecord] = None

            for cand in gen_evaluated_candidates:
                if not cand.is_valid or cand.candidate_id not in cand_scorecards:
                    continue
                c_card = cand_scorecards[cand.candidate_id]
                c_comp = cand_comparisons[cand.candidate_id]
                c_rec = next((r for r in gen_candidate_records if r.candidate_id == cand.candidate_id), None)

                # Disqualify reliability regression
                if c_card.reliability < current_scorecard.reliability:
                    if c_rec:
                        c_rec.rejection_reason = "reliability_regression"
                    continue

                # Disqualify accuracy regression
                if c_card.accuracy < current_scorecard.accuracy:
                    if c_rec:
                        c_rec.rejection_reason = "accuracy_regression"
                    continue

                # Disqualify strictly worse
                if c_comp.relationship == "strictly_worse":
                    if c_rec:
                        c_rec.rejection_reason = "strictly_worse_than_parent"
                    continue

                # Improvement condition
                is_improvement = (
                    c_comp.relationship in ["strictly_better", "tradeoff"]
                    and c_card.accuracy >= current_scorecard.accuracy
                    and c_card.reliability >= current_scorecard.reliability
                )

                if is_improvement:
                    if selected_cand is None:
                        selected_cand = cand
                        selected_card = c_card
                        selected_comp = c_comp
                        selected_rec = c_rec
                    elif c_card.accuracy > selected_card.accuracy:
                        selected_cand = cand
                        selected_card = c_card
                        selected_comp = c_comp
                        selected_rec = c_rec
                    elif c_card.accuracy == selected_card.accuracy:
                        # Tie-breaking: lower cost
                        if c_card.total_cost_usd < selected_card.total_cost_usd:
                            selected_cand = cand
                            selected_card = c_card
                            selected_comp = c_comp
                            selected_rec = c_rec
                        elif c_card.total_cost_usd == selected_card.total_cost_usd and c_card.total_latency_ms < selected_card.total_latency_ms:
                            # Tie-breaking: lower latency
                            selected_cand = cand
                            selected_card = c_card
                            selected_comp = c_comp
                            selected_rec = c_rec

            # Mark statuses on all candidate records in this generation
            for r in gen_candidate_records:
                if selected_cand and r.candidate_id == selected_cand.candidate_id:
                    r.status = "selected"
                    r.rejection_reason = None
                elif not r.is_valid:
                    r.status = "invalid"
                else:
                    r.status = "rejected"
                    if not r.rejection_reason:
                        if selected_rec:
                            r.rejection_reason = f"inferior_to_{selected_rec.name}"
                        else:
                            r.rejection_reason = "no_improvement_over_parent"
                    self.event_dispatcher.emit(OptimizationEvent(
                        event_type=OptimizationEventType.CANDIDATE_REJECTED,
                        experiment_id=exp_id,
                        generation_number=gen_num,
                        parent_version_id=current_version_id,
                        candidate_id=r.candidate_id,
                        payload={"reason": r.rejection_reason},
                    ))

            # Step 5: Evolution Step or Stopping Decision
            if selected_cand is not None and selected_card is not None and selected_comp is not None:
                decision = "selected"
                best_candidate_overall = selected_cand

                # Create Improvement Record
                improvement_rec = ImprovementRecord(
                    id=uuid4(),
                    experiment_id=exp_id,
                    parent_version_id=current_version_id,
                    candidate_version_id=selected_cand.candidate_id,
                    mutation_type=selected_cand.mutation.mutation_type.value,
                    mutation_description=selected_cand.mutation.rationale,
                    rationale=selected_cand.mutation.rationale,
                    metrics_before=current_scorecard.model_dump(mode="json"),
                    metrics_after=selected_card.model_dump(mode="json"),
                    accepted=True,
                )
                all_improvements.append(improvement_rec)

                # Persist to repositories if configured
                if self.agent_version_repo is not None:
                    await self.agent_version_repo.create(
                        selected_cand.to_agent_version_record(experiment_id=exp_id, status="promoted")
                    )
                if self.improvement_repo is not None:
                    await self.improvement_repo.create(improvement_rec)

                # Register in history tracker
                self.history_tracker.record_graph(selected_cand.graph, selected_cand.candidate_id)
                self.history_tracker.record_mutation(current_version_id, selected_cand.mutation)
                self.history_tracker.add_timeline_entry({
                    "generation": gen_num,
                    "parent_version_id": str(current_version_id),
                    "selected_version_id": str(selected_cand.candidate_id),
                    "mutation": selected_cand.mutation.mutation_type.value,
                    "metrics_before": current_scorecard.model_dump(mode="json"),
                    "metrics_after": selected_card.model_dump(mode="json"),
                    "decision": "selected",
                })

                self.event_dispatcher.emit(OptimizationEvent(
                    event_type=OptimizationEventType.CANDIDATE_SELECTED,
                    experiment_id=exp_id,
                    generation_number=gen_num,
                    parent_version_id=current_version_id,
                    candidate_id=selected_cand.candidate_id,
                    payload={"mutation": selected_cand.mutation.mutation_type.value},
                ))

                # Update current state for NEXT generation
                previous_parent_id = current_version_id
                current_version_id = selected_cand.candidate_id
                current_graph = selected_cand.graph
                current_scorecard = selected_card
                current_case_results = cand_runs[selected_cand.candidate_id].case_results

                generations.append(OptimizationGeneration(
                    generation_number=gen_num,
                    parent_version_id=previous_parent_id,
                    candidate_version_ids=[c.candidate_id for c in gen_evaluated_candidates],
                    selected_version_id=selected_cand.candidate_id,
                    optimization_scorecard=selected_card,
                    diagnoses=diagnoses,
                    mutations=candidates_meta,
                    candidates=gen_candidate_records,
                    comparison=selected_comp,
                    decision=decision,
                    metadata={"accuracy": selected_card.accuracy, "reliability": selected_card.reliability},
                ))

                if gen_num == cfg.max_generations:
                    termination_reason = "max_generations_reached"
            else:
                decision = "no_improvement"
                generations.append(OptimizationGeneration(
                    generation_number=gen_num,
                    parent_version_id=current_version_id,
                    candidate_version_ids=[c.candidate_id for c in gen_evaluated_candidates],
                    selected_version_id=None,
                    optimization_scorecard=current_scorecard,
                    diagnoses=diagnoses,
                    mutations=candidates_meta,
                    candidates=gen_candidate_records,
                    decision=decision,
                    metadata={"reason": "All candidates regressed or failed to improve parent scorecard"},
                ))
                self.history_tracker.add_timeline_entry({
                    "generation": gen_num,
                    "parent_version_id": str(current_version_id),
                    "decision": "no_improvement",
                })

                if cfg.stop_on_no_improvement:
                    termination_reason = "no_improvement"
                    logger.info(f"Generation {gen_num}: no candidate improved parent. Terminating evolution.")
                    gen_span.end()
                    break

            self.event_dispatcher.emit(OptimizationEvent(
                event_type=OptimizationEventType.GENERATION_COMPLETED,
                experiment_id=exp_id,
                generation_number=gen_num,
                parent_version_id=current_version_id,
                payload={"decision": decision},
            ))
            gen_span.end()

        # Final Promotion Gate — Evaluate winning version on HELD-OUT split
        held_out_scorecard: Optional[Scorecard] = None
        promotion_assessment: Optional[PromotionAssessment] = None

        if cfg.run_held_out_at_termination:
            logger.info("Executing final promotion gate evaluation on held-out split...")
            with tracer.start_span(
                "promotion_gate",
                attributes={
                    "split": "held_out",
                    "parent_version_id": str(current_version_id),
                    "initial_version_id": str(init_id),
                },
            ) as promo_span:
                # Baseline held-out
                base_held_run = await active_bench.run_benchmark(
                    graph=graph,
                    split="held_out",
                    persist=False,
                )
                base_held_card = base_held_run.to_scorecard()

                # Final winner held-out
                final_held_run = await active_bench.run_benchmark(
                    graph=current_graph,
                    split="held_out",
                    experiment_id=exp_id,
                    agent_version_id=current_version_id,
                    persist=False,
                )
                held_out_scorecard = final_held_run.to_scorecard()

                # Accumulate held-out accounting
                total_tokens_in += sum(c.tokens_in for c in base_held_run.case_results) + sum(c.tokens_in for c in final_held_run.case_results)
                total_tokens_out += sum(c.tokens_out for c in base_held_run.case_results) + sum(c.tokens_out for c in final_held_run.case_results)
                total_cost_usd += base_held_run.total_cost_usd + final_held_run.total_cost_usd
                total_model_calls += sum(len(c.tool_events) + 1 for c in base_held_run.case_results) + sum(len(c.tool_events) + 1 for c in final_held_run.case_results)
                total_tool_calls += sum(len(c.tool_events) for c in base_held_run.case_results) + sum(len(c.tool_events) for c in final_held_run.case_results)

                promotion_assessment = assess_promotion(
                    baseline=base_held_card,
                    candidate=held_out_scorecard,
                    policy=active_policy,
                )

                comp = promotion_assessment.comparison
                acc_delta = getattr(comp, "accuracy_delta", 0.0) if comp else 0.0
                cost_delta = getattr(comp, "cost_delta", 0.0) if comp else 0.0
                lat_delta = getattr(comp, "latency_delta", 0) if comp else 0
                rel_delta = getattr(comp, "reliability_delta", 0.0) if comp else 0.0

                promo_span.set_attribute("decision", promotion_assessment.decision)
                promo_span.set_attribute("promoted", (promotion_assessment.decision == "promote"))
                promo_span.set_attribute("accuracy_delta", acc_delta)

                tracer.trace_promotion(
                    experiment_id=str(exp_id),
                    parent_version_id=str(init_id),
                    final_version_id=str(current_version_id),
                    decision=promotion_assessment.decision,
                    promoted=(promotion_assessment.decision == "promote"),
                    accuracy_delta=acc_delta,
                    cost_delta=cost_delta,
                    latency_delta=lat_delta,
                    reliability_delta=rel_delta,
                    improved_dimensions=promotion_assessment.improved_dimensions,
                    regressed_dimensions=promotion_assessment.regressed_dimensions,
                )

                self.event_dispatcher.emit(OptimizationEvent(
                    event_type=OptimizationEventType.PROMOTION_ASSESSED,
                    experiment_id=exp_id,
                    parent_version_id=current_version_id,
                    payload={
                        "decision": promotion_assessment.decision,
                        "scorecard": held_out_scorecard.model_dump(mode="json"),
                    },
                ))

        summary_lines = [
            f"Multi-generation optimization completed in {len(generations)} generations.",
            f"Termination reason: {termination_reason}.",
            f"Initial version: {init_id} -> Final version: {current_version_id}.",
            f"Promotion assessment on held-out split: {promotion_assessment.decision if promotion_assessment else 'not_evaluated'}.",
        ]

        result = OptimizationResult(
            experiment_id=exp_id,
            initial_version_id=init_id,
            final_version_id=current_version_id,
            generations=generations,
            termination_reason=termination_reason,
            optimization_history=self.history_tracker.timeline,
            held_out_result=held_out_scorecard,
            final_promotion_assessment=promotion_assessment,
            total_model_calls=total_model_calls,
            total_tool_calls=total_tool_calls,
            total_tokens_in=total_tokens_in,
            total_tokens_out=total_tokens_out,
            total_cost_usd=round(total_cost_usd, 6),
            candidate_evaluations=all_candidate_evaluations,
            parent_version_id=init_id,
            candidates_generated=len(all_evaluated_candidates),
            candidates_evaluated=len([c for c in all_evaluated_candidates if c.is_valid]),
            candidates=all_evaluated_candidates,
            best_candidate=best_candidate_overall,
            promotion_assessment=promotion_assessment,
            improvement_record=all_improvements[-1] if all_improvements else None,
            baseline_scorecard=initial_v0_scorecard,
            optimization_scorecard=current_scorecard,
            held_out_scorecard=held_out_scorecard,
            summary=" ".join(summary_lines),
        )

        self.event_dispatcher.emit(OptimizationEvent(
            event_type=OptimizationEventType.OPTIMIZATION_TERMINATED,
            experiment_id=exp_id,
            parent_version_id=current_version_id,
            payload={"result_summary": result.summary, "termination_reason": termination_reason},
        ))

        return result
