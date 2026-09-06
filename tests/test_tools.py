"""Comprehensive tests for the Generic Tool System and Reconciliation Tool Pack."""

import asyncio
from decimal import Decimal
from typing import Any, Dict
import pytest

from reco.core.interfaces import Tool, ToolResult
from reco.tools.executor import ToolExecutor
from reco.tools.reconciliation import (
    CalculateDifferenceTool,
    FuzzyMatchTransactionsTool,
    ParseBankStatementTool,
    QueryGeneralLedgerTool,
    register_reconciliation_tools,
)
from reco.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Mock Tool for Generic Testing
# ---------------------------------------------------------------------------

class MockCalculatorTool(Tool):
    @property
    def name(self) -> str:
        return "mock_multiplier"

    @property
    def description(self) -> str:
        return "Multiplies two numbers."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["x", "y"],
            "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
        }

    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if "x" not in arguments or "y" not in arguments:
            raise ValueError("Arguments 'x' and 'y' are required")
        return {"x": float(arguments["x"]), "y": float(arguments["y"])}

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        product = arguments["x"] * arguments["y"]
        return ToolResult(success=True, data={"product": product})


@pytest.fixture
def registry() -> ToolRegistry:
    """Provide a clean isolated tool registry."""
    reg = ToolRegistry()
    reg.clear()
    return reg


@pytest.fixture
def executor(registry: ToolRegistry) -> ToolExecutor:
    """Provide a ToolExecutor wired to the isolated test registry."""
    return ToolExecutor(registry=registry)


# ---------------------------------------------------------------------------
# Part 1: Generic Tool System Tests (1-9)
# ---------------------------------------------------------------------------

def test_1_register_tool(registry: ToolRegistry):
    """Test 1: Register tool."""
    tool = MockCalculatorTool()
    registry.register(tool)
    assert registry.has("mock_multiplier")


def test_2_retrieve_tool(registry: ToolRegistry):
    """Test 2: Retrieve tool by name."""
    tool = MockCalculatorTool()
    registry.register(tool)
    retrieved = registry.get("mock_multiplier")
    assert retrieved is not None
    assert retrieved.name == "mock_multiplier"
    assert retrieved.description == "Multiplies two numbers."


def test_3_list_tools_and_schemas(registry: ToolRegistry):
    """Test 3: List tools and export schemas for architecture generator."""
    tool = MockCalculatorTool()
    registry.register(tool)
    tools = registry.list_tools()
    assert len(tools) == 1

    schemas = registry.list_schemas()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "mock_multiplier"
    assert schemas[0]["deterministic"] is True
    assert schemas[0]["side_effect"] is False


def test_4_reject_duplicate_registration(registry: ToolRegistry):
    """Test 4: Reject duplicate tool registration."""
    tool = MockCalculatorTool()
    registry.register(tool)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(tool)


def test_5_validate_valid_arguments():
    """Test 5: Valid arguments pass validation."""
    tool = MockCalculatorTool()
    validated = tool.validate_arguments({"x": 5, "y": 10})
    assert validated == {"x": 5.0, "y": 10.0}


def test_6_reject_invalid_arguments():
    """Test 6: Invalid arguments raise validation error."""
    tool = MockCalculatorTool()
    with pytest.raises(ValueError, match="required"):
        tool.validate_arguments({"x": 5})


def test_7_execute_tool(executor: ToolExecutor, registry: ToolRegistry):
    """Test 7: Execute tool through executor."""
    registry.register(MockCalculatorTool())
    result = asyncio.run(executor.execute("mock_multiplier", {"x": 4, "y": 5}))
    assert result.success is True
    assert result.data == {"product": 20.0}
    assert result.output == {"product": 20.0}


def test_8_structured_tool_error(executor: ToolExecutor, registry: ToolRegistry):
    """Test 8: Structured tool error on missing tool or invalid arguments."""
    # Tool not found
    res1 = asyncio.run(executor.execute("non_existent_tool", {}))
    assert res1.success is False
    assert "not found" in res1.error
    assert res1.metadata["error_type"] == "TOOL_NOT_FOUND"

    # Invalid arguments
    registry.register(MockCalculatorTool())
    res2 = asyncio.run(executor.execute("mock_multiplier", {"x": 10}))  # missing y
    assert res2.success is False
    assert "Invalid arguments" in res2.error
    assert res2.metadata["error_type"] == "VALIDATION_ERROR"


