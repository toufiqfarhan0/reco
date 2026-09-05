"""Candidate DAG Validator and Architectural Diff Generator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from reco.engine.models import AgentArchitecture, EdgeSpec, NodeSpec, NodeType
from reco.tools.registry import ToolRegistry


class CandidateDiff(BaseModel):
    """Detailed structural and configuration delta between baseline and candidate architectures."""

    baseline_id: str = Field(description="Parent baseline architecture ID")
    candidate_id: str = Field(description="Mutated candidate architecture ID")
    added_nodes: List[str] = Field(default_factory=list, description="IDs of newly introduced nodes")
    removed_nodes: List[str] = Field(default_factory=list, description="IDs of pruned nodes")
    modified_nodes: List[str] = Field(default_factory=list, description="IDs of altered nodes")
    added_edges: List[str] = Field(default_factory=list, description="New directed edges (src -> tgt)")
    removed_edges: List[str] = Field(default_factory=list, description="Removed directed edges (src -> tgt)")
    node_details: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Attribute-level modifications per node"
    )

    def has_changes(self) -> bool:
        """Return True if any structural or config modification occurred."""
        return bool(
            self.added_nodes
            or self.removed_nodes
            or self.modified_nodes
            or self.added_edges
            or self.removed_edges
        )

    def to_visual_diff(self) -> str:
        """Render a readable visual representation of the mutation diff."""
        lines = [
            "==================================================",
            f"ARCHITECTURE MUTATION DIFF: {self.baseline_id} -> {self.candidate_id}",
            "==================================================",
        ]

        if not self.has_changes():
            lines.append("  (No structural or configuration changes detected)")
            return "\n".join(lines)

        if self.added_nodes:
            lines.append("  [+] ADDED NODES:")
            for nid in self.added_nodes:
                detail = self.node_details.get(nid, {})
                ntype = detail.get("type", "unknown")
                tool = detail.get("tool_name")
                tool_str = f" [tool: {tool}]" if tool else ""
                lines.append(f"      + {nid} ({ntype}){tool_str}")

        if self.removed_nodes:
            lines.append("  [-] REMOVED NODES:")
            for nid in self.removed_nodes:
                lines.append(f"      - {nid}")

        if self.modified_nodes:
            lines.append("  [*] MODIFIED NODES:")
            for nid in self.modified_nodes:
                detail = self.node_details.get(nid, {})
                changes = detail.get("changes", [])
                lines.append(f"      * {nid}: {', '.join(changes)}")

        if self.added_edges:
            lines.append("  [+] ADDED EDGES:")
            for e in self.added_edges:
                lines.append(f"      + {e}")

        if self.removed_edges:
            lines.append("  [-] REMOVED EDGES:")
            for e in self.removed_edges:
                lines.append(f"      - {e}")

        lines.append("==================================================")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Render markdown representation of the mutation diff."""
        lines = [
            f"#### Architectural Diff: `{self.baseline_id}` -> `{self.candidate_id}`",
            "",
            "| Delta Type | Count | Elements |",
            "| :--- | :--- | :--- |",
            f"| **Added Nodes** | {len(self.added_nodes)} | {', '.join(f'`{n}`' for n in self.added_nodes) or 'None'} |",
            f"| **Removed Nodes** | {len(self.removed_nodes)} | {', '.join(f'`{n}`' for n in self.removed_nodes) or 'None'} |",
            f"| **Modified Nodes** | {len(self.modified_nodes)} | {', '.join(f'`{n}`' for n in self.modified_nodes) or 'None'} |",
            f"| **Added Edges** | {len(self.added_edges)} | {', '.join(f'`{e}`' for e in self.added_edges) or 'None'} |",
            f"| **Removed Edges** | {len(self.removed_edges)} | {', '.join(f'`{e}`' for e in self.removed_edges) or 'None'} |",
            ""
        ]
        return "\n".join(lines)


class ValidationResult(BaseModel):
    """Validation outcome assessing structural integrity and tool authenticity."""

    is_valid: bool = Field(description="True if all DAG and tool constraints pass")
    errors: List[str] = Field(default_factory=list, description="Fatal validation error messages")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warning notices")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Complexity and connectivity metrics")


