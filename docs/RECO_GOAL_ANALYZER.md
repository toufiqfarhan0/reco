# Reco Goal & Task Specification Parser (Milestone 5)

## 1. Goal Analyzer Architecture Overview

The **Goal Analyzer** is the translation boundary between unconstrained human intent and Reco's autonomous agent architecture generation pipeline. It receives:
1. A raw natural-language goal statement
2. The active tool catalog schema (`ToolRegistry.list_schemas()`)
3. Optional success evaluation criteria / benchmark expectations

It produces a strongly-typed, machine-readable, domain-agnostic `TaskSpecification`.

```
                    ┌─────────────────────────────────────────┐
                    │      Human Goal (Natural Language)      │
                    │   + Tool Catalog (list_schemas())       │
                    │   + Optional Evaluator Criteria         │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │            normalize_goal()             │
                    │   - Whitespace consolidation            │
                    │   - Length boundary enforcement         │
                    │   - Empty/whitespace rejection          │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │       LLM Decomposition Gateway         │
                    │       (Provider-Agnostic Model)         │
                    │   - Structured JSON Prompting           │
                    │   - Pydantic Schema Validation          │
                    │   - Bounded 1-Retry Repair              │
                    └───────────┬───────────────────┬─────────┘
                                │ (success)         │ (failure or offline)
                                ▼                   ▼
                    ┌────────────────────┐ ┌────────────────────┐
                    │ Valid Spec Parsed  │ │ Deterministic Rule │
                    │                    │ │ Fallback Parser    │
                    └───────────┬────────┘ └────────┬───────────┘
                                │                   │
                                └─────────┬─────────┘
                                          ▼
                    ┌─────────────────────────────────────────┐
                    │          _sanitize_tools()              │
                    │   - Strict Anti-Fabrication Filter      │
                    │   - Purge uncataloged suggestions       │
                    │   - Flag unavailable capabilities       │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │          TaskSpecification              │
                    │   Consumed by Architecture Generator    │
                    └─────────────────────────────────────────┘
```

---

## 2. Core Models

### TaskSpecification ([`reco/core/task_spec.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/core/task_spec.py))

| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | `str` | UUID identifying the synthesized task specification |
| `original_goal` | `str` | Exact verbatim user string |
| `normalized_goal` | `str` | Preprocessed, normalized user statement |
| `domain` | `str` | Informational classification (`finance`, `research`, `data`, `coding`, `general`) |
| `objective` | `str` | Concise core actionable outcome |
| `subtasks` | `List[Subtask]` | Ordered functional subtasks establishing execution dependencies |
| `required_capabilities` | `List[Capability]` | Domain-neutral capability requirements |
| `available_tool_ids` | `List[str]` | Complete set of tool names provided in the catalog |
| `suggested_tool_bindings` | `List[ToolRecommendation]` | Recommended tool bindings (must be a strict subset of `available_tool_ids`) |
| `inputs` | `Dict[str, Any]` | Inferred or explicit workflow input schema |
| `expected_outputs` | `Dict[str, Any]` | Inferred or explicit workflow output schema |
| `constraints` | `List[str]` | Behavioral, budget, format, and precision boundaries |
| `verification_requirements`| `List[str]` | Validation rules (arithmetic, citations, schema, consistency) |
| `risk_level` | `Literal["low", "medium", "high"]` | Operational risk level assessed from tools and actions |
| `side_effect_requirements` | `bool` | Whether the goal requires mutating external state |
| `ambiguity_flags` | `List[str]` | Detected uncertainties, missing inputs, or unspecified metrics |
| `requires_clarification` | `bool` | High-ambiguity indicator (ambiguities >= 2) |
| `confidence` | `float` | Bounded heuristic score in `[0.20, 1.00]` |
| `evaluator_requirements` | `Optional[EvaluatorSpecification]` | Upstream evaluation and verification benchmarks |
| `metadata` | `Dict[str, Any]` | Execution metadata (parser mode, repair status, errors) |

---

## 3. Subtask Model

Each `Subtask` encapsulates a functional step that the subsequent Architecture Generator will map into graph nodes:

```python
class Subtask(BaseModel):
    id: str                                  # Unique identifier e.g. "subtask_1"
    description: str                         # Summary of work
    objective: str                           # Target outcome
    required_capabilities: List[Capability]  # Capabilities needed
    preferred_tools: List[str]               # Recommended tool names
    expected_input: Dict[str, Any]           # Step input schema
    expected_output: Dict[str, Any]          # Step output schema
    verification_needed: bool = False        # Audit requirement flag
    dependencies: List[str] = []             # List of predecessor subtask IDs
```

---

## 4. Controlled Capability Taxonomy

The capability representation is strictly domain-neutral and avoids sprawling taxonomy:

```python
class Capability(str, Enum):
    RETRIEVAL = "retrieval"
    STRUCTURED_LOOKUP = "structured_lookup"
    CALCULATION = "calculation"
    COMPARISON = "comparison"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    TRANSFORMATION = "transformation"
    REASONING = "reasoning"
    VERIFICATION = "verification"
    SUMMARIZATION = "summarization"
    ANOMALY_DETECTION = "anomaly_detection"
    EVIDENCE_COLLECTION = "evidence_collection"
    DECISION_MAKING = "decision_making"
```

---

## 5. Tool Catalog Input & Anti-Fabrication Guarantee

