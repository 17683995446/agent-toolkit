"""
Tool registry service.

Business logic for tool registration, discovery, and lifecycle management.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import uuid4

from agent_toolkit.adapters.base_adapter_definition import BaseAdapter
from agent_toolkit.adapters.adapter_factory import AdapterFactory
from agent_toolkit.models.adapter_config_models import AdapterConfig
from agent_toolkit.models.shared_api_response_models import APIResponse, Pagination
from agent_toolkit.models.tool_registration_models import ToolRegistration, ToolVersion
from agent_toolkit.models.tool_definition_models import ToolMetadata
from agent_toolkit.observability.prometheus_metrics_definition import registered_tools_gauge
from agent_toolkit.registry.tool_registration_repository import ToolRepository
from agent_toolkit.tools.adapter_tool import AdapterTool
from agent_toolkit.tools.base_tool_definition import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistryService:
    """
    Service for managing tool registrations and their lifecycle.

    Handles registration, deregistration, discovery, and adapter management
    for all tools in the toolkit.
    """

    def __init__(
        self,
        repository: ToolRepository | None = None,
        runtime_service: Any | None = None,
    ) -> None:
        """
        Initialize the registry service.

        Args:
            repository: Optional tool repository. Uses in-memory repo if None.
            runtime_service: Optional runtime service for registering executable tools.
        """
        self._repository = repository or ToolRepository()
        self._adapters: dict[str, BaseAdapter] = {}
        self._tools: dict[str, BaseTool] = {}
        self._runtime_service = runtime_service

    async def register_tool(
        self,
        metadata: ToolMetadata,
        adapter_config: AdapterConfig,
        tool_id: str | None = None,
    ) -> ToolRegistration:
        """
        Register a new tool in the registry.

        Args:
            metadata: Tool metadata.
            adapter_config: Adapter configuration for the tool.
            tool_id: Optional custom tool ID. Auto-generated if None.

        Returns:
            The created ToolRegistration.

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        # Check for duplicate name
        existing = await self._repository.get_by_name(metadata.name)
        if existing:
            raise ValueError(f"Tool with name '{metadata.name}' is already registered")

        tool_id = tool_id or f"{metadata.name}-{uuid4().hex[:8]}"

        registration = ToolRegistration(
            tool_id=tool_id,
            metadata=metadata,
            adapter_config=adapter_config,
        )

        created = await self._repository.create(registration)

        # 创建并初始化适配器
        adapter_init_failed = False
        try:
            adapter = AdapterFactory.create(adapter_config)
            await adapter.initialize()
            self._adapters[tool_id] = adapter
        except (ValueError, RuntimeError, OSError) as exc:
            adapter_init_failed = True
            logger.warning(
                "Failed to initialize adapter for tool '%s': %s. Tool registered but adapter inactive.",
                metadata.name,
                exc,
            )

        # 如果适配器初始化失败，将工具标记为禁用
        if adapter_init_failed:
            created = await self._repository.update(tool_id, {"enabled": False})
            logger.warning(
                "工具 '%s' (id=%s) 因适配器初始化失败已被自动禁用",
                metadata.name,
                tool_id,
            )
            return created

        # 创建 AdapterTool 并注册到运行时服务（如果提供了运行时服务）
        if self._runtime_service is not None and tool_id in self._adapters:
            try:
                adapter_tool = AdapterTool(
                    metadata=metadata,
                    adapter=self._adapters[tool_id],
                )
                await adapter_tool.initialize()
                self._runtime_service.register_tool_instance(adapter_tool)
                logger.info(
                    "Tool '%s' registered to runtime service",
                    metadata.name,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to register tool '%s' to runtime service: %s",
                    metadata.name,
                    exc,
                )

        logger.info("Tool registered: %s (id=%s)", metadata.name, tool_id)
        registered_tools_gauge.labels(category=metadata.category.value).inc()
        return created

    async def deregister_tool(self, tool_id: str) -> bool:
        """
        Remove a tool from the registry.

        即使适配器或工具实例清理失败，仍会执行 repository.delete()，
        确保注册记录被移除。

        Args:
            tool_id: Unique tool identifier.

        Returns:
            True if the tool was found and removed.
        """
        # 清理适配器（异常保护）
        adapter = self._adapters.pop(tool_id, None)
        if adapter:
            try:
                await adapter.cleanup()
            except (RuntimeError, OSError) as exc:
                logger.warning(
                    "清理工具 '%s' 的适配器时发生异常: %s",
                    tool_id,
                    exc,
                )

        # 清理工具实例（异常保护）
        tool = self._tools.pop(tool_id, None)
        if tool:
            try:
                await tool.cleanup()
            except (RuntimeError, OSError) as exc:
                logger.warning(
                    "清理工具 '%s' 的实例时发生异常: %s",
                    tool_id,
                    exc,
                )

        # 获取工具类别用于更新指标
        registration = await self._repository.get(tool_id)
        deleted = await self._repository.delete(tool_id)

        if deleted and registration is not None:
            registered_tools_gauge.labels(category=registration.metadata.category.value).dec()

        return deleted

    async def get_tool(self, tool_id: str) -> Optional[ToolRegistration]:
        """
        Retrieve a tool registration by ID.

        Args:
            tool_id: Unique tool identifier.

        Returns:
            ToolRegistration if found, None otherwise.
        """
        return await self._repository.get(tool_id)

    async def get_tool_by_name(self, name: str) -> Optional[ToolRegistration]:
        """
        Retrieve a tool registration by name.

        Args:
            name: Tool name.

        Returns:
            ToolRegistration if found, None otherwise.
        """
        return await self._repository.get_by_name(name)

    async def list_tools(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> Pagination:
        """
        List registered tools with optional filtering and pagination.

        Args:
            category: Filter by tool category.
            enabled_only: Only return enabled tools.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Pagination with tool registrations.
        """
        tools, total = await self._repository.list_tools(
            category=category,
            enabled_only=enabled_only,
            page=page,
            page_size=page_size,
        )
        return Pagination(
            page=page,
            page_size=page_size,
            total=total,
            items=[t.model_dump() for t in tools],
        )

    async def enable_tool(self, tool_id: str) -> Optional[ToolRegistration]:
        """
        Enable a registered tool.

        Args:
            tool_id: Unique tool identifier.

        Returns:
            Updated ToolRegistration if found.
        """
        return await self._repository.update(tool_id, {"enabled": True})

    async def disable_tool(self, tool_id: str) -> Optional[ToolRegistration]:
        """
        Disable a registered tool.

        Args:
            tool_id: Unique tool identifier.

        Returns:
            Updated ToolRegistration if found.
        """
        return await self._repository.update(tool_id, {"enabled": False})

    async def update_tool(self, tool_id: str, updates: dict[str, Any]) -> Optional[ToolRegistration]:
        """更新工具元数据或配置。"""
        return await self._repository.update(tool_id, updates)

    async def add_version(self, tool_id: str, version: ToolVersion) -> Optional[ToolRegistration]:
        """
        Add a new version to a tool's version history.

        Args:
            tool_id: Unique tool identifier.
            version: Version information.

        Returns:
            Updated ToolRegistration if found.
        """
        return await self._repository.add_version(tool_id, version)

    async def get_adapter(self, tool_id: str) -> Optional[BaseAdapter]:
        """
        Get the adapter for a registered tool.

        Args:
            tool_id: Unique tool identifier.

        Returns:
            BaseAdapter if found, None otherwise.
        """
        return self._adapters.get(tool_id)

    async def get_categories(self) -> list[str]:
        """
        List all unique tool categories.

        Returns:
            Sorted list of category names.
        """
        return await self._repository.list_categories()

    @property
    def repository(self) -> ToolRepository:
        """Return the underlying repository."""
        return self._repository
