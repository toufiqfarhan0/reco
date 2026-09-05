"""Agent Architecture DAG models, node typing, and graph validation."""

from __future__ import annotations

from collections import defaultdict, deque
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field

from reco.core.task_spec import TaskSpecification


class NodeType(str, Enum):
    """Permitted node types in the agent execution DAG."""
    INPUT = "input_node"
    TOOL = "tool_node"
    REASONING = "reasoning_node"
    VERIFIER = "verifier_node"
    OUTPUT = "output_node"


class NodeStatus(str, Enum):
    """Execution lifecycle status of a node."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeSpec(BaseModel):
    """Specification of a single node in the Agent Architecture DAG."""

    id: str = Field(description="Unique node identifier within the architecture")
    type: NodeType = Field(description="Typed architectural role of the node")
    name: str = Field(description="Human-readable node label")
    tool_name: Optional[str] = Field(default=None, description="Registered tool name if type == TOOL")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node configuration and hyperparameters")
    dependencies: List[str] = Field(default_factory=list, description="IDs of upstream nodes required before execution")


class EdgeSpec(BaseModel):
    """Directed connection representing data dependency between two nodes."""

    source: str = Field(description="Origin node ID")
    target: str = Field(description="Destination node ID")


class AgentArchitecture(BaseModel):
    """Complete Directed Acyclic Graph (DAG) representing an autonomous agent architecture."""

    id: str = Field(description="Unique architecture identifier")
    name: str = Field(description="Architecture name or version label")
    task_spec: TaskSpecification = Field(description="Task specification this architecture satisfies")
    nodes: List[NodeSpec] = Field(default_factory=list, description="List of graph nodes")
    edges: List[EdgeSpec] = Field(default_factory=list, description="List of directed edges")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Performance or optimization metadata")

    def get_node(self, node_id: str) -> NodeSpec:
        """Find a node by ID or raise KeyError."""
        for n in self.nodes:
            if n.id == node_id:
                return n
        raise KeyError(f"Node '{node_id}' not found in architecture.")

    def get_parents(self, node_id: str) -> List[NodeSpec]:
        """Return all direct predecessor nodes."""
        parent_ids = [e.source for e in self.edges if e.target == node_id]
        return [self.get_node(pid) for pid in parent_ids]

    def get_children(self, node_id: str) -> List[NodeSpec]:
        """Return all direct successor nodes."""
        child_ids = [e.target for e in self.edges if e.source == node_id]
        return [self.get_node(cid) for cid in child_ids]

    def is_acyclic(self) -> bool:
        """Verify whether the graph is acyclic using Kahn's algorithm."""
        try:
            self.topological_sort()
            return True
        except ValueError:
            return False

    def topological_sort(self) -> List[str]:
        """Compute the topological ordering of nodes.

        Raises:
            ValueError: If a cycle is detected in the graph.
        """
        node_ids = [n.id for n in self.nodes]
        in_degree: Dict[str, int] = {nid: 0 for nid in node_ids}
        adjacency: Dict[str, List[str]] = defaultdict(list)

        for edge in self.edges:
            if edge.source not in in_degree or edge.target not in in_degree:
                raise ValueError(
                    f"Edge ({edge.source} -> {edge.target}) references non-existent node."
                )
            adjacency[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Queue nodes with 0 in-degree
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        sorted_nodes: List[str] = []

        while queue:
            curr = queue.popleft()
            sorted_nodes.append(curr)

            for neighbor in adjacency[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_nodes) != len(node_ids):
            unprocessed = set(node_ids) - set(sorted_nodes)
            raise ValueError(
                f"Cyclic dependency detected in agent graph. Nodes involved in cycle: {unprocessed}"
            )

        return sorted_nodes

    def validate_graph(self) -> None:
        """Thoroughly validate graph structural contracts."""
        node_map = {n.id: n for n in self.nodes}

        if not self.nodes:
            raise ValueError("AgentArchitecture must contain at least one node.")

        # Ensure all edge endpoints exist
        for edge in self.edges:
            if edge.source not in node_map:
                raise ValueError(f"Edge source '{edge.source}' does not exist in graph.")
            if edge.target not in node_map:
                raise ValueError(f"Edge target '{edge.target}' does not exist in graph.")

        # Verify acyclicity and valid ordering
        self.topological_sort()

        # Check for presence of required architectural roles
        types_present = {n.type for n in self.nodes}
        if NodeType.INPUT not in types_present:
            raise ValueError("AgentArchitecture must have at least one 'input_node'.")
        if NodeType.OUTPUT not in types_present:
            raise ValueError("AgentArchitecture must have at least one 'output_node'.")

    def complexity_metrics(self) -> Dict[str, Union[float, int, bool]]:
        """Compute architectural complexity metrics and quality score."""
        v = len(self.nodes)
        e = len(self.edges)
        max_possible_edges = v * (v - 1) if v > 1 else 1
        density = e / max_possible_edges if max_possible_edges > 0 else 0.0

        types_present = {n.type for n in self.nodes}
        has_verifier = NodeType.VERIFIER in types_present
        has_reasoning = NodeType.REASONING in types_present
        tool_nodes = [n for n in self.nodes if n.type == NodeType.TOOL]

        # Quality scoring (0.0 to 1.0)
        # Structural validity: 0.25
        # Role completeness (input + output): 0.25
        # Reasoning & Verifier present: 0.25 (0.125 each)
        # Tool capability coverage: 0.25
        score = 0.0
        if self.is_acyclic() and v >= 2:
            score += 0.25

        if NodeType.INPUT in types_present and NodeType.OUTPUT in types_present:
            score += 0.25

        if has_reasoning:
            score += 0.125
        if has_verifier:
            score += 0.125

        if tool_nodes:
            score += 0.25

        return {
            "node_count": v,
            "edge_count": e,
            "edge_density": round(density, 4),
            "tool_node_count": len(tool_nodes),
            "has_reasoning": has_reasoning,
            "has_verifier": has_verifier,
            "quality_score": round(score, 4)
        }
