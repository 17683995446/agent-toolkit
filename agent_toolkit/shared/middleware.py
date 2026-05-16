"""
FastAPI 中间件和实用工具
"""

import time
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram

from agent_toolkit.shared.structured_logging import get_logger
from agent_toolkit.shared.custom_exceptions import AgentToolkitException

logger = get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'agent_toolkit_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code']
)
REQUEST_DURATION = Histogram(
    'agent_toolkit_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus 指标收集中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        status_code = status.HTTP_200_OK
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            raise
        finally:
            duration = time.time() - start_time
            endpoint = request.url.path
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        
        logger.info(
            "request_started",
            method=request.method,
            path=path,
            client_host=request.client.host if request.client else None
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            logger.info(
                "request_completed",
                method=request.method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2)
            )
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "request_failed",
                method=request.method,
                path=path,
                error=str(e),
                duration_ms=round(duration * 1000, 2)
            )
            raise


def setup_middlewares(app: FastAPI) -> None:
    """为 FastAPI 应用设置所有中间件"""
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware)
