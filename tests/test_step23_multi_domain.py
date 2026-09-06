"""Comprehensive test suite for Multi-Domain Benchmarks and Domain Tools.

Verifies:
- 3 distinct domains: Financial Reconciliation, System Anomaly Detection, Research Synthesis
- Strict partition isolation (6 optimization, 4 held-out, zero leakage) for all domains
- Registration and execution of analytical domain tools:
  * Anomaly tools: compute_zscore, check_threshold, extract_error_logs
  * Research tools: extract_entities, compare_metrics, summarize_text
- ToolRegistry multi-domain factory methods (create_anomaly_default, create_research_default, create_multi_domain_default)
- End-to-end AgentRuntime execution and ground-truth eval_match across all 3 domains
- 4-Axis Scorecard evaluation across multi-domain suites
"""

import pytest
from reco.benchmarks.base import BenchmarkCase, BenchmarkSplit, BenchmarkSuite
from reco.benchmarks.reconciliation import (
    create_reconciliation_benchmark_cases,
    get_reconciliation_benchmark_suite,
)
from reco.benchmarks.anomaly import (
    create_anomaly_benchmark_cases,
    get_anomaly_benchmark_suite,
)
from reco.benchmarks.research import (
    create_research_benchmark_cases,
    get_research_benchmark_suite,
)
from reco.core.goal_analyzer import GoalAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import AgentArchitecture, EdgeSpec, NodeSpec, NodeStatus, NodeType
from reco.engine.runtime import AgentRuntime
from reco.evaluators.scorecard import ScorecardEvaluator
from reco.tools.registry import (
    ToolDefinition,
    ToolRegistry,
    check_threshold_handler,
    compare_metrics_handler,
    compute_zscore_handler,
    extract_entities_handler,
    extract_error_logs_handler,
    summarize_text_handler,
)


# ==============================================================================
# 1. Multi-Domain Benchmark Partitioning & Zero Leakage
# ==============================================================================

@pytest.mark.parametrize(
    "suite_fn, expected_domain_name, required_categories",
    [
        (
            get_reconciliation_benchmark_suite,
            "reconciliation",
            {"exact_match", "missing_records", "amount_mismatch", "duplicate_records", "format_variation"},
        ),
        (
            get_anomaly_benchmark_suite,
            "system_anomaly",
            {"metric_time_series", "threshold_alerts", "root_cause_diagnosis", "multi_metric_correlation"},
        ),
        (
            get_research_benchmark_suite,
            "research_synthesis",
            {"document_extraction", "metric_cross_referencing", "multi_source_summary", "contradiction_detection"},
        ),
    ],
)
def test_multi_domain_benchmark_isolation_and_coverage(suite_fn, expected_domain_name, required_categories):
    """Verify each of the 3 benchmark domains adheres strictly to the 6/4 partition split with zero leakage."""
    suite = suite_fn()
    assert isinstance(suite, BenchmarkSuite)
    assert len(suite) == 10

    # Partition count assertions
    opt_cases = suite.get_optimization_cases()
    held_cases = suite.get_held_out_cases()
    assert len(opt_cases) == 6, f"Expected 6 optimization cases, got {len(opt_cases)}"
    assert len(held_cases) == 4, f"Expected 4 held-out cases, got {len(held_cases)}"

    # Air-gapped disjointness (zero cross-split leakage)
    opt_ids = {c.case_id for c in opt_cases}
    held_ids = {c.case_id for c in held_cases}
    assert opt_ids.isdisjoint(held_ids), f"Cross-split leakage detected: {opt_ids & held_ids}"
    assert len(opt_ids) == 6
    assert len(held_ids) == 4

    # Formal partition isolation validation passes
    assert suite.validate_partition_isolation() is True

    # Phenomenon / Category coverage check
    suite_categories = {c.category for c in suite}
    for req_cat in required_categories:
        assert req_cat in suite_categories, f"Category '{req_cat}' missing from {expected_domain_name} suite."


