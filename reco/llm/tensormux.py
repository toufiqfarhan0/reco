"""TensorMux inference gateway adapter implementing the ModelGateway interface."""

import json
import re
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4
import httpx

from reco.config import get_settings
from reco.core.interfaces import ModelGateway, ModelMessage, ModelRequest, ModelResponse, ToolCall
from reco.logging import get_logger

logger = get_logger("llm.tensormux")


class TensorMuxGateway(ModelGateway):
    """Inference gateway adapter connecting Reco agents to TensorMux."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout_seconds: float = 30.0,
        http_client: Optional[httpx.AsyncClient] = None,
        pricing_per_1k_input: float = 0.0015,
        pricing_per_1k_output: float = 0.0020,
    ):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.tensormux_api_key
        self.base_url = (base_url or settings.tensormux_base_url).rstrip("/")
        self.default_model = default_model or settings.llm_model
        self.timeout_seconds = timeout_seconds
        self._http_client = http_client
        self.pricing_per_1k_input = pricing_per_1k_input
        self.pricing_per_1k_output = pricing_per_1k_output

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Invoke TensorMux chat completion API with structured tools and messages."""
        if not self.api_key or self.api_key == "your-tensormux-key":
            raise ValueError(
                "TensorMux API key is not configured. Set TENSORMUX_API_KEY environment variable."
            )

        start_time = time.perf_counter()

        # Format messages
        formatted_messages: List[Dict[str, Any]] = []

        # Prepend system prompt if provided at request level and not already first message
        if request.system_prompt and (not request.messages or request.messages[0].role != "system"):
            formatted_messages.append({"role": "system", "content": request.system_prompt})

        for msg in request.messages:
            msg_dict: Dict[str, Any] = {"role": msg.role, "content": msg.content or ""}
            if msg.name:
                msg_dict["name"] = msg.name
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                formatted_tcs = []
                for tc in msg.tool_calls:
                    if isinstance(tc, dict) and "function" in tc and "id" in tc:
                        formatted_tcs.append(tc)
                    elif isinstance(tc, dict):
                        name = tc.get("tool_name") or tc.get("name") or ""
                        args = tc.get("arguments") or tc.get("args") or {}
                        args_str = json.dumps(args) if isinstance(args, dict) else str(args)
                        call_id = str(tc.get("call_id") or tc.get("id") or "call_1")
                        formatted_tcs.append({
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": args_str,
                            },
                        })
                    elif isinstance(tc, ToolCall):
                        args_str = json.dumps(tc.arguments) if isinstance(tc.arguments, dict) else str(tc.arguments)
                        formatted_tcs.append({
                            "id": tc.call_id,
                            "type": "function",
                            "function": {
                                "name": tc.tool_name,
                                "arguments": args_str,
                            },
                        })
                msg_dict["tool_calls"] = formatted_tcs
            formatted_messages.append(msg_dict)

        model_name = request.model if (request.model and request.model != "mock-v1") else self.default_model

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": formatted_messages,
            "temperature": float(request.temperature),
        }

        payload["max_tokens"] = max(request.max_tokens, 400) if request.max_tokens is not None else 3000
        if request.tools:
            payload["tools"] = request.tools
        if request.response_format:
            payload["response_format"] = request.response_format

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Reco-Agent-Engineering-Engine/0.1.0",
        }

        client = self._http_client or httpx.AsyncClient(timeout=self.timeout_seconds)
        close_client = self._http_client is None

        try:
            resp = await client.post(endpoint, json=payload, headers=headers)
            # Automatic fallback if provider rejects native tools due to missing parser
            if resp.status_code == 400 and payload.get("tools") and (
                "tool-call-parser" in resp.text
                or "enable-auto-tool-choice" in resp.text
                or "tool choice" in resp.text
            ):
                logger.info("TensorMux endpoint lacks native tool parser; falling back to prompt-guided tool calling")
                fallback_tools = payload.pop("tools")
                tool_directives = (
                    "\n\nYou have access to the following tools:\n"
                    + json.dumps(fallback_tools, indent=2)
                    + "\n\nCRITICAL INSTRUCTION: When you need to invoke a tool, respond ONLY with a JSON object in this format:\n"
                    + '{"tool_calls": [{"name": "<tool_name>", "arguments": { ... }}]}\n'
                    + "Do not output any additional prose outside the JSON."
                )
                updated_messages = [dict(m) for m in payload["messages"]]
                if updated_messages and updated_messages[0].get("role") == "system":
                    updated_messages[0] = {
                        **updated_messages[0],
                        "content": updated_messages[0]["content"] + tool_directives,
                    }
                else:
                    updated_messages.insert(0, {"role": "system", "content": tool_directives.strip()})
                payload["messages"] = updated_messages

                resp = await client.post(endpoint, json=payload, headers=headers)

        except httpx.TimeoutException as exc:
            raise TimeoutError(f"TensorMux inference timed out after {self.timeout_seconds}s") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Network failure connecting to TensorMux: {exc}") from exc
        finally:
            if close_client:
                await client.aclose()

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if resp.status_code != 200:
            error_body = resp.text
            raise RuntimeError(
                f"TensorMux API returned HTTP {resp.status_code}: {error_body}"
            )

        data = resp.json()
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content") or ""
        finish_reason = choice.get("finish_reason")
        raw_tool_calls = msg.get("tool_calls")
        if not raw_tool_calls and content:
            extracted = self._extract_tool_calls(content)
            if extracted:
                raw_tool_calls = extracted
                finish_reason = "tool_calls"

        # Parse usage
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        # Cost calculation
        if "cost_usd" in data:
            cost_usd = float(data["cost_usd"])
            cost_type = "actual"
        elif "cost" in usage:
            cost_usd = float(usage["cost"])
            cost_type = "actual"
        else:
            cost_usd = round(
                (prompt_tokens / 1000.0 * self.pricing_per_1k_input)
                + (completion_tokens / 1000.0 * self.pricing_per_1k_output),
                6,
            )
            cost_type = "estimated"

        # Check for structured output parsing if json_object requested
        structured_output = None
        if request.response_format and request.response_format.get("type") in ["json_object", "json"]:
            try:
                structured_output = json.loads(content)
            except Exception as e:
                logger.warning(f"Failed to parse structured output from model response: {e}")

        response = ModelResponse(
            content=content,
            tool_calls=raw_tool_calls,
            structured_output=structured_output,
            tokens_prompt=prompt_tokens,
            tokens_completion=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            cost_type=cost_type,
            latency_ms=latency_ms,
            model_used=data.get("model", model_name),
            finish_reason=finish_reason,
            provider_metadata={
                "provider": "tensormux",
                "id": data.get("id"),
                "system_fingerprint": data.get("system_fingerprint"),
            },
        )
        return response

    @staticmethod
    def _extract_tool_calls(content: str) -> Optional[List[Dict[str, Any]]]:
        """Extract structured tool calls from raw model text output if returned as JSON."""
        if not content:
            return None
        cleaned = content.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

        def _normalize(data: Any) -> Optional[List[Dict[str, Any]]]:
            if isinstance(data, list):
                valid = []
                for item in data:
                    if isinstance(item, dict):
                        if "name" in item:
                            valid.append({"name": item["name"], "arguments": item.get("arguments") or item.get("args") or item.get("parameters") or {}})
                        elif "function" in item and isinstance(item["function"], dict):
                            valid.append({"name": item["function"].get("name"), "arguments": item["function"].get("arguments", {})})
                return valid if valid else None
            if isinstance(data, dict):
                if "tool_calls" in data and isinstance(data["tool_calls"], list):
                    return data["tool_calls"]
                if "tool_call" in data and isinstance(data["tool_call"], dict):
                    tc = data["tool_call"]
                    return [{"name": tc.get("name"), "arguments": tc.get("arguments") or tc.get("args") or {}}]
                if "name" in data and ("arguments" in data or "args" in data or "parameters" in data):
                    return [{"name": data["name"], "arguments": data.get("arguments") or data.get("args") or data.get("parameters") or {}}]
                if "tool" in data and ("arguments" in data or "args" in data or "parameters" in data):
                    return [{"name": data["tool"], "arguments": data.get("arguments") or data.get("args") or data.get("parameters") or {}}]
                if "function" in data and isinstance(data["function"], dict):
                    fn = data["function"]
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            pass
                    return [{"name": fn.get("name"), "arguments": args}]
            return None

        try:
            parsed = json.loads(cleaned)
            norm = _normalize(parsed)
            if norm:
                return norm
        except Exception:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(cleaned[start:end+1])
                    norm = _normalize(parsed)
                    if norm:
                        return norm
                except Exception:
                    pass
        return None
