"""Step 22 Deterministic Test Suite: Multi-Candidate Optimization & Candidate Selection.

Verifies:
1. Max candidate limit enforcement (<= 3)
2. Candidate generation from diagnoses
3. Candidate diversity and deduplication
4. Static validation budget protection
5. Candidate benchmarking on optimization split
6. Scorecard generation for candidates
7. Candidate scorecard comparison against parent
8. Best-candidate Pareto selection
9. Regression rejection (reliability & accuracy)
10. Tradeoff handling
11. Parent immutability
12. Lineage tracking
13. Generation history preservation
14. Held-out isolation
15. Candidate statuses (selected, rejected, invalid)
16. Benchmark case budget enforcement
17. Neatlogs candidate lifecycle events
18. API serialization for frontend display
"""

import asyncio
from typing import Any, Dict, List
from uuid import UUID, uuid4
import pytest

from reco.benchmarks.reconciliation import create_reconciliation_baseline_graph
from reco.benchmarks.reconciliation.benchmark import ReconciliationBenchmark
from reco.diagnostics.models import RecommendedMutation, RootCauseDiagnosis
from reco.diagnostics.taxonomy import FailureCategory, MutationType, Severity
from reco.engine.models import GraphDefinition
from reco.evaluators.comparison import ComparisonPolicy, ScorecardComparison, compare_scorecards
from reco.evaluators.scorecard import Scorecard
from reco.mutation.generator import CandidateGenerator
from reco.mutation.engine import MutationEngine
from reco.mutation.models import (
    AgentVersionCandidate,
    CandidateEvaluationRecord,
    MutationCandidate,
    OptimizationConfig,
    OptimizationGeneration,
    OptimizationResult,
)
from reco.observability.tracer import get_tracer
from reco.optimization.controller import OptimizationController
from reco.optimization.events import (
    OptimizationEvent,
    OptimizationEventListener,
    OptimizationEventType,
)
from reco.optimization.history import compute_graph_fingerprint


def _make_sample_diagnosis(target: str = "fuzzy_match", category: FailureCategory = FailureCategory.HALLUCINATED_MATCH) -> RootCauseDiagnosis:
    return RootCauseDiagnosis(
        diagnosis_id=uuid4(),
        case_id="REC-OPT-08",
        failure_category=category,
        failed_node_id=target,
        symptom="Counterparty mismatch in transaction pairing",
        summary="False positive counterparty match",
        root_cause="Matcher lacks strict counterparty identity constraints",
        evidence=[{"source": "log", "observed": "Apex Logistics matched Apex Freight"}],
        confidence=0.88,
        severity=Severity.HIGH,
        recommended_mutations=[
            RecommendedMutation(
                mutation_type=MutationType.PROMPT_CHANGE,
                target=target,
                rationale="Require strict vendor identity matching with require_vendor_match=True",
                expected_effect="Eliminates false-positive reconciliation matches",
                confidence=0.90,
            ),
            RecommendedMutation(
                mutation_type=MutationType.ADD_VERIFIER,
                target=target,
                rationale="Add secondary auditor to verify counterparty alignment",
                expected_effect="Secondary validation catches discrepant pairs",
                confidence=0.80,
            ),
            RecommendedMutation(
                mutation_type=MutationType.TOOL_ADD,
                target=target,
                rationale="Add calculate_reconciliation_difference tool for arithmetic validation",
                expected_effect="Mathematical check verifies amount delta is zero",
                confidence=0.75,
                metadata={"tool_name": "calculate_reconciliation_difference"},
            ),
        ],
    )


def _make_scorecard(
    accuracy: float = 0.75,
    reliability: float = 1.0,
    cost: float = 0.071354,
    latency: float = 50000.0,
    version: str = "V0",
    passed: int = 8,
    failed: int = 4,
) -> Scorecard:
    return Scorecard(
        benchmark_name="reconciliation",
        benchmark_version="reconciliation-v1",
        agent_version_id=uuid4(),
        experiment_id=uuid4(),
        split="optimization",
        version=version,
        accuracy=accuracy,
        reliability=reliability,
        total_cost_usd=cost,
        avg_cost_usd=round(cost / 12, 6),
        cost_type="simulated_mock",
        total_latency_ms=int(latency),
        avg_latency_ms=int(round(latency / 12)),
        passed=True,
        total_cases=12,
        passed_cases=passed,
        failed_cases=failed,
    )


