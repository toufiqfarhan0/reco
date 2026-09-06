"""Deterministic evaluator for Dataset Anomaly Detection (Domain B)."""

import json
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from reco.benchmarks.anomaly.models import (
    AnomalyCase,
    AnomalyCaseEvaluationResult,
    AnomalyRunResult,
)
from reco.engine.state import ExecutionState
from reco.evaluators.scorecard import Scorecard


class AnomalyEvaluator:
    """Evaluates agent execution outputs against ground truth anomaly annotations."""

    def evaluate_case(self, case: AnomalyCase, state: Any) -> AnomalyCaseEvaluationResult:
        """Evaluate a single executed case against ground truth."""
        if isinstance(state, dict):
            actual_output = state
        elif hasattr(state, "outputs") and state.outputs:
            actual_output = state.outputs
        elif hasattr(state, "get_last_node_output"):
            actual_output = state.get_last_node_output()
        else:
            actual_output = state

        if isinstance(actual_output, str):
            try:
                actual_output = json.loads(actual_output)
            except Exception:
                actual_output = {"raw_text": actual_output}
        elif not isinstance(actual_output, dict):
            actual_output = {"data": actual_output}

        # Extract detected anomaly IDs from output
        detected_ids: Set[str] = set()
        
        # 1. Look for explicit anomalies list in output
        if "anomalies" in actual_output and isinstance(actual_output["anomalies"], list):
            for item in actual_output["anomalies"]:
                if isinstance(item, str):
                    detected_ids.add(item)
                elif isinstance(item, dict):
                    rid = item.get("id") or item.get("record_id")
                    if rid:
                        detected_ids.add(str(rid))
        elif "flagged_anomalies" in actual_output and isinstance(actual_output["flagged_anomalies"], list):
            for item in actual_output["flagged_anomalies"]:
                if isinstance(item, dict):
                    rid = item.get("record_id") or item.get("id")
                    if rid:
                        detected_ids.add(str(rid))
                elif isinstance(item, str):
                    detected_ids.add(item)
        elif "flagged_anomaly_ids" in actual_output and isinstance(actual_output["flagged_anomaly_ids"], list):
            for item in actual_output["flagged_anomaly_ids"]:
                if isinstance(item, str):
                    detected_ids.add(item)
                elif isinstance(item, str):
                    detected_ids.add(item)
        elif "anomalous_record_ids" in actual_output and isinstance(actual_output["anomalous_record_ids"], list):
            detected_ids.update(str(x) for x in actual_output["anomalous_record_ids"])

        state_tool_events = state.get("tool_events", []) if isinstance(state, dict) else getattr(state, "tool_events", [])
        if not detected_ids and state_tool_events:
            for evt in state_tool_events:
                if evt.get("tool") == "detect_distribution_anomalies" and evt.get("success"):
                    res_data = evt.get("data") or evt.get("output") or {}
                    if isinstance(res_data, dict):
                        for item in res_data.get("flagged_anomalies", []):
                            if isinstance(item, dict) and "record_id" in item:
                                detected_ids.add(str(item["record_id"]))

        expected_ids: Set[str] = set(case.ground_truth.expected_anomaly_ids)

        # Precision, Recall, F1
        tp = len(detected_ids & expected_ids)
        fp = len(detected_ids - expected_ids)
        fn = len(expected_ids - detected_ids)

        if not expected_ids:
            # Case expects zero anomalies (clean dataset)
            if not detected_ids:
                precision = 1.0
                recall = 1.0
                f1 = 1.0
                success = True
            else:
                precision = 0.0
                recall = 1.0
                f1 = 0.0
                success = False
        else:
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            success = (f1 >= 0.90)

        # Cost and tokens extraction from state
        state_meta = state.get("metadata", {}) if isinstance(state, dict) else getattr(state, "metadata", {})
        tokens_in = state_meta.get("tokens_in", state_meta.get("tokens_prompt", getattr(state, "tokens_input", 0)))
        tokens_out = state_meta.get("tokens_out", state_meta.get("tokens_completion", getattr(state, "tokens_output", 0)))
        cost_usd = state_meta.get("cost_usd", getattr(state, "cost_usd", 0.0))
        duration_ms = state.get("latency_ms", getattr(state, "latency_ms", 100)) if isinstance(state, dict) else getattr(state, "latency_ms", getattr(state, "execution_time_ms", 100)) or 100
        state_err = state.get("error") if isinstance(state, dict) else getattr(state, "error", None)

        return AnomalyCaseEvaluationResult(
            case_code=case.case_code,
            split=case.split,
            success=success,
            accuracy_score=round(f1, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            detected_anomaly_ids=list(detected_ids),
            false_positives=list(detected_ids - expected_ids),
            false_negatives=list(expected_ids - detected_ids),
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
        case_results: List[AnomalyCaseEvaluationResult],
        split: str,
        version: str = "V0",
        cost_type: str = "simulated_mock",
    ) -> AnomalyRunResult:
        """Aggregate case evaluation results into complete AnomalyRunResult."""
        total_cases = len(case_results)
        passed_cases = sum(1 for c in case_results if c.success)
        failed_cases = total_cases - passed_cases
        avg_acc = sum(c.accuracy_score for c in case_results) / total_cases if total_cases > 0 else 0.0
        total_cost = sum(c.cost_usd for c in case_results)
        total_lat = sum(c.latency_ms for c in case_results)
        avg_lat = int(round(total_lat / total_cases)) if total_cases > 0 else 0

        return AnomalyRunResult(
            benchmark_name="anomaly_detection",
            benchmark_version="anomaly_detection-v1",
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
                "benchmark_name": "anomaly_detection",
                "split": split,
            },
        )
