# Reco — User-Facing End-to-End Product (Step 18)

## 1. Product Identity & Philosophy

**Product Name:** RECO  
**Tagline:** "Reco automatically engineers agents for the tasks you give it."  
**Track:** Automated Agent Engineering (Track 1)  

Reco is fundamentally distinct from typical conversational AI and chatbot platforms:
- **Non-Chat Interface:** The primary interaction model is not conversational back-and-forth, but rather an engineering lifecycle:
  $$\text{DESCRIBE GOAL} \longrightarrow \text{GENERATE AGENT} \longrightarrow \text{TEST AGENT} \longrightarrow \text{IMPROVE AGENT}$$
- **Authentic Evolution:** Reco takes a natural-language goal, inspects available tools from its central `ToolRegistry`, synthesizes a multi-node Directed Acyclic Graph (DAG), benchmarks the baseline $V_0$ agent, diagnoses failure clusters with clean symptom-versus-cause separation, mutates prompts and tools into candidate versions, validates against an air-gapped held-out split, and produces a formal promotion decision.

---

## 2. Frontend Architecture & Technology Stack

| Layer | Technology | Details |
|---|---|---|
| **Framework** | Next.js 16 (App Router) | High-performance React framework with server rendering and static prerendering. |
| **Language** | TypeScript 5 | Strict end-to-end typing across models, API responses, and component state. |
| **Styling** | Tailwind CSS v4 | Dark-first technical aesthetic (`bg-slate-950`), custom borders (`border-slate-800`), glowing status accents. |
| **Icons** | Lucide React | Minimalist technical icons (`Cpu`, `GitBranch`, `ShieldCheck`, `Activity`, `Award`, `DollarSign`, `Zap`). |
| **Test Suite** | Vitest + React Testing Library + JSDOM | 17 comprehensive unit and integration tests covering the complete product lifecycle. |
| **Backend** | FastAPI + Uvicorn | Existing Reco core engine (`reco/api/app.py`). |

---

## 3. Complete User Flow & Screen Architecture

### 1. Header & Provider Status Bar (`Header.tsx`)
- **Branding:** Displays product identity, version `v0.1.0`, and hackathon track (`Track 1`).
- **Active Model Pill:** Displays the current real-provider model `glm-4-7-flash` (no deprecated Gemma is selectable).
- **Telemetry Pill:** Real-time Neatlogs connection status.
- **Mode Switcher:**
  - **Demo Mode:** Instant, zero-cost access to the empirically verified Step 14 optimization run ($V_0 \to V_1$, $75\% \to 80\%$ accuracy, $-10.38\%$ cost, $-20.54\%$ latency, $82.5\%$ held-out watermark).
  - **Real Provider Mode:** Live model inference via TensorMux using `glm-4-7-flash`.

### 2. Goal Input & Experiment Launch (`GoalInputSection.tsx`)
- **Large Goal Input:** High-contrast input area answering *"What do you want an agent to accomplish?"*
- **Generic Domain Presets:**
  1. *Financial Reconciliation (Benchmark Suite):* Reconcile bank statements against general ledger entries.
  2. *Dataset Anomaly Analysis (Generic Domain):* Analyze incoming transaction streams, detect statistical outliers, and explain variance clusters.
  3. *Technology Comparative Evaluation (Generic Domain):* Compare database technologies under empirical throughput and latency constraints.
- **Actions:**
  - `Engineer Agent`: Initiates goal analysis and asynchronous multi-generation evolution.
  - `Load Step 14 Benchmark`: Immediately loads the authentic historical Step 14 multi-generation run.
  - `Available Tools (N/Total)`: Opens the Central Tool Registry modal.

### 3. Central Tool Registry (`ToolCatalogModal.tsx`)
- Directly queries backend `GET /tools` backed by `default_tool_registry.list_schemas()`.
- **Zero Fake Tools:** Only authorized tools registered in the backend appear in the catalog.
- **Metadata Attributes:**
  - Tool machine name and description.
  - Category (`ingestion`, `reconciliation`, `analytics`).
  - Execution nature: `Deterministic Tool ($0/0ms)` vs `Model-Driven`.
  - Risk Level: `LOW`, `MEDIUM`, `HIGH`.
  - Side Effect status.
  - Parameter schema expander with required field badges.
