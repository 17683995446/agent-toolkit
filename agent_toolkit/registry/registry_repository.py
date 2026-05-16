"""Repository layer for Tool Registry."""

from typing import Any, Optional, List
from datetime import datetime

from sqlalchemy import select, func, and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agent_toolkit.shared.custom_exceptions import NotFoundError, DuplicateError
from agent_toolkit.registry.registry_models import Tool, ToolVersion, ToolCategory, ToolStatus


class ToolRepository:
    """Repository for Tool CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tool_data: dict[str, Any]) -> Tool:
        """Create a new tool."""
        tool = Tool(**tool_data)
        self.session.add(tool)
        await self.session.flush()
        await self.session.refresh(tool)
        return tool

    async def get_by_id(self, tool_id: int) -> Optional[Tool]:
        """Get tool by ID."""
        result = await self.session.execute(
            select(Tool)
            .options(selectinload(Tool.versions))
            .where(Tool.id == tool_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        result = await self.session.execute(
            select(Tool)
            .options(selectinload(Tool.versions))
            .where(Tool.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Tool], int]:
        """Get all tools with pagination and filters."""
        query = select(Tool).options(selectinload(Tool.versions))
        
        if filters:
            if "category_id" in filters:
                query = query.where(Tool.category_id == filters["category_id"])
            if "status" in filters:
                query = query.where(Tool.status == filters["status"])
            if "adapter_type" in filters:
                query = query.where(Tool.adapter_type == filters["adapter_type"])
            if "author" in filters:
                query = query.where(Tool.author == filters["author"])
            if "tags" in filters:
                query = query.where(Tool.tags.contains(filters["tags"]))
            if "search" in filters:
                search_term = f"%{filters['search']}%"
                query = query.where(
                    or_(
                        Tool.name.ilike(search_term),
                        Tool.description.ilike(search_term)
                    )
                )
        
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)
        
        order_column = getattr(Tool, sort_by, Tool.created_at)
        if sort_order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        tools = result.scalars().all()
        
        return list(tools), total or 0

    async def update(self, tool_id: int, update_data: dict[str, Any]) -> Tool:
        """Update a tool."""
        tool = await self.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)
        
        for key, value in update_data.items():
            if value is not None and hasattr(tool, key):
                setattr(tool, key, value)
        
        await self.session.flush()
        await self.session.refresh(tool)
        return tool

    async def delete(self, tool_id: int) -> bool:
        """Delete a tool."""
        tool = await self.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)
        
        await self.session.delete(tool)
        await self.session.flush()
        return True

    async def update_status(self, tool_id: int, status: str) -> Tool:
        """Update tool status."""
        tool = await self.get_by_id(tool_id)
        if not tool:
            raise NotFoundError("Tool", tool_id)
        
        tool.status = status
        if status == ToolStatus.DEPRECATED.value:
            tool.deprecated_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(tool)
        return tool

    async def increment_usage(self, tool_id: int) -> None:
        """Increment tool usage count."""
        await self.session.execute(
            update(Tool)
            .where(Tool.id == tool_id)
            .values(usage_count=Tool.usage_count + 1)
        )
        await self.session.flush()

    async def update_rating(self, tool_id: int, new_rating: float) -> None:
        """Update tool rating."""
        tool = await self.get_by_id(tool_id)
        if tool:
            current_count = await self.session.scalar(
                select(func.count(Tool.id))
                .where(Tool.rating.isnot(None))
                .where(Tool.id == tool_id)
            ) or 1
            current_total = (tool.rating or 0) * current_count
            new_avg = (current_total + new_rating) / (current_count + 1)
            await self.session.execute(
                update(Tool)
                .where(Tool.id == tool_id)
                .values(rating=new_avg)
            )
            await self.session.flush()


class ToolVersionRepository:
    """Repository for ToolVersion CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, version_data: dict[str, Any]) -> ToolVersion:
        """Create a new tool version."""
        version = ToolVersion(**version_data)
        self.session.add(version)
        await self.session.flush()
        await self.session.refresh(version)
        return version

    async def get_by_id(self, version_id: int) -> Optional[ToolVersion]:
        """Get version by ID."""
        result = await self.session.execute(
            select(ToolVersion).where(ToolVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_by_tool_and_version(self, tool_id: int, version: str) -> Optional[ToolVersion]:
        """Get version by tool ID and version string."""
        result = await self.session.execute(
            select(ToolVersion)
            .where(and_(
                ToolVersion.tool_id == tool_id,
                ToolVersion.version == version
            ))
        )
        return result.scalar_one_or_none()

    async def get_versions_by_tool(self, tool_id: int) -> List[ToolVersion]:
        """Get all versions for a tool."""
        result = await self.session.execute(
            select(ToolVersion)
            .where(ToolVersion.tool_id == tool_id)
            .order_by(ToolVersion.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_version(self, tool_id: int) -> Optional[ToolVersion]:
        """Get the latest version for a tool."""
        result = await self.session.execute(
            select(ToolVersion)
            .where(ToolVersion.tool_id == tool_id)
            .order_by(ToolVersion.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def increment_downloads(self, version_id: int) -> None:
        """Increment download count."""
        await self.session.execute(
            update(ToolVersion)
            .where(ToolVersion.id == version_id)
            .values(download_count=ToolVersion.download_count + 1)
        )
        await self.session.flush()


class ToolCategoryRepository:
    """Repository for ToolCategory CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, category_data: dict[str, Any]) -> ToolCategory:
        """Create a new category."""
        category = ToolCategory(**category_data)
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def get_by_id(self, category_id: int) -> Optional[ToolCategory]:
        """Get category by ID."""
        result = await self.session.execute(
            select(ToolCategory)
            .options(selectinload(ToolCategory.children))
            .where(ToolCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[ToolCategory]:
        """Get category by name."""
        result = await self.session.execute(
            select(ToolCategory).where(ToolCategory.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all(self, include_children: bool = False) -> List[ToolCategory]:
        """Get all categories."""
        query = select(ToolCategory)
        if include_children:
            query = query.options(selectinload(ToolCategory.children))
        query = query.where(ToolCategory.parent_id.is_(None))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, category_id: int, update_data: dict[str, Any]) -> ToolCategory:
        """Update a category."""
        category = await self.get_by_id(category_id)
        if not category:
            raise NotFoundError("ToolCategory", category_id)
        
        for key, value in update_data.items():
            if value is not None and hasattr(category, key):
                setattr(category, key, value)
        
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def delete(self, category_id: int) -> bool:
        """Delete a category."""
        category = await self.get_by_id(category_id)
        if not category:
            raise NotFoundError("ToolCategory", category_id)
        
        await self.session.delete(category)
        await self.session.flush()
        return True

    async def get_tool_count(self, category_id: int) -> int:
        """Get count of tools in a category."""
        result = await self.session.scalar(
            select(func.count(Tool.id)).where(Tool.category_id == category_id)
        )
        return result or 0
