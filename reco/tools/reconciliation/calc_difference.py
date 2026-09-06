"""Tool: calculate_reconciliation_difference — exact Decimal variance & fee arithmetic."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from reco.core.interfaces import Tool, ToolResult
from reco.tools.reconciliation.models import ReconciliationDifference


class CalculateDifferenceInput(BaseModel):
    """Input parameters for calculate_reconciliation_difference."""
    bank_amount: Decimal = Field(..., description="Bank statement transaction amount")
    ledger_amount: Decimal = Field(..., description="General ledger entry amount")
    fee_rate: Optional[Decimal] = Field(default=None, description="Expected processing fee percentage (e.g., 0.029 for 2.9%)")
    fee_fixed: Optional[Decimal] = Field(default=Decimal("0.00"), description="Fixed fee component (e.g., 0.30)")
    fx_rate: Optional[Decimal] = Field(default=Decimal("1.0000"), description="Foreign exchange conversion rate (Bank/Ledger)")
    currency_bank: str = Field(default="USD")
    currency_ledger: str = Field(default="USD")

    model_config = ConfigDict(arbitrary_types_allowed=True)


def is_transposition_error(a: Decimal, b: Decimal) -> bool:
    """Detect whether difference is a classical accounting transposition error.

    Properties:
    1. Difference is non-zero and divisible by 9 (in cent/integer space).
    2. Digits of both numbers are permutations of each other.
    """
    diff_cents = abs(int((a - b) * 100))
    if diff_cents == 0 or diff_cents % 9 != 0:
        return False

    # Extract digits ignoring signs and decimal points
    digits_a = sorted(c for c in str(abs(a)) if c.isdigit())
    digits_b = sorted(c for c in str(abs(b)) if c.isdigit())
    return digits_a == digits_b


class CalculateDifferenceTool(Tool):
    """Calculates financial differences using exact Decimal math and isolates exception causes."""

    @property
    def name(self) -> str:
        return "calculate_reconciliation_difference"

    @property
    def description(self) -> str:
        return (
            "Calculates financial variances between bank and ledger amounts using exact Decimal "
            "arithmetic. Detects exact matches, processing fees (gross vs net), FX variances, "
            "and numerical transposition errors (divisible by 9)."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["bank_amount", "ledger_amount"],
            "properties": {
                "bank_amount": {"type": "number", "description": "Bank transaction amount"},
                "ledger_amount": {"type": "number", "description": "Ledger entry amount"},
                "fee_rate": {"type": "number", "description": "Percentage fee (e.g., 0.029 for 2.9%)"},
                "fee_fixed": {"type": "number", "description": "Fixed fee amount (e.g., 0.30)"},
                "fx_rate": {"type": "number", "description": "FX exchange rate"},
                "currency_bank": {"type": "string", "description": "Currency of bank transaction"},
                "currency_ledger": {"type": "string", "description": "Currency of ledger entry"},
            },
        }

    @property
    def category(self) -> str:
        return "reconciliation"

    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        parsed = CalculateDifferenceInput(**arguments)
        return parsed.model_dump()

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        try:
            bank_amt = Decimal(str(arguments["bank_amount"]))
            ledger_amt = Decimal(str(arguments["ledger_amount"]))
            fee_rate = Decimal(str(arguments["fee_rate"])) if arguments.get("fee_rate") is not None else None
            fee_fixed = Decimal(str(arguments.get("fee_fixed", "0.00")))
            fx_rate = Decimal(str(arguments.get("fx_rate", "1.0000")))
            curr_bank = str(arguments.get("currency_bank", "USD")).upper()
            curr_ledger = str(arguments.get("currency_ledger", "USD")).upper()
        except (InvalidOperation, KeyError, TypeError) as e:
            return ToolResult(success=False, error=f"Invalid numeric argument: {e}")

        # Exact raw difference: bank - ledger
        raw_diff = bank_amt - ledger_amt
        is_exact = raw_diff == Decimal("0.00")
        detected_exception: Optional[str] = "exact_match" if is_exact else None
        reasons: List[str] = []
        fee_amount = Decimal("0.00")

        # 1. Exact match check
        if is_exact:
            reasons.append("Bank amount and ledger amount match exactly.")
            net_diff = Decimal("0.00")

        # 2. FX difference check
        elif curr_bank != curr_ledger or fx_rate != Decimal("1.0000"):
            converted_ledger = (ledger_amt * fx_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            fx_diff = bank_amt - converted_ledger
            if abs(fx_diff) <= Decimal("0.05"):  # small rounding boundary
                detected_exception = "fx_difference"
                reasons.append(
                    f"Currencies differ ({curr_bank} vs {curr_ledger}). "
                    f"Converted ledger amount {converted_ledger} matches bank {bank_amt} with FX rate {fx_rate}."
                )
                net_diff = fx_diff
            else:
                detected_exception = "fx_mismatch"
                reasons.append(f"FX variance of {fx_diff} exceeds allowable rounding tolerance.")
                net_diff = fx_diff

        # 3. Transposition error check
        elif is_transposition_error(bank_amt, ledger_amt):
            detected_exception = "transposition"
            diff_val = abs(raw_diff)
            reasons.append(
                f"Transposition error detected: difference of {diff_val} is divisible by 9 and digits match."
            )
            net_diff = raw_diff

        # 4. Processing Fee check (Gross vs Net)
        else:
            # Check if expected fee matches difference
            candidate_fee = abs(raw_diff)
            if fee_rate is not None:
                calc_fee = (abs(ledger_amt) * fee_rate + fee_fixed).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if abs(calc_fee - candidate_fee) <= Decimal("0.02"):
                    fee_amount = calc_fee
                    detected_exception = "processing_fee"
                    reasons.append(f"Matches processing fee of {fee_amount} (rate={fee_rate*100}%, fixed={fee_fixed}).")
                    net_diff = raw_diff + fee_amount if raw_diff < 0 else raw_diff - fee_amount
                else:
                    detected_exception = "wrong_amount"
                    reasons.append(f"Discrepancy of {raw_diff} does not match expected fee calculation of {calc_fee}.")
                    net_diff = raw_diff
            else:
                detected_exception = "wrong_amount"
                reasons.append(f"Unexplained amount discrepancy of {raw_diff}.")
                net_diff = raw_diff

        result_model = ReconciliationDifference(
            bank_amount=bank_amt,
            ledger_amount=ledger_amt,
            raw_difference=raw_diff,
            fee_amount=fee_amount,
            net_difference=net_diff,
            currency_bank=curr_bank,
            currency_ledger=curr_ledger,
            is_exact_match=is_exact,
            detected_exception=detected_exception,
            exception_reasons=reasons,
            details={
                "is_transposition": is_transposition_error(bank_amt, ledger_amt),
                "fx_rate_applied": str(fx_rate),
            },
        )

        return ToolResult(
            success=True,
            data=result_model.model_dump(mode="json"),
            metadata={"detected_exception": detected_exception, "is_exact_match": is_exact},
        )
