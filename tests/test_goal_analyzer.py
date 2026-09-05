"""Deterministic tests for Goal Decomposition and Task Specification."""

import pytest
from reco.core.goal_analyzer import GoalAnalyzer
from reco.core.task_spec import TaskSpecification
from reco.tools.registry import ToolRegistry


def test_tabular_data_goal_decomposition():
    """Test standard tabular data analysis goal decomposition."""
    analyzer = GoalAnalyzer()
    goal = "Analyze tabular data, compute distributions, and detect all anomalous records"
    spec = analyzer.analyze(goal)

    assert isinstance(spec, TaskSpecification)
    assert spec.goal == goal
    assert spec.domain == "data_analysis"
    assert "tabular_parsing" in spec.required_capabilities
    assert "distribution_analysis" in spec.required_capabilities
    assert "anomaly_detection" in spec.required_capabilities

    # Check schemas
    assert "dataset" in spec.input_schema["properties"]
    assert "dataset" in spec.input_schema["required"]
    assert "distributions" in spec.output_schema["required"]
    assert "anomalies" in spec.output_schema["required"]

    # Check default budgets
    assert spec.latency_budget_ms == 5000.0
    assert spec.cost_budget_usd == 0.05
    assert "accuracy" in spec.evaluation_criteria


def test_multi_domain_support():
    """Verify goal decomposition across distinct domain scenarios."""
    analyzer = GoalAnalyzer()

    # Domain: Code Generation / Review
    code_goal = "Analyze python codebase, validate syntax, and refactor slow functions"
    code_spec = analyzer.analyze(code_goal)
    assert code_spec.domain == "code_generation"
    assert "code_analysis" in code_spec.required_capabilities
    assert "syntax_validation" in code_spec.required_capabilities
    assert "code_refactoring" in code_spec.required_capabilities
    assert "code" in code_spec.input_schema["properties"]

    # Domain: Web Research
    web_goal = "Search web documents, retrieve articles, and summarize key insights"
    web_spec = analyzer.analyze(web_goal)
    assert web_spec.domain == "web_research"
    assert "document_retrieval" in web_spec.required_capabilities
    assert "summarization" in web_spec.required_capabilities

    # Domain: Financial Audit
    finance_goal = "Audit financial transactions, reconcile balance ledgers, and detect fraud"
    finance_spec = analyzer.analyze(finance_goal)
    assert finance_spec.domain == "financial_audit"
    assert "transaction_parsing" in finance_spec.required_capabilities
    assert "reconciliation" in finance_spec.required_capabilities
    assert "fraud_detection" in finance_spec.required_capabilities


def test_custom_budget_constraints():
    """Test overriding latency, cost, and evaluation criteria."""
    analyzer = GoalAnalyzer(default_latency_ms=2000.0, default_cost_usd=0.01)
    goal = "Tabular data statistics and outlier extraction"
    spec = analyzer.analyze(
        goal,
        constraints={
            "latency_budget_ms": 1500.0,
            "cost_budget_usd": 0.02,
            "evaluation_criteria": ["accuracy", "speed"]
        }
    )

    assert spec.latency_budget_ms == 1500.0
    assert spec.cost_budget_usd == 0.02
    assert spec.evaluation_criteria == ["accuracy", "speed"]


def test_goal_with_available_tools():
    """Test capability alignment when available tool registry is supplied."""
    registry = ToolRegistry.create_default()
    analyzer = GoalAnalyzer()
    goal = "Analyze tabular distributions and anomalies"
    spec = analyzer.analyze(goal, available_tools=registry.list_tools())

    assert spec.domain == "data_analysis"
    assert spec.has_capability("distribution_analysis")
    assert spec.has_capability("anomaly_detection")
    assert spec.metadata["tool_count"] == 4
