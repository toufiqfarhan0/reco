"""Goal Decomposition and Task Specification Analyzer."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union
from reco.core.task_spec import TaskSpecification


class GoalAnalyzer:
    """Analyzes natural language goals and synthesizes structured TaskSpecifications."""

    # Domain keyword patterns
    DOMAIN_PATTERNS = {
        "data_analysis": [
            r"tabular", r"data\b", r"distribution", r"anomal", r"statistic",
            r"outlier", r"dataset", r"dataframe", r"metrics", r"aggregate"
        ],
        "code_generation": [
            r"code\b", r"python", r"syntax", r"refactor", r"debug", r"lint",
            r"function", r"repository", r"pull request"
        ],
        "web_research": [
            r"web\b", r"search", r"scrape", r"document", r"article",
            r"summar", r"retriev", r"research"
        ],
        "financial_audit": [
            r"financ", r"transaction", r"invoice", r"ledger", r"audit",
            r"reconcil", r"fraud", r"balance"
        ],
        "system_anomaly": [
            r"system anomaly", r"metric time.?series", r"threshold alert", r"root.?cause",
            r"z.?score", r"error log", r"server anomaly"
        ],
        "research_synthesis": [
            r"research synthesis", r"cross.?referenc", r"entity extraction",
            r"metric comparison", r"multi.?source summary", r"paper synthesis"
        ]
    }

    # Capability keyword patterns
    CAPABILITY_PATTERNS = {
        "tabular_parsing": [r"tabular", r"dataset", r"csv", r"table", r"data"],
        "distribution_analysis": [r"distribution", r"statistic", r"mean", r"median", r"variance", r"quantil"],
        "anomaly_detection": [r"anomal", r"outlier", r"deviat", r"abnormal"],
        "data_cleaning": [r"clean", r"null", r"missing", r"impute"],
        "code_analysis": [r"code", r"ast", r"syntax", r"parse code"],
        "code_refactoring": [r"refactor", r"rewrite", r"optimize code"],
        "syntax_validation": [r"lint", r"syntax", r"type check"],
        "document_retrieval": [r"search", r"retrieve", r"crawl", r"fetch"],
        "information_extraction": [r"extract", r"entity", r"key insight"],
        "summarization": [r"summar", r"overview", r"digest"],
        "transaction_parsing": [r"transaction", r"invoice", r"payment"],
        "reconciliation": [r"reconcil", r"balance", r"ledger"],
        "fraud_detection": [r"fraud", r"suspicious", r"unauthorized"],
        "zscore_computation": [r"z.?score", r"time.?series deviat"],
        "threshold_monitoring": [r"threshold alert", r"threshold breach", r"check.?threshold"],
        "error_extraction": [r"error log", r"log burst", r"extract.*error", r"root.?cause"],
        "entity_extraction": [r"extract.*entit", r"entity extract"],
        "metric_comparison": [r"compare.*metric", r"metric.*comparison", r"cross.?referenc"]
    }

    def __init__(self, default_latency_ms: float = 5000.0, default_cost_usd: float = 0.05):
        self.default_latency_ms = default_latency_ms
        self.default_cost_usd = default_cost_usd

    def analyze(
        self,
        goal: str,
        available_tools: Optional[List[Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> TaskSpecification:
        """Decompose a natural language goal into a structured TaskSpecification.

        Args:
            goal: Natural language goal string.
            available_tools: Optional list of available tool names or ToolDefinitions.
            constraints: Optional budget / latency / criteria overrides.

        Returns:
            TaskSpecification object.
        """
        constraints = constraints or {}
        normalized_goal = goal.strip()

        # 1. Infer domain
        domain = self._infer_domain(normalized_goal)

        # 2. Extract capabilities
        capabilities = self._extract_capabilities(normalized_goal, domain, available_tools)

        # 3. Generate domain-aligned schemas
        input_schema, output_schema = self._generate_schemas(domain, capabilities)

        # 4. Determine budget constraints
        latency_budget = constraints.get("latency_budget_ms", self.default_latency_ms)
        cost_budget = constraints.get("cost_budget_usd", self.default_cost_usd)
        eval_criteria = constraints.get(
            "evaluation_criteria",
            ["accuracy", "reliability", "latency", "cost"]
        )

        return TaskSpecification(
            goal=normalized_goal,
            domain=domain,
            required_capabilities=capabilities,
            input_schema=input_schema,
            output_schema=output_schema,
            latency_budget_ms=latency_budget,
            cost_budget_usd=cost_budget,
            evaluation_criteria=eval_criteria,
            metadata={
                "extracted_domain": domain,
                "tool_count": len(available_tools) if available_tools else 0,
                **constraints.get("metadata", {})
            }
        )

    def _infer_domain(self, text: str) -> str:
        """Score and classify domain based on keyword presence."""
        scores: Dict[str, int] = {d: 0 for d in self.DOMAIN_PATTERNS}
        lower_text = text.lower()

        for domain, patterns in self.DOMAIN_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lower_text):
                    scores[domain] += 1

        best_domain = max(scores, key=scores.get)
        if scores[best_domain] > 0:
            return best_domain
        return "general"

    def _extract_capabilities(
        self,
        text: str,
        domain: str,
        available_tools: Optional[List[Any]] = None
    ) -> List[str]:
        """Extract required capabilities based on text and domain defaults."""
        lower_text = text.lower()
        extracted: List[str] = []

        for cap, patterns in self.CAPABILITY_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lower_text):
                    if cap not in extracted:
                        extracted.append(cap)
                    break

        # If domain is data_analysis and nothing extracted, supply core defaults
        if domain == "data_analysis" and not extracted:
            extracted = ["tabular_parsing", "distribution_analysis", "anomaly_detection"]
        elif domain == "code_generation" and not extracted:
            extracted = ["code_analysis", "syntax_validation"]
        elif domain == "web_research" and not extracted:
            extracted = ["document_retrieval", "summarization"]
        elif domain == "financial_audit" and not extracted:
            extracted = ["transaction_parsing", "reconciliation"]
        elif domain == "system_anomaly" and not extracted:
            extracted = ["zscore_computation", "threshold_monitoring", "error_extraction"]
        elif domain == "research_synthesis" and not extracted:
            extracted = ["entity_extraction", "metric_comparison", "summarization"]

        # If available tools are provided, match their capabilities
        if available_tools:
            tool_caps = set()
            for t in available_tools:
                if hasattr(t, "capabilities") and isinstance(t.capabilities, list):
                    tool_caps.update(t.capabilities)
                elif isinstance(t, str):
                    tool_caps.add(t)

            # Ensure tool capabilities that overlap with extracted are aligned
            for tc in tool_caps:
                if any(k in tc for k in ["tabular", "distribution", "anomaly", "summary"]):
                    if tc not in extracted and any(k in lower_text for k in ["data", "distribution", "anomal"]):
                        extracted.append(tc)

        return extracted

    def _generate_schemas(
        self,
        domain: str,
        capabilities: List[str]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Construct domain-appropriate input and output JSON schemas."""
        if domain == "data_analysis":
            input_schema = {
                "type": "object",
                "properties": {
                    "dataset": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Tabular records as list of row objects"
                    }
                },
                "required": ["dataset"]
            }

            output_properties: Dict[str, Any] = {
                "summary": {"type": "object", "description": "Tabular summary metrics"}
            }
            required_outputs = []

            if "distribution_analysis" in capabilities:
                output_properties["distributions"] = {
                    "type": "object",
                    "description": "Calculated distributions per numeric column"
                }
                required_outputs.append("distributions")

            if "anomaly_detection" in capabilities:
                output_properties["anomalies"] = {
                    "type": "array",
                    "description": "Detected anomalous records"
                }
                required_outputs.append("anomalies")

            if not required_outputs:
                required_outputs = ["summary"]

            output_schema = {
                "type": "object",
                "properties": output_properties,
                "required": required_outputs
            }
            return input_schema, output_schema

        elif domain == "code_generation":
            input_schema = {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code snippet"}
                },
                "required": ["code"]
            }
            output_schema = {
                "type": "object",
                "properties": {
                    "analysis": {"type": "object"},
                    "refactored_code": {"type": "string"}
                },
                "required": ["analysis"]
            }
            return input_schema, output_schema

        # Default generic schema
        input_schema = {
            "type": "object",
            "properties": {
                "input_data": {"type": "string", "description": "Generic payload"}
            },
            "required": ["input_data"]
        }
        output_schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string", "description": "Execution output"}
            },
            "required": ["result"]
        }
        return input_schema, output_schema
