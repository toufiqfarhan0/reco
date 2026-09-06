# AGY Prompt 07 — Next.js Dashboard & Visual Engineering Console

## AO Session Setup
```bash
# 1. Create GitHub Issue
# Title: feat: next.js frontend dashboard and interactive 5-stage engineering console

# 2. Spawn AO Session
ao session spawn --name "07-frontend-dashboard" --issue 7

# 3. Run with AGY CLI
agy --file docs/prompts/07_frontend_dashboard.md
```

---

## Objective
Build a rich, responsive Next.js web application for Reco. Provide an intuitive 5-stage visual navigator (`BUILD → RUN → UNDERSTAND → IMPROVE → VALIDATE`), multi-dimensional scorecards, interactive candidate comparisons, and full telemetry inspection.

## Context & Architecture
- System: **Reco** (Autonomous Agent Engineering System)
- Framework: Next.js 16 (Turbopack) with React 19, TypeScript, and Tailwind CSS
- Reference Docs:
  - [UI Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_UI.md)
  - [Scorecard Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_SCORECARD.md)
  - [Multi-Candidate Optimization](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_MULTI_CANDIDATE_OPTIMIZATION.md)

## Requirements to Implement

### 1. 5-Stage Engineering Navigator (`frontend/src/app/page.tsx`)
- Implement progressive workflow tabs:
  1. **Stage 1: BUILD** (`GoalInputSection.tsx`): Natural language goal input, domain preset chips, tool selection modal (`ToolCatalogModal.tsx`), and architecture synthesis triggers.
  2. **Stage 2: RUN** (`ScorecardView.tsx` & `RunProgressTracker.tsx`): Real-time DAG execution visualization and 4-axis scorecard display with delta ($\Delta$) badges.
  3. **Stage 3: UNDERSTAND** (`FailureExplorer.tsx`): Failure mode breakdown, symptom-vs-cause diagnostics, and error stack traces.
  4. **Stage 4: IMPROVE** (`CandidateComparisonView.tsx` & `MutationInspector.tsx`): Multi-candidate tournament (Candidate A, B, C), prompt diff viewer, and evolutionary lineage timeline (`EvolutionTimeline.tsx`).
  5. **Stage 5: VALIDATE** (`HeldOutValidationView.tsx`): Air-gapped held-out split evaluation, promotion decision banner (`PROMOTED` / `REQUIRES_REVIEW` / `REJECTED`), and Neatlogs trace card (`NeatlogsTraceCard.tsx`).

### 2. Header & Global State Controls (`Header.tsx`)
- Execution Mode Switcher: Seamlessly toggle between **Demo Mode** (instant canonical replay) and **Live Mode** (real-time API execution).
- Domain Selector: Switch between Financial Reconciliation, Anomaly Detection, and Research Comparison.
- Auth Modal (`AuthModal.tsx`): Supabase user login, session indicator, and experiment history modal (`MyExperimentsModal.tsx`).
- Billing Modal (`BillingModal.tsx`): Reco Pro upgrade flow and Dodo Payments integration.

### 3. Visual Styling & Polish
- Dark slate theme with cyan/indigo accent hierarchy.
- Responsive layouts (mobile $\to$ ultra-wide desktop).
- Micro-animations on metrics deltas, status badges, and graph node transitions.

## Verification & Acceptance Criteria
1. Frontend renders all 5 stages seamlessly and allows interactive user transitions.
2. Toggle between Demo Mode and Live Mode updates state cleanly without crashes.
3. Pass all Vitest component tests and build with zero TypeScript or packaging errors:
   ```bash
   npm test --prefix frontend
   npm run build --prefix frontend
   ```