def test_9_execution_timing_metadata(executor: ToolExecutor, registry: ToolRegistry):
    """Test 9: Execution timing metadata is accurately recorded."""
    registry.register(MockCalculatorTool())
    result = asyncio.run(executor.execute("mock_multiplier", {"x": 2, "y": 3}))
    assert result.success is True
    assert result.duration_ms >= 0
    assert result.execution_time_ms >= 0
    assert result.tool_name == "mock_multiplier"


# ---------------------------------------------------------------------------
# Part 2: Reconciliation Tools Tests (10-20+)
# ---------------------------------------------------------------------------

def test_10_parse_valid_statement(executor: ToolExecutor, registry: ToolRegistry):
    """Test 10: Parse valid bank statement rows into BankTransaction records."""
    register_reconciliation_tools(registry)
    raw_statement = [
        {"transaction_id": "TX-101", "date": "2026-03-01", "amount": -1450.50, "vendor": "Stripe Payments"},
        {"transaction_id": "TX-102", "date": "2026-03-02", "amount": 25000.00, "vendor": "Acme Corp", "reference": "INV-99"},
    ]
    result = asyncio.run(executor.execute("parse_bank_statement", {"records": raw_statement}))
    assert result.success is True
    txs = result.data["transactions"]
    assert len(txs) == 2
    assert txs[0]["transaction_id"] == "TX-101"
    assert txs[0]["amount"] == "-1450.50"
    assert txs[0]["transaction_type"] == "debit"
    assert txs[1]["transaction_type"] == "credit"


def test_11_reject_malformed_statement(executor: ToolExecutor, registry: ToolRegistry):
    """Test 11: Clear error on missing fields or invalid date/amount in statement."""
    register_reconciliation_tools(registry)
    # Missing date
    res1 = asyncio.run(executor.execute("parse_bank_statement", {
        "records": [{"transaction_id": "TX-1", "amount": 100, "vendor": "Vendor"}]
    }))
    assert res1.success is False
    assert "missing required field 'date'" in res1.error

    # Invalid date format
    res2 = asyncio.run(executor.execute("parse_bank_statement", {
        "records": [{"transaction_id": "TX-2", "date": "03/01/2026", "amount": 100, "vendor": "Vendor"}]
    }))
    assert res2.success is False
    assert "Invalid date format" in res2.error


def test_12_query_ledger_filters(executor: ToolExecutor, registry: ToolRegistry):
    """Test 12: Query and filter general ledger entries."""
    register_reconciliation_tools(registry)
    entries = [
        {"entry_id": "GL-1", "date": "2026-03-01", "amount": -100.00, "vendor": "AWS", "account": "6000-Software"},
        {"entry_id": "GL-2", "date": "2026-03-05", "amount": -500.00, "vendor": "Google Cloud", "account": "6000-Software"},
        {"entry_id": "GL-3", "date": "2026-03-10", "amount": 1000.00, "vendor": "Client A", "account": "1200-AR"},
    ]

    # Filter by vendor
    res_vendor = asyncio.run(executor.execute("query_general_ledger", {"entries": entries, "vendor": "AWS"}))
    assert res_vendor.success is True
    assert res_vendor.data["count"] == 1
    assert res_vendor.data["entries"][0]["vendor"] == "AWS"

    # Filter by date range
    res_date = asyncio.run(executor.execute("query_general_ledger", {
        "entries": entries, "date_from": "2026-03-04", "date_to": "2026-03-12"
    }))
    assert res_date.success is True
    assert res_date.data["count"] == 2


def test_13_calculate_exact_decimal_difference(executor: ToolExecutor, registry: ToolRegistry):
    """Test 13: Calculate exact Decimal difference and exact match."""
    register_reconciliation_tools(registry)
    result = asyncio.run(executor.execute("calculate_reconciliation_difference", {
        "bank_amount": 1500.75,
        "ledger_amount": 1500.75,
    }))
    assert result.success is True
    data = result.data
    assert data["is_exact_match"] is True
    assert data["raw_difference"] == "0.00"
    assert data["detected_exception"] == "exact_match"


