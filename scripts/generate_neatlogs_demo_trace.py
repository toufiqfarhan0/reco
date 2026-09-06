"""Generate comprehensive end-to-end Neatlogs demo trace artifact.

Emits full Reco hierarchical trace covering:
- optimization_run
  ├── generation_0 (baseline evaluation)
  │   ├── benchmark_run.optimization
  │   │   ├── benchmark_case.REC-OPT-01
  │   │   │   ├── node_execution.load_transactions
  │   │   │   │   └── tool_invocation.parse_bank_statement
  │   │   │   ├── node_execution.reconcile
  │   │   │   │   ├── model_invocation
  │   │   │   │   └── tool_invocation.match_exact_amounts
  │   │   │   └── node_execution.generate_report
  │   │   └── benchmark_case.REC-OPT-02 (failure case)
  ├── generation_1 (autonomous optimization cycle)
  │   ├── failure_diagnosis (Root cause taxonomy)
  │   ├── candidate_mutation (Prompt hash mutation)
  │   ├── candidate_benchmark.cand_v1
  │   │   └── benchmark_run.optimization
  │   │       └── benchmark_case.REC-OPT-02 (now passing)
  │   └── promotion_gate
  │       ├── benchmark_run.held_out (isolated test split)
  │       │   └── benchmark_case.REC-HLD-01 (held-out privacy protected)
  │       └── promotion_assessed (delta metrics verified)

Exports scratch/neatlogs_trace_demo.json and sends structured trace to Neatlogs HTTP ingestion.
"""

import hashlib
import json
import os
import sys
import time
from uuid import uuid4

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reco.config import get_settings
from reco.observability.tracer import NeatlogsTracer, set_global_tracer


