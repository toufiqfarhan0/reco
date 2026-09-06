# RECO EXECUTION MODES ARCHITECTURE

## Overview

In Reco (Track 1 — Automated Agent Engineering), agent nodes execute within a directed acyclic graph (DAG). Following the foundational architectural principle:

```
DETERMINISTIC WORK   → Deterministic tool execution (Zero LLM calls)
REASONING / DECISION → Model-driven agent execution (ModelGateway + structured tool calls)
PURE AUDIT / PROSE  → Model inference (Direct LLM generation without tools)
```

By explicitly decoupling execution modes at the node level, Reco eliminates unnecessary LLM calls for deterministic parsing, querying, and arithmetic, while ensuring reasoning nodes genuinely receive prompt mutations, control tool parameters, and produce observable behavioral divergence.

---

## The Execution Mode Contract

Every `NodeModel` explicitly declares its execution mode via the `execution_mode` field:

```python
execution_mode: Optional[Literal["deterministic_tool", "model_driven", "model_inference"]] = None
```

The node's effective execution mode is resolved deterministically via `node.get_execution_mode()`:

1. `self.execution_mode` if explicitly specified.
2. `self.metadata["execution_mode"]` if present in metadata.
3. `"model_driven"` if `self.metadata.get("agent_loop") is True` or if `NodeRunner(agent_mode=True)` is set without explicit node override.
4. `"deterministic_tool"` if `self.tools` is non-empty.
5. `"model_inference"` fallback when no tools are bound.

---

## Execution Modes Deep Dive

### 1. `deterministic_tool` Mode

* **Purpose**: Ingestion, normalization, querying, and exact mathematical operations.
* **Flow**:
  ```
  NodeRunner
      ↓
  Context resolution (input_mapping)
      ↓
  ToolExecutor.execute(tool_name, context)
      ↓
  State audit trail & output recording (Zero Model Calls)
  ```
* **Guarantees**:
  * $0.00$ LLM token and API cost.
  * Sub-millisecond latency (pure in-memory Python math and parsing).
  * 100% deterministic, zero hallucination risk.
* **Nodes in Baseline**:
  * `parse_statement` (`parse_bank_statement` tool)
  * `query_ledger` (`query_general_ledger` tool)

### 2. `model_driven` Mode

* **Purpose**: Complex matching, semantic entity resolution, ambiguity resolution, and decision-making where prompts and policies govern execution.
* **Flow**:
  ```
  fuzzy_match node
      ↓
  ModelGateway (System prompt + Authorized tool schemas + Context)
      ↓
  Model generates structured tool call: fuzzy_match_transactions(...)
      ↓
  ToolExecutor validates & executes tool with model-specified arguments
      ↓
  Tool result data returned in conversation (role="tool")
      ↓
  Model completes reasoning turn & produces final structured output
  ```
* **Key Architecture Features**:
  * **Model Controls Tool Arguments**: The LLM decides crucial tuning parameters such as `vendor_similarity_threshold`, `require_vendor_match`, `date_tolerance_days`, and `amount_tolerance`.
  * **Context Merging**: NodeRunner merges upstream context (e.g. `bank_transactions`, `ledger_entries`) if the model specifies only tuning parameters, ensuring robust execution while respecting model parameter overrides.
  * **Structured Payload Preservation**: If the model provides a textual synthesis or audit rationale, NodeRunner preserves the underlying structured `matched_pairs` and `exceptions_by_type` so downstream evaluators and nodes receive clean records.
* **Nodes in Baseline**:
  * `fuzzy_match` (`fuzzy_match_transactions` tool)

### 3. `model_inference` Mode

* **Purpose**: Final verification, auditing, summary prose, or synthesis where no external tools are invoked.
* **Flow**:
  ```
  NodeRunner → ModelGateway.generate(prompt + context) → Formatted output
  ```
* **Nodes in Baseline**:
  * `verify_summary`

---

## Reconciliation Architecture Summary

| Node ID | Role | Tool Bound | Execution Mode | Model Calls | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `parse_statement` | Extractor | `parse_bank_statement` | `deterministic_tool` | 0 | Strict Decimal parsing; zero reasoning needed. |
| `query_ledger` | Querier | `query_general_ledger` | `deterministic_tool` | 0 | Deterministic query of supplied ledger entries. |
| `fuzzy_match` | Matcher | `fuzzy_match_transactions` | `model_driven` | 1–2 | Model reasons over vendor tokens, sets thresholds, and executes matching. |
| `verify_summary` | Auditor | *None* | `model_inference` | 1 | Audits upstream summary; receives prompt & model mutations. |

---

## Mutation Propagation & Behavioral Path

The fundamental issue in Step 13B was that prompt mutations could not reach `fuzzy_match` because it ran deterministically in Mode B. In Step 13C:

```
Optimizer Mutation Engine
    ↓
PROMPT_CHANGE / TOOL_ADD / MODEL_CHANGE
    ↓
Mutated NodeModel (execution_mode="model_driven")
    ↓
ModelGateway ModelRequest (Mutated system prompt & tool schema)
    ↓
Model produces different tool arguments:
  e.g., require_vendor_match=True, vendor_similarity_threshold=0.85
    ↓
ToolExecutor runs fuzzy_match_transactions with new arguments
    ↓
Reconciliation behavior diverges (false vendor matches rejected)
    ↓
Benchmark Accuracy increases (e.g., 75% → 80% on REC-OPT-08)
```

---

## Latency & Telemetry Breakdown

Execution telemetry captures granular timings for economic and latency profiling:

* `model_latency_ms`: Cumulative duration of all LLM inference calls in the node.
* `tool_latency_ms`: Cumulative duration of all tool executions in the node.
* `model_calls`: Count of LLM API roundtrips.
* `tool_calls`: Count of tool invocations.
* `round_breakdown`: Per-round trace recording `round`, `model_latency_ms`, `tool_latency_ms`, `tool_called`, and `tool_arguments`.