def test_14_fee_difference(executor: ToolExecutor, registry: ToolRegistry):
    """Test 14: Accurately isolate Stripe 2.9% + $0.30 processing fee."""
    register_reconciliation_tools(registry)
    # Customer invoiced $1,000.00 in ledger, bank deposit is $970.70 after $29.30 fee (2.9% + 0.30)
    result = asyncio.run(executor.execute("calculate_reconciliation_difference", {
        "bank_amount": 970.70,
        "ledger_amount": 1000.00,
        "fee_rate": 0.029,
        "fee_fixed": 0.30,
    }))
    assert result.success is True
    data = result.data
    assert data["detected_exception"] == "processing_fee"
    assert Decimal(data["fee_amount"]) == Decimal("29.30")
    assert Decimal(data["net_difference"]) == Decimal("0.00")


def test_15_timing_difference(executor: ToolExecutor, registry: ToolRegistry):
    """Test 15: Detect timing difference / date proximity."""
    register_reconciliation_tools(registry)
    bank_txs = [{"transaction_id": "B-1", "date": "2026-03-05", "amount": 1200.00, "vendor": "Stripe Deposit"}]
    ledger_entries = [{"entry_id": "L-1", "date": "2026-03-02", "amount": 1200.00, "vendor": "Stripe Deposit"}]

    result = asyncio.run(executor.execute("fuzzy_match_transactions", {
        "bank_transactions": bank_txs,
        "ledger_entries": ledger_entries,
        "date_tolerance_days": 5,
    }))
    assert result.success is True
    matched = result.data["matched_pairs"]
    assert len(matched) == 1
    assert matched[0]["match_type"] == "timing_difference"
    assert matched[0]["date_lag_days"] == 3


def test_16_fuzzy_match_exact_candidate(executor: ToolExecutor, registry: ToolRegistry):
    """Test 16: Fuzzy match correlates exact candidate with near-perfect confidence."""
    register_reconciliation_tools(registry)
    bank_txs = [{"transaction_id": "B-EXACT", "date": "2026-03-01", "amount": 450.00, "vendor": "GitHub Inc"}]
    ledger_entries = [{"entry_id": "L-EXACT", "date": "2026-03-01", "amount": 450.00, "vendor": "GitHub Inc"}]

    result = asyncio.run(executor.execute("fuzzy_match_transactions", {
        "bank_transactions": bank_txs,
        "ledger_entries": ledger_entries,
    }))
    assert result.success is True
    matched = result.data["matched_pairs"]
    assert len(matched) == 1
    assert matched[0]["match_type"] == "exact_match"
    assert matched[0]["confidence_score"] >= 0.95


def test_17_fuzzy_match_near_candidate(executor: ToolExecutor, registry: ToolRegistry):
    """Test 17: Fuzzy match correlates near candidate with slight vendor string variation."""
    register_reconciliation_tools(registry)
    bank_txs = [{"transaction_id": "B-AWS", "date": "2026-03-02", "amount": 834.12, "vendor": "Amazon Web Services"}]
    ledger_entries = [{"entry_id": "L-AWS", "date": "2026-03-01", "amount": 834.12, "vendor": "Amazon Web Serv"}]

    result = asyncio.run(executor.execute("fuzzy_match_transactions", {
        "bank_transactions": bank_txs,
        "ledger_entries": ledger_entries,
    }))
    assert result.success is True
    matched = result.data["matched_pairs"]
    assert len(matched) == 1
    assert matched[0]["vendor_similarity"] >= 0.80
    assert matched[0]["confidence_score"] >= 0.80


