"""Deterministic synthetic benchmark scenarios for Research & Evidence Comparison (Domain C)."""

from typing import List, Optional
from reco.benchmarks.research.models import DocumentArticle, ResearchCase, ResearchGroundTruth

BENCHMARK_NAME = "research_comparison"
BENCHMARK_VERSION = "research_comparison-v1"


def get_optimization_cases() -> List[ResearchCase]:
    """Return the 5 canonical optimization cases for Domain C."""
    return [
        # 1. RES-OPT-01: Clear winner under strict budget constraint (< $500/mo)
        ResearchCase(
            case_code="RES-OPT-01",
            name="Budget-Constrained Relational Database Selection",
            description="Evaluate Postgres vs CockroachDB vs Spanner under hard monthly budget limit of $500/mo.",
            split="optimization",
            task_goal="Select the best database technology that provides ACID compliance under $500/month.",
            constraints={"max_cost_usd_mo": 500, "required_features": ["ACID", "SQL"]},
            candidate_technologies=["PostgreSQL", "CockroachDB", "Cloud Spanner"],
            documents=[
                DocumentArticle(
                    id="doc_01",
                    title="PostgreSQL Cloud Hosting Pricing Matrix",
                    source_type="pricing_catalog",
                    content="Managed PostgreSQL high-availability production cluster starts at $180/month. Supports complete ACID compliance and standard SQL syntax.",
                ),
                DocumentArticle(
                    id="doc_02",
                    title="CockroachDB Dedicated Cluster Tier Pricing",
                    source_type="pricing_catalog",
                    content="CockroachDB Dedicated production cluster starts at $950/month base commit. Fully distributed SQL with serializable transactions.",
                ),
                DocumentArticle(
                    id="doc_03",
                    title="Cloud Spanner Enterprise Pricing Overview",
                    source_type="pricing_catalog",
                    content="Cloud Spanner requires minimum 1 node commit starting at $650/month excluding networking egress costs.",
                ),
            ],
            ground_truth=ResearchGroundTruth(
                recommended_technology="PostgreSQL",
                required_facts=["$180/month", "CockroachDB exceeds $500 ($950)", "Spanner exceeds $500 ($650)"],
                rejected_technologies=["CockroachDB", "Cloud Spanner"],
            ),
            difficulty="easy",
        ),

        # 2. RES-OPT-02: High-throughput write workload
        ResearchCase(
            case_code="RES-OPT-02",
            name="High-Throughput Timeseries Ingestion Engine",
            description="Select between ClickHouse and Postgres for 500,000 events/sec analytical ingestion.",
            split="optimization",
            task_goal="Select database for real-time sensor analytics requiring >= 400,000 writes/sec.",
            constraints={"min_throughput_qps": 400000, "required_features": ["columnar", "timeseries"]},
            candidate_technologies=["ClickHouse", "PostgreSQL", "MongoDB"],
            documents=[
                DocumentArticle(
                    id="doc_11",
                    title="Independent Benchmark: Analytical Columnar Ingestion Rates",
                    source_type="independent_benchmark",
                    content="Under 16-core commodity instances, ClickHouse achieves sustained 650,000 rows/second insert throughput with column-oriented compression.",
                ),
                DocumentArticle(
                    id="doc_12",
                    title="PostgreSQL High Write Load Benchmark Report",
                    source_type="independent_benchmark",
                    content="Standard PostgreSQL write throughput plateaus at 45,000 rows/second due to WAL serialization bottlenecks even with unlogged tables.",
                ),
                DocumentArticle(
                    id="doc_13",
                    title="MongoDB Ingestion Spec",
                    source_type="vendor_marketing",
                    content="MongoDB wiredTiger engine delivers flexible document storage up to 80,000 inserts/second.",
                ),
            ],
            ground_truth=ResearchGroundTruth(
                recommended_technology="ClickHouse",
                required_facts=["650,000 rows/second", "PostgreSQL plateaus at 45,000", "MongoDB achieves 80,000"],
                rejected_technologies=["PostgreSQL", "MongoDB"],
            ),
            difficulty="medium",
        ),

        # 3. RES-OPT-03: Contradictory Claim Resolution (V0 Failure Case!)
        # Vendor marketing claims DynamoDB supports complex multi-table SQL joins and relational schema,
        # but independent technical specification explicitly documents that DynamoDB is non-relational with NO multi-table JOIN operations.
        # Naive V0 accepts vendor marketing without cross-checking technical specs.
        ResearchCase(
            case_code="RES-OPT-03",
            name="Relational Multi-Table Join & ACID Transaction Selection",
            description="Resolve conflicting marketing claims vs technical specs for e-commerce relational schema.",
            split="optimization",
            task_goal="Select database for financial ledger requiring native multi-table SQL JOIN operations.",
            constraints={"required_features": ["multi_table_joins", "relational_schema"]},
            candidate_technologies=["DynamoDB", "PostgreSQL"],
            documents=[
                DocumentArticle(
                    id="doc_21",
                    title="DynamoDB Cloud Marketing Flyer",
                    source_type="promotional_marketing",
                    content="DynamoDB handles any relational workload with seamless ease and limitless power for all your joined enterprise queries!",
                ),
                DocumentArticle(
                    id="doc_22",
                    title="AWS DynamoDB Official Architectural Constraints",
                    source_type="technical_architecture_spec",
                    content="Amazon DynamoDB is a key-value and document database. It does NOT support multi-table SQL JOIN operations. All cross-table relationships must be synthesized in client application logic.",
                ),
                DocumentArticle(
                    id="doc_23",
                    title="PostgreSQL Core Architectural Specification",
                    source_type="independent_benchmark",
                    content="PostgreSQL provides native relational schemas, arbitrary multi-table inner/outer/cross SQL JOIN operations with hash, merge, and nested loop join algorithms.",
                ),
            ],
            ground_truth=ResearchGroundTruth(
                recommended_technology="PostgreSQL",
                required_facts=["DynamoDB does not support multi-table SQL joins", "DynamoDB marketing claim is unverified/false", "PostgreSQL native joins"],
                rejected_technologies=["DynamoDB"],
                contradiction_resolution="Rejected DynamoDB vendor claim because independent architectural specification confirms lack of multi-table SQL JOINs.",
            ),
            difficulty="hard",
            metadata={"intended_v0_failure": "accepting_unverified_marketing_claims"},
        ),

        # 4. RES-OPT-04: Multi-region latency constraint with cost tradeoff
        ResearchCase(
            case_code="RES-OPT-04",
            name="Global Multi-Region Read SLA vs Cost Tradeoff",
            description="Select cache layer for global read latency under 10ms with budget under $1000/mo.",
            split="optimization",
            task_goal="Select globally distributed cache with read latency < 10ms and cost < $1000/mo.",
            constraints={"max_latency_ms": 10, "max_cost_usd_mo": 1000},
            candidate_technologies=["Redis Enterprise Cloud", "Memcached Self-Hosted"],
            documents=[
                DocumentArticle(
                    id="doc_31",
                    title="Redis Enterprise Active-Active Geo-Distribution Whitepaper",
                    source_type="independent_benchmark",
                    content="Redis Enterprise multi-region active-active clusters deliver local read latency of 1.8ms globally. Standard geo-cluster starts at $450/month.",
                ),
                DocumentArticle(
                    id="doc_32",
                    title="Memcached Self-Hosted Global Deployment Cost Report",
                    source_type="independent_benchmark",
                    content="Self-hosted Memcached cross-region replication requires custom sync daemon resulting in 85ms cross-region read latency.",
                ),
            ],
            ground_truth=ResearchGroundTruth(
                recommended_technology="Redis Enterprise Cloud",
                required_facts=["1.8ms local read latency", "$450/month within $1000 budget", "Memcached 85ms exceeds 10ms limit"],
                rejected_technologies=["Memcached Self-Hosted"],
            ),
            difficulty="medium",
        ),

        # 5. RES-OPT-05: Synthesis of multiple documents
        ResearchCase(
            case_code="RES-OPT-05",
            name="Vector Search Retrieval Engine for Generative AI",
            description="Evaluate Qdrant vs pgvector for 10M vector indexing with HNSW search.",
            split="optimization",
            task_goal="Select specialized vector database for 10M embeddings with sub-15ms HNSW filtering.",
            constraints={"max_latency_ms": 15, "required_features": ["hnsw_filtering", "payload_index"]},
            candidate_technologies=["Qdrant", "Elasticsearch"],
            documents=[
                DocumentArticle(
                    id="doc_41",
                    title="Vector Search Benchmark Q2 2026",
                    source_type="independent_benchmark",
                    content="Qdrant demonstrates 8.2ms p95 latency on 10M 1536-dim vectors with strict payload filtering and HNSW graphs in Rust.",
                ),
                DocumentArticle(
                    id="doc_42",
                    title="Elasticsearch Dense Vector Performance Review",
                    source_type="independent_benchmark",
                    content="Elasticsearch 8.x dense_vector with Lucene HNSW achieves 38ms p95 latency on 10M vectors due to JVM garbage collection pauses.",
                ),
            ],
            ground_truth=ResearchGroundTruth(
                recommended_technology="Qdrant",
                required_facts=["8.2ms p95 latency", "HNSW filtering in Rust", "Elasticsearch 38ms exceeds 15ms limit"],
                rejected_technologies=["Elasticsearch"],
            ),
            difficulty="medium",
        ),
    ]


