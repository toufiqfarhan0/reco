# Reco System Architecture

## 1. System Overview & Core Philosophy

**Reco** is an autonomous agent engineering system. Instead of requiring human engineers to manually design, test, tweak prompts, and wire together multi-agent systems, Reco automates the entire agent lifecycle:
1. Accepts a **Goal**, a catalog of **Available Tools**, and an **Evaluation Benchmark**.
2. **Analyzes the task** and synthesizes an initial **Agent Architecture** (topology, roles, prompts, tool assignments, model selections).
3. **Executes** the workflow against benchmark scenarios.
4. **Evaluates** results across 4 hard dimensions: **Accuracy**, **Reliability**, **Cost**, and **Latency**.
5. **Inspects failures** and diagnoses the root causes (e.g., prompt hallucination, wrong tool selection, context overflow, lack of verification).
6. **Generates candidate mutations** across multiple structural dimensions (not just prompts, but topology, models, verifiers, retries, and tools).
7. **Re-runs the benchmark** across both an *optimization split* and a *held-out regression split*.
8. **Promotes only genuinely better versions**, archiving full regression evidence and lineage.

```mermaid
flowchart TD
    subgraph Input ["Specification"]
        G[Goal / Task Spec]
        T[Tool Catalog]
        B[Benchmark Dataset]
    end

    subgraph Design ["Synthesis"]
        GA[Goal Analyzer]
        AG[Architecture Generator]
    end

    subgraph Runtime ["Agent Graph Runtime"]
        AR[Agent Graph / State Machine]
        EE[Execution Engine]
    end

    subgraph Feedback ["Evaluation & Optimization Loop"]
        EV[Evaluation Engine\nAccuracy | Reliability | Cost | Latency]
        FA[Failure Analyzer & Diagnoser]
        MO[Mutation & Optimization Engine\nPrompts | Tools | Models | Verifiers | Topologies]
        RB[Regression Benchmark\nHeld-Out Split]
        PC[Promotion Controller]
    end

    subgraph Storage ["Persistence & Observability"]
        SB[(Supabase PostgreSQL)]
        NL[Neatlogs Tracing & Logs]
        TM[TensorMux / LiteLLM Router]
    end

    G & T & B --> GA
    GA --> AG
    AG --> AR
    AR --> EE
    EE <--> TM
    EE -. Traces .-> NL
    EE --> EV
    EV --> SB
    EV --> FA
    FA --> MO
    MO --> AR
    MO --> RB
    RB --> PC
    PC -->|Promote / Reject| SB
```

---

## 2. Component Specifications

### 2.1 API & Control Plane
- **Framework**: FastAPI (Python 3.11+).
- **Responsibilities**: Orchestrate asynchronous experiment runs, expose REST endpoints for the frontend dashboard, manage agent version lifecycles, and handle database transactions.
- **Inputs**: HTTP requests (run benchmark, mutate, promote, inspect traces).
- **Outputs**: Pydantic JSON responses, Server-Sent Events (SSE) for real-time run logs.
- **Dependencies**: Supabase Python SDK, Pydantic v2, Uvicorn.
- **MVP Status**: **Required**.

### 2.2 Goal Analyzer
- **Responsibilities**: Decompose incoming high-level goal descriptions into concrete task criteria, tool requirements, input/output schemas, and verification constraints.
- **Inputs**: User goal text, tool definitions (JSON Schema).
- **Outputs**: Structured `TaskDecomposition` object (sub-tasks, dependency graph, domain constraints).
- **Dependencies**: LLM abstraction.
- **MVP Status**: **Required**.

### 2.3 Architecture Generator
- **Responsibilities**: Synthesize a declarative `AgentArchitecture` specification from the `TaskDecomposition`. Formulates agent nodes, agent roles, system prompts, tool bindings, model tiers, and graph execution flow (sequential, routing, or verifier-loop).
- **Inputs**: `TaskDecomposition`, available tool catalog, baseline model constraints.
- **Outputs**: Declarative `AgentGraphDefinition` (nodes, edges, execution policies).
- **Dependencies**: LLM abstraction.
- **MVP Status**: **Required**.

