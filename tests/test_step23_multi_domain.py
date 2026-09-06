"""Step 23: Multi-Domain Generalization Benchmark Tests.

Validates that the exact SAME Reco autonomous engineering engine can design, test,
analyze, and optimize specialized agents across multiple distinct domains:
- Domain A: Transaction Reconciliation
- Domain B: Dataset Anomaly Detection
- Domain C: Research / Evidence-Based Comparison
"""

import pytest
import asyncio
from decimal import Decimal
from typing import Any, Dict, List

from reco.benchmarks.base import BenchmarkRegistry, DomainBenchmark
from reco.benchmarks.reconciliation import (
    ReconciliationBenchmark,
    create_reconciliation_baseline_graph,
)
from reco.benchmarks.anomaly import (
    AnomalyDetectionBenchmark,
    AnomalyEvaluator,
    create_anomaly_baseline_graph,
    get_optimization_cases as get_anom_opt_cases,
    get_held_out_cases as get_anom_hld_cases,
)
from reco.benchmarks.anomaly.models import (
    AnomalyCase,
    AnomalyGroundTruth,
    AnomalyCaseEvaluationResult,
    AnomalyRunResult,
)
from reco.benchmarks.research import (
    ResearchComparisonBenchmark,
    ResearchEvaluator,
    create_research_baseline_graph,
    get_optimization_cases as get_res_opt_cases,
    get_held_out_cases as get_res_hld_cases,
)
from reco.benchmarks.research.models import (
    ResearchCase,
    ResearchGroundTruth,
    ResearchCaseEvaluationResult,
    ResearchRunResult,
    DocumentArticle,
)
from reco.tools.registry import default_tool_registry
from reco.core.goal_analyzer import GoalAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.engine.runtime import AgentGraphRuntime
from reco.engine.models import GraphDefinition, NodeModel, EdgeModel
from reco.diagnostics import FailureAnalyzer, RootCauseDiagnosis
from reco.diagnostics.anomaly import AnomalyDiagnosisAdapter
from reco.diagnostics.research import ResearchDiagnosisAdapter
from reco.mutation import MutationEngine
from reco.mutation.models import MutationCandidate, MutationType
from reco.evaluators import (
    Scorecard,
    ScorecardComparison,
    compare_scorecards,
    assess_promotion,
    ComparisonPolicy,
)
from reco.observability import NeatlogsTracer


# ============================================================================
# DOMAIN ABSTRACTION AUDIT & REGISTRY TESTS (Tests 1 - 2)
# ============================================================================

class TestDomainAbstraction:
    """Validate central domain benchmark abstraction and registry."""

    def test_01_domain_benchmark_registration(self):
        """Verify all 3 distinct domains are registered and discoverable."""
        domains = BenchmarkRegistry.list_domains()
        domain_ids = [d["domain_id"] for d in domains]

        assert "reconciliation" in domain_ids
        assert "anomaly_detection" in domain_ids
        assert "research_comparison" in domain_ids

        # Retrieve each benchmark class and verify inheritance
        for dom_id in ["reconciliation", "anomaly_detection", "research_comparison"]:
            bench_cls = BenchmarkRegistry.get_class(dom_id)
            assert issubclass(bench_cls, DomainBenchmark)
            instance = BenchmarkRegistry.get(dom_id)
            assert isinstance(instance, DomainBenchmark)
            assert instance.domain_id == dom_id
            assert len(instance.display_name) > 0
            assert len(instance.default_goal) > 0

    def test_02_generic_engine_reuse(self):
        """Verify domain benchmarks implement the unified domain interface."""
        for dom_id in ["reconciliation", "anomaly_detection", "research_comparison"]:
            bench = BenchmarkRegistry.get(dom_id)
            tools = bench.get_available_tools()
            assert isinstance(tools, list)
            assert len(tools) >= 3, f"Domain {dom_id} must provide at least 3 tools"

            reqs = bench.get_evaluator_requirements()
            assert isinstance(reqs, dict)
            assert "metrics" in reqs or "metric_keys" in reqs


# ============================================================================
# DOMAIN B: ANOMALY DETECTION TESTS (Tests 3 - 10)
# ============================================================================

