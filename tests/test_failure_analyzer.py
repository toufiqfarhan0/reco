"""Test suite for 12-Category Failure Diagnostics Taxonomy and Root Cause Analyzer."""

import pytest
from reco.benchmarks.base import BenchmarkCase, BenchmarkSplit
from reco.benchmarks.reconciliation.dataset import get_reconciliation_benchmark_suite
from reco.core.goal_analyzer import GoalAnalyzer
from reco.diagnostics.analyzer import FailureAnalyzer
from reco.diagnostics.taxonomy import (
    CATEGORY_DEFAULT_MUTATORS,
    CATEGORY_DESCRIPTIONS,
    DiagnosticReport,
    FailureCategory,
    FailureDiagnostic,
)
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import AgentArchitecture, NodeStatus, NodeType
from reco.engine.state import NodeExecutionRecord
from reco.engine.runtime import AgentRuntime, ExecutionResult
from reco.evaluators.scorecard import CaseEvaluationResult, Scorecard, ScorecardEvaluator
from reco.tools.registry import ToolRegistry


def test_taxonomy_12_categories_and_models():
    """Verify presence and metadata of all 12 FailureCategory taxonomy categories."""
    expected_categories = [
        "prompt_ambiguity",
        "tool_selection_error",
        "tool_parameter_error",
        "schema_violation",
        "verification_miss",
        "routing_misdirect",
        "context_overflow",
        "retry_exhaustion",
        "model_capability_limit",
        "timeout_exceeded",
        "state_corruption",
        "unhandled_exception",
    ]

    # Verify all 12 categories are present
    assert len(FailureCategory) == 12
    for cat_name in expected_categories:
        cat_enum = FailureCategory(cat_name)
        assert cat_enum in FailureCategory
        assert cat_enum in CATEGORY_DESCRIPTIONS
        assert cat_enum in CATEGORY_DEFAULT_MUTATORS

    # Test FailureDiagnostic initialization
    diag = FailureDiagnostic(
        case_id="case_test_01",
        category=FailureCategory.TOOL_SELECTION_ERROR,
        root_cause="Tool 'exact_reconcile' lacks currency format parsing",
        symptoms=["Discrepancy detected on formatted records"],
        remedy_suggestion="Replace with smart_reconcile",
        target_node_id="tool_exact_reconcile",
        recommended_mutator="ToolAssignmentMutator"
    )
    assert diag.category == FailureCategory.TOOL_SELECTION_ERROR
    assert diag.recommended_mutator == "ToolAssignmentMutator"

    # Test DiagnosticReport helper methods and markdown export
    report = DiagnosticReport(
        architecture_id="arch_test",
        total_cases=6,
        passed_cases=5,
        failed_cases=1,
        failure_diagnostics=[diag],
        category_counts={"tool_selection_error": 1},
        summary="Diagnosed 1 failure."
    )
    assert report.has_category(FailureCategory.TOOL_SELECTION_ERROR) is True
    assert report.has_category("tool_selection_error") is True
    assert report.has_category(FailureCategory.TIMEOUT_EXCEEDED) is False
    assert len(report.get_by_category(FailureCategory.TOOL_SELECTION_ERROR)) == 1
    assert report.get_case_diagnostic("case_test_01") is not None

    md = report.to_markdown()
    assert "Failure Diagnostic Report" in md
    assert "tool_selection_error" in md
    assert "ToolAssignmentMutator" in md


def test_failure_analyzer_isolates_timeout_and_context_overflow():
    """Verify FailureAnalyzer isolates TIMEOUT_EXCEEDED and CONTEXT_OVERFLOW from symptoms."""
    analyzer = FailureAnalyzer()
    case = BenchmarkCase(
        case_id="case_timeout",
        input_data={},
        expected_output={"status": "reconciled"},
        split="optimization"
    )

    # 1. Timeout failure
    timeout_result = ExecutionResult(
        architecture_id="arch_timeout",
        task_goal="test",
        status=NodeStatus.FAILED,
        total_latency_ms=6500.0,  # exceeds 5000.0 budget
        error="Execution exceeded latency budget (6500.0ms > 5000.0ms)",
        node_records={
            "tool_node": NodeExecutionRecord(
                node_id="tool_node",
                node_type=NodeType.TOOL,
                status=NodeStatus.FAILED,
                error="Timeout expired",
                latency_ms=6500.0
            )
        }
    )
    diag_timeout = analyzer.analyze_case(case, timeout_result)
    assert diag_timeout is not None
    assert diag_timeout.category == FailureCategory.TIMEOUT_EXCEEDED
    assert diag_timeout.recommended_mutator == "RetryPolicyMutator"

    # 2. Context Overflow failure
    overflow_result = ExecutionResult(
        architecture_id="arch_overflow",
        task_goal="test",
        status=NodeStatus.FAILED,
        error="Context_overflow: Intermediate payload exceeded maximum context length (4096 tokens)",
        node_records={
            "reasoning_node": NodeExecutionRecord(
                node_id="reasoning_node",
                node_type=NodeType.REASONING,
                status=NodeStatus.FAILED,
                error="Context_overflow error"
            )
        }
    )
    diag_overflow = analyzer.analyze_case(case, overflow_result)
    assert diag_overflow is not None
    assert diag_overflow.category == FailureCategory.CONTEXT_OVERFLOW
    assert diag_overflow.recommended_mutator == "PromptMutator"


