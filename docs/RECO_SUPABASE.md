# Reco — Supabase Authentication & Cloud Persistence Architecture (Step 26)

## 1. Executive Summary

This document details the integration of **Supabase** into **Reco** (Track 1 — Automated Agent Engineering) as an external persistence and authentication provider. 

Core invariants preserved:
- **Core Decoupling**: Core engineering components (`GoalAnalyzer`, `ArchitectureGenerator`, `AgentGraphRuntime`, `Benchmark`, `FailureAnalyzer`, `MutationEngine`, `OptimizationController`, `PromotionAssessment`) remain completely independent of Supabase.
- **Persistence Boundary**: Supabase calls exist solely in external persistence adapters (`reco/db/supabase_adapter.py`, `frontend/src/lib/supabase/`, and API route handlers). No database calls are injected inside benchmark evaluation or LLM scoring logic.
- **Strict Row-Level Security (RLS)**: User data is isolated at the database level. User identity is derived strictly from verified Supabase JWT Bearer tokens; client-supplied `user_id` inputs are never trusted.
- **Failure Containment**: Database timeouts, connectivity issues, or schema errors never crash agent execution. The user interface clearly communicates when persistence is temporarily unavailable.
- **Demo / Live Separation**: Demo Mode plays static, verified benchmark artifacts offline without database writes. Live Authenticated Mode executes real optimizations with cloud persistence.

---

## 2. Relational Schema & Table Verification

The Supabase project schema was inspected directly against live database tables (`https://lcdubsopwtwwtifjxfcu.supabase.co`). All eight target tables exist with the following verified layouts:

```
┌────────────────────────────────────────────────────────┐
│                        profiles                        │
│ id (uuid PK), display_name (text), created_at, updated_at│
└──────────────────────────┬─────────────────────────────┘
                           │ 1:N
                           ▼
┌────────────────────────────────────────────────────────┐
│                      experiments                       │
│ id (uuid PK), user_id (uuid FK), name, goal, domain,   │
│ status, active_version_id (uuid), created_at, updated_at│
└───────┬──────────────────────────────────┬─────────────┘
        │ 1:N                              │ 1:N
        ▼                                  ▼
┌────────────────────────────────┐ ┌────────────────────────────────┐
│         agent_versions         │ │       optimization_runs        │
│ id, experiment_id, version_num,│ │ id, experiment_id, status,     │
│ version_label, parent_version_id│ │ cost_type, total_cost, tokens, │
│ architecture (JSONB), status,  │ │ latency_ms, model/tool calls,  │
│ fingerprint, mutation_type     │ │ result (JSONB), created_at     │
└───────┬────────────────────────┘ └───────┬────────────────────────┘
        │                                  │
        ├─────────────────┬────────────────┤
        ▼                 ▼                ▼
┌────────────────┐ ┌───────────────┐ ┌───────────────────────────┐
│ candidate_evals│ │   diagnoses   │ │   promotion_assessments   │
│ candidate_id,  │ │ category,     │ │ parent_version_id,        │
│ name, score,   │ │ severity,     │ │ candidate_version_id,     │
│ fingerprint,   │ │ root_cause,   │ │ decision (PROMOTE/REVIEW),│
│ status, reason │ │ evidence, mut │ │ held_out_scorecard (JSONB)│
└────────────────┘ └───────────────┘ └───────────────────────────┘
                                           │
                                           ▼
                                   ┌────────────────┐
                                   │trace_references│
                                   │ trace_id, url, │
                                   │ span_count, ms │
                                   └────────────────┘
```

### Table Column Details
1. **`profiles`**: `id` (UUID references `auth.users`), `display_name` (text), `created_at`, `updated_at`.
2. **`experiments`**: `id` (UUID), `user_id` (UUID), `name` (text), `goal` (text), `domain` (text), `status` (text), `active_version_id` (UUID), `created_at`, `updated_at`.
3. **`agent_versions`**: `id` (UUID), `experiment_id` (UUID), `version_number` (int), `version_label` (text), `parent_version_id` (UUID), `architecture` (JSONB), `fingerprint` (text), `mutation_type` (text), `status` (text), `created_at`.
4. **`optimization_runs`**: `id` (UUID), `experiment_id` (UUID), `status` (text), `cost_type` (text), `total_cost` (numeric), `total_latency_ms` (int), `total_tokens` (int), `total_model_calls` (int), `total_tool_calls` (int), `result` (JSONB), `started_at`, `completed_at`, `created_at`.
5. **`candidate_evaluations`**: `id` (UUID), `optimization_run_id` (UUID), `parent_version_id` (UUID), `candidate_id` (text), `candidate_name` (text), `generation` (int), `mutation_type` (text), `target_node` (text), `fingerprint` (text), `scorecard` (JSONB), `status` (text), `rejection_reason` (text), `created_at`.
6. **`diagnoses`**: `id` (UUID), `experiment_id` (UUID), `optimization_run_id` (UUID), `agent_version_id` (UUID), `generation` (int), `category` (text), `severity` (text), `root_cause` (text), `evidence` (JSONB), `recommended_mutation` (text), `created_at`.
7. **`promotion_assessments`**: `id` (UUID), `experiment_id` (UUID), `optimization_run_id` (UUID), `parent_version_id` (UUID), `candidate_version_id` (UUID), `decision` (text), `reasons` (text[]), `held_out_scorecard` (JSONB), `created_at`.
8. **`trace_references`**: `id` (UUID), `experiment_id` (UUID), `optimization_run_id` (UUID), `trace_id` (text), `trace_url` (text), `span_count` (int), `latency_ms` (int), `created_at`.

