"""Tool catalog, parameter validation, and multi-domain tool implementations."""

from reco.tools.executor import ToolExecutor
from reco.tools.reconciliation import (
    BankTransaction,
    CalculateDifferenceTool,
    FuzzyMatchTransactionsTool,
    LedgerEntry,
    MatchCandidate,
    ParseBankStatementTool,
    QueryGeneralLedgerTool,
    ReconciliationDifference,
    ReconciliationSummary,
    register_reconciliation_tools,
)
from reco.tools.anomaly import (
    ReadTabularDatasetTool,
    ComputeStatisticalSummaryTool,
    DetectDistributionAnomaliesTool,
    register_anomaly_tools,
)
from reco.tools.research import (
    SearchDocumentEvidenceTool,
    ExtractEvidenceClaimsTool,
    CompareTechnologyMetricsTool,
    register_research_tools,
)
from reco.tools.registry import ToolRegistry, default_tool_registry

__all__ = [
    "ToolRegistry",
    "default_tool_registry",
    "ToolExecutor",
    # Reconciliation tools
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
    # Anomaly detection tools
    "ReadTabularDatasetTool",
    "ComputeStatisticalSummaryTool",
    "DetectDistributionAnomaliesTool",
    "register_anomaly_tools",
    # Research comparison tools
    "SearchDocumentEvidenceTool",
    "ExtractEvidenceClaimsTool",
    "CompareTechnologyMetricsTool",
    "register_research_tools",
]

# Ensure default_tool_registry contains tools for all 3 domains
def _init_default_registry():
    existing_names = {t.name for t in default_tool_registry.list_tools()}
    if not any("bank" in name for name in existing_names):
        register_reconciliation_tools(default_tool_registry)
    if not any("tabular" in name or "anomal" in name for name in existing_names):
        register_anomaly_tools(default_tool_registry)
    if not any("document" in name or "evidence" in name for name in existing_names):
        register_research_tools(default_tool_registry)

_init_default_registry()
