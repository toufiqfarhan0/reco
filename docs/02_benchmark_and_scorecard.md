# AGY Prompt 02 — Partitioned Benchmark Framework & 4-Axis Scorecard

## AO Session Setup
```bash
# 1. Create GitHub Issue
# Title: feat: partitioned benchmark harness and 4-axis scorecard evaluation

# 2. Spawn AO Session
ao session spawn --name "02-benchmark-scorecard" --issue 2

# 3. Run with AGY CLI
agy --file docs/prompts/02_benchmark_and_scorecard.md
```

---

## Objective
Implement an empirical benchmark evaluation framework that measures agent performance across 4 canonical axes: **Accuracy**, **Reliability**, **Cost**, and **Speed**, with strict partition isolation between optimization and held-out test splits.

## Context & Architecture
- System: **Reco** (Autonomous Agent Engineering System)
- Reference Docs:
  - [Benchmark Framework Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_BENCHMARK.md)
  - [Scorecard Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_SCORECARD.md)
  - [Execution Modes](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_EXECUTION_MODES.md)

## Requirements to Implement

### 1. Partitioned Benchmark Harness (`reco/benchmarks/`)
- Define benchmark test cases comprising:
  - `case_id`: Unique deterministic identifier.
  - `input_data`: Raw payload fed to the agent DAG.
  - `expected_output`: Ground-truth assertion criteria.
  - `split`: Strictly partitioned into `optimization` (for mutation discovery) and `held-out` (air-gapped validation).
- Implement initial domain dataset (`reco/benchmarks/reconciliation/`):
  - 10 distinct reconciliation scenarios (exact matches, missing records, amount mismatches, duplicates, format variations).

### 2. 4-Axis Scorecard Metric Engine (`reco/evaluators/scorecard.py`)
- Calculate aggregate performance along 4 canonical dimensions:
  1. **Accuracy**: Fraction of benchmark cases where output exactly matches ground truth ($0.0 \to 1.0$).
  2. **Reliability**: Fraction of benchmark cases executed without runtime exceptions or tool errors ($0.0 \to 1.0$).
  3. **Cost (USD)**: Exact token-derived inference cost based on provider pricing (or deterministic $0 tool cost).
  4. **Speed / Latency**: Total wall-clock execution time in milliseconds/seconds.
- Implement side-by-side scorecard comparison (`ScorecardComparison`):
  - Compute delta ($\Delta$) for each metric ($\Delta\text{Accuracy}$, $\Delta\text{Reliability}$, $\Delta\text{Cost}$, $\Delta\text{Latency}$).
  - Detect Pareto dominance (Candidate beats baseline on $\ge 1$ axis without regressing on any).
  - Identify tradeoffs (e.g., +20% accuracy at +15% latency cost).

### 3. Baseline V0 Execution
- Run synthesized V0 baseline agent through the benchmark suite.
- Generate structured scorecard artifact recording initial baseline numbers.

## Verification & Acceptance Criteria
1. Benchmark correctly splits cases into optimization and held-out sets without overlap.
2. Scorecard calculator computes mathematical metrics without rounding anomalies.
3. Pareto dominance comparator flags improvements, regressions, and trade-offs correctly.
4. Pass all unit tests:
   ```bash
   python -m pytest tests/test_benchmark.py tests/test_scorecard.py -v
   ```