---

## 3. Authentication Architecture

### Minimal Flow
- Email and password sign-up and sign-in.
- Supabase Auth manages sessions and issues signed JWTs.
- Automatic creation of user profile on sign-up in `profiles` table.
- Sign out removes local tokens and clears frontend session state.

### Client-Side Implementations
- **`frontend/src/lib/supabase/client.ts`**: Implements browser client using `@supabase/ssr` `createBrowserClient` with public publishable key.
- **`frontend/src/lib/supabase/server.ts`**: Implements server-side SSR client using Next.js cookie handling (`createServerClient`).
- **`frontend/src/components/AuthModal.tsx`**: Lightweight modal for sign-in and sign-up with feedback alerts and automatic modal dismissal.
- **`frontend/src/components/Header.tsx`**: Shows user profile badge (`User` icon with truncated name), `My Experiments` trigger, and `Sign Out` button when authenticated, or `Sign In` when unauthenticated.

### Backend Verification
- **Token Verification**: In `reco/db/supabase_adapter.py`, `verify_auth_token(token)` uses `supabase.auth.get_user(token)` to validate the cryptographic signature and extract identity (`user_id`, `email`).
- **Route Protection**: `require_authenticated_user(request)` in `reco/api/app.py` extracts the Bearer token from the `Authorization` header, verifies the session, and aborts with `HTTP 401 Unauthorized` if invalid or missing.
- **Spoofing Prevention**: Client-supplied `user_id` fields are never accepted in route parameters or request bodies; identity is exclusively derived from the verified token.

---

## 4. Persistence Architecture

### Decoupled Adapter Pattern
The `SupabasePersistenceService` in `reco/db/supabase_adapter.py` sits completely outside the core optimization engine. During an optimization job (`reco/api/app.py`):
1. The optimization controller runs to completion (`OptimizationResult`).
2. If the user provided a valid auth token, the adapter formats the canonical output and writes to Supabase.
3. If Supabase persistence encounters a network error, timeout, or RLS block, the failure is caught, logged with warning diagnostics, and the optimization job result remains intact in memory.

### Persistence Layers
1. **Experiment**: Writes `id`, `user_id`, `name`, `goal`, `domain`, `status`.
2. **Agent Versions**:
   - V0 baseline architecture (JSONB nodes, prompts, tool definitions).
   - V1 evolved architecture with mutation type and lineage link (`parent_version_id`).
   - Secret scrubbing: No API keys, passwords, or credentials are saved in architectures.
3. **Optimization Runs**:
   - Records generation count, total model calls, tool calls, tokens, latency, cost, and `cost_type` (`actual` / `estimated` / `simulated_mock`).
   - Full `result` JSONB storing the complete structured payload to guarantee zero-data-loss across complex graphs and candidates.
4. **Sub-Entities (Safe Best-Effort)**:
   - Evaluated candidates saved to `candidate_evaluations`.
   - Diagnoses saved to `diagnoses`.
   - Promotion assessments saved to `promotion_assessments`.
   - Neatlogs trace references saved to `trace_references` with URL, span count, and latency (no internal chain-of-thought or raw secrets).

---

## 5. Row-Level Security (RLS) & User Isolation

Row-level security policies are enforced directly in PostgreSQL:
- **Experiments Policy**: Users can only `SELECT`, `INSERT`, `UPDATE`, and `DELETE` rows where `auth.uid() = user_id`.
- **Cross-User Verification**:
  - User A creates an experiment.
  - User B authenticated query `SELECT * FROM experiments WHERE id = exp_a_id` returns zero rows (`[]`).
  - User B attempting to update or delete User A's experiment affects 0 rows.
  - Unauthenticated queries return zero rows.
- **Service Role Prohibition**: The frontend never receives or uses the `service_role` key. All browser and client requests utilize the publishable key and the user's JWT.

---

## 6. Frontend Experiment History & Reload

- **"My Experiments" Modal** (`frontend/src/components/MyExperimentsModal.tsx`):
  - Lists all persisted experiments owned by the logged-in user.
  - Displays name, domain badge, goal, creation date, and status.
  - Clicking an experiment fetches full details (`GET /experiments/{id}`).
  - Directly populates dashboard state: multi-axis scorecards (V0 vs V1), agent architecture DAG, failure diagnoses, mutation diffs, candidate pool, held-out validation gate, and Neatlogs trace card.
- **Browser Refresh**: After page reload, user signs in or restores session; previous experiments remain intact in the database and can be loaded immediately.

---

## 7. Migration Strategy & SQLite / In-Memory Decision

**Decision**: SQLite / In-Memory persistence remains active as:
1. **Deterministic Test Backend**: All core optimization and benchmark tests use fast in-memory stores, ensuring offline capability, zero latency, and zero dependency on external network services.
2. **Local Development Fallback**: When developers work offline without Supabase credentials, Reco defaults to in-memory repositories seamlessly.
3. **Production Cloud Persistence**: Supabase is the primary persistence backend for production deployments.

---

## 8. Environment Variables

### Frontend (`frontend/.env.example`)
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_your_key_here
```

### Backend (`.env`)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=sb_publishable_your_key_here
```
*Note: Reco supports both `SUPABASE_URL`/`SUPABASE_KEY` and `NEXT_PUBLIC_SUPABASE_URL`/`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.*
