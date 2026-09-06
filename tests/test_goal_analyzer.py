"""Comprehensive unit tests for the Goal & Task Specification Parser (Milestone 5)."""

import json
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from reco.api.app import app
from reco.core.goal_analyzer import GoalAnalyzer, normalize_goal
from reco.core.task_spec import (
    Capability,
    EvaluatorSpecification,
    Subtask,
    TaskSpecification,
    ToolRecommendation,
)
from reco.llm.mock import MockModelGateway
from reco.tools.reconciliation import register_reconciliation_tools
from reco.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def recon_registry() -> ToolRegistry:
    """Registry loaded with the standard reconciliation toolpack."""
    reg = ToolRegistry()
    register_reconciliation_tools(reg)
    return reg


@pytest.fixture
def sample_catalog():
    """Standardized tool catalog schema list."""
    reg = ToolRegistry()
    register_reconciliation_tools(reg)
    return reg.list_schemas()


@pytest.fixture
def api_client():
    """TestClient for FastAPI app."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. MODEL TESTS
# ---------------------------------------------------------------------------

def test_model_valid_task_specification():
    """1. Test creating a fully populated valid TaskSpecification."""
    subtask = Subtask(
        id="st_1",
        description="Extract statements",
        objective="Parse CSV files",
        required_capabilities=[Capability.EXTRACTION],
        preferred_tools=["parse_bank_statement"],
        expected_input={"raw_csv": "string"},
        expected_output={"records": "list"},
        verification_needed=False,
        dependencies=[],
    )
    spec = TaskSpecification(
        original_goal="Reconcile bank statements against GL",
        normalized_goal="Reconcile bank statements against GL",
        domain="finance",
        objective="Reconcile transactions",
        subtasks=[subtask],
        required_capabilities=[Capability.EXTRACTION, Capability.CALCULATION],
        available_tool_ids=["parse_bank_statement"],
        suggested_tool_bindings=[
            ToolRecommendation(
                tool_name="parse_bank_statement",
                relevance_score=0.95,
                reason="Direct match for bank statements",
                required=True,
                confidence=0.90,
            )
        ],
        inputs={"file": "path"},
        expected_outputs={"summary": "dict"},
        constraints=["Preserve currency decimals"],
        verification_requirements=["Arithmetic check"],
        risk_level="low",
        side_effect_requirements=False,
        ambiguity_flags=[],
        confidence=0.95,
    )
    assert spec.original_goal == "Reconcile bank statements against GL"
    assert len(spec.subtasks) == 1
    assert spec.subtasks[0].id == "st_1"
    assert spec.confidence == 0.95
    spec.validate_tool_integrity()


def test_model_invalid_task_specification():
    """2. Test that missing required fields or invalid types fail validation."""
    with pytest.raises(ValidationError):
        # Missing objective and original_goal
        TaskSpecification(normalized_goal="Test")

    with pytest.raises(ValidationError):
        # Invalid confidence (> 1.0)
        TaskSpecification(
            original_goal="Do work",
            normalized_goal="Do work",
            objective="Deliver results",
            confidence=1.5,
        )


def test_model_valid_subtask():
    """3. Test valid Subtask instantiation and defaults."""
    st = Subtask(
        id="sub_0",
        description="Filter records",
        objective="Eliminate inactive rows",
        required_capabilities=[Capability.TRANSFORMATION, Capability.COMPARISON],
    )
    assert st.id == "sub_0"
    assert st.dependencies == []
    assert st.verification_needed is False
    assert st.preferred_tools == []


def test_model_dependency_references():
    """4. Test that subtask dependencies store string identifiers."""
    st1 = Subtask(id="step_1", description="Step 1", objective="Obj 1")
    st2 = Subtask(id="step_2", description="Step 2", objective="Obj 2", dependencies=["step_1"])
    assert st2.dependencies == ["step_1"]


# ---------------------------------------------------------------------------
# 2. NORMALIZATION TESTS
# ---------------------------------------------------------------------------

def test_normalization_whitespace():
    """5. Test whitespace and newline normalization."""
    raw = "  Reconcile   these    transactions \t\t against  \n\n\n  ledger.   "
    cleaned = normalize_goal(raw)
    assert cleaned == "Reconcile these transactions against \n\n ledger."


def test_normalization_empty_goal_rejection():
    """6. Test that empty or whitespace-only goals are rejected."""
    with pytest.raises(ValueError, match="empty or whitespace only"):
        normalize_goal("")

    with pytest.raises(ValueError, match="empty or whitespace only"):
        normalize_goal("   \t  \n  ")


def test_normalization_original_goal_preservation():
    """7. Test that TaskSpecification preserves verbatim raw goal alongside normalized goal."""
    analyzer = GoalAnalyzer()
    raw = "  Reconcile   bank  statement   "
    import asyncio
    spec = asyncio.run(analyzer.analyze(goal=raw))
    assert spec.original_goal == raw
    assert spec.normalized_goal == "Reconcile bank statement"


# ---------------------------------------------------------------------------
# 3. TOOL CATALOG INTEGRITY TESTS
# ---------------------------------------------------------------------------

def test_tool_catalog_available_tools_preserved(sample_catalog):
    """8. Test that available tool IDs are faithfully recorded in TaskSpecification."""
    analyzer = GoalAnalyzer()
    import asyncio
    spec = asyncio.run(analyzer.analyze("Reconcile statements", available_tools=sample_catalog))
    expected_ids = {t["name"] for t in sample_catalog}
    assert set(spec.available_tool_ids) == expected_ids


def test_tool_catalog_suggested_tools_must_exist(sample_catalog):
    """9. Test that analyzer never fabricates tools and purges unrecognized tools."""
    analyzer = GoalAnalyzer()
    import asyncio
    spec = asyncio.run(analyzer.analyze("Reconcile ledger", available_tools=sample_catalog))
    spec.validate_tool_integrity()

    # If an unrecognized tool is forcibly injected, validate_tool_integrity detects it
    spec.suggested_tool_bindings.append(
        ToolRecommendation(
            tool_name="fabricated_magic_tool",
            relevance_score=0.99,
            reason="Imaginary tool",
        )
    )
    with pytest.raises(ValueError, match="Fabricated tool detected"):
        spec.validate_tool_integrity()


def test_tool_catalog_recommendation_structure(sample_catalog):
    """10. Test ToolRecommendation field requirements and bounds."""
    rec = ToolRecommendation(
        tool_name="calc_difference",
        relevance_score=0.88,
        reason="Calculates numerical discrepancies",
        required=True,
        confidence=0.92,
    )
    assert rec.tool_name == "calc_difference"
    assert 0.0 <= rec.relevance_score <= 1.0
    assert rec.required is True
    assert 0.0 <= rec.confidence <= 1.0


# ---------------------------------------------------------------------------
# 4. LLM ANALYSIS BOUNDARY & REPAIR TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_llm_analysis_mock_gateway_decomposition(sample_catalog):
    """11. Test deterministic MockModelGateway decomposition."""
    canned_json = json.dumps({
        "domain": "finance",
        "objective": "Perform multi-source bank statement reconciliation",
        "subtasks": [
            {
                "id": "st_1",
                "description": "Parse inputs",
                "objective": "Read statements",
                "required_capabilities": ["extraction"],
                "preferred_tools": ["parse_bank_statement"],
                "dependencies": [],
            }
        ],
        "required_capabilities": ["extraction", "calculation"],
        "suggested_tool_bindings": [
            {
                "tool_name": "parse_bank_statement",
                "relevance_score": 0.95,
                "reason": "Direct CSV parser",
                "required": True,
            }
        ],
        "inputs": {"files": "list"},
        "expected_outputs": {"matches": "list"},
        "constraints": ["Zero tolerance"],
        "verification_requirements": ["Arithmetic proof"],
        "risk_level": "low",
        "side_effect_requirements": False,
        "ambiguity_flags": [],
        "requires_clarification": False,
        "confidence": 0.92,
    })
    mock_gateway = MockModelGateway(default_content=canned_json)
    analyzer = GoalAnalyzer(model_gateway=mock_gateway)
    spec = await analyzer.analyze(
        goal="Reconcile bank accounts against GL",
        available_tools=sample_catalog,
    )
    assert spec.domain == "finance"
    assert spec.objective == "Perform multi-source bank statement reconciliation"
    assert len(spec.subtasks) == 1
    assert spec.confidence == 0.92
    assert "parse_bank_statement" in [b.tool_name for b in spec.suggested_tool_bindings]


@pytest.mark.anyio
async def test_llm_analysis_structured_output_validation(sample_catalog):
    """12. Test Pydantic validation of model output structure."""
    valid_json = json.dumps({
        "domain": "data",
        "objective": "Analyze CSV statistics",
        "subtasks": [],
        "required_capabilities": ["transformation"],
        "confidence": 0.85,
    })
    mock_gateway = MockModelGateway(default_content=f"```json\n{valid_json}\n```")
    analyzer = GoalAnalyzer(model_gateway=mock_gateway)
    spec = await analyzer.analyze("Analyze CSV", available_tools=sample_catalog)
    assert spec.domain == "data"
    assert spec.confidence == 0.85


@pytest.mark.anyio
async def test_llm_analysis_malformed_model_output_handling(sample_catalog):
    """13. Test malformed model output triggers safe fallback or error."""
    # When fallback_on_error=False, an unfixable malformed output raises clear RuntimeError
    broken_content = "This is not JSON at all: { broken"
    mock_gateway = MockModelGateway(default_content=broken_content)
    strict_analyzer = GoalAnalyzer(model_gateway=mock_gateway, fallback_on_error=False)

    with pytest.raises(RuntimeError, match="LLM decomposition failed"):
        await strict_analyzer.analyze("Analyze data", available_tools=sample_catalog)

    # When fallback_on_error=True (default), it falls back to deterministic analysis and records error
    safe_analyzer = GoalAnalyzer(model_gateway=mock_gateway, fallback_on_error=True)
    spec = await safe_analyzer.analyze("Analyze data", available_tools=sample_catalog)
    assert spec is not None
    assert "llm_error" in spec.metadata
    assert any("llm_parsing_error" in flag for flag in spec.ambiguity_flags)


@pytest.mark.anyio
async def test_llm_analysis_bounded_repair_behavior(sample_catalog):
    """14. Test bounded repair: initial broken JSON is fixed on single retry."""
    repair_json = json.dumps({
        "domain": "research",
        "objective": "Survey observability platforms",
        "subtasks": [],
        "required_capabilities": ["retrieval", "comparison"],
        "confidence": 0.88,
    })
    # First response broken, second response (matching 'Fix the following text') is valid JSON
    mock_gateway = MockModelGateway(
        default_content="Malformed { unclosed json",
        canned_responses={
            "Fix the following text": repair_json,
        },
    )
    analyzer = GoalAnalyzer(model_gateway=mock_gateway)
    spec = await analyzer.analyze("Compare platforms", available_tools=sample_catalog)
    assert spec.domain == "research"
    assert spec.confidence == 0.88
    assert spec.metadata.get("repaired") is True


# ---------------------------------------------------------------------------
# 5. MULTI-DOMAIN SEMANTIC DECOMPOSITION TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_semantic_generic_research_goal():
    """15. Test research domain: comparison, literature, citation."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Compare the top three open-source observability platforms for Python.")
    assert spec.domain == "research"
    assert Capability.COMPARISON in spec.required_capabilities
    assert Capability.REASONING in spec.required_capabilities
    assert "comparative_analysis" in spec.expected_outputs


