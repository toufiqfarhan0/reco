"""Tests for the Reco persistence layer (Models, Repositories, In-Memory implementation)."""

import asyncio
from uuid import uuid4
import pytest

from reco.db.memory import InMemoryDatabase
from reco.db.models import (
    AgentVersionRecord,
    BenchmarkCaseRecord,
    BenchmarkRunRecord,
    CaseExecutionRecord,
    ExperimentRecord,
    FailureDiagnosisRecord,
    ImprovementRecord,
    ToolRecord,
)
from reco.db.supabase import get_supabase_client


@pytest.fixture
def db() -> InMemoryDatabase:
    """Provide a fresh isolated in-memory database for each test."""
    database = InMemoryDatabase()
    database.clear()
    return database


def test_experiment_crud(db: InMemoryDatabase):
    """Test 1, 2, 3: Create, retrieve, and update an experiment."""
    exp = ExperimentRecord(
        name="Reconciliation Tuning v1",
        goal="Reconcile bank statements against general ledger",
        status="running",
    )
    # Create
    created = asyncio.run(db.experiments.create(exp))
    assert created.id == exp.id
    assert created.name == "Reconciliation Tuning v1"
    assert created.status == "running"

    # Retrieve
    fetched = asyncio.run(db.experiments.get(exp.id))
    assert fetched is not None
    assert fetched.name == "Reconciliation Tuning v1"
    assert fetched.goal == "Reconcile bank statements against general ledger"

    # Update
    fetched.status = "completed"
    updated = asyncio.run(db.experiments.update(fetched))
    assert updated.status == "completed"

    all_exps = asyncio.run(db.experiments.list_all())
    assert len(all_exps) == 1


def test_agent_version_crud_and_uniqueness(db: InMemoryDatabase):
    """Test 4, 5, 6: Create, retrieve agent version, and enforce version uniqueness."""
    exp_id = uuid4()

    v0 = AgentVersionRecord(
        experiment_id=exp_id,
        version_number=0,
        architecture={"topology": "single_agent", "nodes": ["reconciler"]},
        prompts={"reconciler": "You are a financial reconciler."},
        tools=["parse_statement", "match_records"],
        status="evaluated",
    )
    created_v0 = asyncio.run(db.agent_versions.create(v0))
    assert created_v0.version_number == 0

    # Retrieve by ID and by version number
    fetched_v0 = asyncio.run(db.agent_versions.get(v0.id))
    assert fetched_v0 is not None
    assert fetched_v0.tools == ["parse_statement", "match_records"]

    by_num = asyncio.run(db.agent_versions.get_by_version_number(exp_id, 0))
    assert by_num is not None
    assert by_num.id == v0.id

    # Test 6: Enforce version uniqueness (experiment_id + version_number)
    duplicate_v0 = AgentVersionRecord(
        experiment_id=exp_id,
        version_number=0,
        architecture={"topology": "duplicate"},
    )
    with pytest.raises(ValueError, match="already exists"):
        asyncio.run(db.agent_versions.create(duplicate_v0))

    # Create v1 with parent reference
    v1 = AgentVersionRecord(
        experiment_id=exp_id,
        version_number=1,
        parent_version_id=v0.id,
        mutation_summary="Added verifier node to eliminate fee miscalculations",
        architecture={"topology": "verifier_loop"},
        status="promoted",
    )
    created_v1 = asyncio.run(db.agent_versions.create(v1))
    assert created_v1.version_number == 1
    assert created_v1.parent_version_id == v0.id

    # List versions for experiment
    versions = asyncio.run(db.agent_versions.list_for_experiment(exp_id))
    assert len(versions) == 2
    assert versions[0].version_number == 0
    assert versions[1].version_number == 1


def test_benchmark_cases_and_splits(db: InMemoryDatabase):
    """Test 7, 8: Create benchmark cases and distinguish optimization vs held_out."""
    case_opt = BenchmarkCaseRecord(
        case_code="REC-OPT-001",
        split="optimization",
        difficulty="easy",
        input_data={"statement_amount": 1000.0, "ledger_amount": 1000.0},
        ground_truth={"matched": True, "discrepancy": 0.0},
    )
    case_held = BenchmarkCaseRecord(
        case_code="REC-HELD-001",
        split="held_out",
        difficulty="hard",
        input_data={"statement_amount": 971.0, "ledger_amount": 1000.0, "fee": 29.0},
        ground_truth={"matched": True, "fee_detected": 29.0},
    )

    asyncio.run(db.benchmark_cases.create(case_opt))
    asyncio.run(db.benchmark_cases.create(case_held))

    # Duplicate case code check
    with pytest.raises(ValueError, match="already exists"):
        asyncio.run(db.benchmark_cases.create(case_opt))

    # Test 8: Filter by split
    opt_cases = asyncio.run(db.benchmark_cases.list_by_split("reconciliation", "optimization"))
    assert len(opt_cases) == 1
    assert opt_cases[0].case_code == "REC-OPT-001"

    held_cases = asyncio.run(db.benchmark_cases.list_by_split("reconciliation", "held_out"))
    assert len(held_cases) == 1
    assert held_cases[0].case_code == "REC-HELD-001"


