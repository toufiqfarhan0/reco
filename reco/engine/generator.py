"""Domain-agnostic Architecture Generator (V0) for Reco."""

import json
import re
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field

from reco.core.interfaces import ModelGateway, ModelMessage, ModelRequest
from reco.core.task_spec import (
    Capability,
    EvaluatorSpecification,
    Subtask,
    TaskSpecification,
)
from reco.engine.models import EdgeModel, GraphDefinition, GraphValidationError, NodeModel

from reco.logging import get_logger
from reco.tools.registry import ToolRegistry

logger = get_logger("engine.generator")

# Maximum complexity boundaries for V0
MAX_NODE_COUNT = 10
MAX_EDGE_COUNT = 20
MAX_TOOLS_PER_NODE = 4
MAX_GRAPH_DEPTH = 6


class ArchitectureValidationResult(BaseModel):
    """Structured report detailing structural, capability, tool, and risk validation of a graph."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    capability_coverage: Dict[str, bool] = Field(default_factory=dict)
    tool_authorization_ok: bool = True
    executable: bool = True
    risk_checks: Dict[str, Any] = Field(default_factory=dict)
    graph_metrics: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class ArchitectureQualityScore(BaseModel):
    """Interpretable deterministic pre-execution quality metric for an architecture."""
    overall_score: float = Field(..., ge=0.0, le=1.0)
    capability_coverage_score: float = Field(..., ge=0.0, le=1.0)
    tool_validity_score: float = Field(..., ge=0.0, le=1.0)
    structural_efficiency_score: float = Field(..., ge=0.0, le=1.0)
    risk_alignment_score: float = Field(..., ge=0.0, le=1.0)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class ArchitectureGenerator:
    """Synthesizes valid, executable Agent GraphDefinitions from TaskSpecifications."""

    def __init__(
        self,
        model_gateway: Optional[ModelGateway] = None,
        tool_registry: Optional[ToolRegistry] = None,
        fallback_on_error: bool = True,
    ):
        self.model_gateway = model_gateway
        self.tool_registry = tool_registry
        self.fallback_on_error = fallback_on_error

    async def generate(
        self,
        task_spec: TaskSpecification,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        evaluator_spec: Optional[EvaluatorSpecification] = None,
    ) -> GraphDefinition:
        """Generate a valid, executable GraphDefinition from a TaskSpecification."""
        graph, _, _ = await self.generate_with_validation(
            task_spec=task_spec,
            available_tools=available_tools,
            evaluator_spec=evaluator_spec,
        )
        return graph

    async def generate_with_validation(
        self,
        task_spec: TaskSpecification,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        evaluator_spec: Optional[EvaluatorSpecification] = None,
    ) -> Tuple[GraphDefinition, ArchitectureValidationResult, ArchitectureQualityScore]:
        """Generate an architecture along with its validation report and quality score."""
        # 1. Resolve tool catalog
        catalog = available_tools or []
        if not catalog and self.tool_registry:
            catalog = self.tool_registry.list_schemas()

        active_eval = evaluator_spec or task_spec.evaluator_requirements

        # 2. Attempt LLM generation if ModelGateway is available
        graph: Optional[GraphDefinition] = None
        last_err: Optional[Exception] = None

        if self.model_gateway:
            try:
                graph = await self._generate_with_model(
                    task_spec=task_spec,
                    catalog=catalog,
                    evaluator_spec=active_eval,
                )
            except Exception as err:
                last_err = err
                logger.warning(f"LLM architecture generation failed: {err}")
                if not self.fallback_on_error:
                    raise RuntimeError(f"Architecture generation failed: {err}") from err

        # 3. Fallback deterministic generation if model unavailable or failed
        if graph is None:
            graph = self._generate_fallback(
                task_spec=task_spec,
                catalog=catalog,
                evaluator_spec=active_eval,
            )
            if last_err:
                graph.metadata["llm_generation_error"] = str(last_err)

        # 4. Validate architecture and compute quality score
        validation = self.validate_architecture(graph, task_spec, catalog)
        quality = self.evaluate_quality(graph, task_spec, validation)

        graph.metadata["validation_result"] = validation.model_dump(mode="json")
        graph.metadata["quality_score"] = quality.model_dump(mode="json")

        return graph, validation, quality

    def validate_architecture(
        self,
        graph: GraphDefinition,
        task_spec: TaskSpecification,
        catalog: List[Dict[str, Any]],
    ) -> ArchitectureValidationResult:
        """Deterministically validate topological, tool, capability, and risk invariants."""
        errors: List[str] = []
        warnings: List[str] = []
        catalog_map = {t["name"]: t for t in catalog}
        catalog_ids = set(catalog_map.keys())

        # 1. Topological & DAG Invariants (Kahn's algorithm, connectivity, cycle check)
        try:
            graph.validate_graph()
        except GraphValidationError as ve:
            errors.append(f"DAG validation failed: {ve}")

        # 2. Graph Complexity Boundaries
        node_count = len(graph.nodes)
        edge_count = len(graph.edges)
        if node_count > MAX_NODE_COUNT:
            errors.append(f"Node count ({node_count}) exceeds maximum limit of {MAX_NODE_COUNT}")
        if edge_count > MAX_EDGE_COUNT:
            errors.append(f"Edge count ({edge_count}) exceeds maximum limit of {MAX_EDGE_COUNT}")

        max_depth = self._calculate_max_depth(graph)
        if max_depth > MAX_GRAPH_DEPTH:
            errors.append(f"Graph execution depth ({max_depth}) exceeds maximum allowed depth of {MAX_GRAPH_DEPTH}")

        # 3. Tool Authorization & Anti-Fabrication
        tool_auth_ok = True
        side_effect_tools_used: List[str] = []
        high_risk_tools_used: List[str] = []
        tools_per_node: Dict[str, int] = {}

        for nid, node in graph.nodes.items():
            tools_per_node[nid] = len(node.tools)
            if len(node.tools) > MAX_TOOLS_PER_NODE:
                errors.append(f"Node '{nid}' assigns {len(node.tools)} tools, exceeding limit of {MAX_TOOLS_PER_NODE}")

            for t_name in node.tools:
                if t_name not in catalog_ids:
                    tool_auth_ok = False
                    errors.append(f"Unauthorized/fabricated tool '{t_name}' on node '{nid}' is not in the supplied catalog")
                else:
                    t_meta = catalog_map[t_name]
                    if t_meta.get("side_effect", False):
                        side_effect_tools_used.append(t_name)
                    if t_meta.get("risk_level") == "high":
                        high_risk_tools_used.append(t_name)

        # 4. Risk & Side-Effect Policy
        risk_aligned = True
        if not task_spec.side_effect_requirements and side_effect_tools_used:
            risk_aligned = False
            errors.append(
                f"Read-only task assigned side-effect tools: {sorted(list(set(side_effect_tools_used)))}"
            )

        if task_spec.risk_level == "low" and high_risk_tools_used:
            warnings.append(
                f"Low-risk task contains high-risk tools: {sorted(list(set(high_risk_tools_used)))}"
            )

        # 5. Capability Coverage Analysis
        coverage_map: Dict[str, bool] = {}
        all_node_caps = self._extract_graph_capabilities(graph, catalog_map)

        for cap in task_spec.required_capabilities:
            cap_val = cap.value if hasattr(cap, "value") else str(cap)
            is_covered = cap_val in all_node_caps
            coverage_map[cap_val] = is_covered
            if not is_covered:
                warnings.append(f"Required capability '{cap_val}' has no matching node or tool binding in the architecture")

        # 6. Verification Node Logic
        needs_verification = bool(
            task_spec.verification_requirements
            or (task_spec.evaluator_requirements and task_spec.evaluator_requirements.correctness_criteria)
            or (Capability.VERIFICATION in task_spec.required_capabilities)
        )
        has_verification_node = any(
            "verif" in node.role.lower()
            or "audit" in node.role.lower()
            or "check" in node.role.lower()
            or "verification" in node.metadata.get("capabilities", [])
            for node in graph.nodes.values()
        )
        if needs_verification and not has_verification_node:
            warnings.append("Task specifies verification requirements but no dedicated verifier node was found in architecture")

        # Compile results
        is_valid = (len(errors) == 0) and tool_auth_ok
        risk_checks = {
            "read_only_aligned": risk_aligned,
            "side_effect_tools": sorted(list(set(side_effect_tools_used))),
            "high_risk_tools": sorted(list(set(high_risk_tools_used))),
        }
        graph_metrics = {
            "node_count": node_count,
            "edge_count": edge_count,
            "max_depth": max_depth,
            "tools_per_node": tools_per_node,
        }

        return ArchitectureValidationResult(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            capability_coverage=coverage_map,
            tool_authorization_ok=tool_auth_ok,
            executable=is_valid,
            risk_checks=risk_checks,
            graph_metrics=graph_metrics,
        )

    def evaluate_quality(
        self,
        graph: GraphDefinition,
        task_spec: TaskSpecification,
        validation: ArchitectureValidationResult,
    ) -> ArchitectureQualityScore:
        """Compute interpretable pre-execution architecture quality metrics."""
        # 1. Capability Coverage Score
        if validation.capability_coverage:
            covered = sum(1 for covered in validation.capability_coverage.values() if covered)
            cap_score = round(covered / len(validation.capability_coverage), 2)
        else:
            cap_score = 1.0

        # 2. Tool Validity Score
        tool_score = 1.0 if validation.tool_authorization_ok and not any("Unauthorized" in e for e in validation.errors) else 0.0

        # 3. Structural Efficiency Score
        # Optimal V0 graph has 2 to 5 nodes and depth 2 to 4
        node_count = len(graph.nodes)
        if node_count < 1 or not validation.valid:
            struct_score = 0.0
        elif 2 <= node_count <= 5:
            struct_score = 1.0
        elif node_count <= 8:
            struct_score = 0.80
        else:
            struct_score = 0.50

        # 4. Risk Alignment Score
        risk_score = 1.0 if validation.risk_checks.get("read_only_aligned", True) else 0.40

        # 5. Overall Weighted Score
        overall = round(
            0.35 * cap_score + 0.35 * tool_score + 0.15 * struct_score + 0.15 * risk_score,
            2,
        )

        return ArchitectureQualityScore(
            overall_score=overall,
            capability_coverage_score=cap_score,
            tool_validity_score=tool_score,
            structural_efficiency_score=struct_score,
            risk_alignment_score=risk_score,
            metrics={
                "valid": validation.valid,
                "node_count": node_count,
                "edge_count": len(graph.edges),
                "error_count": len(validation.errors),
                "warning_count": len(validation.warnings),
            },
        )

    async def _generate_with_model(
        self,
        task_spec: TaskSpecification,
        catalog: List[Dict[str, Any]],
        evaluator_spec: Optional[EvaluatorSpecification],
    ) -> GraphDefinition:
        """Invoke ModelGateway with structured prompting and bounded 1-retry repair."""
        prompt = self._build_generation_prompt(task_spec, catalog, evaluator_spec)
        req = ModelRequest(
            messages=[
                ModelMessage(
                    role="system",
                    content=(
                        "You are an expert Autonomous Agent Architect. Synthesize an executable Agent GraphDefinition "
                        "JSON for the given task. You must output strictly valid JSON matching the schema, with no prose."
                    ),
                ),
                ModelMessage(role="user", content=prompt),
            ],
            temperature=0.0,
        )

        resp = await self.model_gateway.generate(req)
        content = resp.content.strip()

        # Initial attempt
        first_err: Optional[Exception] = None
        try:
            parsed = self._extract_json(content)
            graph = self._build_graph_from_dict(parsed, catalog)
            graph.validate_graph()
            graph.metadata["generation_method"] = "llm"
            return graph
        except Exception as err:
            first_err = err
            logger.warning(f"Initial model architecture parsing failed: {err}. Attempting bounded repair.")

        # Bounded 1-retry repair
        repair_req = ModelRequest(
            messages=[
                ModelMessage(
                    role="system",
                    content="Fix the following text so that it is strictly valid JSON matching GraphDefinition schema.",
                ),
                ModelMessage(role="user", content=f"Raw text:\n{content}\nError:\n{first_err}"),
            ],
            temperature=0.0,
        )
        repair_resp = await self.model_gateway.generate(repair_req)
        parsed = self._extract_json(repair_resp.content.strip())
        graph = self._build_graph_from_dict(parsed, catalog)
        graph.validate_graph()
        graph.metadata["generation_method"] = "llm"
        graph.metadata["repaired"] = True
        return graph

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON dictionary from raw model text, stripping markdown if present."""
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
        elif "{" in text and "}" in text:
            start = text.index("{")
            end = text.rindex("}") + 1
            text = text[start:end]
        return json.loads(text)

    def _build_graph_from_dict(self, data: Dict[str, Any], catalog: List[Dict[str, Any]]) -> GraphDefinition:
        """Construct and sanitize GraphDefinition from parsed dictionary."""
        catalog_ids = {t["name"] for t in catalog}

        # Validate nodes mapping
        raw_nodes = data.get("nodes", {})
        nodes: Dict[str, NodeModel] = {}
        for nid, node_data in raw_nodes.items():
            if isinstance(node_data, dict):
                # Sanitize tools: keep only catalog tools
                node_tools = [t for t in node_data.get("tools", []) if t in catalog_ids]
                node_data["tools"] = node_tools
                nodes[nid] = NodeModel(**node_data)

        # Validate edges
        edges = [EdgeModel(**e) if isinstance(e, dict) else e for e in data.get("edges", [])]

        return GraphDefinition(
            graph_id=data.get("graph_id", "generated_graph_v0"),
            name=data.get("name", "Synthesized Agent Graph"),
            entry_node_id=data.get("entry_node_id", list(nodes.keys())[0] if nodes else ""),
            terminal_node_ids=data.get("terminal_node_ids", [list(nodes.keys())[-1]] if nodes else []),
            nodes=nodes,
            edges=edges,
            metadata=data.get("metadata", {}),
        )

    def _build_generation_prompt(
        self,
        task_spec: TaskSpecification,
        catalog: List[Dict[str, Any]],
        evaluator_spec: Optional[EvaluatorSpecification],
    ) -> str:
        """Create structured prompt with strict architecture guidelines."""
        tools_summary = [
            {
                "name": t["name"],
                "description": t["description"],
                "side_effect": t.get("side_effect", False),
                "risk_level": t.get("risk_level", "low"),
            }
            for t in catalog
        ]
        return (
            f"TASK OBJECTIVE:\n{task_spec.objective}\n\n"
            f"REQUIRED CAPABILITIES:\n{[c.value if hasattr(c, 'value') else str(c) for c in task_spec.required_capabilities]}\n\n"
            f"SUBTASKS:\n{[s.model_dump(mode='json') for s in task_spec.subtasks]}\n\n"
            f"AVAILABLE TOOLS CATALOG:\n{json.dumps(tools_summary, indent=2)}\n\n"
            f"CONSTRAINTS:\n{task_spec.constraints}\n\n"
            f"VERIFICATION REQUIREMENTS:\n{task_spec.verification_requirements}\n\n"
            f"EVALUATOR BENCHMARK:\n{evaluator_spec.model_dump(mode='json') if evaluator_spec else {}}\n\n"
            "Produce a valid GraphDefinition JSON with:\n"
            "- graph_id, name, entry_node_id, terminal_node_ids\n"
            "- nodes: map of node_id to NodeModel (node_id, name, role, system_prompt, tools, input_mapping, output_key, metadata.capabilities)\n"
            "- edges: list of EdgeModel (source_node_id, target_node_id)\n"
            "RULES: Graph must be a DAG. All tools must exist in catalog. No fabricated tools."
        )

    def _generate_fallback(
        self,
        task_spec: TaskSpecification,
        catalog: List[Dict[str, Any]],
        evaluator_spec: Optional[EvaluatorSpecification],
    ) -> GraphDefinition:
        """Synthesize a valid, minimal DAG from subtasks or capabilities without an external LLM."""
        catalog_map = {t["name"]: t for t in catalog}
        catalog_ids = set(catalog_map.keys())
        nodes: Dict[str, NodeModel] = {}
        edges: List[EdgeModel] = []

        # Strategy A: Subtask-Driven Pipeline
        if task_spec.subtasks:
            prev_subtasks: List[Subtask] = []
            for idx, subtask in enumerate(task_spec.subtasks):
                nid = subtask.id
                tools = [t for t in subtask.preferred_tools if t in catalog_ids]
                caps = [c.value if hasattr(c, "value") else str(c) for c in subtask.required_capabilities]

                # Determine meaningful role
                role = "Worker"
                if any(c in caps for c in ["extraction", "retrieval", "structured_lookup"]):
                    role = "IngestionSpecialist"
                elif any(c in caps for c in ["comparison", "calculation", "anomaly_detection"]):
                    role = "AnalyticalProcessor"
                elif any(c in caps for c in ["verification", "decision_making"]):
                    role = "Auditor"
                elif "summarization" in caps:
                    role = "Synthesizer"

                # Build input mapping with tool parameter intelligence
                input_mapping = self._resolve_subtask_input_mapping(
                    subtask=subtask,
                    tools=tools,
                    catalog_map=catalog_map,
                    task_inputs=task_spec.inputs,
                    prev_subtasks=prev_subtasks,
                )

                nodes[nid] = NodeModel(
                    node_id=nid,
                    name=subtask.description,
                    role=role,
                    system_prompt=f"Execute {subtask.objective}. Fulfill capabilities: {caps}.",
                    tools=tools,
                    input_mapping=input_mapping,
                    output_key=f"{nid}_output",
                    max_retries=1,
                    metadata={"capabilities": caps},
                )

                # Connect dependencies
                for dep in subtask.dependencies:
                    if dep in nodes:
                        edges.append(EdgeModel(source_node_id=dep, target_node_id=nid))
                    elif idx > 0:
                        edges.append(EdgeModel(source_node_id=task_spec.subtasks[idx - 1].id, target_node_id=nid))

                prev_subtasks.append(subtask)

            # Deduplicate edges
            unique_edges = []
            edge_set = set()
            for e in edges:
                key = (e.source_node_id, e.target_node_id)
                if key not in edge_set and e.source_node_id in nodes and e.target_node_id in nodes:
                    edge_set.add(key)
                    unique_edges.append(e)
            edges = unique_edges

            # If no edges created, chain linearly
            if not edges and len(nodes) > 1:
                node_keys = list(nodes.keys())
                for i in range(len(node_keys) - 1):
                    edges.append(EdgeModel(source_node_id=node_keys[i], target_node_id=node_keys[i + 1]))

            entry_node_id = task_spec.subtasks[0].id
            # Terminal nodes: nodes with no outgoing edges
            outgoing_sources = {e.source_node_id for e in edges}
            terminal_ids = [nid for nid in nodes if nid not in outgoing_sources]
            if not terminal_ids:
                terminal_ids = [task_spec.subtasks[-1].id]

            return GraphDefinition(
                graph_id=f"graph_{task_spec.task_id[:8]}",
                name=f"Synthesized {task_spec.domain.capitalize()} Architecture",
                entry_node_id=entry_node_id,
                terminal_node_ids=terminal_ids,
                nodes=nodes,
                edges=edges,
                metadata={"generation_method": "fallback", "strategy": "subtask_pipeline"},
            )

        # Strategy B: Capability-Driven Archetype Fallback
        # 1. Ingestion / Analysis node
        caps_list = [c.value if hasattr(c, "value") else str(c) for c in task_spec.required_capabilities]
        primary_tools = [b.tool_name for b in task_spec.suggested_tool_bindings if b.tool_name in catalog_ids]

        nodes["node_1"] = NodeModel(
            node_id="node_1",
            name="Primary Task Processor",
            role="AnalyticalProcessor",
            system_prompt=f"Perform core processing for: {task_spec.objective}",
            tools=primary_tools[:2],
            output_key="primary_output",
            metadata={"capabilities": caps_list},
        )

        entry_node_id = "node_1"
        terminal_ids = ["node_1"]

        # Check if verification is needed
        needs_verif = (
            bool(task_spec.verification_requirements)
            or (evaluator_spec and evaluator_spec.correctness_criteria)
            or (Capability.VERIFICATION in task_spec.required_capabilities)
        )
        if needs_verif:
            nodes["node_verifier"] = NodeModel(
                node_id="node_verifier",
                name="Result Auditor",
                role="Auditor",
                system_prompt="Audit discrepancies, verify arithmetic, and enforce correctness constraints.",
                tools=primary_tools[2:4],
                input_mapping={"results": "primary_output"},
                output_key="verified_output",
                metadata={"capabilities": ["verification", "reasoning"]},
            )
            edges.append(EdgeModel(source_node_id="node_1", target_node_id="node_verifier"))
            terminal_ids = ["node_verifier"]

        return GraphDefinition(
            graph_id=f"graph_{task_spec.task_id[:8]}",
            name=f"Synthesized {task_spec.domain.capitalize()} Fallback Graph",
            entry_node_id=entry_node_id,
            terminal_node_ids=terminal_ids,
            nodes=nodes,
            edges=edges,
            metadata={"generation_method": "fallback", "strategy": "capability_archetype"},
        )

    def _resolve_subtask_input_mapping(
        self,
        subtask: Subtask,
        tools: List[str],
        catalog_map: Dict[str, Dict[str, Any]],
        task_inputs: Dict[str, Any],
        prev_subtasks: List[Subtask],
    ) -> Dict[str, str]:
        """Resolve precise input mappings for a subtask and its assigned tool."""
        mapping: Dict[str, str] = {}

        # 1. Check if subtask.expected_input already provides an explicit target->source mapping
        if subtask.expected_input and all(isinstance(v, str) for v in subtask.expected_input.values()):
            looks_like_mapping = any(
                v in task_inputs or any(p.id in v for p in prev_subtasks) or "." in v
                for v in subtask.expected_input.values()
            )
            if looks_like_mapping:
                return dict(subtask.expected_input)

        # 2. Tool parameter-based automatic inference
        if tools and tools[0] in catalog_map:
            primary_tool = tools[0]
            schema = catalog_map[primary_tool].get("parameters_schema", {})
            required_params = schema.get("required", [])

            available_input_keys = set(task_inputs.keys())

            for param in required_params:
                # Direct match in task_inputs
                if param in available_input_keys:
                    mapping[param] = param
                elif param == "records":
                    for alt in ["raw_statement", "statement", "records", "bank_transactions", "bank_records", "dataset"]:
                        if alt in available_input_keys:
                            mapping[param] = alt
                            break
                elif param == "entries":
                    for alt in ["general_ledger", "ledger_entries", "entries", "ledger", "dataset"]:
                        if alt in available_input_keys:
                            mapping[param] = alt
                            break
                elif param == "bank_transactions":
                    parsed_node_id = None
                    for p in prev_subtasks:
                        if "parse_bank_statement" in p.preferred_tools:
                            parsed_node_id = p.id
                            break
                    if parsed_node_id:
                        mapping[param] = f"{parsed_node_id}_output.transactions"
                    elif "bank_transactions" in available_input_keys:
                        mapping[param] = "bank_transactions"
                    elif "raw_statement" in available_input_keys:
                        mapping[param] = "raw_statement"
                elif param == "ledger_entries":
                    query_node_id = None
                    for p in prev_subtasks:
                        if "query_general_ledger" in p.preferred_tools:
                            query_node_id = p.id
                            break
                    if query_node_id:
                        mapping[param] = f"{query_node_id}_output.entries"
                    elif "ledger_entries" in available_input_keys:
                        mapping[param] = "ledger_entries"
                    elif "general_ledger" in available_input_keys:
                        mapping[param] = "general_ledger"

            if mapping:
                return mapping

        # 3. Default fallback chaining
        if prev_subtasks:
            mapping["previous_output"] = f"{prev_subtasks[-1].id}_output"
        else:
            for k in task_inputs.keys():
                mapping[k] = k

        return mapping


    def _extract_graph_capabilities(
        self,
        graph: GraphDefinition,
        catalog_map: Dict[str, Dict[str, Any]],
    ) -> Set[str]:
        """Infer all capabilities covered by graph nodes and assigned tools."""
        caps: Set[str] = set()

        for node in graph.nodes.values():
            # 1. Direct metadata capabilities
            node_caps = node.metadata.get("capabilities", [])
            for c in node_caps:
                caps.add(str(c).lower())

            # 2. Role-derived capabilities
            role_lower = node.role.lower()
            if "extractor" in role_lower or "ingest" in role_lower:
                caps.add("extraction")
                caps.add("transformation")
            if "retriev" in role_lower or "lookup" in role_lower or "search" in role_lower:
                caps.add("retrieval")
                caps.add("structured_lookup")
            if "calc" in role_lower or "math" in role_lower or "difference" in role_lower:
                caps.add("calculation")
            if "match" in role_lower or "compar" in role_lower:
                caps.add("comparison")
            if "classif" in role_lower or "tag" in role_lower:
                caps.add("classification")
            if "audit" in role_lower or "verif" in role_lower or "check" in role_lower:
                caps.add("verification")
            if "synthes" in role_lower or "summar" in role_lower:
                caps.add("summarization")
                caps.add("reasoning")
            if "anomal" in role_lower:
                caps.add("anomaly_detection")

            # 3. Tool-derived capabilities
            for t_name in node.tools:
                t_lower = t_name.lower()
                if "parse" in t_lower:
                    caps.add("extraction")
                    caps.add("transformation")
                if "query" in t_lower or "get" in t_lower or "fetch" in t_lower or "search" in t_lower:
                    caps.add("retrieval")
                    caps.add("structured_lookup")
                if "calc" in t_lower or "diff" in t_lower or "sum" in t_lower:
                    caps.add("calculation")
                if "match" in t_lower or "fuzzy" in t_lower or "compare" in t_lower:
                    caps.add("comparison")
                if "anomal" in t_lower:
                    caps.add("anomaly_detection")

        return caps

    def _calculate_max_depth(self, graph: GraphDefinition) -> int:
        """Compute the longest path length in the DAG."""
        if not graph.nodes:
            return 0

        adj: Dict[str, List[str]] = {nid: [] for nid in graph.nodes}
        in_degree: Dict[str, int] = {nid: 0 for nid in graph.nodes}

        for edge in graph.edges:
            if edge.source_node_id in adj and edge.target_node_id in adj:
                adj[edge.source_node_id].append(edge.target_node_id)
                in_degree[edge.target_node_id] += 1

        dist: Dict[str, int] = {nid: 1 for nid in graph.nodes}
        queue = deque([nid for nid in graph.nodes if in_degree[nid] == 0])

        while queue:
            curr = queue.popleft()
            for neighbor in adj[curr]:
                if dist[curr] + 1 > dist[neighbor]:
                    dist[neighbor] = dist[curr] + 1
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return max(dist.values()) if dist else 0
