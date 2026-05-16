"""Unit tests for Shared configuration."""

import pytest
from unittest.mock import patch
import os

from agent_toolkit.shared.application_settings import (
    Settings,
    DatabaseConfig,
    RedisConfig,
    LoggingConfig,
    get_settings,
    reload_settings,
)


class TestDatabaseConfig:
    """Test suite for DatabaseConfig."""

    def test_default_values(self) -> None:
        """Test default database configuration."""
        config = DatabaseConfig()
        
        assert config.url == "sqlite:///./agent_toolkit.db"
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.echo is False

    def test_custom_values(self) -> None:
        """Test custom database configuration."""
        config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost/db",
            pool_size=20,
            max_overflow=40
        )
        
        assert "postgresql" in config.url
        assert config.pool_size == 20


class TestRedisConfig:
    """Test suite for RedisConfig."""

    def test_default_values(self) -> None:
        """Test default Redis configuration."""
        config = RedisConfig()
        
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.ssl is False

    def test_custom_values(self) -> None:
        """Test custom Redis configuration."""
        config = RedisConfig(
            host="redis.example.com",
            port=6380,
            password="secret",
            ssl=True
        )
        
        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.password == "secret"
        assert config.ssl is True


class TestLoggingConfig:
    """Test suite for LoggingConfig."""

    def test_default_values(self) -> None:
        """Test default logging configuration."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.format == "json"
        assert "stdout" in config.output

    def test_custom_values(self) -> None:
        """Test custom logging configuration."""
        config = LoggingConfig(
            level="DEBUG",
            format="text",
            file_path="/var/log/app.log"
        )
        
        assert config.level == "DEBUG"
        assert config.file_path == "/var/log/app.log"


class TestSettings:
    """Test suite for Settings."""

    def test_default_environment(self) -> None:
        """Test default environment."""
        settings = Settings()
        
        assert settings.environment == "development"
        assert settings.debug is False

    def test_environment_validation(self) -> None:
        """Test environment validation."""
        settings = Settings(environment="production")
        
        assert settings.environment == "production"
        assert settings.is_production() is True

    def test_invalid_environment(self) -> None:
        """Test invalid environment raises error."""
        with pytest.raises(ValueError):
            Settings(environment="invalid")

    def test_get_database_url(self) -> None:
        """Test getting database URL."""
        settings = Settings()
        
        url = settings.get_database_url()
        assert url is not None

    def test_test_environment_url(self) -> None:
        """Test test environment uses in-memory database."""
        settings = Settings(environment="test")
        
        url = settings.get_database_url()
        assert "test" in url

    @patch.dict(os.environ, {"AGENT_TOOLKIT_DEBUG": "true"})
    def test_env_override(self) -> None:
        """Test environment variable override."""
        settings = Settings()
        
        assert settings.debug is True

    def test_reload_settings(self) -> None:
        """Test reloading settings."""
        settings1 = get_settings()
        settings2 = reload_settings()
        
        assert settings1 is not settings2