The parser accepts `ToolRegistry.list_schemas()` output directly.

### Strict Anti-Fabrication Rule
An LLM or heuristic analyzer **must never fabricate tools**.
- Every tool in `suggested_tool_bindings` and every tool in `subtask.preferred_tools` must exist in `available_tool_ids`.
- `TaskSpecification.validate_tool_integrity()` raises `ValueError` if a fabricated tool is detected.
- `GoalAnalyzer._sanitize_tools()` automatically strips uncataloged tools and records an ambiguity flag:
  `unavailable_capability: tool '<tool_name>' requested but not in catalog`.

```python
class ToolRecommendation(BaseModel):
    tool_name: str
    relevance_score: float  # 0.0 to 1.0
    reason: str
    required: bool = False
    confidence: float = 0.80
```

---

## 6. Evaluator Specification

Evaluator benchmarks are preserved to inform agent verification node synthesis:

```python
class EvaluatorSpecification(BaseModel):
    required_output_properties: List[str]    # e.g., ["matched_count", "net_difference"]
    correctness_criteria: List[str]          # e.g., ["Net difference equals sum of exceptions"]
    constraint_checks: List[str]             # e.g., ["No negative inventory"]
    evidence_requirements: List[str]         # e.g., ["Must cite row IDs for discrepancies"]
    threshold_conditions: Dict[str, float]   # e.g., {"accuracy": 0.99, "max_latency_sec": 5.0}
```

---

## 7. Ambiguity Handling & Confidence Semantics

### Ambiguity Classes
The analyzer flags common underspecifications:
- `missing_input`: Dataset, file path, or input stream was not defined.
- `unspecified_success_criteria`: Quantitative threshold or tolerance not defined.
- `ambiguous_output_format`: Output format (JSON, table, report) was not explicitly requested.
- `unclear_scope`: Goal statement is too brief (< 4 words).
- `conflicting_requirements`: Opposing demands (e.g. "read-only" and "delete records").
- `unavailable_capability`: User requested functionality for which no tool is registered.

### Confidence Score Semantics
The score is a bounded heuristic (not an uncalibrated probability):
- Baseline: `0.90`
- Penalties: `-0.10` per detected ambiguity
- Clamped range: `[0.20, 1.00]`
- If `len(ambiguities) >= 2`, `requires_clarification` is set to `True`.

---

## 8. Deterministic Fallback & Provider-Agnostic LLM Boundary

### Provider-Agnostic ModelGateway
When a `ModelGateway` (such as `MockModelGateway` or a future LLM gateway) is passed to `GoalAnalyzer`:
1. The goal and tool catalog are prompted to produce a structured JSON `TaskSpecification`.
2. Output is validated against the Pydantic schema.
3. If JSON parsing or validation fails, exactly **one bounded repair attempt** is performed.
4. If repair fails:
   - If `fallback_on_error=False`, raises `RuntimeError`.
   - If `fallback_on_error=True`, logs a warning, falls back to deterministic parsing, and records the error in `spec.metadata["llm_error"]` and `spec.ambiguity_flags`.

### Deterministic Rule-Based Fallback
If `model_gateway=None` or during complete network isolation:
- Derives domain and capabilities via keyword stems (`calculat`, `reconcil`, `anomal`, `diagnos`).
- Computes tool relevance scores against the provided catalog.
- Generates a canonical 3-stage subtask pipeline (Ingest/Normalize -> Core Processing -> Verify/Format).
- Infers schemas, constraints, verification requirements, and risk levels deterministically.

---

## 9. Multi-Domain Generalization Examples

### 1. Finance Reconciliation
- **Goal**: `"Reconcile these bank transactions against the general ledger."`
- **Domain**: `finance`
- **Capabilities**: `CALCULATION`, `COMPARISON`, `REASONING`
- **Inferred Inputs**: `bank_transactions`, `general_ledger`
- **Inferred Outputs**: `reconciliation_summary`

### 2. Research & Comparison
- **Goal**: `"Compare the top three open-source observability platforms for Python."`
- **Domain**: `research`
- **Capabilities**: `COMPARISON`, `RETRIEVAL`, `SUMMARIZATION`, `REASONING`
- **Inferred Inputs**: `research_query`
- **Inferred Outputs**: `comparative_analysis`

### 3. Data Anomaly Detection
- **Goal**: `"Find anomalies in this CSV and explain the likely causes."`
- **Domain**: `data`
- **Capabilities**: `ANOMALY_DETECTION`, `EXTRACTION`, `TRANSFORMATION`, `REASONING`
- **Inferred Inputs**: `dataset`
- **Inferred Outputs**: `anomalies_and_causes`

### 4. Coding & Root-Cause Diagnosis
- **Goal**: `"Diagnose this failing test suite and propose the most likely root cause."`
- **Domain**: `coding`
- **Capabilities**: `REASONING`, `VERIFICATION`
- **Inferred Inputs**: `test_suite_or_logs`
- **Inferred Outputs**: `diagnosis_and_fix`

---

## 10. API Endpoint

An internal test endpoint is available on the FastAPI app:

```http
POST /analyze-goal
Content-Type: application/json

{
  "goal": "Reconcile bank statements against general ledger in json format",
  "available_tools": null,
  "evaluator_spec": null
}
```

Returns `200 OK` with the complete `TaskSpecification` JSON payload, or `400 Bad Request` if the goal is empty or invalid.
