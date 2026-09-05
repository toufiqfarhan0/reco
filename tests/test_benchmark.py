"""Comprehensive test suite for Partitioned Benchmark Harness and Dataset isolation."""

import pytest
from reco.benchmarks.base import BenchmarkCase, BenchmarkSplit, BenchmarkSuite
from reco.benchmarks.reconciliation.dataset import (
    create_reconciliation_benchmark_cases,
    get_reconciliation_benchmark_suite,
)
from reco.core.goal_analyzer import GoalAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import NodeStatus
from reco.engine.runtime import AgentRuntime
from reco.tools.registry import ToolRegistry


def test_benchmark_case_structure_and_normalization():
    """Verify BenchmarkCase validation, deterministic ID, and split normalization."""
    # Test valid optimization case
    case_opt = BenchmarkCase(
        case_id="case_opt_test_01",
        name="Test Opt Case",
        description="Testing optimization split initialization",
        category="exact_match",
        input_data={"source_records": [], "target_records": []},
        expected_output={"matched_ids": []},
        split="optimization"
    )
    assert case_opt.case_id == "case_opt_test_01"
    assert case_opt.split == BenchmarkSplit.OPTIMIZATION

    # Test held-out normalization (handles underscore and hyphen)
    case_held = BenchmarkCase(
        case_id="case_held_test_01",
        input_data={},
        expected_output={},
        split="held_out"
    )
    assert case_held.split == BenchmarkSplit.HELD_OUT

    # Test invalid split
    with pytest.raises(ValueError, match="Invalid split"):
        BenchmarkCase(
            case_id="invalid_split_case",
            input_data={},
            expected_output={},
            split="training_dev"
        )


def test_reconciliation_dataset_case_count_and_categories():
    """Verify dataset contains >=10 cases covering all required reconciliation phenomena."""
    suite = get_reconciliation_benchmark_suite()

    # Total cases >= 10
    assert len(suite) >= 10

    # Ensure all required phenomena are covered
    categories = {case.category for case in suite}
    assert "exact_match" in categories
    assert "missing_records" in categories
    assert "amount_mismatch" in categories
    assert "duplicate_records" in categories
    assert "format_variation" in categories


def test_strict_partition_isolation_and_zero_leakage():
    """Verify strictly partitioned 6 optimization and 4 held-out cases with zero leakage."""
    suite = get_reconciliation_benchmark_suite()

    opt_cases = suite.get_optimization_cases()
    held_cases = suite.get_held_out_cases()

    # Strict count requirement: 6 optimization, 4 held-out
    assert len(opt_cases) == 6, f"Expected 6 optimization cases, got {len(opt_cases)}"
    assert len(held_cases) == 4, f"Expected 4 held-out cases, got {len(held_cases)}"

    opt_ids = {c.case_id for c in opt_cases}
    held_ids = {c.case_id for c in held_cases}

    # Air-gapped separation: zero cross-split leakage
    assert opt_ids.isdisjoint(held_ids), f"Cross-split leakage detected: {opt_ids & held_ids}"
    assert len(opt_ids) == 6
    assert len(held_ids) == 4

    # Formal partition isolation validation passes
    assert suite.validate_partition_isolation() is True


def test_partition_isolation_violation_detection():
    """Verify suite validator actively catches leakage, empty partitions, and duplicates."""
    # 1. Test cross-split leakage detection
    leaking_suite = BenchmarkSuite(
        name="leaking_suite",
        cases=[
            BenchmarkCase(
                case_id="shared_id_001",
                input_data={},
                expected_output={},
                split=BenchmarkSplit.OPTIMIZATION
            ),
            BenchmarkCase(
                case_id="shared_id_001",  # Same ID in held-out
                input_data={},
                expected_output={},
                split=BenchmarkSplit.HELD_OUT
            )
        ]
    )
    with pytest.raises(ValueError, match="Cross-split leakage"):
        leaking_suite.validate_partition_isolation()

    # 2. Test empty partition detection
    empty_held_suite = BenchmarkSuite(
        name="empty_held",
        cases=[
            BenchmarkCase(
                case_id="opt_only",
                input_data={},
                expected_output={},
                split=BenchmarkSplit.OPTIMIZATION
            )
        ]
    )
    with pytest.raises(ValueError, match="Held-out partition cannot be empty"):
        empty_held_suite.validate_partition_isolation()

    # 3. Test duplicate addition to suite
    clean_suite = BenchmarkSuite(name="clean")
    c1 = BenchmarkCase(case_id="id_1", input_data={}, expected_output={}, split="opt")
    clean_suite.add_case(c1)
    with pytest.raises(ValueError, match="Duplicate case_id"):
        clean_suite.add_case(c1)


def test_case_ground_truth_assertion_matching():
    """Verify BenchmarkCase eval_match handles exact equality, sets of IDs, and nested keys."""
    case = BenchmarkCase(
        case_id="eval_test",
        input_data={},
        expected_output={
            "matched_ids": ["TX101", "TX102"],
            "unmatched_source_ids": ["TX103"],
            "status": "discrepancy_detected",
            "matched_count": 2
        },
        split=BenchmarkSplit.OPTIMIZATION
    )

    # 1. Exact match (order-independent list of IDs)
    assert case.eval_match({
        "matched_ids": ["TX102", "TX101"],  # reversed order
        "unmatched_source_ids": ["TX103"],
        "status": "discrepancy_detected",
        "matched_count": 2
    }) is True

    # 2. Nested under reconciliation wrapper
    assert case.eval_match({
        "reconciliation": {
            "matched_ids": ["TX101", "TX102"],
            "unmatched_source_ids": ["TX103"],
            "status": "discrepancy_detected",
            "matched_count": 2
        }
    }) is True

    # 3. Missing key fails
    assert case.eval_match({
        "matched_ids": ["TX101", "TX102"],
        "status": "discrepancy_detected"
    }) is False

    # 4. Value mismatch fails
    assert case.eval_match({
        "matched_ids": ["TX101", "TX999"],  # wrong ID
        "unmatched_source_ids": ["TX103"],
        "status": "discrepancy_detected",
        "matched_count": 2
    }) is False

    # 5. None payload fails
    assert case.eval_match(None) is False


def test_end_to_end_benchmark_case_execution():
    """Verify running a benchmark case through AgentRuntime with reconciliation tool."""
    suite = get_reconciliation_benchmark_suite()
    case = suite.get_case("reco_opt_001_exact_match")
    assert case is not None

    registry = ToolRegistry.create_reconciliation_default()
    analyzer = GoalAnalyzer()
    spec = analyzer.analyze("Reconcile financial ledger transactions")

    generator = ArchitectureGenerator(tool_registry=registry)
    arch = generator.generate(spec)

    runtime = AgentRuntime(tool_registry=registry)
    result = runtime.execute(arch, case.input_data)

    assert result.status == NodeStatus.COMPLETED
    assert result.error is None
    assert result.total_latency_ms > 0.0

    # Ground truth matching succeeds for exact match case
    assert case.eval_match(result.final_output) is True
