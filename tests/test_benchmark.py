"""Comprehensive deterministic test suite for Milestone 7: Reconciliation Benchmark Harness.

Covers all 35 milestone test requirements across Dataset, Ground Truth, Benchmark Engine,
Metrics, Persistence, Baseline Agent, and Internal API.
"""

import asyncio
from decimal import Decimal
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from reco.api.app import app
from reco.benchmarks.reconciliation import (
    BENCHMARK_NAME,
    BENCHMARK_VERSION,
    CaseEvaluationResult,
    ExpectedMatchPair,
    ReconciliationBenchmark,
    ReconciliationCase,
    ReconciliationEvaluator,
    ReconciliationGroundTruth,
    ReconciliationRunResult,
    create_reconciliation_baseline_graph,
    get_case_by_code,
    get_held_out_cases,
    get_optimization_cases,
    load_cases,
)
from reco.db.memory import (
    InMemoryBenchmarkCaseRepository,
    InMemoryBenchmarkRunRepository,
    InMemoryCaseExecutionRepository,
)
from reco.engine.models import EdgeModel, GraphDefinition, NodeModel
from reco.engine.runtime import AgentGraphRuntime
from reco.engine.state import ExecutionState
from reco.llm.mock import MockModelGateway
from reco.tools.executor import ToolExecutor
from reco.tools.reconciliation import register_reconciliation_tools
from reco.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def evaluator() -> ReconciliationEvaluator:
    return ReconciliationEvaluator()


@pytest.fixture
def runtime() -> AgentGraphRuntime:
    reg = ToolRegistry()
    register_reconciliation_tools(reg)
    executor = ToolExecutor(registry=reg)
    gateway = MockModelGateway(
        default_content="Verification confirmed matching results without discrepancies."
    )
    return AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)


@pytest.fixture
def benchmark(runtime: AgentGraphRuntime, evaluator: ReconciliationEvaluator) -> ReconciliationBenchmark:
    return ReconciliationBenchmark(runtime=runtime, evaluator=evaluator)


# ---------------------------------------------------------------------------
# PART 1: DATASET TESTS (1 - 7)
# ---------------------------------------------------------------------------

def test_1_exactly_20_cases():
    """Requirement 1: Dataset contains exactly 20 canonical cases."""
    all_cases = load_cases()
    assert len(all_cases) == 20
    assert len(load_cases("full")) == 20


def test_2_stable_case_codes():
    """Requirement 2: Every case has a stable, deterministic case code."""
    cases = load_cases()
    codes = [c.case_code for c in cases]
    assert len(codes) == len(set(codes)), "Case codes must be unique"

    # Verify standard code conventions
    for i in range(1, 13):
        assert f"REC-OPT-{i:02d}" in codes
    for i in range(1, 9):
        assert f"REC-HLD-{i:02d}" in codes


def test_3_optimization_split_size():
    """Requirement 3: Optimization split contains exactly 12 cases."""
    opt_cases = load_cases("optimization")
    assert len(opt_cases) == 12
    assert all(c.split == "optimization" for c in opt_cases)
    assert all(c.case_code.startswith("REC-OPT-") for c in opt_cases)


def test_4_held_out_split_size():
    """Requirement 4: Held-out split contains exactly 8 cases."""
    hld_cases = load_cases("held_out")
    assert len(hld_cases) == 8
    assert all(c.split == "held_out" for c in hld_cases)
    assert all(c.case_code.startswith("REC-HLD-") for c in hld_cases)


def test_5_all_exception_categories_represented():
    """Requirement 5: Coverage includes all 11 required exception categories."""
    cases = load_cases()
    exceptions = {c.exception_class for c in cases}
    required = {
        "exact_match",
        "near_match",
        "processing_fee",
        "timing_difference",
        "duplicate",
        "missing_transaction",
        "wrong_vendor",
        "wrong_amount",
        "transposition",
        "fx_difference",
        "compound_exception",
    }
    assert required.issubset(exceptions), f"Missing required exception classes: {required - exceptions}"


