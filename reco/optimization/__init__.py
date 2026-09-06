"""Autonomous agent multi-generation optimization package."""

from reco.optimization.controller import OptimizationController
from reco.optimization.events import (
    OptimizationEvent,
    OptimizationEventDispatcher,
    OptimizationEventListener,
    OptimizationEventType,
)
from reco.optimization.history import (
    HistoryTracker,
    compute_graph_fingerprint,
    compute_mutation_fingerprint,
)
from reco.optimization.models import (
    OptimizationConfig,
    OptimizationGeneration,
    OptimizationResult,
)

__all__ = [
    "OptimizationController",
    "OptimizationConfig",
    "OptimizationGeneration",
    "OptimizationResult",
    "OptimizationEvent",
    "OptimizationEventType",
    "OptimizationEventDispatcher",
    "OptimizationEventListener",
    "HistoryTracker",
    "compute_graph_fingerprint",
    "compute_mutation_fingerprint",
]
