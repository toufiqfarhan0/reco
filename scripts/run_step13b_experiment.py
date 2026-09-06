"""Step 13B: Real-Provider Autonomous Optimization Experiment Runner.

Executes:
V0 (Opt) -> V0 (Held-Out) -> Failure Analysis -> Candidate Generation -> V1 (Opt) -> Compare
-> V2 (Opt if justified) -> Final Held-Out -> Promotion Assessment -> Leakage Verification.
"""

import asyncio
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

from reco.config import get_settings
from reco.llm.tensormux import TensorMuxGateway
from reco.engine.runtime import AgentGraphRuntime
from reco.engine.models import GraphDefinition
from reco.benchmarks.reconciliation.benchmark import ReconciliationBenchmark
from reco.benchmarks.reconciliation.baseline import create_reconciliation_baseline_graph
from reco.benchmarks.reconciliation.models import CaseEvaluationResult, ReconciliationRunResult
from reco.diagnostics.analyzer import FailureAnalyzer
from reco.mutation.engine import MutationEngine
from reco.mutation.generator import CandidateGenerator
from reco.evaluators.comparison import ComparisonPolicy, compare_scorecards, assess_promotion
from reco.tools.executor import ToolExecutor
from reco.tools.registry import default_tool_registry

CACHE_FILE_PATH = Path(r"C:\Users\toufi\.gemini\antigravity-ide\brain\7d9a276d-29fd-4456-9c5b-a153840fd462\scratch\case_cache.json")
OUTPUT_JSON_PATH = Path(r"C:\Users\toufi\.gemini\antigravity-ide\brain\7d9a276d-29fd-4456-9c5b-a153840fd462\scratch\experiment_results.json")


def _compute_graph_fingerprint(graph: GraphDefinition) -> str:
    parts = []
    for nid in sorted(graph.nodes.keys()):
        n = graph.nodes[nid]
        parts.append(f"{nid}|{n.role}|{n.system_prompt}|{sorted(n.tools)}|{json.dumps(n.input_mapping, sort_keys=True)}")
    for e in sorted(graph.edges, key=lambda x: (x.source_node_id, x.target_node_id)):
        parts.append(f"{e.source_node_id}->{e.target_node_id}")
    return hashlib.sha256(";".join(parts).encode("utf-8")).hexdigest()[:16]


