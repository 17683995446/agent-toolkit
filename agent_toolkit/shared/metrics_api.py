"""
Enhanced Metrics API for Agent Toolkit
Comprehensive metrics collection and API endpoints
"""

import time
import math
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
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._request_times: Dict[str, List[float]] = defaultdict(list)

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric"""
        logger.debug(f"📊 [METRICS] Counter increment: {name} += {value}")  # 日志1
        
        # Handle invalid values
        if math.isnan(value) or math.isinf(value):
            logger.debug(f"⚠️ [METRICS] Skipping invalid counter increment value: {value}")
            self._record_point(name, 0.0, MetricType.COUNTER, labels)
            logger.debug(f"✅ [METRICS] Metric point recorded for {name}")  # 日志3
            return
            
        # Handle current value being NaN/inf
        current = self._counters.get(name, 0.0)
        if math.isnan(current) or math.isinf(current):
            current = 0.0
            
        self._counters[name] = current + value
        logger.debug(f"✅ [METRICS] Counter updated: {name} = {self._counters[name]}")  # 日志2
        self._record_point(name, value, MetricType.COUNTER, labels)
        logger.debug(f"✅ [METRICS] Metric point recorded for {name}")  # 日志3

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric"""
        logger.debug(f"📊 [METRICS] Gauge set: {name} = {value}")  # 日志4
        
        # Handle invalid values
        if math.isnan(value) or math.isinf(value):
            logger.debug(f"⚠️ [METRICS] Skipping invalid gauge value: {value}")
            self._record_point(name, 0.0, MetricType.GAUGE, labels)
            logger.debug(f"✅ [METRICS] Metric point recorded for {name}")  # 日志6
            return
            
        self._gauges[name] = value
        logger.debug(f"✅ [METRICS] Gauge updated: {name} = {self._gauges[name]}")  # 日志5
        self._record_point(name, value, MetricType.GAUGE, labels)
        logger.debug(f"✅ [METRICS] Metric point recorded for {name}")  # 日志6

    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric"""
        logger.debug(f"📊 [METRICS] Histogram record: {name} = {value}")  # 日志7
        self._histograms[name].append(value)
        if len(self._histograms[name]) > 1000:
            logger.debug(f"⚠️ [METRICS] Histogram {name} exceeded 1000 points, trimming...")  # 日志8
            self._histograms[name] = self._histograms[name][-1000:]
        logger.debug(f"✅ [METRICS] Histogram recorded: {name} (total: {len(self._histograms[name])})")  # 日志9
        self._record_point(name, value, MetricType.HISTOGRAM, labels)
        logger.debug(f"✅ [METRICS] Metric point recorded for {name}")  # 日志10

    def record_request(self, endpoint: str, method: str, duration: float, status_code: int) -> None:
        """Record an API request"""
        logger.debug(f"📊 [METRICS] Request recorded: {method} {endpoint} - {status_code} in {duration*1000:.2f}ms")  # 日志11
        key = f"{method}:{endpoint}"
        self._request_counts[key] += 1
        self._request_times[key].append(duration)
        if len(self._request_times[key]) > 1000:
            logger.debug(f"⚠️ [METRICS] Request times for {key} exceeded 1000, trimming...")  # 日志12
            self._request_times[key] = self._request_times[key][-1000:]
        logger.debug(f"✅ [METRICS] Request count updated: {key} = {self._request_counts[key]}")  # 日志13

    def _record_point(self, name: str, value: float, type_: MetricType, labels: Optional[Dict[str, str]] = None) -> None:
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
            "histograms": dict(self._histograms),
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
        
        # Filter out invalid values for mean calculation
        valid_values = [v for v in values if v == v and v not in (float('inf'), float('-inf'))]
        if valid_values:
            mean_value = sum(valid_values) / len(valid_values)
        else:
            mean_value = 0.0
        
        return {
            "count": n,
            "min": values_sorted[0],
            "max": values_sorted[-1],
            "mean": mean_value,
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
    logger.info("📊 [METRICS_API] Fetching all metrics...")  # 日志14
    metrics = metrics_collector.get_all_metrics()
    logger.info(f"✅ [METRICS_API] Returned {len(metrics)} metric categories")  # 日志15
    return metrics


@router.get("/counters")
async def get_counters():
    """Get all counter metrics"""
    logger.info("📊 [METRICS_API] Fetching counters...")  # 日志16
    count = len(metrics_collector._counters)
    logger.info(f"✅ [METRICS_API] Returning {count} counters")  # 日志17
    return {"counters": dict(metrics_collector._counters)}


@router.get("/gauges")
async def get_gauges():
    """Get all gauge metrics"""
    logger.info("📊 [METRICS_API] Fetching gauges...")  # 日志18
    count = len(metrics_collector._gauges)
    logger.info(f"✅ [METRICS_API] Returning {count} gauges")  # 日志19
    return {"gauges": dict(metrics_collector._gauges)}


@router.get("/histograms/{name}")
async def get_histogram_stats(name: str):
    """Get statistics for a specific histogram"""
    logger.info(f"📊 [METRICS_API] Fetching histogram: {name}")  # 日志20
    stats = metrics_collector.get_histogram_stats(name)
    logger.info(f"✅ [METRICS_API] Returning stats for {name}")  # 日志21
    return {"name": name, "stats": stats}


@router.get("/history/{name}")
async def get_metric_history(name: str, limit: int = 100):
    """Get historical data for a metric"""
    logger.info(f"📊 [METRICS_API] Fetching history for: {name}, limit={limit}")  # 日志22
    history = metrics_collector.get_metric_history(name, limit)
    logger.info(f"✅ [METRICS_API] Returning {len(history)} history points")  # 日志23
    return {"name": name, "history": history}


@router.get("/dashboard")
async def get_dashboard_metrics():
    """Get comprehensive metrics for the dashboard."""
    logger.info("📊 [METRICS_API] Fetching dashboard metrics...")  # 日志24
    metrics = metrics_collector.get_all_metrics()
    
    # Calculate additional derived metrics
    total_requests = metrics.get("total_requests", 0)
    uptime = metrics.get("uptime", 1)
    
    # Get individual histogram stats
    request_duration_stats = metrics_collector.get_histogram_stats("request_duration")
    
    logger.info(f"✅ [METRICS_API] Dashboard metrics ready - {total_requests} total requests, {uptime:.1f}s uptime")  # 日志25
    
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
from pydantic import BaseModel, field_validator
import math

def validate_metric_value(v: float) -> float:
    """验证指标值，拒绝 inf 和 nan"""
    if not isinstance(v, (int, float)):
        raise ValueError("值必须是数字类型")
    if math.isnan(v):
        raise ValueError("值不能是 NaN")
    if math.isinf(v):
        raise ValueError("值不能是 infinity")
    return float(v)


class CounterIncrementRequest(BaseModel):
    name: str
    value: float = 1.0
    labels: Optional[Dict[str, str]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("名称不能为空")
        if len(v) > 1000:
            raise ValueError("名称不能超过1000个字符")
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v: float) -> float:
        return validate_metric_value(v)


class GaugeSetRequest(BaseModel):
    name: str
    value: float
    labels: Optional[Dict[str, str]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("名称不能为空")
        if len(v) > 1000:
            raise ValueError("名称不能超过1000个字符")
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v: float) -> float:
        return validate_metric_value(v)


class HistogramRecordRequest(BaseModel):
    name: str
    value: float
    labels: Optional[Dict[str, str]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("名称不能为空")
        if len(v) > 1000:
            raise ValueError("名称不能超过1000个字符")
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v: float) -> float:
        return validate_metric_value(v)


class SummaryRecordRequest(BaseModel):
    name: str
    value: float
    labels: Optional[Dict[str, str]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("名称不能为空")
        if len(v) > 1000:
            raise ValueError("名称不能超过1000个字符")
        return v
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v: float) -> float:
        return validate_metric_value(v)


@router.post("/counter")
async def increment_counter_endpoint(request: CounterIncrementRequest):
    """Increment a counter metric."""
    logger.info(f"📊 [METRICS_API] POST /counter - name={request.name}, value={request.value}")  # 日志26
    try:
        metrics_collector.increment_counter(request.name, request.value, request.labels)
        current_value = metrics_collector._counters.get(request.name, 0)
        logger.info(f"✅ [METRICS_API] Counter incremented - {request.name} = {current_value}")  # 日志27
        return {"success": True, "name": request.name, "value": current_value}
    except Exception as e:
        logger.error(f"❌ [METRICS_API] Counter increment failed: {str(e)}")  # 日志28
        raise


@router.post("/gauge")
async def set_gauge_endpoint(request: GaugeSetRequest):
    """Set a gauge metric."""
    logger.info(f"📊 [METRICS_API] POST /gauge - name={request.name}, value={request.value}")  # 日志29
    try:
        metrics_collector.set_gauge(request.name, request.value, request.labels)
        logger.info(f"✅ [METRICS_API] Gauge set - {request.name} = {request.value}")  # 日志30
        return {"success": True, "name": request.name, "value": request.value}
    except Exception as e:
        logger.error(f"❌ [METRICS_API] Gauge set failed: {str(e)}")  # 日志31
        raise


@router.post("/histogram")
async def record_histogram_endpoint(request: HistogramRecordRequest):
    """Record a histogram metric."""
    logger.info(f"📊 [METRICS_API] POST /histogram - name={request.name}, value={request.value}")  # 日志32
    try:
        metrics_collector.record_histogram(request.name, request.value, request.labels)
        logger.info(f"✅ [METRICS_API] Histogram recorded - {request.name} = {request.value}")  # 日志33
        return {"success": True, "name": request.name, "value": request.value}
    except Exception as e:
        logger.error(f"❌ [METRICS_API] Histogram record failed: {str(e)}")  # 日志34
        raise


@router.post("/summary")
async def record_summary_endpoint(request: SummaryRecordRequest):
    """Record a summary metric (alias for histogram)."""
    logger.info(f"📊 [METRICS_API] POST /summary - name={request.name}, value={request.value}")  # 日志35
    try:
        metrics_collector.record_histogram(request.name, request.value, request.labels)
        logger.info(f"✅ [METRICS_API] Summary recorded - {request.name} = {request.value}")  # 日志36
        return {"success": True, "name": request.name, "value": request.value}
    except Exception as e:
        logger.error(f"❌ [METRICS_API] Summary record failed: {str(e)}")  # 日志37
        raise


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