def test_6_difficulty_distribution():
    """Requirement 6: Cases have varying difficulty (easy, medium, hard)."""
    cases = load_cases()
    difficulties = {c.difficulty for c in cases}
    assert difficulties == {"easy", "medium", "hard"}

    easy_count = sum(1 for c in cases if c.difficulty == "easy")
    med_count = sum(1 for c in cases if c.difficulty == "medium")
    hard_count = sum(1 for c in cases if c.difficulty == "hard")

    assert easy_count >= 4
    assert med_count >= 6
    assert hard_count >= 4


def test_7_deterministic_case_loading():
    """Requirement 7: Case loading is deterministic and validates split parameter."""
    run1 = load_cases("optimization")
    run2 = load_cases("optimization")
    assert [c.case_code for c in run1] == [c.case_code for c in run2]
    assert run1[0].bank_records == run2[0].bank_records

    with pytest.raises(ValueError, match="Unknown benchmark split"):
        load_cases("invalid_split")


# ---------------------------------------------------------------------------
# PART 2: GROUND TRUTH TESTS (8 - 16)
# ---------------------------------------------------------------------------

def test_8_exact_match_ground_truth():
    """Requirement 8: Exact match ground truth specifies zero discrepancy and exact match."""
    case = get_case_by_code("REC-OPT-01")
    assert case is not None
    assert case.ground_truth.primary_exception == "exact_match"
    assert case.ground_truth.total_discrepancy == Decimal("0.00")
    assert len(case.ground_truth.expected_pairs) == 1
    pair = case.ground_truth.expected_pairs[0]
    assert pair.match_type == "exact_match"
    assert pair.amount_discrepancy == Decimal("0.00")


def test_9_fee_case_ground_truth():
    """Requirement 9: Processing fee ground truth reflects gross/net difference."""
    case = get_case_by_code("REC-OPT-03")
    assert case is not None
    assert case.ground_truth.primary_exception == "processing_fee"
    assert case.ground_truth.total_discrepancy == Decimal("29.00")
    assert case.ground_truth.expected_pairs[0].match_type == "processing_fee"


def test_10_timing_case_ground_truth():
    """Requirement 10: Timing difference ground truth records timing lag with zero discrepancy."""
    case = get_case_by_code("REC-OPT-04")
    assert case is not None
    assert case.ground_truth.primary_exception == "timing_difference"
    assert case.ground_truth.total_discrepancy == Decimal("0.00")
    assert case.ground_truth.expected_pairs[0].match_type == "timing_difference"


def test_11_duplicate_ground_truth():
    """Requirement 11: Duplicate ground truth flags multiple records matching single counter-entry."""
    case = get_case_by_code("REC-OPT-05")
    assert case is not None
    assert case.ground_truth.primary_exception == "duplicate"
    assert len(case.ground_truth.expected_pairs) == 2
    assert all(p.match_type == "duplicate" for p in case.ground_truth.expected_pairs)


def test_12_missing_transaction_ground_truth():
    """Requirement 12: Missing transaction ground truth identifies unmatched bank/ledger entries."""
    case_in_bank = get_case_by_code("REC-OPT-06")  # Missing in ledger
    assert case_in_bank is not None
    assert "TX-OPT-602" in case_in_bank.ground_truth.unmatched_bank_ids
    assert case_in_bank.ground_truth.total_discrepancy == Decimal("35.00")

    case_in_ledger = get_case_by_code("REC-OPT-07")  # Missing in bank
    assert case_in_ledger is not None
    assert "GL-OPT-702" in case_in_ledger.ground_truth.unmatched_ledger_ids
    assert case_in_ledger.ground_truth.total_discrepancy == Decimal("600.00")


def test_13_wrong_vendor_ground_truth():
    """Requirement 13: Wrong vendor ground truth specifies empty expected pairs to prevent false match."""
    case = get_case_by_code("REC-OPT-08")
    assert case is not None
    assert case.ground_truth.primary_exception == "wrong_vendor"
    assert len(case.ground_truth.expected_pairs) == 0
    assert "TX-OPT-801" in case.ground_truth.unmatched_bank_ids
    assert "GL-OPT-801" in case.ground_truth.unmatched_ledger_ids


