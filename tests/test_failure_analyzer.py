"""Tests for the Failure Analyzer, Root Cause Diagnoser, and Taxonomy.

Covers all 41 requirements:
- Model validation, taxonomy enums, bounded confidence, mutation recommendation validation
- All 12 taxonomy failure categories
- Failure location and source identification
- Structured evidence traces (tool events, ground truth, architecture)
- Symptom vs root cause separation, contributing factors, no false certainty
- Mutation recommendations (prompt, tool, topology, verifier, model/routing)
- Failure clustering, frequency, and prioritization
- Scorecard correlation (accuracy vs reliability degradation)
- Domain-specific reconciliation diagnoses (processing fee, wrong vendor, timing, compound)
- Persistence and retrieval via repository
- API /analyze-failure endpoint
"""

import asyncio
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from reco.api.app import create_app
from reco.db.memory import InMemoryFailureDiagnosisRepository
from reco.diagnostics import (
    FailureAnalyzer,
    FailureCategory,
    FailureCluster,
    FailureSource,
    MutationType,
    RecommendedMutation,
    RootCauseDiagnosis,
    Severity,
)
from reco.diagnostics.models import DiagnosisEvidence
from reco.diagnostics.reconciliation import ReconciliationDiagnosisAdapter


# -----------------------------------------------------------------------------
# Part 1: Model & Taxonomy Tests (1 - 4)
# -----------------------------------------------------------------------------

def test_01_root_cause_diagnosis_validation():
    """Test RootCauseDiagnosis creation and schema validation."""
    diag = RootCauseDiagnosis(
        symptom="Observable syntax crash",
        summary="Syntax error in node prompt",
        root_cause="Node emitted invalid JSON characters",
        failure_category=FailureCategory.OUTPUT_SCHEMA_ERROR,
        severity=Severity.HIGH,
        confidence=0.85,
    )
    assert diag.failure_category == FailureCategory.OUTPUT_SCHEMA_ERROR
    assert diag.severity == Severity.HIGH
    assert diag.confidence == 0.85
    assert diag.diagnosis_id is not None


def test_02_valid_taxonomy_categories():
    """Verify all 12 failure categories exist in FailureCategory enum."""
    expected_categories = [
        "TOOL_ARGUMENT_ERROR",
        "TOOL_RUNTIME_ERROR",
        "ARITHMETIC_MISMATCH",
        "PREMATURE_TERMINATION",
        "HALLUCINATED_MATCH",
        "CONTEXT_OVERFLOW",
        "MISSING_TOOL",
        "WRONG_TOOL_SELECTION",
        "MISSING_VERIFICATION",
        "OUTPUT_SCHEMA_ERROR",
        "MODEL_FAILURE",
        "UNKNOWN_FAILURE",
    ]
    for cat in expected_categories:
        assert cat in FailureCategory.__members__


def test_03_confidence_boundaries():
    """Confidence must be bounded between 0.0 and 1.0."""
    with pytest.raises(ValueError):
        RootCauseDiagnosis(
            symptom="s", summary="sum", root_cause="rc",
            failure_category=FailureCategory.UNKNOWN_FAILURE,
            confidence=1.5,
        )
    with pytest.raises(ValueError):
        RootCauseDiagnosis(
            symptom="s", summary="sum", root_cause="rc",
            failure_category=FailureCategory.UNKNOWN_FAILURE,
            confidence=-0.1,
        )


def test_04_mutation_recommendation_validation():
    """RecommendedMutation requires valid mutation_type, existing target, rationale, and confidence."""
    mutation = RecommendedMutation(
        mutation_type=MutationType.PROMPT_CHANGE,
        target="matcher_node",
        rationale="Update prompt with vendor threshold",
        expected_effect="Prevents false positives",
        confidence=0.90,
    )
    assert mutation.mutation_type == MutationType.PROMPT_CHANGE
    assert mutation.target == "matcher_node"
    assert mutation.confidence == 0.90


# -----------------------------------------------------------------------------
# Part 2: Taxonomy Failure Diagnoses (5 - 16)
# -----------------------------------------------------------------------------

