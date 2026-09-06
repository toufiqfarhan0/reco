"""Domain models, ground-truth representations, and evaluation scorecard models for the Reconciliation Benchmark."""

from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field

from reco.core.interfaces import BenchmarkCase, BenchmarkRunResult
from reco.db.models import BenchmarkCaseRecord, BenchmarkRunRecord, CaseExecutionRecord


class ExpectedMatchPair(BaseModel):
    """Deterministic expected match pair between bank and ledger."""
    bank_transaction_id: str
    ledger_entry_id: str
    match_type: Literal[
        "exact_match",
        "near_match",
        "processing_fee",
        "timing_difference",
        "duplicate",
        "wrong_vendor",
        "wrong_amount",
        "transposition",
        "fx_difference",
        "compound_exception",
    ] = "exact_match"
    amount_discrepancy: Decimal = Field(default=Decimal("0.00"))
    confidence_min: float = 0.50

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ReconciliationGroundTruth(BaseModel):
    """Deterministic ground truth specification for a reconciliation benchmark scenario."""
    expected_pairs: List[ExpectedMatchPair] = Field(default_factory=list)
    unmatched_bank_ids: List[str] = Field(default_factory=list)
    unmatched_ledger_ids: List[str] = Field(default_factory=list)
    primary_exception: str = "exact_match"
    expected_exceptions: Dict[str, int] = Field(default_factory=dict)
    total_discrepancy: Decimal = Field(default=Decimal("0.00"))
    verification_rules: List[str] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ReconciliationCase(BaseModel):
    """A fully deterministic reconciliation benchmark scenario."""
    case_code: str = Field(..., description="Unique immutable scenario identifier (e.g., REC-OPT-01)")
    benchmark_name: str = "reconciliation"
    benchmark_version: str = "reconciliation-v1"
    split: Literal["optimization", "held_out"] = Field(..., description="'optimization' (12) or 'held_out' (8)")
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    description: str = Field(..., description="Scenario business context and description")
    exception_class: str = Field(..., description="Target exception class category")
    bank_records: List[Dict[str, Any]] = Field(..., description="Raw bank statement records input")
    ledger_entries: List[Dict[str, Any]] = Field(..., description="Raw general ledger entries input")
    ground_truth: ReconciliationGroundTruth = Field(..., description="Deterministic expected reconciliation outcome")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_benchmark_case(self) -> BenchmarkCase:
        """Convert to the core interface BenchmarkCase model."""
        return BenchmarkCase(
            case_code=self.case_code,
            split=self.split,
            input_data={
                "bank_records": self.bank_records,
                "ledger_entries": self.ledger_entries,
                "records": self.bank_records,  # Tool compatibility aliases
                "entries": self.ledger_entries,
            },
            ground_truth=self.ground_truth.model_dump(mode="json"),
        )

    def to_db_record(self) -> BenchmarkCaseRecord:
        """Convert to the database persistence BenchmarkCaseRecord model."""
        return BenchmarkCaseRecord(
            benchmark_name=self.benchmark_name,
            case_code=self.case_code,
            split=self.split,
            difficulty=self.difficulty,
            input_data={
                "bank_records": self.bank_records,
                "ledger_entries": self.ledger_entries,
            },
            ground_truth=self.ground_truth.model_dump(mode="json"),
            metadata={
                "benchmark_version": self.benchmark_version,
                "description": self.description,
                "exception_class": self.exception_class,
                **self.metadata,
            },
        )


class CaseEvaluationResult(BaseModel):
    """Detailed case-level score and execution trace for diagnostic analysis."""
    case_code: str
    split: Literal["optimization", "held_out"]
    success: bool = Field(..., description="True if case passed evaluation criteria (e.g. accuracy >= 0.80)")
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Composite accuracy score")
    reliability_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Execution success / valid output")
    pair_matching_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exception_classification_score: float = Field(default=0.0, ge=0.0, le=1.0)
    discrepancy_score: float = Field(default=0.0, ge=0.0, le=1.0)
    latency_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    expected_outcome: Dict[str, Any] = Field(default_factory=dict)
    actual_outcome: Dict[str, Any] = Field(default_factory=dict)
    detected_exceptions: Dict[str, int] = Field(default_factory=dict)
    tool_events: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_case_execution_record(
        self,
        benchmark_run_id: UUID,
        benchmark_case_id: UUID,
        agent_version_id: UUID,
    ) -> CaseExecutionRecord:
        """Convert to database persistence CaseExecutionRecord model."""
        return CaseExecutionRecord(
            benchmark_run_id=benchmark_run_id,
            benchmark_case_id=benchmark_case_id,
            agent_version_id=agent_version_id,
            output=self.actual_outcome,
            expected=self.expected_outcome,
            success=self.success,
            accuracy_score=self.accuracy_score,
            latency_ms=self.latency_ms,
            input_tokens=self.tokens_in,
            output_tokens=self.tokens_out,
            cost_usd=self.cost_usd,
            tool_events=self.tool_events,
            trace_id=self.trace_id,
            error=self.errors[0] if self.errors else None,
        )


class ReconciliationRunResult(BaseModel):
    """Aggregate benchmark evaluation result across a test split."""
    benchmark_name: str = "reconciliation"
    benchmark_version: str = "reconciliation-v1"
    split: Literal["optimization", "held_out", "full"]
    total_cases: int
    passed_cases: int
    failed_cases: int
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Mean case accuracy")
    reliability: float = Field(..., ge=0.0, le=1.0, description="Pass rate across cases")
    total_cost_usd: float = 0.0
    avg_latency_ms: int = 0
    total_latency_ms: int = 0
    case_results: List[CaseEvaluationResult] = Field(default_factory=list)
    generation_method: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_benchmark_run_result(self) -> BenchmarkRunResult:
        """Convert to the core interface BenchmarkRunResult."""
        return BenchmarkRunResult(
            split=self.split,
            accuracy=self.accuracy,
            reliability=self.reliability,
            total_cost_usd=self.total_cost_usd,
            avg_latency_ms=self.avg_latency_ms,
            cases_passed=self.passed_cases,
            cases_total=self.total_cases,
            case_results=[c.model_dump(mode="json") for c in self.case_results],
        )

    def to_scorecard(
        self,
        agent_version_id: Optional[UUID] = None,
        experiment_id: Optional[UUID] = None,
    ) -> Any:
        """Convert to a generic domain-agnostic multi-dimensional Scorecard."""
        from reco.evaluators.scorecard import Scorecard
        return Scorecard.from_reconciliation_run_result(
            self,
            agent_version_id=agent_version_id,
            experiment_id=experiment_id,
        )

    def to_db_record(
        self,
        experiment_id: UUID,
        agent_version_id: UUID,
    ) -> BenchmarkRunRecord:
        """Convert to database persistence BenchmarkRunRecord."""
        return BenchmarkRunRecord(
            experiment_id=experiment_id,
            agent_version_id=agent_version_id,
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
                "generation_method": self.generation_method,
                "avg_latency_ms": self.avg_latency_ms,
                **self.metadata,
            },
        )
