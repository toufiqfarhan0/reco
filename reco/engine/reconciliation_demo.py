"""Deterministic reconciliation architecture demo wiring existing tools into an executable graph."""

from typing import Any, Dict
from reco.engine.models import EdgeModel, GraphDefinition, NodeModel
from reco.engine.runtime import AgentGraphRuntime
from reco.engine.state import ExecutionState
from reco.llm.mock import MockModelGateway
from reco.tools.executor import ToolExecutor
from reco.tools.reconciliation import register_reconciliation_tools
from reco.tools.registry import ToolRegistry


def create_reconciliation_demo_graph() -> GraphDefinition:
    """Create a deterministic 2-node reconciliation workflow DAG."""
    nodes = {
        "statement_parser": NodeModel(
            node_id="statement_parser",
            name="Bank Statement Parser",
            role="Normalizer",
            system_prompt="Normalize raw bank records into standard format.",
            tools=["parse_bank_statement"],
            input_mapping={"records": "raw_statement"},
            output_key="parsed_statement",
        ),
        "transaction_matcher": NodeModel(
            node_id="transaction_matcher",
            name="Transaction Matcher",
            role="Auditor",
            system_prompt="Match bank transactions against general ledger records.",
            tools=["fuzzy_match_transactions"],
            input_mapping={
                "bank_transactions": "parsed_statement",
                "ledger_entries": "ledger_entries",
            },
            output_key="reconciliation_summary",
        ),
    }

    edges = [
        EdgeModel(source_node_id="statement_parser", target_node_id="transaction_matcher")
    ]

    return GraphDefinition(
        graph_id="reconciliation_demo_v0",
        name="Deterministic Reconciliation Demo Graph",
        entry_node_id="statement_parser",
        terminal_node_ids=["transaction_matcher"],
        nodes=nodes,
        edges=edges,
    )


async def run_reconciliation_demo(
    raw_statement: list,
    ledger_entries: list,
    goal: str = "Reconcile monthly bank statement",
) -> ExecutionState:
    """Execute the demonstration reconciliation graph deterministically."""
    registry = ToolRegistry()
    register_reconciliation_tools(registry)
    executor = ToolExecutor(registry=registry)
    gateway = MockModelGateway()

    runtime = AgentGraphRuntime(model_gateway=gateway, tool_executor=executor)
    graph = create_reconciliation_demo_graph()

    inputs = {
        "raw_statement": raw_statement,
        "ledger_entries": ledger_entries,
    }

    return await runtime.run(graph=graph, inputs=inputs, goal=goal)