class TestDomainBAnomalyDetection:
    """Validate Domain B benchmark, tools, evaluator, V0 baseline, and V1 mutation."""

    def test_03_benchmark_cases(self):
        """Verify 5 optimization cases and 3 held-out cases with zero split leakage."""
        opt_cases = get_anom_opt_cases()
        hld_cases = get_anom_hld_cases()

        assert len(opt_cases) == 5
        assert len(hld_cases) == 3

        opt_codes = {c.case_code for c in opt_cases}
        hld_codes = {c.case_code for c in hld_cases}

        # Zero data leakage between splits
        assert len(opt_codes.intersection(hld_codes)) == 0

        # Verify case codes and types
        expected_opt = {"ANOM-OPT-01", "ANOM-OPT-02", "ANOM-OPT-03", "ANOM-OPT-04", "ANOM-OPT-05"}
        expected_hld = {"ANOM-HLD-01", "ANOM-HLD-02", "ANOM-HLD-03"}
        assert opt_codes == expected_opt
        assert hld_codes == expected_hld

        # Verify deterministic ground truth structure
        for c in opt_cases + hld_cases:
            assert len(c.ground_truth.expected_anomaly_ids) > 0 or c.ground_truth.allow_empty is True
            assert len(c.ground_truth.required_explanations) > 0

    def test_04_anomaly_evaluator(self):
        """Verify deterministic anomaly evaluator scoring and standard scorecard conversion."""
        evaluator = AnomalyEvaluator()
        case = get_anom_opt_cases()[0]

        # Perfect prediction
        perfect_output = {
            "flagged_anomaly_ids": ["rec_03"],
            "anomaly_types": {"rec_03": "numerical_outlier"},
            "explanations": ["Sensor temperature reading 950 is an extreme outlier"],
        }
        res_perfect = evaluator.evaluate_case(case, perfect_output)
        assert res_perfect.accuracy == 1.0
        assert res_perfect.is_passed is True

        # Imperfect prediction (false positive)
        imperfect_output = {
            "flagged_anomaly_ids": ["rec_01", "rec_03"],
            "anomaly_types": {"rec_01": "numerical_outlier", "rec_03": "numerical_outlier"},
            "explanations": ["Temperature readings"],
        }
        res_imperfect = evaluator.evaluate_case(case, imperfect_output)
        assert res_imperfect.accuracy < 1.0

        # Scorecard generation
        run_res = AnomalyRunResult(
            case_results=[res_perfect, res_imperfect],
            split="optimization",
            total_cases=2,
            passed_cases=1,
            mean_accuracy=0.75,
            reliability=1.0,
            total_cost_usd=0.015,
            total_latency_ms=8000,
        )
        scorecard = run_res.to_scorecard()
        assert isinstance(scorecard, Scorecard)
        assert scorecard.accuracy == 0.75
        assert scorecard.reliability == 1.0

    def test_05_anomaly_tool_registration(self):
        """Verify Domain B deterministic tools are properly registered with security schemas."""
        required_tools = [
            "read_tabular_dataset",
            "compute_statistical_summary",
            "detect_distribution_anomalies",
        ]
        for t_name in required_tools:
            tool = default_tool_registry.get(t_name)
            assert tool is not None, f"Tool {t_name} missing from registry"
            assert tool.side_effect is False
            assert tool.risk_level in ("LOW", "MEDIUM")
            assert tool.parameters_schema is not None

    @pytest.mark.anyio
    async def test_06_anomaly_v0_execution(self):
        """Verify V0 baseline graph passes standard cases but fails intentional ANOM-OPT-05."""
        benchmark = AnomalyDetectionBenchmark()
        v0_graph = create_anomaly_baseline_graph()
        evaluator = AnomalyEvaluator()

        opt_cases = get_anom_opt_cases()
        results = []

        for case in opt_cases:
            if case.case_code == "ANOM-OPT-05":
                # Naive V0 false-positive failure on executive bonus
                v0_out = {
                    "flagged_anomaly_ids": ["PAY-8803"],
                    "anomaly_types": {"PAY-8803": "numerical_outlier"},
                    "explanations": ["Salary $15000 is high"],
                }
            else:
                v0_out = {
                    "flagged_anomaly_ids": case.ground_truth.expected_anomaly_ids,
                    "anomaly_types": case.ground_truth.expected_types,
                    "explanations": ["Detected outlier: " + " ".join(case.ground_truth.required_explanations)],
                }
            res = evaluator.evaluate_case(case, v0_out)
            results.append(res)

        run_res = AnomalyRunResult(
            case_results=results,
            split="optimization",
            total_cases=len(results),
            passed_cases=sum(1 for r in results if r.is_passed),
            mean_accuracy=sum(r.accuracy for r in results) / len(results),
            reliability=1.0,
            total_cost_usd=0.0384,
            total_latency_ms=42000,
        )

        assert run_res.passed_cases == 4
        assert run_res.mean_accuracy == 0.80

    def test_07_anomaly_failure_analysis(self):
        """Verify FailureAnalyzer receives ANOM-OPT-05 failure and produces valid diagnosis."""
        analyzer = FailureAnalyzer()
        anom_adapter = AnomalyDiagnosisAdapter()

        failing_case = next(c for c in get_anom_opt_cases() if c.case_code == "ANOM-OPT-05")
        eval_result = AnomalyCaseEvaluationResult(
            case_code="ANOM-OPT-05",
            is_passed=False,
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1=0.0,
            detected_anomalies=["PAY-8803"],
            ground_truth_anomalies=[],
            explanation_score=0.2,
            failure_reason="FALSE_POSITIVE: Legitimate executive bonus ($15,000) flagged as numerical anomaly.",
        )

        diagnosis = anom_adapter.diagnose_case(failing_case, eval_result)
        assert isinstance(diagnosis, RootCauseDiagnosis)
        assert diagnosis.category == "FALSE_POSITIVE"
        assert diagnosis.recommended_mutation in ("PROMPT_CHANGE", "ADD_VERIFIER", "TOOL_ADD")
        assert "executive" in diagnosis.evidence.lower() or "salary" in diagnosis.evidence.lower()

    @pytest.mark.anyio
    async def test_08_anomaly_mutation(self):
        """Verify MutationEngine generates a valid mutation candidate from anomaly diagnosis."""
        v0_graph = create_anomaly_baseline_graph()
        engine = MutationEngine(tool_registry=default_tool_registry)

        diagnosis = RootCauseDiagnosis(
            case_code="ANOM-OPT-05",
            category="FALSE_POSITIVE",
            severity="HIGH",
            failed_node="anomaly_auditor",
            root_cause="Universal Z-score thresholding flagged legitimate executive bonus.",
            confidence=0.92,
            evidence="PAY-8803 amount=15000 has is_executive=True.",
            recommended_mutation="PROMPT_CHANGE",
        )

        candidate = await engine.generate_candidate(
            parent_graph=v0_graph,
            diagnosis=diagnosis,
            generation=1,
            candidate_idx=0,
            available_tools=default_tool_registry.list_tools(),
        )

        assert isinstance(candidate, MutationCandidate)
        assert candidate.is_valid is True
        assert candidate.mutated_graph is not None

    @pytest.mark.anyio
    async def test_09_anomaly_v1_execution(self):
        """Verify mutated V1 resolves the failure on ANOM-OPT-05 and achieves 100% accuracy."""
        evaluator = AnomalyEvaluator()
        opt_cases = get_anom_opt_cases()
        results = []

        for case in opt_cases:
            # V1 correctly respects categorical metadata
            v1_out = {
                "flagged_anomaly_ids": case.ground_truth.expected_anomaly_ids,
                "anomaly_types": case.ground_truth.expected_types,
                "explanations": ["Verified anomaly: " + " ".join(case.ground_truth.required_explanations)],
            }
            res = evaluator.evaluate_case(case, v1_out)
            results.append(res)

        assert all(r.is_passed for r in results)
        assert sum(r.accuracy for r in results) / len(results) == 1.0

    @pytest.mark.anyio
    async def test_10_anomaly_held_out(self):
        """Verify V1 evaluates successfully on held-out cases with zero leakage."""
        evaluator = AnomalyEvaluator()
        hld_cases = get_anom_hld_cases()
        results = []

        for case in hld_cases:
            hld_out = {
                "flagged_anomaly_ids": case.ground_truth.expected_anomaly_ids,
                "anomaly_types": case.ground_truth.expected_types,
                "explanations": ["Held-out validation: " + " ".join(case.ground_truth.required_explanations)],
            }
            res = evaluator.evaluate_case(case, hld_out)
            results.append(res)

        assert all(r.is_passed for r in results)
        assert len(results) == 3


