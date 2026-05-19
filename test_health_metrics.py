"""
健康检查和Metrics API测试套件
测试健康检查系统和Metrics收集器的所有功能
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from agent_toolkit.main import create_app
from agent_toolkit.shared.health_check import (
    health_registry, HealthStatus, OverallHealth
)
from agent_toolkit.shared.metrics_api import metrics_collector


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


class TestHealthCheckAPI:
    """健康检查API测试"""
    
    def test_get_health_endpoint(self, client):
        """测试获取健康检查端点"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "total_checks" in data
        assert "passed_checks" in data
        assert "checks" in data
    
    def test_get_liveness_endpoint(self, client):
        """测试获取liveness端点"""
        response = client.get("/liveness")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
    
    def test_get_readiness_endpoint(self, client):
        """测试获取readiness端点"""
        response = client.get("/readiness")
        assert response.status_code in [200, 503]  # 可能健康或不健康
        data = response.json()
        assert "status" in data
    
    def test_get_health_history(self, client):
        """测试获取健康历史端点"""
        response = client.get("/api/v1/health/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "total_entries" in data


class TestMetricsAPI:
    """Metrics API测试"""
    
    def test_get_metrics_dashboard(self, client):
        """测试获取Metrics Dashboard端点"""
        response = client.get("/api/v1/metrics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "overview" in data
        assert "performance" in data
        assert "detailed_metrics" in data
        assert "timestamp" in data
    
    def test_increment_counter(self, client):
        """测试增加counter"""
        response = client.post(
            "/api/v1/metrics/counter",
            json={"name": "test_counter", "value": 1.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_set_gauge(self, client):
        """测试设置gauge"""
        response = client.post(
            "/api/v1/metrics/gauge",
            json={"name": "test_gauge", "value": 50.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_record_histogram(self, client):
        """测试记录histogram"""
        response = client.post(
            "/api/v1/metrics/histogram",
            json={"name": "test_histogram", "value": 25.5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_record_summary(self, client):
        """测试记录summary"""
        response = client.post(
            "/api/v1/metrics/summary",
            json={"name": "test_summary", "value": 100.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestHealthCheckRegistry:
    """健康检查注册中心测试"""
    
    @pytest.mark.asyncio
    async def test_register_check(self):
        """测试注册健康检查"""
        async def custom_check():
            return True, {"message": "Custom check passed"}
        
        health_registry.register_check("custom_test", custom_check)
        assert "custom_test" in health_registry._checks
    
    @pytest.mark.asyncio
    async def test_run_all_checks(self):
        """测试运行所有健康检查"""
        results = await health_registry.run_all_checks()
        assert isinstance(results, list)
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_get_overall_health(self):
        """测试获取整体健康状态"""
        overall = await health_registry.get_overall_health()
        assert isinstance(overall, OverallHealth)
        assert hasattr(overall, "status")


class TestMetricsCollector:
    """Metrics收集器测试"""
    
    def test_counter_operations(self):
        """测试Counter操作"""
        metrics_collector.increment_counter("test_counter_ops", 5.0)
        metrics_collector.increment_counter("test_counter_ops", 3.0)
        assert metrics_collector._counters["test_counter_ops"] == 8.0
    
    def test_gauge_operations(self):
        """测试Gauge操作"""
        metrics_collector.set_gauge("test_gauge_ops", 100.0)
        metrics_collector.set_gauge("test_gauge_ops", 150.0)
        assert metrics_collector._gauges["test_gauge_ops"] == 150.0
    
    def test_histogram_operations(self):
        """测试Histogram操作"""
        metrics_collector.record_histogram("test_histogram_ops", 10.0)
        metrics_collector.record_histogram("test_histogram_ops", 20.0)
        assert len(metrics_collector._histograms["test_histogram_ops"]) == 2
    
    def test_get_all_metrics(self):
        """测试获取所有指标"""
        all_metrics = metrics_collector.get_all_metrics()
        assert "uptime" in all_metrics
        assert "total_requests" in all_metrics
        assert "counters" in all_metrics
        assert "gauges" in all_metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
