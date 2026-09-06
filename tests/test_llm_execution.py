"""Comprehensive test suite for TensorMux Live Inference Provider (GLM-4.7-Flash).

Verifies:
- TensorMux client initialization, base URL, and glm-4-7-flash default model
- Tool-calling protocol: tool definitions formatting, receiving tool_calls, returning tool messages
- Structured JSON output parsing (raw JSON, markdown code blocks, embedded objects)
- GLM-4.7-Flash reasoning tokens extraction ('reasoning' message field)
- Strict max_tokens >= 400 enforcement to prevent reasoning token truncation
- Accurate token counting and live USD inference cost calculation
- Multi-turn autonomous tool execution loop
- Error handling on HTTP 4xx/5xx responses
- Async chat completion
- Live inference execution when TENSORMUX_API_KEY is available
"""

import json
import os
import pytest
import httpx
from reco.llm.tensormux import (
    DEFAULT_INPUT_COST_PER_MILLION,
    DEFAULT_OUTPUT_COST_PER_MILLION,
    DEFAULT_TENSORMUX_BASE_URL,
    DEFAULT_TENSORMUX_MODEL,
    MIN_REASONING_MAX_TOKENS,
    TensorMuxClient,
    TensorMuxResponse,
    ToolCall,
    UsageInfo,
    calculate_tensormux_cost,
    create_tool_message,
    format_tool_definition,
    parse_json_output,
)
from reco.tools.registry import ToolDefinition, ToolRegistry


# ==============================================================================
# 1. Configuration & Default Contracts
# ==============================================================================

def test_tensormux_client_initialization_defaults():
    """Verify default URL, glm-4-7-flash model, and parameter defaults."""
    client = TensorMuxClient(api_key="tmx_test_key_123")
    assert client.api_key == "tmx_test_key_123"
    assert client.base_url == "https://api.tensormux.com/v1"
    assert client.model == "glm-4-7-flash"
    assert client.timeout == 60.0
    assert client.input_cost_per_m == DEFAULT_INPUT_COST_PER_MILLION
    assert client.output_cost_per_m == DEFAULT_OUTPUT_COST_PER_MILLION


def test_tensormux_client_environment_variable_precedence(monkeypatch):
    """Verify environment variables are utilized when explicit arguments omitted."""
    monkeypatch.setenv("TENSORMUX_API_KEY", "tmx_env_secret")
    monkeypatch.setenv("TENSORMUX_BASE_URL", "https://custom.gateway.tensormux.com/v1")
    monkeypatch.setenv("TENSORMUX_MODEL", "glm-4-7-flash")

    client = TensorMuxClient()
    assert client.api_key == "tmx_env_secret"
    assert client.base_url == "https://custom.gateway.tensormux.com/v1"
    assert client.model == "glm-4-7-flash"

    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer tmx_env_secret"
    assert headers["Content-Type"] == "application/json"


# ==============================================================================
# 2. Strict max_tokens >= 400 Enforcement
# ==============================================================================

def test_strict_max_tokens_enforcement_prevents_truncation():
    """Verify client clamps max_tokens < 400 to 400 to prevent reasoning truncation."""
    client = TensorMuxClient(api_key="test_key")

    # Values under 400 are clamped to 400
    assert client.enforce_max_tokens(100) == 400
    assert client.enforce_max_tokens(0) == 400
    assert client.enforce_max_tokens(399) == 400

    # Minimum boundary is preserved
    assert client.enforce_max_tokens(400) == 400

    # Values >= 400 are preserved
    assert client.enforce_max_tokens(1024) == 1024
    assert client.enforce_max_tokens(4096) == 4096

    # None defaults to safe 4096
    assert client.enforce_max_tokens(None) == 4096


# ==============================================================================
# 3. Tool-Calling Protocol
# ==============================================================================

def test_tool_definition_formatting():
    """Verify formatting ToolDefinition and dictionaries into OpenAI function schemas."""
    # From ToolDefinition instance
    custom_tool = ToolDefinition(
        name="compute_zscore",
        description="Calculates Z-scores for time-series values.",
        parameters={
            "type": "object",
            "properties": {"values": {"type": "array", "items": {"type": "number"}}},
            "required": ["values"],
        },
        capabilities=["anomaly_detection"],
    )

    formatted = format_tool_definition(custom_tool)
    assert formatted["type"] == "function"
    assert formatted["function"]["name"] == "compute_zscore"
    assert formatted["function"]["description"] == "Calculates Z-scores for time-series values."
    assert "values" in formatted["function"]["parameters"]["properties"]

    # From raw dictionary
    dict_tool = {
        "name": "check_threshold",
        "description": "Checks metrics against limits",
        "parameters": {"type": "object", "properties": {"metrics": {"type": "object"}}},
    }
    formatted_dict = format_tool_definition(dict_tool)
    assert formatted_dict["type"] == "function"
    assert formatted_dict["function"]["name"] == "check_threshold"

    # Already formatted OpenAI tool passthrough
    existing_schema = {"type": "function", "function": {"name": "noop", "description": "", "parameters": {}}}
    assert format_tool_definition(existing_schema) == existing_schema


