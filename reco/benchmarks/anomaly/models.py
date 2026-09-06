"""Data models for Dataset Anomaly Detection benchmark."""

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from reco.core.interfaces import BenchmarkCase
from reco.evaluators.scorecard import Scorecard


class AnomalyGroundTruth(BaseModel):
    """Ground truth expected anomalies and evaluation criteria."""
    expected_anomaly_ids: List[str] = Field(default_factory=list, description="Record IDs of expected anomalies")
    expected_types: Dict[str, str] = Field(default_factory=dict, description="Expected anomaly type per record ID")
    allow_empty: bool = Field(default=False, description="Whether an empty anomaly set is the expected correct outcome")
    required_explanations: List[str] = Field(default_factory=list, description="Keywords expected in explanations")


class AnomalyCase(BaseModel):
    """A benchmark case scenario for dataset anomaly detection."""
    case_code: str
    name: str
    description: str
    split: str = "optimization"  # "optimization" or "held_out"
    dataset: List[Dict[str, Any]]
    ground_truth: AnomalyGroundTruth
    difficulty: str = "medium"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_benchmark_case(self) -> BenchmarkCase:
        return BenchmarkCase(
            case_code=self.case_code,
            split=self.split,
            input_data={"dataset": self.dataset},
            ground_truth={
                "expected_anomaly_ids": self.ground_truth.expected_anomaly_ids,
                "expected_types": self.ground_truth.expected_types,
            },
        )


from pydantic import BaseModel, ConfigDict, Field, model_validator


class AnomalyCaseEvaluationResult(BaseModel):
    """Result of evaluating an agent execution on a single anomaly benchmark case."""
    case_code: str
    split: str = "optimization"
    success: bool = False
    accuracy_score: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    detected_anomaly_ids: List[str] = Field(default_factory=list)
    false_positives: List[str] = Field(default_factory=list)
    false_negatives: List[str] = Field(default_factory=list)
    latency_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    tool_events: List[Dict[str, Any]] = Field(default_factory=list)
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    failure_reason: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _normalize_case_eval(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "split" not in data:
                data["split"] = "optimization"
            if "accuracy_score" not in data and "accuracy" in data:
                data["accuracy_score"] = data["accuracy"]
            if "success" not in data and "is_passed" in data:
                data["success"] = data["is_passed"]
            if "f1_score" not in data and "f1" in data:
                data["f1_score"] = data["f1"]
            if "detected_anomaly_ids" not in data and "detected_anomalies" in data:
                data["detected_anomaly_ids"] = data["detected_anomalies"]
        return data

    @property
    def accuracy(self) -> float:
        return self.accuracy_score

    @property
    def is_passed(self) -> bool:
        return self.success


class AnomalyRunResult(BaseModel):
    """Aggregated outcome of running the Anomaly Detection benchmark across a split."""
    benchmark_name: str = "anomaly_detection"
    benchmark_version: str = "anomaly_detection-v1"
    split: str
    total_cases: int
    passed_cases: int
    failed_cases: int = 0
    accuracy: float = 0.0
    reliability: float = 1.0
    total_cost_usd: float = 0.0
    avg_latency_ms: int = 0
    total_latency_ms: int = 0
    case_results: List[AnomalyCaseEvaluationResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _normalize_run_result(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "accuracy" not in data and "mean_accuracy" in data:
                data["accuracy"] = data["mean_accuracy"]
            if "failed_cases" not in data and "total_cases" in data and "passed_cases" in data:
                data["failed_cases"] = data["total_cases"] - data["passed_cases"]
            if "avg_latency_ms" not in data and "total_latency_ms" in data and data.get("total_cases", 0) > 0:
                data["avg_latency_ms"] = int(data["total_latency_ms"] / data["total_cases"])
        return data

    @property
    def mean_accuracy(self) -> float:
        return self.accuracy

    def to_scorecard(self) -> Scorecard:
        """Convert run result into authoritative Reco Scorecard."""
        return Scorecard(
            benchmark_name=self.benchmark_name,
            benchmark_version=self.benchmark_version,
            split=self.split,
            version=self.metadata.get("version", "V0"),
            accuracy=self.accuracy,
            reliability=self.reliability,
            total_cost_usd=self.total_cost_usd,
            avg_cost_usd=round(self.total_cost_usd / self.total_cases, 6) if self.total_cases > 0 else 0.0,
            cost_type="actual" if "actual" in str(self.metadata.get("cost_type", "actual")) else ("estimated" if "estimated" in str(self.metadata.get("cost_type", "")) else "simulated_mock"),
            total_latency_ms=self.total_latency_ms,
            avg_latency_ms=self.avg_latency_ms,
            total_cases=self.total_cases,
            passed_cases=self.passed_cases,
            failed_cases=self.failed_cases,
            passed=(self.accuracy >= 0.70),
            execution_metadata=self.metadata,
        )
