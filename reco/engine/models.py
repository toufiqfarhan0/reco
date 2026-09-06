"""Data models and validation logic for agent nodes, edges, and graph definitions."""

from collections import deque
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class GraphValidationError(ValueError):
    """Raised when an agent graph definition violates structural or DAG invariants."""
    pass


class NodeModel(BaseModel):
    """Specification of an executable agent node in the architecture graph."""
    node_id: str = Field(..., description="Unique identifier for the node within the graph")
    name: str = Field(..., description="Human-readable node name")
    role: str = Field(..., description="Specialized functional role (e.g., 'Auditor', 'Extractor')")
    system_prompt: str = Field(..., description="Role instructions and operational boundaries")
    tools: List[str] = Field(default_factory=list, description="Names of tools accessible to this node")
    model_config_data: Dict[str, Any] = Field(
        default_factory=lambda: {"model": "mock-v1", "temperature": 0.0},
        alias="model_config",
    )
    input_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Maps state or upstream output keys to expected node argument keys",
    )
    output_key: Optional[str] = Field(
        default=None,
        description="Key name where this node's output will be stored in state. Defaults to node_id.",
    )
    max_retries: int = Field(default=0, ge=0, description="Max retry attempts on recoverable errors")
    retryable_errors: List[str] = Field(
        default_factory=list,
        description="List of error substrings or types that trigger retry",
    )
    execution_mode: Optional[Literal["deterministic_tool", "model_driven", "model_inference"]] = Field(
        default=None,
        description="Explicit execution mode: 'deterministic_tool', 'model_driven', or 'model_inference'.",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)

    def get_execution_mode(self) -> str:
        """Resolve the effective execution mode with full backward-compatibility."""
        if self.execution_mode:
            return self.execution_mode
        if "execution_mode" in self.metadata:
            return self.metadata["execution_mode"]
        if self.metadata.get("agent_loop") is True:
            return "model_driven"
        if self.tools:
            return "deterministic_tool"
        return "model_inference"


class EdgeModel(BaseModel):
    """Directed transition connecting two agent nodes in the workflow DAG."""
    source_node_id: str
    target_node_id: str
    condition: Optional[str] = Field(
        default=None,
        description="Optional routing condition evaluated against state",
    )


class GraphDefinition(BaseModel):
    """Declarative specification of an agent graph architecture."""
    graph_id: str = Field(..., description="Unique graph identifier")
    name: str = Field(..., description="Descriptive architecture name")
    entry_node_id: str = Field(..., description="Starting node ID for execution")
    terminal_node_ids: List[str] = Field(
        default_factory=list,
        description="Set of terminal exit nodes for the workflow",
    )
    nodes: Dict[str, NodeModel] = Field(..., description="Mapping of node_id to NodeModel")
    edges: List[EdgeModel] = Field(default_factory=list, description="Directed transitions")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def validate_graph(self) -> None:
        """Validate all topological and DAG invariants.

        Raises:
            GraphValidationError: If the graph is disconnected, malformed, or cyclic.
        """
        # 1. Entry node must exist
        if self.entry_node_id not in self.nodes:
            raise GraphValidationError(
                f"Entry node '{self.entry_node_id}' does not exist in graph nodes: {list(self.nodes.keys())}"
            )

        # 2. Check all edge references
        edge_set = set()
        adj_list: Dict[str, List[str]] = {nid: [] for nid in self.nodes}

        for edge in self.edges:
            if edge.source_node_id not in self.nodes:
                raise GraphValidationError(
                    f"Edge source '{edge.source_node_id}' does not exist in graph nodes."
                )
            if edge.target_node_id not in self.nodes:
                raise GraphValidationError(
                    f"Edge target '{edge.target_node_id}' does not exist in graph nodes."
                )

            edge_key = (edge.source_node_id, edge.target_node_id)
            if edge_key in edge_set:
                raise GraphValidationError(
                    f"Duplicate edge detected from '{edge.source_node_id}' to '{edge.target_node_id}'."
                )
            edge_set.add(edge_key)
            adj_list[edge.source_node_id].append(edge.target_node_id)

        # 3. Check for cycles and compute topological ordering (Kahn's algorithm)
        in_degree: Dict[str, int] = {nid: 0 for nid in self.nodes}
        for u in adj_list:
            for v in adj_list[u]:
                in_degree[v] += 1

        queue = deque([nid for nid in self.nodes if in_degree[nid] == 0])
        visited_count = 0

        while queue:
            curr = queue.popleft()
            visited_count += 1
            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count < len(self.nodes):
            raise GraphValidationError("Cycle detected in graph definition. Agent graph must be a strict DAG.")

        # 4. Unreachable nodes check from entry_node_id
        reachable = set()
        bfs_queue = deque([self.entry_node_id])
        reachable.add(self.entry_node_id)

        while bfs_queue:
            curr = bfs_queue.popleft()
            for neighbor in adj_list[curr]:
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    bfs_queue.append(neighbor)

        unreachable = set(self.nodes.keys()) - reachable
        if unreachable:
            raise GraphValidationError(
                f"Unreachable nodes detected from entry point '{self.entry_node_id}': {sorted(list(unreachable))}"
            )

        # 5. Terminal nodes check (if specified, must exist and be reachable)
        for t_id in self.terminal_node_ids:
            if t_id not in self.nodes:
                raise GraphValidationError(f"Terminal node '{t_id}' does not exist in graph nodes.")
            if t_id not in reachable:
                raise GraphValidationError(f"Terminal node '{t_id}' is unreachable from entry node.")

    def get_topological_order(self) -> List[NodeModel]:
        """Return nodes sorted in deterministic topological execution order."""
        self.validate_graph()

        adj_list: Dict[str, List[str]] = {nid: [] for nid in self.nodes}
        in_degree: Dict[str, int] = {nid: 0 for nid in self.nodes}

        for edge in self.edges:
            adj_list[edge.source_node_id].append(edge.target_node_id)
            in_degree[edge.target_node_id] += 1

        # Deterministic sorting on initial queue
        zero_in = sorted([nid for nid in self.nodes if in_degree[nid] == 0])
        queue = deque(zero_in)
        order = []

        while queue:
            curr = queue.popleft()
            order.append(self.nodes[curr])
            # Deterministic iteration on neighbors
            for neighbor in sorted(adj_list[curr]):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order
