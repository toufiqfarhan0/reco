"""Tool Registry and deterministic domain analytical tools."""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ToolDefinition(BaseModel):
    """Specification and executable handler for an agent tool."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(description="Unique tool identifier")
    description: str = Field(description="Purpose and capability of the tool")
    parameters: Dict[str, Any] = Field(description="JSON schema for tool arguments")
    capabilities: List[str] = Field(default_factory=list, description="Capabilities provided by this tool")
    handler: Optional[Callable[..., Any]] = Field(default=None, exclude=True, description="Callable execution handler")


# ==============================================================================
# Built-in Deterministic Analytical Tool Handlers
# ==============================================================================

def tabular_summary_handler(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute structural metrics and schema for a tabular dataset."""
    if not dataset:
        return {
            "row_count": 0,
            "column_names": [],
            "column_types": {},
            "null_counts": {}
        }

    row_count = len(dataset)
    # Collect all unique column names
    all_keys = set()
    for row in dataset:
        all_keys.update(row.keys())
    column_names = sorted(list(all_keys))

    column_types: Dict[str, str] = {}
    null_counts: Dict[str, int] = {col: 0 for col in column_names}

    for col in column_names:
        sample_type = None
        for row in dataset:
            val = row.get(col)
            if val is None:
                null_counts[col] += 1
            elif sample_type is None:
                sample_type = type(val).__name__
        column_types[col] = sample_type or "null"

    return {
        "row_count": row_count,
        "column_names": column_names,
        "column_types": column_types,
        "null_counts": null_counts
    }


def compute_distributions_handler(
    dataset: List[Dict[str, Any]],
    columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Calculate statistical distribution metrics for numeric fields."""
    if not dataset:
        return {"columns": {}, "record_count": 0}

    # Identify numeric columns
    numeric_cols = []
    if columns:
        numeric_cols = columns
    else:
        first_row = dataset[0]
        for k, v in first_row.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                numeric_cols.append(k)

    distributions: Dict[str, Any] = {}

    for col in numeric_cols:
        values = [
            float(row[col]) for row in dataset
            if col in row and row[col] is not None and isinstance(row[col], (int, float)) and not isinstance(row[col], bool)
        ]

        if not values:
            continue

        n = len(values)
        mean_val = sum(values) / n
        sorted_vals = sorted(values)

        # Standard deviation
        variance = sum((x - mean_val) ** 2 for x in values) / n if n > 1 else 0.0
        std_val = math.sqrt(variance)

        # Quartiles
        def get_percentile(p: float) -> float:
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return sorted_vals[int(k)]
            return sorted_vals[int(f)] * (c - k) + sorted_vals[int(c)] * (k - f)

        distributions[col] = {
            "count": n,
            "mean": round(mean_val, 4),
            "std": round(std_val, 4),
            "min": round(sorted_vals[0], 4),
            "max": round(sorted_vals[-1], 4),
            "median": round(get_percentile(0.50), 4),
            "q25": round(get_percentile(0.25), 4),
            "q75": round(get_percentile(0.75), 4)
        }

    return {
        "columns": distributions,
        "record_count": len(dataset)
    }


def detect_anomalies_handler(
    dataset: List[Dict[str, Any]],
    threshold_z: float = 2.5,
    columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Detect outlier / anomalous records using standard Z-score deviations."""
    if not dataset:
        return {"anomalies": [], "total_detected": 0}

    # Compute distribution for numeric columns
    dists = compute_distributions_handler(dataset, columns=columns)["columns"]
    anomalies: List[Dict[str, Any]] = []

    for idx, row in enumerate(dataset):
        row_anomalies = []
        for col, stats in dists.items():
            val = row.get(col)
            if val is not None and isinstance(val, (int, float)) and not isinstance(val, bool):
                std = stats["std"]
                mean = stats["mean"]
                if std > 0:
                    z = abs((float(val) - mean) / std)
                    if z >= threshold_z:
                        row_anomalies.append({
                            "column": col,
                            "value": val,
                            "mean": mean,
                            "std": std,
                            "z_score": round(z, 2)
                        })

        if row_anomalies:
            anomalies.append({
                "row_index": idx,
                "reasons": row_anomalies,
                "record": row
            })

    return {
        "anomalies": anomalies,
        "total_detected": len(anomalies),
        "threshold_z": threshold_z
    }


def json_validator_handler(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a JSON object structure against required schema keys."""
    errors = []
    required_keys = schema.get("required", [])

    for rk in required_keys:
        if rk not in data:
            errors.append(f"Missing required field: '{rk}'")

    properties = schema.get("properties", {})
    for prop, spec in properties.items():
        if prop in data:
            val = data[prop]
            expected_type = spec.get("type")
            if expected_type == "object" and not isinstance(val, dict):
                errors.append(f"Field '{prop}' must be an object (got {type(val).__name__})")
            elif expected_type == "array" and not isinstance(val, list):
                errors.append(f"Field '{prop}' must be a list/array (got {type(val).__name__})")
            elif expected_type == "string" and not isinstance(val, str):
                errors.append(f"Field '{prop}' must be a string (got {type(val).__name__})")
            elif expected_type == "number" and not isinstance(val, (int, float)):
                errors.append(f"Field '{prop}' must be numeric (got {type(val).__name__})")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# ==============================================================================
# Tool Registry Class
# ==============================================================================

class ToolRegistry:
    """Central repository for agent-callable tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition into the catalog."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        """Retrieve a tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry.")
        return self._tools[name]

    def has(self, name: str) -> bool:
        """Check if a tool exists in the registry."""
        return name in self._tools

    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def find_by_capability(self, capability: str) -> List[ToolDefinition]:
        """Find tools supporting a given capability."""
        cap_lower = capability.lower()
        matches = []
        for tool in self._tools.values():
            if any(c.lower() == cap_lower for c in tool.capabilities):
                matches.append(tool)
        return matches

    @classmethod
    def create_default(cls) -> ToolRegistry:
        """Create a registry pre-loaded with standard deterministic analytical tools."""
        registry = cls()

        registry.register(ToolDefinition(
            name="tabular_summary",
            description="Computes structural column metrics, types, and null counts for tabular data.",
            parameters={
                "type": "object",
                "properties": {
                    "dataset": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["dataset"]
            },
            capabilities=["tabular_parsing", "data_processing"],
            handler=tabular_summary_handler
        ))

        registry.register(ToolDefinition(
            name="compute_distributions",
            description="Calculates distribution statistics (mean, std, median, quartiles) for numeric fields.",
            parameters={
                "type": "object",
                "properties": {
                    "dataset": {"type": "array", "items": {"type": "object"}},
                    "columns": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["dataset"]
            },
            capabilities=["distribution_analysis", "statistical_distribution"],
            handler=compute_distributions_handler
        ))

        registry.register(ToolDefinition(
            name="detect_anomalies",
            description="Detects anomalous / outlier records using Z-score deviations from numeric distributions.",
            parameters={
                "type": "object",
                "properties": {
                    "dataset": {"type": "array", "items": {"type": "object"}},
                    "threshold_z": {"type": "number", "default": 2.5},
                    "columns": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["dataset"]
            },
            capabilities=["anomaly_detection", "outlier_detection"],
            handler=detect_anomalies_handler
        ))

        registry.register(ToolDefinition(
            name="json_validator",
            description="Validates a JSON data object against required structure and types.",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "object"},
                    "schema": {"type": "object"}
                },
                "required": ["data", "schema"]
            },
            capabilities=["verification", "schema_validation"],
            handler=json_validator_handler
        ))

        return registry
