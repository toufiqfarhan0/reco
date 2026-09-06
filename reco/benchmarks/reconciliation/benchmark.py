"""Reconciliation Benchmark Suite implementing the core Benchmark interface.

Executes agent graph architectures deterministically across canonical test cases
using AgentGraphRuntime, evaluates outcomes via ReconciliationEvaluator, and
records multi-dimensional metrics and persistence records.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from reco.benchmarks.reconciliation.dataset import (
    BENCHMARK_NAME,
    BENCHMARK_VERSION,
    get_held_out_cases,
    get_optimization_cases,
    load_cases,
)
from reco.benchmarks.reconciliation.evaluator import ReconciliationEvaluator
from reco.benchmarks.reconciliation.models import (
    CaseEvaluationResult,
    ReconciliationCase,
    ReconciliationRunResult,
)
from reco.core.interfaces import Agent, Benchmark, BenchmarkCase, BenchmarkRunResult
from reco.db.models import BenchmarkRunRecord, CaseExecutionRecord
from reco.db.repositories import (
    BenchmarkCaseRepository,
    BenchmarkRunRepository,
    CaseExecutionRepository,
)
from reco.engine.models import GraphDefinition
from reco.engine.runtime import AgentGraphRuntime
from reco.llm.mock import MockModelGateway
from reco.logging import get_logger
from reco.observability.tracer import get_tracer
from reco.tools.executor import ToolExecutor
from reco.tools.reconciliation import register_reconciliation_tools
from reco.benchmarks.base import DomainBenchmark
from reco.tools.registry import ToolRegistry
from reco.core.interfaces import Tool

logger = get_logger("benchmarks.reconciliation")


class ReconciliationBenchmark(DomainBenchmark):
    """Deterministic Bank and General Ledger Reconciliation Benchmark Suite (Domain A)."""

    domain_id = "reconciliation"
    display_name = "Transaction Reconciliation"
    description = "Benchmarks agent capability to ingest bank records, match against general ledger entries, and resolve discrepancies."
    default_goal = "Reconcile bank statements against general ledger records with strict counterparty verification."

    def get_available_tools(self) -> List[Tool]:
        registry = ToolRegistry()
        register_reconciliation_tools(registry)
        return registry.list_tools()

    def get_evaluator_requirements(self) -> Dict[str, Any]:
        return {
            "metrics": ["accuracy", "reliability", "cost", "latency"],
            "expected_output_format": "json_object",
            "schema_requirements": ["matched_pairs", "unmatched_records"],
        }

    def __init__(
        self,
        runtime: Optional[AgentGraphRuntime] = None,
        evaluator: Optional[ReconciliationEvaluator] = None,
        benchmark_run_repo: Optional[BenchmarkRunRepository] = None,
        case_execution_repo: Optional[CaseExecutionRepository] = None,
        benchmark_case_repo: Optional[BenchmarkCaseRepository] = None,
    ):
        # Initialize default deterministic runtime if none supplied
        if runtime is None:
            registry = ToolRegistry()
            register_reconciliation_tools(registry)
            executor = ToolExecutor(registry=registry)
            gateway = MockModelGateway(
                default_content="Reconciliation verification passed without discrepancies.",
                auto_tool_calls=True,
            )
            self.runtime = AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)
        else:
            self.runtime = runtime

        self.evaluator = evaluator or ReconciliationEvaluator()
        self.benchmark_run_repo = benchmark_run_repo
        self.case_execution_repo = case_execution_repo
        self.benchmark_case_repo = benchmark_case_repo

    def load_cases(self, split: Optional[str] = None) -> List[BenchmarkCase]:
        """Load benchmark scenarios conforming to the core Benchmark interface."""
        domain_cases = load_cases(split)
        return [c.to_benchmark_case() for c in domain_cases]

    def load_domain_cases(self, split: Optional[str] = None) -> List[ReconciliationCase]:
        """Load strongly-typed domain ReconciliationCase objects."""
        return load_cases(split)

    def load_optimization_cases(self) -> List[ReconciliationCase]:
        """Explicitly load the 12 optimization cases for diagnosis and mutation."""
        return get_optimization_cases()

    def load_held_out_cases(self) -> List[ReconciliationCase]:
        """Explicitly load the 8 isolated held-out cases for regression gating."""
        return get_held_out_cases()

    async def run_benchmark(
        self,
        graph: GraphDefinition,
        split: str = "optimization",
        experiment_id: Optional[UUID] = None,
        agent_version_id: Optional[UUID] = None,
        persist: bool = True,
    ) -> ReconciliationRunResult:
        """Execute the agent graph sequentially across cases for the given split.

        Args:
            graph: GraphDefinition architecture to evaluate.
            split: 'optimization' (12 cases) or 'held_out' (8 cases).
            experiment_id: Optional experiment UUID for persistence linking.
            agent_version_id: Optional agent version UUID.
            persist: Whether to store results in repositories if configured.

        Returns:
            ReconciliationRunResult with aggregate and per-case scores.
        """
        if split not in ["optimization", "held_out", "full"]:
            raise ValueError(
                f"Invalid benchmark split '{split}'. Must be 'optimization', 'held_out', or 'full'."
            )

        cases = self.load_domain_cases(split)
        logger.info(
            f"Starting reconciliation benchmark '{BENCHMARK_VERSION}' "
            f"split='{split}' ({len(cases)} cases) on graph '{graph.name}'"
        )

        run_id = uuid4()
        exp_id = experiment_id or uuid4()
        ver_id = agent_version_id or uuid4()

        case_results: List[CaseEvaluationResult] = []
        total_latency_ms = 0
        total_cost_usd = 0.0

        tracer = get_tracer()
        is_held_out = (split == "held_out")

        with tracer.start_span(
            f"benchmark_run.{split}",
            attributes={
                "split": split,
                "experiment_id": str(exp_id),
                "agent_version_id": str(ver_id),
                "total_cases": len(cases),
                "is_held_out": is_held_out,
            },
        ):
            # Sequential in-process deterministic execution
            for case in cases:
                with tracer.start_span(
                    f"benchmark_case.{case.case_code}",
                    attributes={
                        "case_code": case.case_code,
                        "split": split,
                        "is_held_out": is_held_out,
                        "experiment_id": str(exp_id),
                        "agent_version_id": str(ver_id),
                    },
                ) as case_span:
                    # Inputs supplied to execution state
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
                        experiment_id=str(exp_id),
                        agent_version_id=str(ver_id),
                    )

                    # Evaluate execution output against ground truth
                    case_eval = self.evaluator.evaluate_case(case, state)
                    case_results.append(case_eval)
                    case_span.set_attribute("success", case_eval.success)
                    case_span.set_attribute("accuracy", case_eval.accuracy_score)
                    case_span.set_attribute("cost_usd", case_eval.cost_usd)
                    case_span.set_attribute("latency_ms", case_eval.latency_ms)

                    print(
                        f"  [{split}] Case {case.case_code}: success={case_eval.success}, "
                        f"acc={case_eval.accuracy_score * 100:.1f}%, cost=${case_eval.cost_usd:.5f}, "
                        f"lat={case_eval.latency_ms}ms",
                        flush=True,
                    )

                    total_latency_ms += case_eval.latency_ms
                    total_cost_usd += case_eval.cost_usd

        # Calculate aggregates
        total_cases = len(case_results)
        passed_cases = sum(1 for c in case_results if c.success)
        failed_cases = total_cases - passed_cases
        avg_accuracy = (
            sum(c.accuracy_score for c in case_results) / total_cases
            if total_cases > 0
            else 0.0
        )
        reliability = (
            sum(c.reliability_score for c in case_results) / total_cases
            if total_cases > 0
            else 0.0
        )
        avg_latency_ms = int(total_latency_ms / total_cases) if total_cases > 0 else 0

        # Cost labelling (simulated mock vs actual)
        is_mock = isinstance(self.runtime.model_gateway, MockModelGateway)

        run_result = ReconciliationRunResult(
            benchmark_name=BENCHMARK_NAME,
            benchmark_version=BENCHMARK_VERSION,
            split=split,  # type: ignore
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
                "cost_type": "simulated_mock" if is_mock else "estimated",
                "pass_rate": round(passed_cases / total_cases, 4) if total_cases > 0 else 0.0,
                "evaluated_at_ms": total_latency_ms,
            },
        )

        # Optional persistence wiring
        if persist and self.benchmark_run_repo is not None:
            try:
                run_record = run_result.to_db_record(
                    experiment_id=exp_id,
                    agent_version_id=ver_id,
                )
                run_record.id = run_id
                await self.benchmark_run_repo.create(run_record)

                if self.case_execution_repo is not None:
                    for c_res in case_results:
                        case_record_id = uuid4()
                        # If benchmark_case_repo available, look up or create case record
                        if self.benchmark_case_repo is not None:
                            existing_case = await self.benchmark_case_repo.get_by_code(c_res.case_code)
                            if existing_case:
                                case_record_id = existing_case.id
                            else:
                                domain_case = next((c for c in cases if c.case_code == c_res.case_code), None)
                                if domain_case:
                                    created_c = await self.benchmark_case_repo.create(domain_case.to_db_record())
                                    case_record_id = created_c.id

                        exec_record = c_res.to_case_execution_record(
                            benchmark_run_id=run_id,
                            benchmark_case_id=case_record_id,
                            agent_version_id=ver_id,
                        )
                        await self.case_execution_repo.create(exec_record)

                logger.info(f"Persisted benchmark run {run_id} to repository")
            except Exception as e:
                logger.error(f"Failed to persist benchmark run to repository: {e}")

        logger.info(
            f"Reconciliation benchmark completed: accuracy={run_result.accuracy}, "
            f"reliability={run_result.reliability}, passed={run_result.passed_cases}/{total_cases}"
        )
        return run_result

    async def evaluate_run(
        self,
        agent: Union[GraphDefinition, Agent, Any],
        split: str = "optimization",
    ) -> BenchmarkRunResult:
        """Evaluate an agent or graph definition conforming to the core Benchmark interface."""
        if isinstance(agent, GraphDefinition):
            run_result = await self.run_benchmark(agent, split=split, persist=False)
            return run_result.to_benchmark_run_result()
        else:
            raise TypeError(
                f"ReconciliationBenchmark requires a GraphDefinition, got {type(agent).__name__}"
            )
