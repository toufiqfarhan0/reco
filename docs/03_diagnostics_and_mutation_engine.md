# AGY Prompt 03 — Failure Diagnostics & Mutation Engine

## AO Session Setup
```bash
# 1. Create GitHub Issue
# Title: feat: failure analyzer taxonomy and autonomous DAG mutation engine

# 2. Spawn AO Session
ao session spawn --name "03-diagnostics-mutation" --issue 3

# 3. Run with AGY CLI
agy --file docs/prompts/03_diagnostics_and_mutation_engine.md
```

---

## Objective
Implement closed-loop autonomous improvement: analyze where an agent fails on optimization cases, classify failure modes using a 12-category diagnostic taxonomy, and generate targeted architecture mutations to iteratively improve performance.

## Context & Architecture
- System: **Reco** (Autonomous Agent Engineering System)
- Reference Docs:
  - [Failure Analyzer Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_FAILURE_ANALYZER.md)
  - [Mutation Engine Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_MUTATION_ENGINE.md)
  - [Closed-Loop Optimization Controller](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_OPTIMIZATION_CONTROLLER.md)

## Requirements to Implement

### 1. Failure Analyzer (`reco/diagnostics/analyzer.py`)
- Ingest failed benchmark execution traces and isolate root causes from intermediate symptoms.
- Map failures into the formal 12-Category Diagnostic Taxonomy:
  - `PROMPT_AMBIGUITY`: Vague system/user instruction causing improper reasoning.
  - `TOOL_SELECTION_ERROR`: Incorrect tool selected for task requirement.
  - `TOOL_PARAMETER_ERROR`: Invalid schema or missing parameters in tool invocation.
  - `SCHEMA_VIOLATION`: Output fails to conform to declared schema.
  - `VERIFICATION_MISS`: Subtle output flaw slipped through without verification.
  - `ROUTING_MISDIRECT`: Execution branched to wrong node in conditional DAG.
  - `CONTEXT_OVERFLOW`: Prompt size exceeded token window.
  - `RETRY_EXHAUSTION`: Transient failures consumed all retry budgets.
  - `MODEL_CAPABILITY_LIMIT`: Reasoning requires stronger model or decomposition.
  - `TIMEOUT_EXCEEDED`: Node took longer than SLA allowed.
  - `STATE_CORRUPTION`: Intermediate state mutation overwrote valid data.
  - `UNHANDLED_EXCEPTION`: Uncaught exception during node execution.
- Recommend targeted remedy strategy for each detected failure cluster.

### 2. Mutation Engine (`reco/mutation/engine.py` & `mutators/`)
- Implement mutation operators that generate new candidate architectures:
  - `PromptMutator`: Rewrites system/instruction prompts to add domain constraints, few-shot examples, and strict formatting rules.
  - `VerifierNodeMutator`: Injects dedicated verification/validation node prior to the final output node.
  - `ToolAssignmentMutator`: Attaches missing tools or replaces misaligned tools from the `ToolRegistry`.
  - `TopologyMutator`: Refactors linear DAGs into branching or ensemble DAGs.
  - `RetryPolicyMutator`: Adds exponential backoff or retry logic to brittle nodes.
- Implement `CandidateValidator`:
  - Ensure all mutated candidates remain valid, acyclic DAGs.
  - Reject hallucinated tools (only tools present in `ToolRegistry` are allowed).
  - Compute candidate diff against parent baseline architecture.

## Verification & Acceptance Criteria
1. Failure analyzer accurately identifies error categories on synthetic and real failure runs.
2. Mutation engine generates valid, non-crashing mutated candidate DAGs.
3. Candidate validator rejects invalid DAG topologies or unknown tool references.
4. Pass all unit tests:
   ```bash
   python -m pytest tests/test_failure_analyzer.py tests/test_mutation_engine.py -v
   ```
