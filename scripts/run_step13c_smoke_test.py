"""Step 13C: Single-Case Real TensorMux Smoke Test.

Demonstrates:
- V0 vs V1 execution on case REC-OPT-08 (Wrong Vendor scenario)
- Model-driven tool execution flow through ModelGateway
- Tool argument control by model
- Detailed latency breakdown:
    * Model Request 1 latency
    * Tool execution latency
    * Model Request 2 latency
    * Other node latency
    * Total graph latency
- Call count & token / cost accounting
- Truthful reporting of behavioral divergence or lack thereof
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

from reco.config import get_settings
from reco.llm.tensormux import TensorMuxGateway
from reco.engine.runtime import AgentGraphRuntime
from reco.engine.models import GraphDefinition, NodeModel
from reco.engine.state import ExecutionState
from reco.benchmarks.reconciliation.baseline import create_reconciliation_baseline_graph
from reco.benchmarks.reconciliation.dataset import get_case_by_code
from reco.benchmarks.reconciliation.evaluator import ReconciliationEvaluator
from reco.tools.executor import ToolExecutor
from reco.tools.registry import default_tool_registry

OUT_JSON_PATH = Path(r"C:\Users\toufi\.gemini\antigravity-ide\brain\7d9a276d-29fd-4456-9c5b-a153840fd462\scratch\step13c_smoke_results.json")


def _sanitize_for_report(data: Any) -> Any:
    """Recursively redact any potential secret or authorization tokens."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(s in k.lower() for s in ["key", "token", "secret", "auth", "credential", "password"]):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = _sanitize_for_report(v)
        return sanitized
    elif isinstance(data, list):
        return [_sanitize_for_report(x) for x in data]
    return data


def extract_latency_telemetry(state: ExecutionState, total_graph_lat: int) -> Dict[str, Any]:
    """Extract comprehensive latency and call count telemetry from state history."""
    nodes_breakdown = {}
    total_model_lat = 0
    total_tool_lat = 0
    total_model_calls = 0
    total_tool_calls = 0

    for step in state.step_history:
        nid = step.get("node_id")
        dur = step.get("duration_ms", 0)
        meta = step.get("metadata", {})
        m_lat = meta.get("model_latency_ms", 0)
        t_lat = meta.get("tool_latency_ms", 0)
        m_calls = meta.get("model_calls", 0)
        t_calls = meta.get("tool_calls", 0)
        rounds = meta.get("round_breakdown", [])

        total_model_lat += m_lat
        total_tool_lat += t_lat
        total_model_calls += m_calls
        total_tool_calls += t_calls

        nodes_breakdown[nid] = {
            "duration_ms": dur,
            "model_latency_ms": m_lat,
            "tool_latency_ms": t_lat,
            "model_calls": m_calls,
            "tool_calls": t_calls,
            "round_breakdown": rounds,
        }

    other_node_lat = sum(
        d["duration_ms"] for nid, d in nodes_breakdown.items() if nid != "fuzzy_match"
    )

    matcher_data = nodes_breakdown.get("fuzzy_match", {})
    rounds = matcher_data.get("round_breakdown", [])
    model_req1_lat = rounds[0]["model_latency_ms"] if len(rounds) > 0 else matcher_data.get("model_latency_ms", 0)
    tool_exec_lat = matcher_data.get("tool_latency_ms", 0)
    model_req2_lat = rounds[1]["model_latency_ms"] if len(rounds) > 1 else 0

    return {
        "total_graph_latency_ms": total_graph_lat,
        "total_model_latency_ms": total_model_lat,
        "total_tool_latency_ms": total_tool_lat,
        "total_model_calls": total_model_calls,
        "total_tool_calls": total_tool_calls,
        "model_request_1_latency_ms": model_req1_lat,
        "tool_execution_latency_ms": tool_exec_lat,
        "model_request_2_latency_ms": model_req2_lat,
        "other_nodes_latency_ms": other_node_lat,
        "nodes": nodes_breakdown,
    }


