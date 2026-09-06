"""Step 14: Full Real Autonomous Optimization Experiment Runner.

Executes:
Phase 1: Real V0 Optimization Split Benchmark (12 cases) & Held-Out Watermark (8 cases)
Phase 2: Real Failure Analysis on V0 Optimization Failures ONLY (Anti-leakage audit)
Phase 3: Candidate Generation for V1 (up to 3 candidates targeting diagnoses)
Phase 4: Real V1 Benchmark (All valid candidates on 12 optimization cases)
Phase 5: Select V1 via ComparisonPolicy
Phase 6: Failure-driven V2 (Residual failures only)
Phase 7: Generation 3 if justified
Phase 8: Held-Out Promotion Gate (V0 held-out vs final Vn held-out)
Phase 9-15: Generalization, cost/speed, attribution, behavioral proof, leakage audit, artifact generation
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

CACHE_FILE_PATH = Path(r"C:\Users\toufi\.gemini\antigravity-ide\brain\7d9a276d-29fd-4456-9c5b-a153840fd462\scratch\case_cache_step14.json")
OUTPUT_JSON_PATH = Path(r"C:\Users\toufi\.gemini\antigravity-ide\brain\7d9a276d-29fd-4456-9c5b-a153840fd462\scratch\step14_real_optimization.json")


def _compute_graph_fingerprint(graph: GraphDefinition) -> str:
    """Deterministic cryptographic fingerprint including node roles, execution modes, prompts, tools, and topology."""
    parts = []
    for nid in sorted(graph.nodes.keys()):
        n = graph.nodes[nid]
        exec_mode = n.get_execution_mode()
        parts.append(
            f"{nid}|{n.role}|{exec_mode}|{n.system_prompt.strip()}|{sorted(n.tools)}|{json.dumps(n.input_mapping, sort_keys=True)}"
        )
    for e in sorted(graph.edges, key=lambda x: (x.source_node_id, x.target_node_id)):
        parts.append(f"{e.source_node_id}->{e.target_node_id}")
    return hashlib.sha256(";".join(parts).encode("utf-8")).hexdigest()[:16]


def _sanitize_for_report(data: Any) -> Any:
    """Recursively redact any secrets or credentials without masking usage token counts."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_lower = k.lower()
            if any(s in k_lower for s in ["api_key", "secret", "credential", "password", "authorization", "bearer", "private_key"]):
                sanitized[k] = "[REDACTED]"
            elif "token" in k_lower and not any(t in k_lower for t in ["tokens_in", "tokens_out", "total_tokens"]):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = _sanitize_for_report(v)
        return sanitized
    elif isinstance(data, list):
        return [_sanitize_for_report(x) for x in data]
    return data


class CachedReconciliationBenchmark(ReconciliationBenchmark):
    """ReconciliationBenchmark with persistent on-disk case caching and bounded retry for transient network glitches."""

    def __init__(self, runtime, cache_path: Path = CACHE_FILE_PATH):
        super().__init__(runtime=runtime)
        self.cache_path = cache_path
        self._cache = self._load_cache()

    def _load_cache(self) -> dict:
        if self.cache_path.exists():
            try:
                data = json.loads(self.cache_path.read_text(encoding="utf-8"))
                print(f"[Cache] Loaded {len(data)} cached case evaluations from {self.cache_path.name}")
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
        experiment_id=None,
        agent_version_id=None,
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

                # Attempt execution with retry on transient network errors
                last_exc = None
                for attempt in range(1, 3):
                    try:
                        state = await self.runtime.run(
                            graph=graph,
                            inputs=case_inputs,
                            goal=f"Reconcile bank records against general ledger entries for scenario {case.case_code}",
                            experiment_id=str(experiment_id) if experiment_id else None,
                            agent_version_id=str(agent_version_id) if agent_version_id else None,
                        )
                        break
                    except Exception as exc:
                        last_exc = exc
                        print(f"    [Warning] Attempt {attempt} failed on {case.case_code}: {exc}. Retrying in 4s...")
                        await asyncio.sleep(4)
                else:
                    raise RuntimeError(f"Case {case.case_code} failed after 2 attempts: {last_exc}")

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
            accuracy=avg_accuracy,
            reliability=reliability,
            total_latency_ms=total_latency_ms,
            avg_latency_ms=avg_latency_ms,
            total_cost_usd=round(total_cost_usd, 6),
            case_results=case_results,
        )


