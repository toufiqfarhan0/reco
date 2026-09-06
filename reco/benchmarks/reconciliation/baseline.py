"""Manual baseline agent architecture (V0) for the reconciliation benchmark.

This establishes the pre-optimization performance watermark for comparison.
Tagged explicitly with generation_method = "manual_baseline".
"""

from typing import Any, Dict
from reco.engine.models import EdgeModel, GraphDefinition, NodeModel


def create_reconciliation_baseline_graph() -> GraphDefinition:
    """Construct the canonical manual 4-node baseline reconciliation architecture.

    DAG Pipeline:
      1. parse_statement (parse_bank_statement)
         -> 2. query_ledger (query_general_ledger)
            -> 3. fuzzy_match (fuzzy_match_transactions)
               -> 4. verify_summary (reconciliation_verifier)
    """
    nodes = {
        "parse_statement": NodeModel(
            node_id="parse_statement",
            name="Bank Statement Parser",
            role="Extractor",
            system_prompt="Normalize and validate raw bank statement records with exact Decimal precision.",
            tools=["parse_bank_statement"],
            input_mapping={"records": "bank_records"},
            output_key="parsed_bank",
            execution_mode="deterministic_tool",
            metadata={"stage": "ingestion"},
        ),
        "query_ledger": NodeModel(
            node_id="query_ledger",
            name="General Ledger Reader",
            role="DatabaseQuerier",
            system_prompt="Extract and validate general ledger entries for the target reconciliation account and period.",
            tools=["query_general_ledger"],
            input_mapping={"entries": "ledger_entries"},
            output_key="queried_ledger",
            execution_mode="deterministic_tool",
            metadata={"stage": "ingestion"},
        ),
        "fuzzy_match": NodeModel(
            node_id="fuzzy_match",
            name="Reconciliation Matcher",
            role="Matcher",
            system_prompt="Match bank transactions against general ledger entries and identify discrepancies.",
            tools=["fuzzy_match_transactions"],
            input_mapping={
                "bank_transactions": "parsed_bank.transactions",
                "ledger_entries": "queried_ledger.entries",
            },
            output_key="reconciliation_summary",
            execution_mode="model_driven",
            metadata={"stage": "matching"},
        ),
        "verify_summary": NodeModel(
            node_id="verify_summary",
            name="Reconciliation Verifier",
            role="Auditor",
            system_prompt="Perform final verification of matched pairs, exception categorizations, and variance calculations.",
            tools=[],
            input_mapping={"reconciliation_summary": "reconciliation_summary"},
            output_key="verified_reconciliation",
            execution_mode="model_inference",
            metadata={"stage": "verification"},
        ),
    }

    edges = [
        EdgeModel(source_node_id="parse_statement", target_node_id="query_ledger"),
        EdgeModel(source_node_id="query_ledger", target_node_id="fuzzy_match"),
        EdgeModel(source_node_id="fuzzy_match", target_node_id="verify_summary"),
    ]

    graph = GraphDefinition(
        graph_id="arch-reconciliation-baseline-v0",
        name="Manual Baseline Reconciliation Architecture V0",
        entry_node_id="parse_statement",
        terminal_node_ids=["verify_summary"],
        nodes=nodes,
        edges=edges,
        metadata={
            "generation_method": "manual_baseline",
            "version": "v0",
            "benchmark_target": "reconciliation-v1",
            "description": "Deterministic manual 4-stage pipeline for baseline performance benchmarking",
        },
    )

    graph.validate_graph()
    return graph