def test_failure_analyzer_tool_parameter_and_unhandled_exception():
    """Verify FailureAnalyzer distinguishes TOOL_PARAMETER_ERROR from UNHANDLED_EXCEPTION."""
    analyzer = FailureAnalyzer()
    case = BenchmarkCase(
        case_id="case_param",
        input_data={},
        expected_output={},
        split="optimization"
    )

    # 1. Tool parameter error
    param_result = ExecutionResult(
        architecture_id="arch_param",
        task_goal="test",
        status=NodeStatus.FAILED,
        error="Node 'tool_exact_reconcile' failed: Parameter validation failed: Missing required parameter 'target_records'",
        node_records={
            "tool_exact_reconcile": NodeExecutionRecord(
                node_id="tool_exact_reconcile",
                node_type=NodeType.TOOL,
                status=NodeStatus.FAILED,
                error="Parameter validation failed: Missing required parameter 'target_records'"
            ),
            "reasoning_node": NodeExecutionRecord(
                node_id="reasoning_node",
                node_type=NodeType.REASONING,
                status=NodeStatus.SKIPPED,
                error="Skipped due to upstream node failure"
            )
        }
    )
    diag_param = analyzer.analyze_case(case, param_result)
    assert diag_param is not None
    # Root cause must be TOOL_PARAMETER_ERROR, NOT intermediate symptom of skipped reasoning
    assert diag_param.category == FailureCategory.TOOL_PARAMETER_ERROR
    assert diag_param.target_node_id == "tool_exact_reconcile"
    assert diag_param.recommended_mutator == "PromptMutator"

    # 2. Unhandled Exception
    crash_result = ExecutionResult(
        architecture_id="arch_crash",
        task_goal="test",
        status=NodeStatus.FAILED,
        error="ZeroDivisionError: division by zero in analytical aggregator\nTraceback: line 42",
        node_records={}
    )
    diag_crash = analyzer.analyze_case(case, crash_result)
    assert diag_crash is not None
    assert diag_crash.category == FailureCategory.UNHANDLED_EXCEPTION
    assert diag_crash.recommended_mutator == "RetryPolicyMutator"


def test_failure_analyzer_retry_exhaustion_and_state_corruption():
    """Verify FailureAnalyzer classifies RETRY_EXHAUSTION and STATE_CORRUPTION."""
    analyzer = FailureAnalyzer()
    case = BenchmarkCase(case_id="case_test", input_data={}, expected_output={}, split="optimization")

    # 1. Retry Exhaustion
    retry_result = ExecutionResult(
        architecture_id="arch_retry",
        task_goal="test",
        status=NodeStatus.FAILED,
        error="Retry exhaustion (3 attempts failed): Connection refused",
        node_records={}
    )
    diag_retry = analyzer.analyze_case(case, retry_result)
    assert diag_retry is not None
    assert diag_retry.category == FailureCategory.RETRY_EXHAUSTION

    # 2. State Corruption
    state_result = ExecutionResult(
        architecture_id="arch_state",
        task_goal="test",
        status=NodeStatus.FAILED,
        error="State_corruption: KeyError: 'state_step_2' snapshot lost during transition",
        node_records={}
    )
    diag_state = analyzer.analyze_case(case, state_result)
    assert diag_state is not None
    assert diag_state.category == FailureCategory.STATE_CORRUPTION


def test_failure_analyzer_diagnoses_tool_selection_error_on_format_variations():
    """Verify FailureAnalyzer diagnoses TOOL_SELECTION_ERROR on format variation test case."""
    suite = get_reconciliation_benchmark_suite()
    case_6 = suite.get_case("reco_opt_006_format_variations")
    assert case_6 is not None

    registry = ToolRegistry.create_reconciliation_default()
    spec = GoalAnalyzer().analyze("Reconcile transactions and identify discrepancies")
    generator = ArchitectureGenerator(tool_registry=registry)
    arch = generator.generate(spec)

    runtime = AgentRuntime(tool_registry=registry)
    exec_result = runtime.execute(arch, case_6.input_data)

    # exact_reconcile runs cleanly, but output fails ground-truth match on format variations
    assert exec_result.status == NodeStatus.COMPLETED
    assert case_6.eval_match(exec_result.final_output) is False

    analyzer = FailureAnalyzer(tool_registry=registry)
    diag = analyzer.analyze_case(case_6, exec_result, architecture=arch)

    assert diag is not None
    assert diag.category == FailureCategory.TOOL_SELECTION_ERROR
    assert "exact_reconcile" in diag.root_cause
    assert "smart_reconcile" in diag.remedy_suggestion
    assert diag.recommended_mutator == "ToolAssignmentMutator"


