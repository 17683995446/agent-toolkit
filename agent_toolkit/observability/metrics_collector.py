"""Metrics collection using Prometheus."""

import time
from typing import Any, Dict, Optional
from functools import wraps

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    REGISTRY,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from agent_toolkit.shared.structured_logging import LoggerMixin


class MetricsCollector(LoggerMixin):
    """Collector for application metrics."""

    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._initialize_metrics()

    def _initialize_metrics(self) -> None:
        """Initialize all application metrics."""
        self.tool_execution_total = Counter(
            "agent_toolkit_tool_execution_total",
            "Total number of tool executions",
            ["tool_name", "status"]
        )

        self.tool_execution_duration_seconds = Histogram(
            "agent_toolkit_tool_execution_duration_seconds",
            "Tool execution duration in seconds",
            ["tool_name"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
        )

        self.active_executions = Gauge(
            "agent_toolkit_active_executions",
            "Number of currently active executions"
        )

        self.chain_execution_total = Counter(
            "agent_toolkit_chain_execution_total",
            "Total number of chain executions",
            ["chain_id", "status"]
        )

        self.chain_execution_duration_seconds = Histogram(
            "agent_toolkit_chain_execution_duration_seconds",
            "Chain execution duration in seconds",
            ["chain_id"],
            buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
        )

        self.adapter_requests_total = Counter(
            "agent_toolkit_adapter_requests_total",
            "Total number of adapter requests",
            ["adapter_type", "status"]
        )

        self.adapter_request_duration_seconds = Histogram(
            "agent_toolkit_adapter_request_duration_seconds",
            "Adapter request duration in seconds",
            ["adapter_type"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )

        self.resource_usage = Gauge(
            "agent_toolkit_resource_usage",
            "Current resource usage",
            ["resource_type"]
        )

        self.queue_size = Gauge(
            "agent_toolkit_queue_size",
            "Size of execution queue",
            ["queue_name"]
        )

        self.service_info = Info(
            "agent_toolkit_service_info",
            "Service information"
        )

        self.service_info.info({
            "version": "0.1.0",
            "service_name": "agent-toolkit"
        })

    def record_execution(
        self,
        tool_name: str,
        status: str,
        duration_ms: float
    ) -> None:
        """Record a tool execution."""
        self.tool_execution_total.labels(
            tool_name=tool_name,
            status=status
        ).inc()

        self.tool_execution_duration_seconds.labels(
            tool_name=tool_name
        ).observe(duration_ms / 1000)

        self.logger.debug(
            "execution_recorded",
            tool_name=tool_name,
            status=status,
            duration_ms=duration_ms
        )

    def record_chain_execution(
        self,
        chain_id: str,
        status: str,
        duration_ms: float
    ) -> None:
        """Record a chain execution."""
        self.chain_execution_total.labels(
            chain_id=chain_id,
            status=status
        ).inc()

        self.chain_execution_duration_seconds.labels(
            chain_id=chain_id
        ).observe(duration_ms / 1000)

    def record_adapter_request(
        self,
        adapter_type: str,
        status: str,
        duration_ms: float
    ) -> None:
        """Record an adapter request."""
        self.adapter_requests_total.labels(
            adapter_type=adapter_type,
            status=status
        ).inc()

        self.adapter_request_duration_seconds.labels(
            adapter_type=adapter_type
        ).observe(duration_ms / 1000)

    def update_active_executions(self, count: int) -> None:
        """Update the number of active executions."""
        self.active_executions.set(count)

    def update_resource_usage(self, resource_type: str, value: float) -> None:
        """Update resource usage metric."""
        self.resource_usage.labels(resource_type=resource_type).set(value)

    def update_queue_size(self, queue_name: str, size: int) -> None:
        """Update queue size metric."""
        self.queue_size.labels(queue_name=queue_name).set(size)

    def get_metrics(self, as_string: bool = False) -> bytes | str:
        """Get all metrics in Prometheus format."""
        result = generate_latest(REGISTRY)
        if as_string:
            return result.decode('utf-8')
        return result

    def get_content_type(self) -> str:
        """Get content type for metrics response."""
        return CONTENT_TYPE_LATEST

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metric values."""
        metrics = {}
        for metric_name, metric in self._metrics.items():
            try:
                samples = metric.collect()
                if samples:
                    metrics[metric_name] = {
                        "samples": [
                            {"labels": dict(sample.labels), "value": sample.value}
                            for sample in samples[0].samples
                        ]
                    }
            except Exception:
                pass
        return metrics


_global_collector: Optional[MetricsCollector] = None


def metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def record_metric(metric_name: str, **kwargs):
    """Decorator to record metrics for a function."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            collector = metrics_collector()
            
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                collector.record_execution(metric_name, status, duration_ms)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            collector = metrics_collector()
            
            try:
                result = func(*args, **kwargs)
                status = "success"
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                collector.record_execution(metric_name, status, duration_ms)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


# Import asyncio
import asyncio
