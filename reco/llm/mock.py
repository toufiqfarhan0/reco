"""Mock ModelGateway implementation for deterministic offline runtime execution and unit tests."""

from typing import Any, Callable, Dict, List, Optional, Union
from reco.core.interfaces import ModelGateway, ModelRequest, ModelResponse, ToolCall


class MockModelGateway(ModelGateway):
    """Deterministic, provider-free model gateway for testing and simulated runtime execution."""

    def __init__(
        self,
        default_content: str = "Mock generation completed successfully.",
        canned_responses: Optional[Dict[str, str]] = None,
        tool_call_generator: Optional[Callable[[ModelRequest], Optional[List[Dict[str, Any]]]]] = None,
        token_cost_rate: float = 0.000002,
        response_sequence: Optional[List[ModelResponse]] = None,
        tool_call_sequence: Optional[List[Optional[List[Union[ToolCall, Dict[str, Any]]]]]] = None,
        structured_output: Optional[Dict[str, Any]] = None,
        should_fail: bool = False,
        fail_exception: Optional[Exception] = None,
        latency_ms: int = 15,
        cost_type: str = "simulated_mock",
        auto_tool_calls: bool = True,
    ):
        self.default_content = default_content
        self.canned_responses = canned_responses or {}
        self.tool_call_generator = tool_call_generator
        self.token_cost_rate = token_cost_rate
        self.response_sequence = list(response_sequence) if response_sequence else []
        self.tool_call_sequence = list(tool_call_sequence) if tool_call_sequence else []
        self.structured_output = structured_output
        self.should_fail = should_fail
        self.fail_exception = fail_exception
        self.latency_ms = latency_ms
        self.cost_type = cost_type
        self.auto_tool_calls = auto_tool_calls
        self.invocation_history: List[ModelRequest] = []
        self._sequence_index = 0
        self._tool_sequence_index = 0

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Deterministically simulate an LLM inference call."""
        self.invocation_history.append(request)

        # 1. Check for forced model failure
        if self.should_fail:
            if self.fail_exception:
                raise self.fail_exception
            raise RuntimeError("Simulated mock model gateway failure")

        # 2. Check for pre-programmed response sequence
        if self._sequence_index < len(self.response_sequence):
            resp = self.response_sequence[self._sequence_index]
            self._sequence_index += 1
            return resp

        # 3. Check for pre-programmed tool call sequence
        tool_calls = None
        if self._tool_sequence_index < len(self.tool_call_sequence):
            tool_calls = self.tool_call_sequence[self._tool_sequence_index]
            self._tool_sequence_index += 1
        elif self.tool_call_generator:
            tool_calls = self.tool_call_generator(request)
        elif self.auto_tool_calls and request.tools and "no tool" not in self.default_content.lower():
            # Autonomous mock tool dispatch for model-driven reconciliation matcher
            tool_names = [
                (t.get("function", {}).get("name") if "function" in t else t.get("name"))
                for t in request.tools
            ]
            if "fuzzy_match_transactions" in tool_names:
                has_tool_reply = any(m.role == "tool" for m in request.messages)
                if not has_tool_reply:
                    first_tool = "fuzzy_match_transactions"
                    tool_args: Dict[str, Any] = {}
                    all_text = " ".join(
                        [(m.content or "") for m in request.messages]
                        + ([request.system_prompt] if request.system_prompt else [])
                    ).lower()

                    if "vendor" in all_text and ("prioritize" in all_text or "reject" in all_text or "strict" in all_text):
                        tool_args["require_vendor_match"] = True
                        tool_args["vendor_similarity_threshold"] = 0.85
                    elif "vendor_similarity_threshold" in all_text:
                        tool_args["vendor_similarity_threshold"] = 0.90
                    elif "amount" in all_text and "tolerance" in all_text:
                        tool_args["amount_tolerance"] = "0.01"

                    tool_calls = [
                        ToolCall(
                            call_id=f"call_{len(self.invocation_history)}",
                            tool_name=first_tool,
                            arguments=tool_args,
                        )
                    ]

        # 4. Check for keyword in canned responses
        prompt_text = " ".join([m.content or "" for m in request.messages])
        content = self.default_content
        for keyword, canned in self.canned_responses.items():
            if keyword.lower() in prompt_text.lower():
                content = canned
                break

        # 5. Token accounting
        tokens_in = max(10, sum(len((m.content or "").split()) for m in request.messages))
        tokens_out = max(5, len(content.split()))
        cost = (tokens_in + tokens_out) * self.token_cost_rate

        return ModelResponse(
            content=content,
            tool_calls=tool_calls,
            structured_output=self.structured_output,
            tokens_prompt=tokens_in,
            tokens_completion=tokens_out,
            total_tokens=tokens_in + tokens_out,
            cost_usd=round(cost, 6),
            cost_type=self.cost_type,
            latency_ms=self.latency_ms,
            model_used=request.model or "mock-deterministic-v1",
            finish_reason="tool_calls" if tool_calls else "stop",
        )
