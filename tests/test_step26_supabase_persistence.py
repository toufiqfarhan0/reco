"""Tests for Supabase PostgreSQL Persistence, GoTrue Authentication, and RLS Isolation (Step 6).

Verifies:
1. Schema migration file (supabase/migrations/001_initial_schema.sql) with 6 core tables,
   Row-Level Security (RLS), and immutability policies.
2. Graceful fallback: Default to in-memory repository when running in local development
   mode without cloud credentials or with unconfigured placeholders.
3. Supabase repository initialization with credentials / client injection.
4. Experiment lineage and immutable architecture definitions.
5. Historical immutability: past generation benchmarks, evaluations, and mutations cannot be overwritten.
6. Neatlogs trace persistence with deep-link URLs and span telemetry.
7. GoTrue JWT authentication (Authorization: Bearer <token>) and UserContext extraction.
8. Multi-tenant user isolation: cross-tenant access is strictly denied.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from reco.core.goal_analyzer import GoalAnalyzer
from reco.db.auth import GoTrueAuthHandler, UserContext
from reco.db.models import (
    ArchitectureRecord,
    AuthenticationError,
    BenchmarkRunRecord,
    EvaluationRecord,
    ExperimentRecord,
    ImmutabilityError,
    MutationRecord,
    TraceRecord,
    UserIsolationError,
)
from reco.db.repository import ExperimentRepository, InMemoryRepository
from reco.db.supabase import SupabaseRepository, get_repository
from reco.engine.generator import ArchitectureGenerator
from reco.evaluators.scorecard import CaseEvaluationResult, Scorecard, ScorecardComparison
from reco.mutation.engine import MutationResult
from reco.mutation.validator import CandidateDiff
from reco.observability.tracer import NeatlogsSpan, NeatlogsTrace


# ==============================================================================
# 1. SQL Schema Migration Verification
# ==============================================================================

def test_sql_migration_file_structure_and_tables():
    """Verify supabase/migrations/001_initial_schema.sql contains all required tables, RLS, and immutability policies."""
    migration_path = Path("supabase/migrations/001_initial_schema.sql")
    assert migration_path.exists(), f"Migration file missing at {migration_path}"

    sql_content = migration_path.read_text(encoding="utf-8")

    # 1. Verify all 6 required tables are defined
    required_tables = [
        "experiments",
        "architectures",
        "benchmark_runs",
        "evaluations",
        "mutations",
        "traces",
    ]
    for table in required_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql_content or f"CREATE TABLE {table}" in sql_content, (
            f"Table '{table}' not found in migration SQL"
        )

    # 2. Verify Row-Level Security (RLS) enabled on all 6 tables
    for table in required_tables:
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;" in sql_content, (
            f"RLS not enabled for table '{table}'"
        )

    # 3. Verify user isolation policies using auth.uid() = user_id
    assert "auth.uid() = user_id" in sql_content

    # 4. Verify immutability policy (denying updates on historical records)
    assert "Deny updates on benchmark runs to preserve historical immutability" in sql_content
    assert "Deny updates on evaluations to preserve historical immutability" in sql_content
    assert "Deny updates on mutations to preserve historical immutability" in sql_content


# ==============================================================================
# 2. Repository Factory & Graceful Fallback
# ==============================================================================

def test_repository_factory_graceful_fallback_without_credentials():
    """Verify factory defaults to InMemoryRepository when environment variables are unset."""
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("SUPABASE_URL", raising=False)
        mp.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
        mp.delenv("SUPABASE_KEY", raising=False)

        repo = get_repository()
        assert isinstance(repo, InMemoryRepository)


def test_repository_factory_graceful_fallback_with_placeholder_credentials():
    """Verify factory defaults to InMemoryRepository when placeholders from .env.example are detected."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SUPABASE_URL", "https://your-project.supabase.co")
        mp.setenv("SUPABASE_SERVICE_ROLE_KEY", "your_supabase_service_role_key_here")

        repo = get_repository()
        assert isinstance(repo, InMemoryRepository)


def test_repository_factory_force_in_memory():
    """Verify force_in_memory=True unconditionally produces InMemoryRepository."""
    repo = get_repository(force_in_memory=True)
    assert isinstance(repo, InMemoryRepository)