class CachedReconciliationBenchmark(ReconciliationBenchmark):
    """ReconciliationBenchmark with persistent per-case caching on disk.
    
    Prevents redundant calls to the real model provider and guarantees
    that if network drops or a step halts, already evaluated cases are preserved.
    """

    def __init__(self, runtime, cache_path: Path = CACHE_FILE_PATH):
        super().__init__(runtime=runtime)
        self.cache_path = cache_path
        self._cache = self._load_cache()

    def _load_cache(self) -> dict:
        if self.cache_path.exists():
            try:
                data = json.loads(self.cache_path.read_text(encoding="utf-8"))
                print(f"[Cache] Loaded {len(data)} cached case results from {self.cache_path.name}")
                return data
            except Exception as e:
                print(f"[Cache] Warning loading cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")

    async def run_benchmark(
        self,
        graph: GraphDefinition,
        split: str = "optimization",
        experiment_id = None,
        agent_version_id = None,
        persist: bool = False,
    ) -> ReconciliationRunResult:
        if split not in ["optimization", "held_out", "full"]:
            raise ValueError(f"Invalid benchmark split '{split}'")

        cases = self.load_domain_cases(split)
        g_fp = _compute_graph_fingerprint(graph)

        case_results: List[CaseEvaluationResult] = []
        total_latency_ms = 0
        total_cost_usd = 0.0

        for case in cases:
            cache_key = f"{g_fp}_{split}_{case.case_code}"
            if cache_key in self._cache:
                case_eval = CaseEvaluationResult.model_validate(self._cache[cache_key])
                print(
                    f"  [{split}] Case {case.case_code} (cached): success={case_eval.success}, "
                    f"acc={case_eval.accuracy_score * 100:.1f}%, cost=${case_eval.cost_usd:.5f}, "
                    f"lat={case_eval.latency_ms}ms",
                    flush=True,
                )
            else:
                case_inputs = {
                    "bank_records": case.bank_records,
                    "ledger_entries": case.ledger_entries,
                    "records": case.bank_records,
                    "entries": case.ledger_entries,
                }
                state = await self.runtime.run(
                    graph=graph,
                    inputs=case_inputs,
                    goal=f"Reconcile bank records against general ledger entries for scenario {case.case_code}",
                    experiment_id=str(experiment_id) if experiment_id else None,
                    agent_version_id=str(agent_version_id) if agent_version_id else None,
                )
                case_eval = self.evaluator.evaluate_case(case, state)
                self._cache[cache_key] = case_eval.model_dump(mode="json")
                self._save_cache()
                print(
                    f"  [{split}] Case {case.case_code}: success={case_eval.success}, "
                    f"acc={case_eval.accuracy_score * 100:.1f}%, cost=${case_eval.cost_usd:.5f}, "
                    f"lat={case_eval.latency_ms}ms",
                    flush=True,
                )

            case_results.append(case_eval)
            total_latency_ms += case_eval.latency_ms
            total_cost_usd += case_eval.cost_usd

        total_cases = len(case_results)
        passed_cases = sum(1 for c in case_results if c.success)
        failed_cases = total_cases - passed_cases
        avg_accuracy = (
            sum(c.accuracy_score for c in case_results) / total_cases if total_cases > 0 else 0.0
        )
        reliability = (
            sum(c.reliability_score for c in case_results) / total_cases if total_cases > 0 else 0.0
        )
        avg_latency_ms = int(total_latency_ms / total_cases) if total_cases > 0 else 0

        return ReconciliationRunResult(
            benchmark_name="reconciliation",
            benchmark_version="reconciliation-v1",
            split=split,
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            accuracy=round(avg_accuracy, 4),
            reliability=round(reliability, 4),
            total_cost_usd=round(total_cost_usd, 6),
            avg_latency_ms=avg_latency_ms,
            total_latency_ms=total_latency_ms,
            case_results=case_results,
            generation_method=graph.metadata.get("generation_method"),
            metadata={
                "graph_id": graph.graph_id,
                "graph_name": graph.name,
                "cost_type": "estimated",
                "pass_rate": round(passed_cases / total_cases, 4) if total_cases > 0 else 0.0,
                "evaluated_at_ms": total_latency_ms,
            },
        )