async def main():
    print("=" * 80)
    print("RECO STEP 14: FULL REAL AUTONOMOUS OPTIMIZATION EXPERIMENT")
    print("=" * 80)

    settings = get_settings()
    has_api_key = bool(settings.tensormux_api_key and settings.tensormux_api_key.strip())
    print(f"Provider: {settings.llm_provider}")
    print(f"Model: {settings.llm_model}")
    print(f"Base URL: {settings.tensormux_base_url}")
    print(f"API Key Configured: {has_api_key}")

    if not has_api_key:
        print("[ERROR] TENSORMUX_API_KEY is not configured.")
        return

    # Initialize Real TensorMux Gateway & Runtime
    gateway = TensorMuxGateway(
        api_key=settings.tensormux_api_key,
        base_url=settings.tensormux_base_url,
        default_model=settings.llm_model,
        timeout_seconds=90.0,
    )
    executor = ToolExecutor(registry=default_tool_registry)
    runtime = AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)
    benchmark = CachedReconciliationBenchmark(runtime=runtime)
    analyzer = FailureAnalyzer()
    mutation_engine = MutationEngine(tool_registry=default_tool_registry)
    candidate_generator = CandidateGenerator(tool_registry=default_tool_registry)
    policy = ComparisonPolicy(
        min_accuracy_improvement=0.0,
        allow_cost_increase=True,
        allow_latency_increase=True,
    )

    exp_id = uuid4()
    v0_id = uuid4()

    # Step 13C Canonical Model-Driven Architecture
    v0_graph = create_reconciliation_baseline_graph()
    v0_graph.nodes["parse_statement"].execution_mode = "deterministic_tool"
    v0_graph.nodes["query_ledger"].execution_mode = "deterministic_tool"
    v0_graph.nodes["fuzzy_match"].execution_mode = "model_driven"
    v0_graph.nodes["verify_summary"].execution_mode = "model_inference"

    print(f"\nInitial Architecture V0: {v0_graph.name}")
    for nid, node in v0_graph.nodes.items():
        print(f"  Node [{nid}]: role={node.role}, mode={node.get_execution_mode()}, tools={node.tools}")

    results_data: Dict[str, Any] = {
        "experiment_id": str(exp_id),
        "model": settings.llm_model,
        "provider": settings.llm_provider,
        "timestamp": time.time(),
        "phases": {},
        "generations": [],
    }

    # =========================================================================
    # PHASE 1: Real V0 Optimization Split Benchmark (12 cases) & Held-Out Watermark (8 cases)
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
    print(f"V0 Opt Total Cost USD: ${v0_opt_card.total_cost_usd:.6f}")
    print(f"V0 Opt Avg Latency: {v0_opt_card.avg_latency_ms} ms")

    total_tokens_in_v0_opt = sum(c.tokens_in for c in v0_opt_run.case_results)
    total_tokens_out_v0_opt = sum(c.tokens_out for c in v0_opt_run.case_results)
    total_model_calls_v0_opt = sum(len(c.tool_events) + 1 for c in v0_opt_run.case_results)
    total_tool_calls_v0_opt = sum(len(c.tool_events) for c in v0_opt_run.case_results)

    failed_v0_opt = [c for c in v0_opt_run.case_results if not c.success]
    print(f"V0 Opt Failed Case Codes: {[c.case_code for c in failed_v0_opt]}")

    results_data["phases"]["phase_1_v0_opt"] = {
        "scorecard": v0_opt_card.model_dump(mode="json"),
        "total_tokens_in": total_tokens_in_v0_opt,
        "total_tokens_out": total_tokens_out_v0_opt,
        "total_model_calls": total_model_calls_v0_opt,
        "total_tool_calls": total_tool_calls_v0_opt,
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
        ],
    }

    # Held-Out Split Benchmark for V0 Watermark (8 cases)
    print("\n" + "=" * 80)
    print("PHASE 1 (HELD-OUT WATERMARK): BENCHMARKING V0 ON HELD-OUT SPLIT (8 cases)")
    print("=" * 80)

    v0_held_run = await benchmark.run_benchmark(
        graph=v0_graph,
        split="held_out",
        experiment_id=exp_id,
        agent_version_id=v0_id,
        persist=False,
    )
    v0_held_card = v0_held_run.to_scorecard()

    print(f"V0 Held-Out Accuracy: {v0_held_card.accuracy * 100:.2f}%")
    print(f"V0 Held-Out Reliability: {v0_held_card.reliability * 100:.2f}%")
    print(f"V0 Held-Out Total Cost USD: ${v0_held_card.total_cost_usd:.6f}")
    print(f"V0 Held-Out Avg Latency: {v0_held_card.avg_latency_ms} ms")

    total_tokens_in_v0_held = sum(c.tokens_in for c in v0_held_run.case_results)
    total_tokens_out_v0_held = sum(c.tokens_out for c in v0_held_run.case_results)

    results_data["phases"]["phase_1_v0_held"] = {
        "scorecard": v0_held_card.model_dump(mode="json"),
        "total_tokens_in": total_tokens_in_v0_held,
        "total_tokens_out": total_tokens_out_v0_held,
        "passed_cases": v0_held_run.passed_cases,
        "failed_cases": v0_held_run.failed_cases,
    }

    # =========================================================================
    # MULTI-GENERATION EVOLUTIONARY LOOP (Max 3 Generations)
    # =========================================================================
    current_parent_graph = v0_graph
    current_parent_card = v0_opt_card
    current_parent_failed_cases = failed_v0_opt
    current_parent_version_id = v0_id
    current_version_name = "V0"

    selected_versions_history = [{"version": "V0", "id": str(v0_id), "scorecard": v0_opt_card.model_dump(mode="json")}]
    mutation_attributions = []

    for gen_idx in range(1, 4):
        print("\n" + "#" * 80)
        print(f"GENERATION {gen_idx}: EVOLVING FROM PARENT {current_version_name}")
        print("#" * 80)

        # Check convergence
        if not current_parent_failed_cases:
            print(f"Convergence reached! Parent {current_version_name} has 100% accuracy on optimization split.")
            break

        # ---------------------------------------------------------------------
        # Step A: Failure Analysis on CURRENT parent's failed cases ONLY
        # ---------------------------------------------------------------------
        print(f"\n[Gen {gen_idx}] Running Failure Analysis on {len(current_parent_failed_cases)} failed cases...")
        gen_diagnoses = []
        for case_res in current_parent_failed_cases:
            # STRICT ANTI-LEAKAGE ASSERTION: case must be in optimization split
            assert not case_res.case_code.startswith("REC-HLD"), f"LEAKAGE DETECTED: {case_res.case_code} is held-out!"
            diag = analyzer.analyze(
                execution_record=case_res,
                architecture=current_parent_graph,
                benchmark_context={
                    "benchmark_name": current_parent_card.benchmark_name,
                    "case_code": case_res.case_code,
                    "ground_truth": case_res.expected_outcome,
                },
                scorecard_metrics={
                    "accuracy": current_parent_card.accuracy,
                    "reliability": current_parent_card.reliability,
                },
            )
            gen_diagnoses.append(diag)
            print(f"  Diagnosis for {case_res.case_code}: {diag.failure_category.value} on node '{diag.failed_node_id or 'graph'}'")

        gen_clusters = analyzer.cluster_failures(gen_diagnoses) if gen_diagnoses else []
        print(f"[Gen {gen_idx}] Clusters formed: {len(gen_clusters)}")

        # ---------------------------------------------------------------------
        # Step B: Candidate Generation (up to 3 candidates)
        # ---------------------------------------------------------------------
        print(f"\n[Gen {gen_idx}] Synthesizing candidates (max 3)...")
        candidates_meta = candidate_generator.generate(
            agent_graph=current_parent_graph,
            diagnoses=gen_diagnoses,
            parent_version_id=current_parent_version_id,
            max_candidates=3,
            clusters=gen_clusters,
        )
        print(f"[Gen {gen_idx}] Generated {len(candidates_meta)} mutation candidates.")

        if not candidates_meta:
            print(f"[Gen {gen_idx}] No candidates generated. Ending evolution.")
            break

        applied_candidates = []
        for c_idx, cand_meta in enumerate(candidates_meta, start=1):
            version_cand = mutation_engine.apply_mutation(
                graph=current_parent_graph,
                mutation=cand_meta,
                parent_version_id=current_parent_version_id,
                version_number=gen_idx,
            )
            applied_candidates.append(version_cand)
            print(f"  Candidate {c_idx}: type={cand_meta.mutation_type.value}, target={cand_meta.target}, valid={version_cand.is_valid}")

        valid_candidates = [c for c in applied_candidates if c.is_valid]
        if not valid_candidates:
            print(f"[Gen {gen_idx}] No valid candidates after static validation. Ending evolution.")
            break

        # ---------------------------------------------------------------------
        # Step C: Real Benchmarking of EACH Valid Candidate (12 optimization cases)
        # ---------------------------------------------------------------------
        print(f"\n[Gen {gen_idx}] Benchmarking {len(valid_candidates)} valid candidates across 12 optimization cases...")
        cand_eval_records = []

        for c_idx, cand in enumerate(valid_candidates, start=1):
            print(f"\n--- Benchmarking Candidate {c_idx} ({cand.mutation.mutation_type.value} on '{cand.mutation.target}') ---")
            cand_run = await benchmark.run_benchmark(
                graph=cand.graph,
                split="optimization",
                experiment_id=exp_id,
                agent_version_id=cand.candidate_id,
                persist=False,
            )
            cand_card = cand_run.to_scorecard()
            comp = compare_scorecards(current_parent_card, cand_card, policy)

            print(f"  Candidate {c_idx} Accuracy: {cand_card.accuracy * 100:.2f}% (Parent: {current_parent_card.accuracy * 100:.2f}%)")
            print(f"  Candidate {c_idx} Cost: ${cand_card.total_cost_usd:.6f} | Latency: {cand_card.avg_latency_ms} ms")
            print(f"  Relationship to Parent: {comp.relationship}")
            print(f"  Accuracy Delta: {comp.accuracy_delta:+.4f}")

            cand_eval_records.append({
                "candidate": cand,
                "run": cand_run,
                "scorecard": cand_card,
                "comparison": comp,
            })

        # ---------------------------------------------------------------------
        # Step D: Candidate Selection
        # ---------------------------------------------------------------------
        # Find candidates that improve accuracy or are non-regressive
        improving_cands = [
            r for r in cand_eval_records
            if r["scorecard"].accuracy > current_parent_card.accuracy
            and r["scorecard"].reliability >= current_parent_card.reliability
        ]

        gen_record: Dict[str, Any] = {
            "generation": gen_idx,
            "parent_version": current_version_name,
            "parent_version_id": str(current_parent_version_id),
            "diagnoses": [d.model_dump(mode="json") for d in gen_diagnoses],
            "candidates": [
                {
                    "candidate_id": str(r["candidate"].candidate_id),
                    "mutation_type": r["candidate"].mutation.mutation_type.value,
                    "target": r["candidate"].mutation.target,
                    "rationale": r["candidate"].mutation.rationale,
                    "scorecard": r["scorecard"].model_dump(mode="json"),
                    "comparison": r["comparison"].model_dump(mode="json"),
                }
                for r in cand_eval_records
            ],
            "selected": None,
        }

        if improving_cands:
            # Sort by highest accuracy, then lowest cost
            improving_cands.sort(key=lambda r: (r["scorecard"].accuracy, -r["scorecard"].total_cost_usd), reverse=True)
            winner = improving_cands[0]
            winner_version_name = f"V{gen_idx}"
            print(f"\n>>> PROMOTING CANDIDATE TO {winner_version_name}! Accuracy: {winner['scorecard'].accuracy * 100:.2f}% (Delta: {winner['comparison'].accuracy_delta:+.4f}) <<<")

            # Record mutation attribution
            mutation_attributions.append({
                "from_version": current_version_name,
                "to_version": winner_version_name,
                "addressed_failures": [d.failure_category.value for d in gen_diagnoses],
                "mutation_type": winner["candidate"].mutation.mutation_type.value,
                "target": winner["candidate"].mutation.target,
                "rationale": winner["candidate"].mutation.rationale,
                "observed_accuracy_delta": winner["comparison"].accuracy_delta,
                "scorecard_before": current_parent_card.model_dump(mode="json"),
                "scorecard_after": winner["scorecard"].model_dump(mode="json"),
            })

            gen_record["selected"] = {
                "version": winner_version_name,
                "candidate_id": str(winner["candidate"].candidate_id),
                "mutation_type": winner["candidate"].mutation.mutation_type.value,
                "target": winner["candidate"].mutation.target,
                "accuracy": winner["scorecard"].accuracy,
                "relationship": winner["comparison"].relationship,
            }

            # Update parent for next round
            current_parent_graph = winner["candidate"].graph
            current_parent_card = winner["scorecard"]
            current_parent_failed_cases = [c for c in winner["run"].case_results if not c.success]
            current_parent_version_id = winner["candidate"].candidate_id
            current_version_name = winner_version_name

            selected_versions_history.append({
                "version": current_version_name,
                "id": str(current_parent_version_id),
                "scorecard": current_parent_card.model_dump(mode="json"),
            })
            results_data["generations"].append(gen_record)
        else:
            print(f"\n[Gen {gen_idx}] No candidate improved parent accuracy. Halting evolutionary search non-destructively.")
            gen_record["selected"] = None
            gen_record["decision"] = "no_improvement"
            results_data["generations"].append(gen_record)
            break

    final_winning_version = current_version_name
    final_winning_graph = current_parent_graph
    final_winning_opt_card = current_parent_card

    print("\n" + "=" * 80)
    print(f"EVOLUTION COMPLETED: Final Best Architecture is {final_winning_version}")
    print("=" * 80)

    # =========================================================================
    # PHASE 8: Held-Out Promotion Gate
    # =========================================================================
    print("\n" + "=" * 80)
    print(f"PHASE 8: HELD-OUT PROMOTION GATE (Evaluating {final_winning_version} on 8 Held-Out Cases)")
    print("=" * 80)

    if final_winning_version == "V0":
        final_held_run = v0_held_run
        final_held_card = v0_held_card
    else:
        final_held_run = await benchmark.run_benchmark(
            graph=final_winning_graph,
            split="held_out",
            experiment_id=exp_id,
            agent_version_id=current_parent_version_id,
            persist=False,
        )
        final_held_card = final_held_run.to_scorecard()

    # Assess promotion: compare V0 held-out vs Final Vn held-out
    promotion_assessment = assess_promotion(
        baseline=v0_held_card,
        candidate=final_held_card,
        policy=policy,
    )

    print(f"V0 Held-Out Accuracy: {v0_held_card.accuracy * 100:.2f}%")
    print(f"{final_winning_version} Held-Out Accuracy: {final_held_card.accuracy * 100:.2f}%")
    print(f"Promotion Decision: {promotion_assessment.decision.upper()}")
    print(f"Promotion Reasons: {promotion_assessment.reasons}")

    # =========================================================================
    # PHASE 9-15: Generalization, Cost/Speed, Behavioral Proof, Leakage Audit, and Artifacts
    # =========================================================================
    opt_accuracy_delta = final_winning_opt_card.accuracy - v0_opt_card.accuracy
    held_accuracy_delta = final_held_card.accuracy - v0_held_card.accuracy

    generalization_summary = {
        "optimization_improvement": {
            "v0_accuracy": v0_opt_card.accuracy,
            "final_accuracy": final_winning_opt_card.accuracy,
            "delta": round(opt_accuracy_delta, 4),
        },
        "held_out_improvement": {
            "v0_accuracy": v0_held_card.accuracy,
            "final_accuracy": final_held_card.accuracy,
            "delta": round(held_accuracy_delta, 4),
        },
        "generalized": (opt_accuracy_delta >= 0 and held_accuracy_delta >= 0 and (opt_accuracy_delta > 0 or held_accuracy_delta > 0)),
    }

    # Behavioral Proof: Compare V0 vs Final Vn on REC-OPT-08 (Wrong Vendor)
    # Check cache for REC-OPT-08
    v0_fp = _compute_graph_fingerprint(v0_graph)
    final_fp = _compute_graph_fingerprint(final_winning_graph)
    v0_case08_raw = benchmark._cache.get(f"{v0_fp}_optimization_REC-OPT-08", {})
    final_case08_raw = benchmark._cache.get(f"{final_fp}_optimization_REC-OPT-08", {})

    behavioral_proof = {
        "case_code": "REC-OPT-08",
        "v0": {
            "accuracy": v0_case08_raw.get("accuracy_score"),
            "success": v0_case08_raw.get("success"),
            "matched_pairs": len(v0_case08_raw.get("details", {}).get("matched_pairs", [])),
        },
        "final": {
            "version": final_winning_version,
            "accuracy": final_case08_raw.get("accuracy_score"),
            "success": final_case08_raw.get("success"),
            "matched_pairs": len(final_case08_raw.get("details", {}).get("matched_pairs", [])),
        },
        "diverged": (
            v0_case08_raw.get("accuracy_score") != final_case08_raw.get("accuracy_score")
            or len(v0_case08_raw.get("details", {}).get("matched_pairs", [])) != len(final_case08_raw.get("details", {}).get("matched_pairs", []))
        ),
    }

    # Leakage Audit: Confirm zero held-out cases passed to FailureAnalyzer
    leakage_audit = {
        "held_out_cases_count": 8,
        "held_out_cases_fed_to_analyzer": 0,
        "held_out_cases_fed_to_mutator": 0,
        "leakage_detected": False,
        "verification_statement": "Held-out split was strictly evaluated at watermark and final promotion gate; zero held-out data was provided to FailureAnalyzer or CandidateGenerator.",
    }

    # Resource Accounting
    total_tokens_in_all = sum(v["tokens_in"] for v in benchmark._cache.values() if "tokens_in" in v)
    total_tokens_out_all = sum(v["tokens_out"] for v in benchmark._cache.values() if "tokens_out" in v)
    total_cost_all = sum(v["cost_usd"] for v in benchmark._cache.values() if "cost_usd" in v)

    results_data["summary"] = {
        "final_selected_version": final_winning_version,
        "promotion_decision": promotion_assessment.decision,
        "generalization": generalization_summary,
        "behavioral_proof": behavioral_proof,
        "mutation_attributions": mutation_attributions,
        "leakage_audit": leakage_audit,
        "benchmark_table": [
            {
                "version": "V0",
                "accuracy_opt": v0_opt_card.accuracy,
                "accuracy_held": v0_held_card.accuracy,
                "reliability_opt": v0_opt_card.reliability,
                "cost_opt": v0_opt_card.total_cost_usd,
                "avg_latency_ms": v0_opt_card.avg_latency_ms,
            },
            {
                "version": final_winning_version,
                "accuracy_opt": final_winning_opt_card.accuracy,
                "accuracy_held": final_held_card.accuracy,
                "reliability_opt": final_winning_opt_card.reliability,
                "cost_opt": final_winning_opt_card.total_cost_usd,
                "avg_latency_ms": final_winning_opt_card.avg_latency_ms,
            },
        ],
        "resource_accounting": {
            "total_tokens_in": total_tokens_in_all,
            "total_tokens_out": total_tokens_out_all,
            "total_cost_usd": round(total_cost_all, 6),
        },
    }

    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.write_text(json.dumps(_sanitize_for_report(results_data), indent=2), encoding="utf-8")
    print(f"\nComplete experiment results persisted to: {OUTPUT_JSON_PATH}")

    print("\n" + "=" * 80)
    print("STEP 14 EXPERIMENT EXECUTION COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"Final Version: {final_winning_version}")
    print(f"Optimization Accuracy: {v0_opt_card.accuracy * 100:.1f}% -> {final_winning_opt_card.accuracy * 100:.1f}% (Delta: {opt_accuracy_delta:+.4f})")
    print(f"Held-Out Accuracy: {v0_held_card.accuracy * 100:.1f}% -> {final_held_card.accuracy * 100:.1f}% (Delta: {held_accuracy_delta:+.4f})")
    print(f"Promotion Gate Decision: {promotion_assessment.decision.upper()}")


if __name__ == "__main__":
    asyncio.run(main())
