"""Model-driven reconciliation architecture for autonomous agent execution."""

from reco.engine.models import EdgeModel, GraphDefinition, NodeModel


def create_model_driven_reconciliation_graph() -> GraphDefinition:
    """Construct a model-driven reconciliation graph where nodes autonomously decide tool invocations."""
    nodes = {
        "parse_statement": NodeModel(
            node_id="parse_statement",
            name="Bank Statement Parser",
            role="Extractor",
            system_prompt=(
                "You are an autonomous banking data extractor. When raw statements are provided, "
                "invoke parse_bank_statement to produce structured, normalized transaction objects."
            ),
            tools=["parse_bank_statement"],
            input_mapping={"records": "bank_records"},
            output_key="parsed_bank",
            metadata={"execution_mode": "model_driven", "max_tool_rounds": 3, "stage": "ingestion"},
        ),
        "query_ledger": NodeModel(
            node_id="query_ledger",
            name="General Ledger Reader",
            role="DatabaseQuerier",
            system_prompt=(
                "You are a general ledger reader agent. When raw ledger entries are present in context, "
                "invoke query_general_ledger to validate and filter relevant journal entries."
            ),
            tools=["query_general_ledger"],
            input_mapping={"entries": "ledger_entries"},
            output_key="queried_ledger",
            metadata={"execution_mode": "model_driven", "max_tool_rounds": 3, "stage": "ingestion"},
        ),
        "fuzzy_match": NodeModel(
            node_id="fuzzy_match",
            name="Reconciliation Matcher",
            role="Matcher",
            system_prompt=(
                "You are an autonomous financial reconciliation agent. Inspect the parsed bank transactions "
                "and ledger entries from upstream nodes. Formulate tool arguments and call fuzzy_match_transactions "
                "to correlate matching pairs and classify discrepancies. Finally, provide a structured summary."
            ),
            tools=["fuzzy_match_transactions"],
            input_mapping={
                "bank_transactions": "parsed_bank.transactions",
                "ledger_entries": "queried_ledger.entries",
            },
            output_key="reconciliation_summary",
            metadata={"execution_mode": "model_driven", "max_tool_rounds": 3, "stage": "matching"},
        ),
        "verify_summary": NodeModel(
            node_id="verify_summary",
            name="Reconciliation Verifier",
            role="Auditor",
            system_prompt=(
                "You are an independent reconciliation auditor. Review the matching output from fuzzy_match. "
                "Verify that all calculated variances match expected totals. If there are fee or FX variances, "
                "call calculate_reconciliation_difference. Emit the final verified reconciliation payload."
            ),
            tools=["calculate_reconciliation_difference"],
            input_mapping={"reconciliation_summary": "reconciliation_summary"},
            output_key="verified_reconciliation",
            metadata={"execution_mode": "model_driven", "max_tool_rounds": 3, "stage": "verification"},
        ),
    }

    edges = [
        EdgeModel(source_node_id="parse_statement", target_node_id="query_ledger"),
        EdgeModel(source_node_id="query_ledger", target_node_id="fuzzy_match"),
        EdgeModel(source_node_id="fuzzy_match", target_node_id="verify_summary"),
    ]

    graph = GraphDefinition(
        graph_id="arch-reconciliation-model-driven-v1",
        name="Model-Driven Autonomous Reconciliation Architecture",
        entry_node_id="parse_statement",
        terminal_node_ids=["verify_summary"],
        nodes=nodes,
        edges=edges,
        metadata={
            "generation_method": "model_driven",
            "version": "v1-model-driven",
            "benchmark_target": "reconciliation-v1",
            "description": "Multi-agent model-driven architecture with autonomous tool dispatch",
        },
    )

    graph.validate_graph()
    return graph