### 2.4 Agent Runtime & Execution Engine
- **Responsibilities**: Execute the generated `AgentGraphDefinition` deterministically. Manages state passing, agent tool dispatch, context window compaction, and step-level telemetry.
- **Design Rule**: Custom lightweight Python runtime (~400 lines) using an explicit state-machine/DAG runner. **Avoid heavy frameworks** (LangChain, LangGraph, AutoGPT, CrewAI) to guarantee execution transparency, zero hidden prompts, and exact token/cost accounting.
- **Inputs**: `AgentGraphDefinition`, benchmark case input data, execution context.
- **Outputs**: Execution output, raw message log, tool execution trace, token consumption, execution latency.
- **Dependencies**: Tool Registry, Model Gateway.
- **MVP Status**: **Required**.

### 2.5 Tool Registry & Sandbox
- **Responsibilities**: Provide isolated, validated python-callable tools with standard JSON Schema specifications.
- **Initial Benchmark Tools**:
  - `parse_bank_statement(file_bytes | text)`
  - `query_general_ledger(account_id, date_range)`
  - `calculate_reconciliation_difference(bank_amount, ledger_amount, fx_rate, fee)`
  - `fuzzy_match_transactions(vendor_name, reference_no, tolerance)`
  - `post_reconciliation_journal_entry(entry_payload)`
- **Dependencies**: Pure Python, standard financial math.
- **MVP Status**: **Required**.

### 2.6 Evaluation Engine
- **Responsibilities**: Score execution runs objectively without hallucinated or simulated metrics.
- **Metrics Calculated**:
  1. **Accuracy**: Fraction of transactions correctly matched/flagged against ground truth labels (Precision, Recall, F1).
  2. **Reliability**: Valid schema conformity, zero uncaught exceptions, compliance with financial invariance rules (e.g. debits == credits).
  3. **Cost**: Actual token costs calculated via token counters multiplied by model-specific pricing tables ($/1k prompt, $/1k completion).
  4. **Latency**: End-to-end wall-clock time (seconds) and per-node execution breakdown.
- **Inputs**: Execution outputs, ground truth labels from benchmark cases.
- **Outputs**: `EvaluationScorecard` with explicit sub-scores and failure flags.
- **Dependencies**: None (pure analytical evaluation).
- **MVP Status**: **Required**.

### 2.7 Failure Analyzer & Root Cause Diagnoser
- **Responsibilities**: Ingest failed test cases and execution traces, categorize failure modes, and isolate the exact faulty component (prompt ambiguity, inappropriate tool call, hallucinated parameter, model reasoning limit, missing verification step).
- **Failure Taxonomy**:
  - `TOOL_ARGUMENT_ERROR`: Called tool with invalid types or missing parameters.
  - `ARITHMETIC_MISMATCH`: Incorrect math on fees or FX conversion.
  - `PREMATURE_TERMINATION`: Agent stopped before resolving all discrepancies.
  - `HALLUCINATED_MATCH`: Paired transactions that violate tolerance boundaries.
  - `CONTEXT_OVERFLOW`: Truncated statement context or dropped transactions.
- **Inputs**: `EvaluationScorecard`, step-level execution trace, ground truth diff.
- **Outputs**: `RootCauseDiagnosis` with prioritized mutation suggestions.
- **Dependencies**: LLM abstraction.
- **MVP Status**: **Required**.

### 2.8 Mutation & Optimization Engine
- **Responsibilities**: Transform a diagnosed `AgentGraphDefinition` into a candidate version $V_{k+1}$ by applying targeted mutations along specific architectural axes:
  - **Prompt Mutator**: Refines role instructions, few-shot examples, and strict formatting guidelines.
  - **Topology Mutator**: Adds a reflection/verifier node (e.g., dual-agent audit), splits a monolithic agent into a specialist pair, or adjusts fallback routes.
  - **Tool Binding Mutator**: Restricts or expands tool visibility per agent; changes tool invocation ordering.
  - **Model Router Mutator**: Upgrades reasoning-heavy nodes to frontier models; downscales extraction nodes to fast/cheap models.
  - **Policy Mutator**: Modifies retry count, maximum steps, temperature, and confidence thresholds.
- **Inputs**: Current `AgentGraphDefinition`, `RootCauseDiagnosis`, mutation budget.
- **Outputs**: Candidate `AgentGraphDefinition` ($V_{cand}$).
- **Dependencies**: LLM abstraction.
- **MVP Status**: **Required**.