def test_benchmark_run_and_case_execution(db: InMemoryDatabase):
    """Test 9, 10: Create benchmark run and store case execution logs."""
    exp_id = uuid4()
    version_id = uuid4()
    case_id = uuid4()

    run = BenchmarkRunRecord(
        experiment_id=exp_id,
        agent_version_id=version_id,
        split="optimization",
        total_cases=10,
        passed_cases=8,
        failed_cases=2,
        accuracy=0.80,
        reliability=1.0,
        total_cost_usd=0.0045,
        latency_ms=1850,
        status="completed",
    )
    created_run = asyncio.run(db.benchmark_runs.create(run))
    assert created_run.accuracy == 0.80

    # Test 10: Store case execution
    exec_record = CaseExecutionRecord(
        benchmark_run_id=run.id,
        benchmark_case_id=case_id,
        agent_version_id=version_id,
        output={"matched": True, "fee": 29.0},
        expected={"matched": True, "fee": 29.0},
        success=True,
        accuracy_score=1.0,
        latency_ms=210,
        input_tokens=150,
        output_tokens=45,
        cost_usd=0.0004,
        tool_events=[{"tool": "parse_statement", "duration_ms": 15}],
        trace_id="trace-rec-001",
    )
    created_exec = asyncio.run(db.case_executions.create(exec_record))
    assert created_exec.success is True
    assert created_exec.cost_usd == 0.0004

    executions = asyncio.run(db.case_executions.list_for_run(run.id))
    assert len(executions) == 1
    assert executions[0].id == exec_record.id


def test_failure_diagnosis(db: InMemoryDatabase):
    """Test 11: Create and retrieve failure diagnosis."""
    exec_id = uuid4()
    diagnosis = FailureDiagnosisRecord(
        case_execution_id=exec_id,
        category="ARITHMETIC_MISMATCH",
        severity="high",
        root_cause="Agent failed to account for 2.9% Stripe merchant processing fee",
        evidence={"expected_fee": 29.0, "actual_fee": 0.0},
        recommended_mutations=[
            {"type": "prompt_refinement", "axis": "prompts", "note": "Add fee awareness instruction"},
            {"type": "tool_binding", "axis": "tools", "note": "Bind calculate_processing_fee tool"},
        ],
    )
    created = asyncio.run(db.failure_diagnoses.create(diagnosis))
    assert created.category == "ARITHMETIC_MISMATCH"
    assert created.severity == "high"

    fetched = asyncio.run(db.failure_diagnoses.get_for_case_execution(exec_id))
    assert fetched is not None
    assert len(fetched.recommended_mutations) == 2


def test_improvement_lineage(db: InMemoryDatabase):
    """Test 12: Track improvement mutation lineage and comparison metrics."""
    exp_id = uuid4()
    parent_id = uuid4()
    candidate_id = uuid4()

    improvement = ImprovementRecord(
        experiment_id=exp_id,
        parent_version_id=parent_id,
        candidate_version_id=candidate_id,
        mutation_type="add_verifier_node",
        mutation_description="Inserted secondary audit node to verify fee arithmetic",
        rationale="Eliminates ARITHMETIC_MISMATCH failures observed on Stripe test cases",
        metrics_before={"accuracy": 0.75, "cost_usd": 0.003},
        metrics_after={"accuracy": 0.95, "cost_usd": 0.004},
        accepted=True,
    )
    created = asyncio.run(db.improvements.create(improvement))
    assert created.accepted is True
    assert created.metrics_after["accuracy"] == 0.95

    improvements = asyncio.run(db.improvements.list_for_experiment(exp_id))
    assert len(improvements) == 1
    assert improvements[0].mutation_type == "add_verifier_node"


def test_tool_catalog(db: InMemoryDatabase):
    """Verify tool repository operations and uniqueness."""
    tool = ToolRecord(
        name="calculate_reconciliation_difference",
        description="Calculates differences between bank and ledger amounts",
        parameters_schema={"type": "object", "properties": {"bank": {"type": "number"}, "ledger": {"type": "number"}}},
        enabled=True,
    )
    created = asyncio.run(db.tools.create(tool))
    assert created.name == "calculate_reconciliation_difference"

    # Name uniqueness
    with pytest.raises(ValueError, match="already exists"):
        asyncio.run(db.tools.create(tool))

    active_tools = asyncio.run(db.tools.list_active())
    assert len(active_tools) == 1


def test_repository_isolation_between_tests(db: InMemoryDatabase):
    """Test 13: Verify repository isolation (clean empty state for new fixture)."""
    exps = asyncio.run(db.experiments.list_all())
    assert len(exps) == 0


def test_supabase_unconfigured_error():
    """Verify Supabase client raises explicit error when unconfigured."""
    from reco.config import Settings
    unconfigured_settings = Settings(supabase_url="", supabase_key="")
    with pytest.raises(RuntimeError, match="Supabase credentials missing"):
        get_supabase_client(settings=unconfigured_settings)