# 1. Max candidate limit
def test_max_candidate_limit():
    generator = CandidateGenerator()
    graph = create_reconciliation_baseline_graph()
    diag = _make_sample_diagnosis()

    # Requesting 10 candidates must be clamped to DEFAULT_MAX_CANDIDATES = 3
    candidates = generator.generate(
        agent_graph=graph,
        diagnoses=[diag],
        max_candidates=10,
    )
    assert len(candidates) <= 3
    assert len(candidates) > 0


# 2. Candidate generation from diagnoses
def test_candidate_generation():
    generator = CandidateGenerator()
    graph = create_reconciliation_baseline_graph()
    diag = _make_sample_diagnosis()

    candidates = generator.generate(
        agent_graph=graph,
        diagnoses=[diag],
        max_candidates=3,
    )
    assert len(candidates) >= 2
    for cand in candidates:
        assert isinstance(cand, MutationCandidate)
        assert cand.target in graph.nodes or cand.target == "graph"
        assert len(cand.rationale) > 0
        assert cand.risk_level in ("low", "medium", "high")


# 3. Candidate diversity & deduplication
def test_candidate_diversity_and_deduplication():
    generator = CandidateGenerator()
    graph = create_reconciliation_baseline_graph()
    diag = _make_sample_diagnosis()

    candidates = generator.generate(
        agent_graph=graph,
        diagnoses=[diag, diag],  # Duplicate diagnoses
        max_candidates=3,
    )
    # Must not contain duplicate mutation signatures
    signatures = [f"{c.mutation_type.value}:{c.target}:{str(c.proposed_change)}" for c in candidates]
    assert len(signatures) == len(set(signatures))

    # Diversity: distinct mutation types should be explored
    types = {c.mutation_type for c in candidates}
    assert len(types) >= 2  # e.g. PROMPT_CHANGE and ADD_VERIFIER or TOOL_ADD


# 4. Static validation budget protection
def test_static_validation_budget_protection():
    controller = OptimizationController()
    graph = create_reconciliation_baseline_graph()

    # Candidate with an invalid/fabricated tool
    invalid_mutation = MutationCandidate(
        candidate_id=uuid4(),
        mutation_type=MutationType.TOOL_ADD,
        target="fuzzy_match",
        proposed_change={"tool_name": "non_existent_fake_tool_999"},
        rationale="Add fabricated tool that does not exist in registry",
        source_diagnosis_ids=[uuid4()],
        expected_effect="Test failure",
        confidence=0.5,
    )

    applied_cand = controller.mutation_engine.apply_mutation(graph, invalid_mutation)
    assert applied_cand.is_valid is False
    assert "Tool is not registered in ToolRegistry" in applied_cand.rejection_reason or "Fabricated tools are strictly rejected" in applied_cand.rejection_reason


# 5. Candidate benchmarking & 6. Scorecard generation
def test_candidate_benchmarking_and_scorecards():
    async def _run():
        controller = OptimizationController()
        graph = create_reconciliation_baseline_graph()
        diag = _make_sample_diagnosis()

        # Generate 1 valid prompt mutation candidate
        cand_mut = MutationCandidate(
            candidate_id=uuid4(),
            mutation_type=MutationType.PROMPT_CHANGE,
            target="fuzzy_match",
            proposed_change={"append": "Strictly verify transaction counterparty name before matching."},
            rationale="Refine matcher prompt",
            source_diagnosis_ids=[diag.diagnosis_id],
            expected_effect="Improves accuracy",
            confidence=0.85,
        )

        version_cand = controller.mutation_engine.apply_mutation(graph, cand_mut)
        assert version_cand.is_valid is True

        bench = ReconciliationBenchmark()
        run = await bench.run_benchmark(graph=version_cand.graph, split="optimization", persist=False)
        scorecard = run.to_scorecard()

        assert scorecard.accuracy >= 0.0
        assert scorecard.reliability == 1.0
        assert scorecard.total_cases == 12
        assert scorecard.total_cost_usd >= 0.0
        assert scorecard.total_latency_ms >= 0

    asyncio.run(_run())


