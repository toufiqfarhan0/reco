"""Persistence layer for Reco (Supabase PostgreSQL & In-Memory)."""

from reco.db.memory import (
    InMemoryAgentVersionRepository,
    InMemoryBenchmarkCaseRepository,
    InMemoryBenchmarkRunRepository,
    InMemoryCaseExecutionRepository,
    InMemoryDatabase,
    InMemoryExperimentRepository,
    InMemoryFailureDiagnosisRepository,
    InMemoryImprovementRepository,
    InMemoryToolRepository,
)
from reco.db.models import (
    AgentVersionRecord,
    BenchmarkCaseRecord,
    BenchmarkRunRecord,
    CaseExecutionRecord,
    ExperimentRecord,
    FailureDiagnosisRecord,
    ImprovementRecord,
    ToolRecord,
)
from reco.db.repositories import (
    AgentVersionRepository,
    BenchmarkCaseRepository,
    BenchmarkRunRepository,
    CaseExecutionRepository,
    ExperimentRepository,
    FailureDiagnosisRepository,
    ImprovementRepository,
    ToolRepository,
)
from reco.db.session import get_db
from reco.db.supabase import SupabaseDatabase

__all__ = [
    # Models
    "ExperimentRecord",
    "ToolRecord",
    "AgentVersionRecord",
    "BenchmarkCaseRecord",
    "BenchmarkRunRecord",
    "CaseExecutionRecord",
    "FailureDiagnosisRecord",
    "ImprovementRecord",
    # Abstract Repositories
    "ExperimentRepository",
    "AgentVersionRepository",
    "ToolRepository",
    "BenchmarkCaseRepository",
    "BenchmarkRunRepository",
    "CaseExecutionRepository",
    "FailureDiagnosisRepository",
    "ImprovementRepository",
    # In-memory implementation
    "InMemoryDatabase",
    "InMemoryExperimentRepository",
    "InMemoryAgentVersionRepository",
    "InMemoryToolRepository",
    "InMemoryBenchmarkCaseRepository",
    "InMemoryBenchmarkRunRepository",
    "InMemoryCaseExecutionRepository",
    "InMemoryFailureDiagnosisRepository",
    "InMemoryImprovementRepository",
    # Supabase implementation
    "SupabaseDatabase",
    # Factory
    "get_db",
]