@pytest.mark.anyio
async def test_semantic_generic_data_analysis_goal():
    """16. Test data domain: anomaly detection, CSV, outliers."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Find anomalies in this CSV and explain the likely causes.")
    assert spec.domain == "data"
    assert Capability.ANOMALY_DETECTION in spec.required_capabilities
    assert "anomalies_and_causes" in spec.expected_outputs


@pytest.mark.anyio
async def test_semantic_finance_reconciliation_goal(sample_catalog):
    """17. Test finance domain: reconciliation, bank transactions, ledger."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze(
        "Reconcile these bank transactions against the general ledger.",
        available_tools=sample_catalog,
    )
    assert spec.domain == "finance"
    assert Capability.CALCULATION in spec.required_capabilities
    assert Capability.COMPARISON in spec.required_capabilities
    assert "reconciliation_summary" in spec.expected_outputs


@pytest.mark.anyio
async def test_semantic_coding_debugging_goal():
    """18. Test coding domain: test suite diagnosis, bug root cause."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Diagnose this failing test suite and propose the most likely root cause.")
    assert spec.domain == "coding"
    assert Capability.REASONING in spec.required_capabilities
    assert "diagnosis_and_fix" in spec.expected_outputs


# ---------------------------------------------------------------------------
# 6. CONSTRAINTS & REQUIREMENTS TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_constraints_output_format_extraction():
    """19. Test output format constraint extraction (JSON)."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Reconcile records. Output must strictly be JSON.")
    assert any("JSON" in c for c in spec.constraints)


