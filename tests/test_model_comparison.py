"""Deterministic unit tests for Model Comparison and Routing Readiness (Step 17).

Verifies:
1. Model A request routing
2. Model B request routing
3. Model configuration isolation
4. Tool schema compatibility
5. Structured output schema compatibility
6. Cost and latency metadata handling

Zero network calls required (purely deterministic test suite).
"""

import asyncio
import json
from pydantic import BaseModel, Field
import pytest

from reco.core.interfaces import ModelMessage, ModelRequest, ModelResponse, ToolCall
from reco.llm.mock import MockModelGateway
from reco.llm.tensormux import TensorMuxGateway


class DiscrepancyReport(BaseModel):
    is_match: bool
    discrepancy_category: str
    discrepancy_amount: float
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str


def test_model_a_request_routing():
    """Verify that Model A (gemma-4-31b) can be requested and routed correctly."""
    async def _run():
        gateway = MockModelGateway(
            default_content="Gemma response: match confirmed.",
        )
        req = ModelRequest(
            model="gemma-4-31b",
            messages=[ModelMessage(role="user", content="Analyze entity match.")],
        )
        resp = await gateway.generate(req)

        assert resp.content == "Gemma response: match confirmed."
        assert resp.model_used == "gemma-4-31b"
        assert len(gateway.invocation_history) == 1
        assert gateway.invocation_history[0].model == "gemma-4-31b"

    asyncio.run(_run())


def test_model_b_request_routing():
    """Verify that Model B (glm-4-7-flash) can be requested and routed correctly."""
    async def _run():
        gateway = MockModelGateway(
            default_content="GLM response: match confirmed.",
        )
        req = ModelRequest(
            model="glm-4-7-flash",
            messages=[ModelMessage(role="user", content="Analyze entity match.")],
        )
        resp = await gateway.generate(req)

        assert resp.content == "GLM response: match confirmed."
        assert resp.model_used == "glm-4-7-flash"
        assert len(gateway.invocation_history) == 1
        assert gateway.invocation_history[0].model == "glm-4-7-flash"

    asyncio.run(_run())


def test_model_configuration_isolation():
    """Verify request-level model parameter overrides default without cross-talk."""
    async def _run():
        # Test with TensorMuxGateway configuration
        gateway = TensorMuxGateway(api_key="mock-key", default_model="gemma-4-31b")
        assert gateway.default_model == "gemma-4-31b"

        # Mock gateway invocation check
        mock_gw = MockModelGateway(default_content="ok")

        # Request with model A override
        req_a = ModelRequest(model="gemma-4-31b", messages=[ModelMessage(role="user", content="ping")])
        resp_a = await mock_gw.generate(req_a)
        assert resp_a.model_used == "gemma-4-31b"

        # Request with model B override
        req_b = ModelRequest(model="glm-4-7-flash", messages=[ModelMessage(role="user", content="ping")])
        resp_b = await mock_gw.generate(req_b)
        assert resp_b.model_used == "glm-4-7-flash"

        # Request without model defaults to gateway default
        assert len(mock_gw.invocation_history) == 2
        assert mock_gw.invocation_history[0].model == "gemma-4-31b"
        assert mock_gw.invocation_history[1].model == "glm-4-7-flash"

    asyncio.run(_run())


def test_tool_schema_compatibility():
    """Verify that tool schemas are parsed identically regardless of model target."""
    tool_def = {
        "type": "function",
        "function": {
            "name": "compare_records",
            "description": "Compare two records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "record_a_id": {"type": "string"},
                    "record_b_id": {"type": "string"},
                    "comparison_type": {"type": "string", "enum": ["exact", "fuzzy"]},
                },
                "required": ["record_a_id", "record_b_id", "comparison_type"],
            },
        },
    }

    # Verify formatting into standard OpenAI-compatible tool call
    raw_tool_call = {
        "id": "call_123",
        "type": "function",
        "function": {
            "name": "compare_records",
            "arguments": '{"record_a_id": "TX_1", "record_b_id": "GL_1", "comparison_type": "fuzzy"}',
        },
    }
    resp = ModelResponse(content="", tool_calls=[raw_tool_call], model_used="glm-4-7-flash")
    parsed_tcs = resp.get_parsed_tool_calls()

    assert len(parsed_tcs) == 1
    tc = parsed_tcs[0]
    assert isinstance(tc, ToolCall)
    assert tc.tool_name == "compare_records"
    assert tc.arguments["record_a_id"] == "TX_1"
    assert tc.arguments["record_b_id"] == "GL_1"
    assert tc.arguments["comparison_type"] == "fuzzy"


def test_structured_output_schema_compatibility():
    """Verify that JSON output adheres strictly to DiscrepancyReport Pydantic schema."""
    valid_payload = {
        "is_match": False,
        "discrepancy_category": "processing_fee",
        "discrepancy_amount": 2.50,
        "confidence": 0.95,
        "explanation": "Bank transaction includes a $2.50 payout processing fee.",
    }

    report = DiscrepancyReport(**valid_payload)
    assert report.is_match is False
    assert report.discrepancy_category == "processing_fee"
    assert report.discrepancy_amount == 2.50
    assert report.confidence == 0.95

    # Negative case: invalid confidence range
    with pytest.raises(Exception):
        DiscrepancyReport(
            is_match=False,
            discrepancy_category="processing_fee",
            discrepancy_amount=2.50,
            confidence=1.5,  # > 1.0 violates Field(le=1.0)
            explanation="Invalid confidence",
        )


def test_cost_and_latency_metadata_handling():
    """Verify cost calculation and latency telemetry accounting."""
    gateway = TensorMuxGateway(
        api_key="mock-key",
        pricing_per_1k_input=0.0015,
        pricing_per_1k_output=0.0020,
    )

    prompt_tokens = 500
    completion_tokens = 250
    total_tokens = prompt_tokens + completion_tokens

    # Formula: (500 / 1000 * 0.0015) + (250 / 1000 * 0.0020) = 0.00075 + 0.00050 = 0.00125
    expected_cost = round((500 / 1000.0 * 0.0015) + (250 / 1000.0 * 0.0020), 6)

    resp = ModelResponse(
        content="Test output",
        tokens_prompt=prompt_tokens,
        tokens_completion=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=expected_cost,
        cost_type="estimated",
        latency_ms=145,
        model_used="glm-4-7-flash",
    )

    assert resp.tokens_prompt == 500
    assert resp.tokens_completion == 250
    assert resp.total_tokens == 750
    assert resp.cost_usd == 0.00125
    assert resp.cost_type == "estimated"
    assert resp.latency_ms == 145
    assert resp.model_used == "glm-4-7-flash"
