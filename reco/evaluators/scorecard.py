"""Generic domain-agnostic multi-dimensional scorecard model.

Evaluates and represents agent performance across four standard axes:
1. Accuracy (higher = better, 0.0 to 1.0)
2. Reliability (higher = better, 0.0 to 1.0)
3. Cost (lower = better, in USD, distinguishing actual vs simulated_mock)
4. Speed / Latency (lower = better, in milliseconds)
"""

from typing import Any, Dict, Literal, Optional, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator

from reco.core.interfaces import BenchmarkRunResult
from reco.db.models import BenchmarkRunRecord


class NormalizedMetrics(BaseModel):
    """Auxiliary normalized 0.0-1.0 representation for visualization and radar charts.

    Raw units are always preserved in the parent Scorecard.
    """
    accuracy_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized accuracy (0.0 to 1.0)")
    reliability_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized reliability (0.0 to 1.0)")
    cost_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized cost efficiency (1.0 = lowest cost)")
    speed_norm: float = Field(..., ge=0.0, le=1.0, description="Normalized speed efficiency (1.0 = lowest latency)")
    reference_bounds: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Scorecard(BaseModel):
    """Generic multi-dimensional evaluation scorecard for an agent version across a benchmark split."""
    benchmark_name: str = Field(..., description="Benchmark suite name (e.g. 'reconciliation', 'research')")
    benchmark_version: str = Field(..., description="Immutable benchmark suite version (e.g. 'reconciliation-v1')")
    agent_version_id: Optional[UUID] = Field(default=None, description="UUID of the evaluated agent version")
    experiment_id: Optional[UUID] = Field(default=None, description="UUID of the parent experiment")
    split: Literal["optimization", "held_out", "full"] = Field(
        ...,
        description="'optimization' (mutation/diagnosis) or 'held_out' (validation/promotion)",
    )

    # 1. Raw Primary Metrics
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Domain-evaluated accuracy score (0.0 to 1.0, higher is better)",
    )
    reliability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Crash-free execution success rate (0.0 to 1.0, higher is better)",
    )
    total_cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Total execution cost in USD (lower is better)",
    )
    avg_cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Average execution cost per case in USD (lower is better)",
    )
    cost_type: Literal["actual", "estimated", "simulated_mock"] = Field(
        default="actual",
        description="Provenance of cost metric ('actual', 'estimated', 'simulated_mock')",
    )
    total_latency_ms: int = Field(
        default=0,
        ge=0,
        description="Total wall-clock execution duration in milliseconds (lower is better)",
    )
    avg_latency_ms: int = Field(
        default=0,
        ge=0,
        description="Average wall-clock duration per case in milliseconds (lower is better)",
    )
    p50_latency_ms: Optional[int] = Field(default=None, ge=0, description="50th percentile latency in ms")
    p95_latency_ms: Optional[int] = Field(default=None, ge=0, description="95th percentile latency in ms")

    # 2. Case Counts
    total_cases: int = Field(..., ge=0, description="Total benchmark test cases executed")
    passed_cases: int = Field(..., ge=0, description="Number of test cases passing accuracy & reliability criteria")
    failed_cases: int = Field(..., ge=0, description="Number of test cases failing criteria")

    # 3. Normalized Representation & Metadata
    normalized: Optional[NormalizedMetrics] = Field(
        default=None,
        description="Optional normalized scores for comparison/visualization without discarding raw metrics",
    )
    execution_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional benchmark, provider, or environment metadata",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def passed(self) -> bool:
        """Convenience boolean indicator for whether the benchmark passed baseline criteria."""
        return self.passed_cases > 0 and self.accuracy >= 0.50

    @field_validator("failed_cases")
    @classmethod
    def validate_case_counts(cls, v: int, info) -> int:
        data = info.data
        total = data.get("total_cases")
        passed = data.get("passed_cases")
        if total is not None and passed is not None:
            if passed + v != total:
                # Rebalance or allow explicit validation
                if passed > total:
                    raise ValueError(f"passed_cases ({passed}) cannot exceed total_cases ({total})")
        return v

    def compute_normalized(
        self,
        cost_max_ref: Optional[float] = None,
        latency_max_ref: Optional[int] = None,
    ) -> NormalizedMetrics:
        """Compute and attach auxiliary normalized 0.0-1.0 scores while preserving raw metrics."""
        cost_max = cost_max_ref if cost_max_ref and cost_max_ref > 0 else max(self.avg_cost_usd * 2, 0.01)
        latency_max = latency_max_ref if latency_max_ref and latency_max_ref > 0 else max(self.avg_latency_ms * 2, 100)

        cost_eff = max(0.0, min(1.0, 1.0 - (self.avg_cost_usd / cost_max)))
        speed_eff = max(0.0, min(1.0, 1.0 - (self.avg_latency_ms / latency_max)))

        norm = NormalizedMetrics(
            accuracy_norm=round(self.accuracy, 4),
            reliability_norm=round(self.reliability, 4),
            cost_norm=round(cost_eff, 4),
            speed_norm=round(speed_eff, 4),
            reference_bounds={
                "cost_max_ref": cost_max,
                "latency_max_ref": latency_max,
                "units": {
                    "accuracy": "ratio (0-1)",
                    "reliability": "ratio (0-1)",
                    "cost": "USD",
                    "latency": "ms",
                },
            },
        )
        self.normalized = norm
        return norm

    @classmethod
    def from_benchmark_run_result(
        cls,
        result: BenchmarkRunResult,
        benchmark_name: str = "generic",
        benchmark_version: str = "v1",
        cost_type: Literal["actual", "estimated", "simulated_mock"] = "simulated_mock",
        agent_version_id: Optional[UUID] = None,
        experiment_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Scorecard":
        """Construct a Scorecard from the core BenchmarkRunResult exchange model."""
        total = result.cases_total
        passed = result.cases_passed
        failed = total - passed
        avg_cost = result.total_cost_usd / total if total > 0 else 0.0
        total_lat = result.avg_latency_ms * total

        card = cls(
            benchmark_name=benchmark_name,
            benchmark_version=benchmark_version,
            agent_version_id=agent_version_id,
            experiment_id=experiment_id,
            split=result.split,  # type: ignore
            accuracy=result.accuracy,
            reliability=result.reliability,
            total_cost_usd=round(result.total_cost_usd, 6),
            avg_cost_usd=round(avg_cost, 6),
            cost_type=cost_type,
            total_latency_ms=total_lat,
            avg_latency_ms=result.avg_latency_ms,
            total_cases=total,
            passed_cases=passed,
            failed_cases=failed,
            execution_metadata=metadata or {},
        )
        return card

    @classmethod
    def from_reconciliation_run_result(
        cls,
        result: Any,  # ReconciliationRunResult
        agent_version_id: Optional[UUID] = None,
        experiment_id: Optional[UUID] = None,
    ) -> "Scorecard":
        """Construct a generic Scorecard from a domain-specific ReconciliationRunResult."""
        total = result.total_cases
        avg_cost = result.total_cost_usd / total if total > 0 else 0.0
        cost_type_meta = result.metadata.get("cost_type", "simulated_mock")
        if cost_type_meta == "actual_provider":
            cost_type_meta = "estimated"
        cost_type: Literal["actual", "estimated", "simulated_mock"] = (
            cost_type_meta if cost_type_meta in ["actual", "estimated", "simulated_mock"] else "simulated_mock"
        )

        # Extract percentiles from case results if available
        latencies = sorted([c.latency_ms for c in result.case_results]) if result.case_results else []
        p50 = latencies[len(latencies) // 2] if latencies else None
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else None

        card = cls(
            benchmark_name=result.benchmark_name,
            benchmark_version=result.benchmark_version,
            agent_version_id=agent_version_id,
            experiment_id=experiment_id,
            split=result.split,
            accuracy=result.accuracy,
            reliability=result.reliability,
            total_cost_usd=result.total_cost_usd,
            avg_cost_usd=round(avg_cost, 6),
            cost_type=cost_type,
            total_latency_ms=result.total_latency_ms,
            avg_latency_ms=result.avg_latency_ms,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            total_cases=total,
            passed_cases=result.passed_cases,
            failed_cases=result.failed_cases,
            execution_metadata={
                **result.metadata,
                "generation_method": result.generation_method,
            },
        )
        return card

    @classmethod
    def from_db_record(
        cls,
        record: BenchmarkRunRecord,
    ) -> "Scorecard":
        """Reconstitute a generic Scorecard from a stored database BenchmarkRunRecord."""
        total = record.total_cases
        avg_cost = record.total_cost_usd / total if total > 0 else 0.0
        avg_lat = int(record.latency_ms / total) if total > 0 else 0
        cost_type_meta = record.metadata.get("cost_type", "actual")
        cost_type: Literal["actual", "estimated", "simulated_mock"] = (
            cost_type_meta if cost_type_meta in ["actual", "estimated", "simulated_mock"] else "actual"
        )

        return cls(
            benchmark_name=record.benchmark_name,
            benchmark_version=record.metadata.get("benchmark_version", "reconciliation-v1"),
            agent_version_id=record.agent_version_id,
            experiment_id=record.experiment_id,
            split=record.split,  # type: ignore
            accuracy=record.accuracy,
            reliability=record.reliability,
            total_cost_usd=record.total_cost_usd,
            avg_cost_usd=round(avg_cost, 6),
            cost_type=cost_type,
            total_latency_ms=record.latency_ms,
            avg_latency_ms=record.metadata.get("avg_latency_ms", avg_lat),
            total_cases=total,
            passed_cases=record.passed_cases,
            failed_cases=record.failed_cases,
            execution_metadata=record.metadata,
        )

    def to_db_record(
        self,
        experiment_id: Optional[UUID] = None,
        agent_version_id: Optional[UUID] = None,
    ) -> BenchmarkRunRecord:
        """Convert this Scorecard into a database BenchmarkRunRecord for persistence."""
        exp_id = experiment_id or self.experiment_id or uuid4()
        ver_id = agent_version_id or self.agent_version_id or uuid4()

        return BenchmarkRunRecord(
            experiment_id=exp_id,
            agent_version_id=ver_id,
            benchmark_name=self.benchmark_name,
            split=self.split,
            total_cases=self.total_cases,
            passed_cases=self.passed_cases,
            failed_cases=self.failed_cases,
            accuracy=self.accuracy,
            reliability=self.reliability,
            total_cost_usd=self.total_cost_usd,
            latency_ms=self.total_latency_ms,
            status="completed",
            metadata={
                "benchmark_version": self.benchmark_version,
                "avg_cost_usd": self.avg_cost_usd,
                "avg_latency_ms": self.avg_latency_ms,
                "cost_type": self.cost_type,
                "p50_latency_ms": self.p50_latency_ms,
                "p95_latency_ms": self.p95_latency_ms,
                **self.execution_metadata,
            },
        )