def test_14_fx_ground_truth():
    """Requirement 14: FX difference ground truth records currency variance."""
    case = get_case_by_code("REC-OPT-11")
    assert case is not None
    assert case.ground_truth.primary_exception == "fx_difference"
    assert case.ground_truth.total_discrepancy == Decimal("85.00")
    assert case.ground_truth.expected_pairs[0].match_type == "fx_difference"


def test_15_transposition_ground_truth():
    """Requirement 15: Transposition ground truth confirms variance divisible by 9."""
    case = get_case_by_code("REC-OPT-10")
    assert case is not None
    assert case.ground_truth.primary_exception == "transposition"
    assert case.ground_truth.total_discrepancy == Decimal("90.00")
    assert int(case.ground_truth.total_discrepancy) % 9 == 0


def test_16_compound_exception_ground_truth():
    """Requirement 16: Compound exception ground truth reflects multi-factor conditions."""
    case = get_case_by_code("REC-OPT-12")
    assert case is not None
    assert case.ground_truth.primary_exception == "compound_exception"
    assert case.ground_truth.total_discrepancy == Decimal("58.00")
    assert case.ground_truth.expected_pairs[0].match_type == "compound_exception"


# ---------------------------------------------------------------------------
# PART 3: BENCHMARK HARNESS & SPLIT ISOLATION (17 - 23)
# ---------------------------------------------------------------------------

def test_17_load_optimization_split():
    """Requirement 17: Explicit loading of optimization split."""
    cases = get_optimization_cases()
    assert len(cases) == 12
    assert all(c.split == "optimization" for c in cases)


def test_18_load_held_out_split():
    """Requirement 18: Explicit loading of held-out split."""
    cases = get_held_out_cases()
    assert len(cases) == 8
    assert all(c.split == "held_out" for c in cases)


def test_19_split_isolation():
    """Requirement 19: Strict isolation between optimization and held-out splits."""
    opt_codes = {c.case_code for c in get_optimization_cases()}
    hld_codes = {c.case_code for c in get_held_out_cases()}

    # Zero overlap
    assert len(opt_codes & hld_codes) == 0
    assert len(opt_codes) == 12
    assert len(hld_codes) == 8


def test_20_deterministic_ordering():
    """Requirement 20: Stable case execution ordering."""
    order1 = [c.case_code for c in load_cases("optimization")]
    order2 = [c.case_code for c in load_cases("optimization")]
    assert order1 == order2


def test_21_benchmark_executes_through_runtime(benchmark: ReconciliationBenchmark):
    """Requirement 21: Benchmark executes graphs through AgentGraphRuntime."""
    graph = create_reconciliation_baseline_graph()
    result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))

    assert isinstance(result, ReconciliationRunResult)
    assert result.split == "optimization"
    assert result.total_cases == 12
    assert len(result.case_results) == 12


def test_22_case_level_result_generated(benchmark: ReconciliationBenchmark):
    """Requirement 22: Each case produces a detailed CaseEvaluationResult for failure analysis."""
    graph = create_reconciliation_baseline_graph()
    result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))

    case_0 = result.case_results[0]
    assert isinstance(case_0, CaseEvaluationResult)
    assert case_0.case_code == "REC-OPT-01"
    assert case_0.latency_ms >= 0
    assert "matched_pairs" in case_0.actual_outcome
    assert len(case_0.tool_events) >= 3


def test_23_aggregate_result_generated(benchmark: ReconciliationBenchmark):
    """Requirement 23: Aggregate result produces all required high-level metrics."""
    graph = create_reconciliation_baseline_graph()
    result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))

    assert result.total_cases == 12
    assert result.passed_cases + result.failed_cases == 12
    assert 0.0 <= result.accuracy <= 1.0
    assert 0.0 <= result.reliability <= 1.0
    assert result.total_latency_ms >= 0
    assert result.avg_latency_ms >= 0


# ---------------------------------------------------------------------------
# PART 4: METRICS & SCORING (24 - 28)
# ---------------------------------------------------------------------------