def test_05_tool_argument_error():
    """Diagnose TOOL_ARGUMENT_ERROR when tool validation fails."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "tool_events": [
            {
                "node_id": "diff_calc_node",
                "tool_name": "calculate_reconciliation_difference",
                "arguments": {"amount": "invalid_string"},
                "success": False,
                "error": "ValidationError: 'amount' must be a Decimal or float",
            }
        ],
    }
    arch = {"nodes": [{"node_id": "diff_calc_node"}]}
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch)
    assert diag.failure_category == FailureCategory.TOOL_ARGUMENT_ERROR
    assert diag.failed_node_id == "diff_calc_node"
    assert diag.failure_source == FailureSource.TOOL_INVOCATION
    assert any(m.mutation_type == MutationType.PROMPT_CHANGE for m in diag.recommended_mutations)


def test_06_tool_runtime_error():
    """Diagnose TOOL_RUNTIME_ERROR when tool execution crashes."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "tool_events": [
            {
                "node_id": "api_fetch_node",
                "tool_name": "query_general_ledger",
                "arguments": {"query": "SELECT *"},
                "success": False,
                "error": "ConnectionResetError: Remote ledger database closed connection abruptly",
            }
        ],
    }
    arch = {"nodes": [{"node_id": "api_fetch_node"}]}
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch)
    assert diag.failure_category == FailureCategory.TOOL_RUNTIME_ERROR
    assert diag.failed_node_id == "api_fetch_node"
    assert any(m.mutation_type == MutationType.RETRY_POLICY_CHANGE for m in diag.recommended_mutations)


def test_07_arithmetic_mismatch():
    """Diagnose ARITHMETIC_MISMATCH on mathematical discrepancy."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "output": {"total_discrepancy": "150.00"},
        "tool_events": [],
    }
    arch = {"nodes": [{"node_id": "calc_node"}]}
    bench_ctx = {
        "ground_truth": {
            "total_discrepancy": "25.00",
        }
    }
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch, benchmark_context=bench_ctx)
    assert diag.failure_category == FailureCategory.ARITHMETIC_MISMATCH
    assert "150.00" in diag.symptom
    assert "25.00" in diag.symptom


def test_08_premature_termination():
    """Diagnose PREMATURE_TERMINATION when terminal node was not reached."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "status": "failed",
        "step_history": [{"node_id": "input_parser"}],
        "tool_events": [],
    }
    arch = {
        "entry_node_id": "input_parser",
        "terminal_node_ids": ["final_auditor"],
        "nodes": [{"node_id": "input_parser"}, {"node_id": "final_auditor"}],
    }
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch)
    assert diag.failure_category == FailureCategory.PREMATURE_TERMINATION
    assert diag.failed_node_id == "input_parser"
    assert any(m.mutation_type == MutationType.TOPOLOGY_CHANGE for m in diag.recommended_mutations)


def test_09_hallucinated_match():
    """Diagnose HALLUCINATED_MATCH when agent matches unmatched or wrong vendor item."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "output": {
            "matched_pairs": [{"bank_transaction_id": "TX-999", "ledger_entry_id": "GL-111"}],
            "detected_exceptions": {},
        },
    }
    arch = {"nodes": [{"node_id": "matcher_node", "role": "matcher"}]}
    bench_ctx = {
        "benchmark_name": "reconciliation",
        "case_code": "REC-OPT-08",
        "ground_truth": {
            "primary_exception": "wrong_vendor",
            "unmatched_bank_ids": ["TX-999"],
            "expected_exceptions": {"wrong_vendor": 1},
        },
    }
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch, benchmark_context=bench_ctx)
    assert diag.failure_category == FailureCategory.HALLUCINATED_MATCH
    assert diag.failed_node_id == "matcher_node"
    assert any(m.mutation_type == MutationType.PROMPT_CHANGE for m in diag.recommended_mutations)


def test_10_context_overflow():
    """Diagnose CONTEXT_OVERFLOW when token limit is exceeded."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "errors": [
            {
                "node_id": "aggregator",
                "error_message": "Maximum context length exceeded: 132000 tokens > 128000 allowed.",
                "error_type": "CONTEXT_OVERFLOW",
            }
        ],
    }
    arch = {"nodes": [{"node_id": "aggregator"}]}
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch)
    assert diag.failure_category == FailureCategory.CONTEXT_OVERFLOW
    assert diag.failure_source == FailureSource.STATE_PROPAGATION
    assert any(m.mutation_type == MutationType.CONTEXT_CHANGE for m in diag.recommended_mutations)


