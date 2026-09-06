"""Tool schema translation utilities for LLM function calling."""

from typing import Any, Dict, List, Optional
from reco.core.interfaces import Tool
from reco.tools.registry import ToolRegistry


def tool_to_function_schema(tool: Tool) -> Dict[str, Any]:
    """Translate a Reco Tool into the standard OpenAI / TensorMux function calling format."""
    schema: Dict[str, Any] = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters_schema,
        },
    }
    return schema


def get_tool_schemas_for_node(tool_names: List[str], registry: ToolRegistry) -> List[Dict[str, Any]]:
    """Look up authorized tools for a node in the registry and return function-calling schemas."""
    schemas: List[Dict[str, Any]] = []
    for name in tool_names:
        if registry.has(name):
            tool = registry.get(name)
            schemas.append(tool_to_function_schema(tool))
    return schemas
