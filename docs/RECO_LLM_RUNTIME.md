# Reco LLM Runtime & Structured Tool-Calling Architecture

## 1. Overview

Milestone 11 establishes real, provider-agnostic LLM execution and structured tool-calling in Reco. This enables agents in the Reco graph runtime to dynamically converse with an LLM, emit structured tool calls, receive execution results from the `ToolExecutor`, continue reasoning, and return validated structured outputs.

```
                  ┌────────────────────────────────────────┐
                  │               NodeRunner               │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                        Construct Provider-Neutral
                               ModelRequest
                    (messages, tools, schema, config)
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │              ModelGateway              │
                  │              (Abstraction)             │
                  └─────────┬────────────────────┬─────────┘
                            │                    │
                   ┌────────┴────────┐  ┌────────┴────────┐
                   │MockModelGateway │  │TensorMuxGateway │
                   │  (Unit Tests)   │  │ (Live Provider) │
                   └─────────────────┘  └─────────────────┘
                                      │
                                      ▼
                                ModelResponse
                     (content, tool_calls, tokens, cost)
                                      │
                                      ▼
                             Tool Calls Detected?
                            ┌─────────┴─────────┐
                         YES│                   │NO
                            ▼                   ▼
                  ┌───────────────────┐    Validate Final Output
                  │   Tool Authorization│    (Schema / JSON)
                  │   - in node.tools?│         │
                  │   - in registry?  │         ▼
                  └─────────┬─────────┘    NodeExecutionResult
                            │
                            ▼
                  ┌───────────────────┐
                  │    ToolExecutor   │
                  └─────────┬─────────┘
                            │
                            ▼
                  Append Tool Result to
                    Context Messages
                            │
                            ▼
                   Loop next round (<= 5)
```

---

## 2. ModelGateway Architecture & Provider Abstraction

The runtime remains strictly decoupled from individual LLM vendors or proxies. The abstract interface is defined in [`reco/core/interfaces.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/core/interfaces.py):

```python
class ModelGateway(ABC):
    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        pass
```

### Provider Implementations

1. **`MockModelGateway`** ([`reco/llm/mock.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/llm/mock.py)):
   - Fast, deterministic, offline execution for standard unit and benchmark tests.
   - Supports pre-configured response sequences, simulated tool-call rounds, malformed tool arguments, malformed output schemas, and mock exceptions.
   - Explicitly marks all generated cost metadata as `cost_type="simulated_mock"`.

2. **`TensorMuxGateway`** ([`reco/llm/tensormux.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/llm/tensormux.py)):
   - Concrete production adapter utilizing TensorMux API routing (`POST /v1/chat/completions`).
   - Translates provider-neutral `ModelRequest` to OpenAI-compatible chat completion payload.
   - Bounded async network timeouts (default: 30.0s).
   - Extracts input/output tokens, finish reasons, and tool calls.
   - Marks cost metadata as `cost_type="actual"` if reported or `"estimated"` with published rates.

3. **`get_model_gateway(provider_name)`** ([`reco/llm/factory.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/llm/factory.py)):
   - Instantiates gateways based on environment variables or explicit parameters (`"mock"`, `"tensormux"`).
   - Defaults safely to `"mock"` in test environments.

---

## 3. Request / Response Lifecycle

### `ModelRequest`
- `messages: List[ModelMessage]`: Structured conversation history (`system`, `user`, `assistant`, `tool`).
- `system_prompt: Optional[str]`: Injected as the primary system directive.
- `tools: List[Dict[str, Any]]`: OpenAI-compatible function definitions translated from `ToolRegistry`.
- `temperature: float`: Sampling temperature (default: `0.0` for deterministic evaluation).
- `max_tokens: int`: Token budget per completion.
- `response_format: Optional[Dict[str, Any]]`: Structured JSON schema constraint.
- `metadata: Dict[str, Any]`: Node and experiment context.