@pytest.mark.anyio
async def test_constraints_evidence_requirement_extraction():
    """20. Test evidence requirement extraction."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Compare cloud vendors and cite evidence for each claim.")
    assert any("evidence" in c.lower() for c in spec.constraints)


@pytest.mark.anyio
async def test_constraints_budget_preservation():
    """21. Test execution budget constraint preservation."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Analyze data anomalies with maximum execution budget under $5.")
    assert any("budget" in c.lower() for c in spec.constraints)


# ---------------------------------------------------------------------------
# 7. VERIFICATION REQUIREMENTS TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_verification_requirement_extraction():
    """22. Test verification requirements extraction for arithmetic and duplicates."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Calculate difference between ledger balances and check for duplicate transactions.")
    req_text = " ".join(spec.verification_requirements).lower()
    assert "arithmetic" in req_text
    assert "duplicate" in req_text


# ---------------------------------------------------------------------------
# 8. RISK & SIDE-EFFECT TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_risk_read_only_task(sample_catalog):
    """23. Test read-only task with safe tools has low risk and no side effects."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Query and compare ledger entries in read-only mode.", available_tools=sample_catalog)
    assert spec.risk_level == "low"
    assert spec.side_effect_requirements is False


@pytest.mark.anyio
async def test_risk_side_effect_task():
    """24. Test task with mutation actions is marked with side_effect_requirements."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Delete old records and update general ledger entries.")
    assert spec.side_effect_requirements is True
    assert spec.risk_level in ["medium", "high"]


@pytest.mark.anyio
async def test_risk_high_risk_tool_detection():
    """25. Test that high-risk tools in catalog elevate task risk."""
    high_risk_tools = [
        {
            "name": "drop_production_table",
            "description": "Permanently drops database tables",
            "side_effect": True,
            "risk_level": "high",
        }
    ]
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Clean up database tables", available_tools=high_risk_tools)
    assert spec.risk_level == "high"
    assert spec.side_effect_requirements is True


# ---------------------------------------------------------------------------
# 9. AMBIGUITY DETECTION TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_ambiguity_missing_input():
    """26. Test missing input detection."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Reconcile and find differences with tolerance 0.01 in json format.")
    assert any("missing_input" in a for a in spec.ambiguity_flags)


