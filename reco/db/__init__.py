"""Database persistence and authentication module for Supabase PostgreSQL & GoTrue."""

from reco.db.auth import GoTrueAuthHandler, UserContext
from reco.db.models import (
    ArchitectureRecord,
    AuthenticationError,
    BenchmarkRunRecord,
    EvaluationRecord,
    ExperimentRecord,
    ImmutabilityError,
    MutationRecord,
    TraceRecord,
    UserIsolationError,
)
from reco.db.repository import ExperimentRepository, InMemoryRepository
from reco.db.supabase import SupabaseRepository, get_repository

__all__ = [
    "ArchitectureRecord",
    "AuthenticationError",
    "BenchmarkRunRecord",
    "EvaluationRecord",
    "ExperimentRecord",
    "ExperimentRepository",
    "GoTrueAuthHandler",
    "ImmutabilityError",
    "InMemoryRepository",
    "MutationRecord",
    "SupabaseRepository",
    "TraceRecord",
    "UserContext",
    "UserIsolationError",
    "get_repository",
]