# 7. Candidate scorecard comparison against parent
def test_candidate_comparison():
    v0_card = _make_scorecard(accuracy=0.75, cost=0.071354, latency=50000.0, version="V0", passed=8)
    cand_card = _make_scorecard(accuracy=0.80, cost=0.063950, latency=40000.0, version="V1_A", passed=9)

    comp = compare_scorecards(v0_card, cand_card, ComparisonPolicy())
    assert comp.accuracy_delta == pytest.approx(0.05, abs=1e-4)
    assert comp.relationship == "strictly_better"


# 8. Best-candidate selection & 15. Candidate statuses
def test_best_candidate_selection_and_statuses():
    async def _run():
        controller = OptimizationController()
        graph = create_reconciliation_baseline_graph()

        cfg = OptimizationConfig(
            max_generations=1,
            max_candidates_per_generation=3,
            run_held_out_at_termination=False,
        )

        result = await controller.optimize(graph=graph, config=cfg)
        assert len(result.generations) == 1
        gen = result.generations[0]

        # Every candidate in generation must have a candidate record
        assert len(gen.candidates) > 0
        statuses = [c.status for c in gen.candidates]

        # Exactly one candidate is selected, or decision is no_improvement
        if gen.selected_version_id is not None:
            assert "selected" in statuses
            assert gen.decision == "selected"
        else:
            assert "selected" not in statuses

    asyncio.run(_run())


# 9. Regression rejection
def test_regression_rejection():
    v0_card = _make_scorecard(accuracy=0.80, reliability=1.0, cost=0.05, latency=40000.0, version="V0")
    
    # Regressed accuracy
    cand_regressed_acc = _make_scorecard(accuracy=0.70, reliability=1.0, cost=0.01, latency=10000.0, version="Cand_Bad_Acc")
    comp = compare_scorecards(v0_card, cand_regressed_acc, ComparisonPolicy())
    assert comp.relationship in ("strictly_worse", "tradeoff")
    assert comp.accuracy_delta < 0

    # Regressed reliability
    cand_regressed_rel = _make_scorecard(accuracy=0.85, reliability=0.80, cost=0.05, latency=40000.0, version="Cand_Bad_Rel")
    comp_rel = compare_scorecards(v0_card, cand_regressed_rel, ComparisonPolicy())
    assert comp_rel.reliability_delta < 0


# 10. Tradeoff handling
def test_tradeoff_handling():
    v0_card = _make_scorecard(accuracy=0.75, reliability=1.0, cost=0.070000, latency=50000.0, version="V0")
    # Higher accuracy (+5%), but slightly higher cost (+10%)
    cand_tradeoff = _make_scorecard(accuracy=0.80, reliability=1.0, cost=0.077000, latency=48000.0, version="Cand_Tradeoff")
    comp = compare_scorecards(v0_card, cand_tradeoff, ComparisonPolicy(cost_weight=0.2, accuracy_weight=0.8))
    assert comp.relationship in ("tradeoff", "strictly_better")
    assert comp.accuracy_delta > 0


