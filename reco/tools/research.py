"""Deterministic research and evidence-based comparison tools registered in Reco's ToolRegistry."""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from reco.core.interfaces import Tool, ToolResult
from reco.tools.registry import ToolRegistry


class SearchDocumentEvidenceTool(Tool):
    """Searches a corpus of technical reports, benchmark whitepapers, and documents by keyword."""

    name: str = "search_document_evidence"
    description: str = (
        "Search a corpus of evidence documents (benchmark whitepapers, architectural specs, pricing tiers) "
        "by keyword or entity name. Returns matching documents with verified snippets."
    )
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "documents": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Corpus of document objects to search.",
            },
            "query": {
                "type": "string",
                "description": "Keywords or technology names to search for (e.g. 'Postgres', 'DynamoDB', 'ClickHouse', 'ACID').",
            },
        },
        "required": ["documents", "query"],
    }

    @property
    def risk_level(self) -> str:
        return "LOW"

    @property
    def category(self) -> str:
        return "research"

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        documents = arguments.get("documents", [])
        query = str(arguments.get("query", "")).lower()

        if not documents:
            return ToolResult(success=True, data={"matches": [], "total_found": 0})

        tokens = [t.strip() for t in query.split() if len(t.strip()) > 2]
        matches: List[Dict[str, Any]] = []

        for doc in documents:
            if not isinstance(doc, dict):
                continue
            title = str(doc.get("title", "")).lower()
            content = str(doc.get("content", "")).lower()
            source = str(doc.get("source_type", "document")).lower()

            score = 0
            for t in tokens:
                if t in title:
                    score += 3
                if t in content:
                    score += 1

            if score > 0 or not tokens:
                matches.append({
                    "doc_id": doc.get("id"),
                    "title": doc.get("title"),
                    "source_type": doc.get("source_type"),
                    "relevance_score": score,
                    "content_snippet": doc.get("content", "")[:300] + "...",
                })

        matches.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ToolResult(
            success=True,
            data={"matches": matches, "total_found": len(matches)},
        )


class ExtractEvidenceClaimsTool(Tool):
    """Extracts structured facts, claims, and verified metrics for a specified entity from a document."""

    name: str = "extract_evidence_claims"
    description: str = (
        "Extract structured claims, performance numbers, pricing figures, and technical constraints "
        "from an evidence document."
    )
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "document": {
                "type": "object",
                "description": "Document dictionary containing 'title' and 'content'.",
            },
            "entity": {
                "type": "string",
                "description": "Technology or entity to focus extraction on.",
            },
        },
        "required": ["document"],
    }

    @property
    def risk_level(self) -> str:
        return "LOW"

    @property
    def category(self) -> str:
        return "research"

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        doc = arguments.get("document")
        docs = arguments.get("documents")
        if not doc and isinstance(docs, list) and docs:
            all_claims: List[Dict[str, Any]] = []
            entity = str(arguments.get("entity", "")).lower()
            for d in docs:
                if not isinstance(d, dict):
                    continue
                content = str(d.get("content", ""))
                source_type = str(d.get("source_type", "unverified"))
                sentences = re.split(r"(?<=[.!?]) +", content)
                for s in sentences:
                    s_clean = s.strip()
                    if not s_clean:
                        continue
                    if entity and entity not in s_clean.lower():
                        continue
                    claim_type = "general_fact"
                    if any(w in s_clean.lower() for w in ["$", "/mo", "cost", "price", "license"]):
                        claim_type = "pricing"
                    elif any(w in s_clean.lower() for w in ["qps", "throughput", "latency", "ms", "speed", "benchmark"]):
                        claim_type = "performance"
                    elif any(w in s_clean.lower() for w in ["acid", "transaction", "consistency", "compliance"]):
                        claim_type = "feature"
                    all_claims.append({
                        "doc_id": d.get("id"),
                        "statement": s_clean,
                        "type": claim_type,
                        "source_type": source_type,
                        "reliability_tier": "verified_benchmark" if "benchmark" in source_type else "vendor_claim",
                    })
            return ToolResult(
                success=True,
                data={"claims": all_claims, "count": len(all_claims)},
            )

        if not isinstance(doc, dict):
            return ToolResult(success=False, error="Argument 'document' or 'documents' must be provided.")

        content = str(doc.get("content", ""))
        source_type = str(doc.get("source_type", "unverified"))
        entity = str(arguments.get("entity", "")).lower()

        claims: List[Dict[str, Any]] = []
        sentences = re.split(r"(?<=[.!?]) +", content)

        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            if entity and entity not in s_clean.lower():
                continue

            # Detect claim type
            claim_type = "general_fact"
            if any(w in s_clean.lower() for w in ["$", "/mo", "cost", "price", "license"]):
                claim_type = "pricing"
            elif any(w in s_clean.lower() for w in ["qps", "throughput", "latency", "ms", "speed", "benchmark"]):
                claim_type = "performance"
            elif any(w in s_clean.lower() for w in ["acid", "transaction", "consistency", "compliance"]):
                claim_type = "feature"

            claims.append({
                "statement": s_clean,
                "type": claim_type,
                "source_type": source_type,
                "reliability_tier": "verified_benchmark" if "benchmark" in source_type else "vendor_claim",
            })

        return ToolResult(
            success=True,
            data={"doc_id": doc.get("id"), "claims": claims, "count": len(claims)},
        )


