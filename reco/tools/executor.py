"""Generic ToolExecutor for safely invoking tools with validation, timing, and error handling."""

import time
from typing import Any, Dict, Optional
from reco.core.interfaces import ToolResult
from reco.logging import get_logger
from reco.tools.registry import ToolRegistry, default_tool_registry

logger = get_logger("tools.executor")


class ToolExecutor:
    """Dispatches tool calls through validation, execution timing, and error containment."""

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or default_tool_registry

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name with strict argument validation and telemetry."""
        tool = self.registry.get(tool_name)
        if not tool:
            logger.warning(f"Tool invocation failed: tool '{tool_name}' not found")
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found in registry",
                tool_name=tool_name,
                metadata={"error_type": "TOOL_NOT_FOUND"},
            )

        # 1. Argument Validation
        try:
            validated_args = tool.validate_arguments(arguments)
        except Exception as val_err:
            logger.warning(f"Tool validation error for '{tool_name}': {val_err}")
            return ToolResult(
                success=False,
                error=f"Invalid arguments for tool '{tool_name}': {str(val_err)}",
                tool_name=tool_name,
                metadata={"error_type": "VALIDATION_ERROR"},
            )

        # 2. Timed Execution
        start_time = time.perf_counter()
        try:
            result = await tool.execute(validated_args)
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            # Ensure tool metadata and duration are set
            result.tool_name = tool_name
            if result.duration_ms == 0:
                result.duration_ms = duration_ms
                result.execution_time_ms = duration_ms

            return result
        except Exception as exec_err:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Unhandled error executing tool '{tool_name}': {exec_err}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Runtime error in tool '{tool_name}': {str(exec_err)}",
                tool_name=tool_name,
                duration_ms=duration_ms,
                execution_time_ms=duration_ms,
                metadata={"error_type": "RUNTIME_ERROR"},
            )
