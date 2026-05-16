"""Service layer for Tool Registry."""

from typing import Any, Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from agent_toolkit.shared.custom_exceptions import (
    NotFoundError, DuplicateError, ValidationError
)
from agent_toolkit.shared.structured_logging import LoggerMixin
from agent_toolkit.registry.registry_models import Tool, ToolVersion, ToolCategory, ToolStatus
from agent_toolkit.registry.registry_repository import (
    ToolRepository, ToolVersionRepository, ToolCategoryRepository
)
from agent_toolkit.registry.registry_schemas import (
    ToolCreate, ToolUpdate, ToolVersionCreate, ToolCategoryCreate, ToolCategoryUpdate
)


class ToolService(LoggerMixin):
    """Service for Tool business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ToolRepository(session)
        self.version_repository = ToolVersionRepository(session)

    async def create_tool(self, tool_data: ToolCreate) -> Tool:
        """Create a new tool with initial version."""
        existing = await self.repository.get_by_name(tool_data.name)
        if existing:
            raise DuplicateError("Tool", tool_data.name)
        
        tool_dict = tool_data.model_dump()
        
        tool = await self.repository.create(tool_dict)
        
        await self.version_repository.create({
            "tool_id": tool.id,
            "version": tool.version,
            "changelog": "Initial release",
            "breaking_changes": False
        })
        
        self.logger.info("tool_created", tool_id=tool.id, name=tool.name)
        return tool

    async def get_tool(self, tool_id: int, include_versions: bool = False) -> Tool:
        """Get tool by ID."""
        tool = await self.repository.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)
        return tool

    async def get_tool_by_name(self, name: str) -> Tool:
        """Get tool by name."""
        tool = await self.repository.get_by_name(name)
        if not tool:
            raise NotFoundError("Tool", name)
        return tool

    async def list_tools(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        adapter_type: Optional[str] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Tool], int]:
        """List tools with filters and pagination."""
        filters = {}
        if category_id:
            filters["category_id"] = category_id
        if status:
            filters["status"] = status
        if adapter_type:
            filters["adapter_type"] = adapter_type
        if search:
            filters["search"] = search
        if tags:
            filters["tags"] = tags
        if author:
            filters["author"] = author
        
        return await self.repository.get_all(
            page=page,
            page_size=page_size,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order
        )

    async def update_tool(self, tool_id: int, update_data: ToolUpdate) -> Tool:
        """Update a tool."""
        await self.get_tool(tool_id)
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            raise ValidationError("No fields to update")
        
        tool = await self.repository.update(tool_id, update_dict)
        
        self.logger.info("tool_updated", tool_id=tool_id)
        return tool

    async def delete_tool(self, tool_id: int) -> bool:
        """Delete a tool."""
        await self.get_tool(tool_id)
        result = await self.repository.delete(tool_id)
        self.logger.info("tool_deleted", tool_id=tool_id)
        return result

    async def activate_tool(self, tool_id: int) -> Tool:
        """Activate a tool."""
        tool = await self.repository.update_status(tool_id, ToolStatus.ACTIVE.value)
        self.logger.info("tool_activated", tool_id=tool_id)
        return tool

    async def deprecate_tool(self, tool_id: int) -> Tool:
        """Deprecate a tool."""
        tool = await self.repository.update_status(tool_id, ToolStatus.DEPRECATED.value)
        self.logger.info("tool_deprecated", tool_id=tool_id)
        return tool

    async def archive_tool(self, tool_id: int) -> Tool:
        """Archive a tool."""
        tool = await self.repository.update_status(tool_id, ToolStatus.ARCHIVED.value)
        self.logger.info("tool_archived", tool_id=tool_id)
        return tool

    async def record_tool_usage(self, tool_id: int) -> None:
        """Record tool usage."""
        await self.repository.increment_usage(tool_id)

    async def rate_tool(self, tool_id: int, rating: float) -> None:
        """Rate a tool."""
        if not 0 <= rating <= 5:
            raise ValidationError("Rating must be between 0 and 5")
        
        await self.get_tool(tool_id)
        await self.repository.update_rating(tool_id, rating)


class ToolVersionService(LoggerMixin):
    """Service for ToolVersion business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ToolVersionRepository(session)
        self.tool_repository = ToolRepository(session)

    async def create_version(self, tool_id: int, version_data: ToolVersionCreate) -> ToolVersion:
        """Create a new version for a tool."""
        tool = await self.tool_repository.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)
        
        existing = await self.repository.get_by_tool_and_version(tool_id, version_data.version)
        if existing:
            raise DuplicateError("ToolVersion", version_data.version)
        
        version_dict = version_data.model_dump()
        version_dict["tool_id"] = tool_id
        
        version = await self.repository.create(version_dict)
        
        await self.tool_repository.update(tool_id, {"version": version.version})
        
        self.logger.info(
            "tool_version_created",
            tool_id=tool_id,
            version=version.version
        )
        return version

    async def get_version(self, version_id: int) -> ToolVersion:
        """Get version by ID."""
        version = await self.repository.get_by_id(version_id)
        if not version:
            raise NotFoundError("ToolVersion", version_id)
        return version

    async def list_versions(self, tool_id: int) -> List[ToolVersion]:
        """List all versions for a tool."""
        return await self.repository.get_versions_by_tool(tool_id)

    async def get_latest_version(self, tool_id: int) -> ToolVersion:
        """Get the latest version for a tool."""
        version = await self.repository.get_latest_version(tool_id)
        if not version:
            raise NotFoundError("ToolVersion", f"for tool {tool_id}")
        return version

    async def record_download(self, version_id: int) -> None:
        """Record a version download."""
        await self.repository.increment_downloads(version_id)
        version = await self.repository.get_by_id(version_id)
        if version:
            self.logger.info(
                "version_downloaded",
                version_id=version_id,
                tool_id=version.tool_id,
                version=version.version
            )


