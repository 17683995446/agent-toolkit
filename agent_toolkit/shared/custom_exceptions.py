"""
统一异常系统 - 所有模块的异常定义和处理
"""

from typing import Any, Dict, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class ErrorCode(str, Enum):
    """错误码枚举 - 标准化错误类型"""
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    DUPLICATE_ERROR = "DUPLICATE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    
    # 工具仓库错误 (3000-3999)
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_ALREADY_EXISTS = "TOOL_ALREADY_EXISTS"
    TOOL_VERSION_NOT_FOUND = "TOOL_VERSION_NOT_FOUND"
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    
    # 适配器错误 (4000-4999)
    ADAPTER_NOT_FOUND = "ADAPTER_NOT_FOUND"
    ADAPTER_EXECUTION_FAILED = "ADAPTER_EXECUTION_FAILED"
    ADAPTER_TIMEOUT = "ADAPTER_TIMEOUT"
    ADAPTER_HEALTH_CHECK_FAILED = "ADAPTER_HEALTH_CHECK_FAILED"
    ADAPTER_CONFIG_ERROR = "ADAPTER_CONFIG_ERROR"
    
    # 运行时错误 (5000-5999)
    EXECUTION_NOT_FOUND = "EXECUTION_NOT_FOUND"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EXECUTION_CANCELLED = "EXECUTION_CANCELLED"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    SANDBOX_ERROR = "SANDBOX_ERROR"
    
    # 编排器错误 (6000-6999)
    CHAIN_NOT_FOUND = "CHAIN_NOT_FOUND"
    CHAIN_EXECUTION_FAILED = "CHAIN_EXECUTION_FAILED"
    CIRCULAR_DEPENDENCY = "CIRCULAR_DEPENDENCY"
    INVALID_DEPENDENCY = "INVALID_DEPENDENCY"
    TASK_FAILED = "TASK_FAILED"
    INVALID_WORKFLOW = "INVALID_WORKFLOW"


