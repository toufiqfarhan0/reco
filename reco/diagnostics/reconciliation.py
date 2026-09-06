"""Reconciliation-specific diagnostic adapter for analyzing domain-specific benchmark failures.

Translates domain-specific reconciliation anomalies into generic RootCauseDiagnosis models,
preserving the domain-agnostic boundary of the core FailureAnalyzer.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

from reco.diagnostics.models import (
    DiagnosisEvidence,
    RecommendedMutation,
    RootCauseDiagnosis,
)
from reco.diagnostics.taxonomy import (
    FailureCategory,
    FailureSource,
    MutationType,
    Severity,
)


class ReconciliationDiagnosisAdapter:
    """Domain diagnostic adapter for bank-to-ledger reconciliation anomalies."""

    @classmethod
    def can_handle(cls, benchmark_context: Dict[str, Any]) -> bool:
        """Check if context pertains to reconciliation benchmark."""
        bench_name = benchmark_context.get("benchmark_name", "")
        if "reconciliation" in bench_name.lower():
            return True
        # Check for reconciliation-specific keys in ground truth or inputs
        gt = benchmark_context.get("ground_truth", {})
        if "expected_pairs" in gt or "unmatched_bank_ids" in gt or "primary_exception" in gt:
            return True
        return False

    @classmethod
    def diagnose(
        cls,
        actual_outcome: Dict[str, Any],
        ground_truth: Dict[str, Any],
        graph_nodes: List[Dict[str, Any]],
        tool_events: List[Dict[str, Any]],
        case_code: Optional[str] = None,
        case_execution_id: Optional[Any] = None,
    ) -> Optional[RootCauseDiagnosis]:
        """Perform reconciliation-specific root cause analysis."""
        primary_exception = ground_truth.get("primary_exception", "")
        expected_exceptions = ground_truth.get("expected_exceptions", {})
        actual_exceptions = actual_outcome.get("detected_exceptions", {})
        if not actual_exceptions and "exceptions" in actual_outcome:
            raw_ex = actual_outcome["exceptions"]
            if isinstance(raw_ex, dict):
                actual_exceptions = raw_ex
            elif isinstance(raw_ex, list):
                actual_exceptions = {e: 1 for e in raw_ex}

        expected_pairs = ground_truth.get("expected_pairs", [])
        actual_pairs = actual_outcome.get("matched_pairs", [])
        if not actual_pairs and "pairs" in actual_outcome:
            actual_pairs = actual_outcome["pairs"]

        node_ids = [n.get("node_id") for n in graph_nodes if "node_id" in n]
        matcher_node = next((n for n in graph_nodes if "match" in n.get("role", "").lower() or "match" in n.get("node_id", "").lower()), None)
        matcher_node_id = matcher_node.get("node_id") if matcher_node else (node_ids[0] if node_ids else None)
        verifier_node = next((n for n in graph_nodes if "verif" in n.get("role", "").lower() or "verif" in n.get("node_id", "").lower()), None)
        verifier_node_id = verifier_node.get("node_id") if verifier_node else None

        # 1. Check for Hallucinated Match / Wrong Vendor
        if primary_exception == "wrong_vendor" or "wrong_vendor" in expected_exceptions:
            # Check if agent claimed a match between records that have mismatched vendors
            unmatched_in_gt = ground_truth.get("unmatched_bank_ids", [])
            hallucinated = False
            for p in actual_pairs:
                b_id = p.get("bank_transaction_id") or p.get("bank_id")
                if b_id in unmatched_in_gt:
                    hallucinated = True
                    break

            if hallucinated or actual_exceptions.get("wrong_vendor", 0) == 0:
                evidence = [
                    DiagnosisEvidence(
                        source="benchmark_ground_truth",
                        field="primary_exception",
                        observed=list(actual_exceptions.keys()),
                        expected="wrong_vendor",
                        details={"case_code": case_code, "actual_pairs": len(actual_pairs)},
                    ),
                    DiagnosisEvidence(
                        source="evaluation",
                        field="matched_pairs",
                        observed="Matched records with mismatched entity/vendor identity",
                        expected="Flagged as unmatched or classified as wrong_vendor",
                    ),
                ]
                mutations = []
                if matcher_node_id:
                    mutations.append(
                        RecommendedMutation(
                            mutation_type=MutationType.PROMPT_CHANGE,
                            target=matcher_node_id,
                            rationale="Prioritize vendor/counterparty identity over monetary amount similarity. Invoke fuzzy_match_transactions with require_vendor_match=True and vendor_similarity_threshold=0.85 to reject false pairings with conflicting counterparty identities.",
                            expected_effect="Prevents false-positive matches when vendor names do not meet entity similarity thresholds.",
                            confidence=0.85,
                            evidence_refs=["benchmark_ground_truth", "evaluation"],
                        )
                    )
                if not verifier_node_id and node_ids:
                    mutations.append(
                        RecommendedMutation(
                            mutation_type=MutationType.ADD_VERIFIER,
                            target=node_ids[-1],
                            rationale="Architecture lacks an independent counter-party verification node to gate proposed matches.",
                            expected_effect="Catches vendor mismatches before final reconciliation commit.",
                            confidence=0.80,
                            evidence_refs=["evaluation"],
                        )
                    )

                return RootCauseDiagnosis(
                    case_execution_id=case_execution_id,
                    failure_category=FailureCategory.HALLUCINATED_MATCH,
                    severity=Severity.HIGH,
                    failed_node_id=matcher_node_id,
                    failure_source=FailureSource.NODE_EXECUTION,
                    symptom=f"Agent produced a false match or failed to flag wrong_vendor in scenario {case_code or 'reconciliation'}.",
                    summary="Matcher weighting overvalues amount and underweights counterparty/vendor identity.",
                    root_cause="Matcher prompt and similarity threshold do not penalize vendor / counterparty identity mismatches when amounts match exactly.",
                    evidence=evidence,
                    contributing_factors=[
                        "Lack of vendor identity verification step in DAG topology",
                        "High reliance on numerical amount equality in matching logic",
                    ],
                    confidence=0.90,
                    recommended_mutations=mutations,
                    affected_capabilities=["vendor_identity_validation", "fuzzy_matching"],
                    metadata={"benchmark": "reconciliation", "exception_class": "wrong_vendor"},
                )

        # 2. Check for Processing Fee Mismatch (classified as wrong_amount or fee missed)
        if primary_exception == "processing_fee" or "processing_fee" in expected_exceptions:
            # Did agent report wrong_amount instead of processing_fee?
            reported_wrong_amount = actual_exceptions.get("wrong_amount", 0) > 0
            missed_fee = actual_exceptions.get("processing_fee", 0) == 0

            if reported_wrong_amount or missed_fee:
                evidence = [
                    DiagnosisEvidence(
                        source="benchmark_ground_truth",
                        field="primary_exception",
                        observed=list(actual_exceptions.keys()),
                        expected="processing_fee",
                        details={"expected_discrepancy": str(ground_truth.get("total_discrepancy", "0.00"))},
                    )
                ]
                mutations = []
                target_node = matcher_node_id or (node_ids[0] if node_ids else "graph")
                mutations.append(
                    RecommendedMutation(
                        mutation_type=MutationType.TOOL_ADD,
                        target=target_node,
                        rationale="Insert fee-aware difference analysis capability before final discrepancy classification.",
                        expected_effect="Distinguishes standard payment processor fee deductions (1-3%) from erroneous transaction amounts.",
                        confidence=0.88,
                        evidence_refs=["benchmark_ground_truth"],
                    )
                )
                if node_ids:
                    mutations.append(
                        RecommendedMutation(
                            mutation_type=MutationType.TOPOLOGY_CHANGE,
                            target=node_ids[-1],
                            rationale="Insert fee-normalization pipeline step before final discrepancy categorization.",
                            expected_effect="Correctly isolates processing fee deductions from irregular balance discrepancies.",
                            confidence=0.82,
                            evidence_refs=["benchmark_ground_truth"],
                        )
                    )

                return RootCauseDiagnosis(
                    case_execution_id=case_execution_id,
                    failure_category=FailureCategory.ARITHMETIC_MISMATCH,
                    severity=Severity.MEDIUM,
                    failed_node_id=target_node,
                    failure_source=FailureSource.NODE_EXECUTION,
                    symptom=f"Agent classified fee variance as generic 'wrong_amount' instead of 'processing_fee' in {case_code or 'scenario'}.",
                    summary="Architecture lacks fee-aware discrepancy decomposition prior to exception classification.",
                    root_cause="The discrepancy classification pipeline does not check for characteristic payment processing fee percentages (e.g. 2-3% + fixed fee) before classifying amount differences.",
                    evidence=evidence,
                    contributing_factors=[
                        "Missing fee-aware normalization tool or sub-prompt",
                        "Single-pass difference calculator without fee detection rule",
                    ],
                    confidence=0.88,
                    recommended_mutations=mutations,
                    affected_capabilities=["fee_detection", "arithmetic_reconciliation"],
                    metadata={"benchmark": "reconciliation", "exception_class": "processing_fee"},
                )

        # 3. Check for Timing Difference / In-Flight Lag
        if primary_exception == "timing_difference" or "timing_difference" in expected_exceptions:
            missed_timing = actual_exceptions.get("timing_difference", 0) == 0
            if missed_timing:
                evidence = [
                    DiagnosisEvidence(
                        source="benchmark_ground_truth",
                        field="primary_exception",
                        observed=list(actual_exceptions.keys()),
                        expected="timing_difference",
                        details={"case_code": case_code},
                    )
                ]
                mutations = []
                target_node = matcher_node_id or (node_ids[0] if node_ids else "graph")
                mutations.append(
                    RecommendedMutation(
                        mutation_type=MutationType.PROMPT_CHANGE,
                        target=target_node,
                        rationale="Update matcher prompt to accept a configurable calendar window (e.g. +/- 3 business days) for transaction settlement lag.",
                        expected_effect="Identifies matching transactions that settle across date boundaries as timing differences rather than orphan items.",
                        confidence=0.84,
                        evidence_refs=["benchmark_ground_truth"],
                    )
                )

                return RootCauseDiagnosis(
                    case_execution_id=case_execution_id,
                    failure_category=FailureCategory.ARITHMETIC_MISMATCH,
                    severity=Severity.MEDIUM,
                    failed_node_id=target_node,
                    failure_source=FailureSource.NODE_EXECUTION,
                    symptom=f"Agent marked timing-lagged transaction as unmatched instead of timing_difference in {case_code or 'scenario'}.",
                    summary="Architecture lacks temporal reconciliation reasoning and window tolerance.",
                    root_cause="Matching logic enforces strict date identity rather than evaluating typical bank clearing lag windows (T+1 to T+3).",
                    evidence=evidence,
                    contributing_factors=[
                        "Rigid temporal matching constraint",
                        "Absence of settlement lag heuristic in matcher prompt",
                    ],
                    confidence=0.85,
                    recommended_mutations=mutations,
                    affected_capabilities=["temporal_matching", "reconciliation_logic"],
                    metadata={"benchmark": "reconciliation", "exception_class": "timing_difference"},
                )

        # 4. Check for Transposition Error (divisible by 9 difference)
        if primary_exception == "transposition" or "transposition" in expected_exceptions:
            missed_transposition = actual_exceptions.get("transposition", 0) == 0
            if missed_transposition:
                evidence = [
                    DiagnosisEvidence(
                        source="benchmark_ground_truth",
                        field="primary_exception",
                        observed=list(actual_exceptions.keys()),
                        expected="transposition",
                        details={"case_code": case_code},
                    )
                ]
                target_node = matcher_node_id or (node_ids[0] if node_ids else "graph")
                return RootCauseDiagnosis(
                    case_execution_id=case_execution_id,
                    failure_category=FailureCategory.ARITHMETIC_MISMATCH,
                    severity=Severity.LOW,
                    failed_node_id=target_node,
                    failure_source=FailureSource.NODE_EXECUTION,
                    symptom=f"Agent failed to identify numerical digit transposition in {case_code or 'scenario'}.",
                    summary="Numerical difference analysis lacks transposition check (divisible-by-9 invariant).",
                    root_cause="Discrepancy analysis lacks algorithmic check for digit swapping where difference is evenly divisible by 9.",
                    evidence=evidence,
                    contributing_factors=[
                        "Standard difference tool computes delta without transposition check",
                    ],
                    confidence=0.80,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.PROMPT_CHANGE,
                            target=target_node,
                            rationale="Instruct calculation node to test differences for divisibility by 9 to flag digit transpositions.",
                            expected_effect="Accurately classifies data entry digit transposition errors.",
                            confidence=0.80,
                            evidence_refs=["benchmark_ground_truth"],
                        )
                    ],
                    affected_capabilities=["transposition_detection", "arithmetic_reconciliation"],
                    metadata={"benchmark": "reconciliation", "exception_class": "transposition"},
                )

        # 5. Check for Compound Exception (multi-cause anomaly)
        if primary_exception == "compound_exception" or "compound_exception" in expected_exceptions:
            missed_compound = actual_exceptions.get("compound_exception", 0) == 0
            if missed_compound:
                evidence = [
                    DiagnosisEvidence(
                        source="benchmark_ground_truth",
                        field="primary_exception",
                        observed=list(actual_exceptions.keys()),
                        expected="compound_exception",
                        details={"case_code": case_code},
                    )
                ]
                target_node = node_ids[-1] if node_ids else "graph"
                return RootCauseDiagnosis(
                    case_execution_id=case_execution_id,
                    failure_category=FailureCategory.MISSING_VERIFICATION,
                    severity=Severity.HIGH,
                    failed_node_id=target_node,
                    failure_source=FailureSource.NODE_EXECUTION,
                    symptom=f"Agent stopped at single discrepancy and missed compound exception factors in {case_code or 'scenario'}.",
                    summary="Discrepancy pipeline assumes single-cause anomalies and lacks compound decomposition.",
                    root_cause="Reconciliation graph exits upon detecting the first anomaly without verifying secondary or compounding factors.",
                    evidence=evidence,
                    contributing_factors=[
                        "Short-circuit exception handling",
                        "Absence of multi-factor reconciliation verification step",
                    ],
                    confidence=0.82,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.TOPOLOGY_CHANGE,
                            target=target_node,
                            rationale="Add multi-factor decomposition step before exception classification.",
                            expected_effect="Enables compound exception diagnosis across multiple discrepancy dimensions.",
                            confidence=0.80,
                            evidence_refs=["benchmark_ground_truth"],
                        )
                    ],
                    affected_capabilities=["compound_reconciliation", "multi_factor_verification"],
                    metadata={"benchmark": "reconciliation", "exception_class": "compound_exception"},
                )

        return None
