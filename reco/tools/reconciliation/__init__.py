"""Financial reconciliation domain tool pack."""

from reco.tools.reconciliation.calc_difference import CalculateDifferenceTool
from reco.tools.reconciliation.match_transactions import FuzzyMatchTransactionsTool
from reco.tools.reconciliation.models import (
    BankTransaction,
    LedgerEntry,
    MatchCandidate,
    ReconciliationDifference,
    ReconciliationSummary,
)
from reco.tools.reconciliation.parse_statement import ParseBankStatementTool
from reco.tools.reconciliation.query_ledger import QueryGeneralLedgerTool
from reco.tools.registry import ToolRegistry


def register_reconciliation_tools(registry: ToolRegistry) -> None:
    """Register all 4 core reconciliation tools into the provided ToolRegistry."""
    registry.register(ParseBankStatementTool())
    registry.register(QueryGeneralLedgerTool())
    registry.register(CalculateDifferenceTool())
    registry.register(FuzzyMatchTransactionsTool())


__all__ = [
    "BankTransaction",
    "LedgerEntry",
    "ReconciliationDifference",
    "MatchCandidate",
    "ReconciliationSummary",
    "ParseBankStatementTool",
    "QueryGeneralLedgerTool",
    "CalculateDifferenceTool",
    "FuzzyMatchTransactionsTool",
    "register_reconciliation_tools",
]
