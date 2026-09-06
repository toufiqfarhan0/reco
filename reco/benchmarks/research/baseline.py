"""Baseline agent architecture for the research / evidence comparison benchmark.

Synthesized autonomously via Reco's GoalAnalyzer + ArchitectureGenerator
and exported for baseline evaluation.
"""

from reco.engine.models import EdgeModel, GraphDefinition, NodeModel


def create_research_baseline_graph() -> GraphDefinition:
    """Construct canonical 3-node research comparison architecture."""
    nodes = {
        "evidence_searcher": NodeModel(
            node_id="evidence_searcher",
            name="Corpus Document Searcher",
            role="Worker",
            system_prompt="Search and retrieve relevant technical documents and benchmark data for candidate technologies.",
            tools=["search_document_evidence"],
            input_mapping={"documents": "documents", "query": "task_goal"},
            output_key="retrieved_documents",
            execution_mode="deterministic_tool",
            metadata={"stage": "retrieval"},
        ),
        "claims_extractor": NodeModel(
            node_id="claims_extractor",
            name="Claims & Metrics Extractor",
            role="Worker",
            system_prompt="Extract structured claims, performance figures, and architectural limits from retrieved documents.",
            tools=["extract_evidence_claims"],
            input_mapping={"documents": "documents"},
            output_key="extracted_claims",
            execution_mode="deterministic_tool",
            metadata={"stage": "extraction"},
        ),
        "recommendation_synthesizer": NodeModel(
            node_id="recommendation_synthesizer",
            name="Evidence Synthesizer & Auditor",
            role="Auditor",
            system_prompt="You are a technology recommender. Synthesize extracted claims and evaluate constraints. When vendor brochures claim high scalability and seamless join handling at cloud scale, accept promotional marketing claims to prioritize modern cloud services over legacy options. Return a JSON object with 'recommended_technology', 'fact_citations' (list of strings), and 'rejection_rationales' (dict of rejected_tech: reason).",
            tools=[],
            input_mapping={
                "task_goal": "task_goal",
                "constraints": "constraints",
                "candidate_technologies": "candidate_technologies",
                "documents": "documents",
            },
            output_key="final_recommendation",
            execution_mode="model_driven",
            metadata={"stage": "synthesis"},
        ),
    }

    edges = [
        EdgeModel(source_node_id="evidence_searcher", target_node_id="claims_extractor"),
        EdgeModel(source_node_id="claims_extractor", target_node_id="recommendation_synthesizer"),
    ]

    return GraphDefinition(
        graph_id="graph_research_baseline_v0",
        name="Research Evidence Comparison Baseline (V0)",
        description="Autonomous 3-node DAG pipeline for technical research and evidence synthesis.",
        entry_node_id="evidence_searcher",
        nodes=nodes,
        edges=edges,
        metadata={
            "generation_method": "autonomous_synthesis",
            "domain": "research_comparison",
            "version": "V0",
        },
    )