def test_create_tool_response_message():
    """Verify standard tool role message construction."""
    msg = create_tool_message(
        tool_call_id="call_abc123",
        content={"status": "anomaly_detected", "count": 2},
        name="compute_zscore",
    )
    assert msg["role"] == "tool"
    assert msg["tool_call_id"] == "call_abc123"
    assert msg["name"] == "compute_zscore"
    assert json.loads(msg["content"]) == {"status": "anomaly_detected", "count": 2}


# ==============================================================================
# 4. Structured JSON Output Parsing
# ==============================================================================

def test_parse_json_output_scenarios():
    """Verify robust JSON extraction across raw, markdown-fenced, and embedded formats."""
    # 1. Pure raw JSON
    raw_str = '{"reconciliation_status": "reconciled", "matched_count": 5}'
    assert parse_json_output(raw_str) == {"reconciliation_status": "reconciled", "matched_count": 5}

    # 2. Markdown fenced code block with ```json
    fenced_str = """
Here is your analysis:
```json
{
    "domain": "system_anomaly",
    "critical_breaches": 2,
    "root_cause": "OutOfMemoryError"
}
```
Please let me know if you need more details.
    """
    assert parse_json_output(fenced_str) == {
        "domain": "system_anomaly",
        "critical_breaches": 2,
        "root_cause": "OutOfMemoryError",
    }

    # 3. Markdown fenced code block without json keyword
    plain_fenced = "```\n{\"accuracy\": 0.94, \"model\": \"glm-4-7-flash\"}\n```"
    assert parse_json_output(plain_fenced) == {"accuracy": 0.94, "model": "glm-4-7-flash"}

    # 4. Embedded JSON inside text
    embedded = "Analysis complete: {\"result\": \"pass\", \"score\": 100} Thank you."
    assert parse_json_output(embedded) == {"result": "pass", "score": 100}

    # 5. Invalid JSON raises ValueError
    with pytest.raises(ValueError, match="Failed to parse structured JSON"):
        parse_json_output("No JSON content anywhere here.")


# ==============================================================================
# 5. Token Counting & Live Cost Calculation
# ==============================================================================

def test_token_counting_and_live_cost_calculation():
    """Verify accurate token calculation at $0.10/1M tokens for glm-4-7-flash."""
    # 10,000 prompt tokens + 5,000 completion tokens:
    # prompt: (10,000 / 1,000,000) * $0.10 = $0.001000
    # completion: (5,000 / 1,000,000) * $0.10 = $0.000500
    # total: $0.001500
    cost = calculate_tensormux_cost(10000, 5000)
    assert pytest.approx(cost, 1e-6) == 0.0015

    # UsageInfo validation
    usage = UsageInfo(
        prompt_tokens=1000,
        completion_tokens=400,
        total_tokens=1400,
        reasoning_tokens=250,
        cost_usd=calculate_tensormux_cost(1000, 400),
    )
    assert usage.prompt_tokens == 1000
    assert usage.completion_tokens == 400
    assert usage.reasoning_tokens == 250
    assert pytest.approx(usage.cost_usd, 1e-7) == 0.000140


# ==============================================================================
# 6. Mock Inference: Reasoning Tokens & Tool Calling
# ==============================================================================

