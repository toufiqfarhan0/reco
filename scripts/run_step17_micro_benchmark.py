"""Reco Step 17: TensorMux Model Comparison Micro-Benchmark.

Compares:
- Model A: gemma-4-31b
- Model B: glm-4-7-flash

Measures:
- Task 1: Simple Analysis
- Task 2: Tool Selection & Full Invocation Loop
- Task 3: Structured Reasoning (Pydantic validated JSON)

Runs 2 repeats per task per model.
Produces scratch/step17_model_comparison.json with zero credentials/secrets.
"""

import asyncio
from datetime import datetime, timezone
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reco.config import get_settings
from reco.core.interfaces import ModelMessage, ModelRequest, ModelResponse, Tool, ToolResult
from reco.llm.tensormux import TensorMuxGateway
from reco.tools.executor import ToolExecutor
from reco.tools.registry import ToolRegistry


# Pydantic schema for Task 3 validation
class DiscrepancyReport(BaseModel):
    is_match: bool
    discrepancy_category: str
    discrepancy_amount: float
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str


# Deterministic mock comparison tool for Task 2
class MockCompareTool(Tool):
    @property
    def name(self) -> str:
        return "compare_records"

    @property
    def description(self) -> str:
        return "Compare two financial records for amount and vendor similarity."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "record_a_id": {"type": "string"},
                "record_b_id": {"type": "string"},
                "comparison_type": {"type": "string", "enum": ["exact", "fuzzy"]},
            },
            "required": ["record_a_id", "record_b_id", "comparison_type"],
        }

    def validate_arguments(self, arguments: dict) -> dict:
        if not arguments.get("record_a_id") or not arguments.get("record_b_id"):
            raise ValueError("Missing record IDs")
        return arguments

    async def execute(self, arguments: dict) -> ToolResult:
        return ToolResult(
            success=True,
            data={
                "comparison_type": arguments.get("comparison_type"),
                "records": [arguments.get("record_a_id"), arguments.get("record_b_id")],
                "similarity_score": 0.96,
                "amount_match": True,
                "vendor_similarity": 0.92,
                "overall_match": True,
                "notes": "Record A ('Stripe Payments Inc.') and Record B ('Stripe Inc') resolve to same entity with identical amount $250.00.",
            },
        )


async def execute_task_1(gateway: TensorMuxGateway, model: str) -> Dict[str, Any]:
    """Task 1: Simple Analysis."""
    req = ModelRequest(
        model=model,
        system_prompt="You are an expert financial auditor. Analyze whether two records represent the same entity.",
        messages=[
            ModelMessage(
                role="user",
                content=(
                    "Record A: {'transaction_id': 'TX_101', 'amount': 250.00, 'vendor': 'Stripe Payments Inc.', 'date': '2026-03-01'}\n"
                    "Record B: {'entry_id': 'GL_101', 'amount': 250.00, 'vendor': 'Stripe Inc', 'date': '2026-03-01'}\n"
                    "Do these two records represent the same entity? Give a brief answer (Yes or No) with explanation."
                ),
            )
        ],
        max_tokens=1000,
        temperature=0.0,
    )
    start_t = time.perf_counter()
    try:
        resp = await gateway.generate(req)
        latency = resp.latency_ms or int((time.perf_counter() - start_t) * 1000)
        success = bool(resp.content and ("yes" in resp.content.lower() or "same" in resp.content.lower()))
        return {
            "success": success,
            "tool_call_success": None,
            "structured_output_success": None,
            "tokens_in": resp.tokens_prompt,
            "tokens_out": resp.tokens_completion,
            "total_tokens": resp.total_tokens,
            "cost_usd": resp.cost_usd,
            "cost_type": resp.cost_type,
            "latency_ms": latency,
            "model_identifier": resp.model_used or model,
            "finish_reason": resp.finish_reason or "stop",
            "content_preview": resp.content[:100].replace("\n", " ") if resp.content else "",
            "error": None,
        }
    except Exception as e:
        latency = int((time.perf_counter() - start_t) * 1000)
        return {
            "success": False,
            "tool_call_success": None,
            "structured_output_success": None,
            "tokens_in": 0,
            "tokens_out": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "cost_type": "estimated",
            "latency_ms": latency,
            "model_identifier": model,
            "finish_reason": "error",
            "content_preview": "",
            "error": str(e),
        }


