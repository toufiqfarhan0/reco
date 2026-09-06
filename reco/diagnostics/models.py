"""Data models for root cause diagnoses, structured evidence, mutation recommendations, and failure clusters."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from reco.db.models import FailureDiagnosisRecord
from reco.diagnostics.taxonomy import FailureCategory, FailureSource, MutationType, Severity


class DiagnosisEvidence(BaseModel):
    """Structured, verifiable evidence trace supporting a root cause diagnosis."""
    source: str = Field(..., description="Evidence origin (e.g., 'tool_event', 'benchmark_ground_truth', 'node_execution')")
    tool: Optional[str] = Field(default=None, description="Name of relevant tool if applicable")
    field: Optional[str] = Field(default=None, description="Target field, parameter, or state key")
    observed: Optional[Any] = Field(default=None, description="Observed runtime value, exception, or state")
    expected: Optional[Any] = Field(default=None, description="Expected ground-truth or invariant value")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional contextual telemetry")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RecommendedMutation(BaseModel):
    """Structured recommendation for future agent optimizer iterations."""
    mutation_type: MutationType = Field(..., description="Targeted architectural or configuration mutation")
    target: str = Field(..., description="Referenced entity: node ID, tool name, edge, or config parameter")
    rationale: str = Field(..., description="Diagnostic justification explaining why this mutation addresses the root cause")
    expected_effect: str = Field(..., description="Expected performance, reliability, or accuracy improvement")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Diagnostic confidence in this recommendation")
    evidence_refs: List[str] = Field(default_factory=list, description="References to supporting evidence items")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class EvidenceList(list):
    """List of DiagnosisEvidence supporting string methods like lower()."""
    def lower(self) -> str:
        parts = []
        for item in self:
            if isinstance(item, DiagnosisEvidence):
                parts.extend([str(item.source), str(item.field or ""), str(item.observed or ""), str(item.expected or ""), str(item.details or "")])
            else:
                parts.append(str(item))
        return " ".join(parts).lower()


class RootCauseDiagnosis(BaseModel):
    """Strongly typed root cause diagnosis produced by the Failure Analyzer."""
    diagnosis_id: UUID = Field(default_factory=uuid4)
    execution_id: Optional[UUID] = None
    case_execution_id: Optional[UUID] = None
    failure_category: FailureCategory
    severity: Severity = Severity.MEDIUM
    failed_node_id: Optional[str] = None
    failure_source: FailureSource = FailureSource.NODE_EXECUTION
    symptom: str = Field(default="", description="Observable external error, incorrect output, or mismatch")
    summary: str = Field(default="", description="Concise diagnostic summary")
    root_cause: str = Field(default="", description="Underlying architectural, logical, or tool defect")
    evidence: Any = Field(default_factory=EvidenceList)
    contributing_factors: List[str] = Field(default_factory=list)
    confidence: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
        description="Bounded diagnostic confidence score (0.0 to 1.0); NOT a calibrated probability",
    )
    recommended_mutations: List[RecommendedMutation] = Field(default_factory=list)
    affected_capabilities: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _normalize_diagnosis_input(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "failure_category" not in data and "category" in data:
                cat_val = data["category"]
                if isinstance(cat_val, str):
                    try:
                        data["failure_category"] = FailureCategory(cat_val)
                    except ValueError:
                        data["failure_category"] = FailureCategory.UNKNOWN_FAILURE
                else:
                    data["failure_category"] = cat_val
            if "severity" in data and isinstance(data["severity"], str):
                try:
                    data["severity"] = Severity(data["severity"].lower())
                except ValueError:
                    data["severity"] = Severity.HIGH
            if "failed_node_id" not in data and "failed_node" in data:
                data["failed_node_id"] = data["failed_node"]
            if "symptom" not in data or not data["symptom"]:
                data["symptom"] = data.get("root_cause") or data.get("summary") or "Diagnostic failure observed"
            if "summary" not in data or not data["summary"]:
                data["summary"] = data.get("root_cause") or data.get("symptom") or "Failure analyzed"
            if "root_cause" not in data or not data["root_cause"]:
                data["root_cause"] = data.get("summary") or data.get("symptom") or "Unknown root cause"
            if "confidence" not in data:
                data["confidence"] = 0.90

            # Normalize evidence
            raw_ev = data.get("evidence")
            ev_list = EvidenceList()
            if isinstance(raw_ev, str):
                ev_list.append(DiagnosisEvidence(source="diagnostic_evidence", observed=raw_ev))
            elif isinstance(raw_ev, list):
                for item in raw_ev:
                    if isinstance(item, DiagnosisEvidence):
                        ev_list.append(item)
                    elif isinstance(item, dict):
                        ev_list.append(DiagnosisEvidence(**item))
                    else:
                        ev_list.append(DiagnosisEvidence(source="evidence_item", observed=str(item)))
            data["evidence"] = ev_list

            # Normalize recommended_mutation
            rec_mut = data.get("recommended_mutation")
            if rec_mut:
                mut_type = MutationType(rec_mut) if isinstance(rec_mut, str) else rec_mut
                target_node = data.get("failed_node_id") or "target_node"
                data["recommended_mutations"] = [
                    RecommendedMutation(
                        mutation_type=mut_type,
                        target=target_node,
                        rationale=data.get("root_cause", ""),
                        expected_effect="Addresses diagnostic root cause",
                        confidence=data.get("confidence", 0.90),
                    )
                ]
            if "case_code" in data:
                if "metadata" not in data:
                    data["metadata"] = {}
                data["metadata"]["case_code"] = data["case_code"]
        return data

    @property
    def category(self) -> str:
        return self.failure_category.value if hasattr(self.failure_category, "value") else str(self.failure_category)

    @property
    def failed_node(self) -> Optional[str]:
        return self.failed_node_id

    @property
    def recommended_mutation(self) -> str:
        if self.recommended_mutations:
            m = self.recommended_mutations[0].mutation_type
            return m.value if hasattr(m, "value") else str(m)
        return "PROMPT_CHANGE"

    @field_validator("confidence")
    @classmethod
    def validate_bounded_confidence(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("Confidence must be a bounded value between 0.0 and 1.0")
        return round(v, 4)

    def to_db_record(self) -> FailureDiagnosisRecord:
        """Convert this diagnosis to the database persistence model."""
        target_case_execution_id = self.case_execution_id or self.execution_id or uuid4()
        return FailureDiagnosisRecord(
            id=self.diagnosis_id,
            case_execution_id=target_case_execution_id,
            category=self.failure_category.value,
            severity=self.severity.value,
            root_cause=self.root_cause,
            evidence={
                "symptom": self.symptom,
                "summary": self.summary,
                "failed_node_id": self.failed_node_id,
                "failure_source": self.failure_source.value,
                "contributing_factors": self.contributing_factors,
                "confidence": self.confidence,
                "affected_capabilities": self.affected_capabilities,
                "items": [e.model_dump(mode="json") for e in self.evidence],
                "metadata": self.metadata,
            },
            recommended_mutations=[m.model_dump(mode="json") for m in self.recommended_mutations],
            created_at=self.created_at,
        )

    @classmethod
    def from_db_record(cls, record: FailureDiagnosisRecord) -> "RootCauseDiagnosis":
        """Reconstruct a RootCauseDiagnosis from a stored database record."""
        raw_evidence = record.evidence or {}
        items = raw_evidence.get("items", [])
        evidence_list = [DiagnosisEvidence(**item) for item in items]
        mutations = [RecommendedMutation(**m) for m in record.recommended_mutations or []]

        # Parse category safely
        cat_str = record.category
        try:
            category = FailureCategory(cat_str)
        except ValueError:
            category = FailureCategory.UNKNOWN_FAILURE

        try:
            sev = Severity(record.severity)
        except ValueError:
            sev = Severity.MEDIUM

        raw_source = raw_evidence.get("failure_source", FailureSource.NODE_EXECUTION.value)
        try:
            source = FailureSource(raw_source)
        except ValueError:
            source = FailureSource.NODE_EXECUTION

        return cls(
            diagnosis_id=record.id,
            case_execution_id=record.case_execution_id,
            failure_category=category,
            severity=sev,
            failed_node_id=raw_evidence.get("failed_node_id"),
            failure_source=source,
            symptom=raw_evidence.get("symptom", "Execution failure observed"),
            summary=raw_evidence.get("summary", record.root_cause),
            root_cause=record.root_cause,
            evidence=evidence_list,
            contributing_factors=raw_evidence.get("contributing_factors", []),
            confidence=float(raw_evidence.get("confidence", 0.5)),
            recommended_mutations=mutations,
            affected_capabilities=raw_evidence.get("affected_capabilities", []),
            metadata=raw_evidence.get("metadata", {}),
            created_at=record.created_at,
        )


class FailureCluster(BaseModel):
    """Deterministic cluster of related diagnoses sharing structural or causal patterns."""
    cluster_id: str
    category: FailureCategory
    root_cause_pattern: str
    count: int = Field(default=0, ge=0)
    diagnoses: List[RootCauseDiagnosis] = Field(default_factory=list)
    priority_score: float = Field(default=0.0, ge=0.0, description="Interpretable prioritization score")
    affected_nodes: List[str] = Field(default_factory=list)
    recommended_mutations: List[RecommendedMutation] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)
