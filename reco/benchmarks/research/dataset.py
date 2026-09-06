"""Multi-case benchmark dataset for Research Synthesis.

Strictly split into 6 optimization cases and 4 held-out cases with zero cross-split leakage.
Covers:
- Document extraction (AI models, datasets, metrics, organizations, methods)
- Metric cross-referencing (relative deltas, leaderboard leaders, baseline comparison)
- Multi-source summary (topical coverage, key points synthesis)
- Contradiction and discrepancy detection across reports
"""

from __future__ import annotations

from typing import List
from reco.benchmarks.base import BenchmarkCase, BenchmarkSplit, BenchmarkSuite


def create_research_benchmark_cases() -> List[BenchmarkCase]:
    """Instantiate the 10 canonical benchmark test cases for research synthesis."""
    cases: List[BenchmarkCase] = []

    # =========================================================================
    # OPTIMIZATION SPLIT (6 Cases)
    # =========================================================================

    # 1. AI Entity Extraction from Research Abstract
    cases.append(BenchmarkCase(
        case_id="rsch_opt_001_entity_extraction",
        name="Research Abstract AI Entity Extraction",
        description="Extract recognized AI models, benchmarks, and organizations from a paper abstract.",
        category="document_extraction",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "text": "We evaluate GLM-4.7-Flash released by Zhipu AI on the SWE-bench verified benchmark for software engineering tasks, observing significant accuracy and latency improvements."
        },
        expected_output={
            "status": "extracted",
            "entities": {
                "models": ["GLM-4.7-Flash"],
                "datasets": ["SWE-bench"],
                "metrics": ["Accuracy", "Latency"],
                "organizations": ["Zhipu AI"]
            }
        },
        metadata={"difficulty": "easy", "domain": "research_synthesis", "split_target": "optimization"}
    ))

    # 2. Quantitative Metric Comparison of Two Models
    cases.append(BenchmarkCase(
        case_id="rsch_opt_002_model_metric_comparison",
        name="Quantitative Comparison of Two Agent Models",
        description="Cross-reference accuracy and latency across two models to determine leaderboard leaders.",
        category="metric_cross_referencing",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "sources": {
                "Model_Alpha": {"accuracy": 82.5, "latency_ms": 110.0},
                "Model_Beta": {"accuracy": 89.0, "latency_ms": 85.0}
            },
            "baseline": "Model_Alpha"
        },
        expected_output={
            "status": "comparison_complete",
            "leaders": {"accuracy": "Model_Beta", "latency_ms": "Model_Beta"},
            "baseline": "Model_Alpha"
        },
        metadata={"difficulty": "easy", "domain": "research_synthesis", "split_target": "optimization"}
    ))

    # 3. Multi-Document Architectural Research Synthesis
    cases.append(BenchmarkCase(
        case_id="rsch_opt_003_multi_document_summary",
        name="Multi-Document Architectural Research Synthesis",
        description="Consolidate findings across multiple technical papers into an executive synthesis.",
        category="multi_source_summary",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "text": {
                "paper_1": "Autonomous agent engineering systems iteratively mutate DAG architectures. Scorecard evaluation proves Pareto dominance across accuracy and latency.",
                "paper_2": "Failure diagnostics classify root causes into taxonomy categories. Mutators apply targeted remedies to resolve tool selection and schema violations."
            },
            "focus_topics": ["autonomous agent", "failure diagnostics"]
        },
        expected_output={
            "status": "summarized",
            "topics_covered": ["autonomous agent", "failure diagnostics"],
            "source_count": 2
        },
        metadata={"difficulty": "medium", "domain": "research_synthesis", "split_target": "optimization"}
    ))

    # 4. Cross-Document Accuracy Discrepancy Detection
    cases.append(BenchmarkCase(
        case_id="rsch_opt_004_accuracy_contradiction_detection",
        name="Cross-Document Discrepancy Detection",
        description="Flag divergent accuracy claims reported in main paper text versus appendix tables.",
        category="contradiction_detection",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "sources": {
                "Paper_Main": {"accuracy": 94.5},
                "Appendix_Table": {"accuracy": 89.2}
            },
            "baseline": "Paper_Main"
        },
        expected_output={
            "status": "comparison_complete",
            "leaders": {"accuracy": "Paper_Main"}
        },
        metadata={"difficulty": "medium", "domain": "research_synthesis", "split_target": "optimization"}
    ))

    # 5. Method, Dataset, and Organization Extraction
    cases.append(BenchmarkCase(
        case_id="rsch_opt_005_method_and_dataset_extraction",
        name="Deep Learning Survey Entity Extraction",
        description="Isolate deep learning techniques (MoE, LoRA, RLHF) and benchmark datasets.",
        category="document_extraction",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "text": "Survey on OpenAI and Meta training techniques utilizing MoE, LoRA, and RLHF on MMLU and GSM8K benchmarks."
        },
        expected_output={
            "status": "extracted",
            "entities": {
                "datasets": ["MMLU", "GSM8K"],
                "organizations": ["OpenAI", "Meta"],
                "methods": ["MoE", "LoRA", "RLHF"]
            }
        },
        metadata={"difficulty": "medium", "domain": "research_synthesis", "split_target": "optimization"}
    ))

    # 6. Three-Model Leaderboard Comparison Matrix
    cases.append(BenchmarkCase(
        case_id="rsch_opt_006_three_way_leaderboard_comparison",
        name="Three-Model Leaderboard Comparison",
        description="Evaluate trade-offs across 3 candidate agent generations on accuracy and cost.",
        category="metric_cross_referencing",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "sources": {
                "Agent_V0": {"accuracy": 83.3, "cost_usd": 0.01},
                "Agent_V1": {"accuracy": 100.0, "cost_usd": 0.012},
                "Agent_V2": {"accuracy": 100.0, "cost_usd": 0.009}
            },
            "baseline": "Agent_V0"
        },
        expected_output={
            "status": "comparison_complete",
            "leaders": {"accuracy": "Agent_V1", "cost_usd": "Agent_V2"}
        },
        metadata={"difficulty": "hard", "domain": "research_synthesis", "split_target": "optimization"}
    ))

    # =========================================================================
    # HELD-OUT SPLIT (4 Cases)
    # =========================================================================

    # 7. Held-Out SWE-bench Evaluation Extraction
    cases.append(BenchmarkCase(
        case_id="rsch_held_001_swe_bench_evaluation_extraction",
        name="Held-Out SWE-bench Evaluation Extraction",
        description="Air-gapped verification of entity extraction on frontier coding models.",
        category="document_extraction",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "text": "Evaluating DeepSeek-R1 and Claude 3.5 Sonnet on SWE-bench for bug resolution accuracy."
        },
        expected_output={
            "status": "extracted",
            "entities": {
                "models": ["DeepSeek-R1", "Claude 3.5 Sonnet"],
                "datasets": ["SWE-bench"],
                "metrics": ["Accuracy"]
            }
        },
        metadata={"difficulty": "medium", "domain": "research_synthesis", "split_target": "held-out"}
    ))

    # 8. Held-Out Throughput and Latency Matrix
    cases.append(BenchmarkCase(
        case_id="rsch_held_002_throughput_latency_matrix",
        name="Held-Out Throughput and Latency Matrix",
        description="Air-gapped verification identifying Engine_B as throughput and latency leader.",
        category="metric_cross_referencing",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "sources": {
                "Engine_A": {"throughput": 450.0, "latency_ms": 12.0},
                "Engine_B": {"throughput": 620.0, "latency_ms": 9.5}
            },
            "baseline": "Engine_A"
        },
        expected_output={
            "status": "comparison_complete",
            "leaders": {"throughput": "Engine_B", "latency_ms": "Engine_B"}
        },
        metadata={"difficulty": "medium", "domain": "research_synthesis", "split_target": "held-out"}
    ))

    # 9. Held-Out Multi-Source Technical Synthesis
    cases.append(BenchmarkCase(
        case_id="rsch_held_003_multisource_technical_synthesis",
        name="Held-Out Multi-Source Technical Synthesis",
        description="Air-gapped verification of multi-document topic coverage and summary synthesis.",
        category="multi_source_summary",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "text": [
                "Cloud benchmark reports state GLM-4.7-Flash achieves lowest time-to-first-token.",
                "Developer feedback notes superior tool calling precision on complex nested schemas."
            ],
            "focus_topics": ["tool calling", "latency"]
        },
        expected_output={
            "status": "summarized",
            "topics_covered": ["tool calling", "latency"],
            "source_count": 2
        },
        metadata={"difficulty": "medium", "domain": "research_synthesis", "split_target": "held-out"}
    ))

    # 10. Held-Out Divergent Benchmark Audit
    cases.append(BenchmarkCase(
        case_id="rsch_held_004_divergent_benchmark_audit",
        name="Held-Out Divergent Benchmark Audit",
        description="Air-gapped verification of longitudinal report score progression.",
        category="contradiction_detection",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "sources": {
                "Report_2026_Q1": {"f1_score": 0.91},
                "Report_2026_Q2": {"f1_score": 0.95}
            },
            "baseline": "Report_2026_Q1"
        },
        expected_output={
            "status": "comparison_complete",
            "leaders": {"f1_score": "Report_2026_Q2"}
        },
        metadata={"difficulty": "easy", "domain": "research_synthesis", "split_target": "held-out"}
    ))

    return cases


def get_research_benchmark_suite() -> BenchmarkSuite:
    """Build and validate the standard 10-case research synthesis benchmark suite."""
    cases = create_research_benchmark_cases()
    suite = BenchmarkSuite(
        name="research_synthesis_benchmark_v1",
        description="Standard 10-case research synthesis benchmark partitioned 6/4 (opt/held-out).",
        cases=cases
    )
    # Strictly validate partition isolation
    suite.validate_partition_isolation()
    return suite
