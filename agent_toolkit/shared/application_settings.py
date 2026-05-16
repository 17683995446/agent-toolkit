"""Enhanced configuration management for Agent Toolkit using Pydantic Settings."""

from functools import lru_cache
from typing import Optional, Dict, Any, List
from pathlib import Path
import os
import yaml

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(default="sqlite+aiosqlite:///./agent_toolkit.db")
    pool_size: int = Field(default=10, ge=1)
    max_overflow: int = Field(default=20, ge=0)
    echo: bool = Field(default=False)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=0)
    pool_pre_ping: bool = Field(default=True)


class RedisConfig(BaseModel):
    """Redis configuration for caching and message queue."""
    host: str = Field(default="localhost")
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0)
    password: Optional[str] = Field(default=None)
    ssl: bool = Field(default=False)
    max_connections: int = Field(default=50, ge=1)

    @property
    def url(self) -> str:
        """Generate Redis URL."""
        scheme = "rediss" if self.ssl else "redis"
        auth = f":{self.password}@" if self.password else ""
        return f"{scheme}://{auth}{self.host}:{self.port}/{self.db}"


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    format: str = Field(default="json")
    output: List[str] = Field(default_factory=lambda: ["stdout"])
    file_path: Optional[str] = None
    rotation: str = Field(default="daily")
    retention: int = Field(default=7, ge=1)
    max_bytes: int = Field(default=10485760)


class ObservabilityConfig(BaseModel):
    """Observability configuration."""
    enable_tracing: bool = Field(default=True)
    enable_metrics: bool = Field(default=True)
    tracing_endpoint: str = Field(default="http://localhost:4317")
    metrics_port: int = Field(default=9090)
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    service_name: str = Field(default="agent-toolkit")
    service_version: str = Field(default="0.1.0")


class SecurityConfig(BaseModel):
    """Security configuration."""
    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1)
    refresh_token_expire_days: int = Field(default=7, ge=1)
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])


class RuntimeConfig(BaseModel):
    """Runtime environment configuration."""
    executor_type: str = Field(default="docker")
    default_timeout: int = Field(default=300, ge=1)
    max_concurrent_executions: int = Field(default=100, ge=1)
    resource_limits: Dict[str, Any] = Field(default_factory=lambda: {
        "cpu_limit": "2",
        "memory_limit": "4Gi",
        "disk_limit": "10Gi",
        "network_bandwidth": "1Gbps"
    })
    sandbox_enabled: bool = Field(default=True)
    docker_host: str = Field(default="unix:///var/run/docker.sock")
    kubernetes_config: Optional[str] = Field(default=None)


class RegistryConfig(BaseModel):
    """Registry service configuration."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1)
    reload: bool = Field(default=False)
    title: str = Field(default="Agent Toolkit Registry")
    description: str = Field(default="Tool Registry API")
    version: str = Field(default="0.1.0")


class ServerConfig(BaseModel):
    """HTTP server configuration."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1)
    reload: bool = Field(default=False)
    debug: bool = Field(default=False)
    timeout_keep_alive: int = Field(default=5)
    graceful_shutdown_timeout: int = Field(default=15)
    limit_concurrency: Optional[int] = Field(default=None)
    limit_max_requests: Optional[int] = Field(default=None)

    @property
    def url(self) -> str:
        """Generate server URL."""
        return f"http://{self.host}:{self.port}"


class AdapterConfig(BaseModel):
    """Adapter configuration."""
    http_timeout: int = Field(default=30, ge=1)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0)
    retry_backoff: str = Field(default="exponential")
    enable_caching: bool = Field(default=True)
    cache_ttl: int = Field(default=300, ge=0)
    max_connections: int = Field(default=100)
    connection_timeout: int = Field(default=10)


class CeleryConfig(BaseModel):
    """Celery configuration for task queue."""
    broker_url: str = Field(default="redis://localhost:6379/0")
    result_backend: str = Field(default="redis://localhost:6379/0")
    task_serializer: str = Field(default="json")
    result_serializer: str = Field(default="json")
    accept_content: List[str] = Field(default_factory=lambda: ["json"])
    timezone: str = Field(default="UTC")
    enable_utc: bool = Field(default=True)
    task_track_started: bool = Field(default=True)
    task_time_limit: int = Field(default=3600)
    worker_prefetch_multiplier: int = Field(default=4)


class Settings(BaseSettings):
    """Main settings class for Agent Toolkit."""
    
    model_config = SettingsConfigDict(
        env_prefix="AGENT_TOOLKIT_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )
    
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    registry: RegistryConfig = Field(default_factory=RegistryConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    adapter: AdapterConfig = Field(default_factory=AdapterConfig)
    celery: CeleryConfig = Field(default_factory=CeleryConfig)
    
    project_root: Path = Field(default_factory=lambda: Path.cwd())
    config_dir: Optional[Path] = Field(default=None)
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name."""
        allowed = ["development", "staging", "production", "test"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @field_validator("config_dir")
    @classmethod
    def set_config_dir(cls, v: Optional[Path], info) -> Path:
        """Set config directory based on project root."""
        if v is None:
            project_root = info.data.get("project_root", Path.cwd())
            return project_root / "configs"
        return v

    @model_validator(mode="after")
    def validate_config_files(self) -> "Settings":
        """Validate configuration files exist."""
        config_file = self.config_dir / f"{self.environment}.yaml"
        if config_file.exists():
            self._load_from_yaml(config_file)
        return self

    def _load_from_yaml(self, config_file: Path) -> None:
        """Load additional config from YAML file."""
        try:
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)
                if config_data:
                    for key, value in config_data.items():
                        if hasattr(self, key):
                            section = getattr(self, key)
                            if isinstance(section, BaseModel):
                                for sub_key, sub_value in value.items():
                                    if hasattr(section, sub_key):
                                        setattr(section, sub_key, sub_value)
        except Exception as e:
            # Log the error but don't fail
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load config file {config_file}: {e}")

    def get_database_url(self) -> str:
        """Get database URL from database config."""
        return self.database.url

    def get_redis_url(self) -> str:
        """Get Redis URL from redis config."""
        return self.redis.url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the settings instance (cached)."""
    return Settings()


def reload_settings() -> Settings:
    """Reload settings (clear cache and reload)."""
    get_settings.cache_clear()
    return get_settings()


def get_settings_from_file(config_path: Path) -> Settings:
    """Create settings from a specific config file."""
    settings = Settings()
    if config_path.exists():
        settings._load_from_yaml(config_path)
    return settings


def override_settings(**kwargs) -> Settings:
    """Override specific settings for testing."""
    settings = get_settings()
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings
