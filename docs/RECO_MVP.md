# Reco MVP Specification & Data Model

## 1. MVP Boundary Definition

The Reco MVP demonstrates the complete closed-loop agent engineering cycle on a realistic, objective financial benchmark: **Bank & Ledger Reconciliation**.

### What MUST Exist for MVP:
1. **Goal Specification**: User submits a goal (e.g., *"Reconcile monthly bank statements against the company general ledger, identifying discrepancies, processing fees, and timing mismatches"*).
2. **Architecture Generation**: System synthesizes an initial agent graph ($V_0$) with roles, prompts, tool assignments, and workflow routing.
3. **Tool Execution**: Python runtime executing real reconciliation tools on synthetic but authentic financial records.
4. **Benchmark Evaluation**: Multi-case benchmark scoring Accuracy, Reliability, Cost, and Latency against verifiable ground truth.
5. **Failure Analysis**: Automatic parsing of mismatches, classifying root causes (e.g., fee oversight, arithmetic error, wrong tool parameter).
6. **Mutation & Optimization**: Synthesizing Version $V_1$ with targeted prompt, topology, or tool adjustments (e.g., inserting a fee-calculation tool or a verification agent).
7. **Regression Re-run**: Executing $V_1$ against both optimization and held-out test splits.
8. **Promotion & Comparison**: Demonstrating measurable improvement ($V_1 > V_0$) with full version diffing and metric reporting.

### What is Explicitly DEFERRED Post-MVP:
- Invoice processing workflow (Workflow #2).
- Audit evidence gathering workflow (Workflow #3).
- Complex multi-tenant workspace permissions.
- Heavy asynchronous task queues (Celery/RabbitMQ/Kafka) — use FastAPI background tasks or asyncio.
- Live bank API connectors (Plaid/Yodlee) — use structured benchmark datasets.

---

## 2. Benchmark Domain: Bank & Ledger Reconciliation

The reconciliation benchmark consists of **20 realistic test scenarios** partitioned into:
- **Optimization Set (12 cases)**: For failure inspection, root-cause diagnosis, and mutation generation.
- **Held-out Evaluation Set (8 cases)**: Never exposed to the failure analyzer; used strictly for unbiased promotion gating.

### Scenario Distribution & Exception Types:
1. **Exact Match**: Direct 1-to-1 match of amount, date, and reference string.
2. **Near Match**: Slight timing variance (1–3 business day lag) or minor reference string variation (e.g., "AWS EMEA" vs "Amazon Web Services").
3. **Processing Fees**: Gross vs. net discrepancies (e.g., customer paid $1,000, bank statement shows $971 after 2.9% merchant fee).
4. **Timing Differences**: Month-end deposits in transit or outstanding checks.
5. **Duplicate Transactions**: Double-billed charge in bank statement with single ledger entry, or accidental duplicate ledger journal entry.
6. **Missing Transactions**: Bank statement item with no matching general ledger entry (unrecorded bank charges or automatic ACH).
7. **Wrong Vendor / Entity**: Amount matches, but payee/payer does not correspond.
8. **Wrong Amount (Transposition Error)**: Ledger records $1,420.00 while bank cleared $1,240.00.
9. **FX Differences**: Currency conversion variances between invoice booking date and settlement date.
10. **Compound Exception**: Transaction with both merchant fee deduction and timing difference across month-end.

---

## 3. Supabase / PostgreSQL Data Model

The schema is streamlined for high query efficiency, relational consistency, and JSONB flexibility for agent graphs and execution traces.

```sql
-- 1. Experiments (High-level tuning run initiated by user)
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    goal_description TEXT NOT NULL,
    domain VARCHAR(100) DEFAULT 'reconciliation',
    status VARCHAR(50) DEFAULT 'running', -- 'running', 'completed', 'failed'
    best_agent_version_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Available Tool Catalog
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    parameters_schema JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Agent Versions (Each synthesized or mutated architecture)
CREATE TABLE agent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    parent_version_id UUID REFERENCES agent_versions(id),
    architecture_definition JSONB NOT NULL, -- Nodes, edges, prompts, tool bindings, model config
    mutation_summary TEXT, -- Description of changes from parent
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'evaluated', 'promoted', 'rejected'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Benchmark Cases
CREATE TABLE benchmark_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(100) DEFAULT 'reconciliation',
    case_code VARCHAR(50) UNIQUE NOT NULL,
    split VARCHAR(20) NOT NULL, -- 'optimization', 'held_out'
    difficulty VARCHAR(20) DEFAULT 'medium', -- 'easy', 'medium', 'hard'
    input_data JSONB NOT NULL, -- bank statement rows, ledger rows, metadata
    ground_truth JSONB NOT NULL, -- expected matched pairs, discrepancies, fee breakdowns
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Benchmark Runs (Evaluation of an Agent Version against a set of Benchmark Cases)
CREATE TABLE benchmark_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_version_id UUID REFERENCES agent_versions(id) ON DELETE CASCADE,
    split VARCHAR(20) NOT NULL, -- 'optimization', 'held_out', 'full'
    accuracy NUMERIC(5, 4) NOT NULL, -- 0.0000 to 1.0000
    reliability NUMERIC(5, 4) NOT NULL,
    total_cost_usd NUMERIC(10, 6) NOT NULL,
    avg_latency_ms INT NOT NULL,
    cases_passed INT NOT NULL,
    cases_total INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Case Execution Results (Individual case outputs)
CREATE TABLE case_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    benchmark_run_id UUID REFERENCES benchmark_runs(id) ON DELETE CASCADE,
    benchmark_case_id UUID REFERENCES benchmark_cases(id),
    passed BOOLEAN NOT NULL,
    accuracy_score NUMERIC(5, 4) NOT NULL,
    raw_output JSONB,
    execution_trace JSONB, -- Step logs, tool invocations, tokens used
    tokens_prompt INT DEFAULT 0,
    tokens_completion INT DEFAULT 0,
    cost_usd NUMERIC(10, 6) DEFAULT 0,
    latency_ms INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Failure Diagnoses
CREATE TABLE failure_diagnoses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_version_id UUID REFERENCES agent_versions(id) ON DELETE CASCADE,
    case_execution_id UUID REFERENCES case_executions(id) ON DELETE CASCADE,
    failure_category VARCHAR(100) NOT NULL, -- 'TOOL_ARGUMENT_ERROR', 'ARITHMETIC_MISMATCH', etc.
    root_cause_analysis TEXT NOT NULL,
    recommended_mutation_axis VARCHAR(100), -- 'prompt', 'topology', 'tool_selection', 'verifier'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Mutation Records
CREATE TABLE improvements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_version_id UUID REFERENCES agent_versions(id),
    to_version_id UUID REFERENCES agent_versions(id),
    mutation_type VARCHAR(50) NOT NULL, -- 'prompt_refinement', 'add_verifier', 'tool_reorder', 'model_switch'
    diff_summary JSONB NOT NULL,
    predicted_improvement TEXT,
    actual_accuracy_delta NUMERIC(5, 4),
    was_promoted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. MVP Verification Matrix

| Criterion | Target Metric | Verification Method |
| :--- | :--- | :--- |
| **Baseline Architecture ($V_0$)** | Valid executable graph | Generated autonomously from goal input; passes schema validation. |
| **Execution Completeness** | 100% of benchmark cases executed | All 20 cases run to completion without unhandled runtime crashes. |
| **Failure Diagnosis** | Accurate root-cause isolation | Correctly flags missing fee tool or missed tolerance bounds on failed cases. |
| **Mutation Applicability** | Non-trivial structural mutation | $V_1$ modifies prompts, tool configs, or adds a verification step based on diagnosis. |
| **Promotion Correctness** | Rigorous gating | $V_1$ is promoted only if held-out accuracy $\ge V_0$, with zero regression on baseline passes. |
| **Cost & Latency Tracking** | Accurate calculation | Real token counting and latency tracking recorded per run in Supabase. |
