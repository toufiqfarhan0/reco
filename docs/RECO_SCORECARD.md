# Reco Generic Multi-Dimensional Evaluator & Scorecard System

## 1. Overview & Architectural Role

Reco is an Autonomous Agent Engineering System (Track 1: Automated Agent Engineering). The core self-improvement loop requires comparing synthesized agent versions across four fundamental engineering dimensions:

$$\text{Architecture } V_k \quad \overset{\text{Benchmark}}{\Longrightarrow} \quad \text{Scorecard } S_k \quad \overset{\text{Compare}}{\Longleftrightarrow} \quad \text{Scorecard } S_{k+1} \quad \overset{\text{Assess}}{\Longrightarrow} \quad \text{Promotion / Rejection}$$

The Generic Evaluator & Scorecard layer sits above domain-specific benchmark implementations (such as the Bank & Ledger Reconciliation benchmark). It provides:
1. A strongly-typed, domain-agnostic `Scorecard` representation.
2. Separation between raw units and normalized scores.
3. Multi-axis dominance evaluation (strictly better, strictly worse, tradeoff, equivalent).
4. Deterministic programmatic narrative summaries (no LLM in the evaluation loop).
5. Configurable `ComparisonPolicy` and `PromotionAssessment` models ready for the future promotion controller.
6. Split awareness (`optimization` vs `held_out`) to prevent data leakage and unwarranted promotions.

---

## 2. Generic Scorecard Model

