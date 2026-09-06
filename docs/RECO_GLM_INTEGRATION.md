# RECO — GLM-4.7-FLASH INTEGRATION AUDIT & SPECIFICATION

**Document Version:** 1.0.0  
**Target Runtime:** Reco Autonomous Agent Engineering System (Track 1)  
**Provider:** TensorMux (`https://api.tensormux.com/v1`)  
**Verified Active Model:** `glm-4-7-flash`  

---

## 1. Executive Summary

This document specifies the architecture, integration invariants, observed runtime behaviors, and bug fixes for running `glm-4-7-flash` as Reco's primary agent inference model. 

The Step 19 integration audit verified the complete real execution path from configuration, structured output generation, multi-round tool dispatching, and topological DAG execution through to error recovery, cost accounting, and Neatlogs observability.

---

## 2. Configuration & Invariants

### 2.1 Environment Settings
The canonical environment configuration for Reco under Track 1 is:
```env
LLM_PROVIDER=tensormux
LLM_MODEL=glm-4-7-flash
TENSORMUX_BASE_URL=https://api.tensormux.com/v1
TENSORMUX_API_KEY=<configured>
```

### 2.2 Model Selection Invariant
- `glm-4-7-flash` is the single active live model.
- `gemma-4-31b` has been completely retired and is absent from all active runtime and UI pathways.
- The `TensorMuxGateway` initializes `default_model` to `settings.llm_model` (`glm-4-7-flash`).
- In `NodeRunner`, if a node's model is specified as `"mock-v1"` or omitted, `TensorMuxGateway` substitutes `default_model`.

---

## 3. Provider Request Lifecycle & Message Schema

### 3.1 Serialization
In OpenAI-compatible inference endpoints (such as TensorMux), messages exchanged during agent loops adhere to standard roles (`system`, `user`, `assistant`, `tool`):

1. **System & User Prompts:**
   - Prepend `system` instructions to the conversation.
   - User inputs pass dynamic execution context serialized as clean JSON.

2. **Assistant Tool Calls:**
   - Provider format requires:
     ```json
     {
       "role": "assistant",
       "content": "",
       "tool_calls": [
         {
           "id": "call_123",
           "type": "function",
           "function": {
             "name": "fuzzy_match_transactions",
             "arguments": "{\"vendor_similarity_threshold\": 0.85}"
           }
         }
       ]
     }
     ```
   - **Bug Fix Applied (Step 19):** `ModelMessage.tool_calls` accepts both raw dictionary objects and typed `ToolCall` instances. `TensorMuxGateway` formats both uniformly into provider-compatible specifications.

3. **Tool Execution Results:**
   - Return message format:
     ```json
     {
       "role": "tool",
       "tool_call_id": "call_123",
       "name": "fuzzy_match_transactions",
       "content": "{\"matched_pairs\": [...], \"unmatched\": []}"
     }
     ```

---

## 4. Reasoning Field Handling (`message.reasoning`)