async def run_single_case_smoke_test():
    print("=" * 60)
    print("RECO STEP 13C: REAL TENSORMUX SINGLE-CASE SMOKE TEST")
    print("=" * 60)

    # 1. Verify environment configuration safely
    settings = get_settings()
    has_api_key = bool(settings.tensormux_api_key and settings.tensormux_api_key.strip())
    print(f"Provider: {settings.llm_provider}")
    print(f"Model ID: {settings.llm_model}")
    print(f"Base URL: {settings.tensormux_base_url}")
    print(f"API Key configured: {has_api_key}")

    if not has_api_key:
        print("[ERROR] TENSORMUX_API_KEY is not configured.")
        return

    # 2. Initialize Real TensorMux Gateway & Runtime
    api_key_val = settings.tensormux_api_key
    gateway = TensorMuxGateway(
        api_key=api_key_val,
        base_url=settings.tensormux_base_url,
        default_model=settings.llm_model,
        timeout_seconds=90.0,
    )
    executor = ToolExecutor(registry=default_tool_registry)
    runtime = AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)
    evaluator = ReconciliationEvaluator()

    # 3. Load Target Case: REC-OPT-08 (Wrong Vendor: Apex Logistics vs Delta Hotel Group)
    case = get_case_by_code("REC-OPT-08")
    if not case:
        print("[ERROR] Case REC-OPT-08 not found.")
        return

    case_inputs = {
        "bank_records": case.bank_records,
        "ledger_entries": case.ledger_entries,
        "records": case.bank_records,
        "entries": case.ledger_entries,
    }

    print("\nTarget Case: REC-OPT-08")
    print(f"Description: {case.description}")
    print(f"Bank Record: {case.bank_records[0]['vendor']} - ${case.bank_records[0]['amount']}")
    print(f"Ledger Entry: {case.ledger_entries[0]['vendor']} - ${case.ledger_entries[0]['amount']}")
    print(f"Ground Truth Expected Pairs: {len(case.ground_truth.expected_pairs)} (should NOT match)")

    # -------------------------------------------------------------------------
    # PART A: RUN V0 (Baseline with generic matcher prompt)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 50)
    print("RUNNING V0 BASELINE")
    print("-" * 50)

    v0_graph = create_reconciliation_baseline_graph()
    v0_graph.nodes["parse_statement"].execution_mode = "deterministic_tool"
    v0_graph.nodes["query_ledger"].execution_mode = "deterministic_tool"
    v0_graph.nodes["fuzzy_match"].execution_mode = "model_driven"
    v0_graph.nodes["verify_summary"].execution_mode = "model_inference"

    t0_start = time.perf_counter()
    v0_state = await runtime.run(
        graph=v0_graph,
        inputs=case_inputs,
        goal="Reconcile bank records against general ledger entries for scenario REC-OPT-08",
    )
    v0_total_graph_lat = int((time.perf_counter() - t0_start) * 1000)
    v0_eval = evaluator.evaluate_case(case, v0_state)
    v0_telemetry = extract_latency_telemetry(v0_state, v0_total_graph_lat)

    v0_matcher_events = [e for e in v0_state.tool_events if e["node_id"] == "fuzzy_match"]
    v0_matcher_out = v0_state.node_outputs.get("reconciliation_summary", {})

    print(f"V0 Graph Status: {v0_state.status}")
    print(f"V0 Evaluator Accuracy: {v0_eval.accuracy_score * 100:.1f}%")
    print(f"V0 Evaluator Success: {v0_eval.success}")
    print(f"V0 Total Graph Latency: {v0_total_graph_lat} ms")
    print(f"V0 Model Req 1 Latency: {v0_telemetry['model_request_1_latency_ms']} ms")
    print(f"V0 Tool Exec Latency: {v0_telemetry['tool_execution_latency_ms']} ms")
    print(f"V0 Model Req 2 Latency: {v0_telemetry['model_request_2_latency_ms']} ms")
    print(f"V0 Other Nodes Latency: {v0_telemetry['other_nodes_latency_ms']} ms")
    print(f"V0 Model Calls: {v0_telemetry['total_model_calls']}, Tool Calls: {v0_telemetry['total_tool_calls']}")
    print(f"V0 Tokens In: {v0_state.tokens_input}, Tokens Out: {v0_state.tokens_output}")
    print(f"V0 Cost: ${v0_state.cost_usd:.6f}")

    v0_tool_args = v0_matcher_events[0]["arguments"] if v0_matcher_events else {}
    print(f"V0 Tool Calls in Matcher: {len(v0_matcher_events)}")
    print(f"V0 Tool Arguments (require_vendor_match): {v0_tool_args.get('require_vendor_match', False)}")
    print(f"V0 Tool Arguments (vendor_similarity_threshold): {v0_tool_args.get('vendor_similarity_threshold', 'default')}")
    print(f"V0 Matched Pairs: {len(v0_matcher_out.get('matched_pairs', []))}")

    # -------------------------------------------------------------------------
    # PART B: RUN V1 (Mutated Prompt: Prioritize Vendor Identity)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 50)
    print("RUNNING V1 MUTATED PROMPT")
    print("-" * 50)

    v1_graph = create_reconciliation_baseline_graph()
    v1_graph.nodes["parse_statement"].execution_mode = "deterministic_tool"
    v1_graph.nodes["query_ledger"].execution_mode = "deterministic_tool"
    v1_graph.nodes["fuzzy_match"].execution_mode = "model_driven"
    v1_graph.nodes["verify_summary"].execution_mode = "model_inference"

    v1_prompt = (
        "Match bank transactions against general ledger entries and identify discrepancies. "
        "CRITICAL INSTRUCTION: Prioritize vendor/counterparty identity over monetary amount similarity. "
        "You MUST invoke the fuzzy_match_transactions tool with require_vendor_match=True and "
        "vendor_similarity_threshold=0.85 so that transactions with conflicting vendor names "
        "(such as Apex Logistics vs Delta Hotel Group) are strictly rejected as false pairings."
    )
    v1_graph.nodes["fuzzy_match"].system_prompt = v1_prompt

    t1_start = time.perf_counter()
    v1_state = await runtime.run(
        graph=v1_graph,
        inputs=case_inputs,
        goal="Reconcile bank records against general ledger entries for scenario REC-OPT-08",
    )
    v1_total_graph_lat = int((time.perf_counter() - t1_start) * 1000)
    v1_eval = evaluator.evaluate_case(case, v1_state)
    v1_telemetry = extract_latency_telemetry(v1_state, v1_total_graph_lat)

    v1_matcher_events = [e for e in v1_state.tool_events if e["node_id"] == "fuzzy_match"]
    v1_matcher_out = v1_state.node_outputs.get("reconciliation_summary", {})

    print(f"V1 Graph Status: {v1_state.status}")
    print(f"V1 Evaluator Accuracy: {v1_eval.accuracy_score * 100:.1f}%")
    print(f"V1 Evaluator Success: {v1_eval.success}")
    print(f"V1 Total Graph Latency: {v1_total_graph_lat} ms")
    print(f"V1 Model Req 1 Latency: {v1_telemetry['model_request_1_latency_ms']} ms")
    print(f"V1 Tool Exec Latency: {v1_telemetry['tool_execution_latency_ms']} ms")
    print(f"V1 Model Req 2 Latency: {v1_telemetry['model_request_2_latency_ms']} ms")
    print(f"V1 Other Nodes Latency: {v1_telemetry['other_nodes_latency_ms']} ms")
    print(f"V1 Model Calls: {v1_telemetry['total_model_calls']}, Tool Calls: {v1_telemetry['total_tool_calls']}")
    print(f"V1 Tokens In: {v1_state.tokens_input}, Tokens Out: {v1_state.tokens_output}")
    print(f"V1 Cost: ${v1_state.cost_usd:.6f}")

    v1_tool_args = v1_matcher_events[0]["arguments"] if v1_matcher_events else {}
    print(f"V1 Tool Calls in Matcher: {len(v1_matcher_events)}")
    print(f"V1 Tool Arguments (require_vendor_match): {v1_tool_args.get('require_vendor_match', False)}")
    print(f"V1 Tool Arguments (vendor_similarity_threshold): {v1_tool_args.get('vendor_similarity_threshold', 'default')}")
    print(f"V1 Matched Pairs: {len(v1_matcher_out.get('matched_pairs', []))}")

    # -------------------------------------------------------------------------
    # PART C: COMPILE COMPARISON EVIDENCE
    # -------------------------------------------------------------------------
    comparison = {
        "case_code": "REC-OPT-08",
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "v0": {
            "prompt": v0_graph.nodes["fuzzy_match"].system_prompt,
            "accuracy": v0_eval.accuracy_score,
            "success": v0_eval.success,
            "latency_ms": v0_total_graph_lat,
            "tokens_in": v0_state.tokens_input,
            "tokens_out": v0_state.tokens_output,
            "cost_usd": v0_state.cost_usd,
            "tool_calls": len(v0_matcher_events),
            "tool_arguments": _sanitize_for_report(v0_tool_args),
            "matched_pairs_count": len(v0_matcher_out.get("matched_pairs", [])),
            "unmatched_bank_ids": v0_matcher_out.get("unmatched_bank_ids", []),
            "unmatched_ledger_ids": v0_matcher_out.get("unmatched_ledger_ids", []),
            "detected_exceptions": v0_matcher_out.get("exceptions_by_type", {}),
            "telemetry": v0_telemetry,
        },
        "v1": {
            "prompt": v1_graph.nodes["fuzzy_match"].system_prompt,
            "accuracy": v1_eval.accuracy_score,
            "success": v1_eval.success,
            "latency_ms": v1_total_graph_lat,
            "tokens_in": v1_state.tokens_input,
            "tokens_out": v1_state.tokens_output,
            "cost_usd": v1_state.cost_usd,
            "tool_calls": len(v1_matcher_events),
            "tool_arguments": _sanitize_for_report(v1_tool_args),
            "matched_pairs_count": len(v1_matcher_out.get("matched_pairs", [])),
            "unmatched_bank_ids": v1_matcher_out.get("unmatched_bank_ids", []),
            "unmatched_ledger_ids": v1_matcher_out.get("unmatched_ledger_ids", []),
            "detected_exceptions": v1_matcher_out.get("exceptions_by_type", {}),
            "telemetry": v1_telemetry,
        },
        "behavioral_change": {
            "accuracy_delta": round(v1_eval.accuracy_score - v0_eval.accuracy_score, 4),
            "arguments_diverged": (
                v0_tool_args.get("require_vendor_match") != v1_tool_args.get("require_vendor_match")
                or v0_tool_args.get("vendor_similarity_threshold") != v1_tool_args.get("vendor_similarity_threshold")
            ),
            "behavior_diverged": (
                len(v0_matcher_out.get("matched_pairs", [])) != len(v1_matcher_out.get("matched_pairs", []))
            ),
        }
    }

    OUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, default=str)

    print("\n" + "=" * 60)
    print("STEP 13C EVIDENCE SUMMARY")
    print("=" * 60)
    print(f"V0 Accuracy: {comparison['v0']['accuracy'] * 100:.1f}% -> V1 Accuracy: {comparison['v1']['accuracy'] * 100:.1f}%")
    print(f"Tool Arguments Diverged: {comparison['behavioral_change']['arguments_diverged']}")
    print(f"Matching Behavior Diverged: {comparison['behavioral_change']['behavior_diverged']}")
    print(f"Results saved to: {OUT_JSON_PATH}")


if __name__ == "__main__":
    asyncio.run(run_single_case_smoke_test())
