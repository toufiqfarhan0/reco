"""Deterministic reconciliation evaluation engine and transparent scoring logic.

Scoring Formula:
  Case Accuracy = 0.40 * Match Score + 0.40 * Exception Score + 0.20 * Discrepancy Score
  Pass Threshold: Accuracy >= 0.80 and Reliability == 1.0
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Set, Tuple

from reco.benchmarks.reconciliation.models import (
    CaseEvaluationResult,
    ReconciliationCase,
    ReconciliationGroundTruth,
)
from reco.core.interfaces import EvaluationResult, Evaluator
from reco.engine.state import ExecutionState


def _parse_decimal(val: Any) -> Decimal:
    """Safely convert any numeric or string representation to exact Decimal."""
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")


def extract_reconciliation_payload(output_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Locate and extract the reconciliation summary dictionary from graph execution output."""
    if not isinstance(output_dict, dict):
        return {}

    # 1. Direct reconciliation summary keys
    if "matched_pairs" in output_dict:
        return output_dict

    # 2. Check within common node output keys
    for candidate_key in [
        "reconciliation_summary",
        "fuzzy_match_transactions",
        "match_transactions",
        "matcher",
        "matching",
        "reconciliation",
        "final_output",
    ]:
        if candidate_key in output_dict and isinstance(output_dict[candidate_key], dict):
            sub = output_dict[candidate_key]
            if "matched_pairs" in sub:
                return sub

    # 3. Check within nested node_outputs dictionary if passing full ExecutionState dict
    node_outputs = output_dict.get("node_outputs", {})
    if isinstance(node_outputs, dict):
        for candidate_key in [
            "fuzzy_match_transactions",
            "match_transactions",
            "matcher",
            "matching",
            "reconciliation",
            "reconciliation_summary",
            "final_output",
        ]:
            if candidate_key in node_outputs and isinstance(node_outputs[candidate_key], dict):
                sub = node_outputs[candidate_key]
                if "matched_pairs" in sub:
                    return sub

        # Fallback: scan all node output dictionaries for matched_pairs
        for val in node_outputs.values():
            if isinstance(val, dict) and "matched_pairs" in val:
                return val

    return output_dict