class ToolCategoryService(LoggerMixin):
    """Service for ToolCategory business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ToolCategoryRepository(session)

    async def create_category(self, category_data: ToolCategoryCreate) -> ToolCategory:
        """Create a new category."""
        existing = await self.repository.get_by_name(category_data.name)
        if existing:
            raise DuplicateError("ToolCategory", category_data.name)
        
        category_dict = category_data.model_dump()
        category = await self.repository.create(category_dict)
        
        self.logger.info("category_created", category_id=category.id)
        return category

    async def get_category(self, category_id: int) -> ToolCategory:
        """Get category by ID."""
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError("ToolCategory", category_id)
        return category

    async def list_categories(self, include_children: bool = False) -> List[ToolCategory]:
        """List all categories."""
        return await self.repository.get_all(include_children=include_children)

    async def update_category(
        self,
        category_id: int,
        update_data: ToolCategoryUpdate
    ) -> ToolCategory:
        """Update a category."""
        await self.get_category(category_id)
        
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise ValidationError("No fields to update")
        
        category = await self.repository.update(category_id, update_dict)
        self.logger.info("category_updated", category_id=category_id)
        return category

    async def delete_category(self, category_id: int) -> bool:
        """Delete a category."""
        await self.get_category(category_id)
        
        tool_count = await self.repository.get_tool_count(category_id)
        if tool_count > 0:
            raise ValidationError(
                f"Cannot delete category with {tool_count} tools",
                field="category_id"
            )
        
        result = await self.repository.delete(category_id)
        self.logger.info("category_deleted", category_id=category_id)
        return result

    async def get_category_stats(self, category_id: int) -> dict[str, Any]:
        """Get statistics for a category."""
        category = await self.get_category(category_id)
        tool_count = await self.repository.get_tool_count(category_id)
        
        return {
            "category_id": category_id,
            "category_name": category.name,
            "tool_count": tool_count,
            "has_children": len(category.children) > 0 if category.children else False
        }


class RegistryStatsService(LoggerMixin):
    """Service for registry statistics."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tool_repository = ToolRepository(session)
        self.version_repository = ToolVersionRepository(session)

    async def get_stats(self) -> dict[str, Any]:
        """Get overall registry statistics."""
        from sqlalchemy import select, func
        
        total_tools = await self.session.scalar(
            select(func.count(Tool.id))
        ) or 0
        
        active_tools = await self.session.scalar(
            select(func.count(Tool.id))
            .where(Tool.status == ToolStatus.ACTIVE.value)
        ) or 0
        
        deprecated_tools = await self.session.scalar(
            select(func.count(Tool.id))
            .where(Tool.status == ToolStatus.DEPRECATED.value)
        ) or 0
        
        total_downloads = await self.session.scalar(
            select(func.sum(ToolVersion.download_count))
        ) or 0
        
        avg_rating = await self.session.scalar(
            select(func.avg(Tool.rating))
            .where(Tool.rating.isnot(None))
        )
        
        return {
            "total_tools": total_tools,
            "active_tools": active_tools,
            "deprecated_tools": deprecated_tools,
            "total_downloads": total_downloads,
            "average_rating": round(avg_rating, 2) if avg_rating else None
        }
