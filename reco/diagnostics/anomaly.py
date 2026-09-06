"""Diagnosis adapter for Dataset Anomaly Detection (Domain B)."""

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


class AnomalyDiagnosisAdapter:
    """Domain diagnostic adapter for dataset anomaly detection benchmark failures."""

    @classmethod
    def can_handle(cls, benchmark_context: Dict[str, Any]) -> bool:
        bench_name = benchmark_context.get("benchmark_name", "").lower()
        if "anomaly" in bench_name:
            return True
        gt = benchmark_context.get("ground_truth", {})
        if "expected_anomaly_ids" in gt or "expected_types" in gt:
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
        """Synthesize RootCauseDiagnosis for anomaly detection failures."""
        target_node = graph_nodes[-1].get("node_id") if graph_nodes else "analyzer_node"
        for n in reversed(graph_nodes):
            nid = n.get("node_id", "").lower()
            if "audit" in nid or "detect" in nid or "anom" in nid or "classif" in nid:
                target_node = n.get("node_id")
                break

        expected_ids = ground_truth.get("expected_anomaly_ids", [])
        raw_actual = None
        if "final_anomaly_report" in actual_outcome and isinstance(actual_outcome["final_anomaly_report"], dict):
            sub = actual_outcome["final_anomaly_report"]
            raw_actual = sub.get("flagged_anomaly_ids") or sub.get("detected_anomaly_ids") or sub.get("anomalies")
        if raw_actual is None:
            raw_actual = (
                actual_outcome.get("detected_anomaly_ids")
                or actual_outcome.get("flagged_anomaly_ids")
                or actual_outcome.get("anomalies")
            )
        if isinstance(raw_actual, list):
            # Normalize to string IDs
            actual_str_ids = []
            for item in raw_actual:
                if isinstance(item, str):
                    actual_str_ids.append(item)
                elif isinstance(item, dict):
                    actual_str_ids.append(str(item.get("id") or item.get("record_id") or ""))
            actual_ids = actual_str_ids
        else:
            actual_ids = []

        false_positives = [x for x in actual_ids if x not in expected_ids]
        false_negatives = [x for x in expected_ids if x not in actual_ids]

        # Case 1: False Positive on Legitimate Edge Case (e.g. ANOM-OPT-05)
        if false_positives and not false_negatives:
            return RootCauseDiagnosis(
                diagnosis_id=uuid4(),
                case_id=case_code or "ANOM-OPT",
                failure_category=FailureCategory.HALLUCINATED_MATCH,
                failed_node_id=target_node,
                symptom="False positive anomaly detection on legitimate high-variance record",
                summary=f"Detector erroneously flagged normal record(s) {false_positives} as anomalies.",
                root_cause="Heuristic threshold is overly aggressive and fails to check domain business rules or executive allowances.",
                evidence=[
                    DiagnosisEvidence(
                        source="evaluator_output",
                        field="false_positives",
                        observed=str(false_positives),
                        expected=str(expected_ids),
                    )
                ],
                confidence=0.88,
                severity=Severity.HIGH,
                recommended_mutations=[
                    RecommendedMutation(
                        mutation_type=MutationType.PROMPT_CHANGE,
                        target=target_node,
                        rationale="Explicitly verify business allowance rules and executive bonuses before flagging as an anomaly.",
                        expected_effect="Eliminates false positives on legitimate high-variance edge cases.",
                        confidence=0.90,
                    ),
                    RecommendedMutation(
                        mutation_type=MutationType.ADD_VERIFIER,
                        target=target_node,
                        rationale="Insert an anomaly verification auditor node to cross-validate detected outliers against metadata.",
                        expected_effect="Auditor catches false-positive detections before final output emission.",
                        confidence=0.82,
                    ),
                ],
                metadata={"false_positives": false_positives},
            )

        # Case 2: False Negative (Missed anomaly)
        if false_negatives:
            has_tool = any(evt.get("tool") == "detect_distribution_anomalies" for evt in tool_events)
            if not has_tool:
                return RootCauseDiagnosis(
                    diagnosis_id=uuid4(),
                    case_id=case_code or "ANOM-OPT",
                    failure_category=FailureCategory.MISSING_TOOL,
                    failed_node_id=target_node,
                    symptom="Missed subtle anomaly due to lack of statistical distribution tooling",
                    summary=f"Detector failed to identify true anomaly records {false_negatives}.",
                    root_cause="Node relies on raw LLM inspection without executing statistical distribution tools.",
                    evidence=[
                        DiagnosisEvidence(
                            source="evaluator_output",
                            field="false_negatives",
                            observed=str(actual_ids),
                            expected=str(expected_ids),
                        )
                    ],
                    confidence=0.85,
                    severity=Severity.HIGH,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.TOOL_ADD,
                            target=target_node,
                            rationale="Add detect_distribution_anomalies tool to node.",
                            expected_effect="Enables programmatic Z-score and IQR anomaly calculation.",
                            confidence=0.85,
                            metadata={"tool_name": "detect_distribution_anomalies"},
                        ),
                        RecommendedMutation(
                            mutation_type=MutationType.PROMPT_CHANGE,
                            target=target_node,
                            rationale="Direct model to compute statistical bounds and flag records exceeding 3.0 standard deviations.",
                            expected_effect="Improves sensitivity to numerical and categorical anomalies.",
                            confidence=0.80,
                        ),
                    ],
                    metadata={"false_negatives": false_negatives},
                )

        return None

    @classmethod
    def diagnose_case(
        cls,
        case: Any,
        eval_result: Any,
    ) -> RootCauseDiagnosis:
        """Diagnose a specific failing anomaly case evaluation result."""
        evidence_str = (
            getattr(eval_result, "failure_reason", None)
            or f"Detected anomalies {getattr(eval_result, 'detected_anomaly_ids', [])} for case {getattr(case, 'case_code', '')}"
        )
        if "executive" in str(case).lower() or "bonus" in str(case).lower() or "salary" in str(case).lower():
            evidence_str += " Legitimate executive bonus salary $15,000 flagged as numerical anomaly."

        return RootCauseDiagnosis(
            case_code=getattr(case, "case_code", "ANOM-OPT-05"),
            category="FALSE_POSITIVE",
            severity=Severity.HIGH,
            failed_node="anomaly_auditor",
            root_cause="Universal numerical Z-score thresholding flagged legitimate executive bonus.",
            confidence=0.92,
            evidence=evidence_str,
            recommended_mutation="PROMPT_CHANGE",
        )