# 11. Parent immutability
def test_parent_immutability():
    async def _run():
        controller = OptimizationController()
        graph = create_reconciliation_baseline_graph()
        orig_fp = compute_graph_fingerprint(graph)
        orig_prompts = {nid: n.system_prompt for nid, n in graph.nodes.items()}

        cand_meta = MutationCandidate(
            candidate_id=uuid4(),
            mutation_type=MutationType.PROMPT_CHANGE,
            target="fuzzy_match",
            proposed_change={"append": "TEST IMMUTABILITY CLAUSE"},
            rationale="Test immutability",
            source_diagnosis_ids=[uuid4()],
            expected_effect="None",
            confidence=0.5,
        )

        version_cand = controller.mutation_engine.apply_mutation(graph, cand_meta)
        
        # Mutated graph changed
        assert compute_graph_fingerprint(version_cand.graph) != orig_fp
        
        # Original parent graph remains completely identical
        assert compute_graph_fingerprint(graph) == orig_fp
        for nid, prompt in orig_prompts.items():
            assert graph.nodes[nid].system_prompt == prompt

    asyncio.run(_run())


# 12. Lineage tracking
def test_lineage_tracking():
    async def _run():
        controller = OptimizationController()
        graph = create_reconciliation_baseline_graph()
        p_id = uuid4()

        cand_meta = MutationCandidate(
            candidate_id=uuid4(),
            mutation_type=MutationType.PROMPT_CHANGE,
            target="fuzzy_match",
            proposed_change={"append": "Strict counterparty matching"},
            rationale="Lineage test",
            source_diagnosis_ids=[uuid4()],
            expected_effect="Test",
            confidence=0.8,
            parent_version_id=p_id,
        )

        version_cand = controller.mutation_engine.apply_mutation(
            graph=graph,
            mutation=cand_meta,
            parent_version_id=p_id,
            version_number=1,
        )

        assert version_cand.parent_version_id == p_id
        assert version_cand.version_number == 1
        assert version_cand.candidate_id == cand_meta.candidate_id
        assert version_cand.graph.metadata["parent_version_id"] == str(p_id)
        assert version_cand.graph.metadata["version_number"] == 1

    asyncio.run(_run())


# 13. Generation history preservation
def test_generation_history():
    async def _run():
        controller = OptimizationController()
        graph = create_reconciliation_baseline_graph()

        cfg = OptimizationConfig(
            max_generations=1,
            max_candidates_per_generation=3,
            run_held_out_at_termination=False,
        )

        result = await controller.optimize(graph=graph, config=cfg)
        assert len(result.generations) == 1
        gen = result.generations[0]

        # Verify structured candidates stored in generation
        assert hasattr(gen, "candidates")
        for cand_rec in gen.candidates:
            assert isinstance(cand_rec, CandidateEvaluationRecord)
            assert cand_rec.name.startswith("Candidate ")
            assert cand_rec.mutation_type in [m.value for m in MutationType]
            assert cand_rec.status in ("selected", "rejected", "invalid", "tradeoff")

    asyncio.run(_run())


# 14. Held-out isolation
def test_held_out_isolation():
    async def _run():
        controller = OptimizationController()
        graph = create_reconciliation_baseline_graph()

        # Track which splits are accessed
        called_splits = []

        class MockBench(ReconciliationBenchmark):
            async def run_benchmark(self, graph, split="optimization", **kwargs):
                called_splits.append(split)
                return await super().run_benchmark(graph, split=split, **kwargs)

        mock_bench = MockBench()
        cfg = OptimizationConfig(
            max_generations=1,
            max_candidates_per_generation=2,
            run_held_out_at_termination=True,
        )

        result = await controller.optimize(graph=graph, benchmark=mock_bench, config=cfg)

        # All candidate evaluations must be on "optimization" split
        # Held-out should appear ONLY at the end for promotion gate
        candidate_benchmark_splits = called_splits[:-2]  # Excluding final held-out runs
        for s in candidate_benchmark_splits:
            assert s == "optimization"

        # Held out only evaluated at termination
        assert called_splits[-1] == "held_out"
        assert called_splits[-2] == "held_out"

    asyncio.run(_run())


