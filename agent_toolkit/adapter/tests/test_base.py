"""Unit tests for BaseAdapter."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from agent_toolkit.adapter.base_adapter import (
    BaseAdapter,
    AdapterType,
    AdapterConfig,
    AdapterResult,
    ToolMetadata,
    ExecutionStatus,
)


class TestAdapterConfig:
    """Test suite for AdapterConfig."""

    def test_default_config(self) -> None:
        """Test default adapter configuration."""
        config = AdapterConfig()
        
        assert config.timeout == 30
        assert config.retry_count == 0
        assert config.retry_delay == 1.0
        assert config.enable_caching is False
        assert config.cache_ttl == 300

    def test_custom_config(self) -> None:
        """Test custom adapter configuration."""
        config = AdapterConfig(
            timeout=60,
            retry_count=3,
            retry_delay=2.0,
            enable_caching=True,
            cache_ttl=600
        )
        
        assert config.timeout == 60
        assert config.retry_count == 3
        assert config.retry_delay == 2.0
        assert config.enable_caching is True
        assert config.cache_ttl == 600


class TestAdapterResult:
    """Test suite for AdapterResult."""

    def test_successful_result(self) -> None:
        """Test creating a successful result."""
        result = AdapterResult(
            status=ExecutionStatus.SUCCESS,
            data={"key": "value"},
            execution_time_ms=150.5
        )
        
        assert result.is_success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_failed_result(self) -> None:
        """Test creating a failed result."""
        result = AdapterResult(
            status=ExecutionStatus.FAILURE,
            error="Connection timeout",
            execution_time_ms=30000.0
        )
        
        assert result.is_success is False
        assert result.data is None
        assert result.error == "Connection timeout"

    def test_result_to_dict(self) -> None:
        """Test converting result to dictionary."""
        result = AdapterResult(
            status=ExecutionStatus.SUCCESS,
            data={"result": "ok"},
            metadata={"request_id": "123"}
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["status"] == "success"
        assert result_dict["data"] == {"result": "ok"}
        assert result_dict["error"] is None
        assert result_dict["metadata"]["request_id"] == "123"
        assert "timestamp" in result_dict


class TestToolMetadata:
    """Test suite for ToolMetadata."""

    def test_metadata_creation(self) -> None:
        """Test creating tool metadata."""
        metadata = ToolMetadata(
            name="test_tool",
            version="1.0.0",
            adapter_type=AdapterType.HTTP,
            description="A test tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            tags=["test", "example"]
        )
        
        assert metadata.name == "test_tool"
        assert metadata.version == "1.0.0"
        assert metadata.adapter_type == AdapterType.HTTP
        assert len(metadata.tags) == 2


class ConcreteTestAdapter(BaseAdapter):
    """Concrete implementation of BaseAdapter for testing."""
    
    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.HTTP
    
    async def initialize(self) -> None:
        self._initialized = True
    
    async def execute(
        self,
        input_data: dict,
        context: dict | None = None
    ) -> AdapterResult:
        return AdapterResult(
            status=ExecutionStatus.SUCCESS,
            data={"executed": True, "input": input_data},
            execution_time_ms=100.0
        )
    
    async def validate_input(self, input_data: dict) -> bool:
        return "required_field" in input_data


class TestBaseAdapter:
    """Test suite for BaseAdapter."""

    @pytest.mark.asyncio
    async def test_adapter_initialization(self) -> None:
        """Test adapter initialization."""
        adapter = ConcreteTestAdapter()
        
        assert adapter._is_initialized is False
        await adapter.initialize()
        assert adapter._is_initialized is True

    @pytest.mark.asyncio
    async def test_adapter_execute(self) -> None:
        """Test adapter execution."""
        adapter = ConcreteTestAdapter()
        await adapter.initialize()
        
        result = await adapter.execute({"test": "data"})
        
        assert result.is_success is True
        assert result.data["executed"] is True

    @pytest.mark.asyncio
    async def test_adapter_health_check(self) -> None:
        """Test adapter health check."""
        adapter = ConcreteTestAdapter()
        
        assert await adapter.health_check() is False
        
        await adapter.initialize()
        assert await adapter.health_check() is True

    @pytest.mark.asyncio
    async def test_adapter_validation(self) -> None:
        """Test input validation."""
        adapter = ConcreteTestAdapter()
        
        assert await adapter.validate_input({"required_field": "value"}) is True
        assert await adapter.validate_input({}) is False

    @pytest.mark.asyncio
    async def test_adapter_cleanup(self) -> None:
        """Test adapter cleanup."""
        adapter = ConcreteTestAdapter()
        await adapter.initialize()
        
        assert adapter._is_initialized is True
        await adapter.cleanup()
        assert adapter._is_initialized is False

    @pytest.mark.asyncio
    async def test_ensure_initialized(self) -> None:
        """Test lazy initialization."""
        adapter = ConcreteTestAdapter()
        
        assert adapter._is_initialized is False
        await adapter._ensure_initialized()
        assert adapter._is_initialized is True
        
        await adapter._ensure_initialized()
        assert adapter._is_initialized is True
