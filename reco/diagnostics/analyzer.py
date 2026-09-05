"""Failure Analyzer for isolating root causes and generating diagnostic reports."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union

from reco.benchmarks.base import BenchmarkCase, BenchmarkSplit, BenchmarkSuite
from reco.diagnostics.taxonomy import (
    CATEGORY_DEFAULT_MUTATORS,
    CATEGORY_DESCRIPTIONS,
    DiagnosticReport,
    FailureCategory,
    FailureDiagnostic,
)
from reco.engine.models import AgentArchitecture, NodeStatus, NodeType
from reco.engine.runtime import AgentRuntime, ExecutionResult
from reco.evaluators.scorecard import CaseEvaluationResult, Scorecard, ScorecardEvaluator
from reco.tools.registry import ToolRegistry


class FailureAnalyzer:
    """Ingests execution traces, isolates root causes from symptoms, and builds diagnostic reports."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry or ToolRegistry.create_reconciliation_default()

    def analyze_case(
        self,
        case: BenchmarkCase,
        exec_result: ExecutionResult,
        architecture: Optional[AgentArchitecture] = None,
        case_eval: Optional[CaseEvaluationResult] = None
    ) -> Optional[FailureDiagnostic]:
        """Isolate root cause from intermediate symptoms for a single benchmark test case failure.

        Args:
            case: The benchmark test case.
            exec_result: Execution result and step telemetry.
            architecture: Optional AgentArchitecture executed.
            case_eval: Optional precomputed CaseEvaluationResult.

        Returns:
            FailureDiagnostic if the case failed, or None if the case passed.
        """
        # Determine if case passed
        is_reliable = exec_result.status == NodeStatus.COMPLETED and exec_result.error is None
        no_node_failures = not any(r.status == NodeStatus.FAILED for r in exec_result.node_records.values())
        clean_run = is_reliable and no_node_failures

        is_accurate = False
        if clean_run:
            is_accurate = case.eval_match(exec_result.final_output)

        if clean_run and is_accurate:
            return None  # No failure

        # Isolate root cause from symptoms
        return self._isolate_root_cause(
            case=case,
            exec_result=exec_result,
            architecture=architecture,
            case_eval=case_eval
        )

    def _isolate_root_cause(
        self,
        case: BenchmarkCase,
        exec_result: ExecutionResult,
        architecture: Optional[AgentArchitecture],
        case_eval: Optional[CaseEvaluationResult]
    ) -> FailureDiagnostic:
        """Rule engine mapping symptoms to the 12-category diagnostic taxonomy."""
        symptoms: List[str] = []
        error_str = (exec_result.error or "")
        node_records = exec_result.node_records

        # Collect observable symptoms
        if exec_result.status == NodeStatus.FAILED:
            symptoms.append(f"Overall execution status failed: {error_str[:120]}")
        for nid, rec in node_records.items():
            if rec.status == NodeStatus.FAILED:
                symptoms.append(f"Node '{nid}' ({rec.node_type.value}) failed: {str(rec.error)[:100]}")
            elif rec.status == NodeStatus.SKIPPED:
                symptoms.append(f"Node '{nid}' was skipped due to upstream dependency failure")

        latency_budget = 5000.0
        if architecture and architecture.task_spec and architecture.task_spec.latency_budget_ms:
            latency_budget = architecture.task_spec.latency_budget_ms

        # ---------------------------------------------------------------------
        # 1. TIMEOUT_EXCEEDED
        # ---------------------------------------------------------------------
        if (
            exec_result.total_latency_ms > latency_budget
            or "timeout" in error_str.lower()
            or "latency budget" in error_str.lower()
        ):
            return FailureDiagnostic(
                case_id=case.case_id,
                category=FailureCategory.TIMEOUT_EXCEEDED,
                root_cause=f"Execution latency ({exec_result.total_latency_ms:.2f}ms) exceeded budget ({latency_budget:.2f}ms).",
                symptoms=symptoms + [f"Elapsed time {exec_result.total_latency_ms:.2f}ms > {latency_budget:.2f}ms"],
                remedy_suggestion="RetryPolicyMutator: Optimize node concurrency or calibrate node timeout threshold.",
                target_node_id=self._find_slowest_or_failed_node(node_records),
                recommended_mutator="RetryPolicyMutator",
                confidence=0.95,
                metadata={"latency_ms": exec_result.total_latency_ms, "budget_ms": latency_budget}
            )

        # ---------------------------------------------------------------------
        # 2. CONTEXT_OVERFLOW
        # ---------------------------------------------------------------------
        if any(
            kw in error_str.lower()
            for kw in [
                "context_overflow", "context overflow", "context length",
                "token limit", "payload limit", "max payload", "maximum context"
            ]
        ):
            return FailureDiagnostic(
                case_id=case.case_id,
                category=FailureCategory.CONTEXT_OVERFLOW,
                root_cause="Input payload or intermediate state exceeded maximum context/token limit.",
                symptoms=symptoms + ["Payload size exceeded memory boundary"],
                remedy_suggestion="PromptMutator: Inject data chunking or summarization instructions.",
                target_node_id=self._find_failed_node_id(node_records),
                recommended_mutator="PromptMutator",
                confidence=0.90
            )

        # ---------------------------------------------------------------------
        # 3. RETRY_EXHAUSTION
        # ---------------------------------------------------------------------
        if any(
            kw in error_str.lower()
            for kw in [
                "retry_exhaustion", "retry exhaustion", "retries exhausted",
                "max retries exceeded", "max retries", "retry budget", "attempts failed"
            ]
        ):
            return FailureDiagnostic(
                case_id=case.case_id,
                category=FailureCategory.RETRY_EXHAUSTION,
                root_cause="Brittle node repeatedly failed without recovery, exhausting maximum retry attempts.",
                symptoms=symptoms + ["All configured retry attempts failed"],
                remedy_suggestion="RetryPolicyMutator: Configure exponential backoff and jitter on brittle node.",
                target_node_id=self._find_failed_node_id(node_records),
                recommended_mutator="RetryPolicyMutator",
                confidence=0.92
            )

        # ---------------------------------------------------------------------
        # 4. STATE_CORRUPTION
        # ---------------------------------------------------------------------
        if any(
            kw in error_str.lower()
            for kw in [
                "state_corruption", "state corruption", "state key",
                "corrupted state", "unhashable", "keyerror: 'state", "invalid state"
            ]
        ):
            return FailureDiagnostic(
                case_id=case.case_id,
                category=FailureCategory.STATE_CORRUPTION,
                root_cause="Execution state store suffered data corruption or lost intermediate keys across step transitions.",
                symptoms=symptoms + ["State key lookup failure during node transition"],
                remedy_suggestion="TopologyMutator: Repair state dependency links and ensure immutable propagation.",
                target_node_id=self._find_failed_node_id(node_records),
                recommended_mutator="TopologyMutator",
                confidence=0.88
            )

        # ---------------------------------------------------------------------
        # 5. TOOL_PARAMETER_ERROR
        # ---------------------------------------------------------------------
        for nid, rec in node_records.items():
            if rec.status == NodeStatus.FAILED and rec.node_type == NodeType.TOOL:
                err = (rec.error or "").lower()
                if any(
                    kw in err
                    for kw in [
                        "parameter validation failed",
                        "missing required parameter",
                        "must be an array",
                        "must be an object",
                        "must be a string",
                        "must be a number",
                        "invalid parameter"
                    ]
                ):
                    return FailureDiagnostic(
                        case_id=case.case_id,
                        category=FailureCategory.TOOL_PARAMETER_ERROR,
                        root_cause=f"Tool node '{nid}' rejected arguments: {rec.error}",
                        symptoms=symptoms + [f"Parameter validation failed at {nid}"],
                        remedy_suggestion="PromptMutator: Inject schema formatting instructions to ensure valid tool parameters.",
                        target_node_id=nid,
                        recommended_mutator="PromptMutator",
                        confidence=0.95,
                        metadata={"node_id": nid, "error": rec.error}
                    )

        # ---------------------------------------------------------------------
        # 6. ROUTING_MISDIRECT
        # ---------------------------------------------------------------------
        if architecture:
            node_ids = {n.id for n in architecture.nodes}
            # Check for disconnected graph or missing dependencies
            has_routing_err = False
            routing_reason = ""
            for n in architecture.nodes:
                for dep in n.dependencies:
                    if dep not in node_ids:
                        has_routing_err = True
                        routing_reason = f"Node '{n.id}' depends on non-existent node '{dep}'"
                        break
            if has_routing_err or "routing" in error_str.lower() or "disconnected" in error_str.lower():
                return FailureDiagnostic(
                    case_id=case.case_id,
                    category=FailureCategory.ROUTING_MISDIRECT,
                    root_cause=f"Graph routing misdirected data flow: {routing_reason or error_str}",
                    symptoms=symptoms + ["Prerequisite node bypassed or disconnected"],
                    remedy_suggestion="TopologyMutator: Rewire DAG dependencies and restore data flow edges.",
                    target_node_id="reasoning_node",
                    recommended_mutator="TopologyMutator",
                    confidence=0.90
                )

        # ---------------------------------------------------------------------
        # 7. UNHANDLED_EXCEPTION
        # ---------------------------------------------------------------------
        if exec_result.status == NodeStatus.FAILED:
            failed_node = self._find_failed_node_id(node_records)
            return FailureDiagnostic(
                case_id=case.case_id,
                category=FailureCategory.UNHANDLED_EXCEPTION,
                root_cause=f"Unhandled runtime exception during execution: {error_str}",
                symptoms=symptoms,
                remedy_suggestion="RetryPolicyMutator: Enclose node in defensive error boundary and retry policy.",
                target_node_id=failed_node,
                recommended_mutator="RetryPolicyMutator",
                confidence=0.85,
                metadata={"error": error_str}
            )

        # ---------------------------------------------------------------------
        # Clean execution, but ground truth mismatch (Inaccurate Output)
        # ---------------------------------------------------------------------
        actual_output = exec_result.final_output
        expected_output = case.expected_output

        # ---------------------------------------------------------------------
        # 8. TOOL_SELECTION_ERROR
        # ---------------------------------------------------------------------
        # Check A: Missing reconciliation tools when task is reconciliation
        arch_tool_names = [n.tool_name for n in architecture.nodes if n.type == NodeType.TOOL and n.tool_name] if architecture else []
        reco_tools = {"exact_reconcile", "smart_reconcile"}
        has_reco_tool = any(t in reco_tools for t in arch_tool_names)

        if not has_reco_tool and case.category in ("exact_match", "missing_records", "amount_mismatch", "duplicate_records", "format_variation"):
            return FailureDiagnostic(
                case_id=case.case_id,
                category=FailureCategory.TOOL_SELECTION_ERROR,
                root_cause="Architecture lacks dedicated reconciliation tools (exact_reconcile or smart_reconcile).",
                symptoms=symptoms + ["Reconciliation payload absent; only generic analytical tools present in graph"],
                remedy_suggestion="ToolAssignmentMutator: Attach smart_reconcile or exact_reconcile from ToolRegistry.",
                target_node_id="input_node",
                recommended_mutator="ToolAssignmentMutator",
                confidence=0.98,
                metadata={"active_tools": arch_tool_names}
            )

        # Check B: Format variations failure when using exact_reconcile
        if "exact_reconcile" in arch_tool_names and "smart_reconcile" not in arch_tool_names:
            is_format_case = case.category == "format_variation" or self._has_format_variations(case.input_data)
            if is_format_case:
                return FailureDiagnostic(
                    case_id=case.case_id,
                    category=FailureCategory.TOOL_SELECTION_ERROR,
                    root_cause="Tool 'exact_reconcile' lacks capability to parse currency formatting, timestamps, or case variations.",
                    symptoms=symptoms + [
                        "Discrepancy detected on formatted records",
                        f"Matched {self._extract_matched_count(actual_output)} records, expected {expected_output.get('matched_count')}"
                    ],
                    remedy_suggestion="ToolAssignmentMutator: Replace exact_reconcile with smart_reconcile to support fuzzy/normalized format matching.",
                    target_node_id="tool_exact_reconcile",
                    recommended_mutator="ToolAssignmentMutator",
                    confidence=0.96,
                    metadata={"case_category": case.category, "current_tool": "exact_reconcile"}
                )

        # ---------------------------------------------------------------------
        # 9. SCHEMA_VIOLATION
        # ---------------------------------------------------------------------
        if not isinstance(actual_output, dict):
            return FailureDiagnostic(
                case_id=case.case_id,
                category=FailureCategory.SCHEMA_VIOLATION,
                root_cause=f"Final output is not a JSON object/dict (got {type(actual_output).__name__}).",
                symptoms=symptoms + ["Output root payload violated object schema"],
                remedy_suggestion="PromptMutator: Enforce JSON dictionary output structure in output_node.",
                target_node_id="output_node",
                recommended_mutator="PromptMutator",
                confidence=0.95
            )

        # Check missing required keys from expected_output
        missing_keys = [k for k in expected_output if k not in actual_output]
        if missing_keys and len(missing_keys) >= 2:
            return FailureDiagnostic(
                case_id=case.case_id,
                category=FailureCategory.SCHEMA_VIOLATION,
                root_cause=f"Output payload omitted required ground-truth schema fields: {missing_keys}",
                symptoms=symptoms + [f"Missing expected keys: {missing_keys}"],
                remedy_suggestion="PromptMutator: Enforce output formatting schema and explicit key requirements.",
                target_node_id="output_node",
                recommended_mutator="PromptMutator",
                confidence=0.90,
                metadata={"missing_keys": missing_keys}
            )

        # ---------------------------------------------------------------------
        # 10. VERIFICATION_MISS
        # ---------------------------------------------------------------------
        has_verifier = architecture and any(n.type == NodeType.VERIFIER for n in architecture.nodes)
        verifier_record = node_records.get("verifier_node")
        verifier_out = verifier_record.output if verifier_record else None

        if not has_verifier:
            return FailureDiagnostic(
                case_id=case.case_id,
                category=FailureCategory.VERIFICATION_MISS,
                root_cause="Architecture lacks a verifier guardrail node prior to output delivery.",
                symptoms=symptoms + ["Unverified inaccurate payload delivered directly to output"],
                remedy_suggestion="VerifierNodeMutator: Inject a dedicated verifier_node prior to output_node.",
                target_node_id="output_node",
                recommended_mutator="VerifierNodeMutator",
                confidence=0.90
            )

        if isinstance(verifier_out, dict) and verifier_out.get("verified") is True:
            # Verifier said it's verified, but ground truth match failed!
            return FailureDiagnostic(
                case_id=case.case_id,
                category=FailureCategory.VERIFICATION_MISS,
                root_cause="Verifier node approved an inaccurate result without flagging discrepancies.",
                symptoms=symptoms + ["Verifier reported verified=True on inaccurate output"],
                remedy_suggestion="VerifierNodeMutator: Strengthen verifier rules to assert ledger match consistency.",
                target_node_id="verifier_node",
                recommended_mutator="VerifierNodeMutator",
                confidence=0.88,
                metadata={"verifier_output": verifier_out}
            )

        # ---------------------------------------------------------------------
        # 11. PROMPT_AMBIGUITY
        # ---------------------------------------------------------------------
        reasoning_record = node_records.get("reasoning_node")
        if reasoning_record and isinstance(reasoning_record.output, dict):
            obs = reasoning_record.output.get("observations", [])
            summary = reasoning_record.output.get("synthesis_summary", "")
            if not obs or not summary or summary.strip() == "":
                return FailureDiagnostic(
                    case_id=case.case_id,
                    category=FailureCategory.PROMPT_AMBIGUITY,
                    root_cause="Reasoning node prompt produced ambiguous synthesis without substantive deduction.",
                    symptoms=symptoms + ["Reasoning observations empty or vague"],
                    remedy_suggestion="PromptMutator: Inject domain-specific reasoning rules and few-shot constraints.",
                    target_node_id="reasoning_node",
                    recommended_mutator="PromptMutator",
                    confidence=0.82
                )

        # ---------------------------------------------------------------------
        # 12. MODEL_CAPABILITY_LIMIT (Default for subtle logic edge-cases)
        # ---------------------------------------------------------------------
        return FailureDiagnostic(
            case_id=case.case_id,
            category=FailureCategory.MODEL_CAPABILITY_LIMIT,
            root_cause="Complex multi-condition scenario exceeded single-pass deductive reasoning limits.",
            symptoms=symptoms + [f"Output mismatch on difficult scenario: {case.description}"],
            remedy_suggestion="TopologyMutator: Add ensemble reasoning path or secondary verification branch.",
            target_node_id="reasoning_node",
            recommended_mutator="TopologyMutator",
            confidence=0.75,
            metadata={"case_category": case.category, "expected": expected_output, "actual": actual_output}
        )

    def analyze_scorecard(
        self,
        scorecard: Scorecard,
        suite_or_cases: Union[BenchmarkSuite, List[BenchmarkCase]],
        architecture: AgentArchitecture,
        runtime_results: Optional[Dict[str, ExecutionResult]] = None
    ) -> DiagnosticReport:
        """Construct a comprehensive DiagnosticReport from evaluated Scorecard telemetry.

        Args:
            scorecard: Empirical 4-axis scorecard from benchmark run.
            suite_or_cases: BenchmarkSuite or list of BenchmarkCase objects.
            architecture: The AgentArchitecture evaluated.
            runtime_results: Optional map of case_id -> ExecutionResult.

        Returns:
            DiagnosticReport mapping each failed case to its isolated root cause.
        """
        if isinstance(suite_or_cases, BenchmarkSuite):
            case_map = {c.case_id: c for c in suite_or_cases.cases}
        else:
            case_map = {c.case_id: c for c in suite_or_cases}

        failure_diagnostics: List[FailureDiagnostic] = []
        category_counts: Dict[str, int] = {}

        for cr in scorecard.case_results:
            if cr.is_accurate and cr.is_reliable:
                continue  # Case passed

            case = case_map.get(cr.case_id)
            if not case:
                continue

            # Retrieve or construct execution result
            if runtime_results and cr.case_id in runtime_results:
                exec_res = runtime_results[cr.case_id]
            else:
                exec_res = ExecutionResult(
                    architecture_id=architecture.id,
                    task_goal=architecture.task_spec.goal,
                    status=NodeStatus.COMPLETED if cr.is_reliable else NodeStatus.FAILED,
                    final_output=cr.actual_output,
                    node_records={},
                    execution_order=[],
                    total_latency_ms=cr.latency_ms,
                    quality_score=0.0,
                    error=cr.error
                )

            diag = self.analyze_case(
                case=case,
                exec_result=exec_res,
                architecture=architecture,
                case_eval=cr
            )
            if diag:
                failure_diagnostics.append(diag)
                cat_key = diag.category.value
                category_counts[cat_key] = category_counts.get(cat_key, 0) + 1

        summary = (
            f"Diagnosed {len(failure_diagnostics)} failures across {scorecard.total_cases} cases for "
            f"architecture '{architecture.name}'. Primary root causes: "
            + ", ".join(f"{k} ({v})" for k, v in sorted(category_counts.items(), key=lambda x: -x[1]))
            if category_counts else "All cases passed successfully; zero failures diagnosed."
        )

        return DiagnosticReport(
            architecture_id=architecture.id,
            total_cases=scorecard.total_cases,
            passed_cases=scorecard.accurate_cases,
            failed_cases=len(failure_diagnostics),
            failure_diagnostics=failure_diagnostics,
            category_counts=category_counts,
            summary=summary
        )

    def analyze(
        self,
        architecture: AgentArchitecture,
        suite_or_cases: Union[BenchmarkSuite, List[BenchmarkCase]],
        runtime: Optional[AgentRuntime] = None,
        split: Optional[Union[BenchmarkSplit, str]] = None
    ) -> DiagnosticReport:
        """End-to-end convenience method: evaluates architecture and diagnoses failures."""
        rt = runtime or AgentRuntime(tool_registry=self.tool_registry)
        evaluator = ScorecardEvaluator(runtime=rt)
        scorecard = evaluator.evaluate(
            architecture=architecture,
            suite_or_cases=suite_or_cases,
            split=split
        )
        return self.analyze_scorecard(scorecard, suite_or_cases, architecture)

    # -------------------------------------------------------------------------
    # Helper Utilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _find_failed_node_id(node_records: Dict[str, Any]) -> Optional[str]:
        for nid, rec in node_records.items():
            if getattr(rec, "status", None) == NodeStatus.FAILED:
                return nid
        return None

    @staticmethod
    def _find_slowest_or_failed_node(node_records: Dict[str, Any]) -> str:
        for nid, rec in node_records.items():
            if getattr(rec, "status", None) == NodeStatus.FAILED:
                return nid
        if node_records:
            slowest = max(node_records.items(), key=lambda x: getattr(x[1], "latency_ms", 0.0))
            return slowest[0]
        return "reasoning_node"

    @staticmethod
    def _has_format_variations(input_data: Dict[str, Any]) -> bool:
        """Detect currency symbols or casing anomalies in input transaction data."""
        for key in ("target_records", "source_records"):
            records = input_data.get(key, [])
            for r in records:
                if not isinstance(r, dict):
                    continue
                amt = str(r.get("amount", ""))
                rid = str(r.get("id", ""))
                date_str = str(r.get("date", ""))
                if "$" in amt or "," in amt or rid != rid.strip().upper() or "T" in date_str or "/" in date_str:
                    return True
        return False

    @staticmethod
    def _extract_matched_count(actual_output: Any) -> int:
        if isinstance(actual_output, dict):
            if "matched_count" in actual_output:
                return int(actual_output["matched_count"])
            if "matched_ids" in actual_output and isinstance(actual_output["matched_ids"], list):
                return len(actual_output["matched_ids"])
        return 0