def test_18_wrong_vendor_rejection(executor: ToolExecutor, registry: ToolRegistry):
    """Test 18: Flag wrong vendor mismatch when amount matches but vendor is unrelated."""
    register_reconciliation_tools(registry)
    # Identical amount ($500.00), but unrelated vendors
    bank_txs = [{"transaction_id": "B-WRONG", "date": "2026-03-01", "amount": 500.00, "vendor": "Uber Technologies"}]
    ledger_entries = [{"entry_id": "L-WRONG", "date": "2026-03-01", "amount": 500.00, "vendor": "Figma Design"}]

    result = asyncio.run(executor.execute("fuzzy_match_transactions", {
        "bank_transactions": bank_txs,
        "ledger_entries": ledger_entries,
    }))
    assert result.success is True
    matched = result.data["matched_pairs"]
    assert len(matched) == 1
    assert matched[0]["match_type"] == "wrong_vendor"
    assert any("Wrong vendor mismatch" in r for r in matched[0]["reasons"])


def test_19_fx_difference_handling(executor: ToolExecutor, registry: ToolRegistry):
    """Test 19: Accurately isolate and classify foreign exchange variances."""
    register_reconciliation_tools(registry)
    # EUR 1000 billed in ledger, settled at USD 1080.00 in bank (FX rate 1.08)
    result = asyncio.run(executor.execute("calculate_reconciliation_difference", {
        "bank_amount": 1080.00,
        "ledger_amount": 1000.00,
        "fx_rate": 1.0800,
        "currency_bank": "USD",
        "currency_ledger": "EUR",
    }))
    assert result.success is True
    data = result.data
    assert data["detected_exception"] == "fx_difference"
    assert Decimal(data["net_difference"]) == Decimal("0.00")


def test_20_transposition_detection(executor: ToolExecutor, registry: ToolRegistry):
    """Test 20: Detect accounting transposition error ($1,420 vs $1,240)."""
    register_reconciliation_tools(registry)
    result = asyncio.run(executor.execute("calculate_reconciliation_difference", {
        "bank_amount": 1240.00,
        "ledger_amount": 1420.00,
    }))
    assert result.success is True
    data = result.data
    assert data["detected_exception"] == "transposition"
    assert Decimal(data["raw_difference"]) == Decimal("-180.00")
    assert any("Transposition error detected" in r for r in data["exception_reasons"])


def test_21_duplicate_detection(executor: ToolExecutor, registry: ToolRegistry):
    """Test 21: Detect multiple bank charges matching a single ledger invoice (duplicate billing)."""
    register_reconciliation_tools(registry)
    bank_txs = [
        {"transaction_id": "B-DUP1", "date": "2026-03-01", "amount": 250.00, "vendor": "SaaS Subscription"},
        {"transaction_id": "B-DUP2", "date": "2026-03-01", "amount": 250.00, "vendor": "SaaS Subscription"},
    ]
    ledger_entries = [
        {"entry_id": "L-SINGLE", "date": "2026-03-01", "amount": 250.00, "vendor": "SaaS Subscription"}
    ]

    result = asyncio.run(executor.execute("fuzzy_match_transactions", {
        "bank_transactions": bank_txs,
        "ledger_entries": ledger_entries,
    }))
    assert result.success is True
    matched = result.data["matched_pairs"]
    assert len(matched) == 2
    assert matched[0]["match_type"] == "duplicate"
    assert matched[1]["match_type"] == "duplicate"


def test_22_compound_exception(executor: ToolExecutor, registry: ToolRegistry):
    """Test 22: Detect compound exception combining both processing fee and timing lag."""
    register_reconciliation_tools(registry)
    # $1000 invoiced on March 1st. Net $971 deposited 3 days later on March 4th.
    bank_txs = [{"transaction_id": "B-COMP", "date": "2026-03-04", "amount": 971.00, "vendor": "Client Checkout"}]
    ledger_entries = [{"entry_id": "L-COMP", "date": "2026-03-01", "amount": 1000.00, "vendor": "Client Checkout"}]

    result = asyncio.run(executor.execute("fuzzy_match_transactions", {
        "bank_transactions": bank_txs,
        "ledger_entries": ledger_entries,
        "fee_rate": 0.029,
        "date_tolerance_days": 5,
    }))
    assert result.success is True
    matched = result.data["matched_pairs"]
    assert len(matched) == 1
    assert matched[0]["match_type"] == "compound_exception"
    assert matched[0]["date_lag_days"] == 3