# ==============================================================================
# 2. System Anomaly Detection Tools
# ==============================================================================

def test_compute_zscore_handler():
    """Verify statistical Z-score calculation and threshold outlier isolation."""
    # Series with a clear spike at index 4 (value 100.0)
    series = [10.0, 11.0, 10.5, 9.5, 100.0, 10.2, 10.8]
    res = compute_zscore_handler(values=series, threshold=2.0)

    assert res["count"] == 7
    assert res["status"] == "anomaly_detected"
    assert res["has_anomaly"] is True
    assert res["anomaly_count"] == 1
    assert res["anomalies"][0]["index"] == 4
    assert res["anomalies"][0]["value"] == 100.0
    assert res["anomalies"][0]["z_score"] >= 2.0

    # Clean series with zero anomalies
    clean_series = [10.0, 10.1, 9.9, 10.0, 10.2, 9.8]
    clean_res = compute_zscore_handler(values=clean_series, threshold=2.5)
    assert clean_res["status"] == "normal"
    assert clean_res["has_anomaly"] is False
    assert clean_res["anomaly_count"] == 0


def test_check_threshold_handler():
    """Verify multi-metric warning and critical threshold evaluations."""
    # 1. Critical breach on memory (94% > 90%)
    metrics = {"cpu_percent": 45.0, "memory_percent": 94.0, "disk_percent": 70.0}
    thresholds = {
        "cpu_percent": {"warning": 80.0, "critical": 90.0},
        "memory_percent": {"warning": 80.0, "critical": 90.0},
        "disk_percent": {"warning": 80.0, "critical": 90.0},
    }
    res = check_threshold_handler(metrics=metrics, thresholds=thresholds)
    assert res["status"] == "critical"
    assert res["is_healthy"] is False
    assert res["critical_count"] == 1
    assert res["warning_count"] == 0
    assert res["breach_count"] == 1
    assert res["breaches"][0]["metric"] == "memory_percent"

    # 2. Warning breach on cpu
    warn_metrics = {"cpu_percent": 85.0}
    warn_res = check_threshold_handler(metrics=warn_metrics, thresholds={"cpu_percent": {"warning": 80.0, "critical": 90.0}})
    assert warn_res["status"] == "warning"
    assert warn_res["warning_count"] == 1

    # 3. All healthy
    healthy_metrics = {"cpu_percent": 30.0, "memory_percent": 40.0}
    healthy_res = check_threshold_handler(metrics=healthy_metrics, thresholds=thresholds)
    assert healthy_res["status"] == "healthy"
    assert healthy_res["is_healthy"] is True
    assert healthy_res["breach_count"] == 0


def test_extract_error_logs_handler():
    """Verify log parsing, error aggregation, and root-cause candidate identification."""
    log_sample = [
        "2026-04-01 10:00:01 [INFO] [web-gateway] Request processed in 12ms",
        "2026-04-01 10:00:03 [ERROR] [payment-service] DatabaseConnectionTimeout: query failed after 30000ms",
        "2026-04-01 10:00:04 [ERROR] [payment-service] DatabaseConnectionTimeout: unable to acquire connection",
        "2026-04-01 10:00:05 [CRITICAL] [payment-service] DatabaseConnectionTimeout: connection pool exhausted",
        "2026-04-01 10:00:06 [WARN] [web-gateway] Upstream 504 Gateway Timeout",
    ]
    res = extract_error_logs_handler(logs=log_sample, min_level="WARN")

    assert res["status"] == "errors_detected"
    assert res["matched_logs"] == 4
    assert res["error_count"] == 2
    assert res["critical_count"] == 1
    assert res["warning_count"] == 1
    assert res["root_cause_candidate"] == "DatabaseConnectionTimeout"
    assert "payment-service" in res["services_affected"]


# ==============================================================================
# 3. Research Synthesis Tools
# ==============================================================================

