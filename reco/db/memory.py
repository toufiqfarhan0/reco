"""In-memory repository implementations for offline testing and fast deterministic unit tests."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

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


class InMemoryExperimentRepository(ExperimentRepository):
    """In-memory store for experiments."""

    def __init__(self):
        self.storage: Dict[UUID, ExperimentRecord] = {}

    async def create(self, record: ExperimentRecord) -> ExperimentRecord:
        if record.id in self.storage:
            raise ValueError(f"Experiment with ID {record.id} already exists")
        self.storage[record.id] = record.model_copy()
        return self.storage[record.id]

    async def get(self, experiment_id: UUID) -> Optional[ExperimentRecord]:
        record = self.storage.get(experiment_id)
        return record.model_copy() if record else None

    async def update(self, record: ExperimentRecord) -> ExperimentRecord:
        if record.id not in self.storage:
            raise KeyError(f"Experiment with ID {record.id} not found")
        record.updated_at = datetime.now(timezone.utc)
        self.storage[record.id] = record.model_copy()
        return self.storage[record.id]

    async def list_all(self) -> List[ExperimentRecord]:
        return [r.model_copy() for r in self.storage.values()]


class InMemoryAgentVersionRepository(AgentVersionRepository):
    """In-memory store for immutable agent versions."""

    def __init__(self):
        self.storage: Dict[UUID, AgentVersionRecord] = {}

    async def create(self, record: AgentVersionRecord) -> AgentVersionRecord:
        # Enforce uniqueness of (experiment_id, version_number)
        for existing in self.storage.values():
            if (
                existing.experiment_id == record.experiment_id
                and existing.version_number == record.version_number
            ):
                raise ValueError(
                    f"AgentVersion {record.version_number} already exists for experiment {record.experiment_id}"
                )
        self.storage[record.id] = record.model_copy()
        return self.storage[record.id]

    async def get(self, version_id: UUID) -> Optional[AgentVersionRecord]:
        record = self.storage.get(version_id)
        return record.model_copy() if record else None

    async def get_by_version_number(self, experiment_id: UUID, version_number: int) -> Optional[AgentVersionRecord]:
        for record in self.storage.values():
            if record.experiment_id == experiment_id and record.version_number == version_number:
                return record.model_copy()
        return None

    async def list_for_experiment(self, experiment_id: UUID) -> List[AgentVersionRecord]:
        matches = [r.model_copy() for r in self.storage.values() if r.experiment_id == experiment_id]
        matches.sort(key=lambda x: x.version_number)
        return matches

    async def update_status(self, version_id: UUID, status: str) -> Optional[AgentVersionRecord]:
        record = self.storage.get(version_id)
        if not record:
            return None
        record.status = status  # type: ignore
        self.storage[version_id] = record.model_copy()
        return self.storage[version_id]


class InMemoryToolRepository(ToolRepository):
    """In-memory store for tools."""

    def __init__(self):
        self.storage: Dict[UUID, ToolRecord] = {}

    async def create(self, record: ToolRecord) -> ToolRecord:
        for existing in self.storage.values():
            if existing.name == record.name:
                raise ValueError(f"Tool with name '{record.name}' already exists")
        self.storage[record.id] = record.model_copy()
        return self.storage[record.id]

    async def get(self, tool_id: UUID) -> Optional[ToolRecord]:
        record = self.storage.get(tool_id)
        return record.model_copy() if record else None

    async def get_by_name(self, name: str) -> Optional[ToolRecord]:
        for record in self.storage.values():
            if record.name == name:
                return record.model_copy()
        return None

    async def list_active(self) -> List[ToolRecord]:
        return [r.model_copy() for r in self.storage.values() if r.enabled]


class InMemoryBenchmarkCaseRepository(BenchmarkCaseRepository):
    """In-memory store for benchmark test cases."""

    def __init__(self):
        self.storage: Dict[UUID, BenchmarkCaseRecord] = {}

    async def create(self, record: BenchmarkCaseRecord) -> BenchmarkCaseRecord:
        for existing in self.storage.values():
            if existing.case_code == record.case_code:
                raise ValueError(f"Benchmark case with code '{record.case_code}' already exists")
        self.storage[record.id] = record.model_copy()
        return self.storage[record.id]

    async def get(self, case_id: UUID) -> Optional[BenchmarkCaseRecord]:
        record = self.storage.get(case_id)
        return record.model_copy() if record else None

    async def get_by_code(self, case_code: str) -> Optional[BenchmarkCaseRecord]:
        for record in self.storage.values():
            if record.case_code == case_code:
                return record.model_copy()
        return None

    async def list_by_split(self, benchmark_name: str, split: str) -> List[BenchmarkCaseRecord]:
        return [
            r.model_copy()
            for r in self.storage.values()
            if r.benchmark_name == benchmark_name and r.split == split
        ]

    async def bulk_create(self, records: List[BenchmarkCaseRecord]) -> List[BenchmarkCaseRecord]:
        created = []
        for rec in records:
            created.append(await self.create(rec))
        return created


class InMemoryBenchmarkRunRepository(BenchmarkRunRepository):
    """In-memory store for benchmark runs."""

    def __init__(self):
        self.storage: Dict[UUID, BenchmarkRunRecord] = {}

    async def create(self, record: BenchmarkRunRecord) -> BenchmarkRunRecord:
        self.storage[record.id] = record.model_copy()
        return self.storage[record.id]

    async def get(self, run_id: UUID) -> Optional[BenchmarkRunRecord]:
        record = self.storage.get(run_id)
        return record.model_copy() if record else None

    async def list_for_version(self, agent_version_id: UUID) -> List[BenchmarkRunRecord]:
        return [r.model_copy() for r in self.storage.values() if r.agent_version_id == agent_version_id]

    async def list_for_experiment(self, experiment_id: UUID) -> List[BenchmarkRunRecord]:
        return [r.model_copy() for r in self.storage.values() if r.experiment_id == experiment_id]


class InMemoryCaseExecutionRepository(CaseExecutionRepository):
    """In-memory store for case execution traces."""

    def __init__(self):
        self.storage: Dict[UUID, CaseExecutionRecord] = {}

    async def create(self, record: CaseExecutionRecord) -> CaseExecutionRecord:
        self.storage[record.id] = record.model_copy()
        return self.storage[record.id]

    async def get(self, execution_id: UUID) -> Optional[CaseExecutionRecord]:
        record = self.storage.get(execution_id)
        return record.model_copy() if record else None

    async def list_for_run(self, benchmark_run_id: UUID) -> List[CaseExecutionRecord]:
        return [r.model_copy() for r in self.storage.values() if r.benchmark_run_id == benchmark_run_id]


class InMemoryFailureDiagnosisRepository(FailureDiagnosisRepository):
    """In-memory store for failure diagnoses."""

    def __init__(self):
        self.storage: Dict[UUID, FailureDiagnosisRecord] = {}

    async def create(self, record: FailureDiagnosisRecord) -> FailureDiagnosisRecord:
        self.storage[record.id] = record.model_copy()
        return self.storage[record.id]

    async def get(self, diagnosis_id: UUID) -> Optional[FailureDiagnosisRecord]:
        record = self.storage.get(diagnosis_id)
        return record.model_copy() if record else None

    async def get_for_case_execution(self, case_execution_id: UUID) -> Optional[FailureDiagnosisRecord]:
        for record in self.storage.values():
            if record.case_execution_id == case_execution_id:
                return record.model_copy()
        return None


class InMemoryImprovementRepository(ImprovementRepository):
    """In-memory store for improvement lineage."""

    def __init__(self):
        self.storage: Dict[UUID, ImprovementRecord] = {}

    async def create(self, record: ImprovementRecord) -> ImprovementRecord:
        self.storage[record.id] = record.model_copy()
        return self.storage[record.id]

    async def get(self, improvement_id: UUID) -> Optional[ImprovementRecord]:
        record = self.storage.get(improvement_id)
        return record.model_copy() if record else None

    async def list_for_experiment(self, experiment_id: UUID) -> List[ImprovementRecord]:
        return [r.model_copy() for r in self.storage.values() if r.experiment_id == experiment_id]


class InMemoryDatabase:
    """Unified container for all in-memory repositories."""

    def __init__(self):
        self.experiments = InMemoryExperimentRepository()
        self.agent_versions = InMemoryAgentVersionRepository()
        self.tools = InMemoryToolRepository()
        self.benchmark_cases = InMemoryBenchmarkCaseRepository()
        self.benchmark_runs = InMemoryBenchmarkRunRepository()
        self.case_executions = InMemoryCaseExecutionRepository()
        self.failure_diagnoses = InMemoryFailureDiagnosisRepository()
        self.improvements = InMemoryImprovementRepository()

    def clear(self):
        """Clear all stored entities across all repositories."""
        self.experiments.storage.clear()
        self.agent_versions.storage.clear()
        self.tools.storage.clear()
        self.benchmark_cases.storage.clear()
        self.benchmark_runs.storage.clear()
        self.case_executions.storage.clear()
        self.failure_diagnoses.storage.clear()
        self.improvements.storage.clear()
