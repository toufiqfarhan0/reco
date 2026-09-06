"""Base abstractions and registry for domain benchmarks in Reco."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from reco.core.interfaces import Benchmark, Tool
from reco.engine.models import GraphDefinition
from reco.evaluators.scorecard import Scorecard


class DomainBenchmark(Benchmark, ABC):
    """Generic base class for all Reco domain benchmarks."""

    domain_id: str
    display_name: str
    description: str
    default_goal: str

    @abstractmethod
    def get_available_tools(self) -> List[Tool]:
        """Return the complete list of tools authorized for this domain."""
        pass

    @abstractmethod
    def get_evaluator_requirements(self) -> Dict[str, Any]:
        """Return the evaluator requirements and success criteria for this domain."""
        pass

    @abstractmethod
    async def run_benchmark(
        self,
        graph: GraphDefinition,
        split: str = "optimization",
        experiment_id: Optional[UUID] = None,
        agent_version_id: Optional[UUID] = None,
        persist: bool = True,
    ) -> Any:
        """Execute the agent graph across scenarios in the specified split."""
        pass

    async def evaluate_run(
        self,
        agent: Any,
        split: str = "optimization",
    ) -> Any:
        """Evaluate an agent conforming to the core Benchmark interface."""
        if isinstance(agent, GraphDefinition):
            return await self.run_benchmark(agent, split=split, persist=False)
        raise TypeError(f"Domain benchmark requires a GraphDefinition, got {type(agent).__name__}")

    def __call__(self) -> "DomainBenchmark":
        """Support both Registry.get(id) and Registry.get(id)()."""
        return self


class BenchmarkRegistry:
    """Registry maintaining active domain benchmarks across Reco."""

    _benchmarks: Dict[str, Type[DomainBenchmark]] = {}
    _instances: Dict[str, DomainBenchmark] = {}

    @classmethod
    def register(cls, domain_id: str, benchmark_cls: Type[DomainBenchmark]) -> None:
        """Register a domain benchmark class."""
        cls._benchmarks[domain_id.lower()] = benchmark_cls

    @classmethod
    def get_class(cls, domain_id: str) -> Type[DomainBenchmark]:
        """Retrieve the registered domain benchmark class."""
        domain_key = domain_id.lower()
        if domain_key not in cls._benchmarks:
            available = list(cls._benchmarks.keys())
            raise KeyError(f"Domain benchmark '{domain_id}' not found in registry. Available: {available}")
        return cls._benchmarks[domain_key]

    @classmethod
    def get(cls, domain_id: str, **kwargs: Any) -> DomainBenchmark:
        """Retrieve or instantiate a registered domain benchmark."""
        domain_key = domain_id.lower()
        if domain_key not in cls._benchmarks:
            available = list(cls._benchmarks.keys())
            raise KeyError(f"Domain benchmark '{domain_id}' not found in registry. Available: {available}")
        
        # If kwargs provided, create fresh instance
        if kwargs:
            return cls._benchmarks[domain_key](**kwargs)
        
        # Otherwise singleton cache
        if domain_key not in cls._instances:
            cls._instances[domain_key] = cls._benchmarks[domain_key]()
        return cls._instances[domain_key]

    @classmethod
    def list_domains(cls) -> List[Dict[str, Any]]:
        """List metadata for all registered domain benchmarks."""
        result = []
        for d_id, b_cls in cls._benchmarks.items():
            result.append({
                "domain_id": d_id,
                "display_name": getattr(b_cls, "display_name", d_id.replace("_", " ").title()),
                "description": getattr(b_cls, "description", ""),
                "default_goal": getattr(b_cls, "default_goal", ""),
            })
        return result

    @classmethod
    def clear(cls) -> None:
        """Clear registry instances."""
        cls._instances.clear()
