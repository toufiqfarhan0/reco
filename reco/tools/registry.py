"""Generic ToolRegistry for registering, cataloging, and discovering tools for Reco."""

from typing import Any, Dict, List, Optional
from reco.core.interfaces import Tool
from reco.logging import get_logger

logger = get_logger("tools.registry")


class ToolRegistry:
    """Central catalog for tools available to synthesized agents."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool instance. Rejects duplicates."""
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' is already registered in registry")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def unregister(self, tool_name: str) -> bool:
        """Remove a tool from the registry."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.debug(f"Unregistered tool: {tool_name}")
            return True
        return False

    def get(self, tool_name: str) -> Optional[Tool]:
        """Retrieve a registered tool by machine name."""
        return self._tools.get(tool_name)

    def has(self, tool_name: str) -> bool:
        """Check whether a tool is registered."""
        return tool_name in self._tools

    def list_tools(self) -> List[Tool]:
        """List all currently registered tool instances."""
        return list(self._tools.values())

    def list_schemas(self) -> List[Dict[str, Any]]:
        """Export standardized tool specifications for the architecture generator and LLMs."""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "name": tool.name,
                "description": tool.description,
                "parameters_schema": tool.parameters_schema,
                "output_schema": tool.output_schema,
                "deterministic": tool.deterministic,
                "side_effect": tool.side_effect,
                "risk_level": tool.risk_level,
                "category": tool.category,
            })
        return schemas

    def clear(self) -> None:
        """Clear all registered tools (used in testing)."""
        self._tools.clear()


# Default global tool registry instance
default_tool_registry = ToolRegistry()


def _ensure_default_tools() -> None:
    """Populate default registry with baseline tools across all active domains."""
    existing = {t.name for t in default_tool_registry.list_tools()}
    if "parse_bank_statement" not in existing:
        try:
            from reco.tools.reconciliation import register_reconciliation_tools
            register_reconciliation_tools(default_tool_registry)
        except Exception:
            pass
    if "read_tabular_dataset" not in existing:
        try:
            from reco.tools.anomaly import register_anomaly_tools
            register_anomaly_tools(default_tool_registry)
        except Exception:
            pass
    if "search_document_evidence" not in existing:
        try:
            from reco.tools.research import register_research_tools
            register_research_tools(default_tool_registry)
        except Exception:
            pass


_ensure_default_tools()
