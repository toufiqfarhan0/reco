"""Abstract repository interfaces for Reco persistence."""

from abc import ABC, abstractmethod
from typing import List, Optional
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


class ExperimentRepository(ABC):
    """Repository contract for experiments."""

    @abstractmethod
    async def create(self, record: ExperimentRecord) -> ExperimentRecord:
        pass

    @abstractmethod
    async def get(self, experiment_id: UUID) -> Optional[ExperimentRecord]:
        pass

    @abstractmethod
    async def update(self, record: ExperimentRecord) -> ExperimentRecord:
        pass

    @abstractmethod
    async def list_all(self) -> List[ExperimentRecord]:
        pass


class AgentVersionRepository(ABC):
    """Repository contract for immutable agent version snapshots."""

    @abstractmethod
    async def create(self, record: AgentVersionRecord) -> AgentVersionRecord:
        pass

    @abstractmethod
    async def get(self, version_id: UUID) -> Optional[AgentVersionRecord]:
        pass

    @abstractmethod
    async def get_by_version_number(self, experiment_id: UUID, version_number: int) -> Optional[AgentVersionRecord]:
        pass

    @abstractmethod
    async def list_for_experiment(self, experiment_id: UUID) -> List[AgentVersionRecord]:
        pass

    @abstractmethod
    async def update_status(self, version_id: UUID, status: str) -> Optional[AgentVersionRecord]:
        pass


class ToolRepository(ABC):
    """Repository contract for tools."""

    @abstractmethod
    async def create(self, record: ToolRecord) -> ToolRecord:
        pass

    @abstractmethod
    async def get(self, tool_id: UUID) -> Optional[ToolRecord]:
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[ToolRecord]:
        pass

    @abstractmethod
    async def list_active(self) -> List[ToolRecord]:
        pass


class BenchmarkCaseRepository(ABC):
    """Repository contract for benchmark test cases."""

    @abstractmethod
    async def create(self, record: BenchmarkCaseRecord) -> BenchmarkCaseRecord:
        pass

    @abstractmethod
    async def get(self, case_id: UUID) -> Optional[BenchmarkCaseRecord]:
        pass

    @abstractmethod
    async def get_by_code(self, case_code: str) -> Optional[BenchmarkCaseRecord]:
        pass

    @abstractmethod
    async def list_by_split(self, benchmark_name: str, split: str) -> List[BenchmarkCaseRecord]:
        pass

    @abstractmethod
    async def bulk_create(self, records: List[BenchmarkCaseRecord]) -> List[BenchmarkCaseRecord]:
        pass


class BenchmarkRunRepository(ABC):
    """Repository contract for benchmark evaluation runs."""

    @abstractmethod
    async def create(self, record: BenchmarkRunRecord) -> BenchmarkRunRecord:
        pass

    @abstractmethod
    async def get(self, run_id: UUID) -> Optional[BenchmarkRunRecord]:
        pass

    @abstractmethod
    async def list_for_version(self, agent_version_id: UUID) -> List[BenchmarkRunRecord]:
        pass

    @abstractmethod
    async def list_for_experiment(self, experiment_id: UUID) -> List[BenchmarkRunRecord]:
        pass


class CaseExecutionRepository(ABC):
    """Repository contract for individual case execution logs."""

    @abstractmethod
    async def create(self, record: CaseExecutionRecord) -> CaseExecutionRecord:
        pass

    @abstractmethod
    async def get(self, execution_id: UUID) -> Optional[CaseExecutionRecord]:
        pass

    @abstractmethod
    async def list_for_run(self, benchmark_run_id: UUID) -> List[CaseExecutionRecord]:
        pass


class FailureDiagnosisRepository(ABC):
    """Repository contract for root-cause failure analyses."""

    @abstractmethod
    async def create(self, record: FailureDiagnosisRecord) -> FailureDiagnosisRecord:
        pass

    @abstractmethod
    async def get(self, diagnosis_id: UUID) -> Optional[FailureDiagnosisRecord]:
        pass

    @abstractmethod
    async def get_for_case_execution(self, case_execution_id: UUID) -> Optional[FailureDiagnosisRecord]:
        pass


class ImprovementRepository(ABC):
    """Repository contract for version mutation lineage."""

    @abstractmethod
    async def create(self, record: ImprovementRecord) -> ImprovementRecord:
        pass

    @abstractmethod
    async def get(self, improvement_id: UUID) -> Optional[ImprovementRecord]:
        pass

    @abstractmethod
    async def list_for_experiment(self, experiment_id: UUID) -> List[ImprovementRecord]:
        pass