- **Interactive Checkboxes:** Users can toggle which tools are made available to `ArchitectureGenerator`.

### 4. Agent Architecture DAG Visualizer (`ArchitectureGraphView.tsx`)
- Renders the synthesized `GraphDefinition` without requiring a graph database:
  - **Entry Node:** Distinctly highlighted (`parse_statement`).
  - **Node Execution Modes:**
    - `deterministic_tool` (Cyan badge, $0 cost, $<1\text{ms}$ execution).
    - `model_driven` (Amber badge, model-driven tool argument tuning).
    - `model_inference` (Purple badge, reasoning and verification).
  - **Directed Edges:** Visible dependency connections ($N_i \to N_j$).
  - **Interactive Node Inspector:** Displays system directives, authorized tool boundaries, and context mappings.
  - **Architecture Quality Score:** Computed metric (e.g., `92/100`) confirming acyclicity, bounded depth, and capability coverage.

### 5. Run Progress Screen (`RunProgressTracker.tsx`)
- Prevents long-running TensorMux calls from appearing frozen:
  - **Live Elapsed Timer:** Real-time execution duration tracking.
  - **Resource Counters:** Model call counter, tool call counter, generation index.
  - **Step Pipeline Indicators:**
    - `[✓] Goal Analyzed into Specification`
    - `[✓] Architecture DAG Synthesized`
    - `[✓] Baseline V0 Benchmarked on 12 Cases`
    - `[✓] Root Cause Failures Diagnosed`
    - `[✓] Targeted V1 Mutation Synthesized`
    - `[✓] Candidate V1 Benchmarked`
    - `[✓] Held-Out Gating (8 Isolated Cases)`
    - `[✓] Promotion Decision Assessed`
  - **Telemetry Stream Drawer:** Displays the live sequence of dispatched `OptimizationEvent`s.

### 6. Multi-Axis Scorecard (`ScorecardView.tsx`)
- Displays the backend's strongly-typed `Scorecard` across 4 fundamental axes:
  - **Accuracy ($\uparrow$):** $75.00\% \to 80.00\%$ ($+5.00\%$)
  - **Reliability ($\uparrow$):** $100.00\% \to 100.00\%$ ($0$ schema or invariant violations)
  - **Total Cost ($\downarrow$):** $\$0.071354 \to \$0.063950$ ($-10.38\%$ reduction)
  - **Avg Latency ($\downarrow$):** $51,583\text{ ms} \to 40,988\text{ ms}$ ($-20.54\%$ speedup)
- **Dominance Badge:** `STRICTLY_BETTER`
- **Policy Narrative:** Explanation synthesized by the backend's `ComparisonPolicy`.

### 7. Evolution Timeline (`EvolutionTimeline.tsx`)
- Visual progression of evolutionary lineage:
  $$V_0 \text{ (Baseline Established)} \longrightarrow V_1 \text{ (Promoted Winner)} \longrightarrow V_2 \text{ (Non-Destructive Exit)}$$
- Clickable cards allow inspecting each generation's scorecards, decision criteria, and candidate mutations.

### 8. Failure Explorer (`FailureExplorer.tsx`)
- Detail view for all failed cases diagnosed by `FailureAnalyzer`:
  - **Case Code:** e.g., `REC-OPT-08`.
  - **Taxonomy Category:** e.g., `HALLUCINATED_MATCH`.
  - **Severity:** `HIGH` / `MEDIUM` / `LOW`.
  - **Failed Node:** `fuzzy_match`.
  - **Root Cause:** Detailed explanation of why the failure occurred.
  - **Evidence:** Exact discrepancy evidence without exposing full ground truth.
  - **Confidence:** e.g., `90%`.
  - **Recommended Mutation:** e.g., `PROMPT_CHANGE`.