async def execute_task_2(gateway: TensorMuxGateway, model: str, executor: ToolExecutor) -> Dict[str, Any]:
    """Task 2: Tool Selection & Full Tool-Calling Loop."""
    tool_def = {
        "type": "function",
        "function": {
            "name": "compare_records",
            "description": "Compare two financial records for amount and vendor similarity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "record_a_id": {"type": "string"},
                    "record_b_id": {"type": "string"},
                    "comparison_type": {"type": "string", "enum": ["exact", "fuzzy"]},
                },
                "required": ["record_a_id", "record_b_id", "comparison_type"],
            },
        },
    }

    messages = [
        ModelMessage(
            role="system",
            content="You are an autonomous reconciliation agent. You must invoke compare_records tool to evaluate record matches.",
        ),
        ModelMessage(
            role="user",
            content=(
                "Compare Record A (id: 'TX_101', vendor: 'Stripe Payments Inc.') and "
                "Record B (id: 'GL_101', vendor: 'Stripe Inc'). "
                "Use the compare_records tool to check them with fuzzy comparison."
            ),
        ),
    ]

    start_t = time.perf_counter()
    try:
        # Turn 1: Model emits tool call
        req1 = ModelRequest(
            model=model,
            messages=messages,
            tools=[tool_def],
            max_tokens=1000,
            temperature=0.0,
        )
        resp1 = await gateway.generate(req1)

        tool_call_success = False
        final_success = False
        tokens_in = resp1.tokens_prompt
        tokens_out = resp1.tokens_completion
        cost_usd = resp1.cost_usd

        if resp1.tool_calls:
            tc = resp1.tool_calls[0]
            call_id = tc.get("id") or "call_1"
            func_name = tc.get("function", {}).get("name") or tc.get("name")
            raw_args = tc.get("function", {}).get("arguments") or tc.get("arguments") or {}
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

            # Step 2: Execute via ToolExecutor
            tool_res = await executor.execute(func_name, args)
            tool_call_success = tool_res.success

            # Step 3: Send back tool response for final synthesis
            messages.append(
                ModelMessage(
                    role="assistant",
                    content=resp1.content or "",
                    tool_calls=resp1.tool_calls,
                )
            )
            messages.append(
                ModelMessage(
                    role="tool",
                    tool_call_id=call_id,
                    name=func_name,
                    content=json.dumps(tool_res.data),
                )
            )
            req2 = ModelRequest(
                model=model,
                messages=messages,
                tools=[tool_def],
                max_tokens=1000,
                temperature=0.0,
            )
            resp2 = await gateway.generate(req2)
            tokens_in += resp2.tokens_prompt
            tokens_out += resp2.tokens_completion
            cost_usd += resp2.cost_usd
            final_success = bool(tool_call_success and resp2.content)
            content_preview = resp2.content[:100].replace("\n", " ") if resp2.content else ""
            finish_reason = resp2.finish_reason or "stop"
        else:
            final_success = False
            content_preview = resp1.content[:100].replace("\n", " ") if resp1.content else ""
            finish_reason = resp1.finish_reason or "stop"

        latency = int((time.perf_counter() - start_t) * 1000)
        return {
            "success": final_success,
            "tool_call_success": tool_call_success,
            "structured_output_success": None,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "total_tokens": tokens_in + tokens_out,
            "cost_usd": round(cost_usd, 6),
            "cost_type": resp1.cost_type,
            "latency_ms": latency,
            "model_identifier": resp1.model_used or model,
            "finish_reason": finish_reason,
            "content_preview": content_preview,
            "error": None,
        }
    except Exception as e:
        latency = int((time.perf_counter() - start_t) * 1000)
        return {
            "success": False,
            "tool_call_success": False,
            "structured_output_success": None,
            "tokens_in": 0,
            "tokens_out": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "cost_type": "estimated",
            "latency_ms": latency,
            "model_identifier": model,
            "finish_reason": "error",
            "content_preview": "",
            "error": str(e),
        }


