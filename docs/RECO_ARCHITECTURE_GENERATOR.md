# Reco Architecture Generator V0 (Milestone 6)

## 1. Architecture Generator Overview

The **Architecture Generator** is the core synthesis engine of Reco. It translates an analyzed, domain-neutral `TaskSpecification` into a valid, executable `GraphDefinition` that runs on Reco's lightweight DAG runtime.

```
                    ┌─────────────────────────────────────────┐
                    │            TaskSpecification            │
                    │   + Tool Catalog (list_schemas())       │
                    │   + Evaluator Benchmark Criteria        │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │          ArchitectureGenerator          │
                    │                                         │
                    │  ┌───────────────────────────────────┐  │
                    │  │ ModelGateway (Provider-Agnostic)  │  │
                    │  │ - Structured JSON Prompting       │  │
                    │  │ - Pydantic Schema Validation      │  │
                    │  │ - Bounded 1-Retry Repair          │  │
                    │  └─────────────────┬─────────────────┘  │
                    │                    │ (fallback)         │
                    │                    ▼                    │
                    │  ┌───────────────────────────────────┐  │
                    │  │ Deterministic Fallback Synthesizer│  │
                    │  │ - Subtask DAG mapping             │  │
                    │  │ - Tool parameter auto-inference   │  │
                    │  │ - Canonical archetype fallback    │  │
                    │  └───────────────────────────────────┘  │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │      Deterministic Validation Pipeline  │
                    │   1. Topological DAG invariants         │
                    │   2. Tool authorization / anti-fabrication│
                    │   3. Capability coverage analysis       │
                    │   4. Verification requirements check    │
                    │   5. Risk & side-effect policy          │
                    │   6. Complexity limits (depth, nodes)   │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │           GraphDefinition               │
                    │   + ArchitectureValidationResult        │
                    │   + ArchitectureQualityScore            │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │         AgentGraphRuntime.run()         │
                    └─────────────────────────────────────────┘
```

---

## 2. Generator Contract & Inputs

### Class Signature ([`reco/engine/generator.py`](file:///c:/Users/toufi/Desktop/test-ao/reco/engine/generator.py))

```python
class ArchitectureGenerator:
    def __init__(
        self,
        model_gateway: Optional[ModelGateway] = None,
        tool_registry: Optional[ToolRegistry] = None,
        fallback_on_error: bool = True,
    ): ...

    async def generate(
        self,
        task_spec: TaskSpecification,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        evaluator_spec: Optional[EvaluatorSpecification] = None,
    ) -> GraphDefinition: ...

    async def generate_with_validation(
        self,
        task_spec: TaskSpecification,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        evaluator_spec: Optional[EvaluatorSpecification] = None,
    ) -> Tuple[GraphDefinition, ArchitectureValidationResult, ArchitectureQualityScore]: ...
```

### Input Requirements
1. **`task_spec`**: Normalized user objective, required capabilities, subtasks with dependency graph, expected inputs/outputs, constraints, verification rules, and risk level.
2. **`available_tools`**: Catalog schemas (`name`, `parameters_schema`, `output_schema`, `deterministic`, `side_effect`, `risk_level`).
3. **`evaluator_spec`**: Benchmark metrics, required output properties, and correctness criteria.

---

## 3. Strict Structured Output & Model Gateway Boundary

When a `ModelGateway` is supplied, the generator prompts the model for a strict JSON matching `GraphDefinition`:
- **Nodes**: `node_id`, `name`, `role`, `system_prompt`, `tools`, `input_mapping`, `output_key`, `max_retries`, `metadata.capabilities`.
- **Edges**: `source_node_id`, `target_node_id`, `condition`.
- **Topology**: `entry_node_id`, `terminal_node_ids`.

### Bounded Repair
If the model produces malformed JSON or invalid schema:
1. The error is recorded.
2. Exactly **one bounded repair prompt** is sent to the model.
3. If repair succeeds, `graph.metadata["repaired"] = True`.
4. If repair fails:
   - If `fallback_on_error=False`, raises `RuntimeError`.
   - If `fallback_on_error=True`, falls back to deterministic synthesis and records `graph.metadata["llm_generation_error"]`.

---

## 4. Deterministic Validation Pipeline

The architecture is validated against 6 explicit policy layers before execution:

### 1. Topological Invariants
- Entry node exists.
- All edge sources and targets exist.
- No duplicate edges.
- Strict Kahn's algorithm cycle rejection (must be a strict DAG).
- Every node is reachable from `entry_node_id`.
- Terminal nodes are non-empty, exist, and are reachable.

### 2. Tool Authorization & Anti-Fabrication
- **Strict Anti-Fabrication Guarantee**: Every tool assigned to any node must exist in the provided catalog schema.
- Assigning an uncataloged or fabricated tool sets `tool_authorization_ok = False` and `valid = False`.
- Tool parameter schemas are checked against declared input mappings.

### 3. Capability Coverage Analysis
- Computes whether all `task_spec.required_capabilities` are satisfied.
- Capabilities are mapped from:
  - Explicit `node.metadata["capabilities"]`
  - Node functional roles (e.g. `Extractor`, `Auditor`, `Matcher`, `Calculator`)
  - Assigned tool capabilities (e.g. `parse_bank_statement` -> `extraction`, `calc_difference` -> `calculation`).
