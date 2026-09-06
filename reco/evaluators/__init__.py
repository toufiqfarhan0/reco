"""Generic Multi-Dimensional Evaluator and Scorecard System for Reco."""

from reco.evaluators.comparison import (
    ComparisonPolicy,
    DimensionDelta,
    PromotionAssessment,
    ScorecardComparison,
    assess_promotion,
    compare_scorecards,
    format_improvement_summary,
)
from reco.evaluators.scorecard import NormalizedMetrics, Scorecard

__all__ = [
    "NormalizedMetrics",
    "Scorecard",
    "ComparisonPolicy",
    "DimensionDelta",
    "ScorecardComparison",
    "PromotionAssessment",
    "compare_scorecards",
    "format_improvement_summary",
    "assess_promotion",
]