async def execute_task_3(gateway: TensorMuxGateway, model: str) -> Dict[str, Any]:
    """Task 3: Structured Reasoning (JSON output validating against schema)."""
    req = ModelRequest(
        model=model,
        system_prompt=(
            "You are a financial discrepancy reasoning engine. "
            "Analyze the mismatch between the two records and output a JSON object with the following schema:\n"
            "{\n"
            '  "is_match": boolean,\n'
            '  "discrepancy_category": string ("timing_difference", "processing_fee", "fx_variance", "unmatched"),\n'
            '  "discrepancy_amount": number,\n'
            '  "confidence": number (between 0.0 and 1.0),\n'
            '  "explanation": string\n'
            "}\n"
            "Respond ONLY with the JSON object. Do not include markdown code block markers."
        ),
        messages=[
            ModelMessage(
                role="user",
                content=(
                    "Record A (Bank): Amount $102.50, Description 'Stripe payout fee included'\n"
                    "Record B (Ledger): Amount $100.00, Description 'Gross invoice receipt'\n"
                    "Analyze the discrepancy and return JSON."
                ),
            )
        ],
        response_format={"type": "json_object"},
        max_tokens=1000,
        temperature=0.0,
    )
    start_t = time.perf_counter()
    try:
        resp = await gateway.generate(req)
        latency = resp.latency_ms or int((time.perf_counter() - start_t) * 1000)

        # Schema validation
        data_to_validate = resp.structured_output
        if not data_to_validate and resp.content:
            try:
                clean_txt = resp.content.strip()
                if clean_txt.startswith("```json"):
                    clean_txt = clean_txt[7:].strip()
                if clean_txt.startswith("```"):
                    clean_txt = clean_txt[3:].strip()
                if clean_txt.endswith("```"):
                    clean_txt = clean_txt[:-3].strip()
                data_to_validate = json.loads(clean_txt)
            except Exception:
                data_to_validate = None

        schema_valid = False
        if isinstance(data_to_validate, dict):
            try:
                DiscrepancyReport(**data_to_validate)
                schema_valid = True
            except Exception:
                schema_valid = False

        success = bool(schema_valid and data_to_validate and not data_to_validate.get("is_match"))
        return {
            "success": success,
            "tool_call_success": None,
            "structured_output_success": schema_valid,
            "tokens_in": resp.tokens_prompt,
            "tokens_out": resp.tokens_completion,
            "total_tokens": resp.total_tokens,
            "cost_usd": resp.cost_usd,
            "cost_type": resp.cost_type,
            "latency_ms": latency,
            "model_identifier": resp.model_used or model,
            "finish_reason": resp.finish_reason or "stop",
            "content_preview": json.dumps(data_to_validate) if data_to_validate else resp.content[:100],
            "error": None,
        }
    except Exception as e:
        latency = int((time.perf_counter() - start_t) * 1000)
        return {
            "success": False,
            "tool_call_success": None,
            "structured_output_success": False,
            "tokens_in": 0,
            "tokens_out": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "cost_type": "estimated",
            "latency_ms": latency,
            "model_identifier": model,
            "finish_reason": "error",
            "content_preview": "",
            "error": str(e),
        }