def generate_demo_trace() -> int:
    load_dotenv()
    get_settings.cache_clear()
    settings = get_settings()

    api_key = settings.neatlogs_api_key or os.getenv("NEATLOGS_API_KEY", "")
    base_url = settings.neatlogs_base_url or os.getenv("NEATLOGS_BASE_URL", "")

    print("==================================================")
    print("RECO — STEP 16: NEATLOGS FULL WORKFLOW TRACE")
    print("==================================================")
    print(f"Project: reco")
    print(f"Track: Track 1 — Automated Agent Engineering")
    print(f"API Key Configured: {'[REDACTED]' if api_key else 'None'}")
    print("--------------------------------------------------")

    tracer = NeatlogsTracer(
        api_key=api_key or "demo_mock_key",
        base_url=base_url,
        enabled=True,
        timeout_seconds=5.0,
        service_name="reco",
    )
    set_global_tracer(tracer)

    exp_id = str(uuid4())
    v0_id = str(uuid4())
    v1_id = str(uuid4())

    print(f"Experiment ID: {exp_id}")
    print(f"V0 Initial Version: {v0_id}")
    print(f"V1 Candidate Version: {v1_id}")
    print("Recording hierarchical workflow spans...")

    # Root: optimization_run
    with tracer.start_span("optimization_run", attributes={
        "experiment_id": exp_id,
        "track": "Automated Agent Engineering",
        "strategy": "failure_driven",
        "benchmark_dataset": "reconciliation",
        "max_generations": 1,
        "reco.experiment_id": exp_id,
        "reco.total_generations": 1,
        "reco.final_accuracy": 0.95,
        "reco.baseline_accuracy": 0.80,
        "reco.accuracy_lift_pct": 18.75,
    }):
        # Generation 0: Baseline Evaluation
        with tracer.start_span("generation_0", attributes={
            "experiment_id": exp_id,
            "generation_number": 0,
            "parent_version_id": v0_id,
        }):
            with tracer.start_span("baseline_benchmark", attributes={"version_id": v0_id}):
                with tracer.start_span("benchmark_run.optimization", attributes={"split": "optimization"}):
                    # Case 1: Simple match (passes)
                    with tracer.trace_benchmark_case(
                        case_code="REC-OPT-01",
                        split="optimization",
                        experiment_id=exp_id,
                        agent_version_id=v0_id,
                    ):
                        with tracer.trace_node_execution("load_transactions", execution_mode="deterministic_tool"):
                            with tracer.trace_tool_invocation("parse_bank_statement", duration_ms=12, success=True):
                                pass
                        with tracer.trace_node_execution("reconcile", execution_mode="model_driven"):
                            with tracer.trace_model_invocation(
                                model_name="mock-agent-v1",
                                tokens_in=150,
                                tokens_out=45,
                                latency_ms=250,
                                cost_usd=0.00045,
                            ):
                                pass
                            with tracer.trace_tool_invocation("match_exact_amounts", duration_ms=8, success=True):
                                pass
                        with tracer.trace_node_execution("generate_report", execution_mode="deterministic_tool"):
                            pass

                    # Case 2: Timing difference (fails in V0)
                    with tracer.trace_benchmark_case(
                        case_code="REC-OPT-02",
                        split="optimization",
                        experiment_id=exp_id,
                        agent_version_id=v0_id,
                    ):
                        with tracer.trace_node_execution("reconcile", execution_mode="model_driven"):
                            with tracer.trace_model_invocation(
                                model_name="mock-agent-v1",
                                tokens_in=210,
                                tokens_out=60,
                                latency_ms=310,
                                cost_usd=0.00062,
                                status="error",
                            ):
                                pass

        # Generation 1: Autonomous Diagnostics, Mutation, and Candidate Evaluation
        with tracer.start_span("generation_1", attributes={
            "experiment_id": exp_id,
            "generation_number": 1,
            "parent_version_id": v0_id,
        }):
            diag_id = str(uuid4())
            tracer.trace_failure_diagnosis(
                diagnosis_id=diag_id,
                category="TIMING_DIFFERENCE",
                severity="medium",
                failed_node="reconcile",
                confidence=0.92,
                case_code="REC-OPT-02",
                experiment_id=exp_id,
                generation_number=1,
            )

            prompt_hash = hashlib.sha256(b"Updated reconciliation prompt: tolerate 3-day window").hexdigest()[:16]
            tracer.trace_mutation(
                candidate_id=v1_id,
                parent_version_id=v0_id,
                mutation_type="SYSTEM_PROMPT",
                target="reconcile",
                prompt_hash=prompt_hash,
                change_summary="Expanded date tolerance window to 3 business days for timing differences",
                token_count_delta=28,
                experiment_id=exp_id,
                generation_number=1,
            )

            # Candidate Benchmark: Evaluation on Optimization Split
            with tracer.start_span(f"candidate_benchmark.{v1_id}", attributes={
                "candidate_id": v1_id,
                "parent_version_id": v0_id,
                "generation_number": 1,
            }) as cand_span:
                cand_span.set_attributes({
                    "eval.accuracy": 0.95,
                    "eval.reliability": 1.0,
                    "eval.cost_usd": 0.0031,
                    "eval.latency_ms": 312.0,
                    "eval.decision": "PROMOTE",
                    "eval.domain": "reconciliation",
                    "eval.generation": 1,
                    "eval.candidate_id": v1_id,
                    "reco.pareto_dominant": True,
                })
                with tracer.start_span("benchmark_run.optimization", attributes={"split": "optimization"}):
                    with tracer.trace_benchmark_case(
                        case_code="REC-OPT-02",
                        split="optimization",
                        experiment_id=exp_id,
                        agent_version_id=v1_id,
                    ):
                        with tracer.trace_node_execution("reconcile", execution_mode="model_driven"):
                            with tracer.trace_model_invocation(
                                model_name="mock-agent-v1",
                                tokens_in=238,
                                tokens_out=72,
                                latency_ms=290,
                                cost_usd=0.00071,
                                status="ok",
                            ):
                                pass
                            with tracer.trace_tool_invocation("match_exact_amounts", duration_ms=9, success=True):
                                pass

            # Promotion Gate: Isolated Held-Out Evaluation & Gate Assessment
            with tracer.start_span("promotion_gate", attributes={
                "candidate_id": v1_id,
                "parent_version_id": v0_id,
            }):
                with tracer.start_span("benchmark_run.held_out", attributes={"split": "held_out"}):
                    with tracer.trace_benchmark_case(
                        case_code="REC-HLD-01",
                        split="held_out",
                        experiment_id=exp_id,
                        agent_version_id=v1_id,
                    ):
                        with tracer.trace_node_execution("reconcile", execution_mode="model_driven"):
                            with tracer.trace_model_invocation(
                                model_name="mock-agent-v1",
                                tokens_in=195,
                                tokens_out=58,
                                latency_ms=260,
                                cost_usd=0.00058,
                                status="ok",
                            ):
                                pass


                tracer.trace_promotion(
                    experiment_id=exp_id,
                    parent_version_id=v0_id,
                    final_version_id=v1_id,
                    decision="promoted",
                    promoted=True,
                    accuracy_delta=0.15,
                    cost_delta=0.00012,
                    latency_delta=-20,
                    reliability_delta=0.08,
                    improved_dimensions=["accuracy", "reliability", "latency"],
                )

    # Export demo trace artifact
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scratch", "neatlogs_trace_demo.json"))
    tracer.export_trace_demo(output_path)
    print(f"Exported trace artifact to: {output_path}")

    # Build and display hierarchy summary
    tree = tracer.build_trace_hierarchy_from_spans("optimization_run")
    print("--------------------------------------------------")
    print(f"Total Recorded Spans: {len(tracer.recorded_spans)}")
    print(f"Root Span: {tree.get('name')} (kind: {tree.get('kind', 'WORKFLOW')})")
    print(f"Direct Child Nodes: {[c.get('name') for c in tree.get('children', [])]}")
    print("--------------------------------------------------")

    # Transmit trace to Neatlogs HTTP ingestion if API key present
    if api_key:
        print("Sending structured trace to Neatlogs HTTP endpoint (POST https://ingest.neatlogs.com/v1/trace)...")
        t0 = time.time()
        http_res = tracer.send_structured_trace(tree)
        duration_ms = int((time.time() - t0) * 1000)
        print(f"HTTP Ingestion Result: {http_res.get('status_code', 'error')}")
        print(f"Success: {http_res.get('success', False)}")
        print(f"Duration: {duration_ms} ms")
        if http_res.get("trace_id"):
            print(f"Neatlogs Trace ID: {http_res.get('trace_id')}")
        if not http_res.get("success"):
            print(f"Ingest Notice (best effort): {http_res.get('error')}")
    else:
        print("[INFO] NEATLOGS_API_KEY not configured; skipped live network transmission.")

    print("==================================================")
    print("[SUCCESS] Neatlogs full workflow trace generated successfully!")
    print("==================================================")
    return 0


if __name__ == "__main__":
    sys.exit(generate_demo_trace())
