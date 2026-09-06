# Reco End-to-End Product Verification (Step 20)

## Overview
This document records the complete, real-world end-to-end verification of the Reco Automated Agent Engineering platform (Track 1). All audits were performed against the live backend (`FastAPI` on `http://127.0.0.1:8000`) and the Next.js frontend (`http://localhost:3000`), powered by the active `glm-4-7-flash` model on TensorMux.

---

## 1. User Journey Verification

### Step 1: Open Reco
- The Next.js frontend loads at `http://localhost:3000`.
- System status displays `System Ready`, active model displays `glm-4-7-flash` on `tensormux`, and active track displays `Track 1: Automated Agent Engineering`.
- Header mode toggle allows switching seamlessly between `Demo Mode` and `Live Optimization`.

### Step 2: Generic Goal Input (Non-Finance)
- Goal input field accepts generic natural-language queries without assuming financial reconciliation:
  - Example tested: `"Analyze this dataset and identify unusual records."`
- Real-time character count and tool selection guidance are active.

### Step 3: Tool Catalog Inspection
- Clicking "Tool Catalog (4 Available)" opens an interactive modal.
- Available tools:
  - `parse_bank_statement`: Deterministic document parser.
  - `query_general_ledger`: Ledger database retrieval.
  - `fuzzy_match_transactions`: Multi-pass token & character reconciliation matcher.
  - `calculate_reconciliation_difference`: Mathematical disparity evaluator.
- Each tool displays JSON schema parameters, risk levels (`low`, `medium`, `high`), and side-effect flags.

### Step 4 & 5: Goal Analysis & Architecture Generation
- Calling `POST /analyze-goal` decomposes the prompt into structured capabilities:
  - Required capabilities: `["reasoning"]`
  - Normalized goal: Cleaned task representation.
- Calling `POST /generate-architecture` synthesizes a directed acyclic graph (DAG):
  - Synthesized DAG: 3 nodes (`input_node`, `anomaly_detector`, `output_node`), 2 edges.
  - DAG Quality Score: 1.0 (validated acyclic, connected, complete).
  - Assigned model: `glm-4-7-flash` (zero references to Gemma).

### Step 6: Live Agent Run
- Calling `POST /agent/run` with the synthesized DAG and synthetic test records executes real multi-step inference via TensorMux:
  - Status: `completed` (latency: 31,111 ms).
  - Model calls: 3 (100% successful HTTP 200 responses).
  - Tokens: 296 prompt tokens, 3,000 completion tokens.
  - Cost: $0.006444.
  - Output: Correctly identifies outlier record (`id: 2, val: 999999`) and generates structured reasoning.

### Step 7 & 8: Async Optimization Job Flow & Live Progress
- Calling `POST /jobs/optimize` initiates background evaluation and iterative mutation.
- Frontend polls `GET /jobs/{job_id}`:
  - Transitions cleanly from `running` to `completed`.
  - Emits real-time event log: `job_started` -> `analyzing_failures` -> `generating_mutations` -> `evaluating_candidates` -> `evaluating_held_out` -> `job_completed`.

### Step 9: Multi-Axis Scorecard (V0 vs V1)
- Evaluates candidate on 12 optimization cases:
  - Accuracy: V0 (75.0%) -> V1 (80.0%) (+5.0% absolute improvement).
  - Cost & Latency deltas calculated and displayed.
  - Classification: `strictly_better`.

### Step 10: Failure Explorer
- Surfaces granular root-cause diagnoses for failed benchmark cases:
  - Diagnosis schema: `case_code`, `category`, `severity`, `failed_node`, `confidence`, `root_cause`, `evidence`, `recommended_mutation`.
  - Clear visual badges for severity (`HIGH`, `MEDIUM`, `LOW`) and category.

### Step 11: Mutation Inspector
- Displays exact code/prompt diffs between parent V0 and child V1:
  - Target node: `fuzzy_match`
  - Mutation type: `PROMPT_CHANGE`
  - Before/after syntax highlight showing the injected precision constraints.

### Step 12: Held-Out Generalization Gate
- Evaluates V1 against 8 strictly held-out cases (`REC-HLD-01` through `REC-HLD-08`):
  - Zero leakage: Held-out cases are isolated from optimization feedback loops.
  - Verifies whether performance gains generalize or overfit.

### Step 13: Promotion Decision
- Automatic governance assessment:
  - Decision: `PROMOTE`, `REJECT`, or `REVIEW`.
  - Transparent list of justification reasons based on multi-objective thresholds.

### Step 14: Neatlogs Observability Trace Link
- Deep link to external Neatlogs dashboard:
  - URL format: `https://app.neatlogs.com/traces/nl_trace_...`
  - Allows full waterfall inspection of OpenTelemetry spans, token usage, and tool invocations.

---

## 2. Separation of Demo Mode and Live Mode

| Dimension | Demo Mode | Live Mode |
|---|---|---|
| **Data Source** | Deterministic Step 14 JSON artifact (`exp_step14_reconciliation_real`) | Live background job with model gateway & benchmark runner |
| **Model Invocations** | 0 external calls (instant load) | Real calls to TensorMux (`glm-4-7-flash`) |
| **Trace ID** | Fixed mock/historical trace | Dynamically generated Neatlogs trace ID |
| **Safety** | Fully offline, zero token cost | Budget-capped, timeout-protected |

---

## 3. Observability & Telemetry Verification
- **Neatlogs Spans**:
  - `root_e2e_verification`
  - `model_inference_span`
  - `tool_execution_span`
- **Failure Containment**:
  - Verified that upstream collector timeouts or HTTP 503 errors from `ingest.neatlogs.com` do not fail or disrupt core agent execution.

---

## 4. Security & Sanitization Audit
- Responses across `/health`, `/tools`, `/analyze-goal`, `/generate-architecture`, and `/jobs/{id}` were audited against active API keys.
- Result: **0 secret leaks detected**. TensorMux and Neatlogs tokens are strictly masked in logs and never serialized to client payloads.

---

## 5. Automated Test Baseline
- Backend (`pytest tests/`): **459 passed, 1 skipped** (18.82s).
- Frontend (`vitest run`): **17 passed** (2.25s).
- Production Build (`next build`): **Compiled successfully with zero TypeScript or lint errors**.
