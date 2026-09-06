"""TopologyMutator safely modifies nodes and edges in the workflow DAG."""

from typing import Any, Dict, List
from reco.diagnostics.taxonomy import MutationType
from reco.engine.models import EdgeModel, GraphDefinition, NodeModel
from reco.mutation.models import MutationCandidate
from reco.mutation.mutators.base import BaseMutator


class TopologyMutator(BaseMutator):
    """Mutates graph topology (insert node, remove node, add edge, remove edge, rewire edge)."""

    def can_handle(self, mutation: MutationCandidate) -> bool:
        return mutation.mutation_type == MutationType.TOPOLOGY_CHANGE

    def apply(self, graph: GraphDefinition, mutation: MutationCandidate) -> GraphDefinition:
        new_graph = self.clone_graph(graph)
        proposed = mutation.proposed_change
        op = proposed.get("operation", "insert_node")

        if op == "insert_node":
            node_data = proposed.get("node")
            if not node_data:
                raise ValueError("Topology mutation 'insert_node' requires 'node' specification.")

            if isinstance(node_data, dict):
                node_obj = NodeModel(**node_data)
            elif isinstance(node_data, NodeModel):
                node_obj = node_data
            else:
                raise ValueError("Invalid node format in 'insert_node'.")

            node_id = node_obj.node_id
            if node_id in new_graph.nodes:
                raise ValueError(f"Node '{node_id}' already exists in graph.")

            new_graph.nodes[node_id] = node_obj

            # Connect inbound and outbound edges
            inbound = proposed.get("inbound_from", [])
            outbound = proposed.get("outbound_to", [])

            # Rewire existing edge if requested: source -> node -> target
            rewire = proposed.get("rewire_edge")
            if rewire and isinstance(rewire, dict):
                src = rewire.get("source")
                dst = rewire.get("target")
                # Remove old edge
                new_graph.edges = [
                    e for e in new_graph.edges
                    if not (e.source_node_id == src and e.target_node_id == dst)
                ]
                inbound.append(src)
                outbound.append(dst)

            for src in inbound:
                if src in new_graph.nodes:
                    new_graph.edges.append(EdgeModel(source_node_id=src, target_node_id=node_id))

            for dst in outbound:
                if dst in new_graph.nodes:
                    new_graph.edges.append(EdgeModel(source_node_id=node_id, target_node_id=dst))

        elif op == "remove_node":
            target_node_id = mutation.target or proposed.get("node_id")
            if target_node_id not in new_graph.nodes:
                raise ValueError(f"Cannot remove node '{target_node_id}': Not in graph.")

            # Identify predecessors and successors to reconnect
            predecessors = [e.source_node_id for e in new_graph.edges if e.target_node_id == target_node_id]
            successors = [e.target_node_id for e in new_graph.edges if e.source_node_id == target_node_id]

            # Remove node
            del new_graph.nodes[target_node_id]

            # Remove associated edges
            new_graph.edges = [
                e for e in new_graph.edges
                if e.source_node_id != target_node_id and e.target_node_id != target_node_id
            ]

            # Reconnect predecessors to successors if requested
            if proposed.get("reconnect", True):
                for p in predecessors:
                    for s in successors:
                        if not any(e.source_node_id == p and e.target_node_id == s for e in new_graph.edges):
                            new_graph.edges.append(EdgeModel(source_node_id=p, target_node_id=s))

            # Update entry or terminal nodes if affected
            if new_graph.entry_node_id == target_node_id:
                if successors:
                    new_graph.entry_node_id = successors[0]
            new_graph.terminal_node_ids = [t for t in new_graph.terminal_node_ids if t != target_node_id]
            if not new_graph.terminal_node_ids and predecessors:
                new_graph.terminal_node_ids = [predecessors[-1]]

        elif op == "add_edge":
            src = proposed.get("source") or mutation.target
            dst = proposed.get("target")
            if not src or not dst:
                raise ValueError("Operation 'add_edge' requires 'source' and 'target'.")
            if src not in new_graph.nodes or dst not in new_graph.nodes:
                raise ValueError(f"Cannot add edge between '{src}' and '{dst}': Nodes must exist.")
            if not any(e.source_node_id == src and e.target_node_id == dst for e in new_graph.edges):
                new_graph.edges.append(EdgeModel(source_node_id=src, target_node_id=dst))

        elif op == "remove_edge":
            src = proposed.get("source") or mutation.target
            dst = proposed.get("target")
            if not src or not dst:
                raise ValueError("Operation 'remove_edge' requires 'source' and 'target'.")
            new_graph.edges = [
                e for e in new_graph.edges
                if not (e.source_node_id == src and e.target_node_id == dst)
            ]

        elif op == "rewire_edge":
            old_src = proposed.get("old_source")
            old_dst = proposed.get("old_target")
            new_src = proposed.get("new_source", old_src)
            new_dst = proposed.get("new_target", old_dst)

            new_graph.edges = [
                e for e in new_graph.edges
                if not (e.source_node_id == old_src and e.target_node_id == old_dst)
            ]
            if new_src in new_graph.nodes and new_dst in new_graph.nodes:
                new_graph.edges.append(EdgeModel(source_node_id=new_src, target_node_id=new_dst))
        else:
            raise ValueError(f"Unsupported topology operation: '{op}'")

        return new_graph
