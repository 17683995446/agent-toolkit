"""Shared pytest fixtures and configuration."""

import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from agent_toolkit.shared.database_connection import Base
from agent_toolkit.shared.application_settings import Settings, get_settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def settings() -> Settings:
    """Get test settings."""
    return get_settings()


@pytest.fixture
def sample_tool_data() -> dict:
    """Sample tool data for testing."""
    return {
        "name": "test_search_tool",
        "description": "A test search tool for unit testing",
        "version": "1.0.0",
        "category_id": 1,
        "status": "active",
        "adapter_type": "http",
        "adapter_config": {
            "base_url": "https://api.example.com",
            "endpoint": "/search",
            "method": "GET",
        },
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "results": {"type": "array"},
                "total": {"type": "integer"}
            }
        },
        "metadata": {
            "author": "Test Team",
            "license": "MIT",
            "tags": ["search", "test"]
        },
        "tags": ["search", "test"],
        "author": "Test Team",
        "license": "MIT"
    }


@pytest.fixture
def sample_adapter_config() -> dict:
    """Sample adapter configuration for testing."""
    return {
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 1.0,
        "enable_caching": True,
        "cache_ttl": 300
    }


@pytest.fixture
def sample_execution_context() -> dict:
    """Sample execution context for testing."""
    return {
        "request_id": "test-request-123",
        "user_id": "test-user-456",
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "source": "pytest",
            "version": "1.0"
        }
    }


@pytest.fixture
def mock_http_response() -> dict:
    """Mock HTTP response for testing."""
    return {
        "status": 200,
        "data": {
            "results": [
                {"id": 1, "title": "Result 1", "url": "https://example.com/1"},
                {"id": 2, "title": "Result 2", "url": "https://example.com/2"},
            ],
            "total": 2
        },
        "headers": {
            "content-type": "application/json"
        }
    }


@pytest.fixture
def mock_cli_output() -> dict:
    """Mock CLI output for testing."""
    return {
        "stdout": "Tool executed successfully",
        "stderr": "",
        "returncode": 0
    }
