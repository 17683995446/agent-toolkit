"""Unit tests for Runtime base components."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from agent_toolkit.runtime.base_executor import BaseExecutor, ExecutorConfig, ExecutionResult, ExecutionStatus


class TestExecutorConfig:
    """Test suite for ExecutorConfig."""

    def test_default_executor_config(self) -> None:
        """Test default executor configuration."""
        config = ExecutorConfig()
        
        assert config.timeout == 300
        assert config.max_retries == 3
        assert config.enable_sandbox is True
        assert config.memory_limit == "4Gi"

    def test_custom_executor_config(self) -> None:
        """Test custom executor configuration."""
        config = ExecutorConfig(
            timeout=600,
            max_retries=5,
            cpu_limit="4",
            memory_limit="8Gi",
            disk_limit="20Gi"
        )
        
        assert config.timeout == 600
        assert config.max_retries == 5
        assert config.cpu_limit == "4"
        assert config.memory_limit == "8Gi"


class TestExecutionResult:
    """Test suite for ExecutionResult."""

    def test_successful_execution(self) -> None:
        """Test successful execution result."""
        result = ExecutionResult(
            execution_id="exec-123",
            status=ExecutionStatus.SUCCESS,
            output={"result": "success"},
            exit_code=0,
            execution_time_ms=150.5
        )
        
        assert result.is_success is True
        assert result.output["result"] == "success"
        assert result.exit_code == 0

    def test_failed_execution(self) -> None:
        """Test failed execution result."""
        result = ExecutionResult(
            execution_id="exec-456",
            status=ExecutionStatus.FAILED,
            error="Runtime error",
            exit_code=1,
            execution_time_ms=50.0
        )
        
        assert result.is_success is False
        assert result.error == "Runtime error"

    def test_timeout_execution(self) -> None:
        """Test timeout execution result."""
        result = ExecutionResult(
            execution_id="exec-789",
            status=ExecutionStatus.TIMEOUT,
            exit_code=124,
            execution_time_ms=300000.0
        )
        
        assert result.status == ExecutionStatus.TIMEOUT
        assert result.exit_code == 124


class MockExecutor(BaseExecutor):
    """Mock executor for testing."""
    
    async def _do_execute(self, tool_id: str, input_data: dict, config: dict) -> ExecutionResult:
        return ExecutionResult(
            execution_id=f"mock-exec-{tool_id}",
            status=ExecutionStatus.SUCCESS,
            output={"executed": True},
            exit_code=0,
            execution_time_ms=100.0
        )


class TestBaseExecutor:
    """Test suite for BaseExecutor."""

    @pytest.mark.asyncio
    async def test_executor_initialization(self) -> None:
        """Test executor initialization."""
        executor = MockExecutor(ExecutorConfig())
        
        assert executor._is_initialized is False
        
        await executor.initialize()
        assert executor._is_initialized is True

    @pytest.mark.asyncio
    async def test_execute_tool(self) -> None:
        """Test executing a tool."""
        executor = MockExecutor(ExecutorConfig())
        await executor.initialize()
        
        result = await executor.execute("test-tool", {"param": "value"})
        
        assert result.is_success is True
        assert result.output["executed"] is True

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self) -> None:
        """Test execution with timeout."""
        executor = MockExecutor(ExecutorConfig(timeout=1))
        await executor.initialize()
        
        result = await executor.execute("test-tool", {"param": "value"})
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_executor_cleanup(self) -> None:
        """Test executor cleanup."""
        executor = MockExecutor(ExecutorConfig())
        await executor.initialize()
        
        assert executor._is_initialized is True
        await executor.cleanup()
        assert executor._is_initialized is False

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        """Test executor health check."""
        executor = MockExecutor(ExecutorConfig())
        
        assert await executor.health_check() is False
        
        await executor.initialize()
        assert await executor.health_check() is True

    @pytest.mark.asyncio
    async def test_get_execution_status(self) -> None:
        """Test getting execution status."""
        executor = MockExecutor(ExecutorConfig())
        await executor.initialize()
        
        result = await executor.execute("test-tool", {})
        status = executor.get_execution_status(result.execution_id)
        
        assert status is not None
        assert status.execution_id == result.execution_id
