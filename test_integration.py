"""
集成测试套件
测试整个系统的集成功能
"""

import pytest
import time
from fastapi.testclient import TestClient
from agent_toolkit.main import create_app


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


class TestSystemIntegration:
    """系统集成测试"""
    
    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
    
    def test_full_workflow(self, client):
        """测试完整工作流：健康检查 -> 指标 -> 指标管理"""
        
        # 1. 检查liveness
        liveness = client.get("/liveness")
        assert liveness.status_code == 200
        
        # 2. 检查readiness
        readiness = client.get("/readiness")
        assert readiness.status_code == 200
        
        # 3. 检查完整健康
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        
        # 4. 检查dashboard指标
        dashboard = client.get("/api/v1/metrics/dashboard")
        assert dashboard.status_code == 200
        
        # 5. 记录一些指标
        counter = client.post(
            "/api/v1/metrics/counter",
            json={"name": "integration_test_counter", "value": 5.0}
        )
        assert counter.status_code == 200
        
        gauge = client.post(
            "/api/v1/metrics/gauge",
            json={"name": "integration_test_gauge", "value": 42.0}
        )
        assert gauge.status_code == 200
        
        histogram = client.post(
            "/api/v1/metrics/histogram",
            json={"name": "integration_test_histogram", "value": 123.45}
        )
        assert histogram.status_code == 200
        
        # 6. 再次检查指标
        updated_dashboard = client.get("/api/v1/metrics/dashboard")
        assert updated_dashboard.status_code == 200
        dashboard_data = updated_dashboard.json()
        assert "detailed_metrics" in dashboard_data
        assert "counters" in dashboard_data["detailed_metrics"]
    
    def test_multiple_requests(self, client):
        """测试多个请求，检查指标更新"""
        # 发送多个请求
        for _ in range(5):
            response = client.get("/api/v1/health")
            assert response.status_code == 200
        
        # 检查指标是否被记录
        dashboard = client.get("/api/v1/metrics/dashboard")
        assert dashboard.status_code == 200
        data = dashboard.json()
        # 至少应该有一些请求被记录
        assert "total_requests" in data["detailed_metrics"]
    
    def test_health_history(self, client):
        """测试健康检查历史记录"""
        # 触发多次健康检查以填充历史
        for _ in range(3):
            client.get("/api/v1/health")
        
        history = client.get("/api/v1/health/history")
        assert history.status_code == 200
        data = history.json()
        assert "history" in data
        assert "total_entries" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