def test_24_accuracy_calculation(evaluator: ReconciliationEvaluator):
    """Requirement 24: Accuracy calculates correctly using the multi-factor formula."""
    # Perfect match test
    ground_truth = {
        "expected_pairs": [
            {
                "bank_transaction_id": "TX-1",
                "ledger_entry_id": "GL-1",
                "match_type": "exact_match",
                "amount_discrepancy": "0.00",
            }
        ],
        "unmatched_bank_ids": [],
        "unmatched_ledger_ids": [],
        "primary_exception": "exact_match",
    }
    actual_output = {
        "matched_pairs": [
            {
                "bank_transaction_id": "TX-1",
                "ledger_entry_id": "GL-1",
                "match_type": "exact_match",
                "amount_discrepancy": "0.00",
            }
        ],
        "unmatched_bank_ids": [],
        "unmatched_ledger_ids": [],
        "exceptions_by_type": {"exact_match": 1},
    }

    res = evaluator.evaluate(actual_output, ground_truth)
    assert res.accuracy == 1.0
    assert res.reliability == 1.0
    assert res.passed is True


def test_25_reliability_calculation(evaluator: ReconciliationEvaluator):
    """Requirement 25: Reliability evaluates schema presence and execution completion."""
    # Missing required reconciliation schema
    malformed_output = {"error": "Pipeline crashed"}
    ground_truth = {"expected_pairs": []}

    res = evaluator.evaluate(malformed_output, ground_truth)
    assert res.reliability == 0.0
    assert res.passed is False


def test_26_cost_calculation(benchmark: ReconciliationBenchmark):
    """Requirement 26: Sums execution cost and marks mock costs accurately."""
    graph = create_reconciliation_baseline_graph()
    result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))

    assert result.total_cost_usd >= 0.0
    assert result.metadata.get("cost_type") == "simulated_mock"


def test_27_latency_calculation(benchmark: ReconciliationBenchmark):
    """Requirement 27: Measures wall-clock execution duration in milliseconds."""
    graph = create_reconciliation_baseline_graph()
    result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))

    assert result.total_latency_ms >= 0
    assert result.avg_latency_ms >= 0
    assert result.total_latency_ms >= result.avg_latency_ms


def test_28_reconciliation_scoring_formula(evaluator: ReconciliationEvaluator):
    """Requirement 28: Verifies 0.40 match + 0.40 exception + 0.20 discrepancy scoring."""
    # Ground truth: processing fee with $29 discrepancy
    gt = {
        "expected_pairs": [
            {
                "bank_transaction_id": "TX-1",
                "ledger_entry_id": "GL-1",
                "match_type": "processing_fee",
                "amount_discrepancy": "29.00",
            }
        ],
        "unmatched_bank_ids": [],
        "unmatched_ledger_ids": [],
        "primary_exception": "processing_fee",
    }
    # Actual: correct pair, correct discrepancy, but misclassified as near_match
    actual = {
        "matched_pairs": [
            {
                "bank_transaction_id": "TX-1",
                "ledger_entry_id": "GL-1",
                "match_type": "near_match",  # Wrong type
                "amount_discrepancy": "29.00",  # Correct discrepancy
            }
        ],
        "unmatched_bank_ids": [],
        "unmatched_ledger_ids": [],
        "exceptions_by_type": {"near_match": 1},
    }

    res = evaluator.evaluate(actual, gt)
    # Match score: 1.0 (weight 0.40 = 0.40)
    # Exception score: 0.0 (weight 0.40 = 0.00)
    # Discrepancy score: 1.0 (weight 0.20 = 0.20)
    # Expected accuracy: 0.60
    assert res.accuracy == 0.60
    assert res.passed is False  # Fails 0.80 threshold


# ---------------------------------------------------------------------------
# PART 5: PERSISTENCE (29 - 32)
# ---------------------------------------------------------------------------