The `Scorecard` model is defined in [reco/evaluators/scorecard.py](file:///c:/Users/toufi/Desktop/test-ao/reco/evaluators/scorecard.py):

```python
class Scorecard(BaseModel):
    benchmark_name: str
    benchmark_version: str
    agent_version_id: Optional[UUID] = None
    experiment_id: Optional[UUID] = None
    split: Literal["optimization", "held_out", "full"]

    # Raw Primary Metrics
    accuracy: float = Field(..., ge=0.0, le=1.0)
    reliability: float = Field(..., ge=0.0, le=1.0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    avg_cost_usd: float = Field(default=0.0, ge=0.0)
    cost_type: Literal["actual", "estimated", "simulated_mock"] = "actual"
    total_latency_ms: int = Field(default=0, ge=0)
    avg_latency_ms: int = Field(default=0, ge=0)
    p50_latency_ms: Optional[int] = None
    p95_latency_ms: Optional[int] = None

    # Case Counts
    total_cases: int = Field(..., ge=0)
    passed_cases: int = Field(..., ge=0)
    failed_cases: int = Field(..., ge=0)

    # Auxiliary Normalized Representation & Metadata
    normalized: Optional[NormalizedMetrics] = None
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
```

---

## 3. Four Core Performance Dimensions

| Dimension | Raw Scale & Units | Directionality | Definition |
| :--- | :--- | :--- | :--- |
| **Accuracy** | `0.0` to `1.0` (ratio) | **Higher is better** ($\uparrow$) | Provided by the domain evaluator (e.g. composite formula for reconciliation). Generic layer does not force a synthetic formula. |
| **Reliability** | `0.0` to `1.0` (ratio) | **Higher is better** ($\uparrow$) | $\frac{\text{successful\_cases}}{\text{total\_cases}}$, where successful means zero fatal execution crashes and valid output schema. Separate from accuracy. |
| **Cost** | USD ($) | **Lower is better** ($\downarrow$) | Measured execution cost (`total_cost_usd`, `avg_cost_usd`). Explicitly labeled as `actual`, `estimated`, or `simulated_mock`. |
| **Speed / Latency** | Milliseconds (`ms`) | **Lower is better** ($\downarrow$) | Wall-clock execution time (`total_latency_ms`, `avg_latency_ms`, optional $P_{50}, P_{95}$). |

---

## 4. Raw vs. Normalized Metrics

Reco strictly maintains **raw metrics** in their original physical units:
- Accuracy & Reliability: fractional ratio (`0.0` to `1.0`)
- Cost: US Dollars (`$`)
- Latency: Milliseconds (`ms`)

To support comparative visualization and Pareto radar charts, the `compute_normalized()` method generates an auxiliary `NormalizedMetrics` object:
- `accuracy_norm`: identical to `accuracy` ($0.0$ to $1.0$)
- `reliability_norm`: identical to `reliability` ($0.0$ to $1.0$)
- `cost_norm`: bounded efficiency score $\max\left(0.0, 1.0 - \frac{\text{avg\_cost}}{\text{cost\_max\_ref}}\right)$
- `speed_norm`: bounded speed efficiency score $\max\left(0.0, 1.0 - \frac{\text{avg\_latency}}{\text{latency\_max\_ref}}\right)$

> [!IMPORTANT]
> Raw values and units are never mutated, scaled, or discarded. Normalized scores are an auxiliary view.

---

## 5. Comparison Algorithm & Dominance Rules

Comparison between a baseline ($S_{\text{base}}$) and candidate ($S_{\text{cand}}$) is performed deterministically by `compare_scorecards()`:

### Dimension Deltas
- $\Delta_{\text{accuracy}} = \text{accuracy}_{\text{cand}} - \text{accuracy}_{\text{base}}$ (improved if $> +\epsilon$)
- $\Delta_{\text{reliability}} = \text{reliability}_{\text{cand}} - \text{reliability}_{\text{base}}$ (improved if $> +\epsilon$)
- $\Delta_{\text{cost}} = \text{avg\_cost}_{\text{cand}} - \text{avg\_cost}_{\text{base}}$ (improved if $< -\epsilon$)
- $\Delta_{\text{latency}} = \text{avg\_latency}_{\text{cand}} - \text{avg\_latency}_{\text{base}}$ (improved if $< -\epsilon$)

### Multi-Dimensional Dominance
The relationship between candidate and baseline is classified into four mutually exclusive categories:
1. **`strictly_better`**: Candidate improved in $\ge 1$ dimension and regressed in $0$ dimensions.
2. **`strictly_worse`**: Candidate regressed in $\ge 1$ dimension and improved in $0$ dimensions.
3. **`tradeoff`**: Candidate improved in $\ge 1$ dimension but regressed in $\ge 1$ other dimension (e.g. accuracy increased by $12\%$ but cost increased by $35\%$).
4. **`equivalent`**: No dimensions exhibited changes exceeding numerical noise tolerance $\epsilon$.

---

## 6. Deterministic Improvement Summary

The `format_improvement_summary()` function compiles a human-readable text narrative directly from metric deltas:

```python
summary = format_improvement_summary(comparison)
```
*Example Output*:
> "Accuracy improved by +12.4 percentage points (75.0% -> 87.4%), reliability remained unchanged at 100.0%, average cost decreased by 31.0% ($0.000575 -> $0.000397), and average latency decreased by 22.0% (100ms -> 78ms)."

- Accuracy and Reliability use **percentage points** (`pp`).
- Cost and Latency use **relative percentage change** (`%`) and raw currency/millisecond transitions.
- Fully programmatic; zero LLM token generation.

---

## 7. Comparison Policy & Tradeoff Handling

Dominance and promotion thresholds are governed by a configurable `ComparisonPolicy`:

```python
class ComparisonPolicy(BaseModel):
    tolerance_eps: float = 0.0001
    min_accuracy_gain: float = 0.0
    require_non_regressive_reliability: bool = True
    max_acceptable_cost_increase_pct: float = 0.0
    max_acceptable_latency_increase_pct: float = 0.0
    allow_tradeoffs: bool = False
```

### Tradeoff Handling
By default (`allow_tradeoffs=False`), any candidate that causes regression in cost or latency is flagged as `decision="review"` rather than promoted. When `allow_tradeoffs=True`, candidates may be promoted if cost/latency increases remain strictly within `max_acceptable_cost_increase_pct` and `max_acceptable_latency_increase_pct`, provided `min_accuracy_gain` is satisfied.

---

## 8. Promotion Assessment & Split Protocol

The `assess_promotion()` function produces a structured `PromotionAssessment`:

```python
class PromotionAssessment(BaseModel):
    decision: Literal["promote", "reject", "review"]
    reasons: List[str]
    scorecard_before: Scorecard
    scorecard_after: Scorecard
    comparison: ScorecardComparison
    improved_dimensions: List[str]
    regressed_dimensions: List[str]
    held_out_required: bool
    split: str
    metadata: Dict[str, Any]
```

### Split Gating Rules
1. **Optimization Split**:
   - If candidate is strictly better: `decision = "review"`, with `held_out_required = True`.
   - Reason: Enhancements on the training/optimization set must be validated on the held-out partition before promotion.
   - If candidate regressed: `decision = "reject"`.
2. **Held-Out Split**:
   - If candidate is strictly better and reliability did not regress: `decision = "promote"`.
   - If candidate regressed: `decision = "reject"`.
   - If reliability dropped: immediate `decision = "reject"` (reliability non-regression invariant).
   - If tradeoff: `decision = "review"` (or `promote` if permitted by `ComparisonPolicy`).

---

## 9. Cross-Domain Compatibility

The scorecard framework is completely decoupled from finance or reconciliation terminology:
- Evaluated and tested with generic benchmarks (e.g. `academic_research_eval`, `code_review_eval`).
- The `Scorecard` model contains zero fields specific to banking, ledger, transactions, or accounting.
- Compatible with any future domain evaluator adhering to `accuracy`, `reliability`, `cost`, and `latency`.

---

## 10. Persistence & API Integration

- **Persistence**: `Scorecard.to_db_record()` and `Scorecard.from_db_record()` provide seamless bidirectional mapping with existing `BenchmarkRunRecord` models without altering database tables.
- **API**: Minimal internal endpoint:
  ```http
  POST /scorecard/compare
  Content-Type: application/json

  {
    "baseline": { ... Scorecard JSON ... },
    "candidate": { ... Scorecard JSON ... },
    "policy": { "allow_tradeoffs": false }
  }
  ```
  Returns full `ScorecardComparison` with deltas, classifications, and narrative summary.
