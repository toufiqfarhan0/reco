"""Domain-agnostic Goal & Task Specification Parser for Reco."""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from reco.core.interfaces import ModelGateway, ModelMessage, ModelRequest
from reco.core.task_spec import (
    Capability,
    EvaluatorSpecification,
    Subtask,
    TaskSpecification,
    ToolRecommendation,
)
from reco.logging import get_logger
from reco.tools.registry import ToolRegistry

logger = get_logger("core.goal_analyzer")


def normalize_goal(goal: str) -> str:
    """Deterministic preprocessing and normalization of the user goal statement."""
    if not goal or not goal.strip():
        raise ValueError("Goal cannot be empty or whitespace only.")

    cleaned = goal.strip()
    if len(cleaned) > 10000:
        cleaned = cleaned[:10000]

    # Consolidate whitespace while preserving line structure
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
    return cleaned


class GoalAnalyzer:
    """Transforms a natural language goal and tool catalog into a structured TaskSpecification."""

    def __init__(
        self,
        model_gateway: Optional[ModelGateway] = None,
        tool_registry: Optional[ToolRegistry] = None,
        fallback_on_error: bool = True,
    ):
        self.model_gateway = model_gateway
        self.tool_registry = tool_registry
        self.fallback_on_error = fallback_on_error

    async def analyze(
        self,
        goal: str,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        evaluator_spec: Optional[Dict[str, Any]] = None,
    ) -> TaskSpecification:
        """Parse and decompose goal into a validated TaskSpecification."""
        normalized = normalize_goal(goal)

        # 1. Resolve available tools catalog
        catalog = available_tools or []
        if not catalog and self.tool_registry:
            catalog = self.tool_registry.list_schemas()

        available_tool_ids = [t["name"] for t in catalog]

        # 2. If model_gateway is available, attempt LLM semantic decomposition
        last_err: Optional[Exception] = None
        if self.model_gateway:
            try:
                spec = await self._decompose_with_model(
                    original_goal=goal,
                    normalized_goal=normalized,
                    catalog=catalog,
                    evaluator_spec=evaluator_spec,
                )
                # Enforce tool integrity (never allow fabricated tools)
                self._sanitize_tools(spec, available_tool_ids)
                return spec
            except Exception as err:
                last_err = err
                logger.warning(
                    f"LLM decomposition failed ({err}). Falling back to deterministic analysis."
                )
                if not self.fallback_on_error:
                    raise RuntimeError(f"LLM decomposition failed: {err}") from err

        # 3. Deterministic rule-based analysis (fallback and provider-free mode)
        spec = self._deterministic_decompose(
            original_goal=goal,
            normalized_goal=normalized,
            catalog=catalog,
            evaluator_spec=evaluator_spec,
        )
        if last_err:
            spec.metadata["llm_error"] = str(last_err)
            spec.ambiguity_flags.append(f"llm_parsing_error: {last_err}")

        self._sanitize_tools(spec, available_tool_ids)
        return spec

    def _sanitize_tools(self, spec: TaskSpecification, available_tool_ids: List[str]) -> None:
        """Filter out any suggested tools that do not exist in the available tool catalog."""
        available_set = set(available_tool_ids)

        # Filter suggested_tool_bindings
        valid_bindings = []
        for b in spec.suggested_tool_bindings:
            if b.tool_name in available_set:
                valid_bindings.append(b)
            else:
                spec.ambiguity_flags.append(
                    f"unavailable_capability: tool '{b.tool_name}' requested but not in catalog"
                )
        spec.suggested_tool_bindings = valid_bindings

        # Filter subtask preferred tools
        for subtask in spec.subtasks:
            subtask.preferred_tools = [t for t in subtask.preferred_tools if t in available_set]

        # Enforce available_tool_ids is recorded
        spec.available_tool_ids = list(available_tool_ids)

    async def _decompose_with_model(
        self,
        original_goal: str,
        normalized_goal: str,
        catalog: List[Dict[str, Any]],
        evaluator_spec: Optional[Dict[str, Any]],
    ) -> TaskSpecification:
        """Invoke ModelGateway to produce a structured TaskSpecification with one repair attempt."""
        prompt = self._build_prompt(normalized_goal, catalog, evaluator_spec)
        req = ModelRequest(
            messages=[
                ModelMessage(
                    role="system",
                    content=(
                        "You are an expert AI task architect. Decompose the user goal into a structured "
                        "TaskSpecification JSON object. Output strictly valid JSON matching the schema, "
                        "with no markdown prose or formatting outside the JSON."
                    ),
                ),
                ModelMessage(role="user", content=prompt),
            ],
            temperature=0.0,
        )

        resp = await self.model_gateway.generate(req)
        content = resp.content.strip()

        # Attempt initial JSON parsing and validation
        first_error: Optional[Exception] = None
        try:
            parsed_data = self._extract_json(content)
            if evaluator_spec and "evaluator_requirements" not in parsed_data:
                parsed_data["evaluator_requirements"] = evaluator_spec
            return self._build_spec_from_dict(original_goal, normalized_goal, parsed_data, catalog)
        except Exception as parse_err:
            first_error = parse_err
            logger.warning(f"Initial JSON parse failed: {parse_err}. Attempting bounded repair.")

        # Bounded repair attempt (exactly 1 retry)
        repair_req = ModelRequest(
            messages=[
                ModelMessage(
                    role="system",
                    content="Fix the following text so that it is strictly valid JSON matching the TaskSpecification schema.",
                ),
                ModelMessage(role="user", content=f"Raw text:\n{content}\nParsing Error:\n{first_error}"),
            ],
            temperature=0.0,
        )
        repair_resp = await self.model_gateway.generate(repair_req)
        parsed_data = self._extract_json(repair_resp.content.strip())
        if evaluator_spec and "evaluator_requirements" not in parsed_data:
            parsed_data["evaluator_requirements"] = evaluator_spec
        spec = self._build_spec_from_dict(original_goal, normalized_goal, parsed_data, catalog)
        spec.metadata["repaired"] = True
        return spec

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON dictionary from raw model text, stripping markdown backticks if present."""
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
        elif "{" in text and "}" in text:
            start = text.index("{")
            end = text.rindex("}") + 1
            text = text[start:end]
        return json.loads(text)

    def _build_spec_from_dict(
        self,
        original_goal: str,
        normalized_goal: str,
        data: Dict[str, Any],
        catalog: List[Dict[str, Any]],
    ) -> TaskSpecification:
        """Construct and validate TaskSpecification from dictionary data."""
        data["original_goal"] = original_goal
        data["normalized_goal"] = normalized_goal
        data["available_tool_ids"] = [t["name"] for t in catalog]
        return TaskSpecification(**data)

    def _build_prompt(
        self,
        goal: str,
        catalog: List[Dict[str, Any]],
        evaluator_spec: Optional[Dict[str, Any]],
    ) -> str:
        """Construct the prompt template providing tools catalog and target schema."""
        tools_summary = [
            {"name": t["name"], "description": t["description"], "risk_level": t.get("risk_level", "low")}
            for t in catalog
        ]
        return (
            f"GOAL:\n{goal}\n\n"
            f"AVAILABLE TOOLS CATALOG:\n{json.dumps(tools_summary, indent=2)}\n\n"
            f"OPTIONAL EVALUATOR SPECIFICATION:\n{json.dumps(evaluator_spec or {}, indent=2)}\n\n"
            "Return a JSON object with: domain, objective, subtasks (array with id, description, objective, "
            "required_capabilities, preferred_tools, dependencies), required_capabilities (array of strings), "
            "suggested_tool_bindings (array with tool_name, relevance_score, reason, required), inputs, expected_outputs, "
            "constraints, verification_requirements, risk_level, side_effect_requirements, ambiguity_flags, "
            "requires_clarification, confidence."
        )

    def _deterministic_decompose(
        self,
        original_goal: str,
        normalized_goal: str,
        catalog: List[Dict[str, Any]],
        evaluator_spec: Optional[Dict[str, Any]],
    ) -> TaskSpecification:
        """Pure-Python deterministic goal analysis without external LLM inference."""
        lower_goal = normalized_goal.lower()

        # 1. Domain Detection
        domain = "general"
        if any(w in lower_goal for w in ["reconcil", "ledger", "bank", "invoice", "payment", "fee", "tax", "statement"]):
            domain = "finance"
        elif any(w in lower_goal for w in ["research", "compare", "paper", "literature", "search", "overview", "survey"]):
            domain = "research"
        elif any(w in lower_goal for w in ["csv", "data", "dataframe", "metric", "column", "anomaly", "dataset"]):
            domain = "data"
        elif any(w in lower_goal for w in ["code", "debug", "test", "function", "bug", "syntax", "python"]):
            domain = "coding"

        # 2. Capabilities Extraction
        caps: Set[Capability] = {Capability.REASONING}
        if any(w in lower_goal for w in ["search", "find", "retrieve", "look up", "query"]):
            caps.add(Capability.RETRIEVAL)
            caps.add(Capability.STRUCTURED_LOOKUP)
        if any(w in lower_goal for w in ["calculat", "sum", "differenc", "rate", "fee", "variance", "reconcil", "ledger", "arithmetic"]):
            caps.add(Capability.CALCULATION)
        if any(w in lower_goal for w in ["compar", "match", "correlat", "versus", "diff", "reconcil"]):
            caps.add(Capability.COMPARISON)
        if any(w in lower_goal for w in ["classif", "categor", "tag", "label"]):
            caps.add(Capability.CLASSIFICATION)
        if any(w in lower_goal for w in ["extract", "parse", "normaliz", "ingest", "csv", "json"]):
            caps.add(Capability.EXTRACTION)
            caps.add(Capability.TRANSFORMATION)
        if any(w in lower_goal for w in ["verif", "audit", "check", "validat", "confirm"]):
            caps.add(Capability.VERIFICATION)
        if any(w in lower_goal for w in ["summar", "report", "overview", "brief"]):
            caps.add(Capability.SUMMARIZATION)
        if any(w in lower_goal for w in ["anomal", "fraud", "outlier", "exception", "discrepanc"]):
            caps.add(Capability.ANOMALY_DETECTION)
        if any(w in lower_goal for w in ["evidenc", "proof", "cite", "citation"]):
            caps.add(Capability.EVIDENCE_COLLECTION)
        if any(w in lower_goal for w in ["decid", "choos", "select"]):
            caps.add(Capability.DECISION_MAKING)
        if any(w in lower_goal for w in ["diagnos", "debug", "root cause", "troubleshoot"]):
            caps.add(Capability.REASONING)
            caps.add(Capability.VERIFICATION)

        # 3. Tool Recommendation & Relevance Scoring
        available_ids = [t["name"] for t in catalog]
        recommendations: List[ToolRecommendation] = []
        has_side_effect = False
        highest_risk = "low"

        for tool in catalog:
            t_name = tool["name"].lower()
            t_desc = tool.get("description", "").lower()

            # Score overlap
            score = 0.0
            reasons = []

            tokens = t_name.replace("_", " ").split()
            for token in tokens:
                if len(token) > 2 and token in lower_goal:
                    score += 0.35
                    reasons.append(f"Keyword '{token}' matches goal.")

            if score > 0.0 or any(c.value in t_desc for c in caps):
                relevance = min(1.0, max(0.40, score))
                is_req = relevance >= 0.70
                recommendations.append(
                    ToolRecommendation(
                        tool_name=tool["name"],
                        relevance_score=round(relevance, 2),
                        reason="; ".join(reasons) or "Tool capabilities align with extracted task requirements.",
                        required=is_req,
                        confidence=0.85,
                    )
                )

            # Check side effects and risk from tools
            if tool.get("side_effect", False):
                has_side_effect = True
                if highest_risk == "low":
                    highest_risk = "medium"
            if tool.get("risk_level") == "high":
                highest_risk = "high"
            elif tool.get("risk_level") == "medium" and highest_risk == "low":
                highest_risk = "medium"

        # Check goal text for mutations
        mutation_words = ["delete", "drop", "update", "modify", "write", "send", "transfer", "execute trade"]
        if any(w in lower_goal for w in mutation_words):
            has_side_effect = True
            if highest_risk == "low":
                highest_risk = "medium"

        recommendations.sort(key=lambda r: r.relevance_score, reverse=True)

        # 4. Constraints Extraction
        constraints = []
        if any(w in lower_goal for w in ["evidence", "cite", "citation"]):
            constraints.append("Must cite evidence for each finding or match")
        if "json" in lower_goal:
            constraints.append("Output must strictly adhere to JSON format")
        if any(w in lower_goal for w in ["budget", "cost", "tokens", "usd", "$"]):
            constraints.append("Must respect execution budget limits")
        if any(w in lower_goal for w in ["latency", "timeout", "seconds", "fast"]):
            constraints.append("Must satisfy latency constraints")
        if any(w in lower_goal for w in ["currency", "decimal", "precision"]):
            constraints.append("Currency amounts and precision must be strictly preserved")
        if any(w in lower_goal for w in ["read-only", "read only", "no side effect", "no side-effect"]):
            constraints.append("No external side effects permitted")
        if any(w in lower_goal for w in ["deterministic", "exact"]):
            constraints.append("Must use exact deterministic calculations")

        # 5. Verification Requirements
        verification_reqs = []
        if Capability.CALCULATION in caps or any(w in lower_goal for w in ["arithmetic", "difference", "sum", "calc"]):
            verification_reqs.append("Arithmetic verification of numerical differences and totals")
        if Capability.COMPARISON in caps or Capability.ANOMALY_DETECTION in caps or "exception" in lower_goal:
            verification_reqs.append("Dual-check verification of exception classifications and false positives")
        if Capability.EXTRACTION in caps or "schema" in lower_goal:
            verification_reqs.append("Schema and null-value check on extracted input fields")
        if any(w in lower_goal for w in ["duplicate", "dedup"]):
            verification_reqs.append("Duplicate detection check across records")
        if any(w in lower_goal for w in ["complete", "completeness", "coverage"]):
            verification_reqs.append("Completeness check of dataset coverage")
        if any(w in lower_goal for w in ["consistent", "consistency"]):
            verification_reqs.append("Consistency check across cross-referenced records")
        if any(w in lower_goal for w in ["source", "citation", "cite", "evidence"]):
            verification_reqs.append("Source verification and citation validation")

        # 6. Ambiguity Flags
        ambiguities = []
        if not any(w in lower_goal for w in ["file", "data", "records", "statement", "query", "transactions", "csv", "logs", "code", "suite"]):
            ambiguities.append("missing_input: specific input dataset or file path was not defined")
        if not any(w in lower_goal for w in ["threshold", "criteria", "complete", "valid", "accuracy", "zero", "tolerance", "success"]):
            ambiguities.append("unspecified_success_criteria: quantitative threshold not defined")
        if not any(w in lower_goal for w in ["json", "report", "table", "summary", "list", "markdown", "csv"]):
            ambiguities.append("ambiguous_output_format: output format was not explicitly requested")
        if len(lower_goal.split()) < 4:
            ambiguities.append("unclear_scope: goal statement is too brief to reliably determine execution scope")
        if ("read-only" in lower_goal or "read only" in lower_goal) and any(w in lower_goal for w in mutation_words):
            ambiguities.append("conflicting_requirements: goal specifies read-only but requests state mutation")

        # 7. Confidence Score
        confidence = 0.90
        for _ in ambiguities:
            confidence -= 0.10
        confidence = round(max(0.20, min(1.0, confidence)), 2)

        # 8. Domain-specific Inferred Inputs & Outputs
        if domain == "finance":
            inputs = {
                "bank_transactions": {"type": "array", "description": "Bank statement records", "inferred": True},
                "general_ledger": {"type": "array", "description": "General ledger records", "inferred": True},
            }
            outputs = {
                "reconciliation_summary": {"type": "object", "description": "Matches, variances, and exceptions", "inferred": True}
            }
        elif domain == "research":
            inputs = {
                "research_query": {"type": "string", "description": "Subject or topic of inquiry", "inferred": True}
            }
            outputs = {
                "comparative_analysis": {"type": "object", "description": "Comparative synthesis and citations", "inferred": True}
            }
        elif domain == "data":
            inputs = {
                "dataset": {"type": "tabular_or_csv", "description": "Tabular records or dataset", "inferred": True}
            }
            outputs = {
                "anomalies_and_causes": {"type": "object", "description": "Identified anomalies and root causes", "inferred": True}
            }
        elif domain == "coding":
            inputs = {
                "test_suite_or_logs": {"type": "string_or_records", "description": "Test failures or diagnostic logs", "inferred": True}
            }
            outputs = {
                "diagnosis_and_fix": {"type": "object", "description": "Root cause analysis and fix proposal", "inferred": True}
            }
        else:
            inputs = {"dataset": {"type": "array_or_object", "description": "Primary input data", "inferred": True}}
            outputs = {"result": {"type": "object", "description": "Processed task outcome", "inferred": True}}

        # 9. Subtasks Generation
        subtasks: List[Subtask] = []
        pref_tools_0 = [r.tool_name for r in recommendations[:1]]
        pref_tools_1 = [r.tool_name for r in recommendations[1:3]]

        subtasks.append(
            Subtask(
                id="subtask_1",
                description="Ingest, validate, and normalize input records",
                objective="Produce clean validated input collections",
                required_capabilities=[c for c in [Capability.EXTRACTION, Capability.RETRIEVAL, Capability.TRANSFORMATION] if c in caps] or [Capability.REASONING],
                preferred_tools=pref_tools_0,
                expected_input=inputs,
                expected_output={"normalized_records": {"type": "array"}},
                dependencies=[],
            )
        )
        subtasks.append(
            Subtask(
                id="subtask_2",
                description="Execute core comparison, calculation, and anomaly detection",
                objective="Identify matches, compute variances, and isolate exceptions",
                required_capabilities=[c for c in [Capability.COMPARISON, Capability.CALCULATION, Capability.ANOMALY_DETECTION, Capability.REASONING] if c in caps] or [Capability.REASONING],
                preferred_tools=pref_tools_1,
                expected_input={"normalized_records": {"type": "array"}},
                expected_output={"raw_results": {"type": "object"}},
                dependencies=["subtask_1"],
            )
        )
        subtasks.append(
            Subtask(
                id="subtask_3",
                description="Verify results and formulate structured output report",
                objective="Audit discrepancies and format final deliverable",
                required_capabilities=[Capability.VERIFICATION, Capability.REASONING],
                verification_needed=True,
                expected_input={"raw_results": {"type": "object"}},
                expected_output=outputs,
                dependencies=["subtask_2"],
            )
        )

        if evaluator_spec:
            eval_spec_obj = EvaluatorSpecification(**evaluator_spec)
        else:
            eval_spec_obj = EvaluatorSpecification(
                required_output_properties=list(outputs.keys()),
                correctness_criteria=["Produce valid output matching schema", "Satisfy domain accuracy thresholds"],
                threshold_conditions={"accuracy": 0.70, "reliability": 0.95},
            )

        return TaskSpecification(
            original_goal=original_goal,
            normalized_goal=normalized_goal,
            domain=domain,
            objective=normalized_goal.split(".")[0],
            subtasks=subtasks,
            required_capabilities=list(caps),
            available_tool_ids=available_ids,
            suggested_tool_bindings=recommendations,
            inputs=inputs,
            expected_outputs=outputs,
            constraints=constraints,
            verification_requirements=verification_reqs,
            risk_level=highest_risk,  # type: ignore
            side_effect_requirements=has_side_effect,
            ambiguity_flags=ambiguities,
            requires_clarification=(len(ambiguities) >= 2),
            confidence=confidence,
            evaluator_requirements=eval_spec_obj,
            metadata={"parser_mode": "deterministic_rule_based"},
        )