def test_extract_entities_handler():
    """Verify research document entity extraction for models, benchmarks, and organizations."""
    abstract = (
        "We evaluate GLM-4.7-Flash released by Zhipu AI on the SWE-bench benchmark, "
        "measuring significant accuracy and latency gains."
    )
    res = extract_entities_handler(text=abstract)

    assert res["status"] == "extracted"
    assert "GLM-4.7-Flash" in res["entities"]["models"]
    assert "SWE-bench" in res["entities"]["datasets"]
    assert "Accuracy" in res["entities"]["metrics"]
    assert "Latency" in res["entities"]["metrics"]
    assert "Zhipu AI" in res["entities"]["organizations"]
    assert res["total_entities"] >= 4


def test_compare_metrics_handler():
    """Verify quantitative cross-referencing, deltas calculation, and best-performer isolation."""
    sources = {
        "Model_Alpha": {"accuracy": 82.5, "latency_ms": 110.0},
        "Model_Beta": {"accuracy": 89.0, "latency_ms": 85.0},
    }
    res = compare_metrics_handler(sources=sources, baseline="Model_Alpha")

    assert res["status"] == "comparison_complete"
    assert res["baseline"] == "Model_Alpha"
    assert "accuracy" in res["metrics_compared"]
    assert "latency_ms" in res["metrics_compared"]

    # Model_Beta is best in both accuracy (higher is better) and latency_ms (lower is better)
    assert res["leaders"]["accuracy"] == "Model_Beta"
    assert res["leaders"]["latency_ms"] == "Model_Beta"

    # Verify delta
    acc_cmp = res["comparison"]["accuracy"]
    assert pytest.approx(acc_cmp["deltas_from_baseline"]["Model_Beta"], 0.01) == 6.5


def test_summarize_text_handler():
    """Verify multi-document synthesis and topical coverage."""
    docs = {
        "doc_a": "Autonomous agent engineering systems iteratively mutate DAG architectures. Scorecard evaluation proves Pareto dominance across accuracy and latency.",
        "doc_b": "Failure diagnostics classify root causes into taxonomy categories. Mutators apply targeted remedies to resolve tool selection and schema violations.",
    }
    res = summarize_text_handler(text=docs, focus_topics=["autonomous agent", "failure diagnostics"])

    assert res["status"] == "summarized"
    assert res["source_count"] == 2
    assert "autonomous agent" in res["topics_covered"]
    assert "failure diagnostics" in res["topics_covered"]
    assert len(res["key_points"]) > 0
    assert len(res["summary"]) > 20


# ==============================================================================
# 4. Tool Registry Multi-Domain Catalog
# ==============================================================================

def test_tool_registry_multi_domain_factory_methods():
    """Verify ToolRegistry creates catalogs pre-loaded with domain-specific tools."""
    # Anomaly registry
    anom_reg = ToolRegistry.create_anomaly_default()
    assert anom_reg.has("compute_zscore")
    assert anom_reg.has("check_threshold")
    assert anom_reg.has("extract_error_logs")
    assert anom_reg.has("tabular_summary")  # Preserves base

    # Research registry
    rsch_reg = ToolRegistry.create_research_default()
    assert rsch_reg.has("extract_entities")
    assert rsch_reg.has("compare_metrics")
    assert rsch_reg.has("summarize_text")
    assert rsch_reg.has("tabular_summary")  # Preserves base

    # Unified Multi-domain registry
    unified_reg = ToolRegistry.create_multi_domain_default()
    # Reconciliation tools
    assert unified_reg.has("exact_reconcile")
    assert unified_reg.has("smart_reconcile")
    # Anomaly tools
    assert unified_reg.has("compute_zscore")
    assert unified_reg.has("check_threshold")
    assert unified_reg.has("extract_error_logs")
    # Research tools
    assert unified_reg.has("extract_entities")
    assert unified_reg.has("compare_metrics")
    assert unified_reg.has("summarize_text")
    # Base tools
    assert unified_reg.has("tabular_summary")
    assert unified_reg.has("compute_distributions")


