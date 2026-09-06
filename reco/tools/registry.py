"""Tool Registry and deterministic domain analytical tools."""

from __future__ import annotations

import math
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
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


def _parse_amount(val: Any) -> Optional[float]:
    """Helper to parse numeric amount from float, int, or currency string."""
    if val is None:
        return None
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    if isinstance(val, str):
        cleaned = val.replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def exact_reconcile_handler(
    source_records: Optional[List[Dict[str, Any]]] = None,
    target_records: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Reconcile transactions between source and target ledgers using strict ID and amount equality."""
    src = source_records or []
    tgt = target_records or []

    matched_ids = []
    discrepancy_ids = []
    unmatched_source_ids = []
    unmatched_target_ids = []
    duplicate_ids = []

    src_map: Dict[str, List[Dict[str, Any]]] = {}
    for r in src:
        rid = str(r.get("id", ""))
        src_map.setdefault(rid, []).append(r)

    tgt_map: Dict[str, List[Dict[str, Any]]] = {}
    for r in tgt:
        rid = str(r.get("id", ""))
        tgt_map.setdefault(rid, []).append(r)

    # Detect duplicates in target or source
    for rid, records in tgt_map.items():
        if len(records) > 1 and rid not in duplicate_ids:
            duplicate_ids.append(rid)
    for rid, records in src_map.items():
        if len(records) > 1 and rid not in duplicate_ids:
            duplicate_ids.append(rid)

    all_src_ids = set(src_map.keys())
    all_tgt_ids = set(tgt_map.keys())
    shared_ids = all_src_ids.intersection(all_tgt_ids)

    for rid in sorted(list(shared_ids)):
        src_rec = src_map[rid][0]
        tgt_rec = tgt_map[rid][0]

        src_amt = src_rec.get("amount")
        tgt_amt = tgt_rec.get("amount")

        # Strict matching: numeric equality without currency string parsing
        is_amt_match = False
        try:
            if isinstance(src_amt, (int, float)) and isinstance(tgt_amt, (int, float)):
                is_amt_match = math.isclose(float(src_amt), float(tgt_amt), abs_tol=1e-3)
            else:
                is_amt_match = (src_amt == tgt_amt)
        except Exception:
            is_amt_match = (src_amt == tgt_amt)

        if is_amt_match:
            matched_ids.append(rid)
        else:
            discrepancy_ids.append(rid)

    for rid in sorted(list(all_src_ids - all_tgt_ids)):
        unmatched_source_ids.append(rid)

    for rid in sorted(list(all_tgt_ids - all_src_ids)):
        unmatched_target_ids.append(rid)

    status = "reconciled"
    if discrepancy_ids or unmatched_source_ids or unmatched_target_ids:
        status = "discrepancy_detected"
    elif duplicate_ids:
        status = "duplicate_detected"

    return {
        "matched_ids": matched_ids,
        "unmatched_source_ids": unmatched_source_ids,
        "unmatched_target_ids": unmatched_target_ids,
        "discrepancy_ids": discrepancy_ids,
        "duplicate_ids": duplicate_ids,
        "matched_count": len(matched_ids),
        "discrepancy_count": len(discrepancy_ids),
        "duplicate_count": len(duplicate_ids),
        "status": status
    }


def smart_reconcile_handler(
    source_records: Optional[List[Dict[str, Any]]] = None,
    target_records: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Smart reconciliation normalizing casing, currency strings, and timestamps."""
    src = source_records or []
    tgt = target_records or []

    matched_ids = []
    discrepancy_ids = []
    unmatched_source_ids = []
    unmatched_target_ids = []
    duplicate_ids = []

    # Normalized maps: key is uppercase stripped id
    src_map: Dict[str, List[Dict[str, Any]]] = {}
    canonical_id_map: Dict[str, str] = {}
    for r in src:
        raw_id = str(r.get("id", ""))
        norm_id = raw_id.strip().upper()
        canonical_id_map[norm_id] = raw_id.strip()
        src_map.setdefault(norm_id, []).append(r)

    tgt_map: Dict[str, List[Dict[str, Any]]] = {}
    for r in tgt:
        raw_id = str(r.get("id", ""))
        norm_id = raw_id.strip().upper()
        if norm_id not in canonical_id_map:
            canonical_id_map[norm_id] = raw_id.strip()
        tgt_map.setdefault(norm_id, []).append(r)

    for norm_id, records in tgt_map.items():
        if len(records) > 1:
            duplicate_ids.append(canonical_id_map[norm_id])
    for norm_id, records in src_map.items():
        if len(records) > 1 and canonical_id_map[norm_id] not in duplicate_ids:
            duplicate_ids.append(canonical_id_map[norm_id])

    all_src_ids = set(src_map.keys())
    all_tgt_ids = set(tgt_map.keys())
    shared_ids = all_src_ids.intersection(all_tgt_ids)

    for norm_id in sorted(list(shared_ids)):
        cid = canonical_id_map[norm_id]
        src_rec = src_map[norm_id][0]
        tgt_rec = tgt_map[norm_id][0]

        src_amt = _parse_amount(src_rec.get("amount"))
        tgt_amt = _parse_amount(tgt_rec.get("amount"))

        if src_amt is not None and tgt_amt is not None:
            if math.isclose(src_amt, tgt_amt, abs_tol=1e-3):
                matched_ids.append(cid)
            else:
                discrepancy_ids.append(cid)
        else:
            if src_rec.get("amount") == tgt_rec.get("amount"):
                matched_ids.append(cid)
            else:
                discrepancy_ids.append(cid)

    for norm_id in sorted(list(all_src_ids - all_tgt_ids)):
        unmatched_source_ids.append(canonical_id_map[norm_id])

    for norm_id in sorted(list(all_tgt_ids - all_src_ids)):
        unmatched_target_ids.append(canonical_id_map[norm_id])

    status = "reconciled"
    if discrepancy_ids or unmatched_source_ids or unmatched_target_ids:
        status = "discrepancy_detected"
    elif duplicate_ids:
        status = "duplicate_detected"

    return {
        "matched_ids": matched_ids,
        "unmatched_source_ids": unmatched_source_ids,
        "unmatched_target_ids": unmatched_target_ids,
        "discrepancy_ids": discrepancy_ids,
        "duplicate_ids": duplicate_ids,
        "matched_count": len(matched_ids),
        "discrepancy_count": len(discrepancy_ids),
        "duplicate_count": len(duplicate_ids),
        "status": status
    }


# ==============================================================================
# System Anomaly Detection Tool Handlers
# ==============================================================================

def compute_zscore_handler(
    values: Optional[List[Union[float, int]]] = None,
    threshold: float = 2.5,
    timestamps: Optional[List[str]] = None,
    labels: Optional[List[str]] = None,
    dataset: Optional[List[Dict[str, Any]]] = None,
    column: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Compute Z-scores for a numeric series and isolate statistical anomalies exceeding threshold."""
    series: List[float] = []
    if values is not None:
        series = [float(v) for v in values if v is not None and isinstance(v, (int, float)) and not isinstance(v, bool)]
    elif dataset and column:
        series = [
            float(row[column]) for row in dataset
            if column in row and row[column] is not None and isinstance(row[column], (int, float)) and not isinstance(row[column], bool)
        ]

    if not series:
        return {
            "count": 0,
            "mean": 0.0,
            "std": 0.0,
            "z_scores": [],
            "anomalies": [],
            "anomaly_indices": [],
            "anomaly_count": 0,
            "has_anomaly": False,
            "threshold": threshold,
            "status": "normal"
        }

    n = len(series)
    mean = sum(series) / n
    variance = sum((x - mean) ** 2 for x in series) / n
    std = math.sqrt(variance)

    z_scores: List[float] = []
    anomalies: List[Dict[str, Any]] = []
    anomaly_indices: List[int] = []

    for idx, val in enumerate(series):
        z = (val - mean) / std if std > 0 else 0.0
        z_round = round(z, 4)
        z_scores.append(z_round)
        if abs(z) >= threshold:
            anomaly_indices.append(idx)
            anomaly_item: Dict[str, Any] = {
                "index": idx,
                "value": val,
                "z_score": z_round,
                "threshold": threshold,
            }
            if timestamps and idx < len(timestamps):
                anomaly_item["timestamp"] = timestamps[idx]
            if labels and idx < len(labels):
                anomaly_item["label"] = labels[idx]
            anomalies.append(anomaly_item)

    return {
        "count": n,
        "mean": round(mean, 4),
        "std": round(std, 4),
        "z_scores": z_scores,
        "anomalies": anomalies,
        "anomaly_indices": anomaly_indices,
        "anomaly_count": len(anomalies),
        "has_anomaly": len(anomalies) > 0,
        "threshold": threshold,
        "status": "anomaly_detected" if anomalies else "normal"
    }


def check_threshold_handler(
    metrics: Optional[Dict[str, Union[float, int]]] = None,
    thresholds: Optional[Dict[str, Any]] = None,
    operator: str = ">",
    records: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Evaluate system metrics against warning and critical thresholds."""
    metrics_map: Dict[str, float] = {}
    if metrics:
        for k, v in metrics.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                metrics_map[k] = float(v)
    elif records and isinstance(records, list) and records:
        latest = records[-1]
        for k, v in latest.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                metrics_map[k] = float(v)

    thresholds_map = thresholds or {}
    breaches: List[Dict[str, Any]] = []
    critical_count = 0
    warning_count = 0

    def evaluate_op(val: float, limit: float, op: str) -> bool:
        if op == ">":
            return val > limit
        elif op == ">=":
            return val >= limit
        elif op == "<":
            return val < limit
        elif op == "<=":
            return val <= limit
        elif op in ("==", "="):
            return math.isclose(val, limit, abs_tol=1e-3)
        return val > limit

    for metric_name, val in metrics_map.items():
        if metric_name not in thresholds_map:
            continue
        rule = thresholds_map[metric_name]

        if isinstance(rule, dict):
            crit_limit = rule.get("critical")
            warn_limit = rule.get("warning")
            op = rule.get("operator", operator)

            if crit_limit is not None and evaluate_op(val, float(crit_limit), op):
                critical_count += 1
                breaches.append({
                    "metric": metric_name,
                    "value": val,
                    "level": "critical",
                    "threshold": float(crit_limit),
                    "operator": op,
                    "message": f"{metric_name} ({val}) breached critical threshold {crit_limit} ({op})"
                })
            elif warn_limit is not None and evaluate_op(val, float(warn_limit), op):
                warning_count += 1
                breaches.append({
                    "metric": metric_name,
                    "value": val,
                    "level": "warning",
                    "threshold": float(warn_limit),
                    "operator": op,
                    "message": f"{metric_name} ({val}) breached warning threshold {warn_limit} ({op})"
                })
        elif isinstance(rule, (int, float)):
            limit = float(rule)
            if evaluate_op(val, limit, operator):
                critical_count += 1
                breaches.append({
                    "metric": metric_name,
                    "value": val,
                    "level": "critical",
                    "threshold": limit,
                    "operator": operator,
                    "message": f"{metric_name} ({val}) breached threshold {limit} ({operator})"
                })

    status = "healthy"
    if critical_count > 0:
        status = "critical"
    elif warning_count > 0:
        status = "warning"

    return {
        "status": status,
        "is_healthy": status == "healthy",
        "breaches": breaches,
        "breach_count": len(breaches),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "metrics_evaluated": len(metrics_map)
    }


def extract_error_logs_handler(
    logs: Union[List[str], str] = "",
    min_level: str = "WARN",
    service_filter: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Parse log streams to isolate warning/error/critical events and identify root-cause candidates."""
    if isinstance(logs, str):
        lines = [line.strip() for line in logs.splitlines() if line.strip()]
    elif isinstance(logs, list):
        lines = [str(line).strip() for line in logs if str(line).strip()]
    else:
        lines = []

    level_hierarchy = {"DEBUG": 0, "INFO": 1, "WARN": 2, "WARNING": 2, "ERROR": 3, "CRITICAL": 4, "FATAL": 5}
    threshold_rank = level_hierarchy.get(min_level.upper(), 2)

    extracted_errors: List[Dict[str, Any]] = []
    error_type_counts: Dict[str, int] = {}
    services_affected: set[str] = set()
    level_counts: Dict[str, int] = {"warning": 0, "error": 0, "critical": 0}

    ts_pattern = re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)")
    level_pattern = re.compile(r"\b(DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE)
    service_pattern = re.compile(r"\[([a-zA-Z0-9_\-]+(?:-service|-api|-worker|-db|-gateway)?)\]|service=([a-zA-Z0-9_\-]+)")
    err_type_pattern = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:Exception|Error|Fault|Timeout|Failure))\b")

    for line in lines:
        lvl_match = level_pattern.search(line)
        lvl = lvl_match.group(1).upper() if lvl_match else "INFO"
        if lvl == "WARNING":
            lvl = "WARN"

        lvl_rank = level_hierarchy.get(lvl, 1)
        if lvl_rank < threshold_rank:
            continue

        svc = "unknown"
        brackets = re.findall(r"\[([^\]]+)\]", line)
        for b in brackets:
            b_clean = b.strip()
            if b_clean.upper() in ("DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"):
                continue
            if re.search(r"\d{4}-\d{2}-\d{2}", b_clean):
                continue
            svc = b_clean
            break
        if svc == "unknown":
            svc_match = re.search(r"\bservice=([a-zA-Z0-9_\-]+)", line, re.IGNORECASE)
            if svc_match:
                svc = svc_match.group(1)

        if service_filter and service_filter.lower() != svc.lower():
            continue

        ts = None
        ts_match = ts_pattern.search(line)
        if ts_match:
            ts = ts_match.group(1)

        err_type = "UnspecifiedError"
        err_match = err_type_pattern.search(line)
        if err_match:
            err_type = err_match.group(1)
        elif "timeout" in line.lower():
            err_type = "TimeoutError"
        elif "connection" in line.lower():
            err_type = "ConnectionError"
        elif "out of memory" in line.lower() or "oom" in line.lower():
            err_type = "OutOfMemoryError"

        norm_lvl = "warning" if lvl == "WARN" else ("critical" if lvl in ("CRITICAL", "FATAL") else "error")
        level_counts[norm_lvl] += 1
        services_affected.add(svc)
        error_type_counts[err_type] = error_type_counts.get(err_type, 0) + 1

        extracted_errors.append({
            "timestamp": ts,
            "level": lvl,
            "service": svc,
            "message": line,
            "error_type": err_type
        })

    root_cause_candidate = None
    if error_type_counts:
        root_cause_candidate = max(error_type_counts, key=error_type_counts.get)

    return {
        "total_logs": len(lines),
        "matched_logs": len(extracted_errors),
        "extracted_errors": extracted_errors,
        "error_count": level_counts["error"],
        "critical_count": level_counts["critical"],
        "warning_count": level_counts["warning"],
        "error_types": error_type_counts,
        "services_affected": sorted(list(services_affected)),
        "root_cause_candidate": root_cause_candidate,
        "status": "errors_detected" if extracted_errors else "clean"
    }


# ==============================================================================
# Research Synthesis Tool Handlers
# ==============================================================================

CANONICAL_CASING = {
    "glm-4-7-flash": "GLM-4.7-Flash",
    "glm-4.7-flash": "GLM-4.7-Flash",
    "glm-4": "GLM-4",
    "gpt-4": "GPT-4",
    "gpt-4o": "GPT-4o",
    "claude 3.5 sonnet": "Claude 3.5 Sonnet",
    "claude-3-5-sonnet": "Claude 3.5 Sonnet",
    "llama-3": "Llama-3",
    "llama 3": "Llama-3",
    "deepseek-r1": "DeepSeek-R1",
    "deepseek": "DeepSeek",
    "mistral": "Mistral",
    "bert": "BERT",
    "swe-bench": "SWE-bench",
    "swe-bench verified": "SWE-bench",
    "gsm8k": "GSM8K",
    "humaneval": "HumanEval",
    "mmlu": "MMLU",
    "imagenet": "ImageNet",
    "squad": "SQuAD",
    "arc": "ARC",
    "math": "MATH",
    "accuracy": "Accuracy",
    "f1": "F1",
    "f1-score": "F1",
    "f1_score": "F1",
    "bleu": "BLEU",
    "latency": "Latency",
    "throughput": "Throughput",
    "precision": "Precision",
    "recall": "Recall",
    "z-score": "Z-Score",
    "error rate": "Error Rate",
    "win rate": "Win Rate",
    "exact match": "Exact Match",
    "zhipu ai": "Zhipu AI",
    "z.ai": "Zhipu AI",
    "openai": "OpenAI",
    "google": "Google",
    "anthropic": "Anthropic",
    "meta": "Meta",
    "microsoft": "Microsoft",
    "tensormux": "TensorMux",
    "moe": "MoE",
    "lora": "LoRA",
    "rlhf": "RLHF",
    "dpo": "DPO",
    "cot": "CoT",
    "rag": "RAG",
    "dag": "DAG",
}


def extract_entities_handler(
    text: Union[str, List[str], Dict[str, Any]] = "",
    entity_types: Optional[List[str]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Extract and classify domain entities (models, metrics, datasets, organizations, methods)."""
    if isinstance(text, dict):
        full_text = " \n ".join(str(v) for v in text.values())
    elif isinstance(text, list):
        full_text = " \n ".join(str(t) for t in text)
    else:
        full_text = str(text or "")

    known_models = [
        "glm-4-7-flash", "glm-4.7-flash", "glm-4", "gpt-4", "gpt-4o", "claude 3.5 sonnet",
        "claude-3-5-sonnet", "llama-3", "llama 3", "deepseek-r1", "deepseek", "mistral",
        "bert", "gemini 1.5 pro", "gemini 1.5 flash"
    ]
    known_datasets = [
        "swe-bench", "swe-bench verified", "gsm8k", "humaneval", "mmlu",
        "imagenet", "squad", "coqa", "arc", "math"
    ]
    known_metrics = [
        "accuracy", "f1", "f1-score", "bleu", "latency", "throughput",
        "precision", "recall", "z-score", "error rate", "win rate", "exact match"
    ]
    known_orgs = [
        "zhipu ai", "z.ai", "openai", "google", "anthropic", "meta",
        "deepseek", "microsoft", "tensormux"
    ]
    known_methods = [
        "moe", "lora", "rlhf", "dpo", "cot", "chain of thought", "rag",
        "dag", "tool calling", "fine-tuning", "few-shot", "zero-shot", "topological sort"
    ]

    target_types = set(t.lower() for t in entity_types) if entity_types else {
        "models", "datasets", "metrics", "organizations", "methods"
    }

    found_entities: Dict[str, List[str]] = {
        "models": [],
        "datasets": [],
        "metrics": [],
        "organizations": [],
        "methods": []
    }

    lower_text = full_text.lower()

    def search_keywords(category: str, catalog: List[str]):
        if category in target_types or category.rstrip("s") in target_types:
            for item in sorted(catalog, key=len, reverse=True):
                pattern = r"\b" + re.escape(item) + r"\b"
                if re.search(pattern, lower_text):
                    canonical = CANONICAL_CASING.get(item, item.title())
                    # Prevent prefix duplication: if a more specific name is already found, don't add substring (e.g. GLM-4 when GLM-4.7-Flash is present)
                    if any(canonical.lower() in existing.lower() and canonical.lower() != existing.lower() for existing in found_entities[category]):
                        continue
                    if canonical not in found_entities[category]:
                        found_entities[category].append(canonical)

    search_keywords("models", known_models)
    search_keywords("datasets", known_datasets)
    search_keywords("metrics", known_metrics)
    search_keywords("organizations", known_orgs)
    search_keywords("methods", known_methods)

    model_regex = re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:[-_][A-Za-z0-9]+)?)\b", full_text)
    for m in model_regex:
        if m.startswith("Model_") or m.startswith("Agent_"):
            if m not in found_entities["models"]:
                found_entities["models"].append(m)

    counts_by_type = {k: len(v) for k, v in found_entities.items()}
    all_unique: set[str] = set()
    for v in found_entities.values():
        all_unique.update(v)

    return {
        "entities": found_entities,
        "total_entities": len(all_unique),
        "counts_by_type": counts_by_type,
        "unique_entities": sorted(list(all_unique)),
        "status": "extracted"
    }


def compare_metrics_handler(
    sources: Optional[Dict[str, Any]] = None,
    baseline: Optional[str] = None,
    metrics: Optional[List[str]] = None,
    higher_is_better: Optional[Dict[str, bool]] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Compare quantitative benchmark metrics across models, papers, or systems."""
    if not sources:
        return {
            "metrics_compared": [],
            "sources": [],
            "baseline": None,
            "comparison": {},
            "leaders": {},
            "discrepancies": [],
            "summary": "No sources provided for metric comparison.",
            "status": "empty"
        }

    source_names = list(sources.keys())
    ref_baseline = baseline if baseline and baseline in sources else source_names[0]

    all_metric_keys: set[str] = set()
    for s_data in sources.values():
        all_metric_keys.update(s_data.keys())

    filter_metrics = set(metrics) if metrics else all_metric_keys
    hib_map = higher_is_better or {
        "accuracy": True, "acc": True, "score": True, "f1": True, "f1_score": True,
        "latency": False, "latency_ms": False, "error_rate": False, "cost": False, "cost_usd": False
    }

    comparison: Dict[str, Any] = {}
    leaders: Dict[str, str] = {}
    discrepancies: List[Dict[str, Any]] = []

    for m in sorted(list(filter_metrics)):
        val_map: Dict[str, float] = {}
        for s_name, s_data in sources.items():
            if m in s_data:
                raw_val = s_data[m]
                parsed_val = _parse_amount(raw_val)
                if parsed_val is not None:
                    val_map[s_name] = parsed_val

        if not val_map:
            continue

        base_val = val_map.get(ref_baseline)
        deltas: Dict[str, float] = {}
        pct_deltas: Dict[str, float] = {}
        for s_name, val in val_map.items():
            if base_val is not None and s_name != ref_baseline:
                d = val - base_val
                deltas[s_name] = round(d, 4)
                pct = (d / base_val * 100.0) if base_val != 0 else 0.0
                pct_deltas[s_name] = round(pct, 2)

        higher_better = hib_map.get(m.lower(), True)
        if higher_better:
            best_s = max(val_map, key=val_map.get)
        else:
            best_s = min(val_map, key=val_map.get)

        best_v = val_map[best_s]
        leaders[m] = best_s

        vals = list(val_map.values())
        max_diff = max(vals) - min(vals) if vals else 0.0
        has_disc = max_diff > 1e-4

        if has_disc:
            discrepancies.append({
                "metric": m,
                "max_difference": round(max_diff, 4),
                "divergence": f"Span of {round(max_diff, 4)} across {len(vals)} sources"
            })

        comparison[m] = {
            "values": val_map,
            "deltas_from_baseline": deltas,
            "pct_deltas_from_baseline": pct_deltas,
            "best_source": best_s,
            "best_value": best_v,
            "has_discrepancy": has_disc,
            "max_discrepancy": round(max_diff, 4)
        }

    summary_parts = [f"Compared {len(comparison)} metrics across {len(source_names)} sources ({', '.join(source_names)})."]
    for m, best_s in leaders.items():
        summary_parts.append(f"{m} leader: {best_s} ({comparison[m]['best_value']}).")

    return {
        "metrics_compared": sorted(list(comparison.keys())),
        "sources": source_names,
        "baseline": ref_baseline,
        "comparison": comparison,
        "leaders": leaders,
        "discrepancies": discrepancies,
        "summary": " ".join(summary_parts),
        "status": "comparison_complete"
    }


def summarize_text_handler(
    text: Union[str, List[str], Dict[str, str]] = "",
    focus_topics: Optional[List[str]] = None,
    max_key_points: int = 5,
    style: str = "executive",
    **kwargs: Any
) -> Dict[str, Any]:
    """Generate structured multi-source research summary and isolate key findings."""
    doc_entries: List[Tuple[str, str]] = []
    if isinstance(text, dict):
        for doc_id, content in text.items():
            doc_entries.append((doc_id, str(content)))
    elif isinstance(text, list):
        for idx, content in enumerate(text):
            doc_entries.append((f"source_{idx+1}", str(content)))
    else:
        doc_entries.append(("source_1", str(text or "")))

    all_sentences: List[Tuple[str, str]] = []
    for doc_id, content in doc_entries:
        raw_sents = re.split(r"(?<=[.!?])\s+", content.strip())
        for s in raw_sents:
            cleaned = s.strip()
            if len(cleaned) > 15:
                all_sentences.append((doc_id, cleaned))

    topics = [t.lower() for t in focus_topics] if focus_topics else []
    scored_sentences: List[Tuple[float, str, str]] = []

    for doc_id, s in all_sentences:
        lower_s = s.lower()
        score = 1.0
        for t in topics:
            if t in lower_s:
                score += 3.0
        if any(w in lower_s for w in ["accuracy", "latency", "result", "improved", "outperform", "found", "critical", "significant"]):
            score += 2.0
        if re.search(r"\d+(?:\.\d+)?%?", lower_s):
            score += 1.5
        scored_sentences.append((score, doc_id, s))

    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    selected_points = [item[2] for item in scored_sentences[:max_key_points]]
    covered_topics = [t for t in topics if any(t in s.lower() for _, s in all_sentences)]

    if style == "executive":
        summary = "Executive Summary: " + " ".join(selected_points[:2]) if selected_points else "No content available to summarize."
    elif style == "comparative":
        summary = "Comparative Synthesis: " + " | ".join(selected_points)
    else:
        summary = " ".join(selected_points)

    total_words = sum(len(content.split()) for _, content in doc_entries)

    return {
        "summary": summary,
        "key_points": selected_points,
        "topics_covered": covered_topics if topics else ["general_synthesis"],
        "source_count": len(doc_entries),
        "word_count": total_words,
        "sentence_count": len(all_sentences),
        "status": "summarized"
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

    @classmethod
    def create_reconciliation_default(cls) -> ToolRegistry:
        """Create a registry loaded with both analytical and reconciliation tools."""
        registry = cls.create_default()

        registry.register(ToolDefinition(
            name="exact_reconcile",
            description="Reconciles transaction records between source and target ledgers using exact ID and amount matching.",
            parameters={
                "type": "object",
                "properties": {
                    "source_records": {"type": "array", "items": {"type": "object"}},
                    "target_records": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["source_records", "target_records"]
            },
            capabilities=["reconciliation", "transaction_parsing"],
            handler=exact_reconcile_handler
        ))

        registry.register(ToolDefinition(
            name="smart_reconcile",
            description="Reconciles transaction records normalizing currency formatting, casing, and timestamps.",
            parameters={
                "type": "object",
                "properties": {
                    "source_records": {"type": "array", "items": {"type": "object"}},
                    "target_records": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["source_records", "target_records"]
            },
            capabilities=["advanced_reconciliation", "smart_matching"],
            handler=smart_reconcile_handler
        ))

        return registry

    def register_anomaly_tools(self) -> None:
        """Register system anomaly detection tools into this registry."""
        self.register(ToolDefinition(
            name="compute_zscore",
            description="Calculates Z-scores for time series or numeric metric values and isolates statistical anomalies.",
            parameters={
                "type": "object",
                "properties": {
                    "values": {"type": "array", "items": {"type": "number"}, "description": "Numeric series to evaluate"},
                    "threshold": {"type": "number", "default": 2.5, "description": "Z-score threshold for anomaly flag"},
                    "timestamps": {"type": "array", "items": {"type": "string"}, "description": "Optional timestamps"},
                    "labels": {"type": "array", "items": {"type": "string"}, "description": "Optional labels"}
                },
                "required": []
            },
            capabilities=["anomaly_detection", "zscore_computation", "statistical_analysis"],
            handler=compute_zscore_handler
        ))

        self.register(ToolDefinition(
            name="check_threshold",
            description="Checks metric values against warning and critical thresholds and generates alert statuses.",
            parameters={
                "type": "object",
                "properties": {
                    "metrics": {"type": "object", "description": "Dictionary of metric names to current values"},
                    "thresholds": {"type": "object", "description": "Mapping of metric names to warning/critical thresholds"},
                    "operator": {"type": "string", "default": ">", "description": "Comparison operator (> , >=, <, <=)"}
                },
                "required": []
            },
            capabilities=["threshold_monitoring", "metric_alerting", "system_health"],
            handler=check_threshold_handler
        ))

        self.register(ToolDefinition(
            name="extract_error_logs",
            description="Parses server log streams to isolate warning/error/critical events and diagnose root cause.",
            parameters={
                "type": "object",
                "properties": {
                    "logs": {"description": "Log lines or multiline log text to inspect"},
                    "min_level": {"type": "string", "default": "WARN", "description": "Minimum severity level"},
                    "service_filter": {"type": "string", "description": "Filter by service name"}
                },
                "required": []
            },
            capabilities=["log_parsing", "error_extraction", "root_cause_analysis"],
            handler=extract_error_logs_handler
        ))

    def register_research_tools(self) -> None:
        """Register research synthesis and metric extraction tools into this registry."""
        self.register(ToolDefinition(
            name="extract_entities",
            description="Extracts models, datasets, metrics, organizations, and methods from research documents.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"description": "Document text, list of passages, or dictionary of documents"},
                    "entity_types": {"type": "array", "items": {"type": "string"}, "description": "Entity classes to extract"}
                },
                "required": []
            },
            capabilities=["entity_extraction", "information_extraction", "nlp_analysis"],
            handler=extract_entities_handler
        ))

        self.register(ToolDefinition(
            name="compare_metrics",
            description="Compares quantitative performance metrics across multiple papers, models, or evaluations.",
            parameters={
                "type": "object",
                "properties": {
                    "sources": {"type": "object", "description": "Nested dict of source name to metric dictionary"},
                    "baseline": {"type": "string", "description": "Baseline source name for relative delta calculation"},
                    "metrics": {"type": "array", "items": {"type": "string"}, "description": "Subset of metrics to compare"},
                    "higher_is_better": {"type": "object", "description": "Dict indicating if higher is better per metric"}
                },
                "required": []
            },
            capabilities=["metric_comparison", "benchmarking", "cross_referencing"],
            handler=compare_metrics_handler
        ))

        self.register(ToolDefinition(
            name="summarize_text",
            description="Synthesizes findings across multiple research sources into structured summaries and key points.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"description": "Text, list, or multi-document payload to summarize"},
                    "focus_topics": {"type": "array", "items": {"type": "string"}, "description": "Target topics to focus summary on"},
                    "max_key_points": {"type": "integer", "default": 5, "description": "Maximum key points to extract"},
                    "style": {"type": "string", "default": "executive", "description": "Summary format style"}
                },
                "required": []
            },
            capabilities=["summarization", "research_synthesis", "document_processing"],
            handler=summarize_text_handler
        ))

    @classmethod
    def create_anomaly_default(cls) -> ToolRegistry:
        """Create a registry loaded with analytical and system anomaly detection tools."""
        registry = cls.create_default()
        registry.register_anomaly_tools()
        return registry

    @classmethod
    def create_research_default(cls) -> ToolRegistry:
        """Create a registry loaded with analytical and research synthesis tools."""
        registry = cls.create_default()
        registry.register_research_tools()
        return registry

    @classmethod
    def create_multi_domain_default(cls) -> ToolRegistry:
        """Create a unified registry loaded with tools across all domains (reconciliation, anomaly, research)."""
        registry = cls.create_reconciliation_default()
        registry.register_anomaly_tools()
        registry.register_research_tools()
        return registry

