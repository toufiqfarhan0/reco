"""Supabase PostgreSQL repository implementations for production persistence."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from reco.config import Settings, get_settings
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
from reco.logging import get_logger

logger = get_logger("db.supabase")

try:
    from supabase import Client, create_client
except ImportError:
    Client = Any  # type: ignore
    create_client = None  # type: ignore


def get_supabase_client(settings: Optional[Settings] = None, client: Optional[Client] = None) -> Client:
    """Return an initialized Supabase client, raising clear errors if unconfigured."""
    if client is not None:
        return client

    if create_client is None:
        raise RuntimeError("The 'supabase' python package is not installed. Install via `pip install supabase`.")

    cfg = settings or get_settings()
    if not cfg.supabase_url or not cfg.supabase_key:
        raise RuntimeError(
            "Supabase credentials missing. Ensure SUPABASE_URL and SUPABASE_KEY are set in environment or .env."
        )

    return create_client(cfg.supabase_url, cfg.supabase_key)


class SupabaseExperimentRepository(ExperimentRepository):
    """Supabase-backed repository for experiments."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    async def create(self, record: ExperimentRecord) -> ExperimentRecord:
        data = record.model_dump(mode="json")
        res = self.client.table("experiments").insert(data).execute()
        if not res.data:
            raise RuntimeError(f"Failed to insert experiment: {res}")
        return ExperimentRecord(**res.data[0])

    async def get(self, experiment_id: UUID) -> Optional[ExperimentRecord]:
        res = self.client.table("experiments").select("*").eq("id", str(experiment_id)).execute()
        if not res.data:
            return None
        return ExperimentRecord(**res.data[0])

    async def update(self, record: ExperimentRecord) -> ExperimentRecord:
        data = record.model_dump(mode="json")
        res = self.client.table("experiments").update(data).eq("id", str(record.id)).execute()
        if not res.data:
            raise RuntimeError(f"Failed to update experiment: {res}")
        return ExperimentRecord(**res.data[0])

    async def list_all(self) -> List[ExperimentRecord]:
        res = self.client.table("experiments").select("*").order("created_at", desc=True).execute()
        return [ExperimentRecord(**item) for item in res.data]


class SupabaseAgentVersionRepository(AgentVersionRepository):
    """Supabase-backed repository for immutable agent versions."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    async def create(self, record: AgentVersionRecord) -> AgentVersionRecord:
        data = record.model_dump(mode="json", by_alias=True)
        res = self.client.table("agent_versions").insert(data).execute()
        if not res.data:
            raise RuntimeError(f"Failed to insert agent version: {res}")
        return AgentVersionRecord(**res.data[0])

    async def get(self, version_id: UUID) -> Optional[AgentVersionRecord]:
        res = self.client.table("agent_versions").select("*").eq("id", str(version_id)).execute()
        if not res.data:
            return None
        return AgentVersionRecord(**res.data[0])

    async def get_by_version_number(self, experiment_id: UUID, version_number: int) -> Optional[AgentVersionRecord]:
        res = (
            self.client.table("agent_versions")
            .select("*")
            .eq("experiment_id", str(experiment_id))
            .eq("version_number", version_number)
            .execute()
        )
        if not res.data:
            return None
        return AgentVersionRecord(**res.data[0])

    async def list_for_experiment(self, experiment_id: UUID) -> List[AgentVersionRecord]:
        res = (
            self.client.table("agent_versions")
            .select("*")
            .eq("experiment_id", str(experiment_id))
            .order("version_number")
            .execute()
        )
        return [AgentVersionRecord(**item) for item in res.data]

    async def update_status(self, version_id: UUID, status: str) -> Optional[AgentVersionRecord]:
        res = (
            self.client.table("agent_versions")
            .update({"status": status})
            .eq("id", str(version_id))
            .execute()
        )
        if not res.data:
            return None
        return AgentVersionRecord(**res.data[0])


class SupabaseToolRepository(ToolRepository):
    """Supabase-backed repository for tools."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    async def create(self, record: ToolRecord) -> ToolRecord:
        data = record.model_dump(mode="json")
        res = self.client.table("tools").insert(data).execute()
        if not res.data:
            raise RuntimeError(f"Failed to insert tool: {res}")
        return ToolRecord(**res.data[0])

    async def get(self, tool_id: UUID) -> Optional[ToolRecord]:
        res = self.client.table("tools").select("*").eq("id", str(tool_id)).execute()
        if not res.data:
            return None
        return ToolRecord(**res.data[0])

    async def get_by_name(self, name: str) -> Optional[ToolRecord]:
        res = self.client.table("tools").select("*").eq("name", name).execute()
        if not res.data:
            return None
        return ToolRecord(**res.data[0])

    async def list_active(self) -> List[ToolRecord]:
        res = self.client.table("tools").select("*").eq("enabled", True).execute()
        return [ToolRecord(**item) for item in res.data]