# ==============================================================================
# 5. End-to-End AgentRuntime Execution Across All 3 Domains
# ==============================================================================

def test_end_to_end_execution_reconciliation_domain():
    """Verify execution and ground truth matching on Financial Reconciliation domain."""
    suite = get_reconciliation_benchmark_suite()
    case = suite.get_case("reco_opt_001_exact_match")
    assert case is not None

    registry = ToolRegistry.create_reconciliation_default()
    generator = ArchitectureGenerator(tool_registry=registry)
    spec = GoalAnalyzer().analyze("Reconcile financial ledger transactions")
    arch = generator.generate(spec)

    runtime = AgentRuntime(tool_registry=registry)
    result = runtime.execute(arch, case.input_data)

    assert result.status == NodeStatus.COMPLETED
    assert result.error is None
    assert case.eval_match(result.final_output) is True


def test_end_to_end_execution_system_anomaly_domain():
    """Verify execution and ground truth matching on System Anomaly Detection domain."""
    suite = get_anomaly_benchmark_suite()
    case = suite.get_case("anom_opt_001_cpu_spike")
    assert case is not None

    registry = ToolRegistry.create_anomaly_default()

    # Build specialized DAG for Z-score time-series analysis
    arch = AgentArchitecture(
        id="arch_anom_zscore",
        name="Agent_Anomaly_Zscore",
        task_spec=GoalAnalyzer().analyze("Analyze metric time-series and isolate Z-score spike"),
        nodes=[
            NodeSpec(id="input_node", type=NodeType.INPUT, name="Input", dependencies=[]),
            NodeSpec(
                id="tool_compute_zscore",
                type=NodeType.TOOL,
                name="Tool ZScore",
                tool_name="compute_zscore",
                dependencies=["input_node"],
            ),
            NodeSpec(id="output_node", type=NodeType.OUTPUT, name="Output", dependencies=["tool_compute_zscore"]),
        ],
        edges=[
            EdgeSpec(source="input_node", target="tool_compute_zscore"),
            EdgeSpec(source="tool_compute_zscore", target="output_node"),
        ],
    )

    runtime = AgentRuntime(tool_registry=registry)
    result = runtime.execute(arch, case.input_data)

    assert result.status == NodeStatus.COMPLETED
    assert result.error is None
    assert case.eval_match(result.final_output) is True


def test_end_to_end_execution_research_synthesis_domain():
    """Verify execution and ground truth matching on Research Synthesis domain."""
    suite = get_research_benchmark_suite()
    case = suite.get_case("rsch_opt_002_model_metric_comparison")
    assert case is not None

    registry = ToolRegistry.create_research_default()

    # Build specialized DAG for research metric comparison
    arch = AgentArchitecture(
        id="arch_rsch_metric_cmp",
        name="Agent_Research_CompareMetrics",
        task_spec=GoalAnalyzer().analyze("Compare quantitative model metrics across benchmark papers"),
        nodes=[
            NodeSpec(id="input_node", type=NodeType.INPUT, name="Input", dependencies=[]),
            NodeSpec(
                id="tool_compare_metrics",
                type=NodeType.TOOL,
                name="Tool Compare Metrics",
                tool_name="compare_metrics",
                dependencies=["input_node"],
            ),
            NodeSpec(id="output_node", type=NodeType.OUTPUT, name="Output", dependencies=["tool_compare_metrics"]),
        ],
        edges=[
            EdgeSpec(source="input_node", target="tool_compare_metrics"),
            EdgeSpec(source="tool_compare_metrics", target="output_node"),
        ],
    )

    runtime = AgentRuntime(tool_registry=registry)
    result = runtime.execute(arch, case.input_data)

    assert result.status == NodeStatus.COMPLETED
    assert result.error is None
    assert case.eval_match(result.final_output) is True


