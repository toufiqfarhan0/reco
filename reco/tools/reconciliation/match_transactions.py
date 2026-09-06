"""Tool: fuzzy_match_transactions — deterministic multi-feature reconciliation matching."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field

from reco.core.interfaces import Tool, ToolResult
from reco.tools.reconciliation.calc_difference import is_transposition_error
from reco.tools.reconciliation.models import (
    BankTransaction,
    LedgerEntry,
    MatchCandidate,
    ReconciliationSummary,
)


def compute_string_similarity(s1: str, s2: str) -> float:
    """Compute pure-Python deterministic string similarity (0.0 to 1.0)."""
    norm1 = "".join(c.lower() for c in s1 if c.isalnum() or c.isspace()).strip()
    norm2 = "".join(c.lower() for c in s2 if c.isalnum() or c.isspace()).strip()

    if not norm1 or not norm2:
        return 0.0
    if norm1 == norm2:
        return 1.0

    # Substring / prefix check (e.g. "Amazon" in "Amazon Web Services")
    if norm1 in norm2 or norm2 in norm1:
        shorter = min(len(norm1), len(norm2))
        longer = max(len(norm1), len(norm2))
        return 0.80 + (0.20 * (shorter / longer))

    # Token overlap (Jaccard on words)
    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())
    if tokens1 and tokens2:
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        jaccard = intersection / union
        if jaccard > 0.5:
            return 0.70 + (0.30 * jaccard)

    # Standard Levenshtein distance
    m, n = len(norm1), len(norm2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if norm1[i - 1] == norm2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    dist = dp[m][n]
    max_len = max(m, n)
    return max(0.0, 1.0 - (dist / max_len))


def compute_date_lag_days(d1_str: str, d2_str: str) -> int:
    """Calculate absolute difference in days between two YYYY-MM-DD date strings."""
    try:
        dt1 = datetime.strptime(d1_str.strip(), "%Y-%m-%d")
        dt2 = datetime.strptime(d2_str.strip(), "%Y-%m-%d")
        return abs((dt1 - dt2).days)
    except ValueError:
        return 999


class FuzzyMatchInput(BaseModel):
    """Input parameters for fuzzy_match_transactions."""
    bank_transactions: Any = Field(default_factory=list, description="List of bank transaction rows or parsed statement object")
    ledger_entries: Any = Field(default_factory=list, description="List of general ledger entry rows or queried entries object")
    amount_tolerance: Optional[Decimal] = Field(default=Decimal("0.05"), description="Allowable cent difference")
    date_tolerance_days: int = Field(default=5, description="Maximum day lag for consideration")
    vendor_similarity_threshold: float = Field(default=0.60, description="Minimum vendor similarity to qualify")
    require_vendor_match: bool = Field(default=False, description="If True, reject pairing transactions with mismatched vendors (wrong_vendor)")
    fee_rate: Optional[Decimal] = Field(default=Decimal("0.029"), description="Expected processing fee rate (2.9%)")
    fx_rate: Optional[Decimal] = Field(default=Decimal("1.0000"), description="FX exchange rate")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class FuzzyMatchTransactionsTool(Tool):
    """Correlates and classifies matches between bank transactions and general ledger entries."""

    @property
    def name(self) -> str:
        return "fuzzy_match_transactions"

    @property
    def description(self) -> str:
        return (
            "Compares bank transactions and ledger entries across multiple features (amount, date proximity, "
            "vendor similarity, reference codes). Deterministically classifies exact matches, near matches, "
            "processing fees, timing differences, duplicate records, wrong vendors, and transpositions."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "vendor_similarity_threshold": {"type": "number", "default": 0.60, "description": "Minimum vendor similarity to qualify (e.g. 0.85 for strict matching)"},
                "require_vendor_match": {"type": "boolean", "default": False, "description": "If True, reject pairing transactions when vendors mismatch"},
                "amount_tolerance": {"type": "number", "default": 0.05, "description": "Allowable cent difference"},
                "date_tolerance_days": {"type": "integer", "default": 5, "description": "Maximum day lag for consideration"},
                "fee_rate": {"type": "number", "default": 0.029, "description": "Expected processing fee rate"},
                "fx_rate": {"type": "number", "default": 1.0, "description": "FX exchange rate"},
                "bank_transactions": {"type": "array", "items": {"type": "object"}, "description": "Bank transactions (optional; auto-injected from upstream)"},
                "ledger_entries": {"type": "array", "items": {"type": "object"}, "description": "Ledger entries (optional; auto-injected from upstream)"},
            },
        }

    @property
    def category(self) -> str:
        return "reconciliation"

    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        parsed = FuzzyMatchInput(**arguments)
        return parsed.model_dump()

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        raw_bank = arguments.get("bank_transactions", [])
        if isinstance(raw_bank, dict) and "transactions" in raw_bank:
            raw_bank = raw_bank["transactions"]

        raw_ledger = arguments.get("ledger_entries", [])
        if isinstance(raw_ledger, dict) and "entries" in raw_ledger:
            raw_ledger = raw_ledger["entries"]

        amount_tol = Decimal(str(arguments.get("amount_tolerance", "0.05")))
        date_tol_days = int(arguments.get("date_tolerance_days", 5))
        vendor_thresh = float(arguments.get("vendor_similarity_threshold", 0.60))
        require_vendor = bool(arguments.get("require_vendor_match", False))
        fee_rate = Decimal(str(arguments["fee_rate"])) if arguments.get("fee_rate") is not None else None
        fx_rate = Decimal(str(arguments.get("fx_rate", "1.0000")))

        # Parse normalized objects
        bank_txs = [
            BankTransaction(
                transaction_id=str(b.get("transaction_id") or b.get("id") or f"tx_{idx+1}"),
                date=str(b["date"]),
                amount=Decimal(str(b["amount"])),
                currency=str(b.get("currency", "USD")),
                vendor=str(b["vendor"]),
                reference=str(b.get("reference", "")),
            )
            for idx, b in enumerate(raw_bank)
        ]

        ledger_entries = [
            LedgerEntry(
                entry_id=str(l.get("entry_id") or l.get("id") or f"le_{idx+1}"),
                date=str(l["date"]),
                amount=Decimal(str(l["amount"])),
                currency=str(l.get("currency", "USD")),
                account=str(l.get("account", "1000-Cash")),
                vendor=str(l["vendor"]),
                reference=str(l.get("reference", "")),
            )
            for idx, l in enumerate(raw_ledger)
        ]

        candidates: List[MatchCandidate] = []
        matched_bank_ids: Set[str] = set()
        matched_ledger_ids: Set[str] = set()
        ledger_match_counts: Dict[str, int] = {}
        bank_match_counts: Dict[str, int] = {}

        # Pairwise comparison
        for b_tx in bank_txs:
            for l_entry in ledger_entries:
                v_sim = compute_string_similarity(b_tx.vendor, l_entry.vendor)
                date_lag = compute_date_lag_days(b_tx.date, l_entry.date)
                amt_diff = abs(b_tx.amount - l_entry.amount)

                # Skip if totally unviable (date lag > 30 days and no vendor overlap)
                if date_lag > 30 and v_sim < 0.30:
                    continue

                reasons = []
                score = 0.0
                match_type = "near_match"

                # Check 1: FX Difference
                is_fx = (
                    (b_tx.currency != l_entry.currency or fx_rate != Decimal("1.0000"))
                    and abs(b_tx.amount - (l_entry.amount * fx_rate)) <= Decimal("0.10")
                )
                if is_fx:
                    match_type = "fx_difference"
                    score += 0.50
                    reasons.append(f"FX conversion match ({b_tx.currency} vs {l_entry.currency} at rate {fx_rate})")

                # Check 2: Exact Amount Match
                elif amt_diff == Decimal("0.00"):
                    score += 0.50
                    reasons.append("Exact monetary amount match.")

                # Check 3: Fee deduction (Gross vs Net deposit)
                elif fee_rate and abs(amt_diff - (l_entry.amount * fee_rate).quantize(Decimal("0.01"))) <= Decimal("0.02"):
                    calculated_fee = (l_entry.amount * fee_rate).quantize(Decimal("0.01"))
                    if date_lag > 0:
                        match_type = "compound_exception"
                        reasons.append(f"Compound exception: Processing fee of {calculated_fee} + {date_lag} day timing lag.")
                    else:
                        match_type = "processing_fee"
                        reasons.append(f"Processing fee discrepancy: bank net amount matches gross minus {calculated_fee}.")
                    score += 0.45

                # Check 4: Transposition error
                elif is_transposition_error(b_tx.amount, l_entry.amount):
                    match_type = "transposition"
                    score += 0.35
                    reasons.append(f"Transposition error detected: digits match, variance of {amt_diff} divisible by 9.")

                # Check 5: Near amount within tolerance
                elif amt_diff <= amount_tol:
                    score += 0.40
                    reasons.append(f"Amount within allowable tolerance ({amt_diff} <= {amount_tol}).")

                # Check 6: Amount Mismatch
                else:
                    score += 0.0

                # Vendor scoring
                score += v_sim * 0.30
                if v_sim >= 0.85:
                    reasons.append(f"High vendor similarity: '{b_tx.vendor}' ≈ '{l_entry.vendor}' ({v_sim:.2f}).")
                elif v_sim >= vendor_thresh:
                    reasons.append(f"Acceptable vendor similarity ({v_sim:.2f}).")
                elif score >= 0.40:
                    # Amount matched, but vendor failed completely
                    match_type = "wrong_vendor"
                    reasons.append(f"Wrong vendor mismatch: '{b_tx.vendor}' vs '{l_entry.vendor}' ({v_sim:.2f}).")

                # Date scoring
                if date_lag == 0:
                    score += 0.15
                    reasons.append("Identical transaction date.")
                elif date_lag <= date_tol_days:
                    lag_penalty = 0.15 * (1.0 - (date_lag / (date_tol_days + 1)))
                    score += lag_penalty
                    reasons.append(f"Timing difference of {date_lag} days.")
                    if match_type not in ["processing_fee", "compound_exception", "wrong_vendor", "transposition", "fx_difference"]:
                        match_type = "timing_difference" if amt_diff == 0 else "near_match"

                # Reference matching
                if b_tx.reference and l_entry.reference and b_tx.reference.lower() == l_entry.reference.lower():
                    score += 0.05
                    reasons.append(f"Reference number matches exactly: '{b_tx.reference}'.")

                # Final classification for pure exact matches
                if amt_diff == Decimal("0.00") and date_lag == 0 and v_sim >= 0.90:
                    match_type = "exact_match"
                    score = max(score, 0.98)

                # Filter candidates by minimum viable score
                if score >= 0.50:
                    if require_vendor and match_type == "wrong_vendor":
                        continue
                    candidate = MatchCandidate(
                        bank_transaction_id=b_tx.transaction_id,
                        ledger_entry_id=l_entry.entry_id,
                        confidence_score=round(min(score, 1.0), 4),
                        match_type=match_type,  # type: ignore
                        reasons=reasons,
                        amount_discrepancy=amt_diff,
                        date_lag_days=date_lag,
                        vendor_similarity=round(v_sim, 4),
                        details={
                            "bank_amount": str(b_tx.amount),
                            "ledger_amount": str(l_entry.amount),
                            "bank_vendor": b_tx.vendor,
                            "ledger_vendor": l_entry.vendor,
                        },
                    )
                    candidates.append(candidate)
                    matched_bank_ids.add(b_tx.transaction_id)
                    matched_ledger_ids.add(l_entry.entry_id)
                    ledger_match_counts[l_entry.entry_id] = ledger_match_counts.get(l_entry.entry_id, 0) + 1
                    bank_match_counts[b_tx.transaction_id] = bank_match_counts.get(b_tx.transaction_id, 0) + 1

        # Check for duplicates: multiple bank items for one ledger entry, or vice versa
        for cand in candidates:
            if (
                ledger_match_counts.get(cand.ledger_entry_id, 0) > 1
                or bank_match_counts.get(cand.bank_transaction_id, 0) > 1
            ):
                if cand.match_type not in ["wrong_vendor"]:
                    cand.match_type = "duplicate"
                    cand.reasons.append("Duplicate detected: Multiple records match the same counter-entry.")

        # Sort candidates by confidence score descending
        candidates.sort(key=lambda c: c.confidence_score, reverse=True)

        unmatched_bank = [b.transaction_id for b in bank_txs if b.transaction_id not in matched_bank_ids]
        unmatched_ledger = [l.entry_id for l in ledger_entries if l.entry_id not in matched_ledger_ids]

        # Exception counts
        exception_counts: Dict[str, int] = {}
        for c in candidates:
            exception_counts[c.match_type] = exception_counts.get(c.match_type, 0) + 1
        if unmatched_bank:
            exception_counts["missing_in_ledger"] = len(unmatched_bank)
        if unmatched_ledger:
            exception_counts["missing_in_bank"] = len(unmatched_ledger)

        summary = ReconciliationSummary(
            matched_pairs=candidates,
            unmatched_bank_ids=unmatched_bank,
            unmatched_ledger_ids=unmatched_ledger,
            exceptions_by_type=exception_counts,
            total_bank_transactions=len(bank_txs),
            total_ledger_entries=len(ledger_entries),
        )

        return ToolResult(
            success=True,
            data=summary.model_dump(mode="json"),
            metadata={
                "candidate_count": len(candidates),
                "unmatched_bank_count": len(unmatched_bank),
                "unmatched_ledger_count": len(unmatched_ledger),
            },
        )
