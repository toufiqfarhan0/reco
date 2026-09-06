# RECO: MULTI-CANDIDATE OPTIMIZATION & CANDIDATE SELECTION ARCHITECTURE

## 1. Executive Summary
Step 22 expands Reco from single-candidate linear evolution ($V0 \to \text{Cand} \to V1$) to bounded multi-candidate Pareto optimization:
```
V0 (Parent)
├── Candidate A (Prompt refinement)
├── Candidate B (Verifier insertion)
└── Candidate C (Tool addition / Context change)
      ↓
Static Pre-Flight Validation & Fingerprint Deduplication
      ↓
Benchmark on 12 Optimization Cases (Budget: max 36 cases/gen)
      ↓
Pareto Scorecard Comparison vs Parent V0
      ↓
Multi-Dimensional Selection Policy (Dominance + Tradeoffs)
      ↓
V1 (Selected Winner)
      ↓
Held-Out Evaluation (8 cases — Winner ONLY, Zero Leakage)
```
This architecture preserves complete determinism, strict safety guarantees, explainable rejection reasons, and rigid held-out isolation.

---

## 2. Architecture & Components

### 2.1 Candidate Generation (`reco/mutation/generator.py`)
- Guided by failure clusters identified by `FailureAnalyzer.cluster_failures()`.
- Generates up to `MAX_CANDIDATES_PER_GENERATION = 3` mutation candidates per generation.
- Supports 10 strongly-typed mutation categories:
  - `PROMPT_CHANGE`
  - `TOOL_ADD`
  - `TOOL_REMOVE`
  - `TOOL_REORDER`
  - `TOPOLOGY_CHANGE`
  - `ADD_VERIFIER`
  - `MODEL_CHANGE`
  - `ROUTING_CHANGE`
  - `CONTEXT_CHANGE`
  - `RETRY_POLICY_CHANGE`

### 2.2 Candidate Diversity
- When multiple diagnoses or failure clusters recommend mutations, the generator prioritizes distinct mutation types (`PROMPT_CHANGE`, `ADD_VERIFIER`, `TOOL_ADD`) across the candidate set.
- If diagnoses only suggest a single mutation category, the generator synthesizes diverse architectural alternatives supported by the target node and registered tools rather than generating trivial prompt variations.

### 2.3 Architecture Fingerprinting & Deduplication (`reco/optimization/history.py`)
- Before executing benchmark evaluations, each mutated candidate graph is fingerprinted using a deterministic cryptographic hash:
  $$\text{Fingerprint} = \text{SHA256}(\text{Nodes} \,\|\, \text{Roles} \,\|\, \text{ExecutionModes} \,\|\, \text{Prompts} \,\|\, \text{Tools} \,\|\, \text{InputMappings} \,\|\, \text{Edges})$$
- If two candidates produce equivalent graph topologies or repeated architectures from previous generations, the duplicate candidate is marked `invalid` with rejection reason `duplicate_candidate_architecture`.
- **Budget Protection**: Duplicate or invalid candidates do NOT consume benchmark execution budget.

### 2.4 Static Validation Pre-Flight (`reco/mutation/validation.py`)
Every generated candidate undergoes static structural validation:
1. **DAG & Cycle Detection**: Graph must be a valid Directed Acyclic Graph without cycles.
2. **Depth Bounds**: Maximum graph depth cannot exceed 10.
3. **Tool Authorization**: Every tool assigned to a node must exist in `ToolRegistry` (anti-fabrication).
4. **Capability Coverage**: Graph must satisfy the capabilities declared in `TaskSpecification`.
5. **Schema Validation**: Nodes and edges conform strictly to Pydantic models.

Invalid candidates are assigned status `invalid` and discarded prior to runtime invocation.

---

## 3. Benchmarking & Multi-Dimensional Comparison

### 3.1 Optimization Benchmark Split
- Valid candidates are evaluated on the 12 canonical optimization split cases.
- Held-out cases (8 cases) are strictly isolated and never accessed during candidate benchmarking.

