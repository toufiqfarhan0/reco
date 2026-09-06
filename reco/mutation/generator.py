"""CandidateGenerator synthesizes targeted MutationCandidate objects from diagnoses and failure clusters."""

from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4

from reco.core.task_spec import TaskSpecification
from reco.db.models import AgentVersionRecord
from reco.diagnostics.models import FailureCluster, RecommendedMutation, RootCauseDiagnosis
from reco.diagnostics.taxonomy import MutationType
from reco.engine.models import GraphDefinition
from reco.logging import get_logger
from reco.mutation.models import MutationCandidate
from reco.tools.registry import ToolRegistry

logger = get_logger("mutation.generator")

DEFAULT_MAX_CANDIDATES = 3


class CandidateGenerator:
    """Generates a bounded set of targeted mutation candidates guided by prioritized failure clusters."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry

    def generate(
        self,
        agent_graph: GraphDefinition,
        diagnoses: List[RootCauseDiagnosis],
        task_specification: Optional[TaskSpecification] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        parent_version_id: Optional[UUID] = None,
        max_candidates: int = DEFAULT_MAX_CANDIDATES,
        clusters: Optional[List[FailureCluster]] = None,
        synthesize_alternatives: bool = False,
    ) -> List[MutationCandidate]:
        """Generate up to max_candidates targeted mutation specifications.

        Priority strategy:
        1. Explores recommendations from top-priority failure clusters first.
        2. Validates that targets exist in the graph before proposing a candidate.
        3. Enforces single-focus mutations for clear attribution.
        4. Strictly adheres to registered tools (no fabricated tools).
        """
        candidates: List[MutationCandidate] = []
        seen_signatures: Set[str] = set()

        # Build list of valid tools
        registered_tools: Set[str] = set()
        if self.tool_registry:
            registered_tools.update(t.name for t in self.tool_registry.list_tools())
        if available_tools:
            for t in available_tools:
                if isinstance(t, dict) and "name" in t:
                    registered_tools.add(t["name"])
                elif hasattr(t, "name"):
                    registered_tools.add(t.name)

        # 1. Order recommendations: if clusters provided, walk clusters descending by priority_score
        recommendation_tuples: List[tuple[RecommendedMutation, List[UUID], float]] = []

        if clusters:
            # Sort clusters descending by priority score
            sorted_clusters = sorted(clusters, key=lambda c: (c.priority_score, c.count), reverse=True)
            for cl in sorted_clusters:
                cl_diag_ids = [d.diagnosis_id for d in cl.diagnoses]
                for rec in cl.recommended_mutations:
                    recommendation_tuples.append((rec, cl_diag_ids, cl.priority_score))

        # Also incorporate individual high-confidence diagnoses
        for diag in diagnoses:
            if diag is None:
                continue
            diag_score = diag.confidence * 2.0
            for rec in diag.recommended_mutations:
                recommendation_tuples.append((rec, [diag.diagnosis_id], diag_score))

        # Sort combined recommendations by score descending
        recommendation_tuples.sort(key=lambda t: t[2], reverse=True)

        effective_max = min(max_candidates, DEFAULT_MAX_CANDIDATES)
        candidate_pool: List[MutationCandidate] = []
        seen_signatures: Set[str] = set()

        for rec, source_ids, score in recommendation_tuples:
            target = rec.target
            # Validate target exists in graph
            if target != "graph" and target not in agent_graph.nodes:
                # If target not in graph, check if it can be assigned to the terminal or first node
                if agent_graph.nodes:
                    target = list(agent_graph.nodes.keys())[-1]
                else:
                    continue

            # Validate tool existence if TOOL_ADD
            if rec.mutation_type == MutationType.TOOL_ADD:
                # Extract requested tool name
                tool_name = rec.metadata.get("tool_name") if hasattr(rec, "metadata") else None
                if not tool_name:
                    # Look for tool name mentioned in rationale
                    for t in registered_tools:
                        if t.lower() in rec.rationale.lower():
                            tool_name = t
                            break
                if not tool_name:
                    # Default to calculate_reconciliation_difference or first registered tool
                    tool_name = "calculate_reconciliation_difference" if "calculate_reconciliation_difference" in registered_tools else None

                if not tool_name or (registered_tools and tool_name not in registered_tools):
                    # Skip if tool is unregistered / fabricated
                    continue

            # Build proposed change payload
            proposed_change: Dict[str, Any] = {}
            if rec.mutation_type == MutationType.PROMPT_CHANGE:
                proposed_change = {
                    "append": rec.rationale,
                    "target_node": target,
                }
            elif rec.mutation_type == MutationType.TOOL_ADD:
                proposed_change = {
                    "tool_name": tool_name,
                    "target_node": target,
                }
            elif rec.mutation_type == MutationType.TOOL_REMOVE:
                node_tools = agent_graph.nodes[target].tools if target in agent_graph.nodes else []
                tool_to_remove = node_tools[0] if node_tools else None
                if not tool_to_remove:
                    continue
                proposed_change = {"tool_name": tool_to_remove}
            elif rec.mutation_type == MutationType.TOOL_REORDER:
                node_tools = agent_graph.nodes[target].tools if target in agent_graph.nodes else []
                if len(node_tools) < 2:
                    continue
                proposed_change = {"tools": list(reversed(node_tools))}
            elif rec.mutation_type == MutationType.ADD_VERIFIER:
                proposed_change = {
                    "node_id": f"{target}_auditor",
                    "name": "Reconciliation Auditor",
                    "role": "Auditor",
                    "system_prompt": f"Audit and verify outputs from '{target}' against business constraints.",
                }
            elif rec.mutation_type == MutationType.TOPOLOGY_CHANGE:
                proposed_change = {
                    "operation": "insert_node",
                    "node": {
                        "node_id": f"{target}_analyzer",
                        "name": "Discrepancy Analyzer",
                        "role": "Analyzer",
                        "system_prompt": "Decompose variances and analyze exception types.",
                        "tools": [],
                    },
                    "inbound_from": [target],
                }
            elif rec.mutation_type == MutationType.MODEL_CHANGE:
                proposed_change = {
                    "model_config": {"model": "mock-reasoning-v1", "temperature": 0.0}
                }
            elif rec.mutation_type == MutationType.RETRY_POLICY_CHANGE:
                proposed_change = {
                    "max_retries": 2,
                    "retryable_errors": ["transient_error", "timeout"],
                }
            elif rec.mutation_type == MutationType.CONTEXT_CHANGE:
                proposed_change = {
                    "input_mapping": {"discrepancies": "reconciliation_summary"},
                    "merge": True,
                }
            elif rec.mutation_type == MutationType.ROUTING_CHANGE:
                proposed_change = {
                    "source": target,
                    "condition": "has_discrepancy == True",
                }
            else:
                continue

            sig = f"{rec.mutation_type.value}:{target}:{str(proposed_change)}"
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)

            cand = MutationCandidate(
                candidate_id=uuid4(),
                mutation_type=rec.mutation_type,
                target=target,
                proposed_change=proposed_change,
                rationale=rec.rationale,
                source_diagnosis_ids=source_ids,
                expected_effect=rec.expected_effect,
                confidence=rec.confidence,
                risk_level="low",
                parent_version_id=parent_version_id,
                metadata={"priority_score": score},
            )
            candidate_pool.append(cand)

        # Diverse alternative synthesis if requested or when multiple diagnoses/clusters are present and pool is below effective_max
        should_synthesize = synthesize_alternatives or (clusters is not None and len(clusters) > 0) or (len(diagnoses) > 1)
        if should_synthesize and len(candidate_pool) < effective_max and diagnoses and agent_graph.nodes:
            primary_target = list(agent_graph.nodes.keys())[-1]
            for nid in agent_graph.nodes:
                if "match" in nid.lower() or "verif" in nid.lower():
                    primary_target = nid
                    break
            diag_ids = [d.diagnosis_id for d in diagnoses]
            pool_types = {c.mutation_type for c in candidate_pool}

            # Alternative 1: Prompt clarification if not already present
            if MutationType.PROMPT_CHANGE not in pool_types and len(candidate_pool) < effective_max:
                cand = MutationCandidate(
                    candidate_id=uuid4(),
                    mutation_type=MutationType.PROMPT_CHANGE,
                    target=primary_target,
                    proposed_change={"append": "Refine verification checks and ensure complete isolation of discrepancies."},
                    rationale="Exploratory prompt refinement targeting unclassified failures.",
                    source_diagnosis_ids=diag_ids,
                    expected_effect="Improves exception discrimination on unclassified discrepancy cases.",
                    confidence=0.70,
                    risk_level="low",
                    parent_version_id=parent_version_id,
                    metadata={"priority_score": 1.0},
                )
                candidate_pool.append(cand)
                pool_types.add(MutationType.PROMPT_CHANGE)

            # Alternative 2: Add verifier if not already present
            if MutationType.ADD_VERIFIER not in pool_types and len(candidate_pool) < effective_max:
                cand = MutationCandidate(
                    candidate_id=uuid4(),
                    mutation_type=MutationType.ADD_VERIFIER,
                    target=primary_target,
                    proposed_change={
                        "node_id": f"{primary_target}_auditor",
                        "name": "Reconciliation Auditor",
                        "role": "Auditor",
                        "system_prompt": f"Audit and verify outputs from '{primary_target}' against business constraints.",
                    },
                    rationale=f"Add secondary audit verification node to eliminate unverified matches from '{primary_target}'.",
                    source_diagnosis_ids=diag_ids,
                    expected_effect="Eliminates false-positive reconciliation matches via independent secondary audit.",
                    confidence=0.75,
                    risk_level="low",
                    parent_version_id=parent_version_id,
                    metadata={"priority_score": 1.2},
                )
                candidate_pool.append(cand)
                pool_types.add(MutationType.ADD_VERIFIER)

            # Alternative 3: Tool enhancement if not already present
            calc_tool = "calculate_reconciliation_difference"
            if MutationType.TOOL_ADD not in pool_types and len(candidate_pool) < effective_max and (not registered_tools or calc_tool in registered_tools):
                cand = MutationCandidate(
                    candidate_id=uuid4(),
                    mutation_type=MutationType.TOOL_ADD,
                    target=primary_target,
                    proposed_change={
                        "tool_name": calc_tool,
                        "target_node": primary_target,
                    },
                    rationale=f"Equip '{primary_target}' with arithmetic verification tool to eliminate tolerance discrepancies.",
                    source_diagnosis_ids=diag_ids,
                    expected_effect="Allows deterministic mathematical verification of amounts.",
                    confidence=0.70,
                    risk_level="low",
                    parent_version_id=parent_version_id,
                    metadata={"priority_score": 1.1},
                )
                candidate_pool.append(cand)
                pool_types.add(MutationType.TOOL_ADD)

        # Diversity-First Selection:
        # Pass 1: Select candidates with distinct mutation types
        selected: List[MutationCandidate] = []
        selected_types: Set[MutationType] = set()

        for cand in candidate_pool:
            if cand.mutation_type not in selected_types:
                selected.append(cand)
                selected_types.add(cand.mutation_type)
                if len(selected) >= effective_max:
                    break

        # Pass 2: If slots remain, select remaining highest-scoring candidates
        if len(selected) < effective_max:
            for cand in candidate_pool:
                if cand not in selected:
                    selected.append(cand)
                    if len(selected) >= effective_max:
                        break

        return selected[:effective_max]