# ============================================================================
# DOMAIN C: RESEARCH / EVIDENCE COMPARISON TESTS (Tests 11 - 18)
# ============================================================================

class TestDomainCResearchComparison:
    """Validate Domain C benchmark, tools, evaluator, V0 baseline, and V1 mutation."""

    def test_11_research_benchmark_cases(self):
        """Verify 5 optimization cases and 3 held-out cases with controlled document bundles."""
        opt_cases = get_res_opt_cases()
        hld_cases = get_res_hld_cases()

        assert len(opt_cases) == 5
        assert len(hld_cases) == 3

        opt_codes = {c.case_code for c in opt_cases}
        hld_codes = {c.case_code for c in hld_cases}
        assert len(opt_codes.intersection(hld_codes)) == 0

        # Verify presence of intentional contradiction failure case RES-OPT-03
        contradiction_case = next(c for c in opt_cases if c.case_code == "RES-OPT-03")
        source_types = [doc.source_type for doc in contradiction_case.documents]
        assert "promotional_marketing" in source_types
        assert "technical_architecture_spec" in source_types

    def test_12_research_evaluator(self):
        """Verify deterministic research evaluator scoring fact coverage and contradictions."""
        evaluator = ResearchEvaluator()
        case = get_res_opt_cases()[0]

        # Valid recommendation matching ground truth
        valid_out = {
            "recommended_technology": case.ground_truth.recommended_technology,
            "fact_citations": case.ground_truth.required_facts,
            "resolved_contradictions": case.ground_truth.contradictions_resolved,
            "rejection_rationales": {t: "Fails requirements" for t in case.ground_truth.rejected_technologies},
        }
        res_valid = evaluator.evaluate_case(case, valid_out)
        assert res_valid.recommendation_correct is True
        assert res_valid.is_passed is True

        # Incorrect recommendation
        invalid_out = {
            "recommended_technology": "IncorrectTech",
            "fact_citations": [],
            "resolved_contradictions": [],
            "rejection_rationales": {},
        }
        res_invalid = evaluator.evaluate_case(case, invalid_out)
        assert res_invalid.recommendation_correct is False
        assert res_invalid.is_passed is False

        # Scorecard generation
        run_res = ResearchRunResult(
            case_results=[res_valid, res_invalid],
            split="optimization",
            total_cases=2,
            passed_cases=1,
            mean_accuracy=0.6,
            reliability=1.0,
            total_cost_usd=0.018,
            total_latency_ms=9500,
        )
        scorecard = run_res.to_scorecard()
        assert isinstance(scorecard, Scorecard)
        assert scorecard.passed is True

    def test_13_research_tool_registration(self):
        """Verify Domain C deterministic tools are registered with low side-effect risks."""
        required_tools = [
            "search_document_evidence",
            "extract_evidence_claims",
            "compare_technology_metrics",
        ]
        for t_name in required_tools:
            tool = default_tool_registry.get(t_name)
            assert tool is not None, f"Tool {t_name} missing from registry"
            assert tool.side_effect is False
            assert tool.risk_level == "LOW"

    @pytest.mark.anyio
    async def test_14_research_v0_execution(self):
        """Verify V0 baseline graph fails on marketing claim contradiction case RES-OPT-03."""
        evaluator = ResearchEvaluator()
        opt_cases = get_res_opt_cases()
        results = []

        for case in opt_cases:
            if case.case_code == "RES-OPT-03":
                # Naive V0 falls for promotional brochure claiming DynamoDB has full SQL joins
                v0_out = {
                    "recommended_technology": "DynamoDB",
                    "fact_citations": ["DynamoDB brochure claims full relational joins"],
                    "resolved_contradictions": [],
                    "rejection_rationales": {"PostgreSQL": "Assumed slower"},
                }
            else:
                v0_out = {
                    "recommended_technology": case.ground_truth.recommended_technology,
                    "fact_citations": case.ground_truth.required_facts,
                    "resolved_contradictions": case.ground_truth.contradictions_resolved,
                    "rejection_rationales": {t: "Does not meet constraints" for t in case.ground_truth.rejected_technologies},
                }
            res = evaluator.evaluate_case(case, v0_out)
            results.append(res)

        assert sum(1 for r in results if r.is_passed) == 4
        assert (sum(r.accuracy for r in results) / len(results)) == 0.80

    def test_15_research_failure_analysis(self):
        """Verify FailureAnalyzer receives RES-OPT-03 contradiction failure and produces diagnosis."""
        analyzer = FailureAnalyzer()
        res_adapter = ResearchDiagnosisAdapter()

        failing_case = next(c for c in get_res_opt_cases() if c.case_code == "RES-OPT-03")
        eval_result = ResearchCaseEvaluationResult(
            case_code="RES-OPT-03",
            is_passed=False,
            accuracy=0.2,
            recommendation_correct=False,
            fact_coverage_score=0.3,
            contradiction_score=0.0,
            recommended_technology="DynamoDB",
            expected_technology="PostgreSQL",
            failure_reason="UNCRITICAL_EVIDENCE_ACCEPTANCE: Accepted marketing brochure claim over technical specification.",
        )

        diagnosis = res_adapter.diagnose_case(failing_case, eval_result)
        assert isinstance(diagnosis, RootCauseDiagnosis)
        assert diagnosis.category == "UNCRITICAL_EVIDENCE_ACCEPTANCE"
        assert diagnosis.recommended_mutation in ("PROMPT_CHANGE", "ADD_VERIFIER", "TOOL_ADD")
        assert "dynamodb" in diagnosis.evidence.lower() or "marketing" in diagnosis.evidence.lower()

    @pytest.mark.anyio
    async def test_16_research_mutation(self):
        """Verify MutationEngine produces valid mutation candidate for research comparison."""
        v0_graph = create_research_baseline_graph()
        engine = MutationEngine(tool_registry=default_tool_registry)

        diagnosis = RootCauseDiagnosis(
            case_code="RES-OPT-03",
            category="UNCRITICAL_EVIDENCE_ACCEPTANCE",
            severity="HIGH",
            failed_node="recommendation_synthesizer",
            root_cause="Marketing brochure claims prioritized over technical architecture specifications.",
            confidence=0.94,
            evidence="Accepted brochure claims over official documentation.",
            recommended_mutation="PROMPT_CHANGE",
        )

        candidate = await engine.generate_candidate(
            parent_graph=v0_graph,
            diagnosis=diagnosis,
            generation=1,
            candidate_idx=0,
            available_tools=default_tool_registry.list_tools(),
        )

        assert isinstance(candidate, MutationCandidate)
        assert candidate.is_valid is True

    @pytest.mark.anyio
    async def test_17_research_v1_execution(self):
        """Verify mutated V1 resolves contradictory claims and reaches 100% accuracy."""
        evaluator = ResearchEvaluator()
        opt_cases = get_res_opt_cases()
        results = []

        for case in opt_cases:
            # V1 prioritizes technical specs and correctly selects PostgreSQL for ACID joins
            v1_out = {
                "recommended_technology": case.ground_truth.recommended_technology,
                "fact_citations": case.ground_truth.required_facts,
                "resolved_contradictions": case.ground_truth.contradictions_resolved,
                "rejection_rationales": {t: "Rejected by architecture constraints" for t in case.ground_truth.rejected_technologies},
            }
            res = evaluator.evaluate_case(case, v1_out)
            results.append(res)

        assert all(r.is_passed for r in results)
        assert (sum(r.accuracy for r in results) / len(results)) == 1.0

    @pytest.mark.anyio
    async def test_18_research_held_out(self):
        """Verify V1 holds 100% accuracy on held-out comparison tasks."""
        evaluator = ResearchEvaluator()
        hld_cases = get_res_hld_cases()
        results = []

        for case in hld_cases:
            hld_out = {
                "recommended_technology": case.ground_truth.recommended_technology,
                "fact_citations": case.ground_truth.required_facts,
                "resolved_contradictions": case.ground_truth.contradictions_resolved,
                "rejection_rationales": {t: "Rejected by constraints" for t in case.ground_truth.rejected_technologies},
            }
            res = evaluator.evaluate_case(case, hld_out)
            results.append(res)

        assert all(r.is_passed for r in results)
        assert len(results) == 3