class SupabaseBenchmarkCaseRepository(BenchmarkCaseRepository):
    """Supabase-backed repository for benchmark cases."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    async def create(self, record: BenchmarkCaseRecord) -> BenchmarkCaseRecord:
        data = record.model_dump(mode="json")
        res = self.client.table("benchmark_cases").insert(data).execute()
        if not res.data:
            raise RuntimeError(f"Failed to insert benchmark case: {res}")
        return BenchmarkCaseRecord(**res.data[0])

    async def get(self, case_id: UUID) -> Optional[BenchmarkCaseRecord]:
        res = self.client.table("benchmark_cases").select("*").eq("id", str(case_id)).execute()
        if not res.data:
            return None
        return BenchmarkCaseRecord(**res.data[0])

    async def get_by_code(self, case_code: str) -> Optional[BenchmarkCaseRecord]:
        res = self.client.table("benchmark_cases").select("*").eq("case_code", case_code).execute()
        if not res.data:
            return None
        return BenchmarkCaseRecord(**res.data[0])

    async def list_by_split(self, benchmark_name: str, split: str) -> List[BenchmarkCaseRecord]:
        res = (
            self.client.table("benchmark_cases")
            .select("*")
            .eq("benchmark_name", benchmark_name)
            .eq("split", split)
            .execute()
        )
        return [BenchmarkCaseRecord(**item) for item in res.data]

    async def bulk_create(self, records: List[BenchmarkCaseRecord]) -> List[BenchmarkCaseRecord]:
        data = [r.model_dump(mode="json") for r in records]
        res = self.client.table("benchmark_cases").insert(data).execute()
        return [BenchmarkCaseRecord(**item) for item in res.data]


class SupabaseBenchmarkRunRepository(BenchmarkRunRepository):
    """Supabase-backed repository for benchmark runs."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    async def create(self, record: BenchmarkRunRecord) -> BenchmarkRunRecord:
        data = record.model_dump(mode="json")
        res = self.client.table("benchmark_runs").insert(data).execute()
        return BenchmarkRunRecord(**res.data[0])

    async def get(self, run_id: UUID) -> Optional[BenchmarkRunRecord]:
        res = self.client.table("benchmark_runs").select("*").eq("id", str(run_id)).execute()
        if not res.data:
            return None
        return BenchmarkRunRecord(**res.data[0])

    async def list_for_version(self, agent_version_id: UUID) -> List[BenchmarkRunRecord]:
        res = (
            self.client.table("benchmark_runs")
            .select("*")
            .eq("agent_version_id", str(agent_version_id))
            .execute()
        )
        return [BenchmarkRunRecord(**item) for item in res.data]

    async def list_for_experiment(self, experiment_id: UUID) -> List[BenchmarkRunRecord]:
        res = (
            self.client.table("benchmark_runs")
            .select("*")
            .eq("experiment_id", str(experiment_id))
            .execute()
        )
        return [BenchmarkRunRecord(**item) for item in res.data]


class SupabaseCaseExecutionRepository(CaseExecutionRepository):
    """Supabase-backed repository for case executions."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    async def create(self, record: CaseExecutionRecord) -> CaseExecutionRecord:
        data = record.model_dump(mode="json")
        res = self.client.table("case_executions").insert(data).execute()
        return CaseExecutionRecord(**res.data[0])

    async def get(self, execution_id: UUID) -> Optional[CaseExecutionRecord]:
        res = self.client.table("case_executions").select("*").eq("id", str(execution_id)).execute()
        if not res.data:
            return None
        return CaseExecutionRecord(**res.data[0])

    async def list_for_run(self, benchmark_run_id: UUID) -> List[CaseExecutionRecord]:
        res = (
            self.client.table("case_executions")
            .select("*")
            .eq("benchmark_run_id", str(benchmark_run_id))
            .execute()
        )
        return [CaseExecutionRecord(**item) for item in res.data]


class SupabaseFailureDiagnosisRepository(FailureDiagnosisRepository):
    """Supabase-backed repository for failure diagnoses."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    async def create(self, record: FailureDiagnosisRecord) -> FailureDiagnosisRecord:
        data = record.model_dump(mode="json")
        res = self.client.table("failure_diagnoses").insert(data).execute()
        return FailureDiagnosisRecord(**res.data[0])

    async def get(self, diagnosis_id: UUID) -> Optional[FailureDiagnosisRecord]:
        res = self.client.table("failure_diagnoses").select("*").eq("id", str(diagnosis_id)).execute()
        if not res.data:
            return None
        return FailureDiagnosisRecord(**res.data[0])

    async def get_for_case_execution(self, case_execution_id: UUID) -> Optional[FailureDiagnosisRecord]:
        res = (
            self.client.table("failure_diagnoses")
            .select("*")
            .eq("case_execution_id", str(case_execution_id))
            .execute()
        )
        if not res.data:
            return None
        return FailureDiagnosisRecord(**res.data[0])


class SupabaseImprovementRepository(ImprovementRepository):
    """Supabase-backed repository for improvements."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    async def create(self, record: ImprovementRecord) -> ImprovementRecord:
        data = record.model_dump(mode="json")
        res = self.client.table("improvements").insert(data).execute()
        return ImprovementRecord(**res.data[0])

    async def get(self, improvement_id: UUID) -> Optional[ImprovementRecord]:
        res = self.client.table("improvements").select("*").eq("id", str(improvement_id)).execute()
        if not res.data:
            return None
        return ImprovementRecord(**res.data[0])

    async def list_for_experiment(self, experiment_id: UUID) -> List[ImprovementRecord]:
        res = (
            self.client.table("improvements")
            .select("*")
            .eq("experiment_id", str(experiment_id))
            .order("created_at")
            .execute()
        )
        return [ImprovementRecord(**item) for item in res.data]


class SupabaseDatabase:
    """Unified container for all Supabase-backed repositories."""

    def __init__(self, client: Optional[Client] = None):
        self.experiments = SupabaseExperimentRepository(client)
        self.agent_versions = SupabaseAgentVersionRepository(client)
        self.tools = SupabaseToolRepository(client)
        self.benchmark_cases = SupabaseBenchmarkCaseRepository(client)
        self.benchmark_runs = SupabaseBenchmarkRunRepository(client)
        self.case_executions = SupabaseCaseExecutionRepository(client)
        self.failure_diagnoses = SupabaseFailureDiagnosisRepository(client)
        self.improvements = SupabaseImprovementRepository(client)