### 4.1 Observed Provider Behavior
`glm-4-7-flash` is a reasoning model that emits internal chain-of-thought tokens in a separate message property:
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "GLM_OK",
      "reasoning": "1. Analyze request...\n2. Output string..."
    },
    "finish_reason": "stop"
  }]
}
```

### 4.2 Strict Privacy & Output Isolation Invariant
- **User-Facing Isolation:** `message.reasoning` is strictly excluded from `ModelResponse.content`. Only sanitized `content` is ever exposed to users, downstream nodes, or state outputs.
- **Persistence Isolation:** Reasoning tokens are never persisted in state outputs (`state.node_outputs`).
- **Telemetry Isolation:** Internal chain-of-thought is never forwarded to Neatlogs span attributes.
- **Answer Gate:** An empty `content` field with non-empty `reasoning` is never treated as a final answer.

---

## 5. Token Limits & Max Tokens Safety Threshold

### 5.1 The Reasoning Headroom Constraint
Because `glm-4-7-flash` generates reasoning tokens *before* emitting final content:
- If `max_tokens` is configured too low (e.g., $\le 200$ tokens for complex instructions), the model exhausts its token budget on reasoning, triggering `finish_reason: "length"` with an empty `content` string.
- Standard requests require a safety headroom of at least $500$ to $1000$ tokens.

### 5.2 Default Configuration
- `TensorMuxGateway` defaults `max_tokens = 1000`.
- This ensures sufficient capacity for ~250 reasoning tokens plus ~750 content/JSON tokens without truncation.
- Raising this default higher is discouraged to prevent latency inflation and unnecessary credit burn.

---

## 6. Structured Output & Pydantic Validation

When `response_format={"type": "json_object"}` is passed:
1. `glm-4-7-flash` produces valid JSON structures (e.g. `{"status": "VERIFIED", ...}`).
2. `TensorMuxGateway` parses this into `ModelResponse.structured_output`.
3. Downstream callers validate using strict Pydantic schemas.
4. Extra keys are safely accepted or pruned; missing keys raise structured validation errors rather than unhandled exceptions.
5. Non-JSON outputs trigger safe parser fallback to raw text.

---

## 7. Tool Calling, Fallback, & Multi-Round Loops

### 7.1 Native Tool Calling
- When tools are attached to `ModelRequest.tools`, `glm-4-7-flash` emits standard `tool_calls`.
- `NodeRunner` parses them via `resp.get_parsed_tool_calls()`, checks authorization against node permissions, runs them through `ToolExecutor`, and appends the `tool` message to the dialogue.
- In turn 2, `glm-4-7-flash` receives the tool outputs and generates the synthesis.

### 7.2 Automatic Fallback
- If the endpoint returns HTTP 400 with tool-choice limitations, `TensorMuxGateway` automatically injects tool JSON schemas into the prompt with strict formatting directives, intercepting JSON tool blocks via `_extract_tool_calls`.

### 7.3 Multi-Round Bounding
- Tool-calling agent loops are bounded by `node.metadata.get("max_tool_rounds", 5)`.
- Reaching the round limit without final output halts execution cleanly with a structured `RuntimeError` rather than entering an infinite loop.

---

## 8. Node Execution Modes

Reco supports three explicit node execution modes:
1. **`deterministic_tool`:** Direct tool dispatch via `ToolExecutor`. Bypasses LLM entirely (0 prompt tokens, 0 completion tokens, 0 latency overhead).
2. **`model_driven`:** Multi-turn ReAct agent loop allowing GLM to call authorized tools sequentially.
3. **`model_inference`:** Single-turn LLM reasoning/auditing without tool access.

---

## 9. Cost & Latency Accounting

- **Prompt Tokens:** Extracted from `usage.prompt_tokens`.
- **Completion Tokens:** Extracted from `usage.completion_tokens` (includes reasoning tokens as reported by the provider).
- **Total Tokens:** `tokens_prompt + tokens_completion`.
- **Cost Type:**
  - Marked `"actual"` only when provider returns explicit `"cost"` or `"cost_usd"`.
  - Marked `"estimated"` when derived from pricing formulas ($0.0015 / 1k in, $0.0020 / 1k out).
- **Latency Accounting:** Measured with high-precision monotonic timers (`time.perf_counter()`), distinguishing `model_latency_ms` from `tool_latency_ms`.

---

## 10. Error Handling & Retry Policies

- **HTTP Status Codes:** `400`, `401`, `404`, `429`, `500`, `503` raise structured `RuntimeError` exceptions with actionable error bodies.
- **Timeouts:** Mapped cleanly to `TimeoutError`.
- **Node-Level Retries:** If `node.max_retries > 0`, recoverable errors (e.g. `429` rate limits or transient network disconnects) trigger bounded retries.
- **Fail-Safe Containment:** Unrecoverable errors halt DAG progression, record structured errors into `state.errors`, and mark `state.status = "failed"` without crashing the server process.

---

## 11. Observability (Neatlogs)

- `NeatlogsTracer` wraps agent executions into hierarchical spans (`optimization_run -> generation -> node_execution -> model_invocation / tool_invocation`).
- Telemetry payloads strictly filter out API keys, tokens, auth headers, and held-out dataset ground truth.
- Internal reasoning content is never mirrored to span attributes.
- Tracer failures are fully contained and never interrupt runtime execution.

---

## 12. Demo Mode vs. Live Mode Isolation

- **Demo Mode:** Served via `reco/api/demo_data.py`. Returns exact Step 14 verified multi-generation artifacts ($V_0 \to V_1$, $75\% \to 80\%$ accuracy, $-10.38\%$ cost, $-20.54\%$ latency, $82.5\%$ held-out watermark, `PROMOTE` decision).
- **Live Mode:** Dispatches actual requests to TensorMux via `AgentGraphRuntime`.
- **Air-Gap Invariant:** Live failures never fall back to demo data. Demo runs are explicitly tagged with `experiment_id = "exp_step14_real_opt_001"`, and demo status banners are rendered in the UI.