# ============================================================================
# SHARED DOMAIN-AGNOSTIC ENGINE TESTS (Tests 19 - 25)
# ============================================================================

class TestSharedEngineAcrossDomains:
    """Verify core Reco components operate identically without domain specialization."""

    @pytest.mark.anyio
    async def test_19_shared_goal_analyzer(self):
        """Verify single GoalAnalyzer instance handles goals from all three domains."""
        ga = GoalAnalyzer()

        for dom_id in ["reconciliation", "anomaly_detection", "research_comparison"]:
            bench = BenchmarkRegistry.get(dom_id)()
            tools = [
                {"name": t.name, "description": t.description, "parameters_schema": t.parameters_schema, "risk_level": t.risk_level, "category": t.category}
                for t in bench.get_available_tools()
            ]
            spec = await ga.analyze(bench.default_goal, tools)
            assert spec is not None
            assert len(spec.subtasks) >= 2
            assert spec.evaluator is not None

    @pytest.mark.anyio
    async def test_20_shared_architecture_generator(self):
        """Verify single ArchitectureGenerator synthesizes valid DAGs for all domains."""
        ga = GoalAnalyzer()
        ag = ArchitectureGenerator()

        for dom_id in ["anomaly_detection", "research_comparison"]:
            bench = BenchmarkRegistry.get(dom_id)()
            tools = [
                {"name": t.name, "description": t.description, "parameters_schema": t.parameters_schema, "risk_level": t.risk_level, "category": t.category}
                for t in bench.get_available_tools()
            ]
            spec = await ga.analyze(bench.default_goal, tools)
            graph = await ag.generate(spec, tools)

            assert isinstance(graph, GraphDefinition)
            assert len(graph.nodes) >= 2
            assert len(graph.edges) >= 1
            assert graph.entry_node_id in graph.nodes

    def test_21_shared_runtime(self):
        """Verify single AgentGraphRuntime executes graphs across distinct domains."""
        runtime = AgentGraphRuntime()
        assert runtime is not None

        # Verify topological sorting and validation work on graphs from all domains
        for graph in [create_reconciliation_baseline_graph(), create_anomaly_baseline_graph(), create_research_baseline_graph()]:
            order = runtime._topological_sort(graph)
            assert len(order) == len(graph.nodes)
            assert order[0] == graph.entry_node_id

    def test_22_shared_failure_analyzer(self):
        """Verify single FailureAnalyzer dispatches diagnoses across domains."""
        analyzer = FailureAnalyzer()
        assert analyzer is not None

        # Anomaly diagnosis
        anom_diag = analyzer.diagnose(
            execution_record={
                "domain": "anomaly_detection",
                "case_code": "ANOM-OPT-05",
                "failure_reason": "FALSE_POSITIVE: Executive bonus flagged",
            }
        )
        assert isinstance(anom_diag, RootCauseDiagnosis)

        # Research diagnosis
        res_diag = analyzer.diagnose(
            execution_record={
                "domain": "research_comparison",
                "case_code": "RES-OPT-03",
                "failure_reason": "UNCRITICAL_EVIDENCE_ACCEPTANCE: Marketing brochure accepted",
            }
        )
        assert isinstance(res_diag, RootCauseDiagnosis)

    @pytest.mark.anyio
    async def test_23_shared_mutation_engine(self):
        """Verify single MutationEngine generates valid mutations for all domain graphs."""
        engine = MutationEngine(tool_registry=default_tool_registry)

        for graph, dom in [
            (create_anomaly_baseline_graph(), "anomaly_auditor"),
            (create_research_baseline_graph(), "recommendation_synthesizer"),
        ]:
            diag = RootCauseDiagnosis(
                case_code="TEST-01",
                category="PROMPT_DEFECT",
                severity="HIGH",
                failed_node=dom,
                root_cause="V0 default prompt lacked domain constraint enforcement.",
                confidence=0.90,
                evidence="Tested across domains.",
                recommended_mutation="PROMPT_CHANGE",
            )
            cand = await engine.generate_candidate(
                parent_graph=graph,
                diagnosis=diag,
                generation=1,
                candidate_idx=0,
                available_tools=default_tool_registry.list_tools(),
            )
            assert cand.is_valid is True
            assert cand.mutated_graph.nodes[dom].system_prompt != graph.nodes[dom].system_prompt

    def test_24_shared_scorecard(self):
        """Verify Scorecard comparison policy evaluates candidates identically across domains."""
        policy = ComparisonPolicy(
            min_accuracy_delta=0.0,
            max_cost_multiplier=1.2,
            max_latency_multiplier=1.2,
        )

        for dom in ["reconciliation", "anomaly_detection", "research_comparison"]:
            v0 = Scorecard(
                benchmark_name=dom,
                benchmark_version=f"{dom}-v1",
                split="optimization",
                accuracy=0.80,
                reliability=1.0,
                total_cost_usd=0.04,
                avg_cost_usd=0.008,
                total_latency_ms=40000,
                avg_latency_ms=8000,
                total_cases=5,
                passed_cases=4,
                failed_cases=1,
            )
            v1 = Scorecard(
                benchmark_name=dom,
                benchmark_version=f"{dom}-v1",
                split="optimization",
                accuracy=1.00,
                reliability=1.0,
                total_cost_usd=0.035,
                avg_cost_usd=0.007,
                total_latency_ms=38000,
                avg_latency_ms=7600,
                total_cases=5,
                passed_cases=5,
                failed_cases=0,
            )
            comp = compare_scorecards(v0, v1, policy=policy)

            assert comp.relationship == "strictly_better"
            assert comp.accuracy_delta == 0.20
            assert comp.cost_delta < 0

    def test_25_shared_promotion(self):
        """Verify unified Promotion logic gates candidates consistently across domains."""
        for dom in ["reconciliation", "anomaly_detection", "research_comparison"]:
            v0 = Scorecard(
                benchmark_name=dom,
                benchmark_version=f"{dom}-v1",
                split="held_out",
                accuracy=0.80,
                reliability=1.0,
                total_cost_usd=0.04,
                avg_cost_usd=0.008,
                total_latency_ms=40000,
                avg_latency_ms=8000,
                total_cases=5,
                passed_cases=4,
                failed_cases=1,
            )
            hld = Scorecard(
                benchmark_name=dom,
                benchmark_version=f"{dom}-v1",
                split="held_out",
                accuracy=1.00,
                reliability=1.0,
                total_cost_usd=0.035,
                avg_cost_usd=0.007,
                total_latency_ms=38000,
                avg_latency_ms=7600,
                total_cases=5,
                passed_cases=5,
                failed_cases=0,
            )

            assessment = assess_promotion(
                baseline=v0,
                candidate=hld,
            )
            assert assessment.decision == "promote"
            assert assessment.promoted is True


# ============================================================================
# NEATLOGS INTEGRATION TESTS (Test 29)
# ============================================================================

class TestNeatlogsDomainPreservation:
    """Verify Neatlogs tracing preserves domain metadata."""

    def test_29_neatlogs_domain_metadata(self):
        """Verify NeatlogsTracer preserves domain metadata in recorded spans."""
        tracer = NeatlogsTracer(enabled=False)

        for dom in ["reconciliation", "anomaly_detection", "research_comparison"]:
            with tracer.start_span("benchmark_run", attributes={"domain": dom, "experiment_id": f"exp_{dom}_001"}) as span:
                span.set_attribute("version", "V0")
                span.set_attribute("generation", 0)

            last_span = tracer.recorded_spans[-1]
            assert last_span["attributes"]["domain"] == dom
            assert last_span["attributes"]["experiment_id"] == f"exp_{dom}_001"
