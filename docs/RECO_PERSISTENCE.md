# Reco Persistence Architecture & Supabase Schema

## 1. Persistence Overview

The Reco persistence layer is designed to support the core closed-loop autonomous agent engineering cycle:
$$\text{Goal} \longrightarrow \text{Architecture Synthesis} \longrightarrow \text{Execution} \longrightarrow \text{Evaluation} \longrightarrow \text{Diagnosis} \longrightarrow \text{Mutation} \longrightarrow \text{Regression} \longrightarrow \text{Promotion}$$

### Architecture Separation
- **Production Layer**: `reco/db/supabase.py` (Supabase PostgreSQL via Supabase Python SDK and PostgREST).
- **Test / Local Offline Layer**: `reco/db/memory.py` (Thread-safe, deterministic, in-memory repository implementation).
- **Abstraction Layer**: `reco/db/repositories.py` (Domain repository contracts).
- **Provider Factory**: `reco/db/session.py` (Dynamically yields `SupabaseDatabase` when credentials exist, otherwise falls back seamlessly to `InMemoryDatabase`).

---

## 2. Relational Schema Summary

The SQL migration is located at [`supabase/migrations/001_initial_schema.sql`](file:///c:/Users/toufi/Desktop/test-ao/supabase/migrations/001_initial_schema.sql).

```
   ┌──────────────────────────────────────────────────────────────┐
   │                         experiments                          │
   │  id, name, goal, domain, status, current_best_version_id     │
   └──────────────────────────────┬───────────────────────────────┘
                                  │ 1:N
                                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │                        agent_versions                        │
   │  id, experiment_id, version_number, architecture (JSONB),    │
   │  prompts, tools, memory_config, model_config, parent_version │
   └───────┬──────────────────────────────────────────────┬───────┘
           │ 1:N                                          │ 1:N
           ▼                                              ▼
┌─────────────────────────┐                   ┌─────────────────────────┐
│     benchmark_runs      │                   │      improvements       │
│  accuracy, reliability, │                   │  parent_id, candidate_id│
│  cost_usd, latency_ms   │                   │  diffs, accept/reject   │
└──────────┬──────────────┘                   └─────────────────────────┘
           │ 1:N
           ▼
┌─────────────────────────┐
│     case_executions     │ ◄─── benchmark_cases (id, code, split, data)
│  output, tokens, cost,  │
│  tool_events, success   │
└──────────┬──────────────┘
           │ 1:1
           ▼
┌─────────────────────────┐
│    failure_diagnoses    │
│  category, root_cause,  │
│  recommended_mutations  │
└─────────────────────────┘
```

### Core Invariants Enforced:
1. **Version Immutability**: Each `agent_versions` record is an immutable snapshot. Mutations create new version records.
2. **Version Uniqueness**: Composite unique constraint on `(experiment_id, version_number)`.
3. **Split Integrity**: Benchmark cases are strictly divided into `optimization` (for diagnosis/mutation) and `held_out` (for unbiased promotion gating).
4. **Lineage Auditing**: `improvements` tracks parent vs. candidate version metrics and promotion decisions.

---

## 3. Local Development & Testing

- **Zero-Dependency Startup**: When `SUPABASE_URL` and `SUPABASE_KEY` are unset, Reco automatically boots with the in-memory persistence provider.
- **Unit Testing**: Pytest uses isolated `InMemoryDatabase` instances per test, ensuring zero flakiness and zero internet/network requirements.
- **Connecting Supabase**: When deploying or connecting to a live Supabase project, execute `supabase/migrations/001_initial_schema.sql` via the Supabase SQL Editor or Supabase CLI, and set `SUPABASE_URL` and `SUPABASE_KEY` in `.env`.
