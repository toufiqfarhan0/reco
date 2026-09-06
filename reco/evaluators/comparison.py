"""Multi-dimensional scorecard comparison, dominance rules, and promotion assessment engine.

Deterministic, multi-axis evaluation:
- Accuracy: Higher is better
- Reliability: Higher is better
- Cost: Lower is better
- Speed / Latency: Lower is better
"""

from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from reco.evaluators.scorecard import Scorecard


class ComparisonPolicy(BaseModel):
    """Configurable decision policy governing multi-dimensional dominance and promotion rules."""
    tolerance_eps: float = Field(
        default=0.0001,
        ge=0.0,
        description="Numerical noise threshold below which metric changes are considered unchanged",
    )
    min_accuracy_gain: float = Field(
        default=0.0,
        description="Minimum accuracy gain required for positive advancement",
    )
    require_non_regressive_reliability: bool = Field(
        default=True,
        description="If True, any decrease in reliability immediately disqualifies promotion",
    )
    max_acceptable_cost_increase_pct: float = Field(
        default=0.0,
        ge=0.0,
        description="Allowable cost increase percentage (0.0 = zero cost regression permitted)",
    )
    max_acceptable_latency_increase_pct: float = Field(
        default=0.0,
        ge=0.0,
        description="Allowable latency increase percentage (0.0 = zero speed regression permitted)",
    )
    allow_tradeoffs: bool = Field(
        default=False,
        description="Whether Pareto tradeoffs within allowable thresholds can be recommended for promotion",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class DimensionDelta(BaseModel):
    """Detailed change breakdown along a single performance dimension."""
    dimension: str = Field(..., description="'accuracy', 'reliability', 'cost', 'speed'")
    baseline_value: float
    candidate_value: float
    raw_delta: float = Field(..., description="candidate_value - baseline_value")
    percentage_change: float = Field(..., description="Percentage change relative to baseline")
    direction: Literal["higher_is_better", "lower_is_better"]
    status: Literal["improved", "regressed", "unchanged"]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ScorecardComparison(BaseModel):
    """Structured multi-dimensional comparison between baseline and candidate scorecards."""
    baseline_agent_version_id: Optional[UUID] = None
    candidate_agent_version_id: Optional[UUID] = None
    benchmark_name: str
    benchmark_version: str
    split: str

    # Raw Deltas
    accuracy_delta: float = Field(..., description="Candidate accuracy - Baseline accuracy")
    reliability_delta: float = Field(..., description="Candidate reliability - Baseline reliability")
    cost_delta: float = Field(..., description="Candidate avg cost - Baseline avg cost")
    cost_total_delta: float = Field(..., description="Candidate total cost - Baseline total cost")
    latency_delta: float = Field(..., description="Candidate avg latency - Baseline avg latency")
    latency_total_delta: float = Field(..., description="Candidate total latency - Baseline total latency")

    # Relative Changes (%)
    relative_changes: Dict[str, float] = Field(default_factory=dict)
    dimensions: Dict[str, DimensionDelta] = Field(default_factory=dict)

    # Classifications
    improved_dimensions: List[str] = Field(default_factory=list)
    regressed_dimensions: List[str] = Field(default_factory=list)
    unchanged_dimensions: List[str] = Field(default_factory=list)
    relationship: Literal["strictly_better", "strictly_worse", "tradeoff", "equivalent"]

    # Deterministic Narrative
    summary: str = Field(..., description="Deterministic human-readable improvement summary")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PromotionAssessment(BaseModel):
    """Structured assessment ready for promotion gating."""
    decision: Literal["promote", "reject", "review"]
    reasons: List[str] = Field(default_factory=list)
    scorecard_before: Scorecard
    scorecard_after: Scorecard
    comparison: ScorecardComparison
    improved_dimensions: List[str]
    regressed_dimensions: List[str]
    held_out_required: bool = Field(
        ...,
        description="True if evaluation was run on optimization split and requires held-out validation",
    )
    split: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def promoted(self) -> bool:
        """Convenience boolean indicator for promotion approval."""
        return self.decision == "promote"


def format_improvement_summary(comparison: ScorecardComparison) -> str:
    """Generate a deterministic, human-readable narrative summary from calculated metrics.

    Does NOT use an LLM.
    """
    parts = []

    # 1. Accuracy (higher is better, reported in percentage points)
    acc_diff_pp = round(comparison.accuracy_delta * 100, 2)
    acc_base = round(comparison.dimensions["accuracy"].baseline_value * 100, 2)
    acc_cand = round(comparison.dimensions["accuracy"].candidate_value * 100, 2)
    if comparison.dimensions["accuracy"].status == "improved":
        parts.append(f"Accuracy improved by +{acc_diff_pp} percentage points ({acc_base}% -> {acc_cand}%)")
    elif comparison.dimensions["accuracy"].status == "regressed":
        parts.append(f"Accuracy regressed by {acc_diff_pp} percentage points ({acc_base}% -> {acc_cand}%)")
    else:
        parts.append(f"Accuracy remained unchanged at {acc_base}%")

    # 2. Reliability (higher is better, reported in percentage points)
    rel_diff_pp = round(comparison.reliability_delta * 100, 2)
    rel_base = round(comparison.dimensions["reliability"].baseline_value * 100, 2)
    rel_cand = round(comparison.dimensions["reliability"].candidate_value * 100, 2)
    if comparison.dimensions["reliability"].status == "improved":
        parts.append(f"reliability improved by +{rel_diff_pp} percentage points ({rel_base}% -> {rel_cand}%)")
    elif comparison.dimensions["reliability"].status == "regressed":
        parts.append(f"reliability regressed by {rel_diff_pp} percentage points ({rel_base}% -> {rel_cand}%)")
    else:
        parts.append(f"reliability remained unchanged at {rel_base}%")

    # 3. Cost (lower is better, reported in relative percentage)
    cost_dim = comparison.dimensions["cost"]
    cost_base = cost_dim.baseline_value
    cost_cand = cost_dim.candidate_value
    cost_pct = abs(cost_dim.percentage_change)
    if cost_dim.status == "improved":
        parts.append(f"average cost decreased by {cost_pct:.1f}% (${cost_base:.6f} -> ${cost_cand:.6f})")
    elif cost_dim.status == "regressed":
        parts.append(f"average cost increased by {cost_pct:.1f}% (${cost_base:.6f} -> ${cost_cand:.6f})")
    else:
        parts.append(f"average cost remained unchanged at ${cost_base:.6f}")

    # 4. Latency / Speed (lower is better, reported in relative percentage)
    lat_dim = comparison.dimensions["speed"]
    lat_base = int(lat_dim.baseline_value)
    lat_cand = int(lat_dim.candidate_value)
    lat_pct = abs(lat_dim.percentage_change)
    if lat_dim.status == "improved":
        parts.append(f"average latency decreased by {lat_pct:.1f}% ({lat_base}ms -> {lat_cand}ms)")
    elif lat_dim.status == "regressed":
        parts.append(f"average latency increased by {lat_pct:.1f}% ({lat_base}ms -> {lat_cand}ms)")
    else:
        parts.append(f"average latency remained unchanged at {lat_base}ms")

    return ", ".join(parts) + "."


def compare_scorecards(
    baseline: Scorecard,
    candidate: Scorecard,
    policy: Optional[ComparisonPolicy] = None,
) -> ScorecardComparison:
    """Compare two scorecards across Accuracy, Reliability, Cost, and Latency deterministically.

    Directionality:
    - Accuracy: higher is better
    - Reliability: higher is better
    - Cost: lower is better
    - Latency (Speed): lower is better
    """
    pol = policy or ComparisonPolicy()
    eps = pol.tolerance_eps

    # Accuracy (higher is better)
    acc_delta = candidate.accuracy - baseline.accuracy
    acc_pct = ((acc_delta / baseline.accuracy) * 100) if baseline.accuracy > 0 else 0.0
    if acc_delta > eps:
        acc_status = "improved"
    elif acc_delta < -eps:
        acc_status = "regressed"
    else:
        acc_status = "unchanged"

    acc_dim = DimensionDelta(
        dimension="accuracy",
        baseline_value=baseline.accuracy,
        candidate_value=candidate.accuracy,
        raw_delta=round(acc_delta, 6),
        percentage_change=round(acc_pct, 2),
        direction="higher_is_better",
        status=acc_status,
    )

    # Reliability (higher is better)
    rel_delta = candidate.reliability - baseline.reliability
    rel_pct = ((rel_delta / baseline.reliability) * 100) if baseline.reliability > 0 else 0.0
    if rel_delta > eps:
        rel_status = "improved"
    elif rel_delta < -eps:
        rel_status = "regressed"
    else:
        rel_status = "unchanged"

    rel_dim = DimensionDelta(
        dimension="reliability",
        baseline_value=baseline.reliability,
        candidate_value=candidate.reliability,
        raw_delta=round(rel_delta, 6),
        percentage_change=round(rel_pct, 2),
        direction="higher_is_better",
        status=rel_status,
    )

    # Cost (lower is better, using micro-dollar precision for epsilon)
    cost_eps = min(eps, 1e-6)
    cost_delta = candidate.avg_cost_usd - baseline.avg_cost_usd
    cost_total_delta = candidate.total_cost_usd - baseline.total_cost_usd
    cost_pct = ((cost_delta / baseline.avg_cost_usd) * 100) if baseline.avg_cost_usd > 0 else 0.0
    if cost_delta < -cost_eps:
        cost_status = "improved"  # Cost went down
    elif cost_delta > cost_eps:
        cost_status = "regressed"  # Cost went up
    else:
        cost_status = "unchanged"

    cost_dim = DimensionDelta(
        dimension="cost",
        baseline_value=baseline.avg_cost_usd,
        candidate_value=candidate.avg_cost_usd,
        raw_delta=round(cost_delta, 6),
        percentage_change=round(cost_pct, 2),
        direction="lower_is_better",
        status=cost_status,
    )

    # Speed / Latency (lower is better)
    lat_delta = candidate.avg_latency_ms - baseline.avg_latency_ms
    lat_total_delta = candidate.total_latency_ms - baseline.total_latency_ms
    lat_pct = ((lat_delta / baseline.avg_latency_ms) * 100) if baseline.avg_latency_ms > 0 else 0.0
    if lat_delta < -eps:
        lat_status = "improved"  # Latency went down (faster)
    elif lat_delta > eps:
        lat_status = "regressed"  # Latency went up (slower)
    else:
        lat_status = "unchanged"

    lat_dim = DimensionDelta(
        dimension="speed",
        baseline_value=float(baseline.avg_latency_ms),
        candidate_value=float(candidate.avg_latency_ms),
        raw_delta=float(lat_delta),
        percentage_change=round(lat_pct, 2),
        direction="lower_is_better",
        status=lat_status,
    )

    dims = {
        "accuracy": acc_dim,
        "reliability": rel_dim,
        "cost": cost_dim,
        "speed": lat_dim,
    }

    improved = [d for d, dim_obj in dims.items() if dim_obj.status == "improved"]
    regressed = [d for d, dim_obj in dims.items() if dim_obj.status == "regressed"]
    unchanged = [d for d, dim_obj in dims.items() if dim_obj.status == "unchanged"]

    # Dominance classification
    if improved and not regressed:
        relationship = "strictly_better"
    elif regressed and not improved:
        relationship = "strictly_worse"
    elif improved and regressed:
        relationship = "tradeoff"
    else:
        relationship = "equivalent"

    comparison = ScorecardComparison(
        baseline_agent_version_id=baseline.agent_version_id,
        candidate_agent_version_id=candidate.agent_version_id,
        benchmark_name=candidate.benchmark_name,
        benchmark_version=candidate.benchmark_version,
        split=candidate.split,
        accuracy_delta=round(acc_delta, 6),
        reliability_delta=round(rel_delta, 6),
        cost_delta=round(cost_delta, 6),
        cost_total_delta=round(cost_total_delta, 6),
        latency_delta=lat_delta,
        latency_total_delta=lat_total_delta,
        relative_changes={
            "accuracy_pct": round(acc_pct, 2),
            "reliability_pct": round(rel_pct, 2),
            "cost_pct": round(cost_pct, 2),
            "speed_pct": round(lat_pct, 2),
        },
        dimensions=dims,
        improved_dimensions=improved,
        regressed_dimensions=regressed,
        unchanged_dimensions=unchanged,
        relationship=relationship,
        summary="",
    )

    comparison.summary = format_improvement_summary(comparison)
    return comparison


def assess_promotion(
    baseline: Scorecard,
    candidate: Scorecard,
    policy: Optional[ComparisonPolicy] = None,
) -> PromotionAssessment:
    """Evaluate candidate scorecard against baseline and produce a promotion assessment.

    Rules:
    1. Optimization Split:
       - If strictly better -> decision="review" with held_out_required=True
       - If strictly worse -> decision="reject"
       - If tradeoff/equivalent -> decision="review" / "reject"
    2. Held-Out Split:
       - If strictly better and non-regressive reliability -> decision="promote"
       - If strictly worse -> decision="reject"
       - If reliability drops -> decision="reject"
       - If tradeoff -> decision="review" (or promote if allowed by policy)
       - If equivalent -> decision="reject"
    """
    pol = policy or ComparisonPolicy()
    comparison = compare_scorecards(baseline, candidate, pol)
    reasons: List[str] = []

    is_optimization = candidate.split == "optimization"
    held_out_required = is_optimization

    # Check reliability non-regression constraint
    if pol.require_non_regressive_reliability and "reliability" in comparison.regressed_dimensions:
        decision = "reject"
        reasons.append(
            f"Reliability regressed from {baseline.reliability:.4f} to {candidate.reliability:.4f} "
            f"(-{abs(comparison.reliability_delta):.4f}). Reliable execution is non-negotiable."
        )
        return PromotionAssessment(
            decision=decision,
            reasons=reasons,
            scorecard_before=baseline,
            scorecard_after=candidate,
            comparison=comparison,
            improved_dimensions=comparison.improved_dimensions,
            regressed_dimensions=comparison.regressed_dimensions,
            held_out_required=held_out_required,
            split=candidate.split,
            metadata={"policy": pol.model_dump()},
        )

    if is_optimization:
        if comparison.relationship == "strictly_better":
            decision = "review"
            reasons.append(
                "Candidate achieved strict dominance on the optimization split. "
                "Held-out evaluation is required before final promotion can occur."
            )
        elif comparison.relationship == "strictly_worse":
            decision = "reject"
            reasons.append(
                f"Candidate regressed across {len(comparison.regressed_dimensions)} dimension(s) "
                f"({', '.join(comparison.regressed_dimensions)}) on optimization split."
            )
        elif comparison.relationship == "tradeoff":
            decision = "review"
            reasons.append(
                f"Tradeoff detected on optimization split: improved in ({', '.join(comparison.improved_dimensions)}), "
                f"but regressed in ({', '.join(comparison.regressed_dimensions)})."
            )
        else:  # equivalent
            decision = "reject"
            reasons.append("Candidate demonstrates zero measurable improvement over baseline.")

    else:
        # Held-out split (or full benchmark validation)
        if comparison.relationship == "strictly_better":
            decision = "promote"
            reasons.append(
                f"Candidate demonstrated strict multi-dimensional dominance on held-out split "
                f"across ({', '.join(comparison.improved_dimensions)}) without regressions."
            )
        elif comparison.relationship == "strictly_worse":
            decision = "reject"
            reasons.append(
                f"Candidate regressed across dimensions: {', '.join(comparison.regressed_dimensions)}."
            )
        elif comparison.relationship == "tradeoff":
            # Check if tradeoff is acceptable per policy
            cost_pct_change = comparison.dimensions["cost"].percentage_change
            lat_pct_change = comparison.dimensions["speed"].percentage_change
            cost_ok = cost_pct_change <= pol.max_acceptable_cost_increase_pct
            lat_ok = lat_pct_change <= pol.max_acceptable_latency_increase_pct
            acc_ok = comparison.accuracy_delta >= pol.min_accuracy_gain

            if pol.allow_tradeoffs and cost_ok and lat_ok and acc_ok:
                decision = "promote"
                reasons.append(
                    "Candidate promoted under acceptable tradeoff policy parameters "
                    f"(accuracy gain +{comparison.accuracy_delta:.4f}, cost change {cost_pct_change:+.1f}%, "
                    f"latency change {lat_pct_change:+.1f}%)."
                )
            else:
                decision = "review"
                reasons.append(
                    f"Tradeoff on held-out split requires review: improved in ({', '.join(comparison.improved_dimensions)}) "
                    f"but regressed in ({', '.join(comparison.regressed_dimensions)})."
                )
        else:  # equivalent
            decision = "reject"
            reasons.append("Candidate demonstrates zero measurable improvement on held-out split.")

    return PromotionAssessment(
        decision=decision,
        reasons=reasons,
        scorecard_before=baseline,
        scorecard_after=candidate,
        comparison=comparison,
        improved_dimensions=comparison.improved_dimensions,
        regressed_dimensions=comparison.regressed_dimensions,
        held_out_required=held_out_required,
        split=candidate.split,
        metadata={"policy": pol.model_dump()},
    )