@pytest.mark.anyio
async def test_ambiguity_missing_success_criteria():
    """27. Test missing success criteria / threshold detection."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Analyze CSV data records for outliers in json.")
    assert any("unspecified_success_criteria" in a for a in spec.ambiguity_flags)


@pytest.mark.anyio
async def test_ambiguity_ambiguous_output():
    """28. Test ambiguous output format detection."""
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Reconcile transactions file with zero tolerance criteria.")
    assert any("ambiguous_output_format" in a for a in spec.ambiguity_flags)


# ---------------------------------------------------------------------------
# 10. DETERMINISTIC FALLBACK TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_fallback_no_llm_deterministic_fallback(sample_catalog):
    """29. Test that pure deterministic mode works offline without any LLM."""
    analyzer = GoalAnalyzer(model_gateway=None)
    spec = await analyzer.analyze("Reconcile bank statements against ledger", available_tools=sample_catalog)
    assert spec is not None
    assert spec.metadata.get("parser_mode") == "deterministic_rule_based"
    assert len(spec.subtasks) >= 2
    assert len(spec.suggested_tool_bindings) > 0
    spec.validate_tool_integrity()


# ---------------------------------------------------------------------------
# 11. EVALUATOR SPECIFICATION & API TESTS
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_evaluator_specification_preservation():
    """Test evaluator specification criteria are preserved in TaskSpecification."""
    eval_spec = {
        "required_output_properties": ["matched_count", "unmatched_count", "net_difference"],
        "correctness_criteria": ["Net difference matches sum of exceptions"],
        "threshold_conditions": {"accuracy": 0.99},
    }
    analyzer = GoalAnalyzer()
    spec = await analyzer.analyze("Reconcile statements", evaluator_spec=eval_spec)
    assert spec.evaluator_requirements is not None
    assert "matched_count" in spec.evaluator_requirements.required_output_properties
    assert spec.evaluator_requirements.threshold_conditions["accuracy"] == 0.99


def test_api_analyze_goal_endpoint(api_client):
    """Test POST /analyze-goal internal test endpoint."""
    # Valid goal
    resp = api_client.post(
        "/analyze-goal",
        json={"goal": "Reconcile bank statements against general ledger in json format"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["domain"] == "finance"
    assert "task_id" in data
    assert "subtasks" in data
    assert len(data["subtasks"]) > 0

    # Empty goal rejects with 400
    bad_resp = api_client.post("/analyze-goal", json={"goal": "   "})
    assert bad_resp.status_code == 400
    assert "empty or whitespace" in bad_resp.json()["detail"]
