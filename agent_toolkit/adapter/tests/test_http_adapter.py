"""Unit tests for HTTP Adapter."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import Response, Request

from agent_toolkit.adapter.http_adapter_implementation import HTTPAdapter, HTTPAdapterConfig
from agent_toolkit.adapter.base_adapter import AdapterType, ExecutionStatus


class TestHTTPAdapterConfig:
    """Test suite for HTTPAdapterConfig."""

    def test_default_http_config(self) -> None:
        """Test default HTTP adapter configuration."""
        config = HTTPAdapterConfig(
            base_url="https://api.example.com",
            endpoint="/test"
        )
        
        assert config.base_url == "https://api.example.com"
        assert config.endpoint == "/test"
        assert config.method == "GET"
        assert config.timeout == 30

    def test_custom_http_config(self) -> None:
        """Test custom HTTP adapter configuration."""
        config = HTTPAdapterConfig(
            base_url="https://custom.api.com",
            endpoint="/custom",
            method="POST",
            timeout=60,
            headers={"Authorization": "Bearer token"},
            verify_ssl=True
        )
        
        assert config.method == "POST"
        assert config.timeout == 60
        assert "Authorization" in config.headers


class TestHTTPAdapter:
    """Test suite for HTTPAdapter."""

    @pytest.mark.asyncio
    async def test_adapter_type(self) -> None:
        """Test HTTP adapter type."""
        adapter = HTTPAdapter(
            HTTPAdapterConfig(base_url="https://api.example.com")
        )
        assert adapter.adapter_type == AdapterType.HTTP

    @pytest.mark.asyncio
    async def test_initialize(self) -> None:
        """Test HTTP adapter initialization."""
        adapter = HTTPAdapter(
            HTTPAdapterConfig(base_url="https://api.example.com")
        )
        await adapter.initialize()
        assert adapter._is_initialized is True

    @pytest.mark.asyncio
    @patch("agent_toolkit.adapter.http_adapter.HTTPAdapter._send_request")
    async def test_execute_get_request(self, mock_send: AsyncMock) -> None:
        """Test executing GET request."""
        mock_send.return_value = {
            "status": 200,
            "data": {"result": "success"}
        }
        
        adapter = HTTPAdapter(
            HTTPAdapterConfig(
                base_url="https://api.example.com",
                endpoint="/test",
                method="GET"
            )
        )
        await adapter.initialize()
        
        result = await adapter.execute({"param": "value"})
        
        assert result.is_success is True
        assert result.data["result"] == "success"

    @pytest.mark.asyncio
    @patch("agent_toolkit.adapter.http_adapter.HTTPAdapter._send_request")
    async def test_execute_post_request(self, mock_send: AsyncMock) -> None:
        """Test executing POST request."""
        mock_send.return_value = {
            "status": 201,
            "data": {"id": 123}
        }
        
        adapter = HTTPAdapter(
            HTTPAdapterConfig(
                base_url="https://api.example.com",
                endpoint="/create",
                method="POST"
            )
        )
        await adapter.initialize()
        
        result = await adapter.execute({"name": "test"})
        
        assert result.is_success is True
        assert result.data["id"] == 123

    @pytest.mark.asyncio
    async def test_validate_input_schema(self) -> None:
        """Test input validation against schema."""
        adapter = HTTPAdapter(
            HTTPAdapterConfig(
                base_url="https://api.example.com",
                endpoint="/test",
                input_schema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string"}
                    }
                }
            )
        )
        
        assert await adapter.validate_input({"query": "test"}) is True
        assert await adapter.validate_input({}) is False

    @pytest.mark.asyncio
    @patch("agent_toolkit.adapter.http_adapter.HTTPAdapter._send_request")
    async def test_handle_error_response(self, mock_send: AsyncMock) -> None:
        """Test handling error responses."""
        mock_send.return_value = {
            "status": 404,
            "error": "Not Found"
        }
        
        adapter = HTTPAdapter(
            HTTPAdapterConfig(base_url="https://api.example.com", endpoint="/notfound")
        )
        await adapter.initialize()
        
        result = await adapter.execute({})
        
        assert result.is_success is False
        assert result.status == ExecutionStatus.FAILURE

    @pytest.mark.asyncio
    async def test_build_url(self) -> None:
        """Test URL building."""
        adapter = HTTPAdapter(
            HTTPAdapterConfig(
                base_url="https://api.example.com",
                endpoint="/test"
            )
        )
        
        url = adapter._build_url()
        assert url == "https://api.example.com/test"
        
        url_with_path = adapter._build_url(path="/specific")
        assert url_with_path == "https://api.example.com/specific"
