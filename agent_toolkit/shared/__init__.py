"""Shared utilities for Agent Toolkit."""

from agent_toolkit.shared.application_settings import get_settings, Settings
from agent_toolkit.shared.database_connection import Base, get_db_session
from agent_toolkit.shared.custom_exceptions import (
    AgentToolkitException,
    ValidationError,
    NotFoundError,
    DuplicateError,
    ConfigurationError,
)
from agent_toolkit.shared.structured_logging import setup_logging, get_logger, LoggerMixin
from agent_toolkit.shared.api_response import (
    APIResponse,
    APIException,
    ErrorCode,
    ErrorDetail,
    NotFoundException,
    ValidationException,
    UnauthorizedException,
    ForbiddenException,
    register_exception_handlers,
)
from agent_toolkit.shared.pagination import (
    PaginatedResponse,
    PaginationMeta,
    PageParams,
)
from agent_toolkit.shared.performance import (
    PerformanceMonitor,
    PerformanceMetric,
    get_performance_monitor,
    track_performance,
    monitor_performance,
    get_performance_report,
)

__version__ = "0.1.0"

__all__ = [
    # 配置和数据库
    "__version__",
    "get_settings",
    "Settings",
    "Base",
    "get_db_session",
    
    # 异常处理
    "AgentToolkitException",
    "ValidationError",
    "NotFoundError",
    "DuplicateError",
    "ConfigurationError",
    "APIResponse",
    "APIException",
    "ErrorCode",
    "ErrorDetail",
    "NotFoundException",
    "ValidationException",
    "UnauthorizedException",
    "ForbiddenException",
    "register_exception_handlers",
    
    # 日志
    "setup_logging",
    "get_logger",
    "LoggerMixin",
    
    # 分页
    "PaginatedResponse",
    "PaginationMeta",
    "PageParams",
    
    # 性能监控
    "PerformanceMonitor",
    "PerformanceMetric",
    "get_performance_monitor",
    "track_performance",
    "monitor_performance",
    "get_performance_report",
]