- Multi-capability nodes are supported (one node may fulfill multiple capabilities).

### 4. Verification Requirements
- When the task, evaluator, or capability set requests verification (e.g. arithmetic variance audit, completeness check):
  - Enforces presence of a verifier/auditor node.
  - If omitted, flags a structured warning.
- When no verification is required, verifiers are omitted to preserve graph efficiency.

### 5. Risk & Side-Effect Enforcement
- Read-only tasks (`side_effect_requirements=False`) **must never** be assigned tools with `side_effect=True`.
- Violations produce validation errors, preventing inadvertent state mutations.
- High-risk tools in low-risk tasks trigger explicit safety warnings.

### 6. Complexity Boundaries (V0)
- `MAX_NODE_COUNT = 10`
- `MAX_EDGE_COUNT = 20`
- `MAX_TOOLS_PER_NODE = 4`
- `MAX_GRAPH_DEPTH = 6` (longest topological path from entry)

---

## 5. Deterministic Fallback Synthesizer

When operating offline or when the model gateway is unconfigured:

### Subtask-Driven Pipeline
- Each subtask in `task_spec.subtasks` becomes an agent node.
- Subtask dependencies are mapped to directed edges.
- Entry node is determined by topological in-degree 0.
- Terminal nodes are determined by topological out-degree 0.
- **Intelligent Input Mapping**: Tool parameters (e.g. `records`, `entries`, `bank_transactions`, `ledger_entries`) are automatically resolved against state inputs and predecessor outputs using dot-notation.

### Capability Archetype Fallback
When subtasks are not provided:
- Generates a canonical 2-to-3 node DAG:
  `IngestionSpecialist -> AnalyticalProcessor [-> Auditor if verification needed]`
- Metadata is tagged with `generation_method = "fallback"`.

---

## 6. Architecture Quality Score

A deterministic pre-execution quality score in `[0.0, 1.0]`:

$$\text{Overall Score} = 0.35 \cdot S_{\text{cap}} + 0.35 \cdot S_{\text{tool}} + 0.15 \cdot S_{\text{struct}} + 0.15 \cdot S_{\text{risk}}$$

| Component | Weight | Criteria |
| :--- | :--- | :--- |
| **Capability Coverage** ($S_{\text{cap}}$) | 35% | Fraction of required capabilities satisfied by nodes/tools |
| **Tool Validity** ($S_{\text{tool}}$) | 35% | 1.0 if all tools authorized & cataloged; 0.0 if fabricated |
| **Structural Efficiency** ($S_{\text{struct}}$) | 15% | 1.0 for optimal 2–5 node DAG; penalizes excessive complexity |
| **Risk Alignment** ($S_{\text{risk}}$) | 15% | 1.0 if side-effect policy matches task requirements |

---

## 7. Multi-Domain Demonstrations

### 1. Finance Reconciliation
- **Goal**: `"Reconcile these bank transactions against the general ledger and identify unexplained discrepancies."`
- **Synthesized Architecture**:
  - `subtask_1` (IngestionSpecialist): `parse_bank_statement`
  - `subtask_2` (AnalyticalProcessor): `fuzzy_match_transactions`, `calculate_reconciliation_difference`
  - `subtask_3` (Auditor): Verification & discrepancy summary
- **Runtime Execution**: Successfully executes in `AgentGraphRuntime`, producing a reconciled output summary.

### 2. Research & Comparison
- **Goal**: `"Compare three open-source observability platforms using public evidence."`
- **Synthesized Architecture**:
  - `subtask_1` (IngestionSpecialist): Query & evidence extraction
  - `subtask_2` (AnalyticalProcessor): Comparative matrix synthesis
  - `subtask_3` (Auditor): Citation and evidence verification

### 3. Data Anomaly Detection
- **Goal**: `"Find anomalies in this CSV and explain likely causes."`
- **Synthesized Architecture**:
  - `subtask_1` (IngestionSpecialist): CSV ingestion and schema validation
  - `subtask_2` (AnalyticalProcessor): Statistical outlier & anomaly detection
  - `subtask_3` (Auditor): Root-cause correlation report

---

## 8. Internal API Endpoint

```http
POST /generate-architecture
Content-Type: application/json

{
  "task_spec": { ... },
  "available_tools": [ ... ],
  "evaluator_spec": null
}
```

Or with raw goal:

```http
POST /generate-architecture
Content-Type: application/json

{
  "goal": "Reconcile bank statements against ledger in json format"
}
```

**Response (200 OK)**:
```json
{
  "graph": {
    "graph_id": "...",
    "name": "...",
    "entry_node_id": "...",
    "terminal_node_ids": ["..."],
    "nodes": { ... },
    "edges": [ ... ]
  },
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "capability_coverage": { ... },
    "tool_authorization_ok": true,
    "executable": true
  },
  "quality": {
    "overall_score": 0.95,
    "capability_coverage_score": 1.0,
    "tool_validity_score": 1.0,
    "structural_efficiency_score": 1.0,
    "risk_alignment_score": 1.0
  }
}
```
