"""Deterministic Research & Evidence Comparison Benchmark Suite."""

import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from reco.benchmarks.base import DomainBenchmark
from reco.benchmarks.research.dataset import (
    BENCHMARK_NAME,
    BENCHMARK_VERSION,
    get_held_out_cases,
    get_optimization_cases,
    load_cases,
)
from reco.benchmarks.research.evaluator import ResearchEvaluator
from reco.benchmarks.research.models import (
    ResearchCase,
    ResearchCaseEvaluationResult,
    ResearchRunResult,
)
from reco.core.interfaces import BenchmarkCase, Tool
from reco.engine.models import GraphDefinition
from reco.engine.runtime import AgentGraphRuntime
from reco.llm.mock import MockModelGateway
from reco.logging import get_logger
from reco.observability.tracer import get_tracer
from reco.tools.executor import ToolExecutor
from reco.tools.registry import ToolRegistry
from reco.tools.research import register_research_tools

logger = get_logger("benchmarks.research")


class ResearchComparisonBenchmark(DomainBenchmark):
    """Deterministic Research & Evidence-Based Comparison Benchmark Suite (Domain C)."""

    domain_id = "research_comparison"
    display_name = "Research & Evidence Comparison"
    description = "Benchmarks agent capability to synthesize technical documents, resolve contradictory claims, and select optimal architectures under constraints."
    default_goal = "Analyze technical documentation, resolve conflicting claims, and evaluate technologies against specified business constraints."

    def __init__(
        self,
        runtime: Optional[AgentGraphRuntime] = None,
        evaluator: Optional[ResearchEvaluator] = None,
    ):
        if runtime is None:
            registry = ToolRegistry()
            register_research_tools(registry)
            executor = ToolExecutor(registry=registry)
            gateway = MockModelGateway(
                default_content='{"recommendation": "PostgreSQL", "justification": "Provides native ACID compliance and relational schema within budget."}',
                auto_tool_calls=True,
            )
            self.runtime = AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)
        else:
            self.runtime = runtime

        self.evaluator = evaluator or ResearchEvaluator()

    def get_available_tools(self) -> List[Tool]:
        registry = ToolRegistry()
        register_research_tools(registry)
        return registry.list_tools()

    def get_evaluator_requirements(self) -> Dict[str, Any]:
        return {
            "metrics": ["recommendation_accuracy", "fact_coverage", "contradiction_resolution"],
            "expected_output_format": "json_object",
            "schema_requirements": ["recommendation", "justification"],
        }

    def load_cases(self, split: Optional[str] = None) -> List[BenchmarkCase]:
        domain_cases = load_cases(split)
        return [c.to_benchmark_case() for c in domain_cases]

    def load_domain_cases(self, split: Optional[str] = None) -> List[ResearchCase]:
        return load_cases(split)

    async def run_benchmark(
        self,
        graph: GraphDefinition,
        split: str = "optimization",
        experiment_id: Optional[UUID] = None,
        agent_version_id: Optional[UUID] = None,
        persist: bool = False,
    ) -> ResearchRunResult:
        cases = self.load_domain_cases(split)
        case_results: List[ResearchCaseEvaluationResult] = []

        tracer = get_tracer()
        with tracer.start_span(
            f"research_benchmark.{split}",
            attributes={
                "domain": "research_comparison",
                "split": split,
                "cases_count": len(cases),
                "graph_name": graph.name,
            },
        ):
            for case in cases:
                state = await self.runtime.run(
                    graph=graph,
                    inputs={
                        "task_goal": case.task_goal,
                        "constraints": case.constraints,
                        "candidate_technologies": case.candidate_technologies,
                        "documents": [d.model_dump(mode="json") for d in case.documents],
                    },
                    goal=f"Evaluate technology options for scenario {case.case_code}: {case.task_goal}",
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