def test_supabase_repository_initialization_with_mock():
    """Verify SupabaseRepository can be initialized with an injected mock Client."""
    mock_client = MagicMock()
    repo = SupabaseRepository(
        supabase_url="https://mock.supabase.co",
        supabase_key="mock_key",
        client=mock_client,
    )
    assert repo.client == mock_client


# ==============================================================================
# 3. Experiment and Architecture Lineage Persistence
# ==============================================================================

def test_experiment_creation_and_lifecycle():
    """Verify creating, querying, and updating experiment status."""
    repo = InMemoryRepository()
    user_id = "user_001_uuid"

    # Create experiment
    exp = repo.create_experiment(
        name="Autonomous Dual-Ledger Optimization",
        domain="financial_reconciliation",
        user_id=user_id,
        metadata={"target_accuracy": 1.0, "max_generations": 3},
    )
    assert isinstance(exp, ExperimentRecord)
    assert exp.name == "Autonomous Dual-Ledger Optimization"
    assert exp.domain == "financial_reconciliation"
    assert exp.user_id == user_id
    assert exp.status == "running"

    # Fetch experiment
    fetched = repo.get_experiment(exp.id, user_id=user_id)
    assert fetched is not None
    assert fetched.id == exp.id

    # Update status
    updated = repo.update_experiment_status(exp.id, status="completed", user_id=user_id)
    assert updated.status == "completed"

    # List experiments for user
    experiments = repo.list_experiments(user_id=user_id)
    assert len(experiments) == 1
    assert experiments[0].id == exp.id


def test_architecture_lineage_persistence():
    """Verify persisting immutable agent architectures across generations."""
    repo = InMemoryRepository()
    user_id = "user_001_uuid"

    exp = repo.create_experiment(
        name="Architecture Lineage Test",
        domain="financial_reconciliation",
        user_id=user_id,
    )

    analyzer = GoalAnalyzer()
    spec = analyzer.analyze("Reconcile financial ledgers and detect discrepancies")
    generator = ArchitectureGenerator()
    arch_v0 = generator.generate(spec, architecture_name="Agent_Reconciliation_V0")

    # Save baseline (generation 0)
    saved_v0 = repo.save_architecture(arch_v0, experiment_id=exp.id, user_id=user_id, generation=0)
    assert saved_v0.id == arch_v0.id
    assert saved_v0.generation == 0
    assert saved_v0.experiment_id == exp.id

    # Retrieve architectures
    archs = repo.get_architectures(exp.id, user_id=user_id)
    assert len(archs) == 1
    assert archs[0].name == "Agent_Reconciliation_V0"


# ==============================================================================
# 4. Historical Immutability (Benchmarks, Evaluations, Mutations)
# ==============================================================================

def test_historical_immutability_of_benchmark_scorecards():
    """Verify past generation benchmark runs are strictly immutable and cannot be overwritten."""
    repo = InMemoryRepository()
    user_id = "user_001_uuid"

    exp = repo.create_experiment(
        name="Immutability Benchmark Test",
        domain="financial_reconciliation",
        user_id=user_id,
    )

    analyzer = GoalAnalyzer()
    spec = analyzer.analyze("Reconcile financial transactions")
    generator = ArchitectureGenerator()
    arch = generator.generate(spec, architecture_name="Agent_Reconciliation_V0")
    repo.save_architecture(arch, exp.id, user_id, generation=0)

    scorecard_v0 = Scorecard(
        name="Baseline_Scorecard",
        split="optimization",
        total_cases=10,
        accurate_cases=7,
        reliable_cases=10,
        accuracy=0.70,
        reliability=1.00,
        cost_usd=0.005,
        latency_ms=120.0,
        case_results=[
            CaseEvaluationResult(
                case_id="case_1",
                split="optimization",
                is_accurate=True,
                is_reliable=True,
                cost_usd=0.0005,
                latency_ms=12.0,
            )
        ],
    )

    # Save initial benchmark run
    run_record = repo.save_benchmark_run(
        scorecard=scorecard_v0,
        architecture_id=arch.id,
        experiment_id=exp.id,
        user_id=user_id,
        split="optimization",
    )
    assert run_record.accuracy == 0.70
    assert run_record.total_cases == 10

    # Attempting to overwrite the exact same benchmark run on optimization split must raise ImmutabilityError
    with pytest.raises(ImmutabilityError, match="cannot be overwritten"):
        repo.save_benchmark_run(
            scorecard=scorecard_v0,
            architecture_id=arch.id,
            experiment_id=exp.id,
            user_id=user_id,
            split="optimization",
        )

    # Verify existing benchmark run was untouched
    runs = repo.get_benchmark_runs(exp.id, user_id=user_id)
    assert len(runs) == 1
    assert runs[0].accuracy == 0.70