async def run_experiment():
    print("=" * 80)
    print("RECO STEP 13B: REAL-PROVIDER AUTONOMOUS OPTIMIZATION EXPERIMENT")
    print("=" * 80)

    settings = get_settings()
    print(f"Provider: {settings.llm_provider}")
    print(f"Model: {settings.llm_model}")
    print(f"Base URL: {settings.tensormux_base_url}")
    print("API Key present:", bool(settings.tensormux_api_key))

    # Initialize components
    gateway = TensorMuxGateway(timeout_seconds=60.0)
    executor = ToolExecutor(registry=default_tool_registry)
    runtime = AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)
    benchmark = CachedReconciliationBenchmark(runtime=runtime)
    analyzer = FailureAnalyzer(model_gateway=gateway, tool_registry=default_tool_registry)
    mutation_engine = MutationEngine(tool_registry=default_tool_registry, model_gateway=gateway)
    candidate_generator = CandidateGenerator(tool_registry=default_tool_registry)

    policy = ComparisonPolicy(
        accuracy_margin=0.0,
        max_latency_overhead_ratio=0.5,
        max_cost_overhead_ratio=0.5,
        allow_cost_latency_tradeoffs=True,
    )

    exp_id = uuid4()
    v0_graph = create_reconciliation_baseline_graph()
    v0_id = uuid4()

    results_data = {
        "experiment_id": str(exp_id),
        "model": settings.llm_model,
        "provider": settings.llm_provider,
        "timestamp": time.time(),
        "phases": {}
    }

    # =========================================================================
    # PHASE 1: Real V0 Optimization Split Benchmark (12 cases)
    # =========================================================================
    print("\n" + "=" * 80)
    print("PHASE 1: BENCHMARKING V0 ON OPTIMIZATION SPLIT (12 cases)")
    print("=" * 80)

    v0_opt_run = await benchmark.run_benchmark(
        graph=v0_graph,
        split="optimization",
        experiment_id=exp_id,
        agent_version_id=v0_id,
        persist=False,
    )
    v0_opt_card = v0_opt_run.to_scorecard()

    print(f"V0 Opt Total Cases: {v0_opt_run.total_cases}")
    print(f"V0 Opt Passed Cases: {v0_opt_run.passed_cases}")
    print(f"V0 Opt Failed Cases: {v0_opt_run.failed_cases}")
    print(f"V0 Opt Accuracy: {v0_opt_card.accuracy * 100:.2f}%")
    print(f"V0 Opt Reliability: {v0_opt_card.reliability * 100:.2f}%")
    print(f"V0 Opt Total Cost USD: ${v0_opt_card.total_cost_usd:.6f} ({v0_opt_card.cost_type})")
    print(f"V0 Opt Avg Cost USD: ${v0_opt_card.avg_cost_usd:.6f}")
    print(f"V0 Opt Total Latency: {v0_opt_card.total_latency_ms} ms")
    print(f"V0 Opt Avg Latency: {v0_opt_card.avg_latency_ms} ms")

    total_tokens_in_v0_opt = sum(c.tokens_in for c in v0_opt_run.case_results)
    total_tokens_out_v0_opt = sum(c.tokens_out for c in v0_opt_run.case_results)
    print(f"V0 Opt Tokens In: {total_tokens_in_v0_opt} | Tokens Out: {total_tokens_out_v0_opt}")

    failed_v0_opt = [c for c in v0_opt_run.case_results if not c.success]
    print(f"Failed Case Codes: {[c.case_code for c in failed_v0_opt]}")

    results_data["phases"]["phase_1_v0_opt"] = {
        "scorecard": v0_opt_card.model_dump(mode="json"),
        "total_tokens_in": total_tokens_in_v0_opt,
        "total_tokens_out": total_tokens_out_v0_opt,
        "failed_case_codes": [c.case_code for c in failed_v0_opt],
        "case_summaries": [
            {
                "case_code": c.case_code,
                "success": c.success,
                "accuracy": c.accuracy_score,
                "cost_usd": c.cost_usd,
                "latency_ms": c.latency_ms,
                "tokens_in": c.tokens_in,
                "tokens_out": c.tokens_out,
            }
            for c in v0_opt_run.case_results
        ]
    }

    # =========================================================================
    # PHASE 2: Baseline Held-Out Split Benchmark (8 cases)
    # =========================================================================
    print("\n" + "=" * 80)
    print("PHASE 2: BENCHMARKING V0 ON HELD-OUT SPLIT (8 cases)")
    print("=" * 80)

    v0_held_run = await benchmark.run_benchmark(
        graph=v0_graph,
        split="held_out",
        experiment_id=exp_id,
        agent_version_id=v0_id,
        persist=False,
    )
    v0_held_card = v0_held_run.to_scorecard()

    print(f"V0 Held-Out Total Cases: {v0_held_run.total_cases}")
    print(f"V0 Held-Out Passed Cases: {v0_held_run.passed_cases}")
    print(f"V0 Held-Out Failed Cases: {v0_held_run.failed_cases}")
    print(f"V0 Held-Out Accuracy: {v0_held_card.accuracy * 100:.2f}%")
    print(f"V0 Held-Out Reliability: {v0_held_card.reliability * 100:.2f}%")
    print(f"V0 Held-Out Total Cost USD: ${v0_held_card.total_cost_usd:.6f} ({v0_held_card.cost_type})")
    print(f"V0 Held-Out Avg Cost USD: ${v0_held_card.avg_cost_usd:.6f}")
    print(f"V0 Held-Out Total Latency: {v0_held_card.total_latency_ms} ms")
    print(f"V0 Held-Out Avg Latency: {v0_held_card.avg_latency_ms} ms")

    total_tokens_in_v0_held = sum(c.tokens_in for c in v0_held_run.case_results)
    total_tokens_out_v0_held = sum(c.tokens_out for c in v0_held_run.case_results)

    results_data["phases"]["phase_2_v0_held"] = {
        "scorecard": v0_held_card.model_dump(mode="json"),
        "total_tokens_in": total_tokens_in_v0_held,
        "total_tokens_out": total_tokens_out_v0_held,
        "passed_cases": v0_held_run.passed_cases,
        "failed_cases": v0_held_run.failed_cases,
    }

    # =========================================================================
    # PHASE 3: Real Failure Analysis on V0 Optimization Failures
    # =========================================================================
    print("\n" + "=" * 80)
    print("PHASE 3: FAILURE ANALYSIS ON V0 OPTIMIZATION FAILURES")
    print("=" * 80)

    v0_diagnoses = []
    for case_res in failed_v0_opt:
        diag = analyzer.analyze(
            execution_record=case_res,
            architecture=v0_graph,
            benchmark_context={
                "benchmark_name": v0_opt_card.benchmark_name,
                "case_code": case_res.case_code,
                "ground_truth": case_res.expected_outcome,
            },
            scorecard_metrics={
                "accuracy": v0_opt_card.accuracy,
                "reliability": v0_opt_card.reliability,
            },
        )
        v0_diagnoses.append(diag)
        case_code = case_res.case_code
        print(f"\n[Diagnosis] Case: {case_code}")
        print(f"  Category: {diag.failure_category.value}")
        print(f"  Failed Node: {diag.failed_node_id or 'graph'}")
        print(f"  Confidence: {diag.confidence}")
        print(f"  Severity: {diag.severity.value}")
        print(f"  Root Cause: {diag.root_cause}")
        print(f"  Symptom: {diag.symptom}")
        print(f"  Evidence Count: {len(diag.evidence)}")
        print(f"  Recommended Mutations: {[r.mutation_type.value for r in diag.recommended_mutations]}")

    v0_clusters = analyzer.cluster_failures(v0_diagnoses) if v0_diagnoses else []
    print(f"\nTotal Failure Clusters Formed: {len(v0_clusters)}")
    for cl in v0_clusters:
        print(f"Cluster: {cl.cluster_id} | Primary: {cl.category.value} | Cases: {len(cl.diagnoses)} | Priority Score: {cl.priority_score}")

    results_data["phases"]["phase_3_v0_analysis"] = {
        "diagnoses_count": len(v0_diagnoses),
        "diagnoses": [d.model_dump(mode="json") for d in v0_diagnoses],
        "clusters": [
            {
                "cluster_id": cl.cluster_id,
                "primary_category": cl.category.value,
                "count": len(cl.diagnoses),
                "priority_score": cl.priority_score,
                "recommended_mutations": [r.model_dump(mode="json") for r in cl.recommended_mutations]
            }
            for cl in v0_clusters
        ]
    }

    # =========================================================================
    # PHASE 4: Candidate Generation for V1
    # =========================================================================
    print("\n" + "=" * 80)
    print("PHASE 4: CANDIDATE GENERATION (Max 3 candidates)")
    print("=" * 80)

    v0_candidates_meta = candidate_generator.generate(
        agent_graph=v0_graph,
        diagnoses=v0_diagnoses,
        parent_version_id=v0_id,
        max_candidates=3,
        clusters=v0_clusters,
    )
    print(f"Synthesized Mutation Proposals: {len(v0_candidates_meta)}")

    applied_candidates_v1 = []
    for idx, cand_meta in enumerate(v0_candidates_meta, start=1):
        version_cand = mutation_engine.apply_mutation(
            graph=v0_graph,
            mutation=cand_meta,
            parent_version_id=v0_id,
            version_number=1,
        )
        applied_candidates_v1.append(version_cand)
        print(f"\nCandidate {idx}: ID={version_cand.candidate_id}")
        print(f"  Mutation Type: {cand_meta.mutation_type.value}")
        print(f"  Target: {cand_meta.target}")
        print(f"  Rationale: {cand_meta.rationale}")
        print(f"  Confidence: {cand_meta.confidence}")
        print(f"  Is Valid: {version_cand.is_valid}")
        print(f"  Rejection Reason: {version_cand.rejection_reason or 'None'}")

    results_data["phases"]["phase_4_candidates_v1"] = [
        {
            "candidate_id": str(c.candidate_id),
            "mutation_type": c.mutation.mutation_type.value,
            "target": c.mutation.target,
            "rationale": c.mutation.rationale,
            "confidence": c.mutation.confidence,
            "is_valid": c.is_valid,
            "rejection_reason": c.rejection_reason,
            "proposed_change": c.mutation.proposed_change,
        }
        for c in applied_candidates_v1
    ]

    valid_candidates_v1 = [c for c in applied_candidates_v1 if c.is_valid]
    if not valid_candidates_v1:
        print("ERROR: No valid candidate generated for V1. Terminating experiment.")
        OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_JSON_PATH.write_text(json.dumps(results_data, indent=2), encoding="utf-8")
        return results_data

    # Select the candidate with highest confidence / priority
    v1_chosen = sorted(valid_candidates_v1, key=lambda c: c.mutation.confidence, reverse=True)[0]
    print(f"\nSelected Candidate for V1: {v1_chosen.candidate_id} ({v1_chosen.mutation.mutation_type.value})")

    # =========================================================================
    # PHASE 5: Real V1 Optimization Benchmark (12 cases) & Comparison
    # =========================================================================
    print("\n" + "=" * 80)
    print("PHASE 5: BENCHMARKING V1 ON OPTIMIZATION SPLIT (12 cases)")
    print("=" * 80)

    v1_opt_run = await benchmark.run_benchmark(
        graph=v1_chosen.graph,
        split="optimization",
        experiment_id=exp_id,
        agent_version_id=v1_chosen.candidate_id,
        persist=False,
    )
    v1_opt_card = v1_opt_run.to_scorecard()

    print(f"V1 Opt Total Cases: {v1_opt_run.total_cases}")
    print(f"V1 Opt Passed Cases: {v1_opt_run.passed_cases}")
    print(f"V1 Opt Failed Cases: {v1_opt_run.failed_cases}")
    print(f"V1 Opt Accuracy: {v1_opt_card.accuracy * 100:.2f}%")
    print(f"V1 Opt Reliability: {v1_opt_card.reliability * 100:.2f}%")
    print(f"V1 Opt Total Cost USD: ${v1_opt_card.total_cost_usd:.6f} ({v1_opt_card.cost_type})")
    print(f"V1 Opt Avg Cost USD: ${v1_opt_card.avg_cost_usd:.6f}")
    print(f"V1 Opt Total Latency: {v1_opt_card.total_latency_ms} ms")
    print(f"V1 Opt Avg Latency: {v1_opt_card.avg_latency_ms} ms")

    total_tokens_in_v1_opt = sum(c.tokens_in for c in v1_opt_run.case_results)
    total_tokens_out_v1_opt = sum(c.tokens_out for c in v1_opt_run.case_results)
    print(f"V1 Opt Tokens In: {total_tokens_in_v1_opt} | Tokens Out: {total_tokens_out_v1_opt}")

    failed_v1_opt = [c for c in v1_opt_run.case_results if not c.success]
    print(f"V1 Failed Case Codes: {[c.case_code for c in failed_v1_opt]}")

    # Compare V0 vs V1
    v0_v1_comparison = compare_scorecards(v0_opt_card, v1_opt_card, policy)
    print(f"\nScorecard Comparison (V0 -> V1):")
    print(f"  Relationship: {v0_v1_comparison.relationship}")
    print(f"  Accuracy Delta: {v0_v1_comparison.accuracy_delta:+.4f} ({v0_v1_comparison.relative_changes.get('accuracy', 0.0):+.2f}%)")
    print(f"  Reliability Delta: {v0_v1_comparison.reliability_delta:+.4f}")
    print(f"  Cost Delta: ${v0_v1_comparison.cost_delta:+.6f} ({v0_v1_comparison.relative_changes.get('cost', 0.0):+.2f}%)")
    print(f"  Latency Delta: {v0_v1_comparison.latency_delta:+.1f} ms ({v0_v1_comparison.relative_changes.get('speed', 0.0):+.2f}%)")
    print(f"  Summary: {v0_v1_comparison.summary}")

    results_data["phases"]["phase_5_v1_opt"] = {
        "candidate_id": str(v1_chosen.candidate_id),
        "scorecard": v1_opt_card.model_dump(mode="json"),
        "total_tokens_in": total_tokens_in_v1_opt,
        "total_tokens_out": total_tokens_out_v1_opt,
        "failed_case_codes": [c.case_code for c in failed_v1_opt],
        "comparison_vs_v0": v0_v1_comparison.model_dump(mode="json"),
    }

    # =========================================================================
    # PHASE 6: Decide Whether V2 is Justified
    # =========================================================================
    print("\n" + "=" * 80)
    print("PHASE 6: DECISION ON V2 GENERATION")
    print("=" * 80)

    is_v1_viable = (
        v0_v1_comparison.relationship in ["strictly_better", "tradeoff"]
        and v1_opt_card.accuracy >= v0_opt_card.accuracy
        and v1_opt_card.reliability >= v0_opt_card.reliability
    )

    current_winner_graph = v1_chosen.graph if is_v1_viable else v0_graph
    current_winner_id = v1_chosen.candidate_id if is_v1_viable else v0_id
    current_winner_card = v1_opt_card if is_v1_viable else v0_opt_card

    v2_produced = False
    v2_results = None

    if is_v1_viable and failed_v1_opt:
        print(f"V1 is viable ({v0_v1_comparison.relationship}). Proceeding to synthesize V2 from V1 failures.")
        # Diagnose V1 failures
        v1_diagnoses = []
        for case_res in failed_v1_opt:
            diag = analyzer.analyze(
                execution_record=case_res,
                architecture=v1_chosen.graph,
                benchmark_context={
                    "benchmark_name": v1_opt_card.benchmark_name,
                    "case_code": case_res.case_code,
                    "ground_truth": case_res.expected_outcome,
                },
                scorecard_metrics={
                    "accuracy": v1_opt_card.accuracy,
                    "reliability": v1_opt_card.reliability,
                },
            )
            v1_diagnoses.append(diag)
        v1_clusters = analyzer.cluster_failures(v1_diagnoses) if v1_diagnoses else []

        v1_candidates_meta = candidate_generator.generate(
            agent_graph=v1_chosen.graph,
            diagnoses=v1_diagnoses,
            parent_version_id=v1_chosen.candidate_id,
            max_candidates=3,
            clusters=v1_clusters,
        )

        valid_v2_candidates = []
        for cand_meta in v1_candidates_meta:
            version_cand = mutation_engine.apply_mutation(
                graph=v1_chosen.graph,
                mutation=cand_meta,
                parent_version_id=v1_chosen.candidate_id,
                version_number=2,
            )
            if version_cand.is_valid:
                valid_v2_candidates.append(version_cand)

        if valid_v2_candidates:
            v2_chosen = sorted(valid_v2_candidates, key=lambda c: c.mutation.confidence, reverse=True)[0]
            print(f"Running V2 candidate: {v2_chosen.candidate_id} ({v2_chosen.mutation.mutation_type.value})...")
            v2_opt_run = await benchmark.run_benchmark(
                graph=v2_chosen.graph,
                split="optimization",
                experiment_id=exp_id,
                agent_version_id=v2_chosen.candidate_id,
                persist=False,
            )
            v2_opt_card = v2_opt_run.to_scorecard()
            v1_v2_comparison = compare_scorecards(v1_opt_card, v2_opt_card, policy)
            print(f"V2 Opt Accuracy: {v2_opt_card.accuracy * 100:.2f}% | Reliability: {v2_opt_card.reliability * 100:.2f}%")
            print(f"Comparison V1 -> V2: {v1_v2_comparison.relationship} (Acc delta: {v1_v2_comparison.accuracy_delta:+.4f})")

            v2_produced = True
            v2_results = {
                "candidate_id": str(v2_chosen.candidate_id),
                "mutation": v2_chosen.mutation.model_dump(mode="json"),
                "scorecard": v2_opt_card.model_dump(mode="json"),
                "comparison_vs_v1": v1_v2_comparison.model_dump(mode="json"),
            }

            if (
                v1_v2_comparison.relationship in ["strictly_better", "tradeoff"]
                and v2_opt_card.accuracy >= v1_opt_card.accuracy
            ):
                print("V2 selected as overall winner!")
                current_winner_graph = v2_chosen.graph
                current_winner_id = v2_chosen.candidate_id
                current_winner_card = v2_opt_card
            else:
                print("V2 did not improve upon V1. Retaining V1 as winner.")
        else:
            print("No valid candidates could be generated for V2.")
    else:
        if not is_v1_viable:
            print(f"V1 was not viable (relationship: {v0_v1_comparison.relationship}). Stopping without generating V2.")
        else:
            print("V1 achieved 100% accuracy on optimization split. No failures to optimize.")

    results_data["phases"]["phase_6_v2"] = {
        "v2_produced": v2_produced,
        "v2_data": v2_results,
        "current_winner_id": str(current_winner_id),
    }

    # =========================================================================
    # PHASE 7: Held-Out Promotion Gate
    # =========================================================================
    print("\n" + "=" * 80)
    print("PHASE 7: HELD-OUT PROMOTION GATE EVALUATION")
    print("=" * 80)

    print(f"Evaluating Winner ({current_winner_id}) on Held-Out Split (8 cases)...")
    winner_held_run = await benchmark.run_benchmark(
        graph=current_winner_graph,
        split="held_out",
        experiment_id=exp_id,
        agent_version_id=current_winner_id,
        persist=False,
    )
    winner_held_card = winner_held_run.to_scorecard()

    print(f"Winner Held-Out Total Cases: {winner_held_run.total_cases}")
    print(f"Winner Held-Out Passed Cases: {winner_held_run.passed_cases}")
    print(f"Winner Held-Out Failed Cases: {winner_held_run.failed_cases}")
    print(f"Winner Held-Out Accuracy: {winner_held_card.accuracy * 100:.2f}%")
    print(f"Winner Held-Out Reliability: {winner_held_card.reliability * 100:.2f}%")
    print(f"Winner Held-Out Cost USD: ${winner_held_card.total_cost_usd:.6f} ({winner_held_card.cost_type})")
    print(f"Winner Held-Out Latency: {winner_held_card.total_latency_ms} ms")

    total_tokens_in_winner_held = sum(c.tokens_in for c in winner_held_run.case_results)
    total_tokens_out_winner_held = sum(c.tokens_out for c in winner_held_run.case_results)

    # Run formal promotion assessment
    promotion_assessment = assess_promotion(
        baseline=v0_held_card,
        candidate=winner_held_card,
        policy=policy,
    )

    print(f"\nFormal Promotion Assessment Result:")
    print(f"  Decision: {promotion_assessment.decision.upper()}")
    print(f"  Reasons: {promotion_assessment.reasons}")
    print(f"  Improved Dimensions: {promotion_assessment.improved_dimensions}")
    print(f"  Regressed Dimensions: {promotion_assessment.regressed_dimensions}")
    print(f"  Gate Relationship: {promotion_assessment.comparison.relationship}")
    print(f"  Held-Out Accuracy Delta: {promotion_assessment.comparison.accuracy_delta:+.4f} ({promotion_assessment.comparison.relative_changes.get('accuracy', 0.0):+.2f}%)")
    print(f"  Held-Out Cost Delta: ${promotion_assessment.comparison.cost_delta:+.6f}")
    print(f"  Held-Out Latency Delta: {promotion_assessment.comparison.latency_delta:+.1f} ms")

    results_data["phases"]["phase_7_promotion_gate"] = {
        "winner_version_id": str(current_winner_id),
        "winner_held_out_scorecard": winner_held_card.model_dump(mode="json"),
        "total_tokens_in": total_tokens_in_winner_held,
        "total_tokens_out": total_tokens_out_winner_held,
        "promotion_assessment": promotion_assessment.model_dump(mode="json"),
    }

    # Save results to scratch JSON
    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.write_text(json.dumps(results_data, indent=2), encoding="utf-8")
    print(f"\nExperiment execution complete! Full results saved to: {OUTPUT_JSON_PATH}")

    return results_data


if __name__ == "__main__":
    asyncio.run(run_experiment())
