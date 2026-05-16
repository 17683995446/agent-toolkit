"""
统一的 API 响应格式和错误处理
提供一致的 API 响应结构和错误码定义
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    """错误码枚举"""
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    DUPLICATE_ERROR = "DUPLICATE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    
    # 认证错误 (2000-2999)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    
    # 工具仓库错误 (3000-3999)
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_ALREADY_EXISTS = "TOOL_ALREADY_EXISTS"
    TOOL_VERSION_NOT_FOUND = "TOOL_VERSION_NOT_FOUND"
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"
    
    # 适配器错误 (4000-4999)
    ADAPTER_NOT_FOUND = "ADAPTER_NOT_FOUND"
    ADAPTER_EXECUTION_FAILED = "ADAPTER_EXECUTION_FAILED"
    ADAPTER_TIMEOUT = "ADAPTER_TIMEOUT"
    ADAPTER_HEALTH_CHECK_FAILED = "ADAPTER_HEALTH_CHECK_FAILED"
    
    # 运行时错误 (5000-5999)
    EXECUTION_NOT_FOUND = "EXECUTION_NOT_FOUND"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EXECUTION_CANCELLED = "EXECUTION_CANCELLED"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    
    # 编排器错误 (6000-6999)
    TOOLCHAIN_NOT_FOUND = "TOOLCHAIN_NOT_FOUND"
    CHAIN_EXECUTION_FAILED = "CHAIN_EXECUTION_FAILED"
    CIRCULAR_DEPENDENCY = "CIRCULAR_DEPENDENCY"
    INVALID_DEPENDENCY = "INVALID_DEPENDENCY"


@dataclass
class ErrorDetail:
    """错误详情"""
    error_code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "error_type": self.error_code.value,
            "message": self.message,
            "error_code": self.error_code.name,
            "timestamp": self.timestamp,
        }
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class APIResponse(Generic[TypeVar("T")]):
    """统一 API 响应格式"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[ErrorDetail] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "success": self.success,
            "timestamp": self.timestamp,
        }
        
        if self.data is not None:
            result["data"] = self.data
        
        if self.message:
            result["message"] = self.message
        
        if self.error:
            result["error"] = self.error.to_dict()
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    @classmethod
    def success_response(
        cls,
        data: Any = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "APIResponse":
        """创建成功响应"""
        return cls(
            success=True,
            data=data,
            message=message,
            metadata=metadata
        )
    
    @classmethod
    def success(
        cls,
        data: Any = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "APIResponse":
        """创建成功响应（便捷方法）"""
        return cls.success_response(data, message, metadata)
    
    @classmethod
    def error_response(
        cls,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> "APIResponse":
        """创建错误响应"""
        return cls(
            success=False,
            error=ErrorDetail(
                error_code=error_code,
                message=message,
                details=details
            )
        )
    
    @classmethod
    def error_response_quick(
        cls,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ) -> "APIResponse":
        """创建错误响应（便捷方法）"""
        return cls.error_response(error_code, message, details)


class APIException(HTTPException):
    """统一的 API 异常"""
    
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.error_detail = ErrorDetail(
            error_code=error_code,
            message=message,
            details=details
        )
        super().__init__(
            status_code=status_code,
            detail=self.error_detail.to_dict()
        )


class NotFoundException(APIException):
    """资源未找到异常"""
    
    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.NOT_FOUND,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            message=message,
            details=details
        )


class ValidationException(APIException):
    """数据验证异常"""
    
    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details
        )


class UnauthorizedException(APIException):
    """未授权异常"""
    
    def __init__(
        self,
        message: str = "Unauthorized",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            message=message,
            details=details
        )


class ForbiddenException(APIException):
    """禁止访问异常"""
    
    def __init__(
        self,
        message: str = "Forbidden",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=ErrorCode.FORBIDDEN,
            message=message,
            details=details
        )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """API 异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.error_detail.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP 异常处理器"""
    error_code = ErrorCode.UNKNOWN_ERROR
    
    if exc.status_code == 404:
        error_code = ErrorCode.NOT_FOUND
    elif exc.status_code == 422:
        error_code = ErrorCode.VALIDATION_ERROR
    elif exc.status_code == 401:
        error_code = ErrorCode.UNAUTHORIZED
    elif exc.status_code == 403:
        error_code = ErrorCode.FORBIDDEN
    elif exc.status_code >= 500:
        error_code = ErrorCode.INTERNAL_ERROR
    
    error_detail = ErrorDetail(
        error_code=error_code,
        message=str(exc.detail) if isinstance(exc.detail, str) else "Unknown error",
        details={"status_code": exc.status_code}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": error_detail.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    error_detail = ErrorDetail(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="An internal error occurred",
        details={"exception_type": type(exc).__name__}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": error_detail.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def register_exception_handlers(app):
    """注册异常处理器到 FastAPI 应用"""
    from fastapi import FastAPI
    
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
