"""4-Axis Scorecard Engine: Accuracy, Reliability, Cost, and Speed evaluation.

Provides deterministic evaluation of agent architectures and side-by-side
comparisons with delta badges, Pareto dominance detection, and tradeoff flagging.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from reco.benchmarks.base import BenchmarkCase, BenchmarkSplit, BenchmarkSuite
from reco.benchmarks.reconciliation.dataset import get_reconciliation_benchmark_suite
from reco.core.goal_analyzer import GoalAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import AgentArchitecture, NodeStatus
from reco.engine.runtime import AgentRuntime, ExecutionResult


class CaseEvaluationResult(BaseModel):
    """Detailed evaluation telemetry for a single benchmark test case."""

    case_id: str = Field(description="Unique benchmark case identifier")
    split: str = Field(description="Partition split of the test case")
    is_accurate: bool = Field(description="True if output matches ground truth")
    is_reliable: bool = Field(description="True if execution had no exceptions/errors")
    cost_usd: float = Field(default=0.0, description="Inference/tool cost for this case in USD")
    latency_ms: float = Field(default=0.0, description="Wall-clock latency in milliseconds")
    error: Optional[str] = Field(default=None, description="Error detail if execution failed")
    actual_output: Any = Field(default=None, description="Actual output payload produced")
    expected_output: Any = Field(default=None, description="Expected ground-truth criteria")


class Scorecard(BaseModel):
    """4-Axis empirical scorecard measuring agent performance."""

    name: str = Field(description="Architecture or benchmark run identifier")
    split: str = Field(description="Evaluated partition split ('optimization', 'held-out', or 'full')")
    total_cases: int = Field(description="Total number of evaluated test cases")
    accurate_cases: int = Field(description="Number of cases matching ground-truth output")
    reliable_cases: int = Field(description="Number of cases executing without runtime exceptions")

    # Canonical 4 Axes
    accuracy: float = Field(
        description="Axis 1: Fraction of cases matching ground-truth output (0.0 to 1.0)"
    )
    reliability: float = Field(
        description="Axis 2: Fraction of cases executed without exceptions or tool errors (0.0 to 1.0)"
    )
    cost_usd: float = Field(
        description="Axis 3: Exact token-derived inference cost or deterministic $0 tool cost in USD"
    )
    latency_ms: float = Field(
        description="Axis 4: Total wall-clock execution time in milliseconds"
    )

    avg_latency_ms: float = Field(default=0.0, description="Average wall-clock latency per case (ms)")
    latency_s: float = Field(default=0.0, description="Total wall-clock execution time in seconds")
    case_results: List[CaseEvaluationResult] = Field(default_factory=list, description="Per-case evaluation breakdown")

    def summary_dict(self) -> Dict[str, Any]:
        """Return a structured dictionary of core metrics."""
        return {
            "name": self.name,
            "split": self.split,
            "total_cases": self.total_cases,
            "accuracy": round(self.accuracy, 4),
            "reliability": round(self.reliability, 4),
            "cost_usd": round(self.cost_usd, 6),
            "latency_ms": round(self.latency_ms, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "latency_s": round(self.latency_s, 4),
        }

    def to_markdown(self) -> str:
        """Render a readable markdown summary table of the 4 canonical axes."""
        acc_pct = f"{self.accuracy * 100:.1f}%"
        rel_pct = f"{self.reliability * 100:.1f}%"
        cost_str = f"${self.cost_usd:.4f}"
        lat_str = f"{self.latency_ms:.2f} ms ({self.latency_s:.4f} s, avg {self.avg_latency_ms:.2f} ms/case)"

        lines = [
            f"### 4-Axis Scorecard: {self.name} (Split: {self.split.upper()})",
            f"Evaluated {self.total_cases} benchmark test cases.",
            "",
            "| Axis | Metric | Value | Detail |",
            "| :--- | :--- | :--- | :--- |",
            f"| **1. Accuracy** | Ground-Truth Match Rate | **{acc_pct}** | {self.accurate_cases}/{self.total_cases} cases passed |",
            f"| **2. Reliability** | Error-Free Execution Rate | **{rel_pct}** | {self.reliable_cases}/{self.total_cases} cases passed |",
            f"| **3. Cost** | Inference & Tool Cost | **{cost_str}** | Deterministic / token-derived |",
            f"| **4. Speed** | Wall-Clock Latency | **{self.latency_ms:.2f} ms** | Total: {lat_str} |",
            ""
        ]
        return "\n".join(lines)


class ScorecardComparison(BaseModel):
    """Side-by-side comparison between baseline and candidate architectures across all 4 axes."""

    baseline_name: str
    candidate_name: str
    split: str
    baseline_scorecard: Scorecard
    candidate_scorecard: Scorecard

    # Metric Deltas (Candidate - Baseline)
    accuracy_delta: float = Field(description="Δ Accuracy (candidate - baseline)")
    reliability_delta: float = Field(description="Δ Reliability (candidate - baseline)")
    cost_delta_usd: float = Field(description="Δ Cost in USD (candidate - baseline)")
    latency_delta_ms: float = Field(description="Δ Latency in milliseconds (candidate - baseline)")
    latency_pct_delta: float = Field(description="Percentage change in latency")

    # Delta Badges
    accuracy_badge: str = Field(description="Formatted delta badge for accuracy")
    reliability_badge: str = Field(description="Formatted delta badge for reliability")
    cost_badge: str = Field(description="Formatted delta badge for cost")
    latency_badge: str = Field(description="Formatted delta badge for latency")

    # Multi-Axis Pareto & Tradeoff Assessments
    is_pareto_dominant: bool = Field(
        description="True if candidate improves on >=1 axis with zero regressions on any axis"
    )
    has_tradeoff: bool = Field(
        description="True if candidate improves on >=1 axis but regresses on another"
    )
    tradeoffs: List[str] = Field(default_factory=list, description="Descriptive list of flagged tradeoffs")
    verdict: str = Field(
        description="Summary decision: 'PARETO_DOMINANT', 'TRADEOFF', 'REGRESSION', or 'NEUTRAL'"
    )

    def to_markdown(self) -> str:
        """Render an executive side-by-side comparison table with delta badges."""
        lines = [
            f"### Scorecard Comparison: {self.candidate_name} vs {self.baseline_name} (Split: {self.split.upper()})",
            f"**Verdict:** `{self.verdict}`"
            + (" (Pareto Dominant: improves without regression)" if self.is_pareto_dominant else ""),
            "",
            "| Axis | Baseline | Candidate | Delta | Badge | Assessment |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
            f"| **Accuracy** | {self.baseline_scorecard.accuracy * 100:.1f}% | {self.candidate_scorecard.accuracy * 100:.1f}% | {self.accuracy_delta * 100:+.1f}% | `{self.accuracy_badge}` | {self._assess_axis('accuracy')} |",
            f"| **Reliability** | {self.baseline_scorecard.reliability * 100:.1f}% | {self.candidate_scorecard.reliability * 100:.1f}% | {self.reliability_delta * 100:+.1f}% | `{self.reliability_badge}` | {self._assess_axis('reliability')} |",
            f"| **Cost (USD)** | ${self.baseline_scorecard.cost_usd:.4f} | ${self.candidate_scorecard.cost_usd:.4f} | {self.cost_delta_usd:+.4f} | `{self.cost_badge}` | {self._assess_axis('cost')} |",
            f"| **Speed (ms)** | {self.baseline_scorecard.latency_ms:.2f} ms | {self.candidate_scorecard.latency_ms:.2f} ms | {self.latency_delta_ms:+.2f} ms | `{self.latency_badge}` | {self._assess_axis('speed')} |",
            ""
        ]

        if self.tradeoffs:
            lines.append("**Flagged Tradeoffs:**")
            for t in self.tradeoffs:
                lines.append(f"- [Tradeoff] {t}")
            lines.append("")

        return "\n".join(lines)

    def _assess_axis(self, axis: str) -> str:
        if axis == "accuracy":
            if self.accuracy_delta > 1e-4:
                return "[Improved]"
            elif self.accuracy_delta < -1e-4:
                return "[Regressed]"
            return "[Equal]"
        elif axis == "reliability":
            if self.reliability_delta > 1e-4:
                return "[Improved]"
            elif self.reliability_delta < -1e-4:
                return "[Regressed]"
            return "[Equal]"
        elif axis == "cost":
            if self.cost_delta_usd < -1e-5:
                return "[Cheaper]"
            elif self.cost_delta_usd > 1e-5:
                return "[More Expensive]"
            return "[Equal]"
        elif axis == "speed":
            if self.latency_delta_ms < -0.1:
                return "[Faster]"
            elif self.latency_delta_ms > 0.1:
                return "[Slower]"
            return "[Equal]"
        return "[Equal]"


class ScorecardEvaluator:
    """Evaluates agent architectures on partitioned benchmark suites across all 4 canonical axes."""

    def __init__(
        self,
        runtime: Optional[AgentRuntime] = None,
        cost_per_case_usd: float = 0.0
    ):
        self.runtime = runtime or AgentRuntime()
        self.cost_per_case_usd = cost_per_case_usd

    def evaluate(
        self,
        architecture: AgentArchitecture,
        suite_or_cases: Union[BenchmarkSuite, List[BenchmarkCase]],
        split: Optional[Union[BenchmarkSplit, str]] = None,
        name: Optional[str] = None
    ) -> Scorecard:
        """Execute benchmark cases and synthesize a 4-axis scorecard.

        Args:
            architecture: The agent DAG architecture to evaluate.
            suite_or_cases: A BenchmarkSuite or a list of BenchmarkCase objects.
            split: Optional partition filter ('optimization' or 'held-out').
            name: Optional descriptive label for the scorecard.

        Returns:
            Computed Scorecard with Accuracy, Reliability, Cost, and Latency metrics.
        """
        # Resolve cases based on split filter
        if isinstance(suite_or_cases, BenchmarkSuite):
            if split:
                cases = suite_or_cases.get_split(split)
                split_label = split if isinstance(split, str) else split.value
            else:
                cases = suite_or_cases.cases
                split_label = "full"
        else:
            if split:
                norm_split = BenchmarkSplit.OPTIMIZATION if str(split).lower() in ("optimization", "opt") else BenchmarkSplit.HELD_OUT
                cases = [c for c in suite_or_cases if c.split == norm_split]
                split_label = norm_split.value
            else:
                cases = suite_or_cases
                split_label = cases[0].split.value if cases else "unknown"

        if not cases:
            raise ValueError(f"No benchmark test cases available to evaluate for split '{split_label}'.")

        run_name = name or architecture.name or architecture.id
        case_results: List[CaseEvaluationResult] = []

        total_latency_ms = 0.0
        total_cost_usd = 0.0

        for case in cases:
            case_start = time.perf_counter()
            exec_result = self.runtime.execute(architecture, case.input_data)
            case_elapsed_ms = (time.perf_counter() - case_start) * 1000.0

            # 1. Reliability: No runtime crash and no failed nodes
            no_runtime_error = exec_result.status == NodeStatus.COMPLETED and exec_result.error is None
            no_node_failures = not any(r.status == NodeStatus.FAILED for r in exec_result.node_records.values())
            is_reliable = no_runtime_error and no_node_failures

            # 2. Accuracy: Ground-truth match
            is_accurate = False
            if is_reliable:
                is_accurate = case.eval_match(exec_result.final_output)

            # 3. Cost: exact token/tool cost or deterministic $0
            case_cost = getattr(exec_result, "total_cost_usd", 0.0) + self.cost_per_case_usd

            # 4. Latency
            case_latency = exec_result.total_latency_ms if exec_result.total_latency_ms > 0 else case_elapsed_ms
            total_latency_ms += case_latency
            total_cost_usd += case_cost

            case_results.append(CaseEvaluationResult(
                case_id=case.case_id,
                split=case.split.value,
                is_accurate=is_accurate,
                is_reliable=is_reliable,
                cost_usd=round(case_cost, 6),
                latency_ms=round(case_latency, 3),
                error=exec_result.error,
                actual_output=exec_result.final_output,
                expected_output=case.expected_output
            ))

        total_count = len(cases)
        accurate_count = sum(1 for r in case_results if r.is_accurate)
        reliable_count = sum(1 for r in case_results if r.is_reliable)

        accuracy = accurate_count / total_count
        reliability = reliable_count / total_count
        avg_latency_ms = total_latency_ms / total_count

        return Scorecard(
            name=run_name,
            split=split_label,
            total_cases=total_count,
            accurate_cases=accurate_count,
            reliable_cases=reliable_count,
            accuracy=round(accuracy, 4),
            reliability=round(reliability, 4),
            cost_usd=round(total_cost_usd, 6),
            latency_ms=round(total_latency_ms, 2),
            avg_latency_ms=round(avg_latency_ms, 2),
            latency_s=round(total_latency_ms / 1000.0, 4),
            case_results=case_results
        )

    def compare(self, baseline: Scorecard, candidate: Scorecard) -> ScorecardComparison:
        """Perform side-by-side 4-axis scorecard comparison between baseline and candidate.

        Calculates delta badges, verifies Pareto dominance, and flags trade-offs.

        Args:
            baseline: Baseline Scorecard (e.g. V0).
            candidate: Candidate Scorecard (e.g. mutated/optimized architecture).

        Returns:
            ScorecardComparison instance.
        """
        # 1. Calculate deltas
        acc_delta = candidate.accuracy - baseline.accuracy
        rel_delta = candidate.reliability - baseline.reliability
        cost_delta = candidate.cost_usd - baseline.cost_usd
        lat_delta = candidate.latency_ms - baseline.latency_ms

        lat_pct = (lat_delta / baseline.latency_ms * 100.0) if baseline.latency_ms > 0 else 0.0

        # 2. Compute formatted badges
        # Accuracy badge
        acc_badge = f"{acc_delta * 100:+.1f}%"
        # Reliability badge
        rel_badge = f"{rel_delta * 100:+.1f}%"

        # Cost badge (negative is better / green)
        if abs(cost_delta) < 1e-6:
            cost_badge = "$0.0000"
        elif cost_delta > 0:
            cost_badge = f"+${cost_delta:.4f}"
        else:
            cost_badge = f"-${abs(cost_delta):.4f}"

        # Latency badge (negative is better / faster)
        lat_badge = f"{lat_delta:+.2f}ms ({lat_pct:+.1f}%)"

        # 3. Assess improvements & regressions per axis
        # Accuracy: higher is better
        acc_improved = acc_delta > 1e-4
        acc_regressed = acc_delta < -1e-4

        # Reliability: higher is better
        rel_improved = rel_delta > 1e-4
        rel_regressed = rel_delta < -1e-4

        # Cost: lower is better
        cost_improved = cost_delta < -1e-5
        cost_regressed = cost_delta > 1e-5

        # Speed: lower latency is better
        speed_improved = lat_delta < -0.1
        speed_regressed = lat_delta > 0.1

        improved_any = acc_improved or rel_improved or cost_improved or speed_improved
        regressed_any = acc_regressed or rel_regressed or cost_regressed or speed_regressed

        # 4. Pareto dominance & Tradeoff identification
        is_pareto = improved_any and not regressed_any
        has_tradeoff = improved_any and regressed_any

        tradeoffs: List[str] = []
        if acc_improved and speed_regressed:
            tradeoffs.append(
                f"+{acc_delta * 100:.1f}% accuracy gain at cost of +{lat_pct:.1f}% latency increase (+{lat_delta:.2f}ms)"
            )
        if acc_improved and cost_regressed:
            tradeoffs.append(
                f"+{acc_delta * 100:.1f}% accuracy gain with higher inference cost (+${cost_delta:.4f})"
            )
        if speed_improved and acc_regressed:
            tradeoffs.append(
                f"{lat_pct:.1f}% faster latency with {acc_delta * 100:.1f}% accuracy degradation"
            )
        if rel_improved and speed_regressed:
            tradeoffs.append(
                f"+{rel_delta * 100:.1f}% reliability improvement with +{lat_pct:.1f}% latency increase"
            )
        if cost_improved and acc_regressed:
            tradeoffs.append(
                f"-${abs(cost_delta):.4f} cost reduction with {acc_delta * 100:.1f}% accuracy loss"
            )

        # Verdict
        if is_pareto:
            verdict = "PARETO_DOMINANT"
        elif has_tradeoff:
            verdict = "TRADEOFF"
        elif regressed_any:
            verdict = "REGRESSION"
        else:
            verdict = "NEUTRAL"

        return ScorecardComparison(
            baseline_name=baseline.name,
            candidate_name=candidate.name,
            split=baseline.split,
            baseline_scorecard=baseline,
            candidate_scorecard=candidate,
            accuracy_delta=round(acc_delta, 4),
            reliability_delta=round(rel_delta, 4),
            cost_delta_usd=round(cost_delta, 6),
            latency_delta_ms=round(lat_delta, 2),
            latency_pct_delta=round(lat_pct, 2),
            accuracy_badge=acc_badge,
            reliability_badge=rel_badge,
            cost_badge=cost_badge,
            latency_badge=lat_badge,
            is_pareto_dominant=is_pareto,
            has_tradeoff=has_tradeoff,
            tradeoffs=tradeoffs,
            verdict=verdict
        )


def run_v0_benchmark(
    split: Union[BenchmarkSplit, str] = BenchmarkSplit.OPTIMIZATION,
    runtime: Optional[AgentRuntime] = None
) -> Scorecard:
    """Execute the V0 baseline DAG through the partitioned benchmark split and compute the scorecard.

    Args:
        split: Partition split to evaluate on (defaults to 'optimization').
        runtime: Optional AgentRuntime instance.

    Returns:
        Scorecard representing initial V0 baseline performance.
    """
    suite = get_reconciliation_benchmark_suite()
    analyzer = GoalAnalyzer()
    spec = analyzer.analyze("Reconcile financial transaction ledgers, match records, and detect discrepancies")

    generator = ArchitectureGenerator()
    v0_architecture = generator.generate(spec, architecture_name="Agent_Reconciliation_V0")

    evaluator = ScorecardEvaluator(runtime=runtime)
    scorecard = evaluator.evaluate(
        architecture=v0_architecture,
        suite_or_cases=suite,
        split=split,
        name="V0_Baseline_Reconciliation"
    )
    return scorecard