### `ModelResponse`
- `content: Optional[str]`: Assistant message body.
- `tool_calls: List[Dict[str, Any]]`: Raw or structured tool invocation requests.
- `tokens_prompt: int`: Input tokens consumed.
- `tokens_completion: int`: Output tokens generated.
- `cost_usd: float`: Measured dollar cost.
- `cost_type: str`: Explicit enum: `"actual"`, `"estimated"`, or `"simulated_mock"`.
- `latency_ms: int`: Provider latency in milliseconds.
- `finish_reason: Optional[str]`: E.g. `"stop"`, `"tool_calls"`.
- `get_parsed_tool_calls()`: Helper parsing `tool_calls` into typed `ToolCall` instances.

---

## 4. Structured Tool Calling & Tool Authorization

Tool calling follows strict safety boundaries:

1. **Schema Translation**: `tool_to_function_schema()` in [`reco/llm/tools.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/llm/tools.py) inspects tool signatures in `ToolRegistry` and outputs OpenAI-compatible function declarations.
2. **Authorized Whitelist**: A node only presents `node.tools` to the model.
3. **Runtime Authorization Check**: When the model emits a `ToolCall`:
   - If `call.name not in node.tools`: The call is rejected immediately.
   - If `call.name not in tool_registry`: The call is rejected immediately.
   - Rejected tool calls produce a structured tool error response appended to the message history:
     ```json
     {"error": "Unauthorized tool 'x'. Node 'y' is only authorized to call: [...]"}
     ```
   - An event with `"success": False` is recorded in `ExecutionState.tool_events`.
4. **Tool Execution**: Authorized calls pass arguments to `ToolExecutor.execute()`.
5. **Observation Feedback**: The result JSON is injected as a message with role `"tool"` and the corresponding `tool_call_id`.
6. **Bounded Loop**: The reasoning loop is strictly bounded by `MAX_TOOL_CALL_ROUNDS = 5`. If the model exceeds this bound without terminating, execution halts with a bounded error.

---

## 5. Token, Cost, and Latency Accounting

All token usage and costs are faithfully accumulated across every model round:
- **`tokens_in`**: Accumulated input tokens across all tool-call rounds.
- **`tokens_out`**: Accumulated completion tokens across all tool-call rounds.
- **`cost_usd`**: Aggregated monetary cost.
- **`cost_type`**: Preserves provider fidelity (`"actual"`, `"estimated"`, `"simulated_mock"`).
- **`latency_ms`**: Measured wall-clock time in milliseconds.

---

## 6. Retries and Timeouts

- **Bounded Network Timeouts**: `TensorMuxGateway` enforces a configurable timeout (default 30 seconds). Timeout exceptions are translated to `ModelGatewayError` and recorded as structured node failures.
- **Node-Level Retries**: Utilizes the existing `node.max_retries` and `node.retryable_errors` configuration. Non-retryable model or tool failures fail fast on attempt 1.

---

## 7. Mutation Propagation Compatibility

A core guarantee of Milestone 11 is that mutations to the agent graph directly impact the LLM runtime request:

1. **Prompt Mutation**:
   - Mutating `NodeModel.system_prompt` alters the system prompt sent in `ModelRequest`.
   - Verified by test `test_19_prompt_mutation_reaches_model`.
2. **Tool Mutation**:
   - Adding or removing tools from `NodeModel.tools` dynamically alters the available functions presented in `ModelRequest.tools`.
   - Verified by test `test_20_tool_mutation_reaches_model`.
3. **Model Configuration Mutation**:
   - Mutating `node.model_config` (e.g. changing model from `qwen/qwen-2.5-72b-instruct` to `anthropic/claude-3-5-sonnet`) directly modifies `ModelRequest.model` and sampling parameters.
   - Verified by test `test_21_model_mutation_reaches_model`.
4. **Context Mapping Mutation**:
   - Mutating `node.input_mapping` dynamically updates the inputs formatted into the model's user message.
   - Verified by test `test_22_context_mutation_reaches_execution`.

---

## 8. Opt-In Live Smoke Test

Live provider testing is strictly opt-in and will never run during standard CI or automated pytest runs:
- **Environment Flags Required**:
  ```bash
  export RUN_LIVE_LLM_TESTS=true
  export TENSORMUX_API_KEY="your-key"
  ```
- **Test Target**: `test_34_opt_in_real_provider_smoke_test` in `tests/test_llm_execution.py`.
- Evaluates fuzzy matching between two transactions using real model inference, validating tool invocation, token accounting, and final structured output without hardcoding expected prose.