### 2.9 Regression Benchmark & Split Controller
- **Responsibilities**: Maintain strict dataset segregation to prevent overfitting to the optimization loop.
  - **Optimization Split (60%)**: Used during the iterative failure diagnosis and mutation phase.
  - **Held-Out Evaluation Split (40%)**: Never seen by the failure analyzer. Evaluated strictly during candidate validation.
- **Inputs**: Candidate version $V_{cand}$, Benchmark datasets.
- **Outputs**: `SplitEvaluationReport` (Train vs. Held-out comparison).
- **Dependencies**: Evaluation Engine.
- **MVP Status**: **Required**.

### 2.10 Promotion Controller
- **Responsibilities**: Enforce algorithmic promotion gates before any candidate becomes the active/promoted version.
- **Promotion Invariant**:
  $$\text{Accuracy}_{\text{held-out}}(V_{cand}) \ge \text{Accuracy}_{\text{held-out}}(V_{best})$$
  $$\text{Reliability}_{\text{held-out}}(V_{cand}) \ge \text{Reliability}_{\text{held-out}}(V_{best})$$
  $$\text{Pareto-Check}: (\text{Cost}, \text{Latency}) \text{ within acceptable bounded tradeoffs}.$$
- **Outputs**: Promoted status (`PROMOTED`, `REJECTED`, `PARETO_CANDIDATE`).
- **Dependencies**: Supabase storage.
- **MVP Status**: **Required**.

---

## 3. External Integrations & Abstraction Boundaries

### 3.1 Supabase (Primary Database & Persistence)
- **Role**: Primary system of record for all experiments, agent graph versions, benchmark cases, execution runs, metrics, and failure diagnoses.
- **Access Pattern**: Handled via standard PostgreSQL connection pool (or Supabase Python client) behind a unified repository interface (`reco/db/`).
- **Postgres Features**: Relational integrity, foreign keys, JSONB for flexible graph definitions and traces.

### 3.2 Neatlogs (Agent Observability & Tracing)
- **Role**: Ingestion of real-time span traces, LLM calls, tool inputs/outputs, and evaluation logs for live observability and failure deep dives.
- **Abstraction Boundary**: `reco/observability/tracer.py`. If Neatlogs API keys are missing or offline, the system falls back seamlessly to local in-memory/JSON logging without failing.

### 3.3 TensorMux (Inference Gateway & Model Router)
- **Role**: Unified model invocation layer providing OpenAI-compatible endpoints with dynamic model routing, latency/cost telemetry, and provider failover.
- **Abstraction Boundary**: `reco/llm/client.py`.
- **Decoupling Rule**: All calls route through an abstract `ModelGateway` interface. TensorMux is an implementation adapter alongside direct LiteLLM or native provider clients. Reco is **never locked** to TensorMux.

### 3.4 Dodo Payments (Monetization Layer)
- **Role**: Handles developer subscription tiers, API credit packs, or per-optimization-run billing.
- **Abstraction Boundary**: `reco/billing/service.py`.
- **Decoupling Rule**: The core agent-engineering loop has **zero runtime dependency** on Dodo Payments. Billing calls are isolated hooks on run initiation/completion. The system runs fully and testably with billing disabled (`BILLING_ENABLED=false`).

### 3.5 AO (Development Environment Only)
- **Absolute Rule**: AO is strictly the pair-programming and development tool used by the engineers during the hackathon. It has **zero runtime dependencies, zero imports, and zero API integrations** in Reco.

---

## 4. Frontend Architecture (Next.js + shadcn/ui)

- **Framework**: Next.js (App Router), TypeScript, Tailwind CSS, Lucide icons, Recharts.
- **Views**:
  1. **Goal & Architecture Studio**: Input goal, visual DAG viewer of current agent graph architecture.
  2. **Benchmark Execution Dashboard**: Live run telemetry, accuracy/cost/latency scorecards.
  3. **Failure Analysis & Mutation Inspector**: Visual diff between Agent Version $V_n$ and $V_{n+1}$, side-by-side prompt and topology diffs, root cause logs.
  4. **Regression & Version History**: Progression curves across successive iterations, Pareto frontier plots (Accuracy vs. Cost vs. Latency).
- **Communication**: REST API + Server-Sent Events (SSE) from FastAPI backend.
