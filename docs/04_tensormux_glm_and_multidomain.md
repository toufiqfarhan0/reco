# AGY Prompt 04 — TensorMux GLM-4.7-Flash Integration & Multi-Domain Benchmarks

## AO Session Setup
```bash
# 1. Create GitHub Issue
# Title: feat: tensormux live glm-4.7-flash provider and multi-domain evaluation

# 2. Spawn AO Session
ao session spawn --name "04-tensormux-multidomain" --issue 4

# 3. Run with AGY CLI
agy --file docs/prompts/04_tensormux_glm_and_multidomain.md
```

---

## Objective
Connect live LLM inference to **TensorMux** using `glm-4-7-flash` (GLM-4.7-Flash) with full support for structured output and tool calling. Expand benchmark coverage across three distinct, challenging domains to prove generalized agent engineering capability.

## Context & Architecture
- System: **Reco** (Autonomous Agent Engineering System)
- Provider: **TensorMux** (`https://api.tensormux.com/v1`)
- Model: `glm-4-7-flash`
- Reference Docs:
  - [GLM-4.7-Flash Integration Audit](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_GLM_INTEGRATION.md)
  - [Multi-Domain Benchmarking Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_MULTI_DOMAIN.md)
  - [LLM Runtime Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_LLM_RUNTIME.md)

## Requirements to Implement

### 1. TensorMux Client Provider (`reco/llm/tensormux.py`)
- Implement OpenAI-compatible HTTP client for TensorMux:
  - Base URL: `https://api.tensormux.com/v1`
  - Model: `glm-4-7-flash`
  - Authorization: Bearer token from `TENSORMUX_API_KEY`
- Support native tool-calling protocol (`tools` array, `tool_calls` response parsing, tool execution loop).
- Support structured JSON completion with reliable parsing.
- Handle GLM-4.7-Flash reasoning tokens (`reasoning` message field) and enforce `max_tokens >= 400` to prevent output truncation.
- Accurately track live tokens and compute execution costs based on official provider rates.

### 2. Multi-Domain Benchmarks (`reco/benchmarks/`)
Implement three distinct real-world evaluation domains:
1. **Financial Reconciliation** (`reco/benchmarks/reconciliation/`):
   - Ledger queries, statement parsing, fuzzy matching, and discrepancy calculation.
2. **System Anomaly Detection** (`reco/benchmarks/anomaly/`):
   - Server metrics analysis, threshold evaluation, and root-cause incident diagnosis.
3. **Research Synthesis & Competitive Analysis** (`reco/benchmarks/research/`):
   - Unstructured document parsing, entity extraction, metric cross-referencing, and summary generation.

### 3. Domain Tools Integration
- Register dedicated domain tools in `ToolRegistry`:
  - Anomaly tools: `compute_zscore`, `check_threshold`, `extract_error_logs`.
  - Research tools: `extract_entities`, `compare_metrics`, `summarize_text`.

## Verification & Acceptance Criteria
1. TensorMux client executes live completions, tool calls, and structured JSON parsing cleanly.
2. All 3 benchmark domains load partitioned datasets (optimization vs held-out) with zero cross-contamination.
3. Pass all unit tests:
   ```bash
   python -m pytest tests/test_llm_execution.py tests/test_glm_integration_audit.py tests/test_step23_multi_domain.py -v
   ```
