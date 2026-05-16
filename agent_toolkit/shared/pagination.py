"""
分页响应格式
提供统一的数据分页结构
"""

from typing import Any, Generic, List, TypeVar, Optional
from dataclasses import dataclass, field
from datetime import datetime

from agent_toolkit.shared.api_response import APIResponse


T = TypeVar("T")


@dataclass
class PaginationMeta:
    """分页元数据"""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(
        cls,
        page: int,
        page_size: int,
        total_items: int
    ) -> "PaginationMeta":
        """创建分页元数据"""
        total_pages = (total_items + page_size - 1) // page_size
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )


@dataclass
class PaginatedData(Generic[T]):
    """分页数据"""
    items: List[T]
    pagination: PaginationMeta
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "items": self.items if isinstance(self.items, list) else list(self.items),
            "pagination": {
                "page": self.pagination.page,
                "page_size": self.pagination.page_size,
                "total_items": self.pagination.total_items,
                "total_pages": self.pagination.total_pages,
                "has_next": self.pagination.has_next,
                "has_previous": self.pagination.has_previous
            }
        }


@dataclass
class PaginatedResponse(APIResponse):
    """分页响应"""
    items: Optional[List[Any]] = None
    pagination: Optional[PaginationMeta] = None
    
    @classmethod
    def create(
        cls,
        items: List[Any],
        page: int,
        page_size: int,
        total_items: int,
        message: Optional[str] = None
    ) -> "PaginatedResponse":
        """创建分页响应"""
        pagination = PaginationMeta.create(page, page_size, total_items)
        
        return cls(
            success=True,
            items=items,
            pagination=pagination,
            message=message,
            metadata={
                "total_items": total_items,
                "page": page,
                "page_size": page_size
            }
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        result = super().to_dict()
        result["items"] = self.items
        result["pagination"] = {
            "page": self.pagination.page,
            "page_size": self.pagination.page_size,
            "total_items": self.pagination.total_items,
            "total_pages": self.pagination.total_pages,
            "has_next": self.pagination.has_next,
            "has_previous": self.pagination.has_previous
        }
        return result


class PageParams:
    """分页参数"""
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), max_page_size)
        self.max_page_size = max_page_size
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """计算限制量"""
        return self.page_size
    
    def to_metadata(self) -> dict:
        """转换为元数据"""
        return {
            "page": self.page,
            "page_size": self.page_size,
            "max_page_size": self.max_page_size
        }