def test_11_missing_tool():
    """Diagnose MISSING_TOOL when required capability lacks tool binding."""
    analyzer = FailureAnalyzer()
    exec_rec = {"execution_id": str(uuid4()), "tool_events": []}
    task_spec = {"required_tools": ["calculate_reconciliation_difference"]}
    arch = {"nodes": [{"node_id": "matcher", "tools": ["fuzzy_match_transactions"]}]}
    diag = analyzer.analyze(execution_record=exec_rec, task_specification=task_spec, architecture=arch)
    assert diag.failure_category == FailureCategory.MISSING_TOOL
    assert diag.failure_source == FailureSource.ARCHITECTURE_GENERATION
    assert any(m.mutation_type == MutationType.TOOL_ADD for m in diag.recommended_mutations)


def test_12_wrong_tool_selection():
    """Diagnose WRONG_TOOL_SELECTION when unsuitable tool was invoked."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "errors": [
            {
                "node_id": "calc_node",
                "error_message": "Wrong tool invoked: fuzzy_match_transactions cannot perform numerical difference computation.",
            }
        ],
    }
    arch = {"nodes": [{"node_id": "calc_node"}]}
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch)
    assert diag.failure_category == FailureCategory.WRONG_TOOL_SELECTION
    assert diag.failed_node_id == "calc_node"


def test_13_missing_verification():
    """Diagnose MISSING_VERIFICATION when workflow lacks verification stage."""
    analyzer = FailureAnalyzer()
    exec_rec = {"execution_id": str(uuid4()), "tool_events": []}
    task_spec = {"requires_verification": True}
    arch = {
        "nodes": [
            {"node_id": "loader", "role": "loader"},
            {"node_id": "matcher", "role": "matcher"},
        ],
        "terminal_node_ids": ["matcher"],
    }
    bench_ctx = {"benchmark_name": "generic"}
    diag = analyzer.analyze(
        execution_record=exec_rec,
        task_specification=task_spec,
        architecture=arch,
        benchmark_context=bench_ctx,
    )
    assert diag.failure_category == FailureCategory.MISSING_VERIFICATION
    assert any(m.mutation_type == MutationType.ADD_VERIFIER for m in diag.recommended_mutations)


def test_14_output_schema_error():
    """Diagnose OUTPUT_SCHEMA_ERROR when required output keys are missing."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "output": {"summary": "Done"},
        "tool_events": [],
    }
    task_spec = {
        "output_schema": {
            "type": "object",
            "required": ["matched_pairs", "discrepancies"],
        }
    }
    arch = {"nodes": [{"node_id": "final_node"}], "terminal_node_ids": ["final_node"]}
    diag = analyzer.analyze(execution_record=exec_rec, task_specification=task_spec, architecture=arch)
    assert diag.failure_category == FailureCategory.OUTPUT_SCHEMA_ERROR
    assert diag.failed_node_id == "final_node"


def test_15_model_failure():
    """Diagnose MODEL_FAILURE on gateway inference crash."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "errors": [
            {
                "node_id": "llm_node",
                "error_message": "Model Gateway HTTP 500: Provider internal server error timeout.",
                "error_type": "MODEL_GATEWAY_ERROR",
            }
        ],
    }
    arch = {"nodes": [{"node_id": "llm_node"}]}
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch)
    assert diag.failure_category == FailureCategory.MODEL_FAILURE
    assert diag.severity == Severity.CRITICAL
    assert diag.failure_source == FailureSource.MODEL_INVOCATION


def test_16_unknown_failure():
    """Honest UNKNOWN_FAILURE when evidence is insufficient (No False Certainty)."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "status": "failed",
        "tool_events": [],
        "errors": [],
    }
    arch = {"nodes": [{"node_id": "node_a"}]}
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch)
    assert diag.failure_category == FailureCategory.UNKNOWN_FAILURE
    assert diag.confidence < 0.60
    assert "Insufficient conclusive telemetry signals" in diag.root_cause


