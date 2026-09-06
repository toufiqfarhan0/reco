"""Domain models and exception classifications for financial reconciliation."""

from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class BankTransaction(BaseModel):
    """Normalized bank statement line item."""
    transaction_id: str
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    amount: Decimal = Field(..., description="Monetary amount (positive = deposit/credit, negative = withdrawal/debit)")
    currency: str = "USD"
    vendor: str = Field(..., description="Counterparty or payee name")
    reference: str = Field(default="", description="Bank reference number or memo")
    transaction_type: Literal["credit", "debit"] = "debit"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class LedgerEntry(BaseModel):
    """Normalized general ledger journal entry."""
    entry_id: str
    date: str = Field(..., description="Booking date in YYYY-MM-DD format")
    amount: Decimal = Field(..., description="Monetary amount in exact Decimal")
    currency: str = "USD"
    account: str = Field(default="1000-Cash", description="GL account code or name")
    vendor: str = Field(..., description="Recorded vendor or customer name")
    reference: str = Field(default="", description="Invoice or invoice reference number")
    entry_type: Literal["debit", "credit"] = "debit"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ReconciliationDifference(BaseModel):
    """Computed financial variance breakdown between bank and ledger records."""
    bank_amount: Decimal
    ledger_amount: Decimal
    raw_difference: Decimal = Field(..., description="bank_amount - ledger_amount")
    fee_amount: Decimal = Field(default=Decimal("0.00"), description="Calculated processing or merchant fee")
    net_difference: Decimal = Field(default=Decimal("0.00"), description="Remaining variance after fee deduction")
    currency_bank: str = "USD"
    currency_ledger: str = "USD"
    is_exact_match: bool = False
    detected_exception: Optional[str] = None
    exception_reasons: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MatchCandidate(BaseModel):
    """A scored pairing between a bank transaction and a general ledger entry."""
    bank_transaction_id: str
    ledger_entry_id: str
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    match_type: Literal[
        "exact_match",
        "near_match",
        "processing_fee",
        "timing_difference",
        "duplicate",
        "wrong_vendor",
        "wrong_amount",
        "transposition",
        "fx_difference",
        "compound_exception",
    ]
    reasons: List[str] = Field(default_factory=list)
    amount_discrepancy: Decimal = Field(default=Decimal("0.00"))
    date_lag_days: int = 0
    vendor_similarity: float = 1.0
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ReconciliationSummary(BaseModel):
    """Aggregate result of a matching and reconciliation pass."""
    matched_pairs: List[MatchCandidate] = Field(default_factory=list)
    unmatched_bank_ids: List[str] = Field(default_factory=list)
    unmatched_ledger_ids: List[str] = Field(default_factory=list)
    exceptions_by_type: Dict[str, int] = Field(default_factory=dict)
    total_bank_transactions: int = 0
    total_ledger_entries: int = 0
