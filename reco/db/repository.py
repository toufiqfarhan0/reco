"""Experiment Repository interface and In-Memory local fallback implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional
import uuid

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
from reco.engine.models import AgentArchitecture
from reco.evaluators.scorecard import Scorecard, ScorecardComparison
from reco.mutation.engine import MutationResult
from reco.observability.tracer import NeatlogsTrace


class ExperimentRepository(ABC):
    """Abstract interface for multi-tenant persistence of agent experiments and lineage."""

    @abstractmethod
    def create_experiment(
        self,
        name: str,
        domain: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExperimentRecord:
        """Create and persist a new optimization experiment session."""
        pass

    @abstractmethod
    def get_experiment(self, experiment_id: str, user_id: str) -> Optional[ExperimentRecord]:
        """Fetch an experiment by ID, enforcing user isolation."""
        pass

    @abstractmethod
    def list_experiments(self, user_id: str) -> List[ExperimentRecord]:
        """List all experiments belonging to the authenticated user."""
        pass

    @abstractmethod
    def update_experiment_status(self, experiment_id: str, status: str, user_id: str) -> ExperimentRecord:
        """Update the status of an ongoing experiment."""
        pass

    @abstractmethod
    def save_architecture(
        self,
        architecture: AgentArchitecture,
        experiment_id: str,
        user_id: str,
        generation: int = 0
    ) -> ArchitectureRecord:
        """Persist an immutable DAG architecture definition."""
        pass

    @abstractmethod
    def get_architectures(self, experiment_id: str, user_id: str) -> List[ArchitectureRecord]:
        """Retrieve all architectures for an experiment."""
        pass

    @abstractmethod
    def save_benchmark_run(
        self,
        scorecard: Scorecard,
        architecture_id: str,
        experiment_id: str,
        user_id: str,
        split: str = "optimization"
    ) -> BenchmarkRunRecord:
        """Persist an empirical benchmark scorecard. Strictly immutable."""
        pass

    @abstractmethod
    def get_benchmark_runs(
        self,
        experiment_id: str,
        user_id: str,
        architecture_id: Optional[str] = None
    ) -> List[BenchmarkRunRecord]:
        """Retrieve benchmark runs for an experiment."""
        pass

    @abstractmethod
    def save_evaluation(
        self,
        comparison: ScorecardComparison,
        experiment_id: str,
        user_id: str,
        baseline_architecture_id: str,
        candidate_architecture_id: str
    ) -> EvaluationRecord:
        """Persist an empirical Pareto comparison. Strictly immutable."""
        pass

    @abstractmethod
    def get_evaluations(self, experiment_id: str, user_id: str) -> List[EvaluationRecord]:
        """Retrieve evaluation comparisons for an experiment."""
        pass

    @abstractmethod
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
        """Persist an architectural mutation record. Strictly immutable."""
        pass

    @abstractmethod
    def get_mutations(self, experiment_id: str, user_id: str) -> List[MutationRecord]:
        """Retrieve mutation lineage for an experiment."""
        pass

    @abstractmethod
    def save_trace(
        self,
        trace: NeatlogsTrace,
        experiment_id: str,
        user_id: str,
        architecture_id: Optional[str] = None
    ) -> TraceRecord:
        """Persist a Neatlogs distributed execution trace."""
        pass

    @abstractmethod
    def get_traces(
        self,
        experiment_id: str,
        user_id: str,
        architecture_id: Optional[str] = None
    ) -> List[TraceRecord]:
        """Retrieve distributed traces for an experiment."""
        pass


class InMemoryRepository(ExperimentRepository):
    """Thread-safe in-memory repository implementing historical immutability & user isolation.

    Used as the default graceful fallback when cloud Supabase credentials are not configured.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._experiments: Dict[str, ExperimentRecord] = {}
        self._architectures: Dict[str, ArchitectureRecord] = {}
        self._benchmark_runs: Dict[str, BenchmarkRunRecord] = {}
        self._evaluations: Dict[str, EvaluationRecord] = {}
        self._mutations: Dict[str, MutationRecord] = {}
        self._traces: Dict[str, TraceRecord] = {}

    def _verify_experiment_ownership(self, experiment_id: str, user_id: str) -> ExperimentRecord:
        """Ensure experiment exists and belongs to the requested user."""
        exp = self._experiments.get(experiment_id)
        if exp is None:
            raise ValueError(f"Experiment '{experiment_id}' does not exist.")
        if exp.user_id != user_id:
            raise UserIsolationError(
                f"Access denied: Experiment '{experiment_id}' belongs to a different user."
            )
        return exp

    def create_experiment(
        self,
        name: str,
        domain: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExperimentRecord:
        with self._lock:
            record = ExperimentRecord(
                name=name,
                domain=domain,
                user_id=user_id,
                metadata=metadata or {},
            )
            self._experiments[record.id] = record
            return record

    def get_experiment(self, experiment_id: str, user_id: str) -> Optional[ExperimentRecord]:
        with self._lock:
            exp = self._experiments.get(experiment_id)
            if exp and exp.user_id == user_id:
                return exp
            return None

    def list_experiments(self, user_id: str) -> List[ExperimentRecord]:
        with self._lock:
            return [
                exp for exp in self._experiments.values()
                if exp.user_id == user_id
            ]

    def update_experiment_status(self, experiment_id: str, status: str, user_id: str) -> ExperimentRecord:
        with self._lock:
            exp = self._verify_experiment_ownership(experiment_id, user_id)
            updated = exp.model_copy(update={
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            self._experiments[experiment_id] = updated
            return updated

    def save_architecture(
        self,
        architecture: AgentArchitecture,
        experiment_id: str,
        user_id: str,
        generation: int = 0
    ) -> ArchitectureRecord:
        with self._lock:
            self._verify_experiment_ownership(experiment_id, user_id)
            if architecture.id in self._architectures:
                existing = self._architectures[architecture.id]
                if existing.experiment_id == experiment_id and existing.user_id == user_id:
                    # Idempotent return if identical definition
                    return existing
                raise ImmutabilityError(
                    f"Architecture '{architecture.id}' already exists and cannot be overwritten."
                )

            record = ArchitectureRecord(
                id=architecture.id,
                experiment_id=experiment_id,
                user_id=user_id,
                name=architecture.name,
                generation=generation,
                definition=architecture.model_dump(),
            )
            self._architectures[record.id] = record
            return record

    def get_architectures(self, experiment_id: str, user_id: str) -> List[ArchitectureRecord]:
        with self._lock:
            self._verify_experiment_ownership(experiment_id, user_id)
            return [
                arch for arch in self._architectures.values()
                if arch.experiment_id == experiment_id and arch.user_id == user_id
            ]

    def save_benchmark_run(
        self,
        scorecard: Scorecard,
        architecture_id: str,
        experiment_id: str,
        user_id: str,
        split: str = "optimization"
    ) -> BenchmarkRunRecord:
        with self._lock:
            self._verify_experiment_ownership(experiment_id, user_id)

            # Historical immutability check: prevent overwriting duplicate benchmark run
            for existing in self._benchmark_runs.values():
                if (
                    existing.experiment_id == experiment_id
                    and existing.architecture_id == architecture_id
                    and existing.split == split
                ):
                    raise ImmutabilityError(
                        f"Benchmark run for architecture '{architecture_id}' on split '{split}' "
                        f"already exists in experiment '{experiment_id}' and cannot be overwritten."
                    )

            case_dicts = [
                c.model_dump() if hasattr(c, "model_dump") else dict(c)
                for c in scorecard.case_results
            ]

            record = BenchmarkRunRecord(
                experiment_id=experiment_id,
                architecture_id=architecture_id,
                user_id=user_id,
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
            self._benchmark_runs[record.id] = record
            return record

    def get_benchmark_runs(
        self,
        experiment_id: str,
        user_id: str,
        architecture_id: Optional[str] = None
    ) -> List[BenchmarkRunRecord]:
        with self._lock:
            self._verify_experiment_ownership(experiment_id, user_id)
            runs = [
                r for r in self._benchmark_runs.values()
                if r.experiment_id == experiment_id and r.user_id == user_id
            ]
            if architecture_id:
                runs = [r for r in runs if r.architecture_id == architecture_id]
            return runs

    def save_evaluation(
        self,
        comparison: ScorecardComparison,
        experiment_id: str,
        user_id: str,
        baseline_architecture_id: str,
        candidate_architecture_id: str
    ) -> EvaluationRecord:
        with self._lock:
            self._verify_experiment_ownership(experiment_id, user_id)

            record = EvaluationRecord(
                experiment_id=experiment_id,
                user_id=user_id,
                baseline_architecture_id=baseline_architecture_id,
                candidate_architecture_id=candidate_architecture_id,
                comparison=comparison.model_dump(),
                verdict=comparison.verdict,
            )
            self._evaluations[record.id] = record
            return record

    def get_evaluations(self, experiment_id: str, user_id: str) -> List[EvaluationRecord]:
        with self._lock:
            self._verify_experiment_ownership(experiment_id, user_id)
            return [
                ev for ev in self._evaluations.values()
                if ev.experiment_id == experiment_id and ev.user_id == user_id
            ]

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
        with self._lock:
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
                user_id=user_id,
                parent_architecture_id=parent_architecture_id,
                child_architecture_id=child_architecture_id,
                generation=generation,
                mutator_name=mutator_name,
                diagnostic_category=diag_category,
                mutation_diff=diff_data,
            )
            self._mutations[record.id] = record
            return record

    def get_mutations(self, experiment_id: str, user_id: str) -> List[MutationRecord]:
        with self._lock:
            self._verify_experiment_ownership(experiment_id, user_id)
            return [
                m for m in self._mutations.values()
                if m.experiment_id == experiment_id and m.user_id == user_id
            ]

    def save_trace(
        self,
        trace: NeatlogsTrace,
        experiment_id: str,
        user_id: str,
        architecture_id: Optional[str] = None
    ) -> TraceRecord:
        with self._lock:
            self._verify_experiment_ownership(experiment_id, user_id)

            if trace.trace_id in self._traces:
                raise ImmutabilityError(
                    f"Trace '{trace.trace_id}' already exists and cannot be overwritten."
                )

            spans_data = [s.model_dump() for s in trace.spans]

            record = TraceRecord(
                id=trace.trace_id,
                experiment_id=experiment_id,
                architecture_id=architecture_id or trace.architecture_id,
                user_id=user_id,
                status=trace.status,
                total_duration_ms=trace.total_duration_ms,
                total_tokens=trace.total_tokens,
                total_cost_usd=trace.total_cost_usd,
                spans=spans_data,
                deep_link_url=trace.deep_link or None,
            )
            self._traces[record.id] = record
            return record

    def get_traces(
        self,
        experiment_id: str,
        user_id: str,
        architecture_id: Optional[str] = None
    ) -> List[TraceRecord]:
        with self._lock:
            self._verify_experiment_ownership(experiment_id, user_id)
            traces = [
                t for t in self._traces.values()
                if t.experiment_id == experiment_id and t.user_id == user_id
            ]
            if architecture_id:
                traces = [t for t in traces if t.architecture_id == architecture_id]
            return traces
