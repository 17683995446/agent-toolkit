"""
Enhanced Metrics API for Agent Toolkit
Comprehensive metrics collection and API endpoints
"""

import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict
from fastapi import APIRouter

from agent_toolkit.shared.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricPoint:
    timestamp: float
    value: float
    labels: Dict[str, str]


class MetricsCollector:
    """Enhanced metrics collector with support for various metric types"""

    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._metric_points: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._start_time = time.time()
        self._request_counts = defaultdict(int)
        self._request_times = defaultdict(list)

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        self._counters[name] += value
        self._record_point(name, value, MetricType.COUNTER, labels)

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        self._gauges[name] = value
        self._record_point(name, value, MetricType.GAUGE, labels)

    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram metric"""
        self._histograms[name].append(value)
        if len(self._histograms[name]) > 1000:
            self._histograms[name] = self._histograms[name][-1000:]
        self._record_point(name, value, MetricType.HISTOGRAM, labels)

    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record an API request"""
        key = f"{method}:{endpoint}"
        self._request_counts[key] += 1
        self._request_times[key].append(duration)
        if len(self._request_times[key]) > 1000:
            self._request_times[key] = self._request_times[key][-1000:]

    def _record_point(self, name: str, value: float, type_: MetricType, labels: Optional[Dict[str, str]] = None):
        """Record a metric point with timestamp"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        self._metric_points[name].append(point)
        if len(self._metric_points[name]) > 1000:
            self._metric_points[name] = self._metric_points[name][-1000:]

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics in dashboard-friendly format"""
        uptime = time.time() - self._start_time
        
        # Request statistics
        total_requests = sum(self._request_counts.values())
        
        request_stats = {}
        for key, count in self._request_counts.items():
            method, endpoint = key.split(":", 1)
            times = self._request_times.get(key, [])
            avg_time = sum(times) / len(times) if times else 0
            request_stats[endpoint] = {
                "method": method,
                "count": count,
                "avg_time_ms": avg_time * 1000
            }
        
        return {
            "uptime": uptime,
            "uptime_formatted": format_uptime(uptime),
            "total_requests": total_requests,
            "requests_per_second": total_requests / uptime if uptime > 0 else 0,
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "request_stats": request_stats,
            "timestamp": datetime.now().isoformat()
        }

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a histogram"""
        values = self._histograms.get(name, [])
        if not values:
            return {}
        
        values_sorted = sorted(values)
        n = len(values_sorted)
        
        return {
            "count": n,
            "min": values_sorted[0],
            "max": values_sorted[-1],
            "mean": sum(values_sorted) / n,
            "p50": values_sorted[int(n * 0.5)],
            "p95": values_sorted[int(n * 0.95)] if n > 20 else values_sorted[-1],
            "p99": values_sorted[int(n * 0.99)] if n > 100 else values_sorted[-1]
        }

    def get_metric_history(self, name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical metric points"""
        points = self._metric_points.get(name, [])[-limit:]
        return [
            {
                "timestamp": point.timestamp,
                "value": point.value,
                "labels": point.labels
            }
            for point in points
        ]


metrics_collector = MetricsCollector()


def format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    
    return " ".join(parts)


@router.get("")
async def get_all_metrics():
    """Get all metrics in dashboard format"""
    metrics = metrics_collector.get_all_metrics()
    return metrics


@router.get("/counters")
async def get_counters():
    """Get all counter metrics"""
    return {"counters": dict(metrics_collector._counters)}


@router.get("/gauges")
async def get_gauges():
    """Get all gauge metrics"""
    return {"gauges": dict(metrics_collector._gauges)}


@router.get("/histograms/{name}")
async def get_histogram_stats(name: str):
    """Get statistics for a specific histogram"""
    return {"name": name, "stats": metrics_collector.get_histogram_stats(name)}


@router.get("/history/{name}")
async def get_metric_history(name: str, limit: int = 100):
    """Get historical data for a metric"""
    return {"name": name, "history": metrics_collector.get_metric_history(name, limit)}


@router.get("/dashboard")
async def get_dashboard_metrics():
    """Get comprehensive metrics for the dashboard."""
    metrics = metrics_collector.get_all_metrics()
    
    # Calculate additional derived metrics
    total_requests = metrics.get("total_requests", 0)
    uptime = metrics.get("uptime", 1)
    
    # Get individual histogram stats
    request_duration_stats = metrics_collector.get_histogram_stats("request_duration")
    
    return {
        "overview": {
            "uptime": format_uptime(uptime),
            "total_requests": total_requests,
            "requests_per_second": round(total_requests / uptime, 2) if uptime > 0 else 0,
            "status": "healthy"
        },
        "performance": {
            "p50_latency_ms": round(request_duration_stats.get("p50", 0) * 1000, 2),
            "p95_latency_ms": round(request_duration_stats.get("p95", 0) * 1000, 2),
            "p99_latency_ms": round(request_duration_stats.get("p99", 0) * 1000, 2)
        },
        "detailed_metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }


# Metric management endpoints
from pydantic import BaseModel

class CounterIncrementRequest(BaseModel):
    name: str
    value: float = 1.0
    labels: Optional[Dict[str, str]] = None


class GaugeSetRequest(BaseModel):
    name: str
    value: float
    labels: Optional[Dict[str, str]] = None


class HistogramRecordRequest(BaseModel):
    name: str
    value: float
    labels: Optional[Dict[str, str]] = None


class SummaryRecordRequest(BaseModel):
    name: str
    value: float
    labels: Optional[Dict[str, str]] = None


@router.post("/counter")
async def increment_counter_endpoint(request: CounterIncrementRequest):
    """Increment a counter metric."""
    metrics_collector.increment_counter(request.name, request.value, request.labels)
    return {"success": True, "name": request.name, "value": metrics_collector._counters.get(request.name, 0)}


@router.post("/gauge")
async def set_gauge_endpoint(request: GaugeSetRequest):
    """Set a gauge metric."""
    metrics_collector.set_gauge(request.name, request.value, request.labels)
    return {"success": True, "name": request.name, "value": request.value}


@router.post("/histogram")
async def record_histogram_endpoint(request: HistogramRecordRequest):
    """Record a histogram metric."""
    metrics_collector.record_histogram(request.name, request.value, request.labels)
    return {"success": True, "name": request.name, "value": request.value}


@router.post("/summary")
async def record_summary_endpoint(request: SummaryRecordRequest):
    """Record a summary metric (alias for histogram)."""
    metrics_collector.record_histogram(request.name, request.value, request.labels)
    return {"success": True, "name": request.name, "value": request.value}


@router.post("/event/request")
async def record_request_event(
    endpoint: str,
    method: str,
    duration_seconds: float,
    status_code: int
):
    """Record a request event (for testing/development)."""
    metrics_collector.record_request(endpoint, method, duration_seconds, status_code)
    return {"status": "recorded"}


# Initialize some basic metrics
metrics_collector.increment_counter("system_startups", 1)
metrics_collector.set_gauge("active_connections", 0)
metrics_collector.set_gauge("cpu_usage", 0)
metrics_collector.set_gauge("memory_usage", 0)

print("🚀 Enhanced Metrics System Loaded")
