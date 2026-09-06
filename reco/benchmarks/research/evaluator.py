"""Deterministic evaluator for Research & Evidence Comparison (Domain C)."""

import json
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from reco.benchmarks.research.models import (
    ResearchCase,
    ResearchCaseEvaluationResult,
    ResearchRunResult,
)
from reco.engine.state import ExecutionState
from reco.evaluators.scorecard import Scorecard


class ResearchEvaluator:
    """Evaluates agent research recommendations and evidence synthesis against ground truth."""

    def evaluate_case(self, case: ResearchCase, state: Any) -> ResearchCaseEvaluationResult:
        """Score an agent's research comparison output on a single scenario."""
        if isinstance(state, dict):
            actual_output = state
        elif hasattr(state, "outputs") and state.outputs:
            actual_output = state.outputs
        elif hasattr(state, "get_last_node_output"):
            actual_output = state.get_last_node_output()
        else:
            actual_output = state
        raw_text = ""
        if isinstance(actual_output, str):
            raw_text = actual_output
            try:
                actual_output = json.loads(actual_output)
            except Exception:
                actual_output = {"recommendation": actual_output, "raw_text": actual_output}
        elif isinstance(actual_output, dict):
            raw_text = json.dumps(actual_output)
        else:
            raw_text = str(actual_output)
            actual_output = {"recommendation": raw_text}

        # 1. Extract recommendation
        rec_tech = None
        for k in ["recommendation", "recommended_technology", "selected_technology", "winner", "recommended"]:
            if k in actual_output and isinstance(actual_output[k], str):
                rec_tech = actual_output[k]
                break

        if not rec_tech:
            # Fallback search in raw text for candidate names
            for cand in case.candidate_technologies:
                if cand.lower() in raw_text.lower():
                    # Check if recommended or chosen
                    if any(phrase in raw_text.lower() for phrase in [f"recommend {cand.lower()}", f"chose {cand.lower()}", f"select {cand.lower()}", f"winner: {cand.lower()}"]):
                        rec_tech = cand
                        break
            if not rec_tech and case.candidate_technologies:
                # Check for mention
                for cand in case.candidate_technologies:
                    if cand.lower() in raw_text.lower():
                        rec_tech = cand
                        break

        expected_tech = case.ground_truth.recommended_technology
        rec_match = bool(rec_tech and expected_tech.lower() in rec_tech.lower())

        # 2. Fact coverage
        required_facts = case.ground_truth.required_facts
        found_facts = 0
        missing_facts = []
        for fact in required_facts:
            # Check key tokens of fact
            tokens = [w.lower() for w in fact.split() if len(w) > 3 and w.lower() not in ["with", "that", "this", "from"]]
            matched = any(t in raw_text.lower() for t in tokens) if tokens else (fact.lower() in raw_text.lower())
            if matched:
                found_facts += 1
            else:
                missing_facts.append(fact)

        fact_coverage = found_facts / len(required_facts) if required_facts else 1.0

        # 3. Contradiction handling
        contra_resolved = True
        for rej in case.ground_truth.rejected_technologies:
            if rec_tech and rej.lower() in rec_tech.lower():
                # Erroneously chose a rejected technology!
                contra_resolved = False

        if not rec_match or not contra_resolved:
            accuracy_score = 0.0
            success = False
        else:
            accuracy_score = (0.60 if rec_match else 0.0) + (0.40 * fact_coverage)
            success = (rec_match and contra_resolved and fact_coverage >= 0.50)

        state_meta = state.get("metadata", {}) if isinstance(state, dict) else getattr(state, "metadata", {})
        tokens_in = state_meta.get("tokens_in", state_meta.get("tokens_prompt", getattr(state, "tokens_input", 0)))
        tokens_out = state_meta.get("tokens_out", state_meta.get("tokens_completion", getattr(state, "tokens_output", 0)))
        cost_usd = state_meta.get("cost_usd", getattr(state, "cost_usd", 0.0))
        duration_ms = state.get("latency_ms", getattr(state, "latency_ms", 100)) if isinstance(state, dict) else getattr(state, "latency_ms", getattr(state, "execution_time_ms", 100)) or 100
        state_tool_events = state.get("tool_events", []) if isinstance(state, dict) else getattr(state, "tool_events", [])
        state_err = state.get("error") if isinstance(state, dict) else getattr(state, "error", None)

        return ResearchCaseEvaluationResult(
            case_code=case.case_code,
            split=case.split,
            success=success,
            accuracy_score=round(accuracy_score, 4),
            recommendation_match=rec_match,
            fact_coverage_score=round(fact_coverage, 4),
            contradiction_resolved=contra_resolved,
            recommended_tech=rec_tech,
            expected_tech=expected_tech,
            missing_facts=missing_facts,
            latency_ms=duration_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=round(cost_usd, 6),
            tool_events=state_tool_events,
            output=actual_output if isinstance(actual_output, dict) else {"raw": actual_output},
            error=state_err,
        )

    def compute_run_result(
        self,
        case_results: List[ResearchCaseEvaluationResult],
        split: str,
        version: str = "V0",
        cost_type: str = "simulated_mock",
    ) -> ResearchRunResult:
        """Aggregate case evaluations into a complete ResearchRunResult."""
        total_cases = len(case_results)
        passed_cases = sum(1 for c in case_results if c.success)
        failed_cases = total_cases - passed_cases
        avg_acc = sum(c.accuracy_score for c in case_results) / total_cases if total_cases > 0 else 0.0
        total_cost = sum(c.cost_usd for c in case_results)
        total_lat = sum(c.latency_ms for c in case_results)
        avg_lat = int(round(total_lat / total_cases)) if total_cases > 0 else 0

        return ResearchRunResult(
            benchmark_name="research_comparison",
            benchmark_version="research_comparison-v1",
            split=split,
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            accuracy=round(avg_acc, 4),
            reliability=1.0,
            total_cost_usd=round(total_cost, 6),
            avg_latency_ms=avg_lat,
            total_latency_ms=total_lat,
            case_results=case_results,
            metadata={
                "version": version,
                "cost_type": cost_type,
                "benchmark_name": "research_comparison",
                "split": split,
            },
        )
