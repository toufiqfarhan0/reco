"""Static pre-flight validation pipeline for candidate agent architectures."""

from collections import deque
from typing import Any, Dict, List, Optional, Set
from reco.core.task_spec import TaskSpecification
from reco.engine.generator import (
    MAX_EDGE_COUNT,
    MAX_GRAPH_DEPTH,
    MAX_NODE_COUNT,
    ArchitectureValidationResult,
)
from reco.engine.models import GraphDefinition, GraphValidationError
from reco.mutation.models import AgentVersionCandidate
from reco.tools.registry import ToolRegistry


class CandidateValidator:
    """Performs comprehensive static verification on candidate agent versions before benchmark execution."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry

    def validate(
        self,
        candidate: AgentVersionCandidate,
        task_spec: Optional[TaskSpecification] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ArchitectureValidationResult:
        """Execute all static pre-flight validation checks."""
        errors: List[str] = []
        warnings: List[str] = []
        graph = candidate.graph

        # 1. Topological & DAG Invariants (Kahn's algorithm, acyclicity, reachability)
        try:
            graph.validate_graph()
        except GraphValidationError as ve:
            errors.append(f"DAG structural validation failed: {ve}")

        # 2. Graph Complexity Boundaries
        node_count = len(graph.nodes)
        edge_count = len(graph.edges)
        if node_count > MAX_NODE_COUNT:
            errors.append(f"Node count ({node_count}) exceeds limit of {MAX_NODE_COUNT}.")
        if edge_count > MAX_EDGE_COUNT:
            errors.append(f"Edge count ({edge_count}) exceeds limit of {MAX_EDGE_COUNT}.")

        depth = 0
        if not errors:
            depth = self._calculate_max_depth(graph)
            if depth > MAX_GRAPH_DEPTH:
                errors.append(f"Graph depth ({depth}) exceeds limit of {MAX_GRAPH_DEPTH}.")

        # 3. Tool Authorization & Anti-Fabrication Check
        known_tools: Set[str] = set()
        if self.tool_registry:
            known_tools.update(t.name for t in self.tool_registry.list_tools())
        if available_tools:
            for t in available_tools:
                if isinstance(t, dict) and "name" in t:
                    known_tools.add(t["name"])
                elif hasattr(t, "name"):
                    known_tools.add(t.name)

        if known_tools:
            for node_id, node in graph.nodes.items():
                for tool_name in node.tools:
                    if tool_name not in known_tools:
                        errors.append(
                            f"Unauthorized or fabricated tool '{tool_name}' on node '{node_id}'. "
                            "Every assigned tool must exist in ToolRegistry."
                        )

        # 4. Capability Coverage
        if task_spec and task_spec.required_tools:
            assigned_tools = {t for node in graph.nodes.values() for t in node.tools}
            missing_tools = [rt for rt in task_spec.required_tools if rt not in assigned_tools]
            if missing_tools:
                errors.append(f"Missing mandatory task capabilities: tools {missing_tools} are not assigned.")

        # 5. Mutation Target Validation
        target = candidate.mutation.target
        # Target should refer to an existing node, tool, or edge
        if target not in graph.nodes and target not in known_tools and not any(e.source_node_id == target or e.target_node_id == target for e in graph.edges):
            warnings.append(f"Mutation target '{target}' is not an active node or edge in candidate graph.")

        # 6. Context & Input Mapping Invariants
        available_keys = {"records", "entries", "bank_records", "ledger_entries", "input", "inputs"}
        for node in graph.nodes.values():
            if node.output_key:
                available_keys.add(node.output_key)
            available_keys.add(node.node_id)

        # 7. Verification Invariants
        if task_spec and task_spec.requires_verification:
            has_verifier = any(
                "audit" in n.role.lower() or "verif" in n.role.lower() or "audit" in n.node_id.lower() or "verif" in n.node_id.lower()
                for n in graph.nodes.values()
            )
            if not has_verifier:
                warnings.append("Task specification recommends verification, but graph lacks an audit/verification node.")

        # Construct result
        is_valid = len(errors) == 0
        val_result = ArchitectureValidationResult(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            metrics={
                "node_count": node_count,
                "edge_count": edge_count,
                "max_depth": depth,
            },
        )

        candidate.validation_result = val_result
        candidate.is_valid = is_valid
        if not is_valid:
            candidate.rejection_reason = "; ".join(errors)

        return val_result

    def _calculate_max_depth(self, graph: GraphDefinition) -> int:
        """Compute longest path depth from entry node."""
        if not graph.entry_node_id or graph.entry_node_id not in graph.nodes:
            return 0
        adj: Dict[str, List[str]] = {nid: [] for nid in graph.nodes}
        for e in graph.edges:
            if e.source_node_id in adj:
                adj[e.source_node_id].append(e.target_node_id)

        distances: Dict[str, int] = {nid: 0 for nid in graph.nodes}
        distances[graph.entry_node_id] = 1
        queue = deque([graph.entry_node_id])
        visited_count = 0
        max_bound = max(len(graph.nodes) * 2, 20)

        while queue and visited_count < max_bound:
            curr = queue.popleft()
            visited_count += 1
            curr_dist = distances[curr]
            if curr_dist > len(graph.nodes):
                return len(graph.nodes) + 1
            for neighbor in adj.get(curr, []):
                if distances[neighbor] < curr_dist + 1:
                    distances[neighbor] = curr_dist + 1
                    queue.append(neighbor)

        return max(distances.values()) if distances else 0
