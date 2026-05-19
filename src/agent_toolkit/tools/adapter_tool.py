"""
Adapter-based tool implementation.

Wraps an adapter to provide a BaseTool interface for tools registered
via the ToolRegistryService.
"""

from __future__ import annotations

import logging
from typing import Any

from agent_toolkit.adapters.base_adapter_definition import BaseAdapter
from agent_toolkit.models.tool_definition_models import (
    ToolConfig,
    ToolExecutionResult,
    ToolMetadata,
)
from agent_toolkit.tools.base_tool_definition import BaseTool

logger = logging.getLogger(__name__)


class AdapterTool(BaseTool):
    """
    A tool implementation that wraps an adapter.

    This allows tools registered via ToolRegistryService to be executed
    by ToolRuntimeService.
    """

    def __init__(
        self,
        metadata: ToolMetadata,
        adapter: BaseAdapter,
        config: ToolConfig | None = None,
    ) -> None:
        """
        Initialize the adapter tool.

        Args:
            metadata: Tool metadata.
            adapter: The adapter to use for execution.
            config: Optional tool configuration.
        """
        super().__init__(config)
        self._metadata = metadata
        self._adapter = adapter

    async def execute(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        """
        Execute the tool via the adapter.

        Args:
            parameters: Input parameters for the tool.

        Returns:
            ToolExecutionResult containing the output or error.
        """
        try:
            result = await self._adapter.execute(parameters)
            if isinstance(result, dict):
                return ToolExecutionResult(
                    success=True,
                    output=result,
                )
            else:
                return ToolExecutionResult(
                    success=True,
                    output={"result": result},
                )
        except Exception as exc:
            logger.error("Adapter execution failed: %s", exc, exc_info=True)
            return ToolExecutionResult(
                success=False,
                error=f"Execution failed: {exc}",
            )

    async def validate_input(self, parameters: dict[str, Any]) -> bool:
        """
        Validate input parameters.

        Args:
            parameters: Input parameters to validate.

        Returns:
            True if valid.
        """
        # Basic validation - check if parameters is a dict
        return isinstance(parameters, dict)

    def get_metadata(self) -> ToolMetadata:
        """
        Return the tool's metadata.

        Returns:
            ToolMetadata instance.
        """
        return self._metadata

    async def cleanup(self) -> None:
        """Release resources."""
        try:
            await self._adapter.cleanup()
        except Exception as exc:
            logger.warning("Adapter cleanup failed: %s", exc)