def test_failure_analyzer_diagnoses_schema_violation():
    """Verify FailureAnalyzer classifies missing ground-truth keys as SCHEMA_VIOLATION."""
    analyzer = FailureAnalyzer()
    case = BenchmarkCase(
        case_id="case_schema",
        input_data={},
        expected_output={
            "matched_ids": ["TX1", "TX2"],
            "unmatched_source_ids": [],
            "unmatched_target_ids": [],
            "discrepancy_ids": [],
            "status": "reconciled"
        },
        split="optimization"
    )

    # Output produced, but missing matched_ids and status
    result = ExecutionResult(
        architecture_id="arch_schema",
        task_goal="test",
        status=NodeStatus.COMPLETED,
        final_output={"summary": "all done"},  # Missing domain keys
        node_records={
            "output_node": NodeExecutionRecord(
                node_id="output_node",
                node_type=NodeType.OUTPUT,
                status=NodeStatus.COMPLETED,
                output={"summary": "all done"}
            )
        }
    )

    diag = analyzer.analyze_case(case, result)
    assert diag is not None
    assert diag.category == FailureCategory.SCHEMA_VIOLATION
    assert diag.recommended_mutator == "PromptMutator"


def test_failure_analyzer_diagnoses_verification_miss():
    """Verify FailureAnalyzer classifies false-positive guardrails as VERIFICATION_MISS."""
    analyzer = FailureAnalyzer()
    case = BenchmarkCase(
        case_id="case_verif",
        input_data={},
        expected_output={"matched_ids": ["TX1"], "status": "reconciled"},
        split="optimization"
    )

    # Architecture has verifier_node, which reported verified=True, but actual output didn't match
    result = ExecutionResult(
        architecture_id="arch_verif",
        task_goal="test",
        status=NodeStatus.COMPLETED,
        final_output={"matched_ids": ["TX999"], "status": "reconciled"},
        node_records={
            "verifier_node": NodeExecutionRecord(
                node_id="verifier_node",
                node_type=NodeType.VERIFIER,
                status=NodeStatus.COMPLETED,
                output={"verified": True, "checks": []}
            )
        }
    )

    spec = GoalAnalyzer().analyze("Reconcile data")
    arch = ArchitectureGenerator().generate(spec)

    diag = analyzer.analyze_case(case, result, architecture=arch)
    assert diag is not None
    assert diag.category == FailureCategory.VERIFICATION_MISS
    assert diag.recommended_mutator == "VerifierNodeMutator"


def test_failure_analyzer_clean_run_returns_none():
    """Verify FailureAnalyzer returns None when a benchmark case passes completely."""
    suite = get_reconciliation_benchmark_suite()
    case_1 = suite.get_case("reco_opt_001_exact_match")
    assert case_1 is not None

    registry = ToolRegistry.create_reconciliation_default()
    spec = GoalAnalyzer().analyze("Reconcile transactions")
    arch = ArchitectureGenerator(tool_registry=registry).generate(spec)

    runtime = AgentRuntime(tool_registry=registry)
    exec_result = runtime.execute(arch, case_1.input_data)

    analyzer = FailureAnalyzer(tool_registry=registry)
    diag = analyzer.analyze_case(case_1, exec_result, architecture=arch)

    assert diag is None  # Zero failure on accurate pass


def test_diagnostic_report_from_scorecard():
    """Verify FailureAnalyzer creates full DiagnosticReport from Scorecard evaluation."""
    suite = get_reconciliation_benchmark_suite()
    registry = ToolRegistry.create_reconciliation_default()
    spec = GoalAnalyzer().analyze("Reconcile transactions")
    arch = ArchitectureGenerator(tool_registry=registry).generate(spec)

    evaluator = ScorecardEvaluator(runtime=AgentRuntime(tool_registry=registry))
    scorecard = evaluator.evaluate(arch, suite, split=BenchmarkSplit.OPTIMIZATION)

    analyzer = FailureAnalyzer(tool_registry=registry)
    report = analyzer.analyze_scorecard(scorecard, suite, arch)

    assert isinstance(report, DiagnosticReport)
    assert report.total_cases == 6
    assert report.failed_cases == 1  # reco_opt_006_format_variations
    assert report.passed_cases == 5
    assert report.has_category(FailureCategory.TOOL_SELECTION_ERROR)
    assert "tool_selection_error" in report.category_counts
    assert report.summary != ""
