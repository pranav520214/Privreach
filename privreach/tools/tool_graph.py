"""Tool Graph Registry and Dispatcher for Privreach OS."""

from typing import Dict, Any, List, Optional
from privearch.schemas import ToolCallRequest, ToolCallResult
from privearch.tools.base import BaseToolAdapter
from privearch.tools.python_sandbox import PythonSandboxAdapter


class ToolGraph:
    """
    Central Tool Graph Bus:
    Registers, validates, and dispatches deterministic software execution requests.
    """

    def __init__(self, register_defaults: bool = True):
        self._adapters: Dict[str, BaseToolAdapter] = {}

        if register_defaults:
            # Register core deterministic tools
            self.register(PythonSandboxAdapter())

    def register(self, adapter: BaseToolAdapter) -> None:
        """Register a new tool adapter in the graph."""
        self._adapters[adapter.name] = adapter

    def get(self, name: str) -> Optional[BaseToolAdapter]:
        """Retrieve tool adapter by name."""
        return self._adapters.get(name)

    def has_tool(self, name: str) -> bool:
        """Check if tool is registered and available on the host."""
        adapter = self._adapters.get(name)
        return adapter is not None and adapter.is_available()

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered tools."""
        results = []
        for name, adapter in self._adapters.items():
            results.append({
                "name": name,
                "description": adapter.description,
                "is_available": adapter.is_available()
            })
        return results

    def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolCallResult:
        """Dispatch execution to the named tool adapter."""
        adapter = self._adapters.get(tool_name)
        if not adapter:
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' is not registered in the Tool Graph."
            )

        if not adapter.is_available():
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' is registered but unavailable (missing binary or dependencies)."
            )

        # Validate parameters
        is_valid, validation_msg = adapter.validate_params(params)
        if not is_valid:
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=f"Invalid parameters for tool '{tool_name}': {validation_msg}"
            )

        return adapter.execute(params)

    def execute_request(self, request: ToolCallRequest) -> ToolCallResult:
        """Execute a structured ToolCallRequest."""
        return self.execute(request.tool_name, request.parameters)
