"""Failure Analyzer and Root Cause Diagnoser.

Analyzes failed agent execution traces, graph architectures, benchmark ground truth,
and scorecard metrics to produce structured, evidence-grounded root cause diagnoses
with actionable mutation recommendations for the future optimizer.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from reco.core.interfaces import ModelGateway
from reco.db.models import FailureDiagnosisRecord
from reco.db.repositories import FailureDiagnosisRepository
from reco.diagnostics.models import (
    DiagnosisEvidence,
    FailureCluster,
    RecommendedMutation,
    RootCauseDiagnosis,
)
from reco.diagnostics.reconciliation import ReconciliationDiagnosisAdapter
from reco.diagnostics.anomaly import AnomalyDiagnosisAdapter
from reco.diagnostics.research import ResearchDiagnosisAdapter
from reco.diagnostics.taxonomy import (
    FailureCategory,
    FailureSource,
    MutationType,
    Severity,
)
from reco.logging import get_logger

logger = get_logger("diagnostics.analyzer")


class FailureAnalyzer:
    """Consumes execution records and produces structured root-cause diagnoses."""

    def __init__(
        self,
        model_gateway: Optional[ModelGateway] = None,
        tool_registry: Optional[Any] = None,
    ):
        self.model_gateway = model_gateway
        self.tool_registry = tool_registry

    def analyze(
        self,
        execution_record: Any,
        task_specification: Optional[Any] = None,
        architecture: Optional[Any] = None,
        benchmark_context: Optional[Dict[str, Any]] = None,
        scorecard_metrics: Optional[Dict[str, Any]] = None,
    ) -> RootCauseDiagnosis:
        diag = self._analyze_internal(
            execution_record=execution_record,
            task_specification=task_specification,
            architecture=architecture,
            benchmark_context=benchmark_context,
            scorecard_metrics=scorecard_metrics,
        )
        try:
            from reco.observability.tracer import get_tracer
            case_code = ""
            if benchmark_context:
                case_code = str(benchmark_context.get("case_code", ""))
            get_tracer().trace_failure_diagnosis(
                diagnosis_id=str(diag.diagnosis_id),
                category=str(diag.category.value if hasattr(diag.category, "value") else diag.category),
                severity=str(diag.severity.value if hasattr(diag.severity, "value") else diag.severity),
                failed_node=str(diag.failed_node or ""),
                confidence=float(diag.confidence),
                case_code=case_code,
            )
        except Exception:
            pass
        return diag

    def diagnose(self, *args: Any, **kwargs: Any) -> RootCauseDiagnosis:
        """Convenience alias matching analyze."""
        return self.analyze(*args, **kwargs)

    def _analyze_internal(
        self,
        execution_record: Any,
        task_specification: Optional[Any] = None,
        architecture: Optional[Any] = None,
        benchmark_context: Optional[Dict[str, Any]] = None,
        scorecard_metrics: Optional[Dict[str, Any]] = None,
    ) -> RootCauseDiagnosis:
        """Analyze an execution failure and synthesize a RootCauseDiagnosis."""
        # 1. Normalize execution inputs
        norm_exec = self._normalize_execution(execution_record)
        norm_task = self._normalize_task_spec(task_specification)
        norm_arch = self._normalize_architecture(architecture)
        bench_ctx = benchmark_context or {}

        # 2. Check for explicit Tool Argument / Validation Errors
        tool_arg_diag = self._check_tool_argument_error(norm_exec, norm_arch)
        if tool_arg_diag:
            return tool_arg_diag

        # 3. Check for Tool Runtime Errors
        tool_runtime_diag = self._check_tool_runtime_error(norm_exec, norm_arch)
        if tool_runtime_diag:
            return tool_runtime_diag

        # 4. Check for Model Gateway Failures
        model_fail_diag = self._check_model_failure(norm_exec, norm_arch)
        if model_fail_diag:
            return model_fail_diag

        # 5. Check for Context Overflow / Truncation
        context_diag = self._check_context_overflow(norm_exec, norm_arch)
        if context_diag:
            return context_diag

        # 6. Check for Missing Tool or Wrong Tool Selection
        tool_selection_diag = self._check_tool_selection(norm_exec, norm_task, norm_arch)
        if tool_selection_diag:
            return tool_selection_diag

        # 7. Check for Premature Termination / Missing Terminal Nodes
        term_diag = self._check_premature_termination(norm_exec, norm_arch)
        if term_diag:
            return term_diag

        # 8. Check for Output Schema Errors
        schema_diag = self._check_output_schema_error(norm_exec, norm_task, norm_arch)
        if schema_diag:
            return schema_diag

        # 9. Domain-Specific Adapter Diagnosis (e.g., Reconciliation)
        if ReconciliationDiagnosisAdapter.can_handle(bench_ctx):
            gt = bench_ctx.get("ground_truth", {})
            actual = norm_exec.get("output", {}) or norm_exec.get("node_outputs", {})
            case_code = bench_ctx.get("case_code") or norm_exec.get("metadata", {}).get("case_code")
            case_exec_id = norm_exec.get("case_execution_id") or norm_exec.get("execution_id")
            reco_diag = ReconciliationDiagnosisAdapter.diagnose(
                actual_outcome=actual,
                ground_truth=gt,
                graph_nodes=self._get_nodes_list(norm_arch),
                tool_events=norm_exec.get("tool_events", []),
                case_code=case_code,
                case_execution_id=case_exec_id,
            )
            if reco_diag:
                # Correlate with scorecard if provided
                if scorecard_metrics:
                    reco_diag.metadata["scorecard_metrics"] = scorecard_metrics
                return reco_diag
        elif AnomalyDiagnosisAdapter.can_handle(bench_ctx):
            gt = bench_ctx.get("ground_truth", {})
            actual = norm_exec.get("output", {}) or norm_exec.get("node_outputs", {})
            case_code = bench_ctx.get("case_code") or norm_exec.get("metadata", {}).get("case_code")
            case_exec_id = norm_exec.get("case_execution_id") or norm_exec.get("execution_id")
            anom_diag = AnomalyDiagnosisAdapter.diagnose(
                actual_outcome=actual,
                ground_truth=gt,
                graph_nodes=self._get_nodes_list(norm_arch),
                tool_events=norm_exec.get("tool_events", []),
                case_code=case_code,
                case_execution_id=case_exec_id,
            )
            if anom_diag:
                if scorecard_metrics:
                    anom_diag.metadata["scorecard_metrics"] = scorecard_metrics
                return anom_diag
        elif ResearchDiagnosisAdapter.can_handle(bench_ctx):
            gt = bench_ctx.get("ground_truth", {})
            actual = norm_exec.get("output", {}) or norm_exec.get("node_outputs", {})
            case_code = bench_ctx.get("case_code") or norm_exec.get("metadata", {}).get("case_code")
            case_exec_id = norm_exec.get("case_execution_id") or norm_exec.get("execution_id")
            res_diag = ResearchDiagnosisAdapter.diagnose(
                actual_outcome=actual,
                ground_truth=gt,
                graph_nodes=self._get_nodes_list(norm_arch),
                tool_events=norm_exec.get("tool_events", []),
                case_code=case_code,
                case_execution_id=case_exec_id,
            )
            if res_diag:
                if scorecard_metrics:
                    res_diag.metadata["scorecard_metrics"] = scorecard_metrics
                return res_diag

        # 9b. Check for explicit domain in execution_record
        if norm_exec.get("domain") == "anomaly_detection":
            failed_node = self._find_first_node(norm_arch) or "anomaly_auditor"
            reason = norm_exec.get("failure_reason") or "Anomaly detection failed"
            return RootCauseDiagnosis(
                case_code=norm_exec.get("case_code", "ANOM-OPT-05"),
                category="FALSE_POSITIVE" if "false_positive" in reason.lower() else FailureCategory.PROMPT_DEFECT,
                severity=Severity.HIGH,
                failed_node=failed_node,
                root_cause=f"Anomaly detection failure: {reason}",
                confidence=0.88,
                evidence=reason,
                recommended_mutation="PROMPT_CHANGE",
            )
        if norm_exec.get("domain") == "research_comparison":
            failed_node = self._find_first_node(norm_arch) or "recommendation_synthesizer"
            reason = norm_exec.get("failure_reason") or "Research comparison failed"
            return RootCauseDiagnosis(
                case_code=norm_exec.get("case_code", "RES-OPT-03"),
                category="UNCRITICAL_EVIDENCE_ACCEPTANCE" if "marketing" in reason.lower() or "uncritical" in reason.lower() else FailureCategory.PROMPT_DEFECT,
                severity=Severity.HIGH,
                failed_node=failed_node,
                root_cause=f"Research comparison failure: {reason}",
                confidence=0.90,
                evidence=reason,
                recommended_mutation="PROMPT_CHANGE",
            )

        # 10. Check for Missing Verification
        verif_diag = self._check_missing_verification(norm_exec, norm_task, norm_arch, bench_ctx)
        if verif_diag:
            return verif_diag

        # 11. Check for Generic Arithmetic Mismatch
        arith_diag = self._check_arithmetic_mismatch(norm_exec, bench_ctx, norm_arch)
        if arith_diag:
            return arith_diag

        # 12. Scorecard-guided fallback or UNKNOWN_FAILURE (No False Certainty)
        return self._handle_unknown_or_scorecard_fallback(norm_exec, norm_arch, scorecard_metrics)

    # -------------------------------------------------------------------------
    # Multi-Signal Diagnostic Checkers
    # -------------------------------------------------------------------------

    def _check_tool_argument_error(
        self, norm_exec: Dict[str, Any], norm_arch: Dict[str, Any]
    ) -> Optional[RootCauseDiagnosis]:
        """Detect ToolExecutor argument validation failures."""
        tool_events = norm_exec.get("tool_events", [])
        errors = norm_exec.get("errors", [])

        # Check tool events for validation errors
        for evt in tool_events:
            if not evt.get("success", True):
                err = str(evt.get("error", "")).lower()
                if any(k in err for k in ["validation", "invalid argument", "missing required", "parameter", "schema validation"]):
                    failed_node = evt.get("node_id") or self._find_first_node(norm_arch)
                    evidence = [
                        DiagnosisEvidence(
                            source="tool_event",
                            tool=evt.get("tool_name"),
                            field="arguments",
                            observed=evt.get("arguments"),
                            expected="Valid arguments matching tool schema",
                            details={"error": evt.get("error")},
                        )
                    ]
                    mutations = []
                    if failed_node:
                        mutations.append(
                            RecommendedMutation(
                                mutation_type=MutationType.PROMPT_CHANGE,
                                target=failed_node,
                                rationale=f"Node prompt does not enforce parameter constraints for tool '{evt.get('tool_name')}'.",
                                expected_effect="Ensures generated tool call payloads satisfy parameter validation schemas.",
                                confidence=0.92,
                                evidence_refs=["tool_event"],
                            )
                        )
                    return RootCauseDiagnosis(
                        case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                        failure_category=FailureCategory.TOOL_ARGUMENT_ERROR,
                        severity=Severity.HIGH,
                        failed_node_id=failed_node,
                        failure_source=FailureSource.TOOL_INVOCATION,
                        symptom=f"Tool '{evt.get('tool_name')}' rejected invocation due to invalid arguments: {evt.get('error')}",
                        summary=f"Argument validation failed for tool '{evt.get('tool_name')}' at node '{failed_node}'.",
                        root_cause=f"Node '{failed_node}' generated arguments incompatible with tool '{evt.get('tool_name')}' parameters schema.",
                        evidence=evidence,
                        contributing_factors=["Inadequate parameter formatting instructions in node system prompt"],
                        confidence=0.95,
                        recommended_mutations=mutations,
                        affected_capabilities=["tool_calling", "argument_formatting"],
                    )

        # Check explicit error log
        for err in errors:
            err_msg = str(err.get("error_message", "")).lower()
            err_type = str(err.get("error_type", "")).lower()
            if "validation" in err_type or "invalid argument" in err_msg or "validation error" in err_msg:
                failed_node = err.get("node_id") or self._find_first_node(norm_arch)
                return RootCauseDiagnosis(
                    case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                    failure_category=FailureCategory.TOOL_ARGUMENT_ERROR,
                    severity=Severity.HIGH,
                    failed_node_id=failed_node,
                    failure_source=FailureSource.TOOL_INVOCATION,
                    symptom=f"Tool argument validation failure reported: {err.get('error_message')}",
                    summary=f"Tool argument validation failed at node '{failed_node}'.",
                    root_cause=f"Node '{failed_node}' passed invalid arguments violating schema.",
                    evidence=[
                        DiagnosisEvidence(
                            source="node_execution",
                            field="error_message",
                            observed=err.get("error_message"),
                            expected="Valid tool arguments",
                            details=err,
                        )
                    ],
                    contributing_factors=["Missing parameter typing in node instructions"],
                    confidence=0.92,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.PROMPT_CHANGE,
                            target=failed_node or "graph",
                            rationale="Constrain parameter synthesis to adhere strictly to schema.",
                            expected_effect="Eliminates tool validation errors.",
                            confidence=0.90,
                        )
                    ],
                    affected_capabilities=["argument_validation"],
                )
        return None

    def _check_tool_runtime_error(
        self, norm_exec: Dict[str, Any], norm_arch: Dict[str, Any]
    ) -> Optional[RootCauseDiagnosis]:
        """Detect execution crashes or unhandled exceptions inside a tool."""
        tool_events = norm_exec.get("tool_events", [])
        for evt in tool_events:
            if not evt.get("success", True):
                err = str(evt.get("error", ""))
                failed_node = evt.get("node_id") or self._find_first_node(norm_arch)
                evidence = [
                    DiagnosisEvidence(
                        source="tool_event",
                        tool=evt.get("tool_name"),
                        observed=err,
                        expected="Successful tool execution (success=True)",
                        details={"arguments": evt.get("arguments")},
                    )
                ]
                return RootCauseDiagnosis(
                    case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                    failure_category=FailureCategory.TOOL_RUNTIME_ERROR,
                    severity=Severity.HIGH,
                    failed_node_id=failed_node,
                    failure_source=FailureSource.TOOL_INVOCATION,
                    symptom=f"Tool '{evt.get('tool_name')}' crashed during execution: {err}",
                    summary=f"Runtime exception in tool '{evt.get('tool_name')}' at node '{failed_node}'.",
                    root_cause=f"Tool '{evt.get('tool_name')}' encountered an unhandled runtime error or data incompatibility: {err}",
                    evidence=evidence,
                    contributing_factors=["Lack of error recovery or retry policy on node"],
                    confidence=0.92,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.RETRY_POLICY_CHANGE,
                            target=failed_node or "graph",
                            rationale="Configure retry policy or fallback handler for transient tool crashes.",
                            expected_effect="Recovers gracefully from transient tool execution errors.",
                            confidence=0.85,
                        )
                    ],
                    affected_capabilities=["tool_runtime_stability"],
                )
        return None

    def _check_model_failure(
        self, norm_exec: Dict[str, Any], norm_arch: Dict[str, Any]
    ) -> Optional[RootCauseDiagnosis]:
        """Detect model gateway crashes, rate limits, or malformed inference responses."""
        errors = norm_exec.get("errors", [])
        for err in errors:
            err_msg = str(err.get("error_message", "")).lower()
            err_type = str(err.get("error_type", "")).lower()
            if any(k in err_msg or k in err_type for k in ["model gateway", "inference error", "ratelimit", "provider error", "500", "gateway timeout"]):
                failed_node = err.get("node_id") or self._find_first_node(norm_arch)
                return RootCauseDiagnosis(
                    case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                    failure_category=FailureCategory.MODEL_FAILURE,
                    severity=Severity.CRITICAL,
                    failed_node_id=failed_node,
                    failure_source=FailureSource.MODEL_INVOCATION,
                    symptom=f"Model invocation failed at node '{failed_node}': {err.get('error_message')}",
                    summary=f"Inference model provider failure at node '{failed_node}'.",
                    root_cause=f"ModelGateway reported provider-level failure: {err.get('error_message')}",
                    evidence=[
                        DiagnosisEvidence(
                            source="node_execution",
                            field="model_gateway",
                            observed=err.get("error_message"),
                            expected="Valid model completion",
                        )
                    ],
                    contributing_factors=["Provider endpoint instability or rate limiting"],
                    confidence=0.95,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.MODEL_CHANGE,
                            target=failed_node or "graph",
                            rationale="Switch node to more reliable backup model configuration.",
                            expected_effect="Mitigates provider-level model outages.",
                            confidence=0.88,
                        )
                    ],
                    affected_capabilities=["inference_reliability"],
                )
        return None

    def _check_context_overflow(
        self, norm_exec: Dict[str, Any], norm_arch: Dict[str, Any]
    ) -> Optional[RootCauseDiagnosis]:
        """Detect context truncation, compaction drops, or token overflow."""
        errors = norm_exec.get("errors", [])
        for err in errors:
            err_msg = str(err.get("error_message", "")).lower()
            if any(k in err_msg for k in ["context length", "maximum context", "token limit", "truncated context", "compaction dropped"]):
                failed_node = err.get("node_id") or self._find_first_node(norm_arch)
                return RootCauseDiagnosis(
                    case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                    failure_category=FailureCategory.CONTEXT_OVERFLOW,
                    severity=Severity.HIGH,
                    failed_node_id=failed_node,
                    failure_source=FailureSource.STATE_PROPAGATION,
                    symptom=f"Context overflow or state truncation: {err.get('error_message')}",
                    summary=f"Context overflow exceeded model token window at node '{failed_node}'.",
                    root_cause="Cumulative state history or large batch input exceeded model context window limits.",
                    evidence=[
                        DiagnosisEvidence(
                            source="state_propagation",
                            field="context_window",
                            observed=err.get("error_message"),
                            expected="Context within token window",
                        )
                    ],
                    contributing_factors=["Unbounded state accumulation across sequential nodes"],
                    confidence=0.90,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.CONTEXT_CHANGE,
                            target=failed_node or "graph",
                            rationale="Implement input projection or selective key extraction rather than passing full state.",
                            expected_effect="Prevents context window overflow and reduces token consumption.",
                            confidence=0.88,
                        )
                    ],
                    affected_capabilities=["context_management"],
                )
        return None

    def _check_tool_selection(
        self,
        norm_exec: Dict[str, Any],
        norm_task: Dict[str, Any],
        norm_arch: Dict[str, Any],
    ) -> Optional[RootCauseDiagnosis]:
        """Detect missing required tools or inappropriate tool binding."""
        nodes = self._get_nodes_list(norm_arch)
        assigned_tools = set()
        for n in nodes:
            for t in n.get("tools", []):
                assigned_tools.add(t)

        required_tools = norm_task.get("required_tools", [])
        missing_tools = [t for t in required_tools if t not in assigned_tools]
        if missing_tools:
            target_node = self._find_first_node(norm_arch) or "graph"
            return RootCauseDiagnosis(
                case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                failure_category=FailureCategory.MISSING_TOOL,
                severity=Severity.HIGH,
                failed_node_id=target_node,
                failure_source=FailureSource.ARCHITECTURE_GENERATION,
                symptom=f"Workflow lacks required tool(s): {missing_tools}",
                summary=f"Missing required tool bindings: {', '.join(missing_tools)}.",
                root_cause=f"Architecture generator did not assign required tools {missing_tools} to any graph node.",
                evidence=[
                    DiagnosisEvidence(
                        source="architecture",
                        field="assigned_tools",
                        observed=list(assigned_tools),
                        expected=required_tools,
                    )
                ],
                contributing_factors=["Architecture generation tool mapping gap"],
                confidence=0.92,
                recommended_mutations=[
                    RecommendedMutation(
                        mutation_type=MutationType.TOOL_ADD,
                        target=target_node,
                        rationale=f"Bind missing tool '{missing_tools[0]}' to the appropriate execution node.",
                        expected_effect=f"Equips the workflow with required capability '{missing_tools[0]}'.",
                        confidence=0.92,
                    )
                ],
                affected_capabilities=["tool_binding"],
            )

        # Check for unassigned tool invocation error in errors log
        errors = norm_exec.get("errors", [])
        for err in errors:
            err_msg = str(err.get("error_message", "")).lower()
            if "tool not found" in err_msg or "unregistered tool" in err_msg:
                failed_node = err.get("node_id") or self._find_first_node(norm_arch)
                return RootCauseDiagnosis(
                    case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                    failure_category=FailureCategory.MISSING_TOOL,
                    severity=Severity.HIGH,
                    failed_node_id=failed_node,
                    failure_source=FailureSource.TOOL_INVOCATION,
                    symptom=f"Node attempted to invoke an unavailable tool: {err.get('error_message')}",
                    summary=f"Unavailable tool invocation at node '{failed_node}'.",
                    root_cause=f"Node '{failed_node}' attempted to execute a tool not registered in the system.",
                    evidence=[
                        DiagnosisEvidence(
                            source="tool_invocation",
                            field="error_message",
                            observed=err.get("error_message"),
                            expected="Registered tool",
                        )
                    ],
                    contributing_factors=["Model hallucinated tool name or tool was unassigned"],
                    confidence=0.90,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.PROMPT_CHANGE,
                            target=failed_node or "graph",
                            rationale="Explicitly list only available registered tools in system prompt.",
                            expected_effect="Prevents invocation of unregistered tools.",
                            confidence=0.88,
                        )
                    ],
                    affected_capabilities=["tool_selection"],
                )

        # Check for WRONG_TOOL_SELECTION
        for err in errors:
            err_msg = str(err.get("error_message", "")).lower()
            if "wrong tool" in err_msg or "inappropriate tool" in err_msg:
                failed_node = err.get("node_id") or self._find_first_node(norm_arch)
                return RootCauseDiagnosis(
                    case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                    failure_category=FailureCategory.WRONG_TOOL_SELECTION,
                    severity=Severity.MEDIUM,
                    failed_node_id=failed_node,
                    failure_source=FailureSource.TOOL_INVOCATION,
                    symptom=f"Selected tool cannot satisfy required capability: {err.get('error_message')}",
                    summary=f"Inappropriate tool selected at node '{failed_node}'.",
                    root_cause=f"Node '{failed_node}' selected an unsuitable tool for the required subtask.",
                    evidence=[
                        DiagnosisEvidence(
                            source="node_execution",
                            field="tool_selection",
                            observed=err.get("error_message"),
                            expected="Appropriate tool selection",
                        )
                    ],
                    contributing_factors=["Tool descriptions in prompt lack clear differentiation"],
                    confidence=0.85,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.TOOL_REMOVE,
                            target=failed_node or "graph",
                            rationale="Remove inappropriate tool from node tool list to eliminate misdirection.",
                            expected_effect="Guides node to invoke the correct specialized tool.",
                            confidence=0.85,
                        )
                    ],
                    affected_capabilities=["tool_selection"],
                )
        return None

    def _check_premature_termination(
        self, norm_exec: Dict[str, Any], norm_arch: Dict[str, Any]
    ) -> Optional[RootCauseDiagnosis]:
        """Detect execution halt prior to executing terminal nodes or producing required output."""
        step_history = norm_exec.get("step_history", [])
        executed_nodes = {s.get("node_id") for s in step_history if s.get("node_id")}

        terminal_nodes = norm_arch.get("terminal_node_ids", [])
        if terminal_nodes:
            executed_terminals = [t for t in terminal_nodes if t in executed_nodes]
            if not executed_terminals and norm_exec.get("status") in ["failed", "completed"]:
                last_node = step_history[-1].get("node_id") if step_history else norm_arch.get("entry_node_id")
                return RootCauseDiagnosis(
                    case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                    failure_category=FailureCategory.PREMATURE_TERMINATION,
                    severity=Severity.HIGH,
                    failed_node_id=last_node,
                    failure_source=FailureSource.NODE_EXECUTION,
                    symptom=f"Workflow halted before reaching any terminal nodes {terminal_nodes}.",
                    summary=f"Premature termination: terminal nodes {terminal_nodes} were never reached.",
                    root_cause="Execution flow stalled or routed off-path prior to entering designated terminal nodes.",
                    evidence=[
                        DiagnosisEvidence(
                            source="graph_execution",
                            field="executed_nodes",
                            observed=list(executed_nodes),
                            expected=terminal_nodes,
                        )
                    ],
                    contributing_factors=["Missing routing edge or unhandled branch condition"],
                    confidence=0.92,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.TOPOLOGY_CHANGE,
                            target=last_node or "graph",
                            rationale=f"Ensure direct edge transition from '{last_node}' to terminal node '{terminal_nodes[0]}'.",
                            expected_effect="Guarantees workflow execution reaches terminal stage.",
                            confidence=0.90,
                        )
                    ],
                    affected_capabilities=["workflow_routing", "terminal_execution"],
                )
        return None

    def _check_output_schema_error(
        self,
        norm_exec: Dict[str, Any],
        norm_task: Dict[str, Any],
        norm_arch: Dict[str, Any],
    ) -> Optional[RootCauseDiagnosis]:
        """Detect missing required fields in terminal output."""
        required_schema = norm_task.get("output_schema", {})
        if not required_schema:
            return None

        actual_output = norm_exec.get("output", {}) or norm_exec.get("node_outputs", {})
        missing_fields = []
        if isinstance(required_schema, dict):
            # Check required properties if json schema
            props = required_schema.get("properties", {})
            required_keys = required_schema.get("required", list(props.keys()))
            for rk in required_keys:
                if rk not in actual_output:
                    missing_fields.append(rk)

        if missing_fields:
            terminal_node = norm_arch.get("terminal_node_ids", [None])[0] or self._find_first_node(norm_arch)
            return RootCauseDiagnosis(
                case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                failure_category=FailureCategory.OUTPUT_SCHEMA_ERROR,
                severity=Severity.HIGH,
                failed_node_id=terminal_node,
                failure_source=FailureSource.NODE_EXECUTION,
                symptom=f"Terminal output missing mandatory schema keys: {missing_fields}",
                summary=f"Output schema validation failure: missing {missing_fields}.",
                root_cause=f"Terminal node '{terminal_node}' did not format its output structure with required keys {missing_fields}.",
                evidence=[
                    DiagnosisEvidence(
                        source="evaluation",
                        field="output_schema",
                        observed=list(actual_output.keys()) if isinstance(actual_output, dict) else type(actual_output).__name__,
                        expected=missing_fields,
                    )
                ],
                contributing_factors=["Unstructured terminal response prompt"],
                confidence=0.92,
                recommended_mutations=[
                    RecommendedMutation(
                        mutation_type=MutationType.PROMPT_CHANGE,
                        target=terminal_node or "graph",
                        rationale=f"Update terminal node prompt to enforce JSON output matching schema {missing_fields}.",
                        expected_effect="Produces valid structured JSON output containing all required fields.",
                        confidence=0.92,
                    )
                ],
                affected_capabilities=["output_formatting", "schema_compliance"],
            )
        return None

    def _check_missing_verification(
        self,
        norm_exec: Dict[str, Any],
        norm_task: Dict[str, Any],
        norm_arch: Dict[str, Any],
        bench_ctx: Dict[str, Any],
    ) -> Optional[RootCauseDiagnosis]:
        """Detect scenarios where evaluator demands verification but architecture lacks verifier."""
        requires_verification = (
            norm_task.get("requires_verification", False)
            or bench_ctx.get("requires_verification", False)
            or bool(bench_ctx.get("ground_truth", {}).get("verification_rules"))
        )
        if not requires_verification:
            return None

        # Check if architecture has any verification node
        nodes = self._get_nodes_list(norm_arch)
        has_verifier = any(
            "verif" in n.get("role", "").lower() or "auditor" in n.get("role", "").lower() or "verif" in n.get("node_id", "").lower()
            for n in nodes
        )

        if not has_verifier:
            terminal_node = norm_arch.get("terminal_node_ids", [None])[0] or self._find_first_node(norm_arch)
            return RootCauseDiagnosis(
                case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                failure_category=FailureCategory.MISSING_VERIFICATION,
                severity=Severity.HIGH,
                failed_node_id=terminal_node,
                failure_source=FailureSource.ARCHITECTURE_GENERATION,
                symptom="Workflow committed conclusions without an independent verification gate.",
                summary="Architecture lacks a mandatory verification / audit node.",
                root_cause="The architecture generator synthesized an unverified feed-forward DAG lacking a post-generation verification stage.",
                evidence=[
                    DiagnosisEvidence(
                        source="architecture",
                        field="nodes",
                        observed=[n.get("role") for n in nodes],
                        expected="Node with verification / audit role",
                    )
                ],
                contributing_factors=["Architecture generation omitted verification topology pattern"],
                confidence=0.88,
                recommended_mutations=[
                    RecommendedMutation(
                        mutation_type=MutationType.ADD_VERIFIER,
                        target=terminal_node or "graph",
                        rationale="Insert an independent verifier node prior to final commit.",
                        expected_effect="Gates output validity and detects errors before termination.",
                        confidence=0.88,
                    )
                ],
                affected_capabilities=["verification", "quality_control"],
            )
        return None

    def _check_arithmetic_mismatch(
        self,
        norm_exec: Dict[str, Any],
        bench_ctx: Dict[str, Any],
        norm_arch: Dict[str, Any],
    ) -> Optional[RootCauseDiagnosis]:
        """Detect numerical differences between computed output and expected ground truth."""
        actual_output = norm_exec.get("output", {}) or norm_exec.get("node_outputs", {})
        gt = bench_ctx.get("ground_truth", {})
        if not gt:
            return None

        # Check total discrepancy if applicable
        if "total_discrepancy" in gt:
            exp_disc = str(gt["total_discrepancy"])
            act_disc = str(actual_output.get("total_discrepancy", actual_output.get("discrepancy", "")))
            if act_disc and act_disc != exp_disc:
                failed_node = self._find_first_node(norm_arch) or "graph"
                return RootCauseDiagnosis(
                    case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
                    failure_category=FailureCategory.ARITHMETIC_MISMATCH,
                    severity=Severity.MEDIUM,
                    failed_node_id=failed_node,
                    failure_source=FailureSource.NODE_EXECUTION,
                    symptom=f"Calculated discrepancy '{act_disc}' does not match expected '{exp_disc}'.",
                    summary="Deterministic arithmetic discrepancy calculation mismatch.",
                    root_cause=f"Calculation node produced numerical value '{act_disc}', conflicting with ground truth '{exp_disc}'.",
                    evidence=[
                        DiagnosisEvidence(
                            source="benchmark_ground_truth",
                            field="total_discrepancy",
                            observed=act_disc,
                            expected=exp_disc,
                        )
                    ],
                    contributing_factors=["Rounding error or erroneous arithmetic operator in calculation"],
                    confidence=0.85,
                    recommended_mutations=[
                        RecommendedMutation(
                            mutation_type=MutationType.TOOL_ADD,
                            target=failed_node,
                            rationale="Bind deterministic precision calculation tool to eliminate numerical variance.",
                            expected_effect="Guarantees exact arithmetic reconciliation.",
                            confidence=0.85,
                        )
                    ],
                    affected_capabilities=["arithmetic_computation"],
                )
        return None

    def _handle_unknown_or_scorecard_fallback(
        self,
        norm_exec: Dict[str, Any],
        norm_arch: Dict[str, Any],
        scorecard_metrics: Optional[Dict[str, Any]],
    ) -> RootCauseDiagnosis:
        """Handle unclassified failures with honest low-confidence UNKNOWN_FAILURE to prevent false certainty."""
        evidence = []
        symptom = "Execution did not satisfy success criteria."
        root_cause = "Insufficient conclusive telemetry signals to determine specific root cause without false certainty."
        contributing_factors = []
        confidence = 0.40
        severity = Severity.LOW

        if scorecard_metrics:
            acc = scorecard_metrics.get("accuracy", 1.0)
            rel = scorecard_metrics.get("reliability", 1.0)
            evidence.append(
                DiagnosisEvidence(
                    source="scorecard",
                    field="metrics",
                    observed={"accuracy": acc, "reliability": rel},
                    expected={"accuracy": 1.0, "reliability": 1.0},
                )
            )
            if rel < 1.0:
                symptom = "Scorecard indicates execution reliability degradation (runtime failure)."
                contributing_factors.append("Reliability dropped below 1.0 indicating runtime or schema breakdown.")
                severity = Severity.HIGH
            elif acc < 0.8:
                symptom = "Scorecard indicates output accuracy degradation while runtime reliability was preserved."
                contributing_factors.append("Accuracy degraded: semantic or business logic failure while DAG structure completed successfully.")
                severity = Severity.MEDIUM

        failed_node = self._find_first_node(norm_arch)

        return RootCauseDiagnosis(
            case_execution_id=norm_exec.get("case_execution_id") or norm_exec.get("execution_id"),
            failure_category=FailureCategory.UNKNOWN_FAILURE,
            severity=severity,
            failed_node_id=failed_node,
            failure_source=FailureSource.NODE_EXECUTION,
            symptom=symptom,
            summary="Unclassified failure: evidence is insufficient for deterministic taxonomy attribution.",
            root_cause=root_cause,
            evidence=evidence,
            contributing_factors=contributing_factors,
            confidence=confidence,
            recommended_mutations=[],
            affected_capabilities=[],
            metadata={"diagnostic_mode": "no_false_certainty"},
        )

    # -------------------------------------------------------------------------
    # Clustering and Prioritization
    # -------------------------------------------------------------------------

    def cluster_failures(self, diagnoses: List[RootCauseDiagnosis]) -> List[FailureCluster]:
        """Deterministically group similar failures by failure category and root-cause pattern."""
        groups: Dict[tuple, List[RootCauseDiagnosis]] = defaultdict(list)

        for diag in diagnoses:
            # Create a normalized root cause key (category + first 60 chars of root cause)
            norm_key = (diag.failure_category, diag.root_cause[:80].strip())
            groups[norm_key].append(diag)

        clusters: List[FailureCluster] = []
        cluster_idx = 1
        for (category, pattern), diag_list in groups.items():
            affected_nodes = sorted(
                list({d.failed_node_id for d in diag_list if d.failed_node_id})
            )
            # Gather unique recommended mutations
            seen_mutations = set()
            mutations: List[RecommendedMutation] = []
            for d in diag_list:
                for m in d.recommended_mutations:
                    m_key = (m.mutation_type, m.target)
                    if m_key not in seen_mutations:
                        seen_mutations.add(m_key)
                        mutations.append(m)

            cluster = FailureCluster(
                cluster_id=f"cluster-{cluster_idx:03d}",
                category=category,
                root_cause_pattern=pattern,
                count=len(diag_list),
                diagnoses=diag_list,
                affected_nodes=affected_nodes,
                recommended_mutations=mutations,
            )
            clusters.append(cluster)
            cluster_idx += 1

        return self.prioritize_clusters(clusters)

    def prioritize_clusters(
        self,
        clusters: List[FailureCluster],
        scorecard_impact: Optional[Dict[str, float]] = None,
    ) -> List[FailureCluster]:
        """Assign interpretable priority scores to clusters based on frequency, severity, and confidence.

        Formula:
        Priority = count * severity_weight * avg_confidence * benchmark_multiplier
        where:
        - critical: 4.0
        - high: 3.0
        - medium: 2.0
        - low: 1.0
        """
        severity_weights = {
            Severity.CRITICAL: 4.0,
            Severity.HIGH: 3.0,
            Severity.MEDIUM: 2.0,
            Severity.LOW: 1.0,
        }

        bench_mult = 1.0
        if scorecard_impact:
            acc_drop = max(0.0, 1.0 - scorecard_impact.get("accuracy", 1.0))
            rel_drop = max(0.0, 1.0 - scorecard_impact.get("reliability", 1.0))
            bench_mult += (acc_drop * 1.5) + (rel_drop * 2.0)

        for cluster in clusters:
            if not cluster.diagnoses:
                cluster.priority_score = 0.0
                continue

            # Compute avg severity weight
            total_sev = sum(severity_weights.get(d.severity, 2.0) for d in cluster.diagnoses)
            avg_sev = total_sev / len(cluster.diagnoses)

            # Compute avg confidence
            total_conf = sum(d.confidence for d in cluster.diagnoses)
            avg_conf = total_conf / len(cluster.diagnoses)

            # Calculate transparent priority
            cluster.priority_score = round(cluster.count * avg_sev * avg_conf * bench_mult, 3)

        # Sort clusters descending by priority_score, then count
        return sorted(clusters, key=lambda c: (c.priority_score, c.count), reverse=True)

    # -------------------------------------------------------------------------
    # Persistence Helpers
    # -------------------------------------------------------------------------

    async def save_diagnosis(
        self,
        diagnosis: RootCauseDiagnosis,
        repository: FailureDiagnosisRepository,
    ) -> FailureDiagnosisRecord:
        """Persist a diagnosis using the existing failure_diagnoses repository abstraction."""
        record = diagnosis.to_db_record()
        return await repository.create(record)

    async def get_diagnosis(
        self,
        diagnosis_id: UUID,
        repository: FailureDiagnosisRepository,
    ) -> Optional[RootCauseDiagnosis]:
        """Retrieve a stored diagnosis by ID and deserialize to RootCauseDiagnosis."""
        record = await repository.get(diagnosis_id)
        if not record:
            return None
        return RootCauseDiagnosis.from_db_record(record)

    async def get_for_case_execution(
        self,
        case_execution_id: UUID,
        repository: FailureDiagnosisRepository,
    ) -> Optional[RootCauseDiagnosis]:
        """Retrieve a diagnosis for a specific case execution."""
        record = await repository.get_for_case_execution(case_execution_id)
        if not record:
            return None
        return RootCauseDiagnosis.from_db_record(record)

    # -------------------------------------------------------------------------
    # Normalization Helpers
    # -------------------------------------------------------------------------

    def _normalize_execution(self, exec_rec: Any) -> Dict[str, Any]:
        """Normalize various execution representations into a uniform dict."""
        if hasattr(exec_rec, "model_dump"):
            return exec_rec.model_dump(mode="json")
        if isinstance(exec_rec, dict):
            return exec_rec
        return {"raw": str(exec_rec)}

    def _normalize_task_spec(self, task_spec: Optional[Any]) -> Dict[str, Any]:
        if task_spec is None:
            return {}
        if hasattr(task_spec, "model_dump"):
            return task_spec.model_dump(mode="json")
        if isinstance(task_spec, dict):
            return task_spec
        return {}

    def _normalize_architecture(self, arch: Optional[Any]) -> Dict[str, Any]:
        if arch is None:
            return {}
        if hasattr(arch, "model_dump"):
            return arch.model_dump(mode="json")
        if isinstance(arch, dict):
            return arch
        return {}

    def _get_nodes_list(self, norm_arch: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize nodes whether represented as a dictionary {node_id: node} or a list."""
        nodes = norm_arch.get("nodes", {})
        if isinstance(nodes, dict):
            return list(nodes.values())
        if isinstance(nodes, list):
            return nodes
        return []

    def _find_first_node(self, norm_arch: Dict[str, Any]) -> Optional[str]:
        nodes = self._get_nodes_list(norm_arch)
        if nodes:
            first = nodes[0]
            if isinstance(first, dict):
                return first.get("node_id")
            elif hasattr(first, "node_id"):
                return first.node_id
        return norm_arch.get("entry_node_id")