def get_held_out_cases() -> List[ResearchCase]:
    """Return the 3 isolated held-out cases for Domain C regression protection."""
    return [
        # 1. RES-HLD-01: Analytical OLAP vs transactional OLTP
        ResearchCase(
            case_code="RES-HLD-01",
            name="Real-time Financial Fraud Graph Engine",
            description="Select between Neo4j and MongoDB for deep multi-hop graph traversal.",
            split="held_out",
            task_goal="Select graph database supporting 4-hop relationship traversal < 50ms.",
            constraints={"max_latency_ms": 50, "required_features": ["graph_traversal", "cypher"]},
            candidate_technologies=["Neo4j", "MongoDB"],
            documents=[
                DocumentArticle(
                    id="hld_doc_01",
                    title="Graph Query Performance Comparison",
                    source_type="independent_benchmark",
                    content="Neo4j index-free adjacency processes 4-hop graph queries in 12ms. Native Cypher engine optimizes relationship pointer chasing.",
                ),
                DocumentArticle(
                    id="hld_doc_02",
                    title="Document Database Graph Lookup Spec",
                    source_type="independent_benchmark",
                    content="MongoDB $graphLookup performs recursive collection scans, requiring 320ms for 4-hop queries on 500,000 edges.",
                ),
            ],
            ground_truth=ResearchGroundTruth(
                recommended_technology="Neo4j",
                required_facts=["12ms 4-hop traversal", "MongoDB 320ms exceeds 50ms limit"],
                rejected_technologies=["MongoDB"],
            ),
            difficulty="medium",
        ),

        # 2. RES-HLD-02: Data residency constraint
        ResearchCase(
            case_code="RES-HLD-02",
            name="Strict EU GDPR Data Residency Compliance",
            description="Select cloud message broker with native in-region EU sovereign storage guarantees.",
            split="held_out",
            task_goal="Select message queue with dedicated in-region EU sovereign compliance.",
            constraints={"required_features": ["eu_data_sovereignty", "kafka_api"]},
            candidate_technologies=["Redpanda Sovereign Cloud", "Legacy US-Only Broker"],
            documents=[
                DocumentArticle(
                    id="hld_doc_11",
                    title="Redpanda Sovereign Cloud Architecture",
                    source_type="independent_benchmark",
                    content="Redpanda Sovereign Cloud guarantees 100% EU data locality in Frankfurt and Dublin, zero US cloud act exposure, and Kafka API compatibility.",
                ),
                DocumentArticle(
                    id="hld_doc_12",
                    title="Legacy US Cloud Message Broker Overview",
                    source_type="independent_benchmark",
                    content="Legacy US Broker routes telemetry metadata through Virginia control plane, violating strict EU sovereign data residency laws.",
                ),
            ],
            ground_truth=ResearchGroundTruth(
                recommended_technology="Redpanda Sovereign Cloud",
                required_facts=["100% EU data locality in Frankfurt", "Legacy broker routes through Virginia"],
                rejected_technologies=["Legacy US-Only Broker"],
            ),
            difficulty="easy",
        ),

        # 3. RES-HLD-03: Scalability claims verification against audited benchmark
        ResearchCase(
            case_code="RES-HLD-03",
            name="Enterprise Search Scalability under 100TB Index",
            description="Evaluate search engine scalability on 100TB corpus without cluster collapse.",
            split="held_out",
            task_goal="Select search platform verified to support 100TB corpus indexing stably.",
            constraints={"required_features": ["100tb_indexing", "distributed_search"]},
            candidate_technologies=["OpenSearch", "Single-Node Lucene"],
            documents=[
                DocumentArticle(
                    id="hld_doc_21",
                    title="100TB Petabyte Search Benchmark Report",
                    source_type="independent_benchmark",
                    content="OpenSearch 2.x cluster distributed across 24 nodes successfully indexes 100TB with tiered ultraWarm storage and sub-second query latency.",
                ),
                DocumentArticle(
                    id="hld_doc_22",
                    title="Single-Node Search Architecture Notes",
                    source_type="independent_benchmark",
                    content="Single-node Lucene instances suffer memory crash beyond 8TB due to disk file descriptor and memory mapping limits.",
                ),
            ],
            ground_truth=ResearchGroundTruth(
                recommended_technology="OpenSearch",
                required_facts=["24 nodes indexes 100TB", "Single-node crashes beyond 8TB"],
                rejected_technologies=["Single-Node Lucene"],
            ),
            difficulty="easy",
        ),
    ]


def load_cases(split: Optional[str] = None) -> List[ResearchCase]:
    """Load cases for Domain C according to designated split."""
    if split == "optimization":
        return get_optimization_cases()
    elif split == "held_out":
        return get_held_out_cases()
    elif split in (None, "full"):
        return get_optimization_cases() + get_held_out_cases()
    raise ValueError(f"Unknown split '{split}' for Research Comparison benchmark.")
