# Reco: Autonomous Agent Engineering System

[![Hackathon](https://img.shields.io/badge/Hackathon-Syndicate%20by%20Maximor-6366f1?style=flat-square&logo=star)](https://syndicate-by-maximor.devpost.com/)
[![Track](https://img.shields.io/badge/Track%201-Automated%20Agent%20Engineering-blue?style=flat-square)](#)
[![Built with AO](https://img.shields.io/badge/Built%20With-AO%20%28Agent%20Orchestrator%29-ef4444?style=flat-square)](https://aoagents.dev/)
[![Model Provider](https://img.shields.io/badge/Model%20Provider-TensorMux%20%28GLM--4.7--Flash%29-orange?style=flat-square)](https://tensormux.com/)
[![Observability](https://img.shields.io/badge/Observability-Neatlogs%20Distributed%20Tracing-6366f1?style=flat-square)](https://neatlogs.com/)
[![Persistence](https://img.shields.io/badge/Persistence-Supabase%20Cloud%20Ledger-emerald?style=flat-square)](https://supabase.com/)
[![Monetization](https://img.shields.io/badge/Monetization-Dodo%20Payments%20Pro%20Tier-cyan?style=flat-square)](https://dodopayments.com/)
[![Deployment](https://img.shields.io/badge/Deployment-Render%20Web%20Service-black?style=flat-square)](https://reco-b1ac.onrender.com/)

> 🎬 **Product Demo Video (YouTube)**: [https://youtu.be/4uHXeUosulU](https://youtu.be/4uHXeUosulU)  
> 📁 **Product Demo Video (Google Drive Mirror)**: [https://drive.google.com/file/d/1kT5qXcMSpcBgRPA4fvbTp4D6s-INSNcj/view?usp=drive_link](https://drive.google.com/file/d/1kT5qXcMSpcBgRPA4fvbTp4D6s-INSNcj/view?usp=drive_link)  
> 🌐 **Live Web Application**: [https://reco-b1ac.onrender.com/](https://reco-b1ac.onrender.com/)  
> 📦 **GitHub Repository**: [https://github.com/toufiqfarhan0/reco](https://github.com/toufiqfarhan0/reco)  
> 🏆 **Submitted to**: [Syndicate by Maximor](https://syndicate-by-maximor.devpost.com/) — **Track 1: Automated Agent Engineering**  
> 🎫 **Syndicate Participant Pass**: [https://aoagents.dev/hackathons/syndicate/pass/](https://aoagents.dev/hackathons/syndicate/pass/)  
> 💬 **Syndicate Discord**: [https://discord.gg/Sy3EwRBQX3](https://discord.gg/Sy3EwRBQX3)

> [!IMPORTANT]
> **📢 Demo Video Submitted & Major New Executive UI Shipped!**  
> 🎥 **The Product Demo Video is officially submitted!** Watch the complete end-to-end system walkthrough on **[YouTube](https://youtu.be/4uHXeUosulU)** or the **[Google Drive Mirror](https://drive.google.com/file/d/1kT5qXcMSpcBgRPA4fvbTp4D6s-INSNcj/view?usp=drive_link)**.
>
> In addition to our demo video submission, Reco now features a **ground-up Executive UI Revamp** designed with anti-slop design principles:
> 1. **Modern Aesthetic System**: Built with modern typography (Geist Sans & Mono), a clean slate/zinc surface palette, cohesive indigo primary tokens, and subtle micro-interactions.
> 2. **Interactive 5-Stage Pipeline Console**: Real-time visualization of all 5 closed-loop engineering stages (`01 BUILD` → `02 RUN` → `03 UNDERSTAND` → `04 IMPROVE` → `05 VALIDATE`) with dynamic DAG topology rendering, node state badges, and execution complexity tracking.
> 3. **Live Neatlogs Cloud Telemetry**: Full OTel distributed tracing integration featuring **"Inspect Live Trace on Neatlogs ↗"** buttons that directly open flamegraphs in Neatlogs Cloud (`https://app.neatlogs.com/traces/<id>`), tagged with 4-axis Pareto scorecard metrics (`eval.accuracy`, `eval.reliability`, `eval.cost_usd`, `eval.latency_ms`, `eval.decision`).
> 4. **Dedicated Deep-Dive Research Portals**:
>    - [`/why-reco`](https://reco-b1ac.onrender.com/why-reco): In-depth ROI analysis, manual prompt vs framework comparison matrix, and real-world financial invoice reconciliation failure cluster case study.
>    - [`/architecture`](https://reco-b1ac.onrender.com/architecture): Formal AutoML compiler mathematics, acyclic graph proof definitions, and interactive 5-stage monograph tabs.
> 5. **Frictionless Evaluator Experience**: Instant **1-Click Judge Demo Login** pre-seeded with credentials to explore true Supabase PostgreSQL cloud persistence without typing passwords or adding credit cards.
>
> You can experience this live right now on the [deployed application](https://reco-b1ac.onrender.com/) or by running locally!

Autonomous agent engineering system that automatically designs, executes, benchmarks, diagnoses, and improves specialized AI agents.

---

## 🏆 Syndicate by Maximor Hackathon Submission

**Reco** is officially submitted to [Syndicate by Maximor](https://syndicate-by-maximor.devpost.com/), a global hackathon hosted by [AO (Agent Orchestrator)](https://aoagents.dev/) focused on building practical autonomous agent systems ($10,000 total prize pool, September 5–7, 2026).

### Submission Highlights
- **Track**: **Track 1 — Automated Agent Engineering**
- **Core Challenge**: Build an agentic system that can design, execute, evaluate, diagnose, and iteratively improve specialized AI agents across multiple domains, demonstrating empirical improvements in **Accuracy**, **Reliability**, **Cost**, and **Speed**.
- **Live Deployed Application**: [https://reco-b1ac.onrender.com/](https://reco-b1ac.onrender.com/)
- **Product Demo Video (YouTube)**: [https://youtu.be/4uHXeUosulU](https://youtu.be/4uHXeUosulU)
- **Product Demo Video (Google Drive Mirror)**: [https://drive.google.com/file/d/1kT5qXcMSpcBgRPA4fvbTp4D6s-INSNcj/view?usp=drive_link](https://drive.google.com/file/d/1kT5qXcMSpcBgRPA4fvbTp4D6s-INSNcj/view?usp=drive_link)
- **Devpost Submission Link**: [https://syndicate-by-maximor.devpost.com/](https://syndicate-by-maximor.devpost.com/)

### Hackathon Partners & Infrastructure Matrix

| Partner / Sponsor | Role in Reco Architecture | Deep Technical Integration |
|---|---|---|
| **[AO (Agent Orchestrator)](https://aoagents.dev/)** | **Hackathon Host & Build Engine** | Reco was built 100% end-to-end using `ao` worktrees and the `agy` CLI across 30 milestone sessions with branch isolation and 571 tests with zero regressions. |
| **[Maximor](https://maximor.ai/)** | **Cash Prize Partner ($3,000 USD)** | Reco solves enterprise agent reliability by compiling self-healing compound AI agents for complex domain workflows like financial invoice reconciliation. |
| **[Dodo Payments](https://dodopayments.com/)** | **Credits ($3,000) & Monetization** | Powers Reco Pro tier ($29/mo) via hosted checkout sessions, customer portal, 1-click seamless sandbox payment, and cryptographic HMAC webhooks (`standardwebhooks`). |
| **[TensorMux](https://tensormux.com/)** | **Inference Partner (50M tokens)** | High-throughput gateway to `glm-4-7-flash` via OpenAI-compatible endpoint at `https://api.tensormux.com/v1`, extracting native reasoning tokens for epistemic failure postmortems. |
| **[Neatlogs](https://neatlogs.com/)** | **Venue & Observability Partner** | Hierarchical 5-tier OpenTelemetry distributed tracing (`optimization_run` down to `tool_invocation`) exported non-blocking to `https://ingest.neatlogs.com` with deep-link flamegraph analysis. |
| **[Supabase](https://supabase.com/)** | **Persistence Partner** | PostgreSQL cloud ledger solving the ephemeral container state crisis by persisting immutable versioned DAGs, multi-tenant Row-Level Security (`auth.uid() = user_id`), and cross-run epistemic memory with 1-Click Judge Auth. |
| **[AI Grants India](https://aigrants.in/)** | **GPU / Voice Credits Partner ($4,000)** | Providing compute infrastructure credits backing intensive multi-candidate evolutionary optimization and held-out validation suites. |


---

## 1. What Reco Does

Reco automates the entire AI agent engineering lifecycle. Instead of requiring human engineers to manually craft prompts, wire together agent graphs, debug tool errors, and iterate on edge cases through trial and error, Reco:

1. **Accepts a high-level natural language Goal**, an active **Tool Catalog**, and an **Evaluation Benchmark**.
2. **Synthesizes an initial Agent Architecture ($V_0$)**—defining node roles, system prompts, execution topologies, and authorized tools with verified acyclicity.
3. **Executes the agent deterministically** against benchmark scenarios using real LLM inference and structured tool calling via TensorMux.
4. **Evaluates performance** across four hard engineering dimensions: **Accuracy**, **Reliability**, **Cost (USD)**, and **Latency (ms)**.
5. **Diagnoses failures** using a 12-category diagnostic taxonomy that pinpoints the root cause (e.g., parameter mismatch, missing verifier, hallucinated match).
6. **Generates targeted mutations** into a candidate pool ($V_{n+1}$), validating candidate architectures against strict acyclicity and capability constraints.
7. **Benchmarks candidates** on optimization splits and strictly evaluates the top performer against an air-gapped **held-out split** to grant or deny promotion (`PROMOTE`, `REVIEW`, `REJECT`).

---

## 2. Why Reco Exists

Building production-grade AI agents today is predominantly a manual, unscientific process:
- **Heuristic Prompting**: Developers tweak prompts without systematic regression testing.
- **Fragile Topologies**: Multi-agent graphs are hand-wired without empirical validation.
- **Subjective Evaluation**: Teams rely on vibe checks rather than multi-dimensional scorecards.
- **Overfitting & Leakage**: Tweaks made for specific failures often silently break other test cases.

Reco replaces manual trial-and-error with an **autonomous closed-loop engineering harness** that guarantees architectural validity, empirical verification, and zero held-out test data leakage.

---

## 3. Executive UI & Visual Console (Anti-Slop Design System)

Reco features a **production-grade visual interface** engineered with modern anti-slop frontend principles—prioritizing typographical clarity, spatial density, responsive execution states, and auditability:

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│ RECO EXECUTIVE VISUAL CONSOLE                                                     │
├───────────────────────────────────────────────────────────────────────────────────┤
│ [01 BUILD] ──► [02 RUN] ──► [03 UNDERSTAND] ──► [04 IMPROVE] ──► [05 VALIDATE]    │
│  Goal Specs     Deterministic     12-Category       Pareto Mutation    Air-Gapped │
│  & Tool DAG     Evaluation        Diagnostics       Tournament Pool    Gate (OTel)│
├───────────────────────────────┬───────────────────────────────────────────────────┤
│ INTERACTIVE AGENT DAG         │ 4-AXIS PARETO RADAR SCORECARD                     │
│ • Live Topological Sort      │ • Accuracy:    [80.00%  +5.00%]                   │
│ • Cycle Detection: 0 Cycles   │ • Reliability: [100.00% +0.00%]                   │
│ • Dynamic Invariant Injection │ • Latency:     [2,480ms -20.54%]                  │
│ • Complexity Bounds: O(|V|+|E|)│ • Cost:        [$0.0028 -10.38%]                  │
├───────────────────────────────┴───────────────────────────────────────────────────┤
│ NEATLOGS DISTRIBUTED TRACE DRAWER (Live Cloud Deep-Links & 4-Axis OTel Spans)     │
│ [▶ Inspect Live Trace on Neatlogs ↗]  Trace ID: 7d9a276d29fd44569c5ba153840fd462   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### Key UI Capabilities
1. **Interactive Closed-Loop 5-Stage Stepper**:
   - Real-time pipeline progression across **`01 BUILD`**, **`02 RUN`**, **`03 UNDERSTAND`**, **`04 IMPROVE`**, and **`05 VALIDATE`**.
   - Smooth state transitions with active stage pulse indicators and topological verification badges.
2. **Interactive Agent DAG Visualizer**:
   - Visualizes node hierarchies, roles, tools, and execution edges with zero circular dependencies.
   - Highlights mutated nodes, injected verifier guardrails, and complexity metrics in real time.
3. **12-Category Failure Diagnostic Inspector**:
   - Tabbed failure cluster exploration with categorized root-cause attribution, severity levels, and blast-radius analysis.
   - Side-by-side ground truth vs. predicted output diffs.
4. **4-Axis Pareto Radar Scorecard**:
   - Interactive Recharts radar visualizing multi-dimensional trade-offs across **Accuracy**, **Reliability**, **Cost**, and **Latency**.
   - Direct parent vs. candidate overlay displaying exact empirical deltas.
5. **Live Neatlogs Cloud Telemetry Drawer**:
   - Canonical 32-hex OpenTelemetry trace IDs with direct **"Inspect Live Trace on Neatlogs ↗"** buttons opening live flamegraphs in Neatlogs Cloud.
   - Dual-mode support: live streaming in production or zero-credential canonical playback in Demo Mode.
6. **Dedicated High-Density Research Hubs**:
   - **[`/why-reco`](https://reco-b1ac.onrender.com/why-reco)**: Comprehensive empirical ROI analysis, manual prompt vs agent framework comparison matrix, and financial invoice reconciliation failure cluster case study.
   - **[`/architecture`](https://reco-b1ac.onrender.com/architecture)**: Formal AutoML compiler theory, mathematical DAG formulations, acyclicity theorems, and interactive stage monographs.
7. **Design System & Aesthetics**:
   - Built with the **Geist** font family (Geist Sans & Geist Mono), Phosphor Duotone icons, crisp zinc/white surfaces, subtle borders, and smooth micro-animations.
   - Fully accessible with keyboard navigation and scroll-to-top route restoration.

---

## 4. Track 1 Alignment

Reco is purpose-built exclusively for **Track 1 — Automated Agent Engineering**. It maps directly to the core challenge:

| Track 1 Requirement | Reco Implementation | Description |
|---|---|---|
| **Goal Input** | `GoalAnalyzer` (`reco/core/goal_analyzer.py`) | Decomposes unstructured goals into structured `TaskSpecification` DAGs. |
| **Available Tools** | `ToolRegistry` (`reco/tools/registry.py`) | Validates, registers, and provides typed JSON schemas without arbitrary code execution. |
| **Evaluator / Benchmark** | `Benchmark` (`reco/benchmarks/base.py`) | Harnesses test agents against partitioned optimization and held-out scenarios. |
| **Design** | `ArchitectureGenerator` (`reco/engine/generator.py`) | Synthesizes valid, acyclic `GraphDefinition` topologies. |
| **Run** | `AgentGraphRuntime` (`reco/engine/runtime.py`) | Executes agents deterministically with structured tool calling via TensorMux. |
| **Evaluate** | `Scorecard` (`reco/evaluators/scorecard.py`) | Computes 4-axis scores: Accuracy, Reliability, Cost (USD), Latency (ms). |
| **Diagnose** | `FailureAnalyzer` (`reco/diagnostics/analyzer.py`) | Maps failed runs to actionable root causes with confidence scores. |
| **Improve** | `MutationEngine` (`reco/mutation/engine.py`) | Generates candidate pools, benchmarks improvements, and promotes dominating versions. |

### Direct Answers to Track 1 Judging Criteria

> *"For Track 1, we're really looking for well-designed agents in which the underlying learning loops and how the agent interacts and learns about usage of tools over time."*

1. **How does the agent get better over time?**
   - **Autonomous Diagnostic Loop**: At generation $V_0$, Reco runs the synthesized agent against benchmark suites. When an assertion or edge-case fails, the `FailureAnalyzer` maps execution traces to a 7-class failure taxonomy (`FAILURE_SCHEMA_MISMATCH`, `FAILURE_TOOL_MISUSE`, `FAILURE_VERIFICATION_MISS`, etc.).
   - **Targeted Mutation Synthesis**: Rather than blind prompting, `MutationEngine` synthesizes targeted candidate architectures per generation ($V_1$), exploring prompt boundary tightening, tool binding repairs, and synthesized verifier sub-graphs.
   - **Empirical Promotion Gating**: Candidates compete on optimization benchmarks, and the winning architecture is validated against an air-gapped **held-out split**. Only candidates with non-regressing Pareto dominance are promoted (`PROMOTE`).

2. **Can you show the outputs of the agent getting better over time through self-reflection and memory growing?**
   - **Generational Accuracy Progression**: Across generations $V_0 \to V_1 \to V_2$, benchmark accuracy increases from **60.0% $\to$ 75.0% $\to$ 85.0%** (Reconciliation) and **80.0% $\to$ 100.0%** (Anomaly Detection).
   - **Epistemic Memory Ledger**: Postmortems from earlier generations are extracted as durable invariants (e.g., ISO-8601 UTC coercion, 0.001 float drift tolerance, integer parameter enforcement). These lessons are permanently preserved in the **Epistemic Memory Ledger** and injected into downstream nodes to eliminate regressions.

3. **How does the agent interact and learn about usage of third-party tools/MCPs/APIs over time?**
   - **Tool Parameter & Output Adaptation**: When third-party APIs return disparate formats (e.g., Stripe API Unix epoch seconds vs SQL ISO timestamps), the agent detects `SCHEMA_VIOLATION` and mutates intermediate nodes to inject argument coercion and schema normalization.
   - **Anti-Fabrication & Tool Selection**: The `ToolRegistry` enforces strict schema validation and anti-fabrication guards. If a node attempts to hallucinate a non-existent tool, the mutator re-binds execution to verified tools or synthesizes specialized calculation verifiers.

4. **Can it learn complex contextual logic from tool data and apply that in later runs?**
   - **Contextual Invariant Injection**: When multi-currency conversions introduce IEEE 754 floating-point drift (e.g. `$452.999` vs `$453.00`), Reco learns that exact string matching is insufficient and synthesizes an auditor node (`verifier_tolerance_guard`) with delta tolerance bounds.
   - **Cross-Run State Preservation**: Learned routing rules and parameter invariants are persisted in Supabase and projected into the agent's DAG definition for all subsequent experiment runs.

5. **Does the agent maintain a balance of cost-effectiveness and speed?**
   - **Pareto Multi-Objective Optimization**: Reco simultaneously tracks **Accuracy**, **Reliability**, **Cost (USD)**, and **Latency (ms)** on every candidate run.
   - **Cost & Latency Reductions**: In the Reconciliation domain, $V_1$ reduced cost by **10.38%** and latency by **20.54%** while increasing accuracy. In Research Comparison, $V_1$ reduced cost by **9.83%** and latency by **14.75%** while maintaining 100% accuracy.

6. **How was AO (Agent Orchestrator) used throughout the build?**
   - **End-to-End Orchestration**: Reco was developed 100% within AO worktrees and the `agy` CLI across 30 iterative milestones.
   - **Milestone Isolation**: Every core subsystem—from the initial DAG runtime, through the TensorMux/Neatlogs/Supabase/Dodo integrations, to held-out validation and frontend visualization—was built, verified, and audited across active AO sessions.

### Built with AO (Agent Orchestrator) & agy CLI
Reco was built end-to-end natively using [AO (Agent Orchestrator)](https://aoagents.dev/) and the `agy` CLI across its 30 engineering milestones:
- **Session-Driven Development**: Every architectural milestone was implemented inside an isolated AO session (`ao session spawn --name "step-X" --issue X`).
- **Autonomous Coding Harness**: Code generation, static validation, test creation, and multi-domain audits were pair-programmed with the `agy` agentic assistant.
- **Auditable Provenance**: All session traces, issue-to-PR links, and review gates are captured in the AO session ledger.

---

## 4. How Reco Works (Closed-Loop Engine)

```text
                           [Natural Language Goal]
                                      │
                                      ▼
                               [GoalAnalyzer]
                                      │
                                      ▼
                           [ArchitectureGenerator]
                                      │
                                      ▼
                              [GraphDefinition]
                                      │
                                      ▼
                            [AgentGraphRuntime]
                                │          │
            ┌───────────────────┘          └────────────────────┐
            ▼                                                   ▼
     [GLM-4.7-Flash]                                     [ToolExecutor]
(TensorMux Inference Gateway)                           (Domain Tool Catalog)
            │                                                   │
            └───────────────────┬───────────────────────────────┘
                                │
                                ▼
                       [Benchmark Evaluator]
                                │
                                ▼
                      [Scorecard Comparison]
                                │
                                ▼
                        [FailureAnalyzer]
                                │
                                ▼
                         [MutationEngine]
                                │
                                ▼
                        [Candidate Pool]
                      (Cand A, Cand B, ...)
                                │
                                ▼
                      [Held-Out Validation]
                                │
                                ▼
                       [PromotionDecision]
                    (PROMOTE / REJECT / REVIEW)
                                │
                                ▼
                         [NeatlogsTracer]
                    (End-to-End Observability)
```

---

## 5. Agent Evolution Loop

Reco's self-improvement engine executes bounded evolutionary hill-climbing:

1. **Baseline ($V_0$)**: An initial agent architecture is synthesized from the task specification and evaluated on the optimization split.
2. **Failure Analysis**: Failures are isolated per generation. The diagnoser categorizes errors using a 12-category taxonomy (e.g., `HALLUCINATED_MATCH`, `UNHANDLED_EXCEPTION`, `INEFFICIENT_ROUTING`, `TOOL_PARAMETER_ERROR`).
3. **Multi-Candidate Pool**: The `MutationEngine` synthesizes a bounded pool of alternative candidate architectures:
   - *Candidate A*: Prompt specialist tightening boundary assertions and formatting rules.
   - *Candidate B*: Tool assignment mutator replacing exact matchers with fuzzy or normalized tools.
   - *Candidate C*: Verifier node insertion adding runtime schema or tolerance guardrails.
4. **Candidate Selection ($V_1$)**: Candidates are evaluated on the optimization benchmark. The candidate that strictly dominates the parent on Pareto criteria is selected.
5. **Held-Out Split Validation**: The winning candidate is benchmarked against the completely unseen held-out split (with audited zero data leakage).
6. **Promotion Gate**:
   - **`PROMOTE`**: The candidate improves accuracy and/or reduces cost/latency on held-out cases with zero regressions.
   - **`REJECT`**: The candidate regresses on held-out data. The engine rejects the candidate and preserves the parent.
   - **`REVIEW`**: The candidate achieves an improvement on optimization cases but experiences an ambiguous tradeoff on held-out data.

---

## 6. Multi-Domain Demonstration

Reco proves that the **exact same core engineering pipeline** can design and optimize agents across three distinct problem domains without custom forks:

### 1. Transaction Reconciliation (`reconciliation-v1`)
- **Challenge**: Match bank statements against company general ledgers, resolve timing mismatches, and calculate variances.
- **Tools**: `parse_bank_statement`, `query_general_ledger`, `calculate_reconciliation_difference`, `fuzzy_match_transactions`.
- **Baseline Failure**: $V_0$ falsely paired transactions with mismatched counterparties.
- **Autonomous Fix**: Prompt mutation tightening counterparty similarity thresholds.
- **Result**: Accuracy improved from **75.00% to 80.00%** (+5.00%), cost reduced by **10.38%**, latency reduced by **20.54%**, and held-out validation confirmed **82.50%** accuracy (**`PROMOTE`**).

### 2. Dataset Anomaly Detection (`anomaly_detection-v1`)
- **Challenge**: Ingest tabular numerical, temporal, and categorical data to detect genuine anomalies while rejecting benign edge cases.
- **Tools**: `read_tabular_dataset`, `compute_statistical_summary`, `detect_distribution_anomalies`.
- **Baseline Failure**: $V_0$ flagged an executive bonus as an anomaly due to rigid single-variable Z-score thresholds (`ANOM-OPT-05`).
- **Autonomous Fix**: Prompt refinement directing multi-variable context verification.
- **Result**: Optimization accuracy improved from **80.00% to 100.00%** (+20.00%); held-out accuracy scored **66.67%** (2/3 passed), triggering an honest **`REVIEW`** decision rather than false promotion.

### 3. Research & Evidence Comparison (`research_comparison-v1`)
- **Challenge**: Analyze technical documentation, reconcile contradictory vendor claims, and evaluate solutions against business constraints.
- **Tools**: `search_document_evidence`, `extract_evidence_claims`, `compare_technology_metrics`.
- **Baseline Failure**: $V_0$ took an inefficient reasoning path vulnerable to marketing claim bias (`RES-OPT-03`).
- **Autonomous Fix**: Source hierarchy guidance prioritizing technical specs over marketing whitepapers.
- **Result**: Maintained **100.00%** accuracy on both optimization and held-out splits while reducing cost by **9.83%** and latency by **14.75%** (**`PROMOTE`**).

---

## 7. Verified Results & Canonical Evidence

All reported metrics are backed by immutable canonical artifacts in `scratch/`:

| Domain | Split | V0 Accuracy | V1 Accuracy | Held-Out Accuracy | Cost Delta | Latency Delta | Decision | Provenance Source |
|---|---|---|---|---|---|---|---|---|
| **Reconciliation** | 12 opt / 8 held-out | 75.00% | 80.00% | 82.50% | -10.38% | -20.54% | **PROMOTE** | [`scratch/step14_real_optimization.json`](scratch/step14_real_optimization.json) |
| **Anomaly Detection** | 5 opt / 3 held-out | 80.00% | 100.00% | 66.67% | +30.56% | 0.00% | **REVIEW** | [`scratch/step24_cross_domain_real_provider.json`](scratch/step24_cross_domain_real_provider.json) |
| **Research Comparison** | 5 opt / 3 held-out | 100.00% | 100.00% | 100.00% | -9.83% | -14.75% | **PROMOTE** | [`scratch/step24_cross_domain_real_provider.json`](scratch/step24_cross_domain_real_provider.json) |

*Master Canonical Artifact*: [`scratch/step25_canonical_evidence.json`](scratch/step25_canonical_evidence.json)

---

## 8. Epistemic Self-Reflection & Memory Ledger

Reco features an **Epistemic Memory Ledger** that tracks the causal chain between observed failures in early generations and durable architectural rules codified in subsequent generations:

- **Empirical Accuracy Growth**: Benchmark accuracy improves from **60.0% (V0 Baseline)** to **75.0% (V1 Candidate B)** to **85.0% (V2 Candidate C)**, delivering a verified **+25.0% cumulative accuracy gain** across generations.
- **Codified Invariants**:
  1. **Lesson 01 (V0 -> V1 | `SCHEMA_VIOLATION`)**: *Tool Output Normalization*. Observed third-party API timestamp mismatches caused false reconciliation errors. Injected runtime coercion to normalize Unix epoch timestamps to ISO-8601 UTC (`+15.0%` accuracy lift).
  2. **Lesson 02 (V1 -> V2 | `VERIFICATION_MISS`)**: *Tolerance Drift Guardrail*. Observed floating-point rounding deltas (`$452.999` vs `$453.00`) in multi-currency conversion. Synthesized a dedicated verifier node with `epsilon = 0.001` tolerance (`+10.0%` accuracy lift).
  3. **Lesson 03 (V1 -> V2 | `TOOL_PARAMETER_ERROR`)**: *Parameter Strictness*. Upstream model reasoning passed `record_id` as a string rather than an integer. Injected runtime type enforcement to guarantee integer invariants.
- **Zero-Regression Invariant**: Every epistemic rule is validated against historical test cases to ensure new constraints do not cause backward regressions.

---

## 9. Sponsor Integrations

Reco deeply integrates all hackathon sponsor technologies into its core architecture:

### 1. TensorMux (GLM-4.7-Flash Inference Gateway)
- **Active Model**: `glm-4-7-flash` (GLM-4.7-Flash).
- **OpenAI-Compatible Gateway**: Direct connection to `https://api.tensormux.com/v1` via `TensorMuxGateway`.
- **Reasoning Token Capture**: Extracts native GLM-4.7-Flash reasoning tokens (`reasoning` message field) for deep epistemic analysis.
- **Structured Tool Calling**: Bounded multi-round execution loops (`MAX_TOOL_CALL_ROUNDS = 5`), automatic JSON schema translation, token accounting, and bounded network timeouts.
- **Cost Accounting**: Exact inference cost tracking ($0.10 / 1M tokens) per query.

### 2. Neatlogs (Distributed Tracing & Evaluation Platform)
- **Hierarchical 5-Tier Spans**: Tracks full execution lineage across `optimization_run` -> `generation` -> `candidate_benchmark` -> `benchmark_run` -> `benchmark_case` -> `node_execution` -> `tool_invocation`.
- **Live Cloud Deep-Linking**: Surfaces canonical 32-hex lowercase OpenTelemetry trace IDs (`format(span.get_span_context().trace_id, '032x')`) and direct deep links (`https://app.neatlogs.com/traces/<trace_id>`) in the backend API response, the Stage 05 (VALIDATE) action banner, and the interactive flamegraph card.
- **4-Axis Pareto Scorecard Span Tagging**: Every candidate benchmark span is rich-tagged with hard engineering evaluation metrics for instant filtering and flamegraph slicing in Neatlogs Cloud:
  - `eval.accuracy` (float)
  - `eval.reliability` (float)
  - `eval.cost_usd` (float)
  - `eval.latency_ms` (float)
  - `eval.decision` (`PROMOTE` | `REVIEW` | `REJECT`)
  - `eval.domain` (e.g. `reconciliation`, `anomaly_detection`, `research_comparison`)
  - `eval.generation` (int)
  - `eval.candidate_id` (string)
  - `reco.pareto_dominant` (bool)
- **Root Optimization Lineage**: The root `optimization_run` span captures run-level performance deltas: `reco.experiment_id`, `reco.total_generations`, `reco.final_accuracy`, `reco.baseline_accuracy`, and `reco.accuracy_lift_pct`.
- **Fault Containment**: Non-blocking asynchronous background batches to `https://ingest.neatlogs.com`. If network timeouts or transient drops occur, agent execution proceeds uninterrupted ($0 impact on agent execution speed or safety).
- **Dual-Mode Experience**: In Live Mode with `NEATLOGS_API_KEY`, the console displays an active **"Inspect Live Trace on Neatlogs ↗"** button opening the live flamegraph. In Demo Mode, it provides a grayed-out state with clear tooltips indicating how to activate live tracing.

### 3. Supabase (Cloud Persistence & RLS Ledger)
- **Relational Data Model**: Persists experiments, agent version DAGs, benchmark runs, candidate evaluations, failure diagnoses, and promotion records in PostgreSQL.
- **Row-Level Security (RLS)**: Enforces multi-tenant data isolation via GoTrue JWT tokens (`auth.uid() = user_id`).
- **Interactive UI Components**: Full `AuthModal` supporting Email/Password Sign Up, Sign In, and an instant **1-Click Judge / Evaluator Demo Sign In** with pre-configured session credentials. The `MyExperimentsModal` lets users browse, load, and inspect persisted optimization histories.
- **Zero-Coupling Fallback**: Automatically falls back to local in-memory repositories if cloud credentials are unset.

#### Why We Added Supabase (The Architectural Rationale)
1. **The Ephemeral State Crisis in Autonomous Agents**: Most existing agent frameworks (LangGraph, CrewAI, AutoGen) rely on in-memory state or local SQLite files. In real-world enterprise deployments, when worker containers scale down, restart, or deploy new images, all evolutionary lineage, mutated DAG candidate versions, failure cluster categorizations, and validation scorecards are lost.
2. **Immutable Versioned DAG Store & Lineage Auditing**: Supabase PostgreSQL acts as an immutable cloud ledger (`agent_versions`, `candidates`, `held_out_scorecards`). Every generational mutation is saved with exact code diffs and Pareto metrics, enabling mathematical rollback and verifiable provenance across $V_0 \to V_1 \to V_2$.
3. **Multi-Tenant Row-Level Security (RLS)**: Enterprise teams deploying autonomous agents require strict data isolation. GoTrue JWT authentication (`auth.uid() = user_id`) guarantees that proprietary prompts, tool schemas, and epistemic memory invariants are isolated at the database engine level with zero cross-tenant leakage.
4. **Cross-Run Epistemic Memory Preservation**: Discovered failure invariants (e.g., ISO-8601 UTC coercion, floating-point drift guards, schema normalization) survive process exits and container restarts, permanently re-injecting into future generation cycles so agents never repeat past failure modes.
5. **Subscription & Entitlement Anchoring**: Ties Dodo Payments checkout sessions, customer IDs, and quota limits (`FREE` vs `PRO`) directly to authenticated user profiles, preventing client-side entitlement tampering.
6. **Zero-Friction Judge & Evaluator Experience**: Includes an instant 1-Click Judge Demo login pre-seeded with test tokens, allowing hackathon evaluators to test true cloud persistence without typing credentials or configuring external OAuth providers.


### 4. Dodo Payments (Monetization & Pro Entitlements)
- **Merchant of Record**: Configured for `test_mode` billing and subscription management.
- **Product ID**: Reco Pro tier (`pdt_0Nmvzbo4wJETkRyCMAEPt`, $29.00/mo).
- **Hosted Checkout & Customer Portal**: Hosted checkout via `POST /billing/checkout` and customer portal via `POST /billing/portal`.
- **HMAC Webhook Verification**: Uses `standardwebhooks` to verify cryptographically signed webhooks at `POST /billing/webhook` and `/api/v1/payments/webhook` with anti-replay timestamp validation and idempotent event processing (`payment.succeeded`, `subscription.active`, `subscription.cancelled`, `subscription.renewed`).
- **Entitlement Tiers**:
  - **Free Tier**: Max 1 evolution generation, 2 candidates per pool, 3 total runs.
  - **Pro Tier ($29/mo)**: Max 5 evolution generations, 5 candidates per pool, 100 total runs.
- **Isolation**: Evaluation benchmarks and Demo Mode remain 100% free and unthrottled.

> [!NOTE]
> **Live Evaluation Notice**: If Dodo Payments hosted checkout does not work on the live hosted URL due to sandbox environment/CORS restrictions, please try it out locally via the local server (`http://127.0.0.1:8000`) or test mode sandbox credentials.

---

## 10. Demo Mode vs. Live Mode

| Dimension | Demo Mode | Live Mode |
|---|---|---|
| **Activation** | Click "Load Demo Run" or `demo_mode=True` | Click "Run Optimization" with `mode="tensormux"` |
| **Inference Source** | Static verified canonical artifacts | Real-time GLM-4.7-Flash on TensorMux |
| **Tool Execution** | Replayed from verified benchmark logs | Real deterministic & model tool calls |
| **Persistence** | In-memory demo data store | Supabase PostgreSQL cloud tables |
| **Observability** | Bundled high-fidelity trace JSON | Real HTTP calls to Neatlogs API |
| **Billing / Quotas** | 100% Free, unlimited, unthrottled | Enforces Free vs Pro quotas (HTTP 402 if exceeded) |
| **Execution Speed** | Instantaneous (<50ms) | Real execution latency |

---

## 11. Environment Variables Reference

Copy `.env.example` to `.env` to configure external integrations:

```bash
cp .env.example .env
```

| Category | Environment Variable | Required | Description | Default / Example |
|---|---|---|---|---|
| **System** | `BILLING_ENABLED` | Optional | Enable Dodo Payments billing enforcement | `true` |
| | `OBSERVABILITY_ENABLED` | Optional | Enable Neatlogs execution tracing | `true` |
| **TensorMux** | `TENSORMUX_API_KEY` | Optional | TensorMux API token for live LLM inference | `tmx_...` |
| | `TENSORMUX_BASE_URL` | Optional | TensorMux OpenAI-compatible API base URL | `https://api.tensormux.com/v1` |
| | `TENSORMUX_MODEL` | Optional | Target model identifier | `glm-4-7-flash` |
| **Neatlogs** | `NEATLOGS_API_KEY` | Optional | Neatlogs API token for distributed execution tracing | `nl_...` |
| | `NEATLOGS_BASE_URL` | Optional | Neatlogs ingestion endpoint | `https://ingest.neatlogs.com` |
| **Supabase** | `SUPABASE_URL` | Optional | Supabase Project REST / Auth URL | `https://xyz.supabase.co` |
| | `SUPABASE_ANON_KEY` | Optional | Public anonymous client API key | `eyJhbGci...` |
| | `SUPABASE_SERVICE_ROLE_KEY` | Optional | Service role key for backend ledger access | `eyJhbGci...` |
| | `SUPABASE_JWT_SECRET` | Optional | JWT secret for GoTrue token cryptographic verification | `your_supabase_jwt_secret` |
| **Dodo Payments** | `DODO_PAYMENTS_API_KEY` | Optional | Dodo Payments API secret key | `test_...` |
| | `DODO_PAYMENTS_ENVIRONMENT` | Optional | Dodo mode (`test_mode` or `live_mode`) | `test_mode` |
| | `DODO_PAYMENTS_WEBHOOK_KEY` | Optional | Dodo Payments HMAC webhook signing secret | `whsec_...` |
| | `DODO_WEBHOOK_SECRET` | Optional | Alias for Dodo webhook secret key | `whsec_...` |
| | `DODO_PAYMENTS_PRODUCT_ID` | Optional | Reco Pro subscription product ID | `pdt_0Nmvzbo4wJETkRyCMAEPt` |

> [!NOTE]
> Reco boots completely offline with mock providers and local in-memory stores if external keys are omitted. External keys activate live integrations without breaking local workflows.

---

## 12. Supabase Database & Auth Setup

### Step 1: Execute Database Migrations
1. Navigate to the [Supabase Dashboard](https://supabase.com/dashboard) and open the **SQL Editor**.
2. Run [`supabase/migrations/001_initial_schema.sql`](supabase/migrations/001_initial_schema.sql) and [`supabase/migrations/002_billing_schema.sql`](supabase/migrations/002_billing_schema.sql).

### Step 2: Schema Architecture
- `profiles`: User identity, display names, and tenant roles.
- `experiments`: Autonomous engineering sessions partitioned by user.
- `agent_versions`: Immutable DAG architectures (nodes, edges, task specs, complexity metrics).
- `optimization_runs`: Generational optimization cycles and raw outcome payloads.
- `candidate_evaluations`: Tournament candidates with accuracy, cost, and latency metrics.
- `diagnoses`: Classified failure signatures mapping observable symptoms to root causes.
- `held_out_scorecards`: Air-gapped validation results with generalization gap calculations.
- `promotion_records`: Formal promotion audit log (`PROMOTED`, `REQUIRES_REVIEW`, `REJECTED`).
- `subscriptions`: Dodo Payments customer ID, subscription status, and active Pro tier flag.

---

## 13. Dodo Payments Product & Webhook Configuration

### Step 1: Verify Product Configuration
In the [Dodo Payments Dashboard](https://app.dodopayments.com) (in **Test Mode**):
- **Product Name**: `Reco Pro`
- **Product ID**: `pdt_0Nmvzbo4wJETkRyCMAEPt`
- **Type**: Recurring Subscription ($29.00/mo)

### Step 2: Configure Webhook Delivery
- **Endpoint URL**: `https://<your-service>.onrender.com/api/v1/payments/webhook` (also supports `/billing/webhook`)
- **Subscribed Events**: `payment.succeeded`, `subscription.active`, `subscription.cancelled`, `subscription.renewed`
- **Secret**: Assign the generated webhook secret to `DODO_PAYMENTS_WEBHOOK_KEY`.

### Step 3: Test Card Credentials (Test Mode)
- **Card Number**: `4242 4242 4242 4242`
- **Expiry**: `12/28` | **CVC**: `123` | **ZIP**: `90210`

> [!TIP]
> **Live Deployment Note**: If Dodo Payments hosted checkout or customer portal does not trigger on the live deployed URL (e.g., due to cloud sandbox environment/CORS restrictions), please test Dodo Payments locally via `uvicorn reco.api.app:app` (see [Quickstart & Local Setup Guide](#15-quickstart--local-setup-guide)) or use the built-in **"⚡ 1-Click Instant Payment (Auto-Fill & Activate Pro)"** button in the billing modal.


---

## 14. Production Deployment & Operations Guide

Reco deploys cleanly as a single unified Web Service where FastAPI serves both backend API endpoints and the pre-built React/Vite SPA from `frontend/dist`.

### Build and Launch Configuration
- **Runtime**: Python 3.11+ (with Node.js 18+ and npm available during the build phase)
- **Build Command**:
  ```bash
  npm install --prefix frontend && npm run build --prefix frontend && pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn reco.api.app:app --host 0.0.0.0 --port $PORT
  ```

### Step-by-Step Cloud Deployment
1. Connect your repository (`toufiqfarhan0/reco`) in your cloud provider console (e.g. Render, Railway, Fly.io, AWS, DigitalOcean).
2. Configure the service type as a **Web Service** with the Python runtime.
3. Set the build command:
   `npm install --prefix frontend && npm run build --prefix frontend && pip install -r requirements.txt`
4. Set the start command:
   `uvicorn reco.api.app:app --host 0.0.0.0 --port $PORT`
5. Configure the production environment variables:
   - `PYTHON_VERSION`: `3.11.4`
   - `DODO_PAYMENTS_ENVIRONMENT`: `test_mode` (or `live_mode`)
   - `DODO_PAYMENTS_PRODUCT_ID`: `pdt_0Nmvzbo4wJETkRyCMAEPt`
   - `DODO_PAYMENTS_API_KEY`: *(your Dodo API key)*
   - `DODO_PAYMENTS_WEBHOOK_KEY`: *(your Dodo webhook secret)*
   - `SUPABASE_URL`: *(your Supabase project URL)*
   - `SUPABASE_ANON_KEY`: *(your Supabase anon key)*
   - `SUPABASE_SERVICE_ROLE_KEY`: *(your Supabase service role key)*
   - `SUPABASE_JWT_SECRET`: *(your Supabase JWT secret)*
   - `TENSORMUX_API_KEY`: *(your TensorMux key)*
   - `TENSORMUX_BASE_URL`: `https://api.tensormux.com/v1`
   - `TENSORMUX_MODEL`: `glm-4-7-flash`
   - `NEATLOGS_API_KEY`: *(your Neatlogs key)*
   - `NEATLOGS_BASE_URL`: `https://ingest.neatlogs.com`
6. Deploy the service. The build step compiles the Vite SPA into `frontend/dist/` and installs dependencies. The runtime then serves both the API and the SPA from a single port.

### Unified Routing & Architecture Guarantees
- **SPA Mounting**: `GET /` serves `frontend/dist/index.html`.
- **SPA Fallback Routing**: Unmatched non-API routes automatically fall back to `index.html` for client-side navigation.
- **API Isolation**: All API endpoints (`/api/*`, `/billing/*`, `/experiments/*`, `/auth/*`, `/tools/*`, etc.) return structured JSON and proper HTTP status codes (e.g., 404 JSON for missing records, never leaking HTML into API calls).
- **Public Config**: `GET /api/config` safely bootstraps frontend authentication and monetization without leaking server secrets.
- **Health Probes**: `GET /health` and `GET /api/health` respond with HTTP 200 `{"status": "ok"}` for container orchestrator health checks.

---

## 15. Quickstart & Local Setup Guide

Follow these exact steps to clone, configure, and run Reco locally in under 3 minutes:

### Step 1: Clone the Repository
```bash
git clone https://github.com/toufiqfarhan0/reco.git
cd reco
```

### Step 2: Configure Environment Variables
Copy the template to `.env`:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `Copy-Item .env.example .env`)*

Open `.env` and configure your credentials. **Reco boots completely offline with mock providers if keys are omitted**, but configuring them activates live production features:

```env
# 1. System Integration Flags
BILLING_ENABLED=true
OBSERVABILITY_ENABLED=true

# 2. TensorMux (Live LLM Inference via GLM-4.7-Flash)
TENSORMUX_API_KEY=tmx_your_key_here
TENSORMUX_BASE_URL=https://api.tensormux.com/v1
TENSORMUX_MODEL=glm-4-7-flash

# 3. Neatlogs (Distributed Execution Tracing & Observability)
NEATLOGS_API_KEY=your_neatlogs_api_key_here
NEATLOGS_BASE_URL=https://ingest.neatlogs.com

# 4. Supabase (Cloud Persistence & GoTrue Authentication)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_public_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
SUPABASE_JWT_SECRET=your_jwt_secret_here

# 5. Dodo Payments (Monetization & Customer Portal in Test Mode)
DODO_PAYMENTS_API_KEY=your_dodo_api_key_here
DODO_PAYMENTS_ENVIRONMENT=test_mode
DODO_PAYMENTS_PRODUCT_ID=pdt_0Nmvzbo4wJETkRyCMAEPt
DODO_PAYMENTS_WEBHOOK_KEY=whsec_your_webhook_signing_secret_here
```

### Step 3: Set Up Python Virtual Environment & Backend
```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify backend test suite (571 passed, 1 skipped)
python -m pytest tests/ -q
```

### Step 4: Set Up Frontend
```bash
# 1. Install Node dependencies
npm install --prefix frontend

# 2. Verify frontend test suite (51 passed across 13 test files)
npm test --prefix frontend

# 3. Build production Vite bundle
npm run build --prefix frontend
```

### Step 5: Start the Application

You can run Reco in either **Unified Mode** (single port) or **Dual Dev Mode** (hot-reload):

#### Option A: Unified Production Server (Recommended)
FastAPI serves both the REST API and the compiled Vite SPA from a single port:
```bash
uvicorn reco.api.app:app --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Interactive Swagger docs are available at `http://127.0.0.1:8000/docs`.

#### Option B: Dual Development Server (Frontend Hot-Reload)
In terminal 1 (Backend):
```bash
uvicorn reco.api.app:app --host 127.0.0.1 --port 8000 --reload
```
In terminal 2 (Frontend):
```bash
npm run dev --prefix frontend
```
Open [http://localhost:5173](http://localhost:5173) in your browser.


---

## 16. Project Structure

```text
reco/
├── reco/                        # Core autonomous agent engineering engine
│   ├── api/                     # FastAPI REST API, schemas, and payment routes
│   │   └── app.py               # Unified 1,146+ line API with dual aliases & SPA static mount
│   ├── benchmarks/              # Multi-domain suites (Reconciliation, Anomaly, Research)
│   ├── billing/                 # Dodo Payments service, entitlements & HMAC webhooks
│   ├── core/                    # GoalAnalyzer, TaskSpecification, domain interfaces
│   ├── db/                      # Supabase PostgreSQL adapter & InMemory fallback
│   ├── diagnostics/             # FailureAnalyzer & 12-category diagnostic taxonomy
│   ├── engine/                  # ArchitectureGenerator & AgentGraphRuntime (DAG engine)
│   ├── evaluators/              # Multi-dimensional Scorecard & PromotionAssessment
│   ├── llm/                     # TensorMux gateway & structured tool-calling adapter
│   ├── mutation/                # MutationEngine & multi-candidate hypothesis generators
│   ├── observability/           # Neatlogs hierarchical distributed tracing
│   └── tools/                   # Generic ToolRegistry & domain-specific tool packs
├── frontend/                    # Vite + React 19 + TypeScript visual console
│   ├── src/components/          # UI components (DAG visualizer, Modals, TasteSkill UI)
│   ├── src/services/            # API client layer
│   ├── src/lib/                 # Data types, domain presets, tool schemas
│   └── dist/                    # Compiled production SPA bundle
├── supabase/
│   └── migrations/              # PostgreSQL schemas (001 initial, 002 billing)
├── tests/                       # Deterministic pytest suite (571 tests)
├── docs/                        # Deep technical specifications & architectural references
├── scratch/                     # Canonical evidence artifacts & experiment provenance
├── scripts/                     # Standalone verification and experiment scripts
├── requirements.txt             # Python dependencies
└── README.md                    # System documentation
```

---

## 17. 🚧 Real-World Product Polish: Prototype Gaps & Future Roadmap

> [!NOTE]
> **Honest Architecture Disclosure for Reviewers & Judges**:  
> Reco was developed under rapid hackathon execution as a functional, verified autonomous agent engineering system. While our core algorithmic engine—acyclic DAG synthesis, epistemic failure postmortems, Pareto mutation pools, held-out validation gates, and sponsor pipelines (TensorMux, Neatlogs, Supabase, Dodo)—is hardened with **571 passing tests**, Reco is currently a **hardened hackathon prototype**. 
>
> Below is our transparent assessment of **current prototype gaps** and our roadmap to turn Reco into a polished, enterprise-ready commercial SaaS.

### 📊 Prototype Gaps vs. Production SaaS Matrix

| Platform Dimension | Current Hackathon Prototype | Planned Real-Product Architecture | Status / Priority |
|---|---|---|:---:|
| **Authentication & RBAC** | Lightweight Supabase GoTrue Auth with Email/Password + instant **1-Click Judge Demo Login** for effortless review. | Enterprise SSO (Google Workspace, Okta, SAML, GitHub OAuth), organization multi-tenancy, multi-seat workspaces, and strict RBAC (`Admin`, `ML Engineer`, `Auditor`). | 🟡 Near-Term |
| **Cloud Observability (Neatlogs)** | Non-blocking OpenTelemetry traces exported to `https://ingest.neatlogs.com` with **32-hex trace deep-links** and **4-axis scorecard tags** (`eval.*`). | In-console embedded flamegraph IFrames, automated Slack/Discord/PagerDuty alerts on `eval.decision == "REJECT"`, and historical latency/cost drift curves. | 🟢 Integrated (Expanding) |
| **Agent Deployment & Export** | Generates verified, immutable JSON DAG topologies and execution logs persisted in Supabase PostgreSQL. | **1-Click Production Deploy**: Auto-packaging promoted DAG agents into Docker containers, Kubernetes Helm charts, serverless Modal endpoints, or native **MCP (Model Context Protocol)** servers. | 🟡 Near-Term |
| **Self-Serve Benchmark Ingestion** | 3 pre-built domain suites (Financial Reconciliation, Anomaly Detection, Research Comparison) with synthetic test cases. | Drag-and-drop CSV/Parquet/JSONL dataset uploaders with automated synthetic test-case generation, boundary condition fuzzer, and split partitioning. | 🟡 Near-Term |
| **Human-in-the-Loop Review** | Automated Pareto promotion gate marks edge-case tradeoffs as `REVIEW`. | Dedicated interactive triage dashboard where engineers inspect node-level visual diffs, adjust verifier tolerances, and manually override promotion gates. | 🔵 Mid-Term |
| **Usage Metering & Billing** | Dodo Payments Pro tier subscription ($29/mo) with customer portal and HMAC webhook processing. | Hybrid subscription + **metered usage billing** via Dodo Payments meters, charging per evolution generation cycle and per 100k inference tokens consumed. | 🔵 Mid-Term |
| **Tool Ecosystem Discovery** | Curated domain tool catalogs with strict JSON Schema typing and argument coercion. | Dynamic third-party tool ingestion via OpenAPI/Swagger specs and native Model Context Protocol (MCP) server integration. | 🔵 Mid-Term |

### 🛠️ In-Depth Product Polish Roadmap

#### 1. Real-World Authentication, Organization Workspaces & Team RBAC
- **Current State**: We implemented Supabase Auth with an instant 1-Click Judge login so evaluators can test cloud persistence without entering credit cards or passwords.
- **Enterprise Product Goal**: 
  - Organization-level multi-tenancy (`org_id`) allowing enterprise teams to share agent blueprints, benchmark suites, and epistemic memory invariants.
  - Granular permissions: *Viewer* (read scorecards and flamegraphs), *Engineer* (run optimizations and tweak prompts), and *Admin* (manage billing, API keys, and production deployments).
  - Native audit logs tracking every human prompt edit or manual promotion override for SOC2 / ISO-27001 compliance.

#### 2. Deepening Neatlogs Cloud Observability
- **Current State**: Full 5-tier hierarchical tracing with direct deep-links (`https://app.neatlogs.com/traces/<trace_id>`) and 4-axis scorecard attributes (`eval.accuracy`, `eval.reliability`, `eval.cost_usd`, `eval.latency_ms`, `eval.decision`, `reco.pareto_dominant`).
- **Enterprise Product Goal**:
  - Direct embedding of live Neatlogs flamegraph canvas directly inside the Stage 05 (VALIDATE) console via secure iframe tokens.
  - Automated webhook alerts sent to engineering channels (Slack, Discord, PagerDuty) whenever a candidate agent triggers an `UNEXPECTED_REGRESSION` on held-out test splits.
  - Longitudinal regression analysis tracking how agent accuracy, token costs, and tool invocation latencies evolve across weeks of production runs.

#### 3. 1-Click Agent Compilation to Microservices & MCP Servers
- **Current State**: Reco compiles and saves optimal DAG definitions to Supabase and outputs runtime execution specifications.
- **Enterprise Product Goal**:
  - **Docker & Container Export**: One-click download of a production-ready `Dockerfile` and FastAPI runner pre-packaged with the winning agent's prompts, tool bindings, and verifier nodes.
  - **Serverless Hosting**: Direct one-click deployment to Modal, AWS Lambda, or Fly.io with auto-generated API tokens.
  - **MCP Server Packaging**: Exporting the promoted agent as a standard Model Context Protocol (MCP) server so external tools (Cursor, Claude Desktop, Antigravity) can call the synthesized agent as a specialized tool.

#### 4. Known Architectural Limitations
1. **Domain Boundedness**: Reco currently includes verified benchmark suites for three domains (Reconciliation, Anomaly Detection, Research Comparison). Universal zero-shot generalization across completely unmodeled domains requires providing corresponding tools and benchmark cases.
2. **LLM Non-Determinism**: Real LLM provider responses can exhibit subtle variance across runs; Reco combats this via strict tool argument typing, bounded retries, and air-gapped held-out validation gating.
3. **Tradeoffs in Evolutionary Optimization**: When mutation candidates improve cost or latency but induce slight boundary regressions, Reco conservatively issues a `REVIEW` status rather than blindly promoting the candidate.
4. **Cloud Persistence Dependency**: Supabase and Dodo features require network connectivity; when offline, Reco automatically falls back to local in-memory repositories.

### 🔮 The Future of Reco: The Autonomous Agent Compiler Vision

Beyond the immediate hackathon scope, Reco is designed to fundamentally redefine how software engineering teams build, deploy, and maintain AI agents at scale. Our long-term technical vision encompasses:

#### 1. Continuous Agent Compilation in CI/CD (Self-Healing Pull Requests)
- **Zero-Touch Maintenance**: Today, when an API changes its response payload or introduces new rate limits, downstream LLM agents break silently.
- **Automated Repair Workflows**: Reco will operate natively inside GitHub Actions and GitLab CI. On every schema migration or dependency upgrade, Reco automatically executes an evolutionary run against regression benchmarks. If a failure cluster is detected, Reco synthesizes the updated prompt boundaries and tool arguments, runs held-out validation, and **automatically opens a verified Pull Request** with before/after Pareto scorecards.

#### 2. Decentralized & Federated Epistemic Memory Network
- **Cross-Organization Failure Knowledge**: Across the industry, hundreds of engineering teams waste thousands of hours resolving the exact same agent edge cases (e.g. currency conversion float drift, ISO-8601 UTC string formats, integer ID casting).
- **Privacy-Preserving Proofs**: Reco’s future memory layer will allow participating organizations to publish and subscribe to a **Federated Epistemic Memory Ledger**. When an invariant is codified at Company A, a cryptographically signed mathematical rule is shared across the network—protecting Company B from the same failure mode with zero exposure of proprietary prompts, data, or company internals.

#### 3. SLM Distillation & Hardware-Accelerated Local Execution
- **From Frontier Models to Edge Distillation**: While large frontier models (e.g. GLM-4.7-Flash) are ideal for exploratory architecture synthesis and postmortems, executing large models at runtime incurs cost and latency.
- **Automated Fine-Tuning Pipeline**: Once an agent DAG reaches Pareto dominance ($V_2$), Reco will automatically collect execution traces and distill individual node roles into compact, specialized Small Language Models (1B–8B parameters) running locally via vLLM or llama.cpp. This cuts operational cost by **95%+** while dropping latency to sub-100ms.

#### 4. Bi-Directional Model Context Protocol (MCP) Ecosystem
- **Instant Tool Dynamic Discovery**: Full dynamic ingestion of remote MCP servers, allowing Reco agents to bind to arbitrary enterprise databases, Slack workspaces, Figma canvases, and developer tools on the fly.
- **Exporting Promoted Agents as MCP Tools**: Promoted compound AI agents will be packaged directly as self-contained MCP servers. Any external agent (Claude Desktop, Cursor IDE, Antigravity, or custom multi-agent swarms) can immediately consume the compiled Reco agent as a trusted, self-healing sub-agent.

#### 5. Universal Adversarial Benchmark Fuzzing (LLM-as-a-Fuzzer)
- **Automated Red-Teaming**: Instead of relying solely on human-curated benchmarks, Reco will deploy adversarial "fuzzer agents" trained to discover blind spots in candidate architectures—generating edge cases with extreme numerical values, noisy OCR inputs, corrupt timestamps, and contradictory context to guarantee unshakeable production reliability.

---

## 18. Hackathon Submission Details (Syndicate by Maximor)

- **Hackathon**: [Syndicate by Maximor](https://syndicate-by-maximor.devpost.com/) — Global Autonomous Agent Hackathon ($10,000 Prize Pool)
- **Host**: [AO (Agent Orchestrator)](https://aoagents.dev/)
- **Track**: **Track 1 — Automated Agent Engineering**
- **Submission Portal**: [Devpost](https://syndicate-by-maximor.devpost.com/)
- **Live Deployed App**: [https://reco-b1ac.onrender.com/](https://reco-b1ac.onrender.com/)
- **Product Demo Video (YouTube)**: [https://youtu.be/4uHXeUosulU](https://youtu.be/4uHXeUosulU)
- **Product Demo Video (Google Drive Mirror)**: [https://drive.google.com/file/d/1kT5qXcMSpcBgRPA4fvbTp4D6s-INSNcj/view?usp=drive_link](https://drive.google.com/file/d/1kT5qXcMSpcBgRPA4fvbTp4D6s-INSNcj/view?usp=drive_link)
- **GitHub Repository**: [https://github.com/toufiqfarhan0/reco](https://github.com/toufiqfarhan0/reco)
- **Syndicate Participant Pass**: [https://aoagents.dev/hackathons/syndicate/pass/](https://aoagents.dev/hackathons/syndicate/pass/)
- **Official Discord**: [https://discord.gg/Sy3EwRBQX3](https://discord.gg/Sy3EwRBQX3)
- **Built With AO**: 100% orchestrated via `ao` worktrees and the `agy` CLI across 30 milestone sessions with branch isolation and 571 tests with zero regressions
- **Cash Prize Partner**: [Maximor](https://maximor.ai/) ($3,000 USD Cash)
- **Credits & Monetization Partner**: [Dodo Payments](https://dodopayments.com/) ($3,000 Credits, Reco Pro tier `pdt_0Nmvzbo4wJETkRyCMAEPt`)
- **GPU / Voice Credits Partner**: [AI Grants India](https://aigrants.in/) ($4,000 Credits)
- **Inference Partner**: [TensorMux](https://tensormux.com/) (GLM-4.7-Flash with native reasoning token capture)
- **Venue & Observability Partner**: [Neatlogs](https://neatlogs.com/) (Distributed OTel Execution Tracing & Flamegraphs)
- **Persistence Partner**: [Supabase](https://supabase.com/) (PostgreSQL Cloud Ledger & GoTrue Row-Level Security)


---

## 19. License

This project is licensed under the MIT License.
