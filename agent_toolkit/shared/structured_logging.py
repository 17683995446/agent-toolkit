"""Shared logging utilities for Agent Toolkit."""

import logging
import sys
from typing import Any, Optional
from contextvars import ContextVar
from datetime import datetime
from functools import lru_cache

import structlog
from structlog.types import Processor

# Global state
_logging_initialized = False


request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


def add_context(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Add request context to log entries."""
    event_dict["request_id"] = request_id_var.get()
    event_dict["user_id"] = user_id_var.get()
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Add timestamp to log entries."""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict


def _ensure_logging_initialized():
    """确保日志系统已初始化"""
    global _logging_initialized
    if not _logging_initialized:
        setup_logging()


def setup_logging(config=None) -> None:
    """Setup structured logging."""
    global _logging_initialized
    
    try:
        from agent_toolkit.shared.application_settings import get_settings
        settings = get_settings()
    except Exception:
        # 如果无法获取配置，使用默认值
        settings = None
    
    if config is None and settings is not None:
        config = settings.logging
    
    # 处理配置对象的情况
    if config is not None and hasattr(config, 'level') and hasattr(config, 'format'):
        level = config.level
        format = config.format
    else:
        level = "INFO"
        format = "json"

    log_level = getattr(logging, str(level).upper(), logging.INFO)

    processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_context,
    ]

    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )

    # 使用标准库日志工厂
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    _logging_initialized = True


@lru_cache(maxsize=1)
def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    _ensure_logging_initialized()
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class that provides logging capabilities."""
    
    _logger: Optional[structlog.stdlib.BoundLogger] = None

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for this class."""
        if self._logger is None:
            name = f"{self.__class__.__module__}.{self.__class__.__name__}"
            self._logger = get_logger(name)
        return self._logger


class RequestContextLogger:
    """Context manager for request-scoped logging."""

    def __init__(self, request_id: str, user_id: str = ""):
        self.request_id = request_id
        self.user_id = user_id
        self._token = None

    def __enter__(self) -> "RequestContextLogger":
        self._token = request_id_var.set(self.request_id)
        user_id_var.set(self.user_id)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._token is not None:
            request_id_var.reset(self._token)
        user_id_var.set("")