# -----------------------------------------------------------------------------
# Part 3: Failure Location (17 - 18)
# -----------------------------------------------------------------------------

def test_17_failed_node_identified():
    """Identify exact failed_node_id from execution trace."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "tool_events": [
            {
                "node_id": "specific_worker_node",
                "tool_name": "some_tool",
                "success": False,
                "error": "Invalid argument format",
            }
        ],
    }
    arch = {"nodes": [{"node_id": "root"}, {"node_id": "specific_worker_node"}]}
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch)
    assert diag.failed_node_id == "specific_worker_node"


def test_18_failure_source_identified():
    """Differentiate tool_invocation from architecture_generation and state_propagation."""
    analyzer = FailureAnalyzer()

    # Tool invocation source
    diag_tool = analyzer.analyze(
        execution_record={"tool_events": [{"tool_name": "t", "success": False, "error": "validation error"}]},
        architecture={"nodes": [{"node_id": "n1"}]},
    )
    assert diag_tool.failure_source == FailureSource.TOOL_INVOCATION

    # Architecture generation source
    diag_arch = analyzer.analyze(
        execution_record={"tool_events": []},
        task_specification={"required_tools": ["missing_tool_x"]},
        architecture={"nodes": [{"node_id": "n1", "tools": []}]},
    )
    assert diag_arch.failure_source == FailureSource.ARCHITECTURE_GENERATION


# -----------------------------------------------------------------------------
# Part 4: Structured Evidence (19 - 21)
# -----------------------------------------------------------------------------

def test_19_tool_event_evidence():
    """Verify tool-event structured evidence schema."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "tool_events": [
            {
                "node_id": "calc",
                "tool_name": "calculate_reconciliation_difference",
                "arguments": {"val": 10},
                "success": False,
                "error": "Validation error on val",
            }
        ]
    }
    diag = analyzer.analyze(execution_record=exec_rec, architecture={"nodes": [{"node_id": "calc"}]})
    assert len(diag.evidence) > 0
    ev = diag.evidence[0]
    assert ev.source == "tool_event"
    assert ev.tool == "calculate_reconciliation_difference"
    assert ev.field == "arguments"


def test_20_ground_truth_evidence():
    """Verify ground truth evidence capture."""
    analyzer = FailureAnalyzer()
    exec_rec = {"output": {"total_discrepancy": "99.00"}, "tool_events": []}
    bench_ctx = {"ground_truth": {"total_discrepancy": "0.00"}}
    diag = analyzer.analyze(execution_record=exec_rec, architecture={"nodes": [{"node_id": "n"}]}, benchmark_context=bench_ctx)
    gt_ev = next(e for e in diag.evidence if e.source == "benchmark_ground_truth")
    assert gt_ev.expected == "0.00"
    assert gt_ev.observed == "99.00"


def test_21_architecture_evidence():
    """Verify architecture evidence capture on missing tools."""
    analyzer = FailureAnalyzer()
    task_spec = {"required_tools": ["t_req"]}
    arch = {"nodes": [{"node_id": "n", "tools": ["t_other"]}]}
    diag = analyzer.analyze(execution_record={}, task_specification=task_spec, architecture=arch)
    arch_ev = next(e for e in diag.evidence if e.source == "architecture")
    assert "t_other" in arch_ev.observed
    assert "t_req" in arch_ev.expected


# -----------------------------------------------------------------------------
# Part 5: Root Cause vs Symptom & Factors (22 - 24)
# -----------------------------------------------------------------------------

