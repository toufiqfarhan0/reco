"""Tool: parse_bank_statement — normalizes and validates raw bank statement lines."""

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from reco.core.interfaces import Tool, ToolResult
from reco.tools.reconciliation.models import BankTransaction


class ParseBankStatementInput(BaseModel):
    """Input parameters schema for parse_bank_statement."""
    records: List[Dict[str, Any]] = Field(..., description="List of raw bank transaction rows to parse and validate")


class ParseBankStatementTool(Tool):
    """Parses raw bank statement entries into strongly-typed BankTransaction objects."""

    @property
    def name(self) -> str:
        return "parse_bank_statement"

    @property
    def description(self) -> str:
        return (
            "Normalizes and strictly validates a list of raw bank statement records into "
            "standardized BankTransaction objects with exact Decimal currency precision."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["records"],
            "properties": {
                "records": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of raw bank statement records containing transaction_id, date, amount, vendor.",
                }
            },
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "transactions": {"type": "array", "description": "List of normalized BankTransaction objects"},
                "count": {"type": "integer"},
            },
        }

    @property
    def category(self) -> str:
        return "reconciliation"

    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        parsed = ParseBankStatementInput(**arguments)
        return parsed.model_dump()

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        records = arguments.get("records", [])
        if not isinstance(records, list):
            return ToolResult(success=False, error="Input 'records' must be a list of dictionaries")

        parsed_transactions: List[BankTransaction] = []

        for idx, rec in enumerate(records):
            if not isinstance(rec, dict):
                return ToolResult(
                    success=False,
                    error=f"Record at index {idx} is not a valid dictionary object: {rec}",
                )

            # Mandatory field check
            for req_field in ["transaction_id", "date", "amount", "vendor"]:
                if req_field not in rec or rec[req_field] is None:
                    return ToolResult(
                        success=False,
                        error=f"Malformed record at index {idx}: missing required field '{req_field}' in {rec}",
                    )

            # Date format validation
            date_str = str(rec["date"]).strip()
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return ToolResult(
                    success=False,
                    error=f"Invalid date format '{date_str}' at index {idx}. Expected YYYY-MM-DD.",
                )

            # Decimal amount validation with 2-decimal standard monetary quantization
            try:
                amount_val = Decimal(str(rec["amount"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            except (InvalidOperation, TypeError):
                return ToolResult(
                    success=False,
                    error=f"Invalid numeric amount '{rec['amount']}' at index {idx}.",
                )

            tx = BankTransaction(
                transaction_id=str(rec["transaction_id"]),
                date=date_str,
                amount=amount_val,
                currency=str(rec.get("currency", "USD")).upper(),
                vendor=str(rec["vendor"]).strip(),
                reference=str(rec.get("reference", "")).strip(),
                transaction_type=rec.get("transaction_type", "credit" if amount_val > 0 else "debit"),
                metadata=rec.get("metadata", {}),
            )
            parsed_transactions.append(tx)

        return ToolResult(
            success=True,
            data={
                "transactions": [t.model_dump(mode="json") for t in parsed_transactions],
                "count": len(parsed_transactions),
            },
            metadata={"parsed_count": len(parsed_transactions)},
        )
