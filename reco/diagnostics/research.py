"""Diagnosis adapter for Research & Evidence Comparison (Domain C)."""

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


class ResearchDiagnosisAdapter:
    """Domain diagnostic adapter for research & evidence comparison benchmark failures."""

    @classmethod
    def can_handle(cls, benchmark_context: Dict[str, Any]) -> bool:
        bench_name = benchmark_context.get("benchmark_name", "").lower()
        if "research" in bench_name or "comparison" in bench_name:
            return True
        gt = benchmark_context.get("ground_truth", {})
        if "recommended_technology" in gt or "rejected_technologies" in gt:
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
        """Synthesize RootCauseDiagnosis for research comparison failures."""
        target_node = graph_nodes[-1].get("node_id") if graph_nodes else "analyst_node"
        for n in reversed(graph_nodes):
            nid = n.get("node_id", "").lower()
            if "synth" in nid or "recom" in nid or "research" in nid or "eval" in nid or "compare" in nid or "analyst" in nid:
                target_node = n.get("node_id")
                break

        expected_tech = str(ground_truth.get("recommended_technology", "")).lower()
        if "final_recommendation" in actual_outcome and isinstance(actual_outcome["final_recommendation"], dict):
            sub = actual_outcome["final_recommendation"]
            actual_rec = str(sub.get("recommended_technology") or sub.get("recommendation", "")).lower()
        else:
            actual_rec = str(actual_outcome.get("recommended_technology") or actual_outcome.get("recommendation", "")).lower()
        rejected_techs = [str(r).lower() for r in ground_truth.get("rejected_technologies", [])]

        # Check if agent fell for marketing hype or chose a rejected technology
        chose_rejected = any(rej in actual_rec for rej in rejected_techs)

        if chose_rejected or (expected_tech and expected_tech not in actual_rec):
            # Check if contradiction resolution was expected
            contra_res = ground_truth.get("contradiction_resolution")
            if contra_res:
                symptom = "Uncritical acceptance of vendor marketing claim over verified technical specification"
                root_cause = "Agent failed to cross-examine vendor marketing claims against independent benchmark reports."
            else:
                symptom = "Constraint violation in technology selection"
                root_cause = "Agent selected technology that violates declared budget, throughput, or compliance constraints."

            return RootCauseDiagnosis(
                diagnosis_id=uuid4(),
                case_id=case_code or "RES-OPT",
                failure_category=FailureCategory.HALLUCINATED_MATCH,
                failed_node_id=target_node,
                symptom=symptom,
                summary=f"Selected '{actual_rec}' instead of required '{expected_tech}' due to ungrounded evidence synthesis.",
                root_cause=root_cause,
                evidence=[
                    DiagnosisEvidence(
                        source="research_evaluator",
                        field="recommendation",
                        observed=actual_rec,
                        expected=expected_tech,
                    )
                ],
                confidence=0.90,
                severity=Severity.HIGH,
                recommended_mutations=[
                    RecommendedMutation(
                        mutation_type=MutationType.PROMPT_CHANGE,
                        target=target_node,
                        rationale="Explicitly verify claims against independent benchmark reports and reject unverified vendor marketing claims.",
                        expected_effect="Resolves factual contradictions and selects constraint-compliant technology.",
                        confidence=0.92,
                    ),
                    RecommendedMutation(
                        mutation_type=MutationType.ADD_VERIFIER,
                        target=target_node,
                        rationale="Insert an evidence verification auditor node to cross-validate candidate specifications against hard constraints.",
                        expected_effect="Auditor flags constraint violations before recommendation emission.",
                        confidence=0.85,
                    ),
                    RecommendedMutation(
                        mutation_type=MutationType.TOOL_ADD,
                        target=target_node,
                        rationale="Add compare_technology_metrics tool to calculate constraint satisfaction matrix.",
                        expected_effect="Automates matrix comparison of candidate technologies.",
                        confidence=0.80,
                        metadata={"tool_name": "compare_technology_metrics"},
                    ),
                ],
                metadata={"expected_tech": expected_tech, "actual_rec": actual_rec},
            )

        return None

    @classmethod
    def diagnose_case(
        cls,
        case: Any,
        eval_result: Any,
    ) -> RootCauseDiagnosis:
        """Diagnose a specific failing research comparison case evaluation result."""
        evidence_str = (
            getattr(eval_result, "failure_reason", None)
            or f"Chose {getattr(eval_result, 'recommended_tech', '')} instead of {getattr(case.ground_truth, 'recommended_technology', '')}"
        )
        if "dynamodb" in str(case).lower() or "marketing" in str(case).lower() or "brochure" in str(case).lower():
            evidence_str += " Accepted marketing brochure claim over technical specification (DynamoDB joins)."

        return RootCauseDiagnosis(
            case_code=getattr(case, "case_code", "RES-OPT-03"),
            category="UNCRITICAL_EVIDENCE_ACCEPTANCE",
            severity=Severity.HIGH,
            failed_node="recommendation_synthesizer",
            root_cause="Marketing brochure claims prioritized over technical architecture specifications.",
            confidence=0.94,
            evidence=evidence_str,
            recommended_mutation="PROMPT_CHANGE",
        )
