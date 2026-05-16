"""
性能监控和性能指标收集
提供应用级别的性能监控功能
"""

import time
import functools
from typing import Any, Callable, Dict, Optional
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from agent_toolkit.shared.structured_logging import get_logger


logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    errors: int = 0
    
    def record(self, duration: float, error: bool = False):
        """记录性能指标"""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.count
        if error:
            self.errors += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "count": self.count,
            "total_time_ms": self.total_time * 1000,
            "min_time_ms": self.min_time * 1000 if self.min_time != float('inf') else 0,
            "max_time_ms": self.max_time * 1000,
            "avg_time_ms": self.avg_time * 1000,
            "errors": self.errors,
            "error_rate": self.errors / self.count if self.count > 0 else 0
        }


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self._metrics: Dict[str, PerformanceMetric] = {}
        self._start_times: Dict[str, float] = {}
    
    def record(self, name: str, duration: float, error: bool = False):
        """记录性能指标"""
        if name not in self._metrics:
            self._metrics[name] = PerformanceMetric(name=name)
        self._metrics[name].record(duration, error)
    
    def start_timer(self, name: str):
        """启动计时器"""
        self._start_times[name] = time.time()
    
    def stop_timer(self, name: str, error: bool = False):
        """停止计时器并记录"""
        if name in self._start_times:
            duration = time.time() - self._start_times[name]
            self.record(name, duration, error)
            del self._start_times[name]
    
    def get_metric(self, name: str) -> Optional[PerformanceMetric]:
        """获取指标"""
        return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有指标"""
        return {name: metric.to_dict() for name, metric in self._metrics.items()}
    
    def reset(self):
        """重置所有指标"""
        self._metrics.clear()
        self._start_times.clear()


# 全局性能监控器实例
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


@contextmanager
def track_performance(name: str, error: bool = False):
    """上下文管理器，用于跟踪代码块性能"""
    start_time = time.time()
    error_occurred = error
    
    try:
        yield
    except Exception as e:
        error_occurred = True
        raise
    finally:
        duration = time.time() - start_time
        monitor = get_performance_monitor()
        monitor.record(name, duration, error_occurred)
        
        # 记录慢操作日志
        if duration > 1.0:  # 超过1秒的操作
            logger.warning(
                "slow_operation_detected",
                operation=name,
                duration_ms=duration * 1000,
                threshold_ms=1000
            )


def monitor_performance(name: Optional[str] = None):
    """装饰器，用于监控函数性能"""
    def decorator(func: Callable) -> Callable:
        operation_name = name or f"{func.__module__}.{func.__qualname__}"
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            error_occurred = False
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_occurred = True
                raise
            finally:
                duration = time.time() - start_time
                monitor = get_performance_monitor()
                monitor.record(operation_name, duration, error_occurred)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_occurred = False
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error_occurred = True
                raise
            finally:
                duration = time.time() - start_time
                monitor = get_performance_monitor()
                monitor.record(operation_name, duration, error_occurred)
        
        # 返回适当的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 导入 asyncio 用于检查协程函数
import asyncio


class PerformanceMiddleware:
    """性能监控中间件"""
    
    def __init__(self, app):
        self.app = app
        self.monitor = get_performance_monitor()
    
    async def __call__(self, scope, receive, send):
        """中间件调用"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # 获取请求路径
        path = scope.get("path", "")
        method = scope.get("method", "")
        operation_name = f"http.{method.lower()}.{path}"
        
        error_occurred = False
        start_time = time.time()
        
        # 定义发送函数
        async def send_wrapper(message):
            nonlocal error_occurred
            
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                if status_code >= 400:
                    error_occurred = True
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            error_occurred = True
            raise
        finally:
            duration = time.time() - start_time
            self.monitor.record(operation_name, duration, error_occurred)


def get_performance_report() -> Dict[str, Any]:
    """获取性能报告"""
    monitor = get_performance_monitor()
    metrics = monitor.get_all_metrics()
    
    # 按平均时间排序
    sorted_metrics = sorted(
        metrics.items(),
        key=lambda x: x[1]["avg_time_ms"],
        reverse=True
    )
    
    # 计算总体统计
    total_requests = sum(m["count"] for m in metrics.values())
    total_errors = sum(m["errors"] for m in metrics.values())
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_operations": total_requests,
            "total_errors": total_errors,
            "overall_error_rate": total_errors / total_requests if total_requests > 0 else 0
        },
        "top_slow_operations": sorted_metrics[:10],
        "all_metrics": metrics
    }
