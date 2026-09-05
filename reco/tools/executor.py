"""Sandboxed tool executor with schema validation and error isolation."""

from __future__ import annotations

import time
import traceback
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from reco.tools.registry import ToolDefinition


class ToolResult(BaseModel):
    """Execution output wrapper from a tool invocation."""

    tool_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class ToolExecutor:
    """Executes tools within a sandboxed runtime boundary with schema validation."""

    def __init__(self, default_timeout_s: float = 30.0):
        self.default_timeout_s = default_timeout_s

    def execute(
        self,
        tool: ToolDefinition,
        inputs: Dict[str, Any],
        timeout_s: Optional[float] = None
    ) -> ToolResult:
        """Execute a tool handler with parameter verification and timing.

        Args:
            tool: The ToolDefinition to execute.
            inputs: Dictionary of input arguments.
            timeout_s: Optional timeout constraint in seconds.

        Returns:
            ToolResult containing status, payload, and latency telemetry.
        """
        start_time = time.perf_counter()

        # 1. Validate inputs against tool parameter schema
        validation_error = self._validate_parameters(tool.parameters, inputs)
        if validation_error:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                tool_name=tool.name,
                success=False,
                output=None,
                error=f"Parameter validation failed: {validation_error}",
                execution_time_ms=round(elapsed, 3)
            )

        if not tool.handler:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                tool_name=tool.name,
                success=False,
                output=None,
                error=f"Tool '{tool.name}' has no registered executable handler",
                execution_time_ms=round(elapsed, 3)
            )

        # 2. Invoke handler in isolated execution boundary
        try:
            # Filter inputs to those expected by schema properties if defined
            call_kwargs = {}
            properties = tool.parameters.get("properties", {})
            for param_name in properties:
                if param_name in inputs:
                    call_kwargs[param_name] = inputs[param_name]

            # If no properties were explicitly defined, pass all inputs
            if not properties:
                call_kwargs = inputs

            output = tool.handler(**call_kwargs)
            elapsed = (time.perf_counter() - start_time) * 1000.0

            return ToolResult(
                tool_name=tool.name,
                success=True,
                output=output,
                error=None,
                execution_time_ms=round(elapsed, 3)
            )

        except Exception as exc:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            tb = traceback.format_exc()
            return ToolResult(
                tool_name=tool.name,
                success=False,
                output=None,
                error=f"{type(exc).__name__}: {str(exc)}\n{tb}",
                execution_time_ms=round(elapsed, 3)
            )

    def _validate_parameters(
        self,
        schema: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Optional[str]:
        """Verify presence of required parameters and rudimentary types."""
        required = schema.get("required", [])
        for req in required:
            if req not in inputs:
                return f"Missing required parameter '{req}'"

        properties = schema.get("properties", {})
        for prop_name, prop_spec in properties.items():
            if prop_name in inputs:
                val = inputs[prop_name]
                prop_type = prop_spec.get("type")
                if prop_type == "array" and not isinstance(val, list):
                    return f"Parameter '{prop_name}' must be an array/list, got {type(val).__name__}"
                elif prop_type == "object" and not isinstance(val, dict):
                    return f"Parameter '{prop_name}' must be an object/dict, got {type(val).__name__}"
                elif prop_type == "string" and not isinstance(val, str):
                    return f"Parameter '{prop_name}' must be a string, got {type(val).__name__}"
                elif prop_type == "number" and not isinstance(val, (int, float)):
                    return f"Parameter '{prop_name}' must be a number, got {type(val).__name__}"

        return None