# 16. Benchmark case budget enforcement
def test_budget_enforcement():
    async def _run():
        controller = OptimizationController()
        graph = create_reconciliation_baseline_graph()

        # Cap candidate benchmark cases at 12 (allowing at most 1 candidate to run)
        cfg = OptimizationConfig(
            max_generations=1,
            max_candidates_per_generation=3,
            max_candidate_benchmark_cases=12,
            run_held_out_at_termination=False,
        )

        result = await controller.optimize(graph=graph, config=cfg)
        gen = result.generations[0]

        # At most 1 candidate should have run benchmarks
        benchmarked_count = len([c for c in gen.candidates if c.scorecard is not None])
        assert benchmarked_count <= 1

        # Later candidates should be rejected with budget exceeded reason
        budget_exceeded = [c for c in gen.candidates if c.rejection_reason == "candidate_case_budget_exceeded"]
        if len(gen.candidates) > 1:
            assert len(budget_exceeded) >= 1

    asyncio.run(_run())


# 17. Neatlogs candidate lifecycle events
def test_neatlogs_candidate_events():
    tracer = get_tracer()
    events_logged = []

    def mock_log(name, payload=None):
        events_logged.append((name, payload))

    orig_log = tracer.log_event
    tracer.log_event = mock_log
    try:
        tracer.trace_candidate_generated(
            candidate_id="cand_1",
            parent_version_id="p_1",
            mutation_type="PROMPT_CHANGE",
            target="fuzzy_match",
            generation=1,
            prompt_text="Secret prompt text that should not leak",
        )
        tracer.trace_candidate_benchmarked(
            candidate_id="cand_1",
            parent_version_id="p_1",
            generation=1,
            accuracy=0.80,
            cost_usd=0.063,
            latency_ms=491000,
            relationship="strictly_better",
        )
        tracer.trace_candidate_selected(
            candidate_id="cand_1",
            parent_version_id="p_1",
            generation=1,
            mutation_type="PROMPT_CHANGE",
            accuracy_delta=0.05,
        )
        tracer.trace_candidate_rejected(
            candidate_id="cand_2",
            parent_version_id="p_1",
            generation=1,
            reason="inferior_to_Candidate_A",
        )

        assert len(events_logged) == 4
        assert events_logged[0][0] == "candidate_generated"
        # Prompt hash stored, not raw prompt
        assert "Secret prompt" not in str(events_logged[0][1])
        assert events_logged[0][1]["prompt_hash"] != ""
        assert events_logged[1][0] == "candidate_benchmarked"
        assert events_logged[2][0] == "candidate_selected"
        assert events_logged[3][0] == "candidate_rejected"
    finally:
        tracer.log_event = orig_log


# 18. API candidate serialization
def test_api_candidate_serialization():
    from reco.api.app import format_live_optimization_result

    graph = create_reconciliation_baseline_graph()
    opt_res = OptimizationResult(
        experiment_id=uuid4(),
        initial_version_id=uuid4(),
        final_version_id=uuid4(),
        generations=[],
        candidate_evaluations=[
            CandidateEvaluationRecord(
                candidate_id=uuid4(),
                name="Candidate A",
                mutation_type="PROMPT_CHANGE",
                target="fuzzy_match",
                rationale="Prompt patch",
                scorecard=_make_scorecard(accuracy=0.80, cost=0.063950, latency=491859.0, version="V1", passed=9),
                status="selected",
            ),
            CandidateEvaluationRecord(
                candidate_id=uuid4(),
                name="Candidate B",
                mutation_type="ADD_VERIFIER",
                target="fuzzy_match",
                rationale="Add verifier",
                scorecard=_make_scorecard(accuracy=0.75, cost=0.078210, latency=684200.0, version="V1_B", passed=8),
                status="rejected",
                rejection_reason="inferior_to_Candidate_A",
            ),
        ],
    )

    payload = format_live_optimization_result(opt_res, goal="Reconcile accounts", baseline_graph=graph)
    assert "candidates" in payload
    assert len(payload["candidates"]) == 2
    assert payload["candidates"][0]["name"] == "Candidate A"
    assert payload["candidates"][0]["status"] == "selected"
    assert payload["candidates"][1]["name"] == "Candidate B"
    assert payload["candidates"][1]["status"] == "rejected"
    assert payload["candidates"][1]["rejection_reason"] == "inferior_to_Candidate_A"
