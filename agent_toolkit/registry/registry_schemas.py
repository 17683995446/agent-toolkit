"""Pydantic schemas for Tool Registry API."""

from datetime import datetime
from typing import Any, Optional, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator

from agent_toolkit.registry.registry_models import ToolStatus


class ToolStatusEnum(str, Enum):
    """Tool status enumeration for API."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class AdapterTypeEnum(str, Enum):
    """Adapter type enumeration for API."""
    HTTP = "http"
    CLI = "cli"
    SDK = "sdk"
    FUNCTION = "function"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"


class ToolBase(BaseModel):
    """Base schema for Tool."""
    name: str = Field(..., min_length=1, max_length=200, description="Tool name")
    description: str = Field(..., min_length=1, description="Tool description")
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$', description="Semantic version")
    category_id: Optional[int] = Field(None, description="Category ID")
    status: ToolStatusEnum = Field(ToolStatusEnum.DRAFT, description="Tool status")
    adapter_type: AdapterTypeEnum = Field(..., description="Adapter type")
    adapter_config: dict[str, Any] = Field(..., description="Adapter configuration")
    input_schema: dict[str, Any] = Field(..., description="Input JSON schema")
    output_schema: Optional[dict[str, Any]] = Field(None, description="Output JSON schema")
    extra_metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata", alias="metadata")
    tags: List[str] = Field(default_factory=list, description="Tool tags")
    author: str = Field(..., description="Tool author")
    license: Optional[str] = Field(None, description="License type")
    
    model_config = ConfigDict(populate_by_name=True)


class ToolCreate(ToolBase):
    """Schema for creating a Tool."""
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tool name."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Name must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower()


class ToolUpdate(BaseModel):
    """Schema for updating a Tool."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    version: Optional[str] = Field(None, pattern=r'^\d+\.\d+\.\d+$')
    category_id: Optional[int] = None
    status: Optional[ToolStatusEnum] = None
    adapter_type: Optional[AdapterTypeEnum] = None
    adapter_config: Optional[dict[str, Any]] = None
    input_schema: Optional[dict[str, Any]] = None
    output_schema: Optional[dict[str, Any]] = None
    extra_metadata: Optional[dict[str, Any]] = Field(None, alias="metadata")
    tags: Optional[List[str]] = None
    license: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class ToolVersionCreate(BaseModel):
    """Schema for creating a ToolVersion."""
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$', description="Semantic version")
    changelog: Optional[str] = Field(None, description="Version changelog")
    breaking_changes: bool = Field(False, description="Has breaking changes")
    code_hash: Optional[str] = Field(None, description="Code hash")
    artifact_url: Optional[str] = Field(None, description="Artifact URL")


class ToolVersionResponse(BaseModel):
    """Schema for ToolVersion response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tool_id: int
    version: str
    changelog: Optional[str]
    breaking_changes: bool
    code_hash: Optional[str]
    artifact_url: Optional[str]
    download_count: int
    created_at: datetime


class ToolResponse(ToolBase):
    """Schema for Tool response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: str
    usage_count: int
    rating: Optional[float]
    created_at: datetime
    updated_at: datetime
    deprecated_at: Optional[datetime]
    versions: Optional[List[ToolVersionResponse]] = None
    
    @field_validator('status', mode='before')
    @classmethod
    def convert_status(cls, v: Any) -> str:
        """Convert status enum to string."""
        if isinstance(v, ToolStatus):
            return v.value
        return v


class ToolListResponse(BaseModel):
    """Schema for paginated Tool list response."""
    items: List[ToolResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ToolSearchQuery(BaseModel):
    """Schema for tool search query."""
    query: Optional[str] = Field(None, description="Search query")
    category_id: Optional[int] = Field(None, description="Filter by category")
    status: Optional[ToolStatusEnum] = Field(None, description="Filter by status")
    adapter_type: Optional[AdapterTypeEnum] = Field(None, description="Filter by adapter type")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    author: Optional[str] = Field(None, description="Filter by author")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Page size")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern=r'^(asc|desc)$', description="Sort order")


class ToolCategoryBase(BaseModel):
    """Base schema for ToolCategory."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    extra_metadata: Optional[dict[str, Any]] = Field(None, alias="metadata")
    
    model_config = ConfigDict(populate_by_name=True)


class ToolCategoryCreate(ToolCategoryBase):
    """Schema for creating a ToolCategory."""
    pass


class ToolCategoryUpdate(BaseModel):
    """Schema for updating a ToolCategory."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    extra_metadata: Optional[dict[str, Any]] = Field(None, alias="metadata")
    
    model_config = ConfigDict(populate_by_name=True)


class ToolCategoryResponse(ToolCategoryBase):
    """Schema for ToolCategory response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
    children: Optional[List["ToolCategoryResponse"]] = None


class ToolDependencyResponse(BaseModel):
    """Schema for tool dependency information."""
    model_config = ConfigDict(from_attributes=True)
    
    tool_id: int
    tool_name: str
    tool_version: str
    dependency_type: str


class ToolStatsResponse(BaseModel):
    """Schema for tool statistics."""
    total_tools: int
    active_tools: int
    deprecated_tools: int
    total_downloads: int
    average_rating: Optional[float]
    top_tags: List[dict[str, Any]]


class ToolInstallRequest(BaseModel):
    """Schema for tool installation request."""
    version: Optional[str] = Field(None, description="Specific version to install")
    force: bool = Field(False, description="Force reinstall")


class ToolInstallResponse(BaseModel):
    """Schema for tool installation response."""
    success: bool
    message: str
    tool_id: int
    version: str
    installed_at: datetime


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str
    database: str
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Schema for error response."""
    error: str
    message: str
    error_code: Optional[str] = None
    details: Optional[dict[str, Any]] = None


ToolCategoryResponse.model_rebuild()
