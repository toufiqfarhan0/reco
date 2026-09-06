# Reco Tool System & Reconciliation Tool Pack

## 1. Generic Tool Architecture

Reco's tool system is strictly generic, allowing autonomous agents to invoke capabilities through a validated, safe, and timed interface without direct imports or arbitrary code execution.

```
┌─────────────────────────────────────────────────────────────┐
│                    Future Agent Runtime                     │
└──────────────────────────────┬──────────────────────────────┘
                               │ execute("tool_name", args)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        ToolExecutor                         │
│  - Lookup in Registry                                       │
│  - Argument Validation (Pydantic schemas)                   │
│  - Execution Timing (duration_ms)                           │
│  - Exception Containment & Structured Error Output          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        ToolRegistry                         │
│  - Central catalog of registered Tool instances             │
│  - list_schemas() -> JSON Schema catalog for Arch Generator │
└──────────────────────────────┬──────────────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│     Reconciliation Pack      │        │    Future Domain Packs       │
│  - parse_bank_statement      │        │  - Invoice processing        │
│  - query_general_ledger      │        │  - Audit evidence            │
│  - calculate_difference      │        │  - Web research              │
│  - fuzzy_match_transactions  │        │                              │
└──────────────────────────────┘        └──────────────────────────────┘
```

---

## 2. Tool Contracts & Metadata

Every tool implements the `Tool` abstract base class defined in [`reco/core/interfaces.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/core/interfaces.py):

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Unique identifier (e.g., `calculate_reconciliation_difference`). |
| `description` | `str` | Human/LLM explanation of functionality. |
| `parameters_schema`| `dict` | JSON Schema specifying required and optional arguments. |
| `output_schema` | `dict` | JSON Schema specifying the return payload format. |
| `deterministic` | `bool` | `True` if identical inputs always produce identical outputs. |
| `side_effect` | `bool` | `False` for pure read/compute tools; `True` for state-changing operations. |
| `risk_level` | `str` | `'low'`, `'medium'`, or `'high'` (used by the architecture generator). |
| `category` | `str` | Functional tag (`'reconciliation'`, `'extraction'`, `'math'`). |

### Tool Execution Result
Tools return a standardized `ToolResult`:
- `success`: boolean status flag.
- `data` / `output`: structured return payload.
- `error`: machine-readable error string if failed.
- `duration_ms` / `execution_time_ms`: execution time in milliseconds.
- `tool_name`: name of tool invoked.
- `metadata`: contextual error codes or execution stats.

---

## 3. Financial Reconciliation Tool Pack

The reconciliation pack implements deterministic financial analysis without floating-point rounding errors by using Python's exact `Decimal` arithmetic.

### 1. `parse_bank_statement`
- **Purpose**: Normalizes raw statement inputs into validated `BankTransaction` records.
- **Validation**: Strict YYYY-MM-DD date checking and standard monetary 2-decimal quantization (`Decimal('0.01')`).

### 2. `query_general_ledger`
- **Purpose**: Queries and filters an array of `LedgerEntry` records.
- **Filters**: Vendor substring, date ranges, min/max amount bounds, account code, and invoice reference.

### 3. `calculate_reconciliation_difference`
- **Purpose**: Calculates financial variances and classifies the root cause of discrepancies.
- **Detections**:
  - Exact match (`raw_difference == 0.00`).
  - Processing fee deduction (e.g. Stripe 2.9% + $0.30) where net deposit equals gross ledger minus fee.
  - Foreign exchange (FX) conversion variances across different currencies.
  - Classical transposition errors (variance divisible by 9 with permuted digits, e.g. $1,420 vs $1,240).

### 4. `fuzzy_match_transactions`
- **Purpose**: Multi-feature correlation pairing bank transactions to ledger entries.
- **Features Evaluated**:
  - Amount proximity (exact, fee-matched, transposition, within tolerance).
  - Date lag in days (timing differences / clearing delays).
  - Vendor string similarity (token overlap + Levenshtein distance).
  - Invoice reference matching.
- **Exception Classifications**:
  - `exact_match`: 1-to-1 match of amount, date, and vendor.
  - `near_match`: Small date variance or minor vendor naming difference.
  - `processing_fee`: Gross vs. net payment deduction.
  - `timing_difference`: Clearing delay with identical amount.
  - `duplicate`: Multiple charges matching the same counter-record.
  - `wrong_vendor`: Amount matches but vendor is unrelated.
  - `transposition`: Transposition numeral swap.
  - `fx_difference`: Cross-currency settlement difference.
  - `compound_exception`: Combined fee deduction and multi-day timing delay.

---

## 4. Supplying Tools to the Architecture Generator

In upcoming milestones, the Architecture Generator will call:
```python
tools_catalog = registry.list_schemas()
```
This catalog allows the system to autonomously reason about:
1. Which tools to bind to specific agent nodes (e.g., binding `query_general_ledger` to an extraction agent and `calculate_reconciliation_difference` to an auditor agent).
2. Distinguishing read-only analytical tools from state-changing tools (`side_effect=False`).
3. Generating prompt instructions describing parameter expectations.