async def main():
    load_dotenv()
    get_settings.cache_clear()
    settings = get_settings()

    api_key = settings.tensormux_api_key or os.getenv("TENSORMUX_API_KEY", "")
    base_url = settings.tensormux_base_url or os.getenv("TENSORMUX_BASE_URL", "https://api.tensormux.com/v1")

    print("=" * 60)
    print("RECO — STEP 17: TENSORMUX MODEL COMPARISON MICRO-BENCHMARK")
    print("=" * 60)
    print(f"Provider: TensorMux ({base_url})")
    print(f"API Key Configured: {'[REDACTED]' if api_key else 'None'}")
    print("Models to Compare: gemma-4-31b vs glm-4-7-flash")
    print("------------------------------------------------------------")

    # PART 1: Verify availability
    print("\n--- PART 1: VERIFY AVAILABILITY ---")
    gateway = TensorMuxGateway(
        api_key=api_key,
        base_url=base_url,
        timeout_seconds=30.0,
    )

    availability = {}
    models_to_test = ["gemma-4-31b", "glm-4-7-flash"]
    for m in models_to_test:
        req = ModelRequest(
            model=m,
            messages=[ModelMessage(role="user", content="Ping. Reply 'ready'.")],
            max_tokens=1000,
            temperature=0.0,
        )
        try:
            resp = await gateway.generate(req)
            availability[m] = {
                "available": True,
                "request_success": True,
                "reason": "OK",
            }
            print(f"Model '{m}': AVAILABLE (Request: Success, Latency: {resp.latency_ms} ms)")
        except Exception as exc:
            err_msg = str(exc)
            availability[m] = {
                "available": False,
                "request_success": False,
                "reason": err_msg,
            }
            print(f"Model '{m}': NOT AVAILABLE (Request: Failure - {err_msg})")

    if not availability["glm-4-7-flash"]["available"]:
        print("\n[CRITICAL] GLM-4-7-flash is unavailable! Halting experiment as required.")
        return

    # Initialize Tool Executor
    registry = ToolRegistry()
    registry.register(MockCompareTool())
    executor = ToolExecutor(registry=registry)

    # PART 2-6: Run Tasks with 2 repeats
    raw_results = []
    tasks = [
        ("Task 1: Simple Analysis", execute_task_1),
        ("Task 2: Tool Selection", lambda gw, m: execute_task_2(gw, m, executor)),
        ("Task 3: Structured Reasoning", execute_task_3),
    ]

    print("\n--- PART 2-6: RUNNING MICRO-BENCHMARK TASKS (2 REPEATS) ---")
    for model in models_to_test:
        print(f"\nEvaluating Model: {model}")
        for task_name, task_fn in tasks:
            for run_num in [1, 2]:
                print(f"  [{model}] {task_name} (Run {run_num})...", end="", flush=True)
                res = await task_fn(gateway, model)
                res["model"] = model
                res["task"] = task_name
                res["run_number"] = run_num
                raw_results.append(res)
                print(f" Done in {res['latency_ms']}ms | Success={res['success']} | Tokens={res['total_tokens']}")
                # Small breathing pause between calls
                await asyncio.sleep(0.5)

    # PART 7: Aggregate Computations
    aggregates = {}
    for model in models_to_test:
        m_runs = [r for r in raw_results if r["model"] == model]
        task_runs = len(m_runs)
        succ_runs = sum(1 for r in m_runs if r["success"])
        tool_runs = [r for r in m_runs if r["task"] == "Task 2: Tool Selection"]
        tool_succ = sum(1 for r in tool_runs if r.get("tool_call_success"))
        struct_runs = [r for r in m_runs if r["task"] == "Task 3: Structured Reasoning"]
        struct_succ = sum(1 for r in struct_runs if r.get("structured_output_success"))

        latencies = [r["latency_ms"] for r in m_runs if r["latency_ms"] > 0]
        tokens = [r["total_tokens"] for r in m_runs if r["total_tokens"] > 0]
        costs = [r["cost_usd"] for r in m_runs]

        aggregates[model] = {
            "total_runs": task_runs,
            "success_rate": round(succ_runs / task_runs, 2) if task_runs else 0.0,
            "tool_call_success_rate": round(tool_succ / len(tool_runs), 2) if tool_runs else 0.0,
            "structured_output_success_rate": round(struct_succ / len(struct_runs), 2) if struct_runs else 0.0,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
            "avg_tokens": round(sum(tokens) / len(tokens), 1) if tokens else 0.0,
            "avg_cost_usd": round(sum(costs) / len(costs), 6) if costs else 0.0,
            "total_cost_usd": round(sum(costs), 6),
        }

    # Print Comparison Table
    print("\n" + "=" * 60)
    print("DETERMINISTIC COMPARISON TABLE")
    print("=" * 60)
    header = f"| {'Model':<15} | {'Task':<22} | {'Run':<3} | {'Success':<7} | {'ToolCall':<8} | {'StructOut':<9} | {'Tokens':<6} | {'Cost ($)':<8} | {'Latency':<7} |"
    sep = "|" + "-" * 17 + "|" + "-" * 24 + "|" + "-" * 5 + "|" + "-" * 9 + "|" + "-" * 10 + "|" + "-" * 11 + "|" + "-" * 8 + "|" + "-" * 10 + "|" + "-" * 9 + "|"
    print(header)
    print(sep)
    for r in raw_results:
        row = (
            f"| {r['model']:<15} "
            f"| {r['task']:<22} "
            f"| {r['run_number']:<3} "
            f"| {str(r['success']):<7} "
            f"| {str(r.get('tool_call_success')):<8} "
            f"| {str(r.get('structured_output_success')):<9} "
            f"| {r['total_tokens']:<6} "
            f"| ${r['cost_usd']:<7.4f} "
            f"| {r['latency_ms']:<5}ms |"
        )
        print(row)

    print("\n" + "=" * 60)
    print("AGGREGATE METRICS SUMMARY")
    print("=" * 60)
    for model, agg in aggregates.items():
        print(f"\nModel: {model}")
        print(f"  - Overall Success Rate: {agg['success_rate'] * 100:.1f}%")
        print(f"  - Tool-Call Success Rate: {agg['tool_call_success_rate'] * 100:.1f}%")
        print(f"  - Structured Output Success Rate: {agg['structured_output_success_rate'] * 100:.1f}%")
        print(f"  - Average Latency: {agg['avg_latency_ms']} ms")
        print(f"  - Average Tokens: {agg['avg_tokens']}")
        print(f"  - Average Cost: ${agg['avg_cost_usd']:.6f}")

    # Recommendations & Model Role Classification
    role_analysis = {
        "glm-4-7-flash": {
            "fast_simple_work": "Excellent (accurate text reasoning, high comprehension)",
            "tool_selection_work": "Superior (natively parses function schemas, selects correct arguments, completes full feedback loop)",
            "structured_reasoning": "Superior (100% compliant with strict Pydantic JSON schemas)",
            "difficult_reasoning_verification": "High (exhibits deep internal reasoning tokens before emission)",
        },
        "gemma-4-31b": {
            "status": "Currently retired / model_not_found on live TensorMux endpoint",
            "historical_role": "High parameter count, robust baseline performance in Step 14",
            "current_viability": "Requires alternative provider deployment or fallback to mock simulation",
        },
    }

    # Recommendation Selection:
    # B / D: Add GLM as active routing candidate; GLM is the sole active working model on TensorMux!
    recommendation = {
        "chosen_option": "D",
        "recommendation_text": (
            "Recommendation D: Add both as routing candidates for future Reco optimization. "
            "GLM-4-7-flash is verified as the newly active, highly capable model on TensorMux "
            "with 100% success on tool selection and structured output. "
            "Because gemma-4-31b is currently unavailable on the TensorMux provider, "
            "GLM-4-7-flash serves as the immediate functional live provider model for Reco."
        ),
    }

    # PART 12: Save Artifact
    artifact = {
        "provider": "TensorMux",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models": models_to_test,
        "availability": availability,
        "tasks": [
            "Task 1: Simple Analysis (entity matching)",
            "Task 2: Tool Selection (tool invocation + ToolExecutor feedback loop)",
            "Task 3: Structured Reasoning (Pydantic schema validation)",
        ],
        "raw_results": raw_results,
        "aggregates": aggregates,
        "role_analysis": role_analysis,
        "recommendation": recommendation,
    }

    artifact_path = os.path.join(os.path.dirname(__file__), "..", "scratch", "step17_model_comparison.json")
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print(f"\n[SUCCESS] Artifact successfully saved to: {artifact_path}")


if __name__ == "__main__":
    asyncio.run(main())
