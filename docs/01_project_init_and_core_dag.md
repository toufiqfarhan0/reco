# AGY Prompt 01 — Project Setup, Goal Decomposition & Core DAG Runtime

## AO Session Setup
```bash
# 1. Create GitHub Issue
# Title: feat: goal analyzer, task spec, and core DAG runtime

# 2. Spawn AO Session
ao session spawn --name "01-core-dag-runtime" --issue 1

# 3. Run with AGY CLI
agy --file docs/prompts/01_project_init_and_core_dag.md
```

---

## Objective
Establish the foundational autonomous agent engineering pipeline for Track 1: Automated Agent Engineering.
Given a user's natural language goal and available tools, Reco must decompose the goal into structured requirements and synthesize an executable Directed Acyclic Graph (DAG) architecture.

## Context & Architecture
- System: **Reco** (Autonomous Agent Engineering System)
- Reference Docs:
  - [Architecture Overview](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_ARCHITECTURE.md)
  - [Goal Analyzer Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_GOAL_ANALYZER.md)
  - [Architecture Generator Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_ARCHITECTURE_GENERATOR.md)
  - [Runtime Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_RUNTIME.md)
  - [Tool Registry Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_TOOLS.md)

## Requirements to Implement

### 1. Goal Analyzer (`reco/core/goal_analyzer.py`)
- Parse unstructured natural language goals (e.g., *"Reconcile internal payment ledgers against bank statements and detect discrepancies"*).
- Extract structured attributes into a `TaskSpecification`:
  - `domain`: Target problem domain.
  - `required_capabilities`: List of essential operational capabilities.
  - `input_modalities` and `output_schema`: Explicit schema requirements.
  - `constraints`: Latency bounds, cost limits, and reliability thresholds.

### 2. Architecture Generator (`reco/engine/generator.py`)
- Dynamically synthesize an `AgentArchitecture` Directed Acyclic Graph (DAG).
- Synthesize typed nodes: `input_node`, `tool_node`, `reasoning_node`, `verifier_node`, `output_node`.
- Compute topological execution order and ensure DAG acyclicity.
- Calculate architecture complexity metrics: node count, edge density, and structural quality score.

### 3. Tool Registry (`reco/tools/registry.py`)
- Provide a centralized catalog of discoverable tools with strict schema validation.
- Register domain-agnostic and deterministic tools (`parse_statement`, `query_ledger`, `match_transactions`, `calc_difference`).
- Enforce tool call sandboxing and parameter type safety.

### 4. Agent Graph Runtime (`reco/engine/runtime.py` & `node_runner.py`)
- Execute nodes in strict topological sequence.
- Maintain immutable execution state across nodes with step-by-step state transitions.
- Record node-level latency, execution status, and intermediate artifacts.

## Verification & Acceptance Criteria
1. Goal analyzer successfully extracts task specifications across distinct natural language descriptions.
2. Architecture generator creates valid, cycle-free DAGs with correct input/output dependencies.
3. Node runner executes DAG to completion and returns formatted state.
4. Pass all unit tests:
   ```bash
   python -m pytest tests/test_goal_analyzer.py tests/test_architecture_generator.py tests/test_runtime.py -v
   ```
