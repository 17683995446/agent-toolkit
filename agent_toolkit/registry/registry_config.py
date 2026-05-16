"""Registry module configuration."""

from pathlib import Path
from typing import Optional, List
from pydantic import Field, field_validator

from agent_toolkit.shared.application_settings import BaseModel


class RegistrySettings(BaseModel):
    """Settings specific to the registry module."""
    
    storage_path: Path = Field(default=Path("./registry_storage"))
    max_tool_size_mb: int = Field(default=100, ge=1)
    allowed_categories: List[str] = Field(default_factory=lambda: [
        "data_processing",
        "web_scraping",
        "file_operations",
        "api_calls",
        "computation",
        "custom",
    ])
    enable_versioning: bool = Field(default=True)
    default_page_size: int = Field(default=20, ge=1, le=100)
    max_page_size: int = Field(default=100, ge=1)
    cache_ttl_seconds: int = Field(default=300, ge=0)
    
    @field_validator("storage_path")
    @classmethod
    def create_storage_dir(cls, v: Path) -> Path:
        """Ensure storage directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v


class RegistryConfig:
    """Registry configuration container."""
    
    def __init__(self):
        self.settings = RegistrySettings()
    
    def get_settings(self) -> RegistrySettings:
        """Get current settings."""
        return self.settings


registry_config = RegistryConfig()
