# AGY Prompt 05 — Multi-Candidate Optimization & Air-Gapped Held-Out Promotion Gate

## AO Session Setup
```bash
# 1. Create GitHub Issue
# Title: feat: multi-candidate exploration, pareto selection, and held-out promotion gate

# 2. Spawn AO Session
ao session spawn --name "05-multicandidate-heldout" --issue 5

# 3. Run with AGY CLI
agy --file docs/prompts/05_multicandidate_optimization_and_heldout.md
```

---

## Objective
Implement multi-candidate exploration per generation (evaluating alternative architectural mutations simultaneously), rank them via multi-dimensional Pareto dominance, and enforce an air-gapped held-out evaluation gate to eliminate benchmark overfitting and false promotions.

## Context & Architecture
- System: **Reco** (Autonomous Agent Engineering System)
- Reference Docs:
  - [Multi-Candidate Optimization Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_MULTI_CANDIDATE_OPTIMIZATION.md)
  - [Scorecard Specification](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_SCORECARD.md)
  - [Failure Diagnostics Taxonomy](file:///c:/Users/toufi/Desktop/test-ao/docs/RECO_FAILURE_ANALYZER.md)

## Requirements to Implement

### 1. Multi-Candidate Pool Generator (`reco/mutation/generator.py`)
- Given diagnosed failure clusters on the optimization split, synthesize multiple competing candidate variants:
  - **Candidate A (Prompt / Few-Shot Specialist)**: Targeted prompt refinement with edge-case instructions.
  - **Candidate B (Verifier Specialist)**: Introduces verification and schema-conformance guardrail node.
  - **Candidate C (Topology / Tool Specialist)**: Restructures graph topology or assigns specialized analytical tools.
- Validate all candidates through `CandidateValidator`.

### 2. Multi-Candidate Tournament & Pareto Dominance
- Benchmark all candidates against the optimization split.
- Compute 4-axis scorecards for each candidate:
  - Identify non-dominated candidates along the Pareto frontier ($\text{Accuracy}, \text{Reliability}, \text{Cost}, \text{Speed}$).
  - Select the winning candidate that achieves maximum accuracy without catastrophic regression on cost/latency.

### 3. Air-Gapped Held-Out Validation Gate (`reco/evaluators/comparison.py`)
- **Strict Isolation**: Held-out split data is never accessible during goal analysis, failure diagnosis, or mutation generation.
- Evaluate winning candidate against unseen held-out cases.
- Apply formal Promotion Decision Policy:
  - `PROMOTED`: Candidate improves accuracy on held-out cases with acceptable cost/latency profile $\to$ Adopt as new champion ($V_1$).
  - `REQUIRES_REVIEW`: Candidate improves accuracy but incurs notable tradeoff ($\ge 3\times$ latency or cost increase).
  - `REJECTED`: Candidate regresses on held-out cases (overfitting detected) $\to$ Retain previous champion.

## Verification & Acceptance Criteria
1. Generates 3 diverse, valid candidate architectures per optimization generation.
2. Correctly selects Pareto-optimal candidate on optimization benchmarks.
3. Air-gapped held-out gate detects and rejects overfitted or regressed mutations.
4. Pass all unit tests:
   ```bash
   python -m pytest tests/test_step22_multi_candidate.py tests/test_closed_loop_verification.py -v
   ```
