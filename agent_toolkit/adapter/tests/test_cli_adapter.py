"""Unit tests for CLI Adapter."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from agent_toolkit.adapter.cli_adapter_implementation import CLIAdapter, CLIAdapterConfig
from agent_toolkit.adapter.base_adapter import AdapterType, ExecutionStatus


class TestCLIAdapterConfig:
    """Test suite for CLIAdapterConfig."""

    def test_default_cli_config(self) -> None:
        """Test default CLI adapter configuration."""
        config = CLIAdapterConfig(
            command="python test.py",
            working_dir="/tmp"
        )
        
        assert config.command == "python test.py"
        assert config.working_dir == "/tmp"
        assert config.timeout == 30
        assert config.shell is True

    def test_custom_cli_config(self) -> None:
        """Test custom CLI adapter configuration."""
        config = CLIAdapterConfig(
            command="docker run --rm image",
            working_dir="/app",
            env_vars={"KEY": "value"},
            shell=False,
            timeout=120
        )
        
        assert config.shell is False
        assert config.timeout == 120
        assert config.env_vars["KEY"] == "value"


class TestCLIAdapter:
    """Test suite for CLIAdapter."""

    @pytest.mark.asyncio
    async def test_adapter_type(self) -> None:
        """Test CLI adapter type."""
        adapter = CLIAdapter(
            CLIAdapterConfig(command="echo hello")
        )
        assert adapter.adapter_type == AdapterType.CLI

    @pytest.mark.asyncio
    async def test_initialize(self) -> None:
        """Test CLI adapter initialization."""
        adapter = CLIAdapter(
            CLIAdapterConfig(command="echo hello")
        )
        await adapter.initialize()
        assert adapter._is_initialized is True

    @pytest.mark.asyncio
    @patch("agent_toolkit.adapter.cli_adapter.asyncio.create_subprocess_shell")
    async def test_execute_success(self, mock_subprocess: AsyncMock) -> None:
        """Test successful CLI execution."""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        adapter = CLIAdapter(
            CLIAdapterConfig(command="echo hello")
        )
        await adapter.initialize()
        
        result = await adapter.execute({})
        
        assert result.is_success is True
        assert "output" in str(result.data)

    @pytest.mark.asyncio
    @patch("agent_toolkit.adapter.cli_adapter.asyncio.create_subprocess_shell")
    async def test_execute_with_error(self, mock_subprocess: AsyncMock) -> None:
        """Test CLI execution with error."""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"", b"error message"))
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process
        
        adapter = CLIAdapter(
            CLIAdapterConfig(command="false")
        )
        await adapter.initialize()
        
        result = await adapter.execute({})
        
        assert result.is_success is False
        assert "error" in result.error.lower()

    @pytest.mark.asyncio
    @patch("agent_toolkit.adapter.cli_adapter.asyncio.create_subprocess_shell")
    async def test_execute_timeout(self, mock_subprocess: AsyncMock) -> None:
        """Test CLI execution timeout."""
        async def slow_communicate():
            await asyncio.sleep(10)
            return (b"", b"")
        
        mock_process = AsyncMock()
        mock_process.communicate = slow_communicate
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        adapter = CLIAdapter(
            CLIAdapterConfig(command="sleep 100", timeout=1)
        )
        await adapter.initialize()
        
        result = await adapter.execute({})
        
        assert result.status == ExecutionStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_validate_input(self) -> None:
        """Test CLI adapter input validation."""
        adapter = CLIAdapter(
            CLIAdapterConfig(command="echo test")
        )
        
        assert await adapter.validate_input({}) is True