def test_22_symptom_vs_root_cause_distinction():
    """Ensure symptom and root cause are cleanly differentiated."""
    analyzer = FailureAnalyzer()
    bench_ctx = {
        "benchmark_name": "reconciliation",
        "ground_truth": {
            "primary_exception": "processing_fee",
            "expected_exceptions": {"processing_fee": 1},
        },
    }
    exec_rec = {
        "output": {"detected_exceptions": {"wrong_amount": 1}},
        "tool_events": [],
    }
    diag = analyzer.analyze(
        execution_record=exec_rec,
        architecture={"nodes": [{"node_id": "classifier"}]},
        benchmark_context=bench_ctx,
    )
    # Symptom explains the observed behavior
    assert "wrong_amount" in diag.symptom
    # Root cause explains the architectural gap
    assert "processing fee" in diag.root_cause.lower() or "discrepancy classification" in diag.root_cause.lower()
    assert diag.symptom != diag.root_cause


def test_23_contributing_factors():
    """Diagnosis captures secondary contributing factors separately."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "tool_events": [
            {
                "node_id": "n1",
                "tool_name": "t1",
                "success": False,
                "error": "Validation error: invalid amount",
            }
        ]
    }
    diag = analyzer.analyze(execution_record=exec_rec, architecture={"nodes": [{"node_id": "n1"}]})
    assert len(diag.contributing_factors) > 0


def test_24_insufficient_evidence_unknown_failure():
    """Honest low confidence when evidence is insufficient."""
    analyzer = FailureAnalyzer()
    diag = analyzer.analyze(execution_record={"status": "unknown"})
    assert diag.failure_category == FailureCategory.UNKNOWN_FAILURE
    assert diag.confidence <= 0.50


# -----------------------------------------------------------------------------
# Part 6: Mutation Recommendations (25 - 29)
# -----------------------------------------------------------------------------

def test_25_prompt_mutation_recommendation():
    """Recommend prompt mutation with real target node."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "tool_events": [
            {
                "node_id": "matcher_node",
                "tool_name": "calc",
                "success": False,
                "error": "validation error",
            }
        ]
    }
    diag = analyzer.analyze(execution_record=exec_rec, architecture={"nodes": [{"node_id": "matcher_node"}]})
    rec = next(m for m in diag.recommended_mutations if m.mutation_type == MutationType.PROMPT_CHANGE)
    assert rec.target == "matcher_node"


def test_26_tool_mutation_recommendation():
    """Recommend TOOL_ADD when capability is missing."""
    analyzer = FailureAnalyzer()
    task_spec = {"required_tools": ["calc_tool"]}
    arch = {"nodes": [{"node_id": "calc_node", "tools": []}]}
    diag = analyzer.analyze(execution_record={}, task_specification=task_spec, architecture=arch)
    rec = next(m for m in diag.recommended_mutations if m.mutation_type == MutationType.TOOL_ADD)
    assert rec.target == "calc_node"


def test_27_topology_mutation_recommendation():
    """Recommend TOPOLOGY_CHANGE when execution terminated prematurely."""
    analyzer = FailureAnalyzer()
    exec_rec = {"status": "failed", "step_history": [{"node_id": "start"}], "tool_events": []}
    arch = {"entry_node_id": "start", "terminal_node_ids": ["finish"], "nodes": [{"node_id": "start"}, {"node_id": "finish"}]}
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch)
    rec = next(m for m in diag.recommended_mutations if m.mutation_type == MutationType.TOPOLOGY_CHANGE)
    assert rec.target == "start"


def test_28_verifier_recommendation():
    """Recommend ADD_VERIFIER when workflow lacks verification."""
    analyzer = FailureAnalyzer()
    task_spec = {"requires_verification": True}
    arch = {"nodes": [{"node_id": "worker"}], "terminal_node_ids": ["worker"]}
    bench_ctx = {"benchmark_name": "general"}
    diag = analyzer.analyze(execution_record={}, task_specification=task_spec, architecture=arch, benchmark_context=bench_ctx)
    rec = next(m for m in diag.recommended_mutations if m.mutation_type == MutationType.ADD_VERIFIER)
    assert rec.target == "worker"