# ==============================================================================
# 6. Multi-Domain 4-Axis Scorecard Evaluation
# ==============================================================================

def test_scorecard_evaluation_across_all_three_domains():
    """Verify ScorecardEvaluator reliably evaluates architectures across all three benchmark suites."""
    evaluator = ScorecardEvaluator()

    # 1. Reconciliation Evaluation
    reco_suite = get_reconciliation_benchmark_suite()
    reco_registry = ToolRegistry.create_reconciliation_default()
    reco_arch = ArchitectureGenerator(tool_registry=reco_registry).generate(
        GoalAnalyzer().analyze("Reconcile financial transactions and match records")
    )
    reco_runtime = AgentRuntime(tool_registry=reco_registry)
    reco_evaluator = ScorecardEvaluator(runtime=reco_runtime)
    reco_scorecard = reco_evaluator.evaluate(reco_arch, reco_suite, split="optimization")

    assert reco_scorecard.total_cases == 6
    assert reco_scorecard.reliability == 1.0
    assert reco_scorecard.accuracy >= 0.8  # Baseline passes 5/6

    # 2. Anomaly Evaluation
    anom_suite = get_anomaly_benchmark_suite()
    anom_registry = ToolRegistry.create_anomaly_default()
    anom_arch = AgentArchitecture(
        id="arch_anom_eval",
        name="Agent_Anomaly_Threshold",
        task_spec=GoalAnalyzer().analyze("Check metric thresholds and detect breaches"),
        nodes=[
            NodeSpec(id="input_node", type=NodeType.INPUT, name="Input", dependencies=[]),
            NodeSpec(
                id="tool_check_threshold",
                type=NodeType.TOOL,
                name="Tool Check Threshold",
                tool_name="check_threshold",
                dependencies=["input_node"],
            ),
            NodeSpec(id="output_node", type=NodeType.OUTPUT, name="Output", dependencies=["tool_check_threshold"]),
        ],
        edges=[
            EdgeSpec(source="input_node", target="tool_check_threshold"),
            EdgeSpec(source="tool_check_threshold", target="output_node"),
        ],
    )
    anom_runtime = AgentRuntime(tool_registry=anom_registry)
    anom_evaluator = ScorecardEvaluator(runtime=anom_runtime)
    anom_scorecard = anom_evaluator.evaluate(anom_arch, anom_suite, split="optimization")

    assert anom_scorecard.total_cases == 6
    assert anom_scorecard.reliability == 1.0
    assert anom_scorecard.latency_ms > 0.0

    # 3. Research Evaluation
    rsch_suite = get_research_benchmark_suite()
    rsch_registry = ToolRegistry.create_research_default()
    rsch_arch = AgentArchitecture(
        id="arch_rsch_eval",
        name="Agent_Research_EntityExtract",
        task_spec=GoalAnalyzer().analyze("Extract research entities and models"),
        nodes=[
            NodeSpec(id="input_node", type=NodeType.INPUT, name="Input", dependencies=[]),
            NodeSpec(
                id="tool_extract_entities",
                type=NodeType.TOOL,
                name="Tool Entity Extract",
                tool_name="extract_entities",
                dependencies=["input_node"],
            ),
            NodeSpec(id="output_node", type=NodeType.OUTPUT, name="Output", dependencies=["tool_extract_entities"]),
        ],
        edges=[
            EdgeSpec(source="input_node", target="tool_extract_entities"),
            EdgeSpec(source="tool_extract_entities", target="output_node"),
        ],
    )
    rsch_runtime = AgentRuntime(tool_registry=rsch_registry)
    rsch_evaluator = ScorecardEvaluator(runtime=rsch_runtime)
    rsch_scorecard = rsch_evaluator.evaluate(rsch_arch, rsch_suite, split="optimization")

    assert rsch_scorecard.total_cases == 6
    assert rsch_scorecard.reliability == 1.0
    assert rsch_scorecard.latency_ms > 0.0
