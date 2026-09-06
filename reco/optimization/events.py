"""Internal structured events for optimization observability and tracing."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field


class OptimizationEventType(str, Enum):
    OPTIMIZATION_STARTED = "optimization_started"
    GENERATION_STARTED = "generation_started"
    CANDIDATE_GENERATED = "candidate_generated"
    CANDIDATE_VALIDATED = "candidate_validated"
    CANDIDATE_BENCHMARKED = "candidate_benchmarked"
    CANDIDATE_SELECTED = "candidate_selected"
    CANDIDATE_REJECTED = "candidate_rejected"
    GENERATION_COMPLETED = "generation_completed"
    OPTIMIZATION_TERMINATED = "optimization_terminated"
    PROMOTION_ASSESSED = "promotion_assessed"


class OptimizationEvent(BaseModel):
    """Structured event emitted during autonomous optimization execution."""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: OptimizationEventType
    experiment_id: UUID
    generation_number: Optional[int] = None
    parent_version_id: Optional[UUID] = None
    candidate_id: Optional[UUID] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(arbitrary_types_allowed=True)


OptimizationEventListener = Callable[[OptimizationEvent], Any]


class OptimizationEventDispatcher:
    """Dispatches optimization events to registered listeners."""

    def __init__(self, listeners: Optional[List[OptimizationEventListener]] = None):
        self.listeners: List[OptimizationEventListener] = listeners or []

    def register(self, listener: OptimizationEventListener) -> None:
        if listener not in self.listeners:
            self.listeners.append(listener)

    def emit(self, event: OptimizationEvent) -> None:
        for listener in self.listeners:
            try:
                res = listener(event)
                # If listener returns a coroutine, we can let it run or log
            except Exception:
                # Observers must never crash the optimization loop
                pass