def test_evaluations_and_mutations_persistence():
    """Verify persisting side-by-side Pareto evaluations and architectural mutation records."""
    repo = InMemoryRepository()
    user_id = "user_001_uuid"

    exp = repo.create_experiment(
        name="Evaluation and Mutation Test",
        domain="financial_reconciliation",
        user_id=user_id,
    )

    # Create dummy comparison
    sc_base = Scorecard(
        name="Baseline", split="optimization", total_cases=5, accurate_cases=3,
        reliable_cases=5, accuracy=0.6, reliability=1.0, cost_usd=0.002, latency_ms=50.0
    )
    sc_cand = Scorecard(
        name="Candidate", split="optimization", total_cases=5, accurate_cases=5,
        reliable_cases=5, accuracy=1.0, reliability=1.0, cost_usd=0.003, latency_ms=55.0
    )
    comparison = ScorecardComparison(
        baseline_name="Baseline",
        candidate_name="Candidate",
        split="optimization",
        baseline_scorecard=sc_base,
        candidate_scorecard=sc_cand,
        accuracy_delta=0.4,
        reliability_delta=0.0,
        cost_delta_usd=0.001,
        latency_delta_ms=5.0,
        latency_pct_delta=10.0,
        accuracy_badge="▲ +40.0%",
        reliability_badge="— 0.0%",
        cost_badge="▼ +0.0010 USD",
        latency_badge="▼ +10.0%",
        is_pareto_dominant=True,
        has_tradeoff=False,
        tradeoffs=[],
        verdict="PARETO_DOMINANT",
    )

    eval_rec = repo.save_evaluation(
        comparison=comparison,
        experiment_id=exp.id,
        user_id=user_id,
        baseline_architecture_id="Agent_V0",
        candidate_architecture_id="Agent_V1",
    )
    assert eval_rec.verdict == "PARETO_DOMINANT"
    assert eval_rec.baseline_architecture_id == "Agent_V0"

    evals = repo.get_evaluations(exp.id, user_id=user_id)
    assert len(evals) == 1
    assert evals[0].verdict == "PARETO_DOMINANT"

    # Persist Mutation
    diff = CandidateDiff(
        baseline_id="Agent_V0",
        candidate_id="Agent_V1",
        summary="Added verifier node",
        added_nodes=["verifier_node"],
    )
    mutation_res = MutationResult(
        success=True,
        applied_mutators=["VerifierNodeMutator"],
        candidate_architecture=None,
        diff=diff,
    )

    mut_rec = repo.save_mutation(
        mutation_result=mutation_res,
        experiment_id=exp.id,
        user_id=user_id,
        parent_architecture_id="Agent_V0",
        child_architecture_id="Agent_V1",
        generation=1,
        diagnostic_category="verification_miss",
    )
    assert mut_rec.mutator_name == "VerifierNodeMutator"
    assert mut_rec.generation == 1

    mutations = repo.get_mutations(exp.id, user_id=user_id)
    assert len(mutations) == 1
    assert mutations[0].diagnostic_category == "verification_miss"


# ==============================================================================
# 5. Neatlogs Trace Persistence
# ==============================================================================

def test_neatlogs_distributed_trace_persistence():
    """Verify persisting and querying Neatlogs distributed traces with deep links."""
    repo = InMemoryRepository()
    user_id = "user_001_uuid"

    exp = repo.create_experiment(
        name="Trace Persistence Test",
        domain="financial_reconciliation",
        user_id=user_id,
    )

    trace = NeatlogsTrace(
        trace_id="tr_neat_test_998877",
        architecture_id="Agent_Reconciliation_V1",
        status="success",
        total_duration_ms=88.5,
        total_tokens=250,
        total_cost_usd=0.0025,
        deep_link="https://app.neatlogs.com/traces/tr_neat_test_998877",
        spans=[
            NeatlogsSpan(
                trace_id="tr_neat_test_998877",
                name="Tool: smart_reconcile",
                kind="tool_invocation",
                duration_ms=45.2,
                status="ok",
                attributes={"currency_parsed": True},
            )
        ],
    )

    trace_rec = repo.save_trace(trace, experiment_id=exp.id, user_id=user_id)
    assert trace_rec.id == "tr_neat_test_998877"
    assert trace_rec.deep_link_url == "https://app.neatlogs.com/traces/tr_neat_test_998877"
    assert len(trace_rec.spans) == 1

    # Overwrite attempt raises ImmutabilityError
    with pytest.raises(ImmutabilityError, match="already exists"):
        repo.save_trace(trace, experiment_id=exp.id, user_id=user_id)

    fetched_traces = repo.get_traces(exp.id, user_id=user_id)
    assert len(fetched_traces) == 1
    assert fetched_traces[0].id == "tr_neat_test_998877"


