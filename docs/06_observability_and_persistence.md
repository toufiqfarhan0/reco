# AGY Prompt 06 — Neatlogs Distributed Tracing & Supabase Cloud Persistence

## AO Session Setup
```bash
# 1. Create GitHub Issue
# Title: feat: neatlogs distributed tracing and supabase postgresql persistence

# 2. Spawn AO Session
ao session spawn --name "06-observability-persistence" --issue 6

# 3. Run with AGY CLI
agy --file docs/prompts/06_observability_and_persistence.md
```

---

## Objective
Integrate production observability with **Neatlogs** for end-to-end distributed tracing across agent runs, and persist experiment lineage, scorecards, and user sessions in **Supabase PostgreSQL** with Row-Level Security (RLS).

## Context & Architecture
- System: **Reco** (Autonomous Agent Engineering System)
- Observability Partner: **Neatlogs** (`https://ingest.neatlogs.com`)
- Database Partner: **Supabase** (`https://your-project.supabase.co`)
- Reference Docs:
  - [Neatlogs Integration Guide](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_NEATLOGS.md)
  - [Supabase Persistence Guide](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_SUPABASE.md)
  - [Database Schemas](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_PERSISTENCE.md)

## Requirements to Implement

### 1. Neatlogs Distributed Tracer (`reco/observability/tracer.py`)
- Implement non-blocking, fault-tolerant telemetry exporter:
  - Generate hierarchical spans: `optimization_run` $\to$ `generation_N` $\to$ `candidate_eval` $\to$ `node_execution` $\to$ `tool_invocation`.
  - Capture span metadata: start/end timestamps, duration, status, model parameters, token usage, tool arguments, and outputs.
  - Safe fault containment: If Neatlogs ingest fails or times out, agent execution must proceed unaffected (zero disruption).
  - Provide direct deep-link URLs to inspect execution traces in the Neatlogs web interface (`https://app.neatlogs.com/traces/<trace_id>`).

### 2. Supabase PostgreSQL Persistence (`reco/db/supabase.py` & migrations)
- Execute schema migrations (`supabase/migrations/001_initial_schema.sql`):
  - Tables: `experiments`, `architectures`, `benchmark_runs`, `evaluations`, `mutations`, `traces`.
- Implement repository abstraction:
  - Store experiment configurations, task specifications, and lineage records.
  - Maintain historical immutability: past generation benchmarks and scorecards are never overwritten.
  - Support fallback to in-memory repository when running in local development mode without Supabase credentials.

### 3. User Authentication & Multi-Tenancy
- Support Supabase GoTrue JWT authentication (`Authorization: Bearer <token>`).
- Enforce user isolation: experiments and architectures belong to authenticated user IDs.

## Verification & Acceptance Criteria
1. Neatlogs tracer generates valid OpenTelemetry-compatible traces and logs spans without throwing uncaught exceptions.
2. Supabase client persists experiment lineage and recovers state without data loss.
3. System functions gracefully in in-memory mode when cloud persistence is unconfigured.
4. Pass all unit tests:
   ```bash
   python -m pytest tests/test_neatlogs.py tests/test_step26_supabase_persistence.py -v
   ```
