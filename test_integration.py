#!/usr/bin/env python3
"""
Agent Toolkit 集成测试
测试各模块之间的集成和协作
"""

import sys
import os
import asyncio
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from httpx import AsyncClient
from agent_toolkit.main import create_app
from agent_toolkit.shared.application_settings import Settings


class TestApplicationIntegration:
    """应用集成测试"""
    
    @pytest.fixture
    async def app_client(self):
        """创建测试客户端"""
        app = create_app(Settings())
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, app_client):
        """测试健康检查端点"""
        response = await app_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, app_client):
        """测试根路径"""
        response = await app_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Agent Toolkit"
        assert data["version"] == "0.1.0"
    
    @pytest.mark.asyncio
    async def test_openapi_docs(self, app_client):
        """测试 API 文档"""
        response = await app_client.get("/docs")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_openapi_json(self, app_client):
        """测试 OpenAPI JSON"""
        response = await app_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestAdapterIntegration:
    """适配器集成测试"""
    
    @pytest.mark.asyncio
    async def test_adapter_types_endpoint(self):
        """测试适配器类型端点"""
        from agent_toolkit.adapter.adapter_api_routes import router
        
        # 测试路由是否正确配置
        assert router is not None
        assert router.prefix == "/api/v1"
    
    @pytest.mark.asyncio
    async def test_http_adapter_creation(self):
        """测试 HTTP 适配器创建"""
        from agent_toolkit.adapter.http_adapter_implementation import HTTPAdapter
        from agent_toolkit.adapter.base_adapter import AdapterConfig
        
        config = AdapterConfig()
        adapter = HTTPAdapter(
            name="test-http",
            config=config,
            endpoint="https://api.example.com"
        )
        
        assert adapter.name == "test-http"
        assert adapter.endpoint == "https://api.example.com"


class TestOrchestratorIntegration:
    """编排器集成测试"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_engine_creation(self):
        """测试编排引擎创建"""
        from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine
        
        engine = OrchestrationEngine()
        assert engine is not None
    
    @pytest.mark.asyncio
    async def test_toolchain_creation(self):
        """测试工具链创建"""
        from agent_toolkit.orchestrator.orchestration_models import (
            ToolChain,
            ChainNode,
            NodeType,
            ExecutionMode,
        )
        
        # 创建简单的工具链
        node1 = ChainNode(
            id="node-1",
            name="first-task",
            node_type=NodeType.TOOL,
            adapter_name="test-adapter",
        )
        
        node2 = ChainNode(
            id="node-2",
            name="second-task",
            node_type=NodeType.TOOL,
            adapter_name="test-adapter",
            dependencies=["node-1"],
        )
        
        toolchain = ToolChain(
            name="test-chain",
            nodes=[node1, node2],
            execution_mode=ExecutionMode.SEQUENTIAL,
        )
        
        assert toolchain.name == "test-chain"
        assert len(toolchain.nodes) == 2
        assert toolchain.execution_mode == ExecutionMode.SEQUENTIAL


class TestObservabilityIntegration:
    """可观测性集成测试"""
    
    @pytest.mark.asyncio
    async def test_metrics_collector(self):
        """测试指标收集器"""
        from agent_toolkit.observability.metrics_collector import metrics_collector
        
        collector = metrics_collector()
        assert collector is not None
        
        # 获取指标
        metrics = collector.get_metrics()
        assert metrics is not None
    
    @pytest.mark.asyncio
    async def test_tracing_manager(self):
        """测试追踪管理器"""
        from agent_toolkit.observability.distributed_tracing import tracing_manager
        
        manager = tracing_manager()
        assert manager is not None
        
        # 创建 span
        with manager.start_span("test-operation") as span:
            assert span is not None


class TestRuntimeIntegration:
    """运行时集成测试"""
    
    @pytest.mark.asyncio
    async def test_base_executor(self):
        """测试基础执行器"""
        from agent_toolkit.runtime.base_executor import BaseExecutor, ExecutionStatus
        
        # 验证枚举值
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.RUNNING.value == "running"


def run_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("  🧪 Agent Toolkit 集成测试")
    print("="*70 + "\n")
    
    # 运行 pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "--asyncio-mode=auto",
    ])
    
    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