# ==============================================================================
# 6. GoTrue JWT Authentication
# ==============================================================================

def test_gotrue_jwt_authentication_valid_token():
    """Verify GoTrueAuthHandler extracts and verifies a valid JWT token."""
    secret = "my_jwt_secret_32_characters_long_12345"
    user_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    email = "engineer@reco.ai"

    # Create signed test token
    token = GoTrueAuthHandler.create_test_token(
        user_id=user_id,
        email=email,
        role="authenticated",
        secret=secret,
        expires_in_seconds=3600,
    )

    auth_handler = GoTrueAuthHandler(jwt_secret=secret)

    # 1. Test header extraction
    auth_header = f"Bearer {token}"
    extracted = auth_handler.extract_bearer_token(auth_header)
    assert extracted == token

    # 2. Test token verification
    user_ctx = auth_handler.authenticate_header(auth_header)
    assert isinstance(user_ctx, UserContext)
    assert user_ctx.user_id == user_id
    assert user_ctx.email == email
    assert user_ctx.role == "authenticated"


def test_gotrue_jwt_authentication_expired_token():
    """Verify expired GoTrue JWT token raises AuthenticationError."""
    secret = "my_jwt_secret_32_characters_long_12345"
    user_id = "expired_user_uuid"

    # Generate token that expired 10 seconds ago
    expired_token = GoTrueAuthHandler.create_test_token(
        user_id=user_id,
        secret=secret,
        expires_in_seconds=-10,
    )

    auth_handler = GoTrueAuthHandler(jwt_secret=secret)

    with pytest.raises(AuthenticationError, match="expired"):
        auth_handler.verify_token(expired_token)


def test_gotrue_jwt_authentication_malformed_header():
    """Verify malformed Authorization headers raise AuthenticationError."""
    auth_handler = GoTrueAuthHandler()

    with pytest.raises(AuthenticationError, match="Missing or malformed Authorization header"):
        auth_handler.authenticate_header("Basic dXNlcjpwYXNz")

    with pytest.raises(AuthenticationError, match="Missing or malformed Authorization header"):
        auth_handler.authenticate_header(None)

    with pytest.raises(AuthenticationError, match="Missing or malformed Authorization header"):
        auth_handler.authenticate_header("")


# ==============================================================================
# 7. Multi-Tenant User Isolation
# ==============================================================================

def test_multi_tenant_user_isolation_strictly_enforced():
    """Verify multi-tenant isolation: User A's data is completely inaccessible to User B."""
    repo = InMemoryRepository()

    user_a = "user_alpha_uuid"
    user_b = "user_beta_uuid"

    # User A creates an experiment
    exp_a = repo.create_experiment(
        name="User A Confidential Optimization",
        domain="financial_reconciliation",
        user_id=user_a,
    )

    # User B cannot see Experiment A
    exp_b_view = repo.get_experiment(exp_a.id, user_id=user_b)
    assert exp_b_view is None

    # User B list_experiments contains 0 experiments
    assert len(repo.list_experiments(user_id=user_b)) == 0

    # User B cannot update Experiment A status
    with pytest.raises(UserIsolationError, match="belongs to a different user"):
        repo.update_experiment_status(exp_a.id, status="tampered", user_id=user_b)

    # User B cannot query User A's benchmark runs
    with pytest.raises(UserIsolationError, match="belongs to a different user"):
        repo.get_benchmark_runs(exp_a.id, user_id=user_b)

    # User B cannot query User A's architectures
    with pytest.raises(UserIsolationError, match="belongs to a different user"):
        repo.get_architectures(exp_a.id, user_id=user_b)

    # User B cannot query User A's traces
    with pytest.raises(UserIsolationError, match="belongs to a different user"):
        repo.get_traces(exp_a.id, user_id=user_b)
