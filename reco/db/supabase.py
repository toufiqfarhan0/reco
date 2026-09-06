"""Supabase PostgreSQL persistence provider with Row-Level Security and graceful fallback (Track 1)."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
import uuid

try:
    from supabase import Client, create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = Any  # type: ignore

from reco.db.models import (
    ArchitectureRecord,
    BenchmarkRunRecord,
    EvaluationRecord,
    ExperimentRecord,
    ImmutabilityError,
    MutationRecord,
    TraceRecord,
    UserIsolationError,
)
from reco.db.repository import ExperimentRepository, InMemoryRepository
from reco.engine.models import AgentArchitecture
from reco.evaluators.scorecard import Scorecard, ScorecardComparison
from reco.mutation.engine import MutationResult
from reco.observability.tracer import NeatlogsTrace

logger = logging.getLogger(__name__)

# Known placeholder substrings in sample config files
PLACEHOLDER_SUBSTRINGS = (
    "your-project.supabase.co",
    "your_supabase_service_role_key_here",
    "your_supabase_anon_key_here",
    "your_api_key_here",
    "<your-supabase",
)


def _is_placeholder_credential(val: Optional[str]) -> bool:
    """Return True if credential is missing, empty, or an unconfigured placeholder."""
    if not val or not val.strip():
        return True
    return any(p in val.lower() for p in PLACEHOLDER_SUBSTRINGS)


class SupabaseRepository(ExperimentRepository):
    """Production PostgreSQL persistence using Supabase Client with RLS user isolation."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        client: Optional[Client] = None,
    ):
        if not SUPABASE_AVAILABLE:
            raise ImportError("supabase package is required to use SupabaseRepository.")

        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL", "")
        self.supabase_key = (
            supabase_key
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_KEY", "")
        )

        if client:
            self.client: Client = client
        else:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def _verify_experiment_ownership(self, experiment_id: str, user_id: str) -> None:
        """Verify experiment exists and belongs to the specified user."""
        res = (
            self.client.table("experiments")
            .select("id, user_id")
            .eq("id", experiment_id)
            .execute()
        )
        if not res.data:
            raise ValueError(f"Experiment '{experiment_id}' not found.")
        row = res.data[0]
        if str(row.get("user_id")) != str(user_id):
            raise UserIsolationError(
                f"Access denied: Experiment '{experiment_id}' belongs to a different user."
            )

    def create_experiment(
        self,
        name: str,
        domain: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExperimentRecord:
        record = ExperimentRecord(
            name=name,
            domain=domain,
            user_id=str(user_id),
            metadata=metadata or {},
        )
        row = {
            "id": record.id,
            "user_id": record.user_id,
            "name": record.name,
            "domain": record.domain,
            "status": record.status,
            "metadata": record.metadata,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
        res = self.client.table("experiments").insert(row).execute()
        if res.data:
            return ExperimentRecord(**res.data[0])
        return record

    def get_experiment(self, experiment_id: str, user_id: str) -> Optional[ExperimentRecord]:
        res = (
            self.client.table("experiments")
            .select("*")
            .eq("id", experiment_id)
            .eq("user_id", str(user_id))
            .execute()
        )
        if res.data:
            return ExperimentRecord(**res.data[0])
        return None

    def list_experiments(self, user_id: str) -> List[ExperimentRecord]:
        res = (
            self.client.table("experiments")
            .select("*")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .execute()
        )
        return [ExperimentRecord(**row) for row in res.data or []]

    def update_experiment_status(self, experiment_id: str, status: str, user_id: str) -> ExperimentRecord:
        self._verify_experiment_ownership(experiment_id, user_id)
        res = (
            self.client.table("experiments")
            .update({"status": status})
            .eq("id", experiment_id)
            .eq("user_id", str(user_id))
            .execute()
        )
        if res.data:
            return ExperimentRecord(**res.data[0])
        exp = self.get_experiment(experiment_id, user_id)
        if not exp:
            raise ValueError(f"Experiment '{experiment_id}' not found.")
        return exp

    def save_architecture(
        self,
        architecture: AgentArchitecture,
        experiment_id: str,
        user_id: str,
        generation: int = 0
    ) -> ArchitectureRecord:
        self._verify_experiment_ownership(experiment_id, user_id)

        # Check existing for idempotency / immutability
        existing = (
            self.client.table("architectures")
            .select("*")
            .eq("id", architecture.id)
            .execute()
        )
        if existing.data:
            row = existing.data[0]
            if str(row.get("experiment_id")) == str(experiment_id) and str(row.get("user_id")) == str(user_id):
                return ArchitectureRecord(**row)
            raise ImmutabilityError(
                f"Architecture '{architecture.id}' already exists and cannot be overwritten."
            )

        record = ArchitectureRecord(
            id=architecture.id,
            experiment_id=experiment_id,
            user_id=str(user_id),
            name=architecture.name,
            generation=generation,
            definition=architecture.model_dump(),
        )
        row = {
            "id": record.id,
            "experiment_id": record.experiment_id,
            "user_id": record.user_id,
            "name": record.name,
            "generation": record.generation,
            "definition": record.definition,
            "created_at": record.created_at,
        }
        res = self.client.table("architectures").insert(row).execute()
        if res.data:
            return ArchitectureRecord(**res.data[0])
        return record

    def get_architectures(self, experiment_id: str, user_id: str) -> List[ArchitectureRecord]:
        self._verify_experiment_ownership(experiment_id, user_id)
        res = (
            self.client.table("architectures")
            .select("*")
            .eq("experiment_id", experiment_id)
            .eq("user_id", str(user_id))
            .order("generation", desc=False)
            .execute()
        )
        return [ArchitectureRecord(**row) for row in res.data or []]

    def save_benchmark_run(
        self,
        scorecard: Scorecard,
        architecture_id: str,
        experiment_id: str,
        user_id: str,
        split: str = "optimization"
    ) -> BenchmarkRunRecord:
        self._verify_experiment_ownership(experiment_id, user_id)

        # Immutability check: historical scorecards cannot be overwritten
        existing = (
            self.client.table("benchmark_runs")
            .select("id")
            .eq("experiment_id", experiment_id)
            .eq("architecture_id", architecture_id)
            .eq("split", split)
            .execute()
        )
        if existing.data:
            raise ImmutabilityError(
                f"Benchmark run for architecture '{architecture_id}' on split '{split}' "
                f"already exists and cannot be overwritten."
            )

        case_dicts = [
            c.model_dump() if hasattr(c, "model_dump") else dict(c)
            for c in scorecard.case_results
        ]

        record = BenchmarkRunRecord(
            experiment_id=experiment_id,
            architecture_id=architecture_id,
            user_id=str(user_id),
            split=split,
            total_cases=scorecard.total_cases,
            passed_cases=scorecard.accurate_cases,
            failed_cases=scorecard.total_cases - scorecard.accurate_cases,
            accuracy=scorecard.accuracy,
            reliability=scorecard.reliability,
            latency_ms=scorecard.avg_latency_ms,
            cost_usd=scorecard.cost_usd,
            case_results=case_dicts,
        )
        row = {
            "id": record.id,
            "experiment_id": record.experiment_id,
            "architecture_id": record.architecture_id,
            "user_id": record.user_id,
            "split": record.split,
            "total_cases": record.total_cases,
            "passed_cases": record.passed_cases,
            "failed_cases": record.failed_cases,
            "accuracy": record.accuracy,
            "reliability": record.reliability,
            "latency_ms": record.latency_ms,
            "cost_usd": record.cost_usd,
            "case_results": record.case_results,
            "created_at": record.created_at,
        }
        res = self.client.table("benchmark_runs").insert(row).execute()
        if res.data:
            return BenchmarkRunRecord(**res.data[0])
        return record

    def get_benchmark_runs(
        self,
        experiment_id: str,
        user_id: str,
        architecture_id: Optional[str] = None
    ) -> List[BenchmarkRunRecord]:
        self._verify_experiment_ownership(experiment_id, user_id)
        query = (
            self.client.table("benchmark_runs")
            .select("*")
            .eq("experiment_id", experiment_id)
            .eq("user_id", str(user_id))
        )
        if architecture_id:
            query = query.eq("architecture_id", architecture_id)
        res = query.order("created_at", desc=False).execute()
        return [BenchmarkRunRecord(**row) for row in res.data or []]

    def save_evaluation(
        self,
        comparison: ScorecardComparison,
        experiment_id: str,
        user_id: str,
        baseline_architecture_id: str,
        candidate_architecture_id: str
    ) -> EvaluationRecord:
        self._verify_experiment_ownership(experiment_id, user_id)

        record = EvaluationRecord(
            experiment_id=experiment_id,
            user_id=str(user_id),
            baseline_architecture_id=baseline_architecture_id,
            candidate_architecture_id=candidate_architecture_id,
            comparison=comparison.model_dump(),
            verdict=comparison.verdict,
        )
        row = {
            "id": record.id,
            "experiment_id": record.experiment_id,
            "user_id": record.user_id,
            "baseline_architecture_id": record.baseline_architecture_id,
            "candidate_architecture_id": record.candidate_architecture_id,
            "comparison": record.comparison,
            "verdict": record.verdict,
            "created_at": record.created_at,
        }
        res = self.client.table("evaluations").insert(row).execute()
        if res.data:
            return EvaluationRecord(**res.data[0])
        return record

    def get_evaluations(self, experiment_id: str, user_id: str) -> List[EvaluationRecord]:
        self._verify_experiment_ownership(experiment_id, user_id)
        res = (
            self.client.table("evaluations")
            .select("*")
            .eq("experiment_id", experiment_id)
            .eq("user_id", str(user_id))
            .order("created_at", desc=False)
            .execute()
        )
        return [EvaluationRecord(**row) for row in res.data or []]

    def save_mutation(
        self,
        mutation_result: MutationResult,
        experiment_id: str,
        user_id: str,
        parent_architecture_id: str,
        child_architecture_id: str,
        generation: int,
        diagnostic_category: Optional[str] = None,
    ) -> MutationRecord:
        self._verify_experiment_ownership(experiment_id, user_id)

        diff_obj = getattr(mutation_result, "diff", None) or getattr(mutation_result, "candidate_diff", None)
        diff_data = (
            diff_obj.model_dump()
            if diff_obj and hasattr(diff_obj, "model_dump")
            else (dict(diff_obj) if diff_obj else {})
        )
        applied_muts = getattr(mutation_result, "applied_mutators", [])
        mutator_name = (
            applied_muts[0]
            if applied_muts
            else getattr(mutation_result, "mutator_applied", "unknown_mutator")
        )
        diag_category = diagnostic_category or getattr(mutation_result, "failure_category", None)

        record = MutationRecord(
            experiment_id=experiment_id,
            user_id=str(user_id),
            parent_architecture_id=parent_architecture_id,
            child_architecture_id=child_architecture_id,
            generation=generation,
            mutator_name=mutator_name,
            diagnostic_category=diag_category,
            mutation_diff=diff_data,
        )
        row = {
            "id": record.id,
            "experiment_id": record.experiment_id,
            "user_id": record.user_id,
            "parent_architecture_id": record.parent_architecture_id,
            "child_architecture_id": record.child_architecture_id,
            "generation": record.generation,
            "mutator_name": record.mutator_name,
            "diagnostic_category": record.diagnostic_category,
            "mutation_diff": record.mutation_diff,
            "created_at": record.created_at,
        }
        res = self.client.table("mutations").insert(row).execute()
        if res.data:
            return MutationRecord(**res.data[0])
        return record

    def get_mutations(self, experiment_id: str, user_id: str) -> List[MutationRecord]:
        self._verify_experiment_ownership(experiment_id, user_id)
        res = (
            self.client.table("mutations")
            .select("*")
            .eq("experiment_id", experiment_id)
            .eq("user_id", str(user_id))
            .order("generation", desc=False)
            .execute()
        )
        return [MutationRecord(**row) for row in res.data or []]

    def save_trace(
        self,
        trace: NeatlogsTrace,
        experiment_id: str,
        user_id: str,
        architecture_id: Optional[str] = None
    ) -> TraceRecord:
        self._verify_experiment_ownership(experiment_id, user_id)

        spans_data = [s.model_dump() for s in trace.spans]

        record = TraceRecord(
            id=trace.trace_id,
            experiment_id=experiment_id,
            architecture_id=architecture_id or trace.architecture_id,
            user_id=str(user_id),
            status=trace.status,
            total_duration_ms=trace.total_duration_ms,
            total_tokens=trace.total_tokens,
            total_cost_usd=trace.total_cost_usd,
            spans=spans_data,
            deep_link_url=trace.deep_link or None,
        )
        row = {
            "id": record.id,
            "experiment_id": record.experiment_id,
            "architecture_id": record.architecture_id,
            "user_id": record.user_id,
            "status": record.status,
            "total_duration_ms": record.total_duration_ms,
            "total_tokens": record.total_tokens,
            "total_cost_usd": record.total_cost_usd,
            "spans": record.spans,
            "deep_link_url": record.deep_link_url,
            "created_at": record.created_at,
        }
        res = self.client.table("traces").insert(row).execute()
        if res.data:
            return TraceRecord(**res.data[0])
        return record

    def get_traces(
        self,
        experiment_id: str,
        user_id: str,
        architecture_id: Optional[str] = None
    ) -> List[TraceRecord]:
        self._verify_experiment_ownership(experiment_id, user_id)
        query = (
            self.client.table("traces")
            .select("*")
            .eq("experiment_id", experiment_id)
            .eq("user_id", str(user_id))
        )
        if architecture_id:
            query = query.eq("architecture_id", architecture_id)
        res = query.order("created_at", desc=False).execute()
        return [TraceRecord(**row) for row in res.data or []]


def get_repository(
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    force_in_memory: bool = False,
) -> ExperimentRepository:
    """Factory creating persistence repository with graceful fallback to InMemoryRepository.

    If Supabase credentials are not provided, contain placeholder values, or force_in_memory
    is True, defaults seamlessly to InMemoryRepository ($0 configuration friction).
    """
    if force_in_memory:
        logger.info("force_in_memory=True specified: using InMemoryRepository.")
        return InMemoryRepository()

    url = supabase_url or os.getenv("SUPABASE_URL")
    key = (
        supabase_key
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
    )

    if _is_placeholder_credential(url) or _is_placeholder_credential(key):
        logger.info(
            "Supabase credentials not configured or placeholder detected. "
            "Gracefully falling back to local InMemoryRepository."
        )
        return InMemoryRepository()

    try:
        return SupabaseRepository(supabase_url=url, supabase_key=key)
    except Exception as exc:
        logger.warning(
            "Failed to initialize SupabaseRepository (%s). Falling back to InMemoryRepository.",
            exc
        )
        return InMemoryRepository()
