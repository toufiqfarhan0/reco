"""Baseline agent architecture for the anomaly detection benchmark.

Synthesized autonomously via Reco's GoalAnalyzer + ArchitectureGenerator
and exported for baseline evaluation.
"""

from reco.engine.models import EdgeModel, GraphDefinition, NodeModel


def create_anomaly_baseline_graph() -> GraphDefinition:
    """Construct canonical 3-node anomaly detection architecture."""
    nodes = {
        "dataset_reader": NodeModel(
            node_id="dataset_reader",
            name="Tabular Ingestion Worker",
            role="Worker",
            system_prompt="Read and parse the tabular dataset records with typed schemas.",
            tools=["read_tabular_dataset"],
            input_mapping={"dataset": "dataset"},
            output_key="parsed_dataset",
            execution_mode="deterministic_tool",
            metadata={"stage": "ingestion"},
        ),
        "statistical_analyzer": NodeModel(
            node_id="statistical_analyzer",
            name="Statistical & Distribution Processor",
            role="AnalyticalProcessor",
            system_prompt="Calculate distribution moments, percentiles, and statistical anomaly scores across numeric and categorical features.",
            tools=["detect_distribution_anomalies"],
            input_mapping={"dataset": "dataset"},
            output_key="anomaly_candidates",
            execution_mode="deterministic_tool",
            metadata={"stage": "analysis"},
        ),
        "anomaly_auditor": NodeModel(
            node_id="anomaly_auditor",
            name="Anomaly Classification Auditor",
            role="Auditor",
            system_prompt="Review candidate distribution anomalies. Flag any record that has an extreme statistical outlier value. Respond concisely in JSON format with 'flagged_anomaly_ids' (list of record IDs) and 'explanations' (list of strings).",
            tools=[],
            input_mapping={"candidates": "anomaly_candidates", "dataset": "dataset"},
            output_key="final_anomaly_report",
            execution_mode="model_driven",
            metadata={"stage": "classification"},
        ),
    }

    edges = [
        EdgeModel(source_node_id="dataset_reader", target_node_id="statistical_analyzer"),
        EdgeModel(source_node_id="statistical_analyzer", target_node_id="anomaly_auditor"),
    ]

    return GraphDefinition(
        graph_id="graph_anomaly_baseline_v0",
        name="Tabular Anomaly Detection Baseline (V0)",
        description="Autonomous 3-node DAG pipeline for tabular anomaly identification.",
        entry_node_id="dataset_reader",
        nodes=nodes,
        edges=edges,
        metadata={
            "generation_method": "autonomous_synthesis",
            "domain": "anomaly_detection",
            "version": "V0",
        },
    )
