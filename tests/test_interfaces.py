"""Tests ensuring core interfaces and models can be imported and subclassed."""

import asyncio
from typing import Any, Dict

from reco.core.interfaces import (
    Agent,
    BenchmarkCase,
    BenchmarkRunResult,
    BillingProvider,
    EvaluationResult,
    Evaluator,
    ModelGateway,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    Tool,
    ToolResult,
    Tracer,
)


def test_core_models_instantiation():
    """Verify core Pydantic data interchange models."""
    tool_res = ToolResult(success=True, data={"matched": True}, execution_time_ms=12)
    assert tool_res.success is True
    assert tool_res.data == {"matched": True}

    msg = ModelMessage(role="user", content="Reconcile transactions")
    assert msg.role == "user"
    assert msg.content == "Reconcile transactions"

    req = ModelRequest(messages=[msg], temperature=0.2)
    assert len(req.messages) == 1
    assert req.temperature == 0.2

    resp = ModelResponse(
        content="Reconciliation complete",
        tokens_prompt=120,
        tokens_completion=45,
        cost_usd=0.00035,
        latency_ms=350,
        model_used="mock-model",
    )
    assert resp.tokens_prompt == 120
    assert resp.cost_usd == 0.00035

    eval_res = EvaluationResult(accuracy=0.95, reliability=1.0, passed=True)
    assert eval_res.accuracy == 0.95
    assert eval_res.passed is True

    case = BenchmarkCase(
        case_code="REC-001",
        split="optimization",
        input_data={"bank_row": 100.0},
        ground_truth={"matched": True},
    )
    assert case.case_code == "REC-001"
    assert case.split == "optimization"

    run_res = BenchmarkRunResult(
        split="optimization",
        accuracy=0.95,
        reliability=1.0,
        total_cost_usd=0.005,
        avg_latency_ms=250,
        cases_passed=19,
        cases_total=20,
    )
    assert run_res.cases_passed == 19


def test_tool_interface_subclassing():
    """Verify custom Tool implementation satisfies abstract interface."""

    class MockCalculatorTool(Tool):
        @property
        def name(self) -> str:
            return "mock_calc"

        @property
        def description(self) -> str:
            return "Calculates differences"

        @property
        def parameters_schema(self) -> Dict[str, Any]:
            return {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}}

        async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
            diff = arguments.get("a", 0) - arguments.get("b", 0)
            return ToolResult(success=True, data={"difference": diff})

    tool = MockCalculatorTool()
    assert tool.name == "mock_calc"
    result = asyncio.run(tool.execute({"a": 100, "b": 95}))
    assert result.success is True
    assert result.data["difference"] == 5


def test_agent_interface_subclassing():
    """Verify custom Agent implementation satisfies abstract interface."""

    class MockReconcilerAgent(Agent):
        @property
        def name(self) -> str:
            return "reconciler_node"

        @property
        def role(self) -> str:
            return "Reconciliation Auditor"

        async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
            state["reconciled"] = True
            return state

    agent = MockReconcilerAgent()
    assert agent.name == "reconciler_node"
    out = asyncio.run(agent.execute({"transactions": []}))
    assert out["reconciled"] is True


def test_model_gateway_interface_subclassing():
    """Verify custom ModelGateway implementation satisfies abstract interface."""

    class MockGateway(ModelGateway):
        async def generate(self, request: ModelRequest) -> ModelResponse:
            return ModelResponse(
                content="Mocked LLM generation",
                tokens_prompt=10,
                tokens_completion=10,
                cost_usd=0.0001,
                latency_ms=50,
                model_used="mock-fast",
            )

    gateway = MockGateway()
    resp = asyncio.run(gateway.generate(ModelRequest(messages=[ModelMessage(role="user", content="test")])))
    assert resp.content == "Mocked LLM generation"
    assert resp.cost_usd == 0.0001


def test_evaluator_interface_subclassing():
    """Verify custom Evaluator implementation satisfies abstract interface."""

    class MockEvaluator(Evaluator):
        def evaluate(self, actual_output: Dict[str, Any], ground_truth: Dict[str, Any]) -> EvaluationResult:
            is_match = actual_output == ground_truth
            return EvaluationResult(
                accuracy=1.0 if is_match else 0.0,
                reliability=1.0,
                passed=is_match,
            )

    evaluator = MockEvaluator()
    res = evaluator.evaluate({"match": True}, {"match": True})
    assert res.accuracy == 1.0
    assert res.passed is True
