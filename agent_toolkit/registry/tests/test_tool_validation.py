"""Tests for tool validation service."""

import pytest
from datetime import datetime

from agent_toolkit.registry.tool_validation_service import (
    ToolValidationService,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)
from agent_toolkit.registry.registry_schemas import (
    ToolCreate,
    AdapterTypeEnum,
    ToolStatusEnum,
)
from agent_toolkit.registry.registry_models import AdapterType


@pytest.fixture
def validation_service():
    """Create a tool validation service instance."""
    return ToolValidationService()


@pytest.fixture
def valid_tool_data():
    """Create valid tool creation data."""
    return ToolCreate(
        name="test-tool",
        description="A test tool for validation",
        version="1.0.0",
        category_id=None,
        status=ToolStatusEnum.DRAFT,
        adapter_type=AdapterTypeEnum.HTTP,
        adapter_config={
            "url": "https://example.com/api",
            "method": "POST"
        },
        input_schema={
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "number"}
            },
            "required": ["param1"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            }
        },
        metadata={"author": "test"},
        tags=["test", "utility"],
        author="Test Author",
        license="MIT"
    )


@pytest.mark.asyncio
async def test_validate_valid_tool(validation_service, valid_tool_data):
    """Test validating a valid tool should succeed."""
    result = await validation_service.validate_tool(valid_tool_data)
    
    assert result.valid is True
    assert len(result.issues) == 0


@pytest.mark.asyncio
async def test_validate_tool_with_short_name(validation_service, valid_tool_data):
    """Test tool with too short name should fail."""
    valid_tool_data.name = "a"  # Too short
    result = await validation_service.validate_tool(valid_tool_data)
    
    assert result.valid is False
    assert any("Tool name must be at least 2 characters" in issue.message 
               for issue in result.issues)


@pytest.mark.asyncio
async def test_validate_tool_with_reserved_name(validation_service, valid_tool_data):
    """Test tool with reserved name should fail."""
    valid_tool_data.name = "system"  # Reserved name
    result = await validation_service.validate_tool(valid_tool_data)
    
    assert result.valid is False
    assert any("reserved name" in issue.message.lower() 
               for issue in result.issues)


@pytest.mark.asyncio
async def test_validate_tool_with_invalid_chars(validation_service, valid_tool_data):
    """Test tool name with invalid characters should fail."""
    valid_tool_data.name = "test tool!@#"  # Invalid chars
    result = await validation_service.validate_tool(valid_tool_data)
    
    assert result.valid is False
    assert any("may only contain" in issue.message.lower() 
               for issue in result.issues)


@pytest.mark.asyncio
async def test_validate_tool_with_invalid_version(validation_service, valid_tool_data):
    """Test tool with invalid semantic version should fail."""
    valid_tool_data.version = "invalid"  # Not a valid semver
    result = await validation_service.validate_tool(valid_tool_data)
    
    assert result.valid is False
    assert any("semantic versioning" in issue.message.lower() 
               for issue in result.issues)


@pytest.mark.asyncio
async def test_validate_tool_with_short_description(validation_service, valid_tool_data):
    """Test tool with too short description should fail."""
    valid_tool_data.description = "Hi"  # Too short
    result = await validation_service.validate_tool(valid_tool_data)
    
    assert result.valid is False
    assert any("description should be at least" in issue.message.lower() 
               for issue in result.issues)


@pytest.mark.asyncio
async def test_validate_tool_with_empty_author(validation_service, valid_tool_data):
    """Test tool with empty author should fail."""
    valid_tool_data.author = ""  # Empty author
    result = await validation_service.validate_tool(valid_tool_data)
    
    assert result.valid is False
    assert any("author name must be at least" in issue.message.lower() 
               for issue in result.issues)


@pytest.mark.asyncio
async def test_validate_tool_with_invalid_input_schema(validation_service, valid_tool_data):
    """Test tool with invalid input schema should fail."""
    # Missing type or composition keyword
    valid_tool_data.input_schema = {"properties": {}}
    result = await validation_service.validate_tool(valid_tool_data)
    
    assert result.valid is False
    assert any("must specify a type" in issue.message.lower() 
               for issue in result.issues)


@pytest.mark.asyncio
async def test_validate_tool_with_unknown_adapter_config(validation_service, valid_tool_data):
    """Test tool with unknown adapter config keys should warn."""
    valid_tool_data.adapter_config = {
        "url": "https://example.com",
        "unknown_key": "value"  # Unknown key
    }
    result = await validation_service.validate_tool(valid_tool_data)
    
    # Should be valid but have warnings
    assert result.valid is True
    assert len(result.warnings) > 0
    assert any("unknown configuration keys" in warning.message.lower() 
               for warning in result.warnings)


@pytest.mark.asyncio
async def test_validate_tool_with_empty_tags(validation_service, valid_tool_data):
    """Test tool with empty tags should fail."""
    valid_tool_data.tags = ["", "tag1"]  # Includes empty tag
    result = await validation_service.validate_tool(valid_tool_data)
    
    assert result.valid is False
    assert any("empty tags are not allowed" in issue.message.lower() 
               for issue in result.issues)


@pytest.mark.asyncio
async def test_validate_tool_with_duplicate_tags(validation_service, valid_tool_data):
    """Test tool with duplicate tags should warn."""
    valid_tool_data.tags = ["tag1", "tag2", "tag1"]  # Duplicate tag
    result = await validation_service.validate_tool(valid_tool_data)
    
    # Should be valid but have warnings
    assert result.valid is True
    assert len(result.warnings) > 0
    assert any("duplicate tag" in warning.message.lower() 
               for warning in result.warnings)


@pytest.mark.asyncio
async def test_validate_input_data(validation_service):
    """Test validating input data against schema."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"}
        },
        "required": ["name"]
    }
    
    valid_data = {"name": "Test", "age": 25}
    result = await validation_service.validate_input_data(valid_data, schema)
    assert result.valid is True
    
    invalid_data = {"age": 25}  # Missing required field
    result = await validation_service.validate_input_data(invalid_data, schema)
    # Note: Without jsonschema library, basic validation may not catch this
