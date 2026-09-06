"""Evaluation engine and 4-axis scorecard computation."""

from reco.evaluators.scorecard import (
    CaseEvaluationResult,
    Scorecard,
    ScorecardComparison,
    ScorecardEvaluator,
    run_v0_benchmark,
)
from reco.evaluators.comparison import (
    HeldOutCaseResult,
    HeldOutValidationGate,
    HeldOutValidationResult,
    PromotionDecision,
    TournamentEvaluator,
    TournamentResult,
    compute_pareto_frontier,
    is_pareto_dominant_pair,
    select_tournament_winner,
)

__all__ = [
    "CaseEvaluationResult",
    "Scorecard",
    "ScorecardComparison",
    "ScorecardEvaluator",
    "run_v0_benchmark",
    "TournamentEvaluator",
    "TournamentResult",
    "HeldOutCaseResult",
    "HeldOutValidationGate",
    "HeldOutValidationResult",
    "PromotionDecision",
    "compute_pareto_frontier",
    "is_pareto_dominant_pair",
    "select_tournament_winner",
]
