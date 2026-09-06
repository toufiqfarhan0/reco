"""Closed-Loop Autonomous Learning & Optimization Controller.

Connects the loop:
Baseline V0 -> Benchmark -> Failure Diagnostics -> Mutation Engine -> Mutated Candidate V1.
Demonstrating measurable, verifiable empirical improvement across benchmark splits.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from reco.benchmarks.base import BenchmarkCase, BenchmarkSplit, BenchmarkSuite
from reco.benchmarks.reconciliation.dataset import get_reconciliation_benchmark_suite
from reco.core.goal_analyzer import GoalAnalyzer
from reco.diagnostics.analyzer import FailureAnalyzer
from reco.diagnostics.taxonomy import DiagnosticReport
from reco.engine.generator import ArchitectureGenerator
from reco.engine.models import AgentArchitecture
from reco.engine.runtime import AgentRuntime
from reco.evaluators.scorecard import Scorecard, ScorecardComparison, ScorecardEvaluator
from reco.mutation.engine import MutationEngine, MutationResult
from reco.mutation.validator import CandidateDiff, CandidateValidator
from reco.tools.registry import ToolRegistry


class OptimizationIteration(BaseModel):
    """Detailed record of a single closed-loop iteration step."""

    iteration: int = Field(description="Iteration counter (0-indexed)")
    architecture_id: str = Field(description="Architecture ID evaluated")
    architecture_name: str = Field(description="Architecture label")
    scorecard: Scorecard = Field(description="Evaluated 4-axis scorecard")
    diagnostic_report: Optional[DiagnosticReport] = Field(
        default=None,
        description="Diagnosed failure telemetry if failures occurred"
    )
    mutation_result: Optional[MutationResult] = Field(
        default=None,
        description="Mutation transformation applied to create next candidate"
    )


class OptimizationResult(BaseModel):
    """Aggregated outcome of an autonomous optimization loop execution."""

    baseline_architecture: AgentArchitecture
    candidate_architecture: AgentArchitecture
    baseline_scorecard: Scorecard
    candidate_scorecard: Scorecard
    scorecard_comparison: ScorecardComparison
    diagnostic_report: DiagnosticReport
    candidate_diff: CandidateDiff
    iterations: List[OptimizationIteration] = Field(default_factory=list)
    has_improved: bool = Field(description="True if candidate achieved measurable empirical gains")
    accuracy_gain: float = Field(description="Δ Accuracy achieved by the candidate")
    status: str = Field(description="Outcome status: 'OPTIMIZED', 'CONVERGED', or 'FAILED'")
    summary: str = Field(description="Executive summary of the optimization cycle")

    def to_markdown(self) -> str:
        """Render a comprehensive markdown report of the closed-loop optimization cycle."""
        lines = [
            "# Autonomous Agent Optimization Report (Track 1)",
            f"**Status:** `{self.status}` | **Empirical Gain:** `{self.accuracy_gain * 100:+.1f}%` Accuracy",
            "",
            "## 1. Closed-Loop Optimization Summary",
            self.summary,
            "",
            "## 2. Empirical Scorecard Comparison",
            self.scorecard_comparison.to_markdown(),
            "",
            "## 3. Failure Diagnostics (Root Causes Identified in Baseline)",
            self.diagnostic_report.to_markdown(),
            "",
            "## 4. Architectural Mutation Diff (Baseline -> Candidate)",
            self.candidate_diff.to_markdown(),
            "",
            "```",
            self.candidate_diff.to_visual_diff(),
            "```",
            ""
        ]
        return "\n".join(lines)


class OptimizationController:
    """Orchestrates closed-loop architecture optimization via diagnostics and targeted mutations."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        runtime: Optional[AgentRuntime] = None,
        evaluator: Optional[ScorecardEvaluator] = None,
        analyzer: Optional[FailureAnalyzer] = None,
        mutation_engine: Optional[MutationEngine] = None,
        validator: Optional[CandidateValidator] = None
    ):
        self.tool_registry = tool_registry or ToolRegistry.create_reconciliation_default()
        self.runtime = runtime or AgentRuntime(tool_registry=self.tool_registry)
        self.evaluator = evaluator or ScorecardEvaluator(runtime=self.runtime)
        self.analyzer = analyzer or FailureAnalyzer(tool_registry=self.tool_registry)
        self.validator = validator or CandidateValidator(tool_registry=self.tool_registry)
        self.mutation_engine = mutation_engine or MutationEngine(
            tool_registry=self.tool_registry,
            validator=self.validator
        )

    def run_optimization_cycle(
        self,
        baseline_architecture: Optional[AgentArchitecture] = None,
        suite: Optional[BenchmarkSuite] = None,
        split: Union[BenchmarkSplit, str] = BenchmarkSplit.OPTIMIZATION,
        max_iterations: int = 1
    ) -> OptimizationResult:
        """Execute a complete closed-loop optimization cycle on the benchmark partition.

        Steps:
            1. Evaluate Baseline V0 on optimization split.
            2. Ingest failure traces into FailureAnalyzer (classify into 12 categories).
            3. Generate targeted mutations via MutationEngine to create Candidate V1.
            4. Validate Candidate V1 with CandidateValidator (integrity, acyclicity, tools).
            5. Evaluate Candidate V1 on the optimization split.
            6. Compute 4-axis scorecard comparison and verify measurable improvement.

        Args:
            baseline_architecture: Optional initial DAG. If None, synthesizes default reconciliation DAG.
            suite: Optional BenchmarkSuite. Defaults to reconciliation benchmark suite.
            split: Partition split to optimize on (defaults to 'optimization').
            max_iterations: Maximum mutation cycles to perform.

        Returns:
            OptimizationResult containing full telemetry, comparisons, and candidate DAG.
        """
        benchmark_suite = suite or get_reconciliation_benchmark_suite()
        current_arch = baseline_architecture or self._create_default_baseline()
        baseline_arch = current_arch

        iterations: List[OptimizationIteration] = []

        # ---------------------------------------------------------------------
        # Step 1: Baseline Evaluation (V0)
        # ---------------------------------------------------------------------
        baseline_scorecard = self.evaluator.evaluate(
            architecture=current_arch,
            suite_or_cases=benchmark_suite,
            split=split,
            name=f"{current_arch.name}_Scorecard"
        )

        current_scorecard = baseline_scorecard

        # Check if baseline already has perfect accuracy
        if baseline_scorecard.accuracy >= 1.0 and baseline_scorecard.reliability >= 1.0:
            diff = self.validator.generate_diff(baseline_arch, current_arch)
            comp = self.evaluator.compare(baseline=baseline_scorecard, candidate=baseline_scorecard)
            diag_rep = DiagnosticReport(
                architecture_id=current_arch.id,
                total_cases=baseline_scorecard.total_cases,
                passed_cases=baseline_scorecard.accurate_cases,
                failed_cases=0,
                summary="Baseline achieved 100% accuracy; no mutations required."
            )
            return OptimizationResult(
                baseline_architecture=baseline_arch,
                candidate_architecture=current_arch,
                baseline_scorecard=baseline_scorecard,
                candidate_scorecard=baseline_scorecard,
                scorecard_comparison=comp,
                diagnostic_report=diag_rep,
                candidate_diff=diff,
                iterations=[],
                has_improved=False,
                accuracy_gain=0.0,
                status="CONVERGED",
                summary="Baseline already passed 100% of benchmark test cases without mutations."
            )

        last_diag_report: Optional[DiagnosticReport] = None
        last_mutation_result: Optional[MutationResult] = None

        # ---------------------------------------------------------------------
        # Step 2-5: Optimization Loop
        # ---------------------------------------------------------------------
        for iteration_idx in range(max_iterations):
            # Step 2: Failure Diagnostics
            diag_report = self.analyzer.analyze_scorecard(
                scorecard=current_scorecard,
                suite_or_cases=benchmark_suite,
                architecture=current_arch
            )
            last_diag_report = diag_report

            if not diag_report.failure_diagnostics:
                break  # All cases passing

            # Step 3: Mutation Engine (derive targeted mutation)
            cand_name = f"{baseline_arch.name.split('_V')[0]}_V{iteration_idx + 1}"
            mutation_res = self.mutation_engine.mutate(
                architecture=current_arch,
                diagnostic_report=diag_report,
                candidate_name=cand_name
            )
            last_mutation_result = mutation_res

            if not mutation_res.success or not mutation_res.candidate_architecture:
                # Mutation failed to synthesize a valid candidate
                break

            # Record iteration before evaluating new candidate
            iterations.append(OptimizationIteration(
                iteration=iteration_idx,
                architecture_id=current_arch.id,
                architecture_name=current_arch.name,
                scorecard=current_scorecard,
                diagnostic_report=diag_report,
                mutation_result=mutation_res
            ))

            candidate_arch = mutation_res.candidate_architecture

            # Step 4 & 5: Evaluate Mutated Candidate
            candidate_scorecard = self.evaluator.evaluate(
                architecture=candidate_arch,
                suite_or_cases=benchmark_suite,
                split=split,
                name=f"{candidate_arch.name}_Scorecard"
            )

            current_arch = candidate_arch
            current_scorecard = candidate_scorecard

            # If perfect accuracy achieved, stop early
            if current_scorecard.accuracy >= 1.0:
                break

        # ---------------------------------------------------------------------
        # Step 6: Side-by-Side Comparison and Verification
        # ---------------------------------------------------------------------
        final_comparison = self.evaluator.compare(
            baseline=baseline_scorecard,
            candidate=current_scorecard
        )

        final_diff = self.validator.generate_diff(baseline_arch, current_arch)

        acc_gain = current_scorecard.accuracy - baseline_scorecard.accuracy
        has_improved = acc_gain > 0 or final_comparison.is_pareto_dominant

        summary = (
            f"Autonomous optimization cycle completed across {len(iterations)} iterations on {split} split. "
            f"Baseline '{baseline_arch.name}' ({baseline_scorecard.accuracy * 100:.1f}%) -> "
            f"Candidate '{current_arch.name}' ({current_scorecard.accuracy * 100:.1f}%). "
            f"Empirical gain: {acc_gain * 100:+.1f}% accuracy. "
            f"Verdict: `{final_comparison.verdict}`."
        )

        status = "OPTIMIZED" if has_improved else ("CONVERGED" if acc_gain == 0.0 else "FAILED")

        return OptimizationResult(
            baseline_architecture=baseline_arch,
            candidate_architecture=current_arch,
            baseline_scorecard=baseline_scorecard,
            candidate_scorecard=current_scorecard,
            scorecard_comparison=final_comparison,
            diagnostic_report=last_diag_report or DiagnosticReport(
                architecture_id=baseline_arch.id,
                total_cases=baseline_scorecard.total_cases,
                passed_cases=baseline_scorecard.accurate_cases,
                failed_cases=0
            ),
            candidate_diff=final_diff,
            iterations=iterations,
            has_improved=has_improved,
            accuracy_gain=round(acc_gain, 4),
            status=status,
            summary=summary
        )

    def _create_default_baseline(self) -> AgentArchitecture:
        """Synthesize the canonical Baseline V0 architecture for financial reconciliation."""
        analyzer = GoalAnalyzer()
        spec = analyzer.analyze("Reconcile financial transaction ledgers, match records, and detect discrepancies")
        generator = ArchitectureGenerator(tool_registry=self.tool_registry)
        return generator.generate(spec, architecture_name="Agent_Reconciliation_V0")
