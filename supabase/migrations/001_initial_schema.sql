-- ============================================================================
-- Reco — Autonomous Agent Engineering System
-- Migration 001: Initial Persistence Schema
-- Target: PostgreSQL / Supabase
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ----------------------------------------------------------------------------
-- 1. EXPERIMENTS
-- High-level tuning/optimization session initiated for a specific goal.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    goal TEXT NOT NULL,
    domain VARCHAR(100) DEFAULT 'reconciliation',
    status VARCHAR(50) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'paused')),
    current_best_version_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 2. TOOLS
-- Declarative catalog of available python/domain tools.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    parameters_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 3. AGENT VERSIONS
-- Immutable snapshots of synthesized or mutated multi-agent graph architectures.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    version_number INT NOT NULL CHECK (version_number >= 0),
    architecture JSONB NOT NULL DEFAULT '{}'::jsonb,
    prompts JSONB NOT NULL DEFAULT '{}'::jsonb,
    tools JSONB NOT NULL DEFAULT '[]'::jsonb,
    memory_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    parent_version_id UUID REFERENCES agent_versions(id) ON DELETE SET NULL,
    mutation_summary TEXT,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'evaluated', 'promoted', 'rejected')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_experiment_version UNIQUE (experiment_id, version_number)
);

-- Add foreign key from experiments to agent_versions for current_best_version_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_experiments_current_best'
    ) THEN
        ALTER TABLE experiments
            ADD CONSTRAINT fk_experiments_current_best
            FOREIGN KEY (current_best_version_id)
            REFERENCES agent_versions(id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 4. BENCHMARK CASES
-- Canonical benchmark test scenarios partitioned by split.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benchmark_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    benchmark_name VARCHAR(100) NOT NULL DEFAULT 'reconciliation',
    case_code VARCHAR(100) UNIQUE NOT NULL,
    split VARCHAR(50) NOT NULL CHECK (split IN ('optimization', 'held_out')),
    difficulty VARCHAR(50) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
    input_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    ground_truth JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 5. BENCHMARK RUNS
-- Execution of an agent version across benchmark cases with aggregate metrics.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benchmark_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    agent_version_id UUID NOT NULL REFERENCES agent_versions(id) ON DELETE CASCADE,
    benchmark_name VARCHAR(100) NOT NULL DEFAULT 'reconciliation',
    split VARCHAR(50) NOT NULL CHECK (split IN ('optimization', 'held_out', 'full')),
    total_cases INT NOT NULL DEFAULT 0 CHECK (total_cases >= 0),
    passed_cases INT NOT NULL DEFAULT 0 CHECK (passed_cases >= 0),
    failed_cases INT NOT NULL DEFAULT 0 CHECK (failed_cases >= 0),
    accuracy NUMERIC(6, 4) NOT NULL DEFAULT 0.0 CHECK (accuracy >= 0.0 AND accuracy <= 1.0),
    reliability NUMERIC(6, 4) NOT NULL DEFAULT 0.0 CHECK (reliability >= 0.0 AND reliability <= 1.0),
    total_cost_usd NUMERIC(12, 6) NOT NULL DEFAULT 0.0,
    latency_ms INT NOT NULL DEFAULT 0,
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('running', 'completed', 'failed')),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ----------------------------------------------------------------------------
-- 6. CASE EXECUTIONS
-- Individual case-level outputs, token usage, tool events, and execution trace.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS case_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    benchmark_run_id UUID NOT NULL REFERENCES benchmark_runs(id) ON DELETE CASCADE,
    benchmark_case_id UUID NOT NULL REFERENCES benchmark_cases(id) ON DELETE CASCADE,
    agent_version_id UUID NOT NULL REFERENCES agent_versions(id) ON DELETE CASCADE,
    output JSONB NOT NULL DEFAULT '{}'::jsonb,
    expected JSONB DEFAULT '{}'::jsonb,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    accuracy_score NUMERIC(6, 4) DEFAULT 0.0,
    latency_ms INT NOT NULL DEFAULT 0,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    cost_usd NUMERIC(12, 6) DEFAULT 0.0,
    tool_events JSONB DEFAULT '[]'::jsonb,
    trace_id VARCHAR(255),
    error JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 7. FAILURE DIAGNOSES
-- Structured root-cause diagnoses of failed case executions.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS failure_diagnoses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_execution_id UUID NOT NULL REFERENCES case_executions(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    severity VARCHAR(50) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    root_cause TEXT NOT NULL,
    evidence JSONB DEFAULT '{}'::jsonb,
    recommended_mutations JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 8. IMPROVEMENTS
-- Lineage records tracking candidate mutations, metrics deltas, and promotions.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS improvements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    parent_version_id UUID REFERENCES agent_versions(id) ON DELETE SET NULL,
    candidate_version_id UUID NOT NULL REFERENCES agent_versions(id) ON DELETE CASCADE,
    mutation_type VARCHAR(100) NOT NULL,
    mutation_description TEXT NOT NULL,
    rationale TEXT NOT NULL,
    metrics_before JSONB DEFAULT '{}'::jsonb,
    metrics_after JSONB DEFAULT '{}'::jsonb,
    accepted BOOLEAN NOT NULL DEFAULT FALSE,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- INDEXES FOR QUERY OPTIMIZATION
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_agent_versions_experiment ON agent_versions(experiment_id);
CREATE INDEX IF NOT EXISTS idx_agent_versions_lookup ON agent_versions(experiment_id, version_number);
CREATE INDEX IF NOT EXISTS idx_benchmark_cases_split ON benchmark_cases(benchmark_name, split);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_version ON benchmark_runs(agent_version_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_experiment ON benchmark_runs(experiment_id);
CREATE INDEX IF NOT EXISTS idx_case_executions_run ON case_executions(benchmark_run_id);
CREATE INDEX IF NOT EXISTS idx_case_executions_case ON case_executions(benchmark_case_id);
CREATE INDEX IF NOT EXISTS idx_failure_diagnoses_case_exec ON failure_diagnoses(case_execution_id);
CREATE INDEX IF NOT EXISTS idx_improvements_experiment ON improvements(experiment_id);