def test_29_30_31_benchmark_persistence_in_memory(runtime: AgentGraphRuntime):
    """Requirements 29, 30, 31: Persists benchmark runs and case executions with in-memory repos."""
    run_repo = InMemoryBenchmarkRunRepository()
    case_repo = InMemoryCaseExecutionRepository()
    bench_case_repo = InMemoryBenchmarkCaseRepository()

    benchmark = ReconciliationBenchmark(
        runtime=runtime,
        benchmark_run_repo=run_repo,
        case_execution_repo=case_repo,
        benchmark_case_repo=bench_case_repo,
    )

    graph = create_reconciliation_baseline_graph()
    exp_id = uuid4()
    ver_id = uuid4()

    result = asyncio.run(benchmark.run_benchmark(
        graph=graph,
        split="optimization",
        experiment_id=exp_id,
        agent_version_id=ver_id,
        persist=True,
    ))

    # Verify run repository persistence
    runs = asyncio.run(run_repo.list_for_experiment(exp_id))
    assert len(runs) == 1
    assert runs[0].total_cases == 12
    assert runs[0].accuracy == result.accuracy

    # Verify case execution repository persistence
    case_execs = asyncio.run(case_repo.list_for_run(runs[0].id))
    assert len(case_execs) == 12
    assert all(c.agent_version_id == ver_id for c in case_execs)


def test_32_disabled_persistence_permits_execution(runtime: AgentGraphRuntime):
    """Requirement 32: Disabling persistence still permits flawless benchmark execution."""
    benchmark = ReconciliationBenchmark(
        runtime=runtime,
        benchmark_run_repo=None,
        case_execution_repo=None,
    )
    graph = create_reconciliation_baseline_graph()
    result = asyncio.run(benchmark.run_benchmark(graph=graph, split="held_out", persist=False))

    assert result.total_cases == 8
    assert result.split == "held_out"


# ---------------------------------------------------------------------------
# PART 6: BASELINE AGENT (33 - 35)
# ---------------------------------------------------------------------------

def test_33_baseline_graph_structure():
    """Requirement 33: Manual baseline graph has valid topological DAG structure."""
    graph = create_reconciliation_baseline_graph()
    graph.validate_graph()
    nodes = graph.get_topological_order()
    assert len(nodes) == 4
    assert nodes[0].node_id == "parse_statement"
    assert nodes[-1].node_id == "verify_summary"


def test_34_baseline_produces_benchmark_metrics(benchmark: ReconciliationBenchmark):
    """Requirement 34: Baseline architecture produces benchmark metrics across cases."""
    graph = create_reconciliation_baseline_graph()
    result = asyncio.run(benchmark.run_benchmark(graph=graph, split="optimization", persist=False))

    assert result.accuracy > 0.50
    assert result.reliability == 1.0
    assert result.passed_cases > 0


def test_35_baseline_marked_correctly():
    """Requirement 35: Baseline is explicitly tagged with generation_method = 'manual_baseline'."""
    graph = create_reconciliation_baseline_graph()
    assert graph.metadata.get("generation_method") == "manual_baseline"
    assert graph.metadata.get("version") == "v0"


# ---------------------------------------------------------------------------
# PART 7: API ENDPOINT TESTS (36 - 38)
# ---------------------------------------------------------------------------

def test_36_api_benchmark_run_default_baseline():
    """Requirement 36: POST /benchmark/reconciliation/run runs baseline by default."""
    client = TestClient(app)
    response = client.post(
        "/benchmark/reconciliation/run",
        json={"split": "held_out", "benchmark_version": "reconciliation-v1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["benchmark_name"] == "reconciliation"
    assert data["split"] == "held_out"
    assert data["total_cases"] == 8
    assert data["generation_method"] == "manual_baseline"


def test_37_api_benchmark_invalid_version():
    """Requirement 37: POST /benchmark/reconciliation/run rejects invalid benchmark version."""
    client = TestClient(app)
    response = client.post(
        "/benchmark/reconciliation/run",
        json={"split": "optimization", "benchmark_version": "invalid-version"},
    )
    assert response.status_code == 400
    assert "Unsupported benchmark version" in response.json()["detail"]


def test_38_api_benchmark_invalid_split():
    """Requirement 38: POST /benchmark/reconciliation/run rejects invalid split."""
    client = TestClient(app)
    response = client.post(
        "/benchmark/reconciliation/run",
        json={"split": "invalid_split", "benchmark_version": "reconciliation-v1"},
    )
    assert response.status_code == 400
    assert "Invalid split" in response.json()["detail"]