class ReconciliationEvaluator(Evaluator):
    """Deterministic, transparent scoring evaluator for financial bank and ledger reconciliation."""

    def evaluate(self, actual_output: Dict[str, Any], ground_truth: Dict[str, Any]) -> EvaluationResult:
        """Score actual output against ground truth per the core Evaluator interface."""
        actual_summary = extract_reconciliation_payload(actual_output)

        # Parse ground truth
        expected_pairs_raw = ground_truth.get("expected_pairs", [])
        expected_unmatched_bank = set(ground_truth.get("unmatched_bank_ids", []))
        expected_unmatched_ledger = set(ground_truth.get("unmatched_ledger_ids", []))
        primary_exception = ground_truth.get("primary_exception", "exact_match")

        # Parse actual summary
        actual_pairs_raw = actual_summary.get("matched_pairs", [])
        actual_unmatched_bank = set(actual_summary.get("unmatched_bank_ids", []))
        actual_unmatched_ledger = set(actual_summary.get("unmatched_ledger_ids", []))
        actual_exceptions = actual_summary.get("exceptions_by_type", {})

        # -------------------------------------------------------------------
        # 1. Pair Matching Correctness (0.0 to 1.0)
        # -------------------------------------------------------------------
        exp_pair_set: Set[Tuple[str, str]] = {
            (p.get("bank_transaction_id", ""), p.get("ledger_entry_id", ""))
            for p in expected_pairs_raw
            if isinstance(p, dict)
        }
        act_pair_set: Set[Tuple[str, str]] = {
            (p.get("bank_transaction_id", ""), p.get("ledger_entry_id", ""))
            for p in actual_pairs_raw
            if isinstance(p, dict)
        }

        # Handle cases with no expected pairs (e.g., wrong vendor)
        if not exp_pair_set:
            if not act_pair_set:
                pair_score = 1.0
            else:
                # Unsupported false matches created when none should exist
                pair_score = 0.0
        else:
            true_positives = len(exp_pair_set & act_pair_set)
            precision = true_positives / len(act_pair_set) if act_pair_set else 0.0
            recall = true_positives / len(exp_pair_set) if exp_pair_set else 0.0
            if precision + recall > 0:
                pair_score = 2 * (precision * recall) / (precision + recall)
            else:
                pair_score = 0.0

        # Unmatched isolation accuracy
        ubank_acc = 1.0 if expected_unmatched_bank == actual_unmatched_bank else 0.5 if (expected_unmatched_bank & actual_unmatched_bank) else 0.0
        uledger_acc = 1.0 if expected_unmatched_ledger == actual_unmatched_ledger else 0.5 if (expected_unmatched_ledger & actual_unmatched_ledger) else 0.0

        if expected_unmatched_bank or expected_unmatched_ledger:
            match_score = 0.60 * pair_score + 0.20 * ubank_acc + 0.20 * uledger_acc
        else:
            match_score = pair_score

        # -------------------------------------------------------------------
        # 2. Exception Classification Correctness (0.0 to 1.0)
        # -------------------------------------------------------------------
        act_pair_type_map: Dict[Tuple[str, str], str] = {
            (p.get("bank_transaction_id", ""), p.get("ledger_entry_id", "")): p.get("match_type", "")
            for p in actual_pairs_raw
            if isinstance(p, dict)
        }

        if exp_pair_set:
            correct_type_count = 0
            for p in expected_pairs_raw:
                k = (p.get("bank_transaction_id", ""), p.get("ledger_entry_id", ""))
                expected_type = p.get("match_type", "")
                actual_type = act_pair_type_map.get(k, "")
                if actual_type == expected_type:
                    correct_type_count += 1
                elif actual_type in ["near_match", "processing_fee", "timing_difference"] and expected_type == "compound_exception":
                    # Partial credit for identifying a component of compound exception
                    correct_type_count += 0.5
            exception_score = correct_type_count / len(expected_pairs_raw)
        else:
            # When no pairs exist, check if primary exception category was recognized
            if primary_exception in actual_exceptions or (
                primary_exception == "wrong_vendor" and not act_pair_set
            ):
                exception_score = 1.0
            else:
                exception_score = 0.5 if not act_pair_set else 0.0

        # -------------------------------------------------------------------
        # 3. Discrepancy Amount Correctness (0.0 to 1.0)
        # -------------------------------------------------------------------
        act_discrepancy_map: Dict[Tuple[str, str], Decimal] = {
            (p.get("bank_transaction_id", ""), p.get("ledger_entry_id", "")): _parse_decimal(p.get("amount_discrepancy", "0.00"))
            for p in actual_pairs_raw
            if isinstance(p, dict)
        }

        if exp_pair_set:
            disc_scores = []
            for p in expected_pairs_raw:
                k = (p.get("bank_transaction_id", ""), p.get("ledger_entry_id", ""))
                exp_disc = _parse_decimal(p.get("amount_discrepancy", "0.00"))
                act_disc = act_discrepancy_map.get(k)
                if act_disc is not None:
                    diff = abs(exp_disc - act_disc)
                    if diff <= Decimal("0.01"):
                        disc_scores.append(1.0)
                    else:
                        denom = max(abs(exp_disc), abs(act_disc), Decimal("1.00"))
                        disc_scores.append(max(0.0, float(1 - (diff / denom))))
                else:
                    disc_scores.append(0.0)
            discrepancy_score = sum(disc_scores) / len(disc_scores)
        else:
            # For cases with no match, verify no hallucinated match discrepancy
            discrepancy_score = 1.0 if not act_pair_set else 0.0

        # -------------------------------------------------------------------
        # Composite Calculation: 40% match, 40% exception, 20% discrepancy
        # -------------------------------------------------------------------
        composite_accuracy = round(
            (0.40 * match_score) + (0.40 * exception_score) + (0.20 * discrepancy_score),
            4,
        )
        composite_accuracy = max(0.0, min(1.0, composite_accuracy))

        # Check reliability: did the tool execute and produce valid summary schema?
        has_required_keys = isinstance(actual_summary, dict) and "matched_pairs" in actual_summary
        reliability = 1.0 if has_required_keys else 0.0

        # Passed threshold: accuracy >= 0.80 and reliability == 1.0
        passed = (composite_accuracy >= 0.80) and (reliability == 1.0)

        return EvaluationResult(
            accuracy=composite_accuracy,
            reliability=reliability,
            passed=passed,
            details={
                "pair_matching_score": round(match_score, 4),
                "exception_classification_score": round(exception_score, 4),
                "discrepancy_score": round(discrepancy_score, 4),
                "matched_pairs_count": len(actual_pairs_raw),
                "expected_pairs_count": len(expected_pairs_raw),
                "detected_exceptions": actual_exceptions,
            },
        )

    def evaluate_case(
        self,
        case: ReconciliationCase,
        state: ExecutionState,
    ) -> CaseEvaluationResult:
        """Perform comprehensive case-level scoring, packaging telemetry and failure trace."""
        actual_summary = extract_reconciliation_payload(state.node_outputs)
        gt_dict = case.ground_truth.model_dump(mode="json")

        # Evaluate correctness
        eval_res = self.evaluate(actual_summary, gt_dict)

        # Fatal execution check
        is_reliable = 1.0 if (state.status == "completed" and eval_res.reliability == 1.0) else 0.0
        passed = eval_res.passed and (is_reliable == 1.0)

        # Collect tool events and errors
        tool_events = list(state.tool_events)
        errors = list(state.errors)

        return CaseEvaluationResult(
            case_code=case.case_code,
            split=case.split,
            success=passed,
            accuracy_score=eval_res.accuracy,
            reliability_score=is_reliable,
            pair_matching_score=eval_res.details.get("pair_matching_score", 0.0),
            exception_classification_score=eval_res.details.get("exception_classification_score", 0.0),
            discrepancy_score=eval_res.details.get("discrepancy_score", 0.0),
            latency_ms=state.latency_ms,
            tokens_in=state.tokens_input,
            tokens_out=state.tokens_output,
            cost_usd=state.cost_usd,
            expected_outcome=gt_dict,
            actual_outcome=actual_summary,
            detected_exceptions=actual_summary.get("exceptions_by_type", {}),
            tool_events=tool_events,
            errors=errors,
            trace_id=state.metadata.get("trace_id"),
            metadata={
                "difficulty": case.difficulty,
                "exception_class": case.exception_class,
                "case_description": case.description,
            },
        )