class CompareTechnologyMetricsTool(Tool):
    """Compares candidate technologies across cost, latency, throughput, and constraint satisfaction."""

    name: str = "compare_technology_metrics"
    description: str = (
        "Builds a structured comparison matrix of candidate technologies against required constraints, "
        "highlighting tradeoffs and constraint violations."
    )
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "candidates": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of technology profiles with 'name', 'cost_usd_mo', 'latency_ms', 'features'.",
            },
            "constraints": {
                "type": "object",
                "description": "Hard constraints (e.g. {'max_cost_usd_mo': 500, 'required_features': ['ACID']}).",
            },
        },
        "required": ["candidates", "constraints"],
    }

    @property
    def risk_level(self) -> str:
        return "LOW"

    @property
    def category(self) -> str:
        return "research"

    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        candidates = arguments.get("candidates", [])
        constraints = arguments.get("constraints", {})

        matrix: List[Dict[str, Any]] = []
        max_cost = constraints.get("max_cost_usd_mo")
        max_lat = constraints.get("max_latency_ms")
        min_throughput = constraints.get("min_throughput_qps")
        required_features = [f.lower() for f in constraints.get("required_features", [])]

        for cand in candidates:
            if not isinstance(cand, dict):
                continue
            name = cand.get("name", "Unknown")
            cost = cand.get("cost_usd_mo")
            lat = cand.get("latency_ms")
            tput = cand.get("throughput_qps")
            features = [str(f).lower() for f in cand.get("features", [])]

            violations = []
            if max_cost is not None and cost is not None and float(cost) > float(max_cost):
                violations.append(f"Cost ${cost}/mo exceeds budget limit ${max_cost}/mo")
            if max_lat is not None and lat is not None and float(lat) > float(max_lat):
                violations.append(f"Latency {lat}ms exceeds SLA limit {max_lat}ms")
            if min_throughput is not None and tput is not None and float(tput) < float(min_throughput):
                violations.append(f"Throughput {tput} QPS below requirement {min_throughput} QPS")
            for rf in required_features:
                if not any(rf in f for f in features):
                    violations.append(f"Missing required capability '{rf}'")

            matrix.append({
                "technology": name,
                "cost_usd_mo": cost,
                "latency_ms": lat,
                "throughput_qps": tput,
                "satisfies_all_constraints": (len(violations) == 0),
                "violations": violations,
            })

        viable = [m["technology"] for m in matrix if m["satisfies_all_constraints"]]

        return ToolResult(
            success=True,
            data={
                "matrix": matrix,
                "viable_candidates": viable,
                "constraints_evaluated": constraints,
            },
        )


def register_research_tools(registry: ToolRegistry) -> None:
    """Register all research & evidence comparison tools into a ToolRegistry."""
    registry.register(SearchDocumentEvidenceTool())
    registry.register(ExtractEvidenceClaimsTool())
    registry.register(CompareTechnologyMetricsTool())
