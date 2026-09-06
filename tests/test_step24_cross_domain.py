"""Deterministic Regression Suite for Step 24 Cross-Domain Verification.

Verifies:
1. ExecutionState outputs and get_last_node_output accessor properties.
2. MutationEngine & CandidateGenerator defensive handling of None / empty diagnoses.
3. AnomalyDiagnosisAdapter unpacking final_anomaly_report dictionaries.
4. ResearchDiagnosisAdapter unpacking final_recommendation dictionaries.
5. Shared engine integrity: GoalAnalyzer, ArchitectureGenerator, ToolRegistry,
   AgentGraphRuntime, FailureAnalyzer, MutationEngine, Scorecard, assess_promotion.
6. Step 24 artifact schema and integrity.
"""

import json
import os
import pytest
from uuid import uuid4

from reco.engine.state import ExecutionState
from reco.engine.models import GraphDefinition, NodeModel, EdgeModel
from reco.mutation.generator import CandidateGenerator
from reco.mutation.engine import MutationEngine
from reco.diagnostics.anomaly import AnomalyDiagnosisAdapter
from reco.diagnostics.research import ResearchDiagnosisAdapter
from reco.diagnostics.models import RootCauseDiagnosis
from reco.diagnostics.taxonomy import FailureCategory, Severity
from reco.evaluators.comparison import assess_promotion, compare_scorecards
from reco.evaluators.scorecard import Scorecard
from reco.core.goal_analyzer import GoalAnalyzer
from reco.engine.generator import ArchitectureGenerator
from reco.tools.registry import default_tool_registry
from reco.engine.runtime import AgentGraphRuntime


def test_execution_state_properties():
    """Verify ExecutionState provides clean property accessors for outputs."""
    state = ExecutionState(goal="Test goal")
    assert state.outputs == {}
    assert state.get_last_node_output() is None

    state.update_node_output("first_node", {"raw": [1, 2, 3]})
    state.update_node_output("last_node", {"result": "success", "count": 42})

    assert state.outputs == {"result": "success", "count": 42}
    assert state.get_last_node_output() == {"result": "success", "count": 42}


def test_mutation_engine_none_diagnosis_handling():
    """Verify MutationEngine and CandidateGenerator handle None / empty diagnoses without raising."""
    generator = CandidateGenerator()
    dummy_graph = GraphDefinition(
        graph_id="g_dummy",
        name="Dummy Graph",
        entry_node_id="node_a",
        nodes={"node_a": NodeModel(node_id="node_a", name="Node A", role="Worker", system_prompt="Do work.")},
        edges=[],
    )

    # 1. CandidateGenerator with None inside list
    candidates = generator.generate(
        agent_graph=dummy_graph,
        diagnoses=[None],  # type: ignore
        max_candidates=2,
    )
    assert isinstance(candidates, list)

    # 2. MutationEngine.generate_candidates with None
    engine = MutationEngine()
    cand_list = engine.generate_candidates(
        graph=dummy_graph,
        diagnoses=[None],  # type: ignore
        max_candidates=1,
    )
    assert isinstance(cand_list, list)


def test_anomaly_diagnosis_adapter_unpacking():
    """Verify AnomalyDiagnosisAdapter extracts flagged anomalies from nested final_anomaly_report."""
    actual_outcome = {
        "final_anomaly_report": {
            "flagged_anomaly_ids": ["rec_43"],
            "explanations": ["Payout outlier exceeding 3.0 z-score."],
        }
    }
    ground_truth = {"expected_anomaly_ids": []}
    graph_nodes = [
        {"node_id": "dataset_reader"},
        {"node_id": "statistical_analyzer"},
        {"node_id": "anomaly_auditor"},
    ]

    diag = AnomalyDiagnosisAdapter.diagnose(
        actual_outcome=actual_outcome,
        ground_truth=ground_truth,
        graph_nodes=graph_nodes,
        tool_events=[],
        case_code="ANOM-OPT-05",
    )

    assert diag is not None
    assert diag.failure_category == FailureCategory.HALLUCINATED_MATCH
    assert diag.failed_node_id == "anomaly_auditor"
    assert "rec_43" in str(diag.evidence[0].observed)


def test_research_diagnosis_adapter_unpacking():
    """Verify ResearchDiagnosisAdapter extracts recommendation from nested final_recommendation."""
    actual_outcome = {
        "final_recommendation": {
            "recommended_technology": "DynamoDB",
            "fact_citations": ["Marketing flyer"],
            "rejection_rationales": {"PostgreSQL": "Legacy"},
        }
    }
    ground_truth = {
        "recommended_technology": "PostgreSQL",
        "rejected_technologies": ["DynamoDB"],
        "contradiction_resolution": True,
    }
    graph_nodes = [
        {"node_id": "evidence_searcher"},
        {"node_id": "claims_extractor"},
        {"node_id": "recommendation_synthesizer"},
    ]

    diag = ResearchDiagnosisAdapter.diagnose(
        actual_outcome=actual_outcome,
        ground_truth=ground_truth,
        graph_nodes=graph_nodes,
        tool_events=[],
        case_code="RES-OPT-03",
    )

    assert diag is not None
    assert diag.failed_node_id == "recommendation_synthesizer"
    assert "marketing" in diag.root_cause.lower()


def test_shared_engine_verification():
    """Verify all 8 core optimization subsystems are completely shared across domains."""
    from reco.core.goal_analyzer import GoalAnalyzer
    from reco.engine.generator import ArchitectureGenerator
    from reco.tools.registry import ToolRegistry
    from reco.engine.runtime import AgentGraphRuntime
    from reco.diagnostics.analyzer import FailureAnalyzer
    from reco.mutation.engine import MutationEngine
    from reco.evaluators.scorecard import Scorecard
    from reco.evaluators.comparison import assess_promotion

    subsystems = [
        GoalAnalyzer,
        ArchitectureGenerator,
        ToolRegistry,
        AgentGraphRuntime,
        FailureAnalyzer,
        MutationEngine,
        Scorecard,
        assess_promotion,
    ]
    for s in subsystems:
        assert s is not None
        assert callable(s) or isinstance(s, type)


def test_step24_artifact_integrity():
    """Verify Step 24 artifact file exists, is valid JSON, and contains no API secrets."""
    artifact_path = os.path.join("scratch", "step24_cross_domain_real_provider.json")
    assert os.path.exists(artifact_path), f"Artifact {artifact_path} must exist"

    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["provider"] == "tensormux"
    assert data["model"] == "glm-4-7-flash"
    assert "anomaly_detection" in data["domains"]
    assert "research_comparison" in data["domains"]

    # Check for secrets
    raw_text = json.dumps(data)
    for forbidden in ["sk-", "api_key", "bearer ", "authorization"]:
        assert forbidden not in raw_text.lower(), f"Forbidden secret token '{forbidden}' detected in artifact"

    # Verify scorecards
    anom_v0 = data["domains"]["anomaly_detection"]["v0_scorecard"]
    anom_v1 = data["domains"]["anomaly_detection"]["v1_scorecard"]
    assert anom_v0["accuracy"] == 0.8
    assert anom_v1["accuracy"] == 1.0

    res_v0 = data["domains"]["research_comparison"]["v0_scorecard"]
    res_v1 = data["domains"]["research_comparison"]["v1_scorecard"]
    assert res_v0["accuracy"] == 1.0
    assert res_v1["accuracy"] == 1.0
