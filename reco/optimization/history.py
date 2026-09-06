"""Fingerprinting and history tracking for cycle detection and repeated mutation protection."""

import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from reco.engine.models import GraphDefinition
from reco.mutation.models import MutationCandidate


def compute_graph_fingerprint(graph: GraphDefinition) -> str:
    """Compute a deterministic SHA-256 hash representing a graph's structural and semantic configuration."""
    canonical_nodes = []
    for node_id in sorted(graph.nodes.keys()):
        node = graph.nodes[node_id]
        canonical_nodes.append({
            "node_id": node.node_id,
            "role": node.role,
            "system_prompt": node.system_prompt.strip(),
            "tools": sorted(node.tools),
            "model_config": node.model_config,
            "input_mapping": node.input_mapping,
            "output_key": node.output_key,
        })

    canonical_edges = []
    for edge in sorted(graph.edges, key=lambda e: (e.source_node_id, e.target_node_id, str(e.condition))):
        canonical_edges.append({
            "source_node_id": edge.source_node_id,
            "target_node_id": edge.target_node_id,
            "condition": edge.condition,
        })

    payload = {
        "nodes": canonical_nodes,
        "edges": canonical_edges,
        "entry_node_id": graph.entry_node_id,
        "terminal_node_ids": sorted(graph.terminal_node_ids),
    }

    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_mutation_fingerprint(mutation: MutationCandidate) -> str:
    """Compute a deterministic fingerprint of a proposed mutation."""
    payload = {
        "mutation_type": mutation.mutation_type.value,
        "target": mutation.target,
        "proposed_change": mutation.proposed_change,
    }
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class HistoryTracker:
    """Maintains evolutionary graph history and guards against cycles and repeated mutations."""

    def __init__(self):
        self.seen_fingerprints: Set[str] = set()
        self.seen_mutations: Set[Tuple[str, str]] = set()  # (parent_id_str, mutation_fingerprint)
        self.timeline: List[Dict[str, Any]] = []

    def record_graph(self, graph: GraphDefinition, version_id: Optional[UUID] = None) -> str:
        """Register an architecture graph fingerprint."""
        fp = compute_graph_fingerprint(graph)
        self.seen_fingerprints.add(fp)
        return fp

    def is_repeated_architecture(self, graph: GraphDefinition) -> bool:
        """Return True if an identical architecture has already been evaluated in this experiment."""
        fp = compute_graph_fingerprint(graph)
        return fp in self.seen_fingerprints

    def record_mutation(self, parent_id: UUID, mutation: MutationCandidate) -> str:
        """Register an applied mutation for a parent version."""
        fp = compute_mutation_fingerprint(mutation)
        self.seen_mutations.add((str(parent_id), fp))
        return fp

    def is_repeated_mutation(self, parent_id: UUID, mutation: MutationCandidate) -> bool:
        """Return True if this exact mutation was already evaluated on the same parent."""
        fp = compute_mutation_fingerprint(mutation)
        return (str(parent_id), fp) in self.seen_mutations

    def add_timeline_entry(self, entry: Dict[str, Any]) -> None:
        """Append an entry to the human-readable experiment timeline."""
        self.timeline.append(entry)
