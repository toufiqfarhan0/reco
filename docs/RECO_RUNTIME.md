# Reco Agent Graph Runtime Architecture

## 1. Runtime Architecture Overview

Reco's execution substrate is a lightweight, deterministic directed acyclic graph (DAG) scheduler built in standard Python. It avoids heavyweight third-party orchestration frameworks (LangChain, LangGraph, AutoGen, CrewAI) to ensure full operational transparency, exact token/cost accounting, and zero framework prompt leakage.

```
                  ┌─────────────────────────────────────┐
                  │          GraphDefinition            │
                  │  nodes, edges, entry, terminals     │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │       DAG Validation & Order        │
                  │  - Kahn's Algo (Cycle Rejection)    │
                  │  - Reachability Analysis            │
                  │  - Deterministic Topological Sort   │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
         ┌───────────────────────────────────────────────────────┐
         │                  Execution Loop                       │
         │                                                       │
         │    For each node in topological order:                │
         │                                                       │
         │    ┌─────────────────────────────────────────────┐    │
         │    │                 NodeRunner                  │    │
         │    │  1. Resolve context via input_mapping       │    │
         │    │  2. Dispatch tools via ToolExecutor         │    │
         │    │  3. Model reasoning via ModelGateway        │    │
         │    │  4. Bounded error retries (max_retries)     │    │
         │    │  5. Return NodeExecutionResult              │    │
         │    └──────────────────────┬──────────────────────┘    │
         │                           │                           │
         │                           ▼                           │
         │    ┌─────────────────────────────────────────────┐    │
         │    │               ExecutionState                │    │
         │    │  - Record node output by output_key         │    │
         │    │  - Accumulate tokens (in/out)               │    │
         │    │  - Accumulate USD costs ($)                 │    │
         │    │  - Accumulate wall-clock duration (ms)      │    │
         │    │  - Block downstream nodes on failure        │    │
         │    └─────────────────────────────────────────────┘    │
         └───────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │        Final ExecutionState         │
                  │  status: completed | failed         │
                  │  terminal outputs, telemetry trace  │
                  └─────────────────────────────────────┘
```

---

## 2. Core Models

Defined in [`reco/engine/models.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/engine/models.py):

### NodeModel
- `node_id: str`: Unique node key.
- `name: str`: Descriptive title.
- `role: str`: Functional specialization (e.g., `'Normalizer'`, `'Auditor'`).
- `system_prompt: str`: Agent instructions.
- `tools: List[str]`: Allowed tools from the `ToolRegistry`.
- `model_config: dict`: LLM parameters (`model`, `temperature`).
- `input_mapping: dict`: Maps state keys/dot paths to node parameters.
- `output_key: Optional[str]`: Key for storing results in state (defaults to `node_id`).
- `max_retries: int`: Maximum retry attempts for recoverable errors.
- `retryable_errors: List[str]`: Substrings triggering retries.

### EdgeModel & GraphDefinition
- Validates that the entry node exists and all edge endpoints are valid.
- Rejects duplicate edges and unreachable nodes.
- Enforces strict DAG properties: Kahn's algorithm rejects any cyclic structures with `GraphValidationError`.
- Produces a deterministic topological sequence for execution.

---

## 3. Execution State & Context Handling

Implemented in [`reco/engine/state.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/engine/state.py):
- **Serializability**: Pure JSON-compatible dictionaries; safe for database persistence.
- **Context Resolution**: Supports root keys (`inputs`, `node_outputs`, `goal`) as well as dot notation (e.g. `"parsed_statement.transactions"`).
- **Context Compaction**: `compact_context()` prunes overly large intermediate transaction arrays to avoid memory bloat.
- **Telemetry Aggregation**:
  - `tokens_input` and `tokens_output`: Accumulated across all node steps.
  - `cost_usd`: Summed across model calls.
  - `latency_ms`: Total end-to-end wall-clock duration.
  - `tool_events`: Complete audit log of every tool call, inputs, execution duration, and success flag.

---

## 4. Error Handling & Downstream Blocking

- **Fatal Node Failure**: If an unhandled error or exhausted retry occurs, `ExecutionState.status` transitions to `'failed'`, the error is logged, and downstream execution is terminated immediately.
- **Bounded Retries**: Configurable per node; retry count is tracked in `NodeExecutionResult.attempts`. Non-retryable errors abort on attempt 1.