def test_29_model_and_routing_recommendations():
    """Recommend MODEL_CHANGE on provider crash."""
    analyzer = FailureAnalyzer()
    exec_rec = {"errors": [{"node_id": "infer_node", "error_message": "Model Gateway HTTP 500 error"}]}
    arch = {"nodes": [{"node_id": "infer_node"}]}
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch)
    rec = next(m for m in diag.recommended_mutations if m.mutation_type == MutationType.MODEL_CHANGE)
    assert rec.target == "infer_node"


# -----------------------------------------------------------------------------
# Part 7: Failure Clustering & Prioritization (30 - 32)
# -----------------------------------------------------------------------------

def test_30_identical_failure_grouping():
    """Group failures with same category and root cause pattern into single cluster."""
    analyzer = FailureAnalyzer()
    d1 = RootCauseDiagnosis(
        symptom="Mismatch", summary="S1", root_cause="Lacks fee analysis before classification",
        failure_category=FailureCategory.ARITHMETIC_MISMATCH, severity=Severity.MEDIUM, confidence=0.8,
    )
    d2 = RootCauseDiagnosis(
        symptom="Mismatch 2", summary="S2", root_cause="Lacks fee analysis before classification",
        failure_category=FailureCategory.ARITHMETIC_MISMATCH, severity=Severity.MEDIUM, confidence=0.8,
    )
    d3 = RootCauseDiagnosis(
        symptom="Tool error", summary="S3", root_cause="Tool crashed with 500",
        failure_category=FailureCategory.TOOL_RUNTIME_ERROR, severity=Severity.HIGH, confidence=0.9,
    )

    clusters = analyzer.cluster_failures([d1, d2, d3])
    assert len(clusters) == 2
    arithmetic_cluster = next(c for c in clusters if c.category == FailureCategory.ARITHMETIC_MISMATCH)
    assert arithmetic_cluster.count == 2
    assert len(arithmetic_cluster.diagnoses) == 2


def test_31_cluster_frequency():
    """Cluster tracks count and aggregate affected nodes correctly."""
    analyzer = FailureAnalyzer()
    d1 = RootCauseDiagnosis(
        symptom="S", summary="Sum", root_cause="Missing verifier in DAG",
        failure_category=FailureCategory.MISSING_VERIFICATION, severity=Severity.HIGH, confidence=0.8,
        failed_node_id="node_1",
    )
    d2 = RootCauseDiagnosis(
        symptom="S", summary="Sum", root_cause="Missing verifier in DAG",
        failure_category=FailureCategory.MISSING_VERIFICATION, severity=Severity.HIGH, confidence=0.8,
        failed_node_id="node_2",
    )
    clusters = analyzer.cluster_failures([d1, d2])
    assert clusters[0].count == 2
    assert "node_1" in clusters[0].affected_nodes
    assert "node_2" in clusters[0].affected_nodes


def test_32_cluster_prioritization():
    """Sort clusters descending by priority_score = frequency * severity_weight * confidence."""
    analyzer = FailureAnalyzer()
    # High severity, 3 occurrences
    d_high = [
        RootCauseDiagnosis(
            symptom="High", summary="Sum", root_cause="Critical crash",
            failure_category=FailureCategory.TOOL_RUNTIME_ERROR, severity=Severity.CRITICAL, confidence=0.95,
        )
        for _ in range(3)
    ]
    # Low severity, 1 occurrence
    d_low = [
        RootCauseDiagnosis(
            symptom="Low", summary="Sum", root_cause="Minor format variance",
            failure_category=FailureCategory.OUTPUT_SCHEMA_ERROR, severity=Severity.LOW, confidence=0.5,
        )
    ]

    clusters = analyzer.cluster_failures(d_high + d_low)
    assert len(clusters) == 2
    assert clusters[0].category == FailureCategory.TOOL_RUNTIME_ERROR
    assert clusters[0].priority_score > clusters[1].priority_score


# -----------------------------------------------------------------------------
# Part 8: Scorecard Connection (33 - 34)
# -----------------------------------------------------------------------------

