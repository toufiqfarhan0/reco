"""Deterministic anomaly detection tools registered in Reco's ToolRegistry."""

import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from reco.core.interfaces import Tool, ToolResult
from reco.tools.registry import ToolRegistry


class ReadTabularDatasetTool(Tool):
    """Parses and inspects a tabular dataset payload, returning shape and column profiles."""

    name: str = "read_tabular_dataset"
    description: str = (
        "Inspect a tabular dataset. Returns the total record count, column names, "
        "and data type inferences for each column."
    )
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "dataset": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of tabular record dictionaries.",
            }
        },
        "required": ["dataset"],
    }

    @property
    def risk_level(self) -> str:
        return "LOW"

    @property
    def category(self) -> str:
        return "anomaly_detection"

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        dataset = arguments.get("dataset", [])
        if not isinstance(dataset, list):
            return ToolResult(success=False, error="Input 'dataset' must be a list of records.")

        if not dataset:
            return ToolResult(
                success=True,
                data={"record_count": 0, "columns": [], "column_types": {}},
            )

        columns = list(dataset[0].keys()) if isinstance(dataset[0], dict) else []
        column_types: Dict[str, str] = {}
        for col in columns:
            types_seen = set()
            for row in dataset:
                if isinstance(row, dict) and col in row:
                    val = row[col]
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        types_seen.add("numeric")
                    elif isinstance(val, bool):
                        types_seen.add("boolean")
                    else:
                        types_seen.add("string")
            column_types[col] = "numeric" if types_seen == {"numeric"} else "string"

        return ToolResult(
            success=True,
            data={
                "record_count": len(dataset),
                "columns": columns,
                "column_types": column_types,
            },
        )


class ComputeStatisticalSummaryTool(Tool):
    """Calculates summary statistics (mean, std, min, max, IQR, z-scores) for numeric fields."""

    name: str = "compute_statistical_summary"
    description: str = (
        "Computes descriptive statistics (mean, std dev, min, max, IQR, quantiles) "
        "for numeric fields in a dataset."
    )
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "dataset": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of records to analyze.",
            },
            "field": {
                "type": "string",
                "description": "Numeric column name to compute statistics for.",
            },
        },
        "required": ["dataset", "field"],
    }

    @property
    def risk_level(self) -> str:
        return "LOW"

    @property
    def category(self) -> str:
        return "anomaly_detection"

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        dataset = arguments.get("dataset", [])
        field = arguments.get("field")
        if not dataset or not field:
            return ToolResult(success=False, error="Arguments 'dataset' and 'field' are required.")

        values: List[float] = []
        for row in dataset:
            if isinstance(row, dict) and field in row:
                val = row[field]
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    continue

        if not values:
            return ToolResult(success=False, error=f"No valid numeric values found for field '{field}'.")

        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n if n > 1 else 0.0
        std = math.sqrt(variance)

        sorted_vals = sorted(values)
        min_v = sorted_vals[0]
        max_v = sorted_vals[-1]
        p25 = sorted_vals[int(0.25 * (n - 1))]
        p50 = sorted_vals[int(0.50 * (n - 1))]
        p75 = sorted_vals[int(0.75 * (n - 1))]
        iqr = p75 - p25

        return ToolResult(
            success=True,
            data={
                "field": field,
                "count": n,
                "mean": round(mean, 4),
                "std": round(std, 4),
                "min": round(min_v, 4),
                "max": round(max_v, 4),
                "median": round(p50, 4),
                "p25": round(p25, 4),
                "p75": round(p75, 4),
                "iqr": round(iqr, 4),
            },
        )


