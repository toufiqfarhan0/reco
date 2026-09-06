"""Data models for Research & Evidence Comparison benchmark (Domain C)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from reco.core.interfaces import BenchmarkCase
from reco.evaluators.scorecard import Scorecard


class DocumentArticle(BaseModel):
    """Synthetic evidence document."""
    id: str
    title: str
    source_type: str  # "independent_benchmark", "vendor_marketing", "pricing_catalog"
    content: str


class ResearchGroundTruth(BaseModel):
    """Ground truth decision criteria for a research scenario."""
    recommended_technology: str
    required_facts: List[str] = Field(default_factory=list, description="Mandatory factual claims that must be cited")
    rejected_technologies: List[str] = Field(default_factory=list, description="Technologies that must be disqualified")
    contradiction_resolution: Optional[str] = Field(default=None, description="Explanation of how conflicting marketing vs benchmark was resolved")

    @property
    def contradictions_resolved(self) -> List[str]:
        if self.contradiction_resolution:
            return [self.contradiction_resolution]
        return []


class ResearchCase(BaseModel):
    """A research and evidence evaluation benchmark case."""
    case_code: str
    name: str
    description: str
    split: str = "optimization"  # "optimization" or "held_out"
    task_goal: str
    constraints: Dict[str, Any]
    candidate_technologies: List[str]
    documents: List[DocumentArticle]
    ground_truth: ResearchGroundTruth
    difficulty: str = "medium"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_benchmark_case(self) -> BenchmarkCase:
        return BenchmarkCase(
            case_code=self.case_code,
            split=self.split,
            input_data={
                "task_goal": self.task_goal,
                "constraints": self.constraints,
                "candidate_technologies": self.candidate_technologies,
                "documents": [d.model_dump(mode="json") for d in self.documents],
            },
            ground_truth={
                "recommended_technology": self.ground_truth.recommended_technology,
                "required_facts": self.ground_truth.required_facts,
            },
        )


from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResearchCaseEvaluationResult(BaseModel):
    """Evaluation outcome of an agent execution on a research case."""
    case_code: str
    split: str = "optimization"
    success: bool = False
    accuracy_score: float = 0.0
    recommendation_match: bool = False
    fact_coverage_score: float = 0.0
    contradiction_resolved: bool = False
    recommended_tech: Optional[str] = None
    expected_tech: str = ""
    missing_facts: List[str] = Field(default_factory=list)
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
            if "recommendation_match" not in data and "recommendation_correct" in data:
                data["recommendation_match"] = data["recommendation_correct"]
            if "recommended_tech" not in data and "recommended_technology" in data:
                data["recommended_tech"] = data["recommended_technology"]
            if "expected_tech" not in data and "expected_technology" in data:
                data["expected_tech"] = data["expected_technology"]
        return data

    @property
    def accuracy(self) -> float:
        return self.accuracy_score

    @property
    def is_passed(self) -> bool:
        return self.success

    @property
    def recommendation_correct(self) -> bool:
        return self.recommendation_match


class ResearchRunResult(BaseModel):
    """Aggregated outcome of running the Research benchmark across a split."""
    benchmark_name: str = "research_comparison"
    benchmark_version: str = "research_comparison-v1"
    split: str
    total_cases: int
    passed_cases: int
    failed_cases: int = 0
    accuracy: float = 0.0
    reliability: float = 1.0
    total_cost_usd: float = 0.0
    avg_latency_ms: int = 0
    total_latency_ms: int = 0
    case_results: List[ResearchCaseEvaluationResult] = Field(default_factory=list)
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
            passed=(self.accuracy >= 0.50),
            execution_metadata=self.metadata,
        )
