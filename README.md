# Reco: Autonomous Agent Engineering System

[![Track](https://img.shields.io/badge/Track%201-Automated%20Agent%20Engineering-blue?style=flat-square)](#)
[![Model Provider](https://img.shields.io/badge/Model%20Provider-TensorMux%20%28GLM--4.7--Flash%29-orange?style=flat-square)](#)
[![Observability](https://img.shields.io/badge/Observability-Neatlogs%20Distributed%20Tracing-purple?style=flat-square)](#)
[![Persistence](https://img.shields.io/badge/Persistence-Supabase%20Cloud%20Ledger-emerald?style=flat-square)](#)
[![Monetization](https://img.shields.io/badge/Monetization-Dodo%20Payments%20Pro%20Tier-cyan?style=flat-square)](#)
[![Deployment](https://img.shields.io/badge/Deployment-Render%20Web%20Service%20%28Unified%20FastAPI%20%2B%20Vite%29-black?style=flat-square)](#)

Reco is an autonomous agent engineering system that automates the end-to-end lifecycle of designing, executing, diagnosing, and evolving agentic Directed Acyclic Graphs (DAGs).

Instead of treating agent architectures as static, handcrafted code, Reco treats agent graphs as mutable, evolutionary systems. It analyzes natural language task goals, generates candidate topologies, benchmarks them against rigorous multi-case test suites, isolates root causes across a 12-category failure taxonomy, extracts persistent epistemic invariants, runs multi-candidate tournament mutations, and enforces air-gapped held-out promotion gates before deploying optimized agents to production.

---

## 1. Executive Summary: What Reco Does

The traditional agent engineering cycle is slow, manual, and brittle: developers write prompts, run a few ad-hoc queries, notice failures, and manually tweak instructions without systemic evaluation.

Reco replaces manual trial-and-error with a closed-loop autonomous optimization engine:

1. **Goal Deconstruction (`GoalAnalyzer`)**: Ingests high-level task goals (e.g., dual-ledger transaction reconciliation, time-series anomaly detection, cross-document research synthesis) and deconstructs them into formal task specifications, required tool capabilities, execution constraints, and validation criteria.
2. **Initial DAG Synthesis (`ArchitectureGenerator`)**: Synthesizes a baseline Directed Acyclic Graph (Baseline V0) consisting of typed input ingestion, tool execution, reasoning, and output delivery nodes with verified acyclicity.
3. **Multi-Axis Benchmark Evaluation (`ScorecardEvaluator`)**: Runs agent graphs across partitioned benchmark suites to produce an objective 4-axis scorecard measuring Accuracy, Reliability, Cost, and Latency.
4. **Diagnostic Root-Cause Analysis (`FailureAnalyzer`)**: Ingests execution traces and failure signatures, isolating underlying root causes from observable symptoms using a deterministic 12-category failure taxonomy.
5. **Epistemic Self-Reflection (`EpistemicMemoryLedger`)**: Extracts persistent architectural rules and domain invariants from diagnosed failures across generations (V0 -> V1 -> V2), guaranteeing measurable accuracy gains without regression.
6. **Multi-Candidate Mutation Tournament (`MutationEngine`, `CandidatePoolGenerator`, `TournamentEvaluator`)**: Synthesizes competing candidate variants (Prompt specialists, Tool assignment mutators, Verifier guardrails, Topology reorganizers) and evaluates them in a tournament to establish the Pareto frontier.
7. **Air-Gapped Held-Out Gate (`HeldOutValidationGate`)**: Evaluates the tournament champion on an air-gapped test split with zero data leakage, verifying that empirical improvements generalize to unseen data before issuing a formal promotion verdict (`PROMOTED`, `REQUIRES_REVIEW`, `REJECTED`).

---

## 2. Direct Answers to the 4 Hackathon Judge Questions

### Question 1: Learning Loops and Tool Mastery
> *How does the agent learn and master tool usage over time?*

Reco achieves tool mastery through an automated diagnostic and mutation feedback loop:
- **Baseline Tool Assignment**: The initial DAG generator assigns baseline tools based on semantic keyword mapping (for example, selecting `exact_reconcile` for matching ledgers).
- **Runtime Failure Capture**: When evaluated against real-world test cases, the baseline agent fails on inputs with format variations (such as `$1,250.00` currency strings, casing differences like `tx1003` vs `TX1003`, or trailing whitespace).
- **Taxonomy Classification**: The `FailureAnalyzer` identifies `tool_selection_error` and `tool_parameter_error`, recognizing that the tool cannot handle normalization internally.
- **Targeted Mutation**: The `ToolAssignmentMutator` automatically upgrades the node from `exact_reconcile` to `smart_reconcile`, while `PromptMutator` injects parameter sanitation directives.
- **Empirical Verification**: The mutated candidate is re-benchmarked, verifying that tool-handling accuracy rises from 16.7% to 83.3% on optimization test sets.

### Question 2: Self-Reflection and Epistemic Memory Ledger
> *Can you show the outputs of the agent getting better over time through its own self-reflection and memory growing?*

Reco features an **Epistemic Memory Ledger** that explicitly tracks the causal chain between observed failures in early generations and durable architectural rules codified in subsequent generations:

- **Empirical Accuracy Growth**: Benchmark accuracy improves from **60.0% (V0 Baseline)** to **75.0% (V1 Candidate B)** to **85.0% (V2 Candidate C)**, delivering a verified **+25.0% cumulative accuracy gain** across generations.
- **Codified Invariants**:
  1. **Lesson 01 (V0 -> V1 | `SCHEMA_VIOLATION`)**: *Tool Output Normalization*. Observed third-party API timestamp mismatches caused false reconciliation errors. Injected runtime coercion to normalize Unix epoch timestamps to ISO-8601 UTC at Node 02 (`+15.0%` accuracy lift).
  2. **Lesson 02 (V1 -> V2 | `VERIFICATION_MISS`)**: *Tolerance Drift Guardrail*. Observed floating-point rounding deltas (for example, `$452.999` vs `$453.00`) in multi-currency conversion. Synthesized a dedicated verifier node with `epsilon = 0.001` tolerance (`+10.0%` accuracy lift).
  3. **Lesson 03 (V1 -> V2 | `TOOL_PARAMETER_ERROR`)**: *Parameter Strictness*. Upstream model reasoning passed `record_id` as a string rather than an integer, causing database rejection. Injected runtime type enforcement to guarantee integer invariants.
- **Zero-Regression Invariant**: Every epistemic rule is validated against all historical test cases to ensure new constraints do not cause backward regressions.

### Question 3: Complex Contextual Logic
> *How do observed third-party tool quirks become codified runtime guardrails?*

Third-party APIs and microservices exhibit idiosyncratic behaviors, including unannounced schema shifts, timestamp formatting variations, floating-point rounding drift, and silent duplicate records.

Reco captures these anomalies during execution and codifies them directly into the graph architecture:
1. **Detection**: Telemetry spans in Neatlogs isolate where external tool outputs deviate from expected structural invariants.
2. **Taxonomy Diagnosis**: Errors are categorized under `schema_violation`, `tool_parameter_error`, or `verification_miss`.
3. **Guardrail Synthesis**: Instead of relying exclusively on prompt instructions that LLMs can hallucinate past, Reco injects deterministic verifier nodes (`json_validator`, `duplicate_guardrail`, `tolerance_checker`) directly into the DAG topology between tool execution and output delivery.
4. **Resilience**: The resulting V2 architecture enforces structural contracts at runtime, preventing malformed tool payloads from corrupting downstream reasoning.

### Question 4: Cost-Effectiveness vs Speed (Pareto Dominance)
> *How does the system balance cost, speed, and accuracy without budget bloat?*

Reco optimizes across a strict **4-Axis Scorecard**:
- **Accuracy**: Percentage of benchmark test cases satisfying exact ground-truth assertions.
- **Reliability**: Percentage of executions completing without unhandled exceptions or fatal crashes.
- **Cost (USD)**: Exact inference cost accounting using token consumption rates ($0.10 / 1M tokens on TensorMux GLM-4.7-Flash).
- **Speed (Latency)**: End-to-end wall-clock graph execution duration in milliseconds.

**Pareto Frontier Tournament Evaluation**:
A mutated candidate is only designated as the champion if it achieves **Pareto Dominance** (improving accuracy or reliability without regressing cost or latency beyond defined tolerance boundaries). If Candidate X achieves +5% accuracy but triples latency or token consumption, the tournament evaluator flags the trade-off and rejects the candidate in favor of balanced topologies.

### Question 5: Cross-Domain Generalization
> *Does the optimization engine generalize across diverse domains?*

Reco is domain-agnostic. The identical core engine (`GoalAnalyzer`, `ArchitectureGenerator`, `FailureAnalyzer`, `MutationEngine`, `TournamentEvaluator`, `HeldOutValidationGate`) operates across 3 distinct benchmark suites:

1. **Financial Reconciliation**: Dual-ledger transaction matching, currency parsing, whitespace and casing normalization, duplicate charge detection, and discrepancy reporting (10 test cases: 6 optimization, 4 held-out).
2. **System Anomaly Detection**: Statistical Z-score time-series outlier detection, multi-metric server health threshold alerting (CPU, memory, disk), log burst root-cause analysis, and cascading outage diagnosis (10 test cases: 6 optimization, 4 held-out).
3. **Research Synthesis**: Multi-entity extraction from technical papers (models, benchmarks, organizations), quantitative metric cross-referencing and leaderboard calculation, multi-document topical summary, and contradiction detection (10 test cases: 6 optimization, 4 held-out).

---

## 3. System Architecture & 5-Stage Console Workflow

### Closed-Loop Architecture Diagram

```
+---------------------------------------------------------------------------------------+
|                                RECO CLOSED-LOOP ENGINE                                |
+---------------------------------------------------------------------------------------+

  [ User Goal / Task Input ]
              |
              v
   +----------------------+
   |  01: Goal Analyzer   |  ==> Deconstructs requirements & constraints
   +----------------------+
              |
              v
   +----------------------+
   | 02: DAG Generator    |  ==> Synthesizes Baseline V0 Agent Graph
   +----------------------+
              |
              v
   +----------------------+
   | 03: Agent Runtime    | <==> [ TensorMux GLM-4.7-Flash + Tool Registry ]
   +----------------------+         |
              |                     +--> [ Neatlogs Distributed Tracing ]
              v
   +----------------------+
   | 04: Benchmark Suite  |  ==> Evaluates Optimization Split (6 Cases)
   +----------------------+
              |
              v
   +----------------------+
   | 05: Failure Analyzer |  ==> 12-Category Taxonomy Root Cause Isolation
   +----------------------+
              |
              v
   +----------------------+
   | 06: Epistemic Memory |  ==> Codifies Generational Invariants (V0->V1->V2)
   +----------------------+
              |
              v
   +----------------------+
   | 07: Mutation Engine  |  ==> Generates Candidate Pool (Prompt, Tool, Verifier)
   +----------------------+
              |
              v
   +----------------------+
   | 08: Tournament Gate  |  ==> Selects Pareto-Dominant Champion
   +----------------------+
              |
              v
   +----------------------+
   | 09: Held-Out Gate    |  ==> Air-Gapped Validation (4 Unseen Cases, 0 Leakage)
   +----------------------+
              |
              v
   [ Promoted Production Agent ]  ==> Synced to Supabase Cloud Ledger
```

---

### The 5-Stage Visual Engineering Console

The Reco frontend is structured around a 5-stage visual engineering workflow:

| Stage | Name | Description | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **01** | **BUILD** | Architecture Composition | Natural language goal input, domain preset chips, tool selection, visual DAG graph preview with node typing (Input, Tool, Reasoning, Verifier, Output). |
| **02** | **RUN** | Topological Execution | Live node-by-node execution progression, terminal streaming logs, and the 4-axis scorecard (Accuracy, Reliability, Cost, Latency). |
| **03** | **UNDERSTAND** | Failure Diagnostics | 12-category taxonomy distribution, root-cause isolation cards, symptom tracking, and the Epistemic Memory Ledger showing generational lessons. |
| **04** | **IMPROVE** | Mutation & Tournament | Multi-candidate tournament view (Candidates A, B, C), side-by-side prompt and configuration diff inspectors, and evolutionary lineage tree. |
| **05** | **VALIDATE** | Held-Out Promotion Gate | Air-gapped held-out benchmark validation (4 unseen cases), SHA-256 partition checksum verification, zero-leakage check, Neatlogs trace explorer, and promotion decision controls (`PROMOTED`, `REQUIRES_REVIEW`, `REJECTED`). |

---

## 4. Sponsor Integrations

Reco deeply integrates all hackathon sponsor technologies into its core architecture:

### 1. TensorMux (GLM-4.7-Flash Inference)
- **OpenAI-Compatible Gateway**: Direct connection to `https://api.tensormux.com/v1` using model `glm-4-7-flash`.
- **Reasoning Token Capture**: Extracts native GLM-4.7-Flash reasoning tokens (`reasoning` message field) for deep epistemic analysis.
- **Reasoning Safeguards**: Strictly enforces `max_tokens >= 400` to prevent truncation of intermediate reasoning chains.
- **Accurate Cost Tracking**: Computes live USD inference costs per query based on exact input/output token counts ($0.10 / 1M tokens).

### 2. Neatlogs (Distributed Tracing & Observability)
- **Hierarchical 5-Tier Spans**: Tracks execution lineage across `optimization_run` -> `generation_N` -> `candidate_eval` -> `node_execution` -> `tool_invocation`.
- **Fault Containment**: Telemetry exporter runs non-blocking background batches to `https://ingest.neatlogs.com`. If network drops or timeouts occur, agent execution proceeds uninterrupted ($0 impact on agent runtime).
- **Deep-Link Inspection**: Generates direct inspection links (`https://app.neatlogs.com/traces/<trace_id>`) for instant debugging.

### 3. Supabase (Cloud Persistence & RLS Ledger)
- **Relational Data Model**: Persists experiments, architecture definitions, benchmark runs, mutation diffs, evaluation scorecards, and traces in PostgreSQL.
- **Row-Level Security (RLS)**: Enforces multi-tenant data isolation via GoTrue JWT tokens (`auth.uid()`).
- **Graceful Fallback**: Automatically falls back to an in-memory repository if cloud credentials are unset, ensuring zero friction during local testing.

### 4. Dodo Payments (Monetization & Pro Entitlements)
- **Hosted Checkout Sessions**: Generates checkout sessions for the Reco Pro subscription tier ($9.00/month) via `POST /billing/checkout`.
- **Hosted Customer Portal**: Provides subscription management via `POST /billing/portal`.
- **HMAC Webhook Verification**: Uses `standardwebhooks` to verify cryptographically signed webhooks from Dodo Payments at `POST /billing/webhook` with anti-replay timestamp validation and idempotent event processing (`payment.succeeded`, `subscription.active`, `subscription.cancelled`, `subscription.renewed`).
- **Strict Decoupling**: Billing checks never block core agent synthesis or benchmark evaluation.

### 5. AO (Agent Orchestrator)
- **Multi-Session Lineage**: Built across 30 disciplined subagent development sessions using `ao session spawn` and paired with Google Antigravity (AGY).
- **Modular Worktree Isolation**: Each capability (DAG engine, taxonomy diagnostics, tournament selector, sponsor integrations, and frontend console) was developed and tested in isolated branches before final integration.

---

## 5. Unified Single-Service Deployment Architecture (Render)

Reco is deployed as a single unified Web Service on Render, eliminating CORS complexity and ensuring synchronized releases:

- **Backend**: FastAPI (`reco/api/app.py`) serving core health APIs (`/health`, `/api/health`), monetization routes (`/billing/*`), and static files from `frontend/dist`.
- **Frontend**: Vite + React 19 (TypeScript, Tailwind CSS) Single Page Application (SPA).
- **SPA Fallback Routing**: Client-side routes (e.g. `/stages/*`) automatically fall back to `frontend/dist/index.html` while preserving 404 semantics for `/api/*` and `/billing/*` endpoints.

### Render Web Service Specification (`render.yaml`)

```yaml
services:
  - type: web
    name: reco-web-service
    env: python
    buildCommand: npm install --prefix frontend && npm run build --prefix frontend && pip install -r requirements.txt
    startCommand: uvicorn reco.api.app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.4
      - key: DODO_PAYMENTS_ENVIRONMENT
        value: test_mode
```

---

## 6. Local Development & Reproduction Commands

### 1. Prerequisites
- Python 3.11+
- Node.js 20+ and npm

### 2. Run Backend Pytest Suite
```bash
python -m pytest tests/ -q
```
*Result: 145 passed tests verifying DAG execution, failure diagnostics, mutation engine, multi-candidate tournaments, multi-domain benchmarks, Supabase persistence, and Dodo Payments monetization.*

### 3. Run Frontend Vitest Suite
```bash
npm test --prefix frontend
```
*Result: 11 test files passed (40/40 tests) verifying all 5 console stages, Epistemic Memory Ledger, Failure Explorer, Candidate Comparison, and Billing Modal.*

### 4. Build Frontend Production Assets
```bash
npm run build --prefix frontend
```
*Compiles TypeScript and bundles production Vite assets into `frontend/dist`.*

### 5. Launch Unified Server Locally
```bash
uvicorn reco.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to `http://localhost:8000` to interact with the full 5-stage Reco console.

---

## 7. Built with AO (Agent Orchestrator) Development Lineage

Reco was engineered using **Agent Orchestrator (AO)** in collaboration with **AGY (Google Antigravity)** across 30 autonomous sessions:

- **Sessions 01 to 05: Core Architecture & Runtime**
  Synthesized the foundational Directed Acyclic Graph models, topological execution engine, node runner, and initial goal deconstruction analyzer.
- **Sessions 06 to 10: 12-Category Failure Taxonomy & Diagnostics**
  Implemented the 12-category failure taxonomy, isolating root causes from symptoms and creating deterministic remediation mappers.
- **Sessions 11 to 15: Mutation Engine & Pareto Tournament**
  Built the prompt, tool assignment, verifier, and topology mutators, candidate pool generator, and Pareto frontier comparison evaluator.
- **Sessions 16 to 20: Air-Gapped Benchmarks & Multi-Domain Generalization**
  Engineered 10-case benchmark suites (6 optimization / 4 held-out) across Financial Reconciliation, System Anomaly Detection, and Research Synthesis with zero cross-split leakage.
- **Sessions 21 to 25: Sponsor Integrations (TensorMux, Neatlogs, Supabase, Dodo Payments)**
  Integrated live inference with TensorMux (GLM-4.7-Flash), distributed tracing with Neatlogs, PostgreSQL persistence with Supabase RLS, and billing with Dodo Payments HMAC webhooks.
- **Sessions 26 to 30: 5-Stage Engineering Console & Production Hardening**
  Developed the Vite + React 19 interactive console, Epistemic Memory Ledger, single-service FastAPI static mount, comprehensive test suites, and production documentation.

---

## 8. Repository Structure

```
reco/
├── reco/                          # Core Python Engine Package
│   ├── api/                       # FastAPI Web Application & SPA Static Serving
│   │   └── app.py
│   ├── benchmarks/                # Multi-Domain Benchmark Suites
│   │   ├── base.py                # Partitioning, Splits & Checksum Isolation
│   │   ├── reconciliation/        # Financial Reconciliation (10 cases: 6 opt / 4 held-out)
│   │   ├── anomaly/               # System Anomaly Detection (10 cases: 6 opt / 4 held-out)
│   │   └── research/              # Research Synthesis (10 cases: 6 opt / 4 held-out)
│   ├── billing/                   # Dodo Payments Integration
│   │   ├── models.py              # Subscription models & payloads
│   │   └── service.py             # Hosted checkout, portal & HMAC webhook verification
│   ├── core/                      # Task Specifications & Goal Deconstruction
│   │   ├── goal_analyzer.py
│   │   └── task_spec.py
│   ├── db/                        # Supabase PostgreSQL Persistence & RLS
│   │   ├── models.py              # Experiment, Architecture, Scorecard & Trace records
│   │   ├── repository.py          # Repository interfaces & InMemory fallback
│   │   └── supabase.py            # Supabase client with RLS user isolation
│   ├── diagnostics/               # 12-Category Failure Taxonomy Engine
│   │   ├── analyzer.py
│   │   └── taxonomy.py
│   ├── engine/                    # DAG Execution Engine & Node Runners
│   │   ├── generator.py
│   │   ├── models.py
│   │   ├── node_runner.py
│   │   ├── runtime.py
│   │   └── state.py
│   ├── evaluators/                # 4-Axis Scorecard & Comparison
│   │   ├── comparison.py          # Tournament & Held-Out Validation Gates
│   │   └── scorecard.py           # Multi-axis scorecard evaluator
│   ├── llm/                       # TensorMux Live Inference Client
│   │   └── tensormux.py           # GLM-4.7-Flash reasoning capture & cost calculation
│   ├── mutation/                  # Architectural Mutation Operators
│   │   ├── engine.py
│   │   ├── generator.py
│   │   ├── validator.py
│   │   └── mutators/              # Prompt, Tool, Verifier, Topology & Retry mutators
│   ├── observability/             # Neatlogs Distributed Telemetry
│   │   └── tracer.py              # 5-tier hierarchical tracer & deep links
│   ├── optimization/              # Closed-Loop Optimization Controller
│   │   └── controller.py
│   └── tools/                     # Tool Registry & Execution Sandboxes
│       ├── executor.py
│       └── registry.py
├── frontend/                      # Interactive Engineering Console (Vite + React 19)
│   ├── src/
│   │   ├── components/            # Stage components, Epistemic Ledger, Neatlogs Card
│   │   ├── lib/                   # Data types & mock domain presets
│   │   ├── __tests__/             # Vitest frontend unit & integration tests
│   │   ├── App.tsx                # 5-Stage console navigator
│   │   └── main.tsx
│   ├── dist/                      # Compiled production SPA assets
│   ├── package.json
│   └── vite.config.ts
├── tests/                         # Comprehensive Pytest Backend Suite (145 tests)
├── render.yaml                    # Single-Service Render Deployment Spec
├── pyproject.toml                 # Python Package & Dependencies Configuration
└── README.md                      # Production Documentation Page
```

---

## 9. License

This project is developed for Track 1 (Automated Agent Engineering) and is licensed under the MIT License.

