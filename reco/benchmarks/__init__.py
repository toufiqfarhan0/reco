"""Benchmark suites and evaluation datasets across multiple domains (Reconciliation, Anomaly, Research)."""

from reco.benchmarks.base import BenchmarkRegistry, DomainBenchmark
from reco.benchmarks.reconciliation import (
    BENCHMARK_NAME,
    BENCHMARK_VERSION,
    CaseEvaluationResult,
    ExpectedMatchPair,
    ReconciliationBenchmark,
    ReconciliationCase,
    ReconciliationEvaluator,
    ReconciliationGroundTruth,
    ReconciliationRunResult,
    create_reconciliation_baseline_graph,
    get_case_by_code,
    get_held_out_cases,
    get_optimization_cases,
    load_cases,
)
from reco.benchmarks.anomaly.benchmark import AnomalyDetectionBenchmark
from reco.benchmarks.anomaly.evaluator import AnomalyEvaluator
from reco.benchmarks.anomaly.models import AnomalyCase, AnomalyCaseEvaluationResult, AnomalyRunResult
from reco.benchmarks.research.benchmark import ResearchComparisonBenchmark
from reco.benchmarks.research.evaluator import ResearchEvaluator
from reco.benchmarks.research.models import ResearchCase, ResearchCaseEvaluationResult, ResearchRunResult

# Register domain benchmarks into central BenchmarkRegistry
BenchmarkRegistry.register("reconciliation", ReconciliationBenchmark)
BenchmarkRegistry.register("anomaly_detection", AnomalyDetectionBenchmark)
BenchmarkRegistry.register("research_comparison", ResearchComparisonBenchmark)

__all__ = [
    "BenchmarkRegistry",
    "DomainBenchmark",
    "BENCHMARK_NAME",
    "BENCHMARK_VERSION",
    "ExpectedMatchPair",
    "ReconciliationGroundTruth",
    "ReconciliationCase",
    "CaseEvaluationResult",
    "ReconciliationRunResult",
    "load_cases",
    "get_optimization_cases",
    "get_held_out_cases",
    "get_case_by_code",
    "ReconciliationEvaluator",
    "create_reconciliation_baseline_graph",
    "ReconciliationBenchmark",
    # Domain B: Anomaly Detection
    "AnomalyDetectionBenchmark",
    "AnomalyEvaluator",
    "AnomalyCase",
    "AnomalyCaseEvaluationResult",
    "AnomalyRunResult",
    # Domain C: Research Comparison
    "ResearchComparisonBenchmark",
    "ResearchEvaluator",
    "ResearchCase",
    "ResearchCaseEvaluationResult",
    "ResearchRunResult",
]
