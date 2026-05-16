"""Unit tests for Registry models."""

import pytest
from datetime import datetime
from sqlalchemy import select

from agent_toolkit.registry.registry_models import Tool, ToolVersion, ToolCategory, ToolStatus


class TestToolModel:
    """Test suite for Tool model."""

    def test_tool_creation(self, sample_tool_data: dict) -> None:
        """Test creating a Tool instance."""
        tool = Tool(**sample_tool_data)
        
        assert tool.name == "test_search_tool"
        assert tool.description == "A test search tool for unit testing"
        assert tool.version == "1.0.0"
        assert tool.status == "active"
        assert tool.adapter_type == "http"

    def test_tool_default_values(self) -> None:
        """Test Tool model default values."""
        tool = Tool(
            name="default_test",
            description="Test default values",
            version="0.1.0",
            adapter_type="cli",
            adapter_config={},
            input_schema={},
            author="Test"
        )
        
        assert tool.status == "draft"
        assert tool.usage_count == 0
        assert tool.rating is None
        assert tool.tags == []

    def test_tool_status_enum(self) -> None:
        """Test ToolStatus enum values."""
        assert ToolStatus.DRAFT.value == "draft"
        assert ToolStatus.ACTIVE.value == "active"
        assert ToolStatus.DEPRECATED.value == "deprecated"
        assert ToolStatus.ARCHIVED.value == "archived"


class TestToolVersionModel:
    """Test suite for ToolVersion model."""

    def test_tool_version_creation(self) -> None:
        """Test creating a ToolVersion instance."""
        version = ToolVersion(
            tool_id=1,
            version="1.0.0",
            changelog="Initial release",
            breaking_changes=False
        )
        
        assert version.tool_id == 1
        assert version.version == "1.0.0"
        assert version.breaking_changes is False
        assert version.download_count == 0

    def test_tool_version_with_artifact(self) -> None:
        """Test ToolVersion with artifact URL."""
        version = ToolVersion(
            tool_id=1,
            version="2.0.0",
            code_hash="abc123",
            artifact_url="https://artifacts.example.com/tool-2.0.0.tar.gz"
        )
        
        assert version.artifact_url is not None
        assert version.code_hash == "abc123"


class TestToolCategoryModel:
    """Test suite for ToolCategory model."""

    def test_category_creation(self) -> None:
        """Test creating a ToolCategory instance."""
        category = ToolCategory(
            name="search",
            description="Search and discovery tools"
        )
        
        assert category.name == "search"
        assert category.description == "Search and discovery tools"
        assert category.parent_id is None
        assert category.metadata is None

    def test_category_with_parent(self) -> None:
        """Test category with parent relationship."""
        parent = ToolCategory(name="ai", description="AI tools")
        child = ToolCategory(
            name="llm",
            description="Large Language Models",
            parent_id=parent.id
        )
        
        assert child.parent_id == parent.id


@pytest.mark.asyncio
class TestToolRepositoryOperations:
    """Test suite for Tool repository operations."""

    async def test_create_tool(self, async_session: "AsyncSession", sample_tool_data: dict) -> None:
        """Test creating a tool in database."""
        tool = Tool(**sample_tool_data)
        async_session.add(tool)
        await async_session.commit()
        await async_session.refresh(tool)
        
        assert tool.id is not None
        assert tool.created_at is not None

    async def test_query_tool_by_name(self, async_session: "AsyncSession", sample_tool_data: dict) -> None:
        """Test querying tool by name."""
        tool = Tool(**sample_tool_data)
        async_session.add(tool)
        await async_session.commit()
        
        result = await async_session.execute(
            select(Tool).where(Tool.name == "test_search_tool")
        )
        found_tool = result.scalar_one()
        
        assert found_tool is not None
        assert found_tool.name == "test_search_tool"

    async def test_update_tool_status(self, async_session: "AsyncSession", sample_tool_data: dict) -> None:
        """Test updating tool status."""
        tool = Tool(**sample_tool_data)
        async_session.add(tool)
        await async_session.commit()
        
        tool.status = ToolStatus.DEPRECATED.value
        await async_session.commit()
        await async_session.refresh(tool)
        
        assert tool.status == "deprecated"

    async def test_delete_tool(self, async_session: "AsyncSession", sample_tool_data: dict) -> None:
        """Test deleting a tool."""
        tool = Tool(**sample_tool_data)
        async_session.add(tool)
        await async_session.commit()
        
        tool_id = tool.id
        await async_session.delete(tool)
        await async_session.commit()
        
        result = await async_session.execute(
            select(Tool).where(Tool.id == tool_id)
        )
        assert result.scalar_one_or_none() is None
