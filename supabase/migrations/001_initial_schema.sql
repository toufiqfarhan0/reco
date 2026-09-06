-- ==============================================================================
-- RECO AUTONOMOUS AGENT SYSTEM - SUPABASE POSTGRESQL INITIAL SCHEMA (STEP 6)
-- Track 1: Automated Agent Engineering
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. EXPERIMENTS TABLE
-- Tracks top-level autonomous optimization sessions and goals.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    domain TEXT NOT NULL DEFAULT 'financial_reconciliation',
    status TEXT NOT NULL DEFAULT 'running',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 2. ARCHITECTURES TABLE
-- Persists immutable DAG architectures synthesized or mutated during an experiment.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS architectures (
    id TEXT PRIMARY KEY,
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    generation INT NOT NULL DEFAULT 0,
    definition JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 3. BENCHMARK RUNS TABLE
-- Maintains immutable empirical evaluation scorecards across benchmark splits.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benchmark_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    architecture_id TEXT NOT NULL REFERENCES architectures(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    split TEXT NOT NULL,
    total_cases INT NOT NULL DEFAULT 0,
    passed_cases INT NOT NULL DEFAULT 0,
    failed_cases INT NOT NULL DEFAULT 0,
    accuracy DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    reliability DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    latency_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    case_results JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 4. EVALUATIONS TABLE
-- Side-by-side Pareto comparisons between baseline and candidate variants.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    baseline_architecture_id TEXT NOT NULL REFERENCES architectures(id),
    candidate_architecture_id TEXT NOT NULL REFERENCES architectures(id),
    comparison JSONB NOT NULL,
    verdict TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 5. MUTATIONS TABLE
-- Records architectural mutations, diagnostics, and structured diffs across generations.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mutations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    parent_architecture_id TEXT NOT NULL REFERENCES architectures(id),
    child_architecture_id TEXT NOT NULL REFERENCES architectures(id),
    generation INT NOT NULL,
    mutator_name TEXT NOT NULL,
    diagnostic_category TEXT,
    mutation_diff JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 6. TRACES TABLE
-- Stores Neatlogs distributed tracing spans, token usage, and deep links.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS traces (
    id TEXT PRIMARY KEY,
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    architecture_id TEXT REFERENCES architectures(id),
    user_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'success',
    total_duration_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    total_tokens INT NOT NULL DEFAULT 0,
    total_cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    spans JSONB NOT NULL DEFAULT '[]'::jsonb,
    deep_link_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ------------------------------------------------------------------------------
-- 7. USER ENTITLEMENTS TABLE
-- Tracks user subscription tiers, Dodo Payments customer and subscription IDs.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_entitlements (
    user_id UUID PRIMARY KEY,
    tier TEXT NOT NULL DEFAULT 'free',
    status TEXT NOT NULL DEFAULT 'none',
    is_pro BOOLEAN NOT NULL DEFAULT false,
    customer_id TEXT,
    subscription_id TEXT,
    payment_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    expires_at TIMESTAMPTZ
);

-- ==============================================================================
-- INDEXES FOR QUERY OPTIMIZATION
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_experiments_user_id ON experiments(user_id);
CREATE INDEX IF NOT EXISTS idx_architectures_exp_id ON architectures(experiment_id);
CREATE INDEX IF NOT EXISTS idx_architectures_user_id ON architectures(user_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_arch_id ON benchmark_runs(architecture_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_exp_id ON benchmark_runs(experiment_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_user_id ON benchmark_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_exp_id ON evaluations(experiment_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_user_id ON evaluations(user_id);
CREATE INDEX IF NOT EXISTS idx_mutations_exp_id ON mutations(experiment_id);
CREATE INDEX IF NOT EXISTS idx_mutations_user_id ON mutations(user_id);
CREATE INDEX IF NOT EXISTS idx_traces_exp_id ON traces(experiment_id);
CREATE INDEX IF NOT EXISTS idx_traces_user_id ON traces(user_id);
CREATE INDEX IF NOT EXISTS idx_user_entitlements_customer_id ON user_entitlements(customer_id);

-- ==============================================================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- Enforce strict multi-tenant isolation so users only access their own data.
-- ==============================================================================
ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE architectures ENABLE ROW LEVEL SECURITY;
ALTER TABLE benchmark_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE mutations ENABLE ROW LEVEL SECURITY;
ALTER TABLE traces ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_entitlements ENABLE ROW LEVEL SECURITY;

-- 1. Experiments Policies (CRUD scoped to auth.uid())
CREATE POLICY "Users can view own experiments" ON experiments
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own experiments" ON experiments
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own experiments" ON experiments
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own experiments" ON experiments
    FOR DELETE USING (auth.uid() = user_id);

-- 2. Architectures Policies (Immutable definitions)
CREATE POLICY "Users can view own architectures" ON architectures
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own architectures" ON architectures
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Deny updates on architectures to preserve lineage immutability" ON architectures
    FOR UPDATE USING (false);

-- 3. Benchmark Runs Policies (Historical Immutability: Append-only)
CREATE POLICY "Users can view own benchmark runs" ON benchmark_runs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own benchmark runs" ON benchmark_runs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Deny updates on benchmark runs to preserve historical immutability" ON benchmark_runs
    FOR UPDATE USING (false);

-- 4. Evaluations Policies (Historical Immutability: Append-only)
CREATE POLICY "Users can view own evaluations" ON evaluations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own evaluations" ON evaluations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Deny updates on evaluations to preserve historical immutability" ON evaluations
    FOR UPDATE USING (false);

-- 5. Mutations Policies (Historical Immutability: Append-only)
CREATE POLICY "Users can view own mutations" ON mutations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own mutations" ON mutations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Deny updates on mutations to preserve historical immutability" ON mutations
    FOR UPDATE USING (false);

-- 6. Traces Policies (Historical Immutability: Append-only)
CREATE POLICY "Users can view own traces" ON traces
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own traces" ON traces
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Deny updates on traces to preserve historical immutability" ON traces
    FOR UPDATE USING (false);

-- 7. User Entitlements Policies
CREATE POLICY "Users can view own entitlements" ON user_entitlements
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own entitlements" ON user_entitlements
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own entitlements" ON user_entitlements
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