### 3.2 Candidate Scorecard Metrics
Each candidate receives an authoritative `Scorecard`:
- **Accuracy**: Case success rate ($0.0 - 1.0$)
- **Reliability**: Execution completion rate without unhandled exceptions ($0.0 - 1.0$)
- **Total Cost USD**: Exact token expenditure computed from input and output rates
- **Average Latency**: Latency per evaluated case (ms)
- **Model Calls & Tool Calls**: Total discrete invocations

### 3.3 Scorecard Comparison vs Parent (`reco/evaluators/comparison.py`)
Each candidate scorecard is compared directly against the current parent version ($V0$):
$$\Delta_{\text{accuracy}} = \text{acc}_{\text{cand}} - \text{acc}_{\text{parent}}$$
$$\Delta_{\text{cost}} = \text{cost}_{\text{cand}} - \text{cost}_{\text{parent}}$$
$$\Delta_{\text{latency}} = \text{lat}_{\text{cand}} - \text{lat}_{\text{parent}}$$

Classifications:
- `strictly_better`: Improved or equal on all metrics, strictly improved on at least one.
- `tradeoff`: Improvement on one metric accompanied by regression on another (e.g. $+5\%$ accuracy, $+10\%$ latency).
- `strictly_worse`: Degraded on at least one metric without improvement on any.

---

## 4. Multi-Candidate Selection Policy (`reco/optimization/controller.py`)

The controller applies a deterministic selection filter across the candidate pool:

1. **Eliminate Regressions**:
   - Any candidate with $\text{reliability}_{\text{cand}} < \text{reliability}_{\text{parent}}$ is rejected (`reliability_regression`).
   - Any candidate with $\text{accuracy}_{\text{cand}} < \text{accuracy}_{\text{parent}}$ is rejected (`accuracy_regression`).
   - Any candidate classified as `strictly_worse` is rejected (`strictly_worse_than_parent`).
2. **Dominance Ranking**:
   - Filter to candidates with $\Delta_{\text{accuracy}} \ge 0$ and $\Delta_{\text{reliability}} \ge 0$.
   - Prioritize candidate with the highest accuracy score.
   - **Tie-Breaking**: If multiple candidates achieve equal accuracy, select the one with the lowest total cost. If cost is identical, select the lowest latency.
3. **Winner Selection**:
   - Strongest candidate is marked `status = "selected"`.
   - Remaining candidates are marked `status = "rejected"` with descriptive reasons (e.g. `inferior_to_Candidate_A`, `accuracy_regression`).
   - If no candidates beat or match the parent, all candidates are rejected and the generation terminates without version promotion.

---

## 5. Held-Out Protection Gate

- **Zero Leakage**: Held-out split data (8 cases) is strictly barred from:
  - Failure diagnosis
  - Candidate generation
  - Candidate benchmarking
  - Candidate comparison and selection
- **Gate Execution**: Held-out evaluation executes ONLY on the single final selected winner AFTER selection is finalized.
- If all candidates are rejected, zero held-out calls are made.

---

## 6. Cost Controls & Limits

| Constraint | Limit | Rationale |
|---|---|---|
| `MAX_CANDIDATES_PER_GENERATION` | 3 | Bounded candidate pool prevents combinatorial explosion |
| `MAX_TOTAL_CANDIDATE_BENCHMARK_CASES` | 36 | Exactly $3 \times 12$ cases max per generation |
| Pre-flight Rejection | 0 benchmark calls | Invalid and duplicate graphs rejected before execution |
| Held-out Gate | 8 cases (winner only) | Zero held-out budget wasted on rejected candidates |

---

## 7. Lineage & Immutability

- **Parent Immutability**: Parent $V0$ graph, scorecards, and database records remain strictly read-only and immutable.
- **Candidate Lineage**: Every candidate record preserves:
  - `parent_version_id`
  - `candidate_id`
  - `candidate_name` (`Candidate A`, `Candidate B`, etc.)
  - `fingerprint`
  - `mutation_type`
  - `status` (`selected`, `rejected`, `invalid`)
  - `rejection_reason`
  - `optimization_scorecard`
  - `comparison`
- **Frontend Observability**: Candidate pool is exposed via `/experiments/demo` and `/jobs/{job_id}` for direct UI rendering in the "Candidate Pool" view tab.
