"""Tool: query_general_ledger — queries and filters ledger entries deterministically."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from reco.core.interfaces import Tool, ToolResult
from reco.tools.reconciliation.models import LedgerEntry


class QueryGeneralLedgerInput(BaseModel):
    """Input filter criteria for query_general_ledger."""
    entries: List[Dict[str, Any]] = Field(..., description="List of ledger entries to query from")
    vendor: Optional[str] = Field(default=None, description="Filter by vendor name (case-insensitive substring)")
    date_from: Optional[str] = Field(default=None, description="Start date (inclusive, YYYY-MM-DD)")
    date_to: Optional[str] = Field(default=None, description="End date (inclusive, YYYY-MM-DD)")
    min_amount: Optional[Decimal] = Field(default=None, description="Minimum entry amount")
    max_amount: Optional[Decimal] = Field(default=None, description="Maximum entry amount")
    currency: Optional[str] = Field(default=None, description="Currency filter (e.g., USD, EUR)")
    account: Optional[str] = Field(default=None, description="Account identifier or name")
    reference: Optional[str] = Field(default=None, description="Reference/invoice identifier")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class QueryGeneralLedgerTool(Tool):
    """Queries and filters ledger entries deterministically without external database calls."""

    @property
    def name(self) -> str:
        return "query_general_ledger"

    @property
    def description(self) -> str:
        return (
            "Queries and filters a collection of general ledger entries using explicit criteria "
            "(date ranges, vendor substring, exact amount bounds, account code, reference)."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["entries"],
            "properties": {
                "entries": {"type": "array", "items": {"type": "object"}, "description": "Ledger entries array"},
                "vendor": {"type": "string", "description": "Vendor name filter"},
                "date_from": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                "date_to": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                "min_amount": {"type": "number", "description": "Minimum amount"},
                "max_amount": {"type": "number", "description": "Maximum amount"},
                "currency": {"type": "string", "description": "Currency code"},
                "account": {"type": "string", "description": "Account code"},
                "reference": {"type": "string", "description": "Reference number"},
            },
        }

    @property
    def category(self) -> str:
        return "reconciliation"

    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        parsed = QueryGeneralLedgerInput(**arguments)
        return parsed.model_dump()

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        raw_entries = arguments.get("entries", [])
        if not isinstance(raw_entries, list):
            return ToolResult(success=False, error="'entries' must be a list of dictionaries")

        # Filters
        vendor_filter = arguments.get("vendor")
        date_from = arguments.get("date_from")
        date_to = arguments.get("date_to")
        min_amount = Decimal(str(arguments["min_amount"])) if arguments.get("min_amount") is not None else None
        max_amount = Decimal(str(arguments["max_amount"])) if arguments.get("max_amount") is not None else None
        currency_filter = str(arguments["currency"]).upper() if arguments.get("currency") else None
        account_filter = arguments.get("account")
        ref_filter = arguments.get("reference")

        matched_entries: List[LedgerEntry] = []

        for idx, item in enumerate(raw_entries):
            try:
                entry = LedgerEntry(
                    entry_id=str(item.get("entry_id", f"entry-{idx}")),
                    date=str(item.get("date", "")).strip(),
                    amount=Decimal(str(item["amount"])),
                    currency=str(item.get("currency", "USD")).upper(),
                    account=str(item.get("account", "1000-Cash")),
                    vendor=str(item.get("vendor", "")).strip(),
                    reference=str(item.get("reference", "")).strip(),
                    entry_type=item.get("entry_type", "debit"),
                    metadata=item.get("metadata", {}),
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Malformed ledger entry at index {idx}: {e}",
                )

            # Apply filters
            if vendor_filter and vendor_filter.lower() not in entry.vendor.lower():
                continue
            if date_from and entry.date < date_from:
                continue
            if date_to and entry.date > date_to:
                continue
            if min_amount is not None and abs(entry.amount) < min_amount:
                continue
            if max_amount is not None and abs(entry.amount) > max_amount:
                continue
            if currency_filter and entry.currency != currency_filter:
                continue
            if account_filter and account_filter.lower() not in entry.account.lower():
                continue
            if ref_filter and ref_filter.lower() not in entry.reference.lower():
                continue

            matched_entries.append(entry)

        return ToolResult(
            success=True,
            data={
                "entries": [e.model_dump(mode="json") for e in matched_entries],
                "count": len(matched_entries),
            },
            metadata={"total_scanned": len(raw_entries), "matched_count": len(matched_entries)},
        )
