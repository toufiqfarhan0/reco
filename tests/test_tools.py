"""Deterministic tests for Tool Registry, Analytical Tools, and Sandboxed Executor."""

import pytest
from reco.tools.executor import ToolExecutor, ToolResult
from reco.tools.registry import (
    ToolDefinition,
    ToolRegistry,
    compute_distributions_handler,
    detect_anomalies_handler,
    json_validator_handler,
    tabular_summary_handler,
)


@pytest.fixture
def sample_dataset():
    """Synthetic dataset with numeric metrics and one injected anomaly."""
    return [
        {"id": "rec_1", "category": "A", "revenue": 100.0, "cost": 60.0},
        {"id": "rec_2", "category": "A", "revenue": 105.0, "cost": 62.0},
        {"id": "rec_3", "category": "B", "revenue": 98.0, "cost": 59.0},
        {"id": "rec_4", "category": "B", "revenue": 102.0, "cost": 61.0},
        {"id": "rec_5", "category": "A", "revenue": 101.0, "cost": 60.0},
        {"id": "rec_6", "category": "B", "revenue": 99.0, "cost": 58.0},
        {"id": "rec_7", "category": "A", "revenue": 104.0, "cost": 63.0},
        {"id": "rec_8", "category": "B", "revenue": 100.0, "cost": 60.0},
        # Injected anomaly: revenue is 10x higher
        {"id": "rec_9", "category": "A", "revenue": 1200.0, "cost": 61.0},
    ]


def test_tool_registry_management():
    """Verify tool registration, lookup, and duplicate prevention."""
    registry = ToolRegistry()

    dummy_tool = ToolDefinition(
        name="custom_math",
        description="Performs arithmetic",
        parameters={"type": "object", "properties": {"x": {"type": "number"}}, "required": ["x"]},
        capabilities=["math_eval"],
        handler=lambda x: x * 2
    )

    registry.register(dummy_tool)
    assert registry.has("custom_math") is True
    assert registry.get("custom_math").name == "custom_math"

    # Duplicate registration must raise ValueError
    with pytest.raises(ValueError, match="already registered"):
        registry.register(dummy_tool)

    # Missing tool lookup must raise KeyError
    with pytest.raises(KeyError, match="not found"):
        registry.get("non_existent_tool")


def test_capability_lookup():
    """Verify lookup by capability across registered tools."""
    registry = ToolRegistry.create_default()
    tools = registry.find_by_capability("distribution_analysis")
    assert len(tools) >= 1
    assert any(t.name == "compute_distributions" for t in tools)

    anom_tools = registry.find_by_capability("anomaly_detection")
    assert len(anom_tools) >= 1
    assert any(t.name == "detect_anomalies" for t in anom_tools)


def test_tabular_summary_handler(sample_dataset):
    """Verify structural dataset summary handler."""
    res = tabular_summary_handler(sample_dataset)

    assert res["row_count"] == 9
    assert sorted(res["column_names"]) == ["category", "cost", "id", "revenue"]
    assert res["column_types"]["revenue"] == "float"
    assert res["null_counts"]["revenue"] == 0


def test_compute_distributions_handler(sample_dataset):
    """Verify statistical distribution computations."""
    res = compute_distributions_handler(sample_dataset)

    assert res["record_count"] == 9
    assert "revenue" in res["columns"]
    assert "cost" in res["columns"]

    cost_stats = res["columns"]["cost"]
    assert cost_stats["count"] == 9
    assert cost_stats["min"] == 58.0
    assert cost_stats["max"] == 63.0
    assert 59.0 <= cost_stats["mean"] <= 62.0


def test_detect_anomalies_handler(sample_dataset):
    """Verify outlier detection correctly isolates injected anomalies."""
    res = detect_anomalies_handler(sample_dataset, threshold_z=2.0)

    assert res["total_detected"] >= 1
    anom_record = res["anomalies"][0]
    assert anom_record["row_index"] == 8
    assert anom_record["record"]["id"] == "rec_9"
    assert any(r["column"] == "revenue" for r in anom_record["reasons"])


def test_json_validator_handler():
    """Verify schema conformance checking."""
    schema = {
        "type": "object",
        "required": ["name", "score"],
        "properties": {
            "name": {"type": "string"},
            "score": {"type": "number"}
        }
    }

    valid_payload = {"name": "agent_alpha", "score": 95.5}
    invalid_payload = {"name": "agent_beta"}  # Missing score

    res_valid = json_validator_handler(valid_payload, schema)
    assert res_valid["valid"] is True
    assert len(res_valid["errors"]) == 0

    res_invalid = json_validator_handler(invalid_payload, schema)
    assert res_invalid["valid"] is False
    assert any("score" in err for err in res_invalid["errors"])


def test_sandboxed_executor_success(sample_dataset):
    """Verify ToolExecutor handles successful invocations and records execution latency."""
    registry = ToolRegistry.create_default()
    executor = ToolExecutor()

    tool = registry.get("tabular_summary")
    res = executor.execute(tool, {"dataset": sample_dataset})

    assert isinstance(res, ToolResult)
    assert res.success is True
    assert res.output["row_count"] == 9
    assert res.error is None
    assert res.execution_time_ms >= 0.0


def test_sandboxed_executor_validation_failure():
    """Verify ToolExecutor catches schema parameter validation errors before execution."""
    registry = ToolRegistry.create_default()
    executor = ToolExecutor()

    tool = registry.get("tabular_summary")
    # Missing required 'dataset' parameter
    res = executor.execute(tool, {"bad_param": 123})

    assert res.success is False
    assert "Parameter validation failed" in res.error
    assert res.output is None


def test_sandboxed_executor_handler_exception():
    """Verify ToolExecutor catches runtime exceptions inside tool handlers cleanly."""
    def broken_handler(dataset):
        raise ZeroDivisionError("Simulated calculation explosion")

    tool = ToolDefinition(
        name="exploding_tool",
        description="Always fails",
        parameters={"type": "object", "properties": {"dataset": {"type": "array"}}, "required": ["dataset"]},
        capabilities=["chaos"],
        handler=broken_handler
    )

    executor = ToolExecutor()
    res = executor.execute(tool, {"dataset": []})

    assert res.success is False
    assert "ZeroDivisionError" in res.error
    assert res.output is None
