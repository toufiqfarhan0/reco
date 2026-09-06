"""Deterministic Dataset Anomaly Detection Benchmark Suite."""

import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from reco.benchmarks.anomaly.dataset import (
    BENCHMARK_NAME,
    BENCHMARK_VERSION,
    get_held_out_cases,
    get_optimization_cases,
    load_cases,
)
from reco.benchmarks.anomaly.evaluator import AnomalyEvaluator
from reco.benchmarks.anomaly.models import (
    AnomalyCase,
    AnomalyCaseEvaluationResult,
    AnomalyRunResult,
)
from reco.benchmarks.base import DomainBenchmark
from reco.core.interfaces import BenchmarkCase, Tool
from reco.engine.models import GraphDefinition
from reco.engine.runtime import AgentGraphRuntime
from reco.llm.mock import MockModelGateway
from reco.logging import get_logger
from reco.observability.tracer import get_tracer
from reco.tools.anomaly import register_anomaly_tools
from reco.tools.executor import ToolExecutor
from reco.tools.registry import ToolRegistry

logger = get_logger("benchmarks.anomaly")


class AnomalyDetectionBenchmark(DomainBenchmark):
    """Deterministic tabular anomaly detection benchmark suite (Domain B)."""

    domain_id = "anomaly_detection"
    display_name = "Dataset Anomaly Detection"
    description = "Benchmarks agent capability to detect numerical, temporal, and categorical anomalies in tabular data."
    default_goal = "Analyze the tabular dataset, compute statistical distributions, and detect all anomalous records."

    def __init__(
        self,
        runtime: Optional[AgentGraphRuntime] = None,
        evaluator: Optional[AnomalyEvaluator] = None,
    ):
        if runtime is None:
            registry = ToolRegistry()
            register_anomaly_tools(registry)
            executor = ToolExecutor(registry=registry)
            gateway = MockModelGateway(
                default_content='{"anomalies": []}',
                auto_tool_calls=True,
            )
            self.runtime = AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)
        else:
            self.runtime = runtime

        self.evaluator = evaluator or AnomalyEvaluator()

    def get_available_tools(self) -> List[Tool]:
        registry = ToolRegistry()
        register_anomaly_tools(registry)
        return registry.list_tools()

    def get_evaluator_requirements(self) -> Dict[str, Any]:
        return {
            "metrics": ["f1_score", "precision", "recall", "accuracy"],
            "expected_output_format": "json_object",
            "schema_requirements": ["anomalies"],
        }

    def load_cases(self, split: Optional[str] = None) -> List[BenchmarkCase]:
        domain_cases = load_cases(split)
        return [c.to_benchmark_case() for c in domain_cases]

    def load_domain_cases(self, split: Optional[str] = None) -> List[AnomalyCase]:
        return load_cases(split)

    async def run_benchmark(
        self,
        graph: GraphDefinition,
        split: str = "optimization",
        experiment_id: Optional[UUID] = None,
        agent_version_id: Optional[UUID] = None,
        persist: bool = False,
    ) -> AnomalyRunResult:
        cases = self.load_domain_cases(split)
        case_results: List[AnomalyCaseEvaluationResult] = []

        tracer = get_tracer()
        with tracer.start_span(
            f"anomaly_benchmark.{split}",
            attributes={
                "domain": "anomaly_detection",
                "split": split,
                "cases_count": len(cases),
                "graph_name": graph.name,
            },
        ):
            for case in cases:
                state = await self.runtime.run(
                    graph=graph,
                    inputs={"dataset": case.dataset},
                    goal=f"Detect anomalies in dataset scenario {case.case_code}",
                    experiment_id=str(experiment_id) if experiment_id else None,
                    agent_version_id=str(agent_version_id) if agent_version_id else None,
                )
                case_res = self.evaluator.evaluate_case(case, state)
                case_results.append(case_res)

        return self.evaluator.compute_run_result(
            case_results=case_results,
            split=split,
            version=graph.metadata.get("version", "V0"),
            cost_type="simulated_mock" if isinstance(self.runtime.model_gateway, MockModelGateway) else "actual_live",
        )