### 9. Mutation Inspector (`MutationInspector.tsx`)
- Inspects the exact architectural diff between parent and child versions:
  - Lineage: $V_0 \to V_1$.
  - Target Node: `fuzzy_match`.
  - Mutation Type: `PROMPT_CHANGE`.
  - Rationale: Enforces strict vendor token match before fuzzy similarity.
  - Before/After Directive Diff with clean syntax highlighting.

### 10. Held-Out Benchmark & Promotion Gate (`HeldOutValidationView.tsx`)
- **Strict Split Isolation Display:**
  - **Optimization Split (12 cases):** Open to failure diagnosis and evolutionary search.
  - **Held-Out Split (8 cases):** Strictly air-gapped until the promotion gate.
- **Leakage Protection Badge:** `AUDITED_ZERO_LEAKAGE`.
- **Validation Watermark:** Confirms $82.50\%$ accuracy maintained ($0.0\%$ regression), $-8.95\%$ cost reduction, and $-13.59\%$ latency speedup.
- **Promotion Decision:** Formal `PROMOTE` outcome with policy checklist.

### 11. Neatlogs Observability Integration (`NeatlogsTraceCard.tsx`)
- Displays execution trace ID and span count ($29$ spans recorded).
- Provides a direct link to the Neatlogs distributed trace view.
- Graceful offline fallback when Neatlogs is not active.

---

## 4. API Endpoints Used & Added

| Endpoint | Method | Source | Purpose |
|---|:---:|---|---|
| `/health` | GET | Existing | Checks backend readiness, active environment, and integration flags. |
| `/version` | GET | Existing | Returns version `0.1.0` and track `Automated Agent Engineering`. |
| `/analyze-goal` | POST | Existing | Synthesizes a natural language goal into a `TaskSpecification`. |
| `/generate-architecture` | POST | Existing | Synthesizes an agent DAG from a goal or task specification. |
| `/benchmark/reconciliation/run` | POST | Existing | Runs the 20-case reconciliation benchmark. |
| `/scorecard/compare` | POST | Existing | Compares two scorecards using multi-dimensional dominance. |
| `/analyze-failure` | POST | Existing | Diagnoses root cause failures from execution records. |
| `/optimize/run` | POST | Existing | Runs the multi-generation autonomous controller. |
| `/tools` | GET | **Added** | Returns schemas, risk levels, and deterministic flags from `ToolRegistry`. |
| `/agent/run` | POST | **Added** | Executes a synthesized graph against provided input payloads. |
| `/experiments/demo` | GET | **Added** | Serves the authentic Step 14 verified optimization dataset for instant demo exploration. |
| `/jobs/optimize` | POST | **Added** | Spawns an asynchronous multi-generation optimization job. |
| `/jobs/{job_id}` | GET | **Added** | Returns live progress, step state, elapsed time, events, and final result. |

---

## 5. Security & Secret Protection

- **Zero Client Bundle Exposure:** Neither `TENSORMUX_API_KEY`, `NEATLOGS_API_KEY`, `SUPABASE_KEY`, nor Dodo secrets are present in frontend bundles.
- **Zero API Secret Leakage:** Backend API endpoints omit sensitive keys from response payloads.
- **Air-Gapped Held-Out Data:** Ground truth of held-out benchmark cases is never transmitted over client APIs.

---

## 6. Verification Results

1. **Frontend Production Build (`npm run build`):**
   - Turbopack compilation: `✓ Compiled successfully`
   - TypeScript verification: `✓ Finished TypeScript in 2.9s with 0 errors`
   - Static page generation: `✓ Generating static pages (4/4)`
2. **Frontend Test Suite (`npm test` / `npx vitest run`):**
   - 17 tests passed out of 17 tests ($100\%$ pass rate in $2.04\text{s}$).
3. **Backend Test Suite (`python -m pytest tests/`):**
   - 438 passed, 1 skipped in $12.82\text{s}$ ($0$ regressions against previous baseline).