def test_33_accuracy_degradation_correlation():
    """Scorecard with accuracy < 0.8 and reliability 1.0 indicates semantic/accuracy failure."""
    analyzer = FailureAnalyzer()
    scorecard = {"accuracy": 0.50, "reliability": 1.0}
    diag = analyzer.analyze(
        execution_record={"status": "completed"},
        architecture={"nodes": [{"node_id": "n1"}]},
        scorecard_metrics=scorecard,
    )
    assert any("accuracy" in f.lower() for f in diag.contributing_factors)
    assert diag.evidence[0].source == "scorecard"


def test_34_reliability_degradation_correlation():
    """Scorecard with reliability < 1.0 indicates execution crash or schema breakdown."""
    analyzer = FailureAnalyzer()
    scorecard = {"accuracy": 0.20, "reliability": 0.40}
    diag = analyzer.analyze(
        execution_record={"status": "failed"},
        architecture={"nodes": [{"node_id": "n1"}]},
        scorecard_metrics=scorecard,
    )
    assert any("reliability" in f.lower() for f in diag.contributing_factors)
    assert diag.severity == Severity.HIGH


# -----------------------------------------------------------------------------
# Part 9: Reconciliation Specific Diagnoses (35 - 38)
# -----------------------------------------------------------------------------

def test_35_reconciliation_processing_fee_diagnosis():
    """Diagnose missing fee analysis when fee is misclassified as wrong_amount."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "output": {"detected_exceptions": {"wrong_amount": 1}},
        "tool_events": [],
    }
    arch = {"nodes": [{"node_id": "matcher_node", "role": "matcher"}]}
    bench_ctx = {
        "benchmark_name": "reconciliation",
        "case_code": "REC-OPT-03",
        "ground_truth": {
            "primary_exception": "processing_fee",
            "expected_exceptions": {"processing_fee": 1},
            "total_discrepancy": "2.50",
        },
    }
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch, benchmark_context=bench_ctx)
    assert diag.failure_category == FailureCategory.ARITHMETIC_MISMATCH
    assert "fee" in diag.root_cause.lower()
    assert any(m.mutation_type == MutationType.TOOL_ADD for m in diag.recommended_mutations)


def test_36_reconciliation_wrong_vendor_diagnosis():
    """Diagnose false match when vendor identity was underweighted."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "output": {
            "matched_pairs": [{"bank_transaction_id": "B-100", "ledger_entry_id": "L-200"}],
            "detected_exceptions": {},
        },
        "tool_events": [],
    }
    arch = {"nodes": [{"node_id": "matcher", "role": "matcher"}]}
    bench_ctx = {
        "benchmark_name": "reconciliation",
        "case_code": "REC-OPT-08",
        "ground_truth": {
            "primary_exception": "wrong_vendor",
            "unmatched_bank_ids": ["B-100"],
            "expected_exceptions": {"wrong_vendor": 1},
        },
    }
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch, benchmark_context=bench_ctx)
    assert diag.failure_category == FailureCategory.HALLUCINATED_MATCH
    assert "vendor" in diag.root_cause.lower()
    assert any(m.mutation_type == MutationType.PROMPT_CHANGE for m in diag.recommended_mutations)