class DetectDistributionAnomaliesTool(Tool):
    """Applies statistical tests (Z-score, IQR, frequency) to identify anomalous records."""

    name: str = "detect_distribution_anomalies"
    description: str = (
        "Applies deterministic statistical anomaly detection (Z-score > threshold, "
        "IQR fence > factor, or categorical frequency < min_freq) and returns anomalous record IDs."
    )
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "dataset": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Dataset records to scan for anomalies.",
            },
            "id_field": {
                "type": "string",
                "description": "Primary key / identifier field (default 'id' or 'record_id').",
            },
            "numeric_field": {
                "type": "string",
                "description": "Numeric column to evaluate.",
            },
            "categorical_field": {
                "type": "string",
                "description": "Categorical column to evaluate.",
            },
            "z_threshold": {
                "type": "number",
                "description": "Z-score threshold for outliers (default 3.0).",
            },
            "iqr_factor": {
                "type": "number",
                "description": "IQR multiplier for fences (default 1.5).",
            },
        },
        "required": ["dataset"],
    }

    @property
    def risk_level(self) -> str:
        return "LOW"

    @property
    def category(self) -> str:
        return "anomaly_detection"

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        dataset = arguments.get("dataset", [])
        if not dataset:
            return ToolResult(success=True, data={"flagged_anomalies": [], "count": 0})

        id_field = arguments.get("id_field")
        if not id_field:
            for cand in ["record_id", "id", "transaction_id", "sensor_id"]:
                if cand in dataset[0]:
                    id_field = cand
                    break
            id_field = id_field or "id"

        numeric_field = arguments.get("numeric_field")
        categorical_field = arguments.get("categorical_field")
        z_threshold = float(arguments.get("z_threshold", 3.0))
        iqr_factor = float(arguments.get("iqr_factor", 1.5))

        flagged: List[Dict[str, Any]] = []

        # 1. Numeric anomaly detection
        if numeric_field:
            values: List[tuple[Any, float]] = []
            for row in dataset:
                rid = row.get(id_field, "unknown")
                val = row.get(numeric_field)
                if val is not None:
                    try:
                        values.append((rid, float(val)))
                    except (ValueError, TypeError):
                        pass

            if values:
                n = len(values)
                mean = sum(v for _, v in values) / n
                std = math.sqrt(sum((v - mean) ** 2 for _, v in values) / n) if n > 1 else 0.0

                sorted_vals = sorted(v for _, v in values)
                p25 = sorted_vals[int(0.25 * (n - 1))]
                p75 = sorted_vals[int(0.75 * (n - 1))]
                iqr = p75 - p25
                lower_fence = p25 - (iqr_factor * iqr)
                upper_fence = p75 + (iqr_factor * iqr)

                for rid, v in values:
                    z = abs(v - mean) / std if std > 0 else 0.0
                    is_outlier = (z > z_threshold) or (v < lower_fence or v > upper_fence)
                    if is_outlier:
                        flagged.append({
                            "record_id": rid,
                            "field": numeric_field,
                            "value": v,
                            "reason": f"Numeric outlier: z-score={z:.2f} > {z_threshold} or outside [{lower_fence:.1f}, {upper_fence:.1f}]",
                            "anomaly_type": "numerical_outlier",
                            "score": round(min(z / (z_threshold * 2), 1.0), 4),
                        })

        # 2. Categorical anomaly detection
        if categorical_field:
            counts: Dict[str, int] = {}
            for row in dataset:
                cat = str(row.get(categorical_field, ""))
                counts[cat] = counts.get(cat, 0) + 1
            total = len(dataset)
            for row in dataset:
                rid = row.get(id_field, "unknown")
                cat = str(row.get(categorical_field, ""))
                freq = counts.get(cat, 0) / total if total > 0 else 0.0
                if freq < 0.05 and total >= 10:
                    flagged.append({
                        "record_id": rid,
                        "field": categorical_field,
                        "value": cat,
                        "reason": f"Rare categorical value with frequency {freq:.3f} (< 0.05)",
                        "anomaly_type": "categorical_anomaly",
                        "score": round(1.0 - freq, 4),
                    })

        return ToolResult(
            success=True,
            data={
                "flagged_anomalies": flagged,
                "count": len(flagged),
                "evaluated_records": len(dataset),
            },
        )


def register_anomaly_tools(registry: ToolRegistry) -> None:
    """Register all anomaly detection domain tools into a ToolRegistry."""
    registry.register(ReadTabularDatasetTool())
    registry.register(ComputeStatisticalSummaryTool())
    registry.register(DetectDistributionAnomaliesTool())
