"""Database models for Tool Registry."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from agent_toolkit.shared.database_connection import Base


class ToolStatus(str, Enum):
    """Tool status enumeration."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class AdapterType(str, Enum):
    """Adapter type enumeration."""
    HTTP = "http"
    CLI = "cli"
    SDK = "sdk"
    FUNCTION = "function"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"


class ToolCategory(Base):
    """Tool category model."""
    
    __tablename__ = "tool_categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tool_categories.id"), nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    tools: Mapped[List["Tool"]] = relationship("Tool", back_populates="category")
    parent: Mapped[Optional["ToolCategory"]] = relationship(
        "ToolCategory",
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[List["ToolCategory"]] = relationship(
        "ToolCategory",
        back_populates="parent"
    )


class Tool(Base):
    """Tool model representing a registered tool."""
    
    __tablename__ = "tools"
    __table_args__ = (
        Index("idx_tool_name", "name"),
        Index("idx_tool_category", "category_id"),
        Index("idx_tool_status", "status"),
        Index("idx_tool_created", "created_at"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tool_categories.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=ToolStatus.DRAFT.value)
    
    adapter_type: Mapped[str] = mapped_column(String(50), nullable=False)
    adapter_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    input_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    output_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    license: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    deprecated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    versions: Mapped[List["ToolVersion"]] = relationship(
        "ToolVersion",
        back_populates="tool",
        cascade="all, delete-orphan"
    )
    category: Mapped[Optional["ToolCategory"]] = relationship("ToolCategory", back_populates="tools")


class ToolVersion(Base):
    """Tool version history."""
    
    __tablename__ = "tool_versions"
    __table_args__ = (
        Index("idx_version_tool", "tool_id", "version"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool_id: Mapped[int] = mapped_column(Integer, ForeignKey("tools.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    breaking_changes: Mapped[bool] = mapped_column(Boolean, default=False)
    
    code_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    artifact_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    tool: Mapped["Tool"] = relationship("Tool", back_populates="versions")