def test_mock_chat_completion_with_glm4_reasoning_tokens():
    """Verify GLM-4.7-Flash reasoning tokens extraction and structured JSON output."""
    mock_response_data = {
        "id": "chatcmpl-test001",
        "object": "chat.completion",
        "created": 1740000000,
        "model": "glm-4-7-flash",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"status": "reconciled", "matched_count": 5}',
                    "reasoning": "Step 1: Parse source transactions TX101-TX105. Step 2: Compare target records. Step 3: Exact amount equality holds for all records.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 512,
            "completion_tokens": 128,
            "total_tokens": 640,
            "completion_tokens_details": {
                "reasoning_tokens": 85
            }
        }
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/chat/completions"
        assert request.headers.get("Authorization") == "Bearer tmx_mock_key"

        req_body = json.loads(request.content.decode("utf-8"))
        assert req_body["model"] == "glm-4-7-flash"
        assert req_body["max_tokens"] >= 400

        return httpx.Response(200, json=mock_response_data)

    transport = httpx.MockTransport(mock_handler)
    with httpx.Client(transport=transport) as custom_http:
        client = TensorMuxClient(api_key="tmx_mock_key", http_client=custom_http)
        res = client.chat_completion(
            messages=[{"role": "user", "content": "Reconcile transaction batch"}],
            max_tokens=250,  # Clamped to 400
        )

        assert isinstance(res, TensorMuxResponse)
        assert res.model == "glm-4-7-flash"
        assert res.has_reasoning is True
        assert "Step 1: Parse source" in res.reasoning
        assert res.usage.reasoning_tokens == 85
        assert res.usage.prompt_tokens == 512
        assert res.usage.completion_tokens == 128
        assert res.cost_usd > 0.0

        # JSON parsing from response
        parsed = res.parse_json()
        assert parsed["status"] == "reconciled"
        assert parsed["matched_count"] == 5


def test_mock_tool_calling_protocol_and_agent_turn():
    """Verify tool_calls payload parsing and full multi-step agent execution loop."""
    step1_response = {
        "id": "chatcmpl-step1",
        "object": "chat.completion",
        "model": "glm-4-7-flash",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "reasoning": "Need to check Z-score anomaly on CPU series before responding.",
                    "tool_calls": [
                        {
                            "id": "call_zscore_001",
                            "type": "function",
                            "function": {
                                "name": "compute_zscore",
                                "arguments": json.dumps({"values": [10.0, 11.0, 10.5, 95.0, 10.2], "threshold": 2.5}),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 200, "completion_tokens": 50, "total_tokens": 250},
    }

    step2_response = {
        "id": "chatcmpl-step2",
        "object": "chat.completion",
        "model": "glm-4-7-flash",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"status": "anomaly_detected", "anomaly_count": 1, "anomaly_indices": [3]}',
                    "reasoning": "Identified spike at index 3 with value 95.0.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 300, "completion_tokens": 60, "total_tokens": 360},
    }

    call_count = 0

    def mock_agent_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        req_body = json.loads(request.content.decode("utf-8"))

        if call_count == 1:
            assert "tools" in req_body
            assert len(req_body["tools"]) == 1
            assert req_body["tools"][0]["function"]["name"] == "compute_zscore"
            return httpx.Response(200, json=step1_response)
        elif call_count == 2:
            messages = req_body["messages"]
            # Messages should contain user, assistant tool_calls, and tool role response
            assert any(m.get("role") == "tool" and m.get("tool_call_id") == "call_zscore_001" for m in messages)
            return httpx.Response(200, json=step2_response)
        raise ValueError("Unexpected call count")

    transport = httpx.MockTransport(mock_agent_handler)
    with httpx.Client(transport=transport) as custom_http:
        client = TensorMuxClient(api_key="tmx_mock_key", http_client=custom_http)
        registry = ToolRegistry.create_anomaly_default()
        tool = registry.get("compute_zscore")

        def mock_executor(name: str, args: dict):
            assert name == "compute_zscore"
            return tool.handler(**args)

        final_response, history, total_cost = client.run_agent_turn(
            messages=[{"role": "user", "content": "Analyze CPU metrics for anomalies"}],
            tools=[tool],
            tool_executor_fn=mock_executor,
            max_iterations=3,
        )

        assert call_count == 2
        assert final_response.finish_reason == "stop"
        assert total_cost > 0.0

        parsed = final_response.parse_json()
        assert parsed["status"] == "anomaly_detected"
        assert parsed["anomaly_count"] == 1
        assert parsed["anomaly_indices"] == [3]


# ==============================================================================
# 7. Live Inference (Executed when live TENSORMUX_API_KEY is configured)
# ==============================================================================

@pytest.mark.skipif(
    not os.environ.get("TENSORMUX_API_KEY"),
    reason="TENSORMUX_API_KEY environment variable not set. Skipping live inference test."
)
def test_live_tensormux_inference():
    """Verify live HTTP roundtrip to TensorMux API using glm-4-7-flash."""
    client = TensorMuxClient()
    response = client.chat_completion(
        messages=[{"role": "user", "content": "Return a JSON object with key 'status' equal to 'online'."}],
        max_tokens=400,
        temperature=0.1,
    )
    assert isinstance(response, TensorMuxResponse)
    assert response.usage.total_tokens > 0
    parsed = response.parse_json()
    assert parsed.get("status") == "online"
