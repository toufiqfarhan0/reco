"""Node execution runner with model gateway invocation, tool dispatch, and retry policies."""

import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from reco.core.interfaces import ModelGateway, ModelMessage, ModelRequest, ToolCall, ToolResult
from reco.engine.models import NodeModel
from reco.engine.state import ExecutionState
from reco.llm.tools import get_tool_schemas_for_node
from reco.logging import get_logger
from reco.observability.tracer import get_tracer
from reco.tools.executor import ToolExecutor

logger = get_logger("engine.node_runner")

MAX_TOOL_CALL_ROUNDS_DEFAULT = 5


class NodeExecutionResult(BaseModel):
    """Structured outcome of an individual agent node execution."""
    node_id: str
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    tool_events: List[Dict[str, Any]] = Field(default_factory=list)
    attempts: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeRunner:
    """Executes a single agent node, orchestrating model inference, tool calls, and retries."""

    def __init__(
        self,
        model_gateway: ModelGateway,
        tool_executor: ToolExecutor,
        agent_mode: bool = False,
        max_tool_rounds: int = MAX_TOOL_CALL_ROUNDS_DEFAULT,
    ):
        self.model_gateway = model_gateway
        self.tool_executor = tool_executor
        self.agent_mode = agent_mode
        self.max_tool_rounds = max_tool_rounds

    async def run_node(self, node: NodeModel, state: ExecutionState) -> NodeExecutionResult:
        """Run an agent node deterministically against the current workflow state."""
        start_time = time.perf_counter()
        context = state.get_context_for_node(node.input_mapping)

        # Check execution mode: explicit execution_mode contract
        exec_mode = node.get_execution_mode() if hasattr(node, "get_execution_mode") else node.metadata.get("execution_mode")
        # Global runner agent_mode only applies when node has no explicit execution_mode or metadata
        if self.agent_mode and not node.execution_mode and "execution_mode" not in node.metadata:
            exec_mode = "model_driven"

        tracer = get_tracer()
        with tracer.start_span(
            f"node_execution.{node.node_id}",
            attributes={
                "node_id": node.node_id,
                "execution_mode": exec_mode or "deterministic_tool",
            },
        ) as node_span:
            res = await self._run_node_body(node, state, context, exec_mode, start_time)
            node_span.set_attribute("success", res.success)
            node_span.set_attribute("tokens_in", res.tokens_in)
            node_span.set_attribute("tokens_out", res.tokens_out)
            node_span.set_attribute("cost_usd", res.cost_usd)
            return res

    async def _run_node_body(
        self,
        node: NodeModel,
        state: ExecutionState,
        context: Dict[str, Any],
        exec_mode: Optional[str],
        start_time: float,
    ) -> NodeExecutionResult:
        """Execute the node attempt loop and strategy dispatch."""
        total_tokens_in = 0
        total_tokens_out = 0
        total_cost = 0.0
        node_tool_events: List[Dict[str, Any]] = []

        max_attempts = node.max_retries + 1
        last_error = None
        tracer = get_tracer()

        for attempt in range(1, max_attempts + 1):
            try:
                # -------------------------------------------------------------
                # Mode A: Model-Driven Agent Loop (Tool-Calling ReAct Loop)
                # -------------------------------------------------------------
                if exec_mode == "model_driven":
                    return await self._run_model_agent_loop(
                        node=node,
                        state=state,
                        context=context,
                        attempt=attempt,
                        start_time=start_time,
                    )

                # -------------------------------------------------------------
                # Mode B: Direct Deterministic Tool Execution (Backward-Compatible)
                # -------------------------------------------------------------
                if exec_mode == "deterministic_tool" or (
                    exec_mode is None and node.tools and any(tool_name in self.tool_executor.registry._tools for tool_name in node.tools)
                ):
                    tool_name = node.tools[0]
                    if not self.tool_executor.registry.has(tool_name):
                        raise ValueError(f"Tool '{tool_name}' configured on node '{node.node_id}' not found in registry")

                    t_start = time.perf_counter()
                    with tracer.start_span(
                        f"tool_invocation.{tool_name}",
                        attributes={
                            "tool_name": tool_name,
                            "node_id": node.node_id,
                        },
                    ) as t_span:
                        tool_res = await self.tool_executor.execute(tool_name, context)
                        tool_dur_ms = int((time.perf_counter() - t_start) * 1000)
                        t_span.set_attribute("duration_ms", tool_dur_ms)
                        t_span.set_attribute("success", tool_res.success)

                    state.record_tool_event(
                        node_id=node.node_id,
                        tool_name=tool_name,
                        arguments=context,
                        result_data=tool_res.data,
                        success=tool_res.success,
                        duration_ms=tool_res.duration_ms,
                        error=tool_res.error,
                    )
                    node_tool_events.append({
                        "tool": tool_name,
                        "success": tool_res.success,
                        "duration_ms": tool_res.duration_ms,
                    })

                    if not tool_res.success:
                        raise RuntimeError(f"Tool '{tool_name}' failed: {tool_res.error}")

                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    output_data = tool_res.data

                    # Optional LLM synthesis over tool output only if explicitly enabled in metadata
                    m_dur_ms = 0
                    model_calls = 0
                    if exec_mode != "deterministic_tool" and node.metadata.get("llm_synthesis", False) and node.system_prompt and "model" in node.model_config_data:
                        req = ModelRequest(
                            messages=[
                                ModelMessage(role="system", content=node.system_prompt),
                                ModelMessage(role="user", content=f"Goal: {state.goal}\nTool Output: {output_data}"),
                            ],
                            model=node.model_config_data.get("model", "mock-v1"),
                            temperature=float(node.model_config_data.get("temperature", 0.0)),
                            system_prompt=node.system_prompt,
                        )
                        m_call_start = time.perf_counter()
                        resp = await self.model_gateway.generate(req)
                        m_dur_ms = int((time.perf_counter() - m_call_start) * 1000)
                        model_calls = 1
                        total_tokens_in += resp.tokens_prompt
                        total_tokens_out += resp.tokens_completion
                        total_cost += resp.cost_usd

                    return NodeExecutionResult(
                        node_id=node.node_id,
                        success=True,
                        output=output_data,
                        duration_ms=duration_ms,
                        tokens_in=total_tokens_in,
                        tokens_out=total_tokens_out,
                        cost_usd=total_cost,
                        tool_events=node_tool_events,
                        attempts=attempt,
                        metadata={
                            "tools_executed": [tool_name],
                            "cost_type": "simulated_mock",
                            "execution_mode": "deterministic_tool",
                            "tool_latency_ms": tool_dur_ms,
                            "model_latency_ms": m_dur_ms,
                            "model_calls": model_calls,
                            "tool_calls": 1,
                        },
                    )

                # -------------------------------------------------------------
                # Mode C: Pure LLM Reasoning Node (No Tools Bound or model_inference)
                # -------------------------------------------------------------
                req = ModelRequest(
                    messages=[
                        ModelMessage(role="system", content=node.system_prompt),
                        ModelMessage(role="user", content=f"Goal: {state.goal}\nContext: {context}"),
                    ],
                    model=node.model_config_data.get("model", "mock-v1"),
                    temperature=float(node.model_config_data.get("temperature", 0.0)),
                    max_tokens=node.model_config_data.get("max_tokens"),
                    system_prompt=node.system_prompt,
                )
                m_call_start = time.perf_counter()
                with tracer.start_span(
                    "model_invocation",
                    attributes={
                        "model_name": node.model_config_data.get("model", "mock-v1"),
                        "node_id": node.node_id,
                    },
                ) as m_span:
                    resp = await self.model_gateway.generate(req)
                    m_dur_ms = int((time.perf_counter() - m_call_start) * 1000)
                    m_span.set_attribute("tokens_in", resp.tokens_prompt)
                    m_span.set_attribute("tokens_out", resp.tokens_completion)
                    m_span.set_attribute("total_tokens", resp.tokens_prompt + resp.tokens_completion)
                    m_span.set_attribute("cost_usd", resp.cost_usd)
                    m_span.set_attribute("latency_ms", m_dur_ms)
                    m_span.set_attribute("model_name", resp.model_used or node.model_config_data.get("model", "mock-v1"))

                total_tokens_in += resp.tokens_prompt
                total_tokens_out += resp.tokens_completion
                total_cost += resp.cost_usd

                duration_ms = int((time.perf_counter() - start_time) * 1000)
                return NodeExecutionResult(
                    node_id=node.node_id,
                    success=True,
                    output={"message": resp.content, "model": resp.model_used},
                    duration_ms=duration_ms,
                    tokens_in=total_tokens_in,
                    tokens_out=total_tokens_out,
                    cost_usd=total_cost,
                    tool_events=[],
                    attempts=attempt,
                    metadata={
                        "cost_type": resp.cost_type,
                        "execution_mode": "model_inference",
                        "tool_latency_ms": 0,
                        "model_latency_ms": m_dur_ms,
                        "model_calls": 1,
                        "tool_calls": 0,
                    },
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Node '{node.node_id}' failed attempt {attempt}/{max_attempts}: {last_error}"
                )

                # Check if retryable
                is_retryable = False
                if node.retryable_errors:
                    is_retryable = any(re.lower() in last_error.lower() for re in node.retryable_errors)
                elif node.max_retries > 0:
                    is_retryable = True

                if attempt < max_attempts and is_retryable:
                    continue  # Retry
                else:
                    break  # Stop retrying

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return NodeExecutionResult(
            node_id=node.node_id,
            success=False,
            error=last_error or "Unknown node execution error",
            duration_ms=duration_ms,
            tokens_in=total_tokens_in,
            tokens_out=total_tokens_out,
            cost_usd=total_cost,
            tool_events=node_tool_events,
            attempts=attempt,
        )

    async def _run_model_agent_loop(
        self,
        node: NodeModel,
        state: ExecutionState,
        context: Dict[str, Any],
        attempt: int,
        start_time: float,
    ) -> NodeExecutionResult:
        """Execute a model-driven agent loop with structured tool calling and bounds."""
        tracer = get_tracer()
        max_rounds = node.metadata.get("max_tool_rounds", self.max_tool_rounds)
        authorized_tools = set(node.tools)
        tool_schemas = get_tool_schemas_for_node(node.tools, self.tool_executor.registry)

        total_tokens_in = 0
        total_tokens_out = 0
        total_cost = 0.0
        total_model_latency_ms = 0
        total_tool_latency_ms = 0
        model_call_count = 0
        tool_call_count = 0
        cost_type = "simulated_mock"
        node_tool_events: List[Dict[str, Any]] = []
        round_breakdown: List[Dict[str, Any]] = []
        last_tool_result_data: Optional[Dict[str, Any]] = None

        conversation: List[ModelMessage] = [
            ModelMessage(role="system", content=node.system_prompt),
            ModelMessage(
                role="user",
                content=f"Goal: {state.goal}\nContext:\n{json.dumps(context, default=str)}",
            ),
        ]

        model_name = node.model_config_data.get("model", "mock-v1")
        temperature = float(node.model_config_data.get("temperature", 0.0))
        max_tokens = node.model_config_data.get("max_tokens")
        response_format = node.metadata.get("response_format")

        final_output = None

        for round_idx in range(1, max_rounds + 1):
            req = ModelRequest(
                messages=list(conversation),
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tool_schemas if tool_schemas else None,
                response_format=response_format,
                system_prompt=node.system_prompt,
            )

            m_call_start = time.perf_counter()
            with tracer.start_span(
                "model_invocation",
                attributes={
                    "model_name": model_name,
                    "node_id": node.node_id,
                },
            ) as m_span:
                resp = await self.model_gateway.generate(req)
                round_model_lat = int((time.perf_counter() - m_call_start) * 1000)
                m_span.set_attribute("tokens_in", resp.tokens_prompt)
                m_span.set_attribute("tokens_out", resp.tokens_completion)
                m_span.set_attribute("total_tokens", resp.tokens_prompt + resp.tokens_completion)
                m_span.set_attribute("cost_usd", resp.cost_usd)
                m_span.set_attribute("latency_ms", round_model_lat)
                m_span.set_attribute("model_name", resp.model_used or model_name)

            total_model_latency_ms += round_model_lat
            model_call_count += 1

            total_tokens_in += resp.tokens_prompt
            total_tokens_out += resp.tokens_completion
            total_cost += resp.cost_usd
            cost_type = resp.cost_type

            parsed_tool_calls = resp.get_parsed_tool_calls()

            # Case 1: Model finished reasoning and returned final text/output
            if not parsed_tool_calls:
                conversation.append(ModelMessage(role="assistant", content=resp.content))

                if resp.structured_output:
                    final_output = resp.structured_output
                else:
                    # Attempt JSON parse if structured output expected
                    cleaned_content = resp.content.strip() if resp.content else ""
                    import re
                    m = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned_content, re.DOTALL)
                    if m:
                        cleaned_content = m.group(1).strip()
                    else:
                        start = cleaned_content.find("{")
                        end = cleaned_content.rfind("}")
                        if start != -1 and end > start:
                            cleaned_content = cleaned_content[start:end+1]
                    try:
                        final_output = json.loads(cleaned_content)
                    except Exception:
                        if node.metadata.get("require_json", False):
                            raise ValueError(f"Malformed output on node '{node.node_id}': expected JSON object, got: {resp.content[:100]}")
                        final_output = {"message": resp.content, "model": resp.model_used}

                # Preserve structured tool results if model response is textual summary
                if isinstance(final_output, dict):
                    if "matched_pairs" not in final_output and last_tool_result_data and "matched_pairs" in last_tool_result_data:
                        merged = dict(last_tool_result_data)
                        merged["model_summary"] = final_output
                        final_output = merged
                elif isinstance(final_output, str) or final_output is None:
                    if last_tool_result_data:
                        merged = dict(last_tool_result_data)
                        merged["model_summary"] = str(final_output)
                        final_output = merged

                # Validate against output schema if specified
                if "expected_schema" in node.metadata:
                    expected_keys = node.metadata["expected_schema"].get("required", [])
                    if isinstance(final_output, dict):
                        missing = [k for k in expected_keys if k not in final_output]
                        if missing:
                            raise ValueError(f"Output schema validation error on node '{node.node_id}': missing required keys {missing}")

                round_breakdown.append({
                    "round": round_idx,
                    "model_latency_ms": round_model_lat,
                    "action": "finish",
                })
                break

            # Case 2: Model emitted tool calls
            conversation.append(
                ModelMessage(
                    role="assistant",
                    content=resp.content or "",
                    tool_calls=[tc.model_dump() for tc in parsed_tool_calls],
                )
            )

            for tc in parsed_tool_calls:
                # PART 7: Strict tool authorization check
                if tc.tool_name not in authorized_tools or not self.tool_executor.registry.has(tc.tool_name):
                    auth_err = (
                        f"Tool authorization failure: Tool '{tc.tool_name}' is not authorized for "
                        f"node '{node.node_id}' or does not exist in ToolRegistry."
                    )
                    state.record_tool_event(
                        node_id=node.node_id,
                        tool_name=tc.tool_name,
                        arguments=tc.arguments,
                        result_data=None,
                        success=False,
                        duration_ms=0,
                        error=auth_err,
                    )
                    node_tool_events.append({
                        "tool": tc.tool_name,
                        "success": False,
                        "error": auth_err,
                    })
                    conversation.append(
                        ModelMessage(
                            role="tool",
                            tool_call_id=tc.call_id,
                            name=tc.tool_name,
                            content=json.dumps({"error": auth_err}),
                        )
                    )
                    if node.metadata.get("fail_on_unauthorized", False):
                        raise PermissionError(auth_err)
                    continue

                # Execute authorized tool: merge missing context defaults, respecting model arguments
                tool_args = dict(context) if isinstance(context, dict) else {}
                if isinstance(tc.arguments, dict):
                    tool_args.update(tc.arguments)

                t_start = time.perf_counter()
                with tracer.start_span(
                    f"tool_invocation.{tc.tool_name}",
                    attributes={
                        "tool_name": tc.tool_name,
                        "node_id": node.node_id,
                    },
                ) as t_span:
                    tool_res = await self.tool_executor.execute(tc.tool_name, tool_args)
                    round_tool_lat = int((time.perf_counter() - t_start) * 1000)
                    t_span.set_attribute("duration_ms", round_tool_lat)
                    t_span.set_attribute("success", tool_res.success)
                round_tool_lat = int((time.perf_counter() - t_start) * 1000)
                total_tool_latency_ms += round_tool_lat
                tool_call_count += 1

                if tool_res.success and isinstance(tool_res.data, dict):
                    last_tool_result_data = tool_res.data

                state.record_tool_event(
                    node_id=node.node_id,
                    tool_name=tc.tool_name,
                    arguments=tc.arguments,
                    result_data=tool_res.data,
                    success=tool_res.success,
                    duration_ms=round_tool_lat,
                    error=tool_res.error,
                )
                node_tool_events.append({
                    "tool": tc.tool_name,
                    "success": tool_res.success,
                    "duration_ms": round_tool_lat,
                    "error": tool_res.error,
                })

                round_breakdown.append({
                    "round": round_idx,
                    "model_latency_ms": round_model_lat,
                    "tool_latency_ms": round_tool_lat,
                    "tool_called": tc.tool_name,
                    "tool_arguments": tc.arguments,
                })

                tool_content = (
                    json.dumps(tool_res.data, default=str)
                    if tool_res.success
                    else json.dumps({"error": tool_res.error}, default=str)
                )

                conversation.append(
                    ModelMessage(
                        role="tool",
                        tool_call_id=tc.call_id,
                        name=tc.tool_name,
                        content=tool_content,
                    )
                )

            # Check if round limit reached
            if round_idx == max_rounds and final_output is None:
                raise RuntimeError(
                    f"Node '{node.node_id}' reached maximum tool call rounds ({max_rounds}) without final output."
                )

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return NodeExecutionResult(
            node_id=node.node_id,
            success=True,
            output=final_output,
            duration_ms=duration_ms,
            tokens_in=total_tokens_in,
            tokens_out=total_tokens_out,
            cost_usd=round(total_cost, 6),
            tool_events=node_tool_events,
            attempts=attempt,
            metadata={
                "cost_type": cost_type,
                "execution_mode": "model_driven",
                "rounds_executed": round_idx,
                "model_latency_ms": total_model_latency_ms,
                "tool_latency_ms": total_tool_latency_ms,
                "model_calls": model_call_count,
                "tool_calls": tool_call_count,
                "round_breakdown": round_breakdown,
            },
        )