class CandidateValidator:
    """Validates DAG acyclicity, connectivity, contracts, and strictly rejects hallucinated tools."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry or ToolRegistry.create_reconciliation_default()

    def validate(
        self,
        architecture: AgentArchitecture,
        tool_registry: Optional[ToolRegistry] = None
    ) -> ValidationResult:
        """Validate acyclicity, connectivity, and strictly reject hallucinated tools.

        Args:
            architecture: The mutated candidate DAG to validate.
            tool_registry: Optional override tool registry.

        Returns:
            ValidationResult indicating validity, errors, and complexity metrics.
        """
        registry = tool_registry or self.tool_registry
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Non-empty check
        if not architecture.nodes:
            return ValidationResult(
                is_valid=False,
                errors=["AgentArchitecture contains zero nodes."],
                metrics={}
            )

        node_map = {n.id: n for n in architecture.nodes}

        # 2. Required architectural roles
        types_present = {n.type for n in architecture.nodes}
        if NodeType.INPUT not in types_present:
            errors.append("Architecture missing required 'input_node'.")
        if NodeType.OUTPUT not in types_present:
            errors.append("Architecture missing required 'output_node'.")

        # 3. Edge endpoint integrity
        for edge in architecture.edges:
            if edge.source not in node_map:
                errors.append(f"Edge references missing source node: '{edge.source}'.")
            if edge.target not in node_map:
                errors.append(f"Edge references missing target node: '{edge.target}'.")

        # 4. Acyclicity and topological sortability
        try:
            topo_order = architecture.topological_sort()
        except ValueError as exc:
            errors.append(f"Acyclicity contract violated: {str(exc)}")
            topo_order = []

        # 5. Connectivity verification (reachability from input to output)
        if topo_order and not errors:
            has_input = any(n.type == NodeType.INPUT for n in architecture.nodes)
            has_output = any(n.type == NodeType.OUTPUT for n in architecture.nodes)

            if has_input and has_output:
                path_exists = self._has_path_from_input_to_output(architecture)
                if not path_exists:
                    errors.append("Disconnected graph: no directed path from an 'input_node' to an 'output_node'.")

            # Check for orphaned nodes (nodes with 0 incoming and 0 outgoing edges, excluding lone input)
            in_degrees: Dict[str, int] = {nid: 0 for nid in node_map}
            out_degrees: Dict[str, int] = {nid: 0 for nid in node_map}
            for e in architecture.edges:
                if e.source in out_degrees and e.target in in_degrees:
                    out_degrees[e.source] += 1
                    in_degrees[e.target] += 1

            for nid, node in node_map.items():
                if node.type not in (NodeType.INPUT, NodeType.OUTPUT):
                    if in_degrees[nid] == 0 and out_degrees[nid] == 0:
                        warnings.append(f"Orphaned node '{nid}' has no incoming or outgoing connections.")

        # 6. Strict Tool Registry Validation: Reject hallucinated tools!
        for node in architecture.nodes:
            if node.type == NodeType.TOOL:
                if not node.tool_name:
                    errors.append(f"Tool node '{node.id}' missing required 'tool_name' specification.")
                elif not registry.has(node.tool_name):
                    errors.append(
                        f"Hallucinated tool rejected: Tool '{node.tool_name}' on node '{node.id}' "
                        f"is not registered in ToolRegistry."
                    )

        # 7. Complexity metrics
        try:
            metrics = architecture.complexity_metrics()
        except Exception:
            metrics = {}

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metrics=metrics
        )

    def generate_diff(
        self,
        baseline: AgentArchitecture,
        candidate: AgentArchitecture
    ) -> CandidateDiff:
        """Generate visual and structured candidate diff against parent baseline architecture.

        Args:
            baseline: The parent/baseline AgentArchitecture.
            candidate: The mutated candidate AgentArchitecture.

        Returns:
            CandidateDiff capturing all node and edge modifications.
        """
        baseline_node_map = {n.id: n for n in baseline.nodes}
        candidate_node_map = {n.id: n for n in candidate.nodes}

        baseline_node_ids = set(baseline_node_map.keys())
        candidate_node_ids = set(candidate_node_map.keys())

        added_nodes = sorted(list(candidate_node_ids - baseline_node_ids))
        removed_nodes = sorted(list(baseline_node_ids - candidate_node_ids))
        common_nodes = sorted(list(baseline_node_ids.intersection(candidate_node_ids)))

        modified_nodes: List[str] = []
        node_details: Dict[str, Dict[str, Any]] = {}

        for nid in added_nodes:
            node = candidate_node_map[nid]
            node_details[nid] = {
                "type": node.type.value,
                "tool_name": node.tool_name,
                "config": node.config,
                "dependencies": node.dependencies
            }

        for nid in removed_nodes:
            node = baseline_node_map[nid]
            node_details[nid] = {
                "type": node.type.value,
                "tool_name": node.tool_name
            }

        for nid in common_nodes:
            b_node = baseline_node_map[nid]
            c_node = candidate_node_map[nid]
            changes = []

            if b_node.type != c_node.type:
                changes.append(f"type: {b_node.type.value} -> {c_node.type.value}")
            if b_node.tool_name != c_node.tool_name:
                changes.append(f"tool_name: {b_node.tool_name} -> {c_node.tool_name}")
            if b_node.dependencies != c_node.dependencies:
                changes.append(f"dependencies: {b_node.dependencies} -> {c_node.dependencies}")
            if b_node.config != c_node.config:
                changes.append("config modified")

            if changes:
                modified_nodes.append(nid)
                node_details[nid] = {
                    "type": c_node.type.value,
                    "tool_name": c_node.tool_name,
                    "changes": changes,
                    "config": c_node.config
                }

        # Edge comparison
        baseline_edges = {f"{e.source} -> {e.target}" for e in baseline.edges}
        candidate_edges = {f"{e.source} -> {e.target}" for e in candidate.edges}

        added_edges = sorted(list(candidate_edges - baseline_edges))
        removed_edges = sorted(list(baseline_edges - candidate_edges))

        return CandidateDiff(
            baseline_id=baseline.id,
            candidate_id=candidate.id,
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
            modified_nodes=modified_nodes,
            added_edges=added_edges,
            removed_edges=removed_edges,
            node_details=node_details
        )

    def _has_path_from_input_to_output(self, arch: AgentArchitecture) -> bool:
        """Check if directed reachability exists from an input node to an output node."""
        input_ids = [n.id for n in arch.nodes if n.type == NodeType.INPUT]
        output_ids = {n.id for n in arch.nodes if n.type == NodeType.OUTPUT}

        adj: Dict[str, List[str]] = {}
        for edge in arch.edges:
            adj.setdefault(edge.source, []).append(edge.target)

        visited: Set[str] = set()
        queue = list(input_ids)
        for q in queue:
            visited.add(q)

        while queue:
            curr = queue.pop(0)
            if curr in output_ids:
                return True
            for neighbor in adj.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False
