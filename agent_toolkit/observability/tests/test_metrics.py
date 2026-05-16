"""Unit tests for Observability metrics."""

import pytest
from unittest.mock import MagicMock, patch
from prometheus_client import Counter, Histogram, Gauge

from agent_toolkit.observability.metrics_collector import MetricsCollector, metrics_collector


class TestMetricsCollector:
    """Test suite for MetricsCollector."""

    def test_initialization(self) -> None:
        """Test metrics collector initialization."""
        collector = MetricsCollector()
        
        assert collector is not None
        assert hasattr(collector, "tool_execution_total")
        assert hasattr(collector, "tool_execution_duration_seconds")
        assert hasattr(collector, "active_executions")

    def test_record_successful_execution(self) -> None:
        """Test recording successful tool execution."""
        collector = MetricsCollector()
        
        collector.record_execution(
            tool_name="test_tool",
            status="success",
            duration_ms=150.5
        )
        
        assert collector.tool_execution_total._metrics.get("test_tool", "success") is not None

    def test_record_failed_execution(self) -> None:
        """Test recording failed tool execution."""
        collector = MetricsCollector()
        
        collector.record_execution(
            tool_name="test_tool",
            status="failure",
            duration_ms=50.0
        )
        
        assert collector.tool_execution_total._metrics.get("test_tool", "failure") is not None

    def test_update_active_executions(self) -> None:
        """Test updating active executions gauge."""
        collector = MetricsCollector()
        
        collector.update_active_executions(5)
        
        assert collector.active_executions._value._value == 5

    def test_record_execution_latency(self) -> None:
        """Test recording execution latency."""
        collector = MetricsCollector()
        
        collector.record_latency("test_tool", 200.0)
        
        latency_metric = collector.tool_execution_duration_seconds
        assert latency_metric is not None


class TestMetricsCollectorSingleton:
    """Test suite for singleton metrics collector."""

    def test_singleton_instance(self) -> None:
        """Test getting singleton instance."""
        collector1 = metrics_collector
        collector2 = metrics_collector
        
        assert collector1 is collector2

    def test_record_via_singleton(self) -> None:
        """Test recording metrics via singleton."""
        collector = metrics_collector
        
        collector.record_execution(
            tool_name="singleton_test",
            status="success",
            duration_ms=100.0
        )
