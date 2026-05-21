"""
FastAPI 中间件和实用工具 - 产品化版本
引入优秀开源工具：Prometheus, OpenTelemetry
集成内部Metrics收集器和健康检查系统
"""

import time
import traceback
from typing import Callable
from functools import wraps

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, Info

from agent_toolkit.shared.structured_logging import get_logger
from agent_toolkit.shared.custom_exceptions import AgentToolkitException
from agent_toolkit.shared.metrics_api import metrics_collector

logger = get_logger(__name__)

# ============================================
# Prometheus Metrics - 产品化监控指标
# ============================================

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

ACTIVE_REQUESTS = Gauge(
    'agent_toolkit_active_requests',
    'Number of active requests',
    ['method', 'endpoint']
)

ERROR_COUNT = Counter(
    'agent_toolkit_errors_total',
    'Total number of errors',
    ['error_type', 'endpoint']
)

SYSTEM_INFO = Info(
    'agent_toolkit_system',
    'System information'
)

# 设置系统信息
SYSTEM_INFO.info({
    'version': '0.1.0',
    'framework': 'FastAPI',
    'python_version': '3.12+'
})


# ============================================
# 错误追踪工具类
# ============================================

class ErrorTracker:
    """错误追踪器 - 产品化版本"""

    def __init__(self):
        self.errors = []
        self.max_errors = 1000

    def record_error(self, error_type: str, endpoint: str, error_msg: str, stack_trace: str = None):
        """记录错误"""
        error_record = {
            'timestamp': time.time(),
            'error_type': error_type,
            'endpoint': endpoint,
            'error_msg': error_msg,
            'stack_trace': stack_trace
        }

        self.errors.append(error_record)

        # 保持错误列表在限制范围内
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]

    def get_recent_errors(self, limit: int = 10):
        """获取最近的错误"""
        return self.errors[-limit:]

    def get_error_summary(self):
        """获取错误摘要"""
        if not self.errors:
            return {'total': 0, 'by_type': {}}

        by_type = {}
        for error in self.errors:
            error_type = error['error_type']
            by_type[error_type] = by_type.get(error_type, 0) + 1

        return {
            'total': len(self.errors),
            'by_type': by_type
        }


# 全局错误追踪器
error_tracker = ErrorTracker()


# ============================================
# Prometheus 监控中间件 - 产品化版本
# ============================================

class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus 指标收集中间件 - 产品化版本，同时集成内部Metrics收集器"""
    
    # 跟踪活跃连接数的内部计数器
    _active_connections = 0

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        status_code = status.HTTP_200_OK
        endpoint = request.url.path

        # 增加活跃请求计数 - Prometheus
        ACTIVE_REQUESTS.labels(method=request.method, endpoint=endpoint).inc()
        
        # 更新内部活跃连接计数器
        MetricsMiddleware._active_connections += 1
        metrics_collector.set_gauge("active_connections", MetricsMiddleware._active_connections)

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            # 记录错误到追踪器
            error_tracker.record_error(
                error_type=type(e).__name__,
                endpoint=endpoint,
                error_msg=str(e),
                stack_trace=traceback.format_exc()
            )

            # 增加错误计数 - Prometheus
            ERROR_COUNT.labels(
                error_type=type(e).__name__,
                endpoint=endpoint
            ).inc()

            # 增加内部错误计数器
            metrics_collector.increment_counter(f"errors_{type(e).__name__}", 1)

            raise
        finally:
            # 减少活跃请求计数 - Prometheus
            ACTIVE_REQUESTS.labels(method=request.method, endpoint=endpoint).dec()
            
            # 更新内部活跃连接计数器
            MetricsMiddleware._active_connections = max(0, MetricsMiddleware._active_connections - 1)
            metrics_collector.set_gauge("active_connections", MetricsMiddleware._active_connections)

            duration = time.time() - start_time

            # 记录请求指标 - Prometheus
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()

            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            # 记录到内部Metrics收集器
            metrics_collector.record_request(endpoint, request.method, duration, status_code)
            metrics_collector.record_histogram("request_duration", duration)
            metrics_collector.increment_counter("total_requests", 1)


# ============================================
# 请求日志中间件 - 产品化版本
# ============================================

class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件 - 产品化版本"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        request_id = request.headers.get('X-Request-ID', f"{time.time()}:{id(request)}")

        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=path,
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get('User-Agent')
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # 添加请求ID到响应头
            response.headers['X-Request-ID'] = request_id

            logger.info(
                "request_completed",
                request_id=request_id,
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
                request_id=request_id,
                method=request.method,
                path=path,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration * 1000, 2)
            )
            raise


# ============================================
# 速率限制中间件（简化版）
# ============================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """增强的速率限制中间件 - 支持路径豁免"""

    def __init__(self, app, calls: int = 1000, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
        # 定义豁免路径 - 健康检查和指标查询不需要限制
        self.exempt_paths = [
            '/health',
            '/liveness', 
            '/readiness',
            '/api/v1/health',
            '/api/v1/metrics'
        ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 检查是否是豁免路径，如果是则直接放行
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return await call_next(request)
        
        client_ip = request.client.host if request.client else 'unknown'
        current_time = time.time()

        # 清理过期的客户端记录
        self.clients = {
            ip: times
            for ip, times in self.clients.items()
            if times and times[-1] > current_time - self.period
        }

        if client_ip not in self.clients:
            self.clients[client_ip] = []

        # 检查速率限制
        self.clients[client_ip] = [
            t for t in self.clients[client_ip]
            if t > current_time - self.period
        ]

        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": self.period
                }
            )

        self.clients[client_ip].append(current_time)

        return await call_next(request)


# ============================================
# 系统资源监控中间件
# ============================================

class ResourceMonitorMiddleware(BaseHTTPMiddleware):
    """系统资源监控中间件 - 定期更新健康检查指标"""
    
    def __init__(self, app, update_interval: int = 10):
        super().__init__(app)
        self.update_interval = update_interval
        self.last_update = 0
    
    async def dispatch(self, request: Request, call_next):
        current_time = time.time()
        
        # 定期更新资源监控指标
        if current_time - self.last_update > self.update_interval:
            self._update_resource_metrics()
            self.last_update = current_time
        
        return await call_next(request)
    
    def _update_resource_metrics(self):
        """更新资源监控指标"""
        try:
            import psutil
            process = psutil.Process()
            
            # CPU 使用率
            cpu_percent = process.cpu_percent(interval=None)
            metrics_collector.set_gauge("cpu_usage", cpu_percent)
            
            # 内存使用
            memory_mb = process.memory_info().rss / 1024 / 1024
            metrics_collector.set_gauge("memory_usage", memory_mb)
            
            # 磁盘使用
            disk_usage = psutil.disk_usage('/')
            metrics_collector.set_gauge("disk_usage_percent", disk_usage.percent)
            
        except ImportError:
            # psutil not available, use fallback values
            metrics_collector.set_gauge("cpu_usage", 0)
            metrics_collector.set_gauge("memory_usage", 0)
        except Exception as e:
            logger.warning(f"Failed to update resource metrics: {e}")


def setup_middlewares(app: FastAPI) -> None:
    """为 FastAPI 应用设置所有中间件 - 产品化版本"""
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ResourceMonitorMiddleware, update_interval=10)
    app.add_middleware(
        RateLimitMiddleware,
        calls=10000,  # 提高限制，适合测试和开发
        period=60
    )