class ChainStatus(str, Enum):
    """工具链执行状态 - 统一的枚举定义"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


@dataclass
class ErrorDetail:
    """详细错误信息"""
    error_code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details
        }


class AgentToolkitException(Exception):
    """基础异常类 - 所有自定义异常的基类"""
    
    def __init__(
        self, 
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.error_detail = ErrorDetail(
            error_code=error_code,
            message=message,
            details=details
        )
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.error_detail.to_dict()
    
    def __str__(self) -> str:
        return f"{self.error_code.value}: {self.message}"


class ValidationError(AgentToolkitException):
    """数据验证错误"""
    
    def __init__(
        self, 
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details
        )


class NotFoundError(AgentToolkitException):
    """资源未找到错误"""
    
    def __init__(
        self, 
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        all_details = {}
        if details:
            all_details.update(details)
        if resource_type:
            all_details["resource_type"] = resource_type
        if resource_id:
            all_details["resource_id"] = resource_id
        
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=message,
            details=all_details if all_details else None
        )


class DuplicateError(AgentToolkitException):
    """资源重复错误"""
    
    def __init__(
        self, 
        message: str,
        resource_type: Optional[str] = None,
        existing_id: Optional[Any] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if existing_id:
            details["existing_id"] = existing_id
        
        super().__init__(
            error_code=ErrorCode.DUPLICATE_ERROR,
            message=message,
            details=details if details else None
        )


class ConfigurationError(AgentToolkitException):
    """配置错误"""
    
    def __init__(
        self, 
        message: str,
        config_key: Optional[str] = None
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=message,
            details=details if details else None
        )


class ToolNotFoundError(AgentToolkitException):
    """工具未找到错误"""
    
    def __init__(
        self, 
        tool_id: Optional[int] = None,
        tool_name: Optional[str] = None
    ):
        details = {}
        message = "Tool not found"
        if tool_id:
            details["tool_id"] = tool_id
            message = f"Tool with ID {tool_id} not found"
        if tool_name:
            details["tool_name"] = tool_name
            message = f"Tool '{tool_name}' not found"
        
        super().__init__(
            error_code=ErrorCode.TOOL_NOT_FOUND,
            message=message,
            details=details
        )


class ToolAlreadyExistsError(AgentToolkitException):
    """工具已存在错误"""
    
    def __init__(
        self, 
        tool_name: str
    ):
        details = {"tool_name": tool_name}
        message = f"Tool '{tool_name}' already exists"
        
        super().__init__(
            error_code=ErrorCode.TOOL_ALREADY_EXISTS,
            message=message,
            details=details
        )


class ToolExecutionError(AgentToolkitException):
    """工具执行错误"""
    
    def __init__(
        self, 
        message: str,
        tool_name: Optional[str] = None,
        original_error: Optional[str] = None
    ):
        details = {}
        if tool_name:
            details["tool_name"] = tool_name
        if original_error:
            details["original_error"] = original_error
        
        super().__init__(
            error_code=ErrorCode.TOOL_EXECUTION_FAILED,
            message=message,
            details=details
        )


class AdapterExecutionError(AgentToolkitException):
    """适配器执行错误"""
    
    def __init__(
        self, 
        message: str,
        adapter_type: Optional[str] = None,
        original_error: Optional[str] = None
    ):
        details = {}
        if adapter_type:
            details["adapter_type"] = adapter_type
        if original_error:
            details["original_error"] = original_error
        
        super().__init__(
            error_code=ErrorCode.ADAPTER_EXECUTION_FAILED,
            message=message,
            details=details
        )


class ChainNotFoundError(AgentToolkitException):
    """工具链未找到错误"""
    
    def __init__(
        self, 
        chain_id: str
    ):
        details = {"chain_id": chain_id}
        message = f"Chain '{chain_id}' not found"
        
        super().__init__(
            error_code=ErrorCode.CHAIN_NOT_FOUND,
            message=message,
            details=details
        )


class ChainExecutionError(AgentToolkitException):
    """工具链执行错误"""
    
    def __init__(
        self, 
        message: str,
        chain_id: Optional[str] = None,
        failed_task: Optional[str] = None,
        original_error: Optional[str] = None
    ):
        details = {}
        if chain_id:
            details["chain_id"] = chain_id
        if failed_task:
            details["failed_task"] = failed_task
        if original_error:
            details["original_error"] = original_error
        
        super().__init__(
            error_code=ErrorCode.CHAIN_EXECUTION_FAILED,
            message=message,
            details=details
        )


class TimeoutError(AgentToolkitException):
    """超时错误"""
    
    def __init__(
        self, 
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None
    ):
        details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        
        super().__init__(
            error_code=ErrorCode.TOOL_TIMEOUT,
            message=message,
            details=details
        )


class UnauthorizedError(AgentToolkitException):
    """未授权错误"""
    
    def __init__(
        self, 
        message: str = "Unauthorized"
    ):
        super().__init__(
            error_code=ErrorCode.UNAUTHORIZED,
            message=message,
            details=None
        )


class ForbiddenError(AgentToolkitException):
    """禁止访问错误"""
    
    def __init__(
        self, 
        message: str = "Forbidden",
        action: Optional[str] = None,
        resource: Optional[str] = None
    ):
        details = {}
        if action:
            details["action"] = action
        if resource:
            details["resource"] = resource
        
        super().__init__(
            error_code=ErrorCode.FORBIDDEN,
            message=message,
            details=details if details else None
        )


def create_error_response(
    error_code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """创建错误响应字典"""
    return {
        "success": False,
        "error": {
            "error_code": error_code.value,
            "message": message,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    }


def wrap_exception(exception: Exception) -> AgentToolkitException:
    """包装标准异常为 AgentToolkitException"""
    if isinstance(exception, AgentToolkitException):
        return exception
    
    return AgentToolkitException(
        error_code=ErrorCode.INTERNAL_ERROR,
        message=str(exception),
        details={"exception_type": type(exception).__name__}
    )