def test_37_reconciliation_timing_difference_diagnosis():
    """Diagnose timing lag when date boundary caused unmatched classification."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "output": {"matched_pairs": [], "detected_exceptions": {}},
        "tool_events": [],
    }
    arch = {"nodes": [{"node_id": "matcher", "role": "matcher"}]}
    bench_ctx = {
        "benchmark_name": "reconciliation",
        "case_code": "REC-OPT-05",
        "ground_truth": {
            "primary_exception": "timing_difference",
            "expected_exceptions": {"timing_difference": 1},
        },
    }
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch, benchmark_context=bench_ctx)
    assert diag.failure_category == FailureCategory.ARITHMETIC_MISMATCH
    assert "temporal" in diag.root_cause.lower() or "window" in diag.root_cause.lower()


def test_38_reconciliation_compound_exception_diagnosis():
    """Diagnose compound exception when pipeline exited on first discrepancy."""
    analyzer = FailureAnalyzer()
    exec_rec = {
        "execution_id": str(uuid4()),
        "output": {"detected_exceptions": {"timing_difference": 1}},
        "tool_events": [],
    }
    arch = {"nodes": [{"node_id": "classifier", "role": "classifier"}]}
    bench_ctx = {
        "benchmark_name": "reconciliation",
        "case_code": "REC-OPT-12",
        "ground_truth": {
            "primary_exception": "compound_exception",
            "expected_exceptions": {"compound_exception": 1},
        },
    }
    diag = analyzer.analyze(execution_record=exec_rec, architecture=arch, benchmark_context=bench_ctx)
    assert diag.failure_category == FailureCategory.MISSING_VERIFICATION
    assert "compound" in diag.root_cause.lower()


# -----------------------------------------------------------------------------
# Part 10: Persistence & API (39 - 41)
# -----------------------------------------------------------------------------

def test_39_diagnosis_persistence():
    """Persist RootCauseDiagnosis via FailureDiagnosisRepository abstraction."""
    repo = InMemoryFailureDiagnosisRepository()
    analyzer = FailureAnalyzer()
    case_exec_id = uuid4()
    diag = RootCauseDiagnosis(
        case_execution_id=case_exec_id,
        symptom="Tool crashed",
        summary="Validation crash",
        root_cause="Missing amount argument",
        failure_category=FailureCategory.TOOL_ARGUMENT_ERROR,
        severity=Severity.HIGH,
        confidence=0.95,
    )
    record = asyncio.run(analyzer.save_diagnosis(diag, repo))
    assert record.id == diag.diagnosis_id
    assert record.case_execution_id == case_exec_id
    assert record.category == "TOOL_ARGUMENT_ERROR"


def test_40_diagnosis_retrieval():
    """Retrieve saved diagnosis and verify round-trip fidelity."""
    repo = InMemoryFailureDiagnosisRepository()
    analyzer = FailureAnalyzer()
    case_exec_id = uuid4()
    diag = RootCauseDiagnosis(
        case_execution_id=case_exec_id,
        symptom="Syntax error",
        summary="Bad JSON",
        root_cause="Terminal node emitted trailing comma",
        failure_category=FailureCategory.OUTPUT_SCHEMA_ERROR,
        severity=Severity.MEDIUM,
        confidence=0.88,
        recommended_mutations=[
            RecommendedMutation(
                mutation_type=MutationType.PROMPT_CHANGE,
                target="terminal_node",
                rationale="Strip trailing commas",
                expected_effect="Valid JSON",
                confidence=0.88,
            )
        ],
    )
    asyncio.run(analyzer.save_diagnosis(diag, repo))

    # Fetch by diagnosis ID
    loaded = asyncio.run(analyzer.get_diagnosis(diag.diagnosis_id, repo))
    assert loaded is not None
    assert loaded.diagnosis_id == diag.diagnosis_id
    assert loaded.failure_category == FailureCategory.OUTPUT_SCHEMA_ERROR
    assert loaded.root_cause == diag.root_cause
    assert len(loaded.recommended_mutations) == 1
    assert loaded.recommended_mutations[0].target == "terminal_node"

    # Fetch by case_execution_id
    loaded_case = asyncio.run(analyzer.get_for_case_execution(case_exec_id, repo))
    assert loaded_case is not None
    assert loaded_case.diagnosis_id == diag.diagnosis_id


def test_41_analyze_failure_api_endpoint():
    """Test POST /analyze-failure endpoint with structured execution payload."""
    app = create_app()
    client = TestClient(app)

    payload = {
        "execution_record": {
            "tool_events": [
                {
                    "node_id": "worker",
                    "tool_name": "calc",
                    "success": False,
                    "error": "ValidationError: missing required argument",
                }
            ]
        },
        "architecture": {
            "nodes": [{"node_id": "worker"}]
        }
    }

    response = client.post("/analyze-failure", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["failure_category"] == "TOOL_ARGUMENT_ERROR"
    assert data["failed_node_id"] == "worker"
    assert data["severity"] == "high"
    assert len(data["recommended_mutations"]) > 0
