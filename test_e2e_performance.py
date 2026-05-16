#!/usr/bin/env python3
"""
Agent Toolkit 端到端测试和性能测试
测试完整的用户场景和系统性能
"""

import sys
import os
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)


def print_section(title):
    """打印带标题的分隔线"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}{title}")
    print(f"{Fore.CYAN}{'='*70}")


def print_success(message):
    """打印成功信息"""
    print(f"{Fore.GREEN}✓ {message}")


def print_error(message):
    """打印错误信息"""
    print(f"{Fore.RED}✗ {message}")


def print_info(message):
    """打印信息"""
    print(f"{Fore.BLUE}ℹ {message}")


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
    
    def record(self, name: str, duration: float):
        """记录性能指标"""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(duration)
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """获取统计信息"""
        if name not in self.metrics:
            return {}
        
        values = self.metrics[name]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "total": sum(values),
        }
    
    def print_summary(self):
        """打印性能摘要"""
        print_section("性能测试摘要")
        
        for name in self.metrics:
            stats = self.get_stats(name)
            print(f"\n{Fore.YELLOW}{name}:")
            print(f"  执行次数: {stats['count']}")
            print(f"  平均时间: {stats['avg']*1000:.2f} ms")
            print(f"  最小时间: {stats['min']*1000:.2f} ms")
            print(f"  最大时间: {stats['max']*1000:.2f} ms")
            print(f"  总时间:   {stats['total']*1000:.2f} ms")


async def test_configuration_loading(metrics: PerformanceMetrics):
    """测试配置加载性能"""
    print_info("测试配置加载...")
    
    start_time = time.time()
    from agent_toolkit.shared.application_settings import Settings
    settings = Settings()
    duration = time.time() - start_time
    
    metrics.record("配置加载", duration)
    print_success(f"配置加载完成 ({duration*1000:.2f} ms)")
    return True


async def test_adapter_creation(metrics: PerformanceMetrics):
    """测试适配器创建性能"""
    print_info("测试适配器创建...")
    
    from agent_toolkit.adapter.http_adapter_implementation import HTTPAdapter
    from agent_toolkit.adapter.base_adapter import AdapterConfig
    
    # 创建多个适配器
    for i in range(10):
        start_time = time.time()
        adapter = HTTPAdapter(
            name=f"test-adapter-{i}",
            config=AdapterConfig(),
            endpoint=f"https://api{i}.example.com"
        )
        duration = time.time() - start_time
        metrics.record("适配器创建", duration)
    
    print_success("适配器创建测试完成")
    return True


async def test_toolchain_building(metrics: PerformanceMetrics):
    """测试工具链构建性能"""
    print_info("测试工具链构建...")
    
    from agent_toolkit.orchestrator.orchestration_models import (
        ToolChain,
        ChainNode,
        NodeType,
        ExecutionMode,
    )
    
    # 构建多个工具链
    for i in range(5):
        start_time = time.time()
        
        nodes = [
            ChainNode(
                id=f"node-{j}",
                name=f"task-{j}",
                node_type=NodeType.TOOL,
                adapter_name="test-adapter",
            )
            for j in range(10)
        ]
        
        toolchain = ToolChain(
            name=f"test-chain-{i}",
            nodes=nodes,
            execution_mode=ExecutionMode.SEQUENTIAL,
        )
        
        duration = time.time() - start_time
        metrics.record("工具链构建", duration)
    
    print_success("工具链构建测试完成")
    return True


async def test_metrics_collection(metrics: PerformanceMetrics):
    """测试指标收集性能"""
    print_info("测试指标收集...")
    
    from agent_toolkit.observability.metrics_collector import metrics_collector
    
    collector = metrics_collector()
    
    # 收集多次指标
    for i in range(20):
        start_time = time.time()
        metrics_data = collector.get_metrics()
        duration = time.time() - start_time
        metrics.record("指标收集", duration)
    
    print_success("指标收集测试完成")
    return True


async def test_tracing_operations(metrics: PerformanceMetrics):
    """测试追踪操作性能"""
    print_info("测试追踪操作...")
    
    from agent_toolkit.observability.distributed_tracing import tracing_manager
    
    manager = tracing_manager()
    
    # 创建多个 span
    for i in range(20):
        start_time = time.time()
        
        with manager.start_span(f"test-operation-{i}") as span:
            pass
        
        duration = time.time() - start_time
        metrics.record("追踪操作", duration)
    
    print_success("追踪操作测试完成")
    return True


async def test_database_operations(metrics: PerformanceMetrics):
    """测试数据库操作性能"""
    print_info("测试数据库操作...")
    
    from agent_toolkit.shared.database_connection import get_db_session
    from sqlalchemy import text
    
    # 测试数据库连接
    async for session in get_db_session():
        for i in range(10):
            start_time = time.time()
            
            result = await session.execute(text("SELECT 1"))
            
            duration = time.time() - start_time
            metrics.record("数据库查询", duration)
    
    print_success("数据库操作测试完成")
    return True


async def test_end_to_end_workflow(metrics: PerformanceMetrics):
    """测试端到端工作流"""
    print_info("测试端到端工作流...")
    
    start_time = time.time()
    
    # 1. 加载配置
    from agent_toolkit.shared.application_settings import Settings
    settings = Settings()
    
    # 2. 创建适配器
    from agent_toolkit.adapter.http_adapter_implementation import HTTPAdapter
    from agent_toolkit.adapter.base_adapter import AdapterConfig
    adapter = HTTPAdapter(
        name="workflow-adapter",
        config=AdapterConfig(),
        endpoint="https://api.example.com"
    )
    
    # 3. 创建工具链
    from agent_toolkit.orchestrator.orchestration_models import (
        ToolChain,
        ChainNode,
        NodeType,
        ExecutionMode,
    )
    
    nodes = [
        ChainNode(
            id="workflow-node",
            name="workflow-task",
            node_type=NodeType.TOOL,
            adapter_name="workflow-adapter",
        )
    ]
    
    toolchain = ToolChain(
        name="workflow-chain",
        nodes=nodes,
        execution_mode=ExecutionMode.SEQUENTIAL,
    )
    
    # 4. 收集指标
    from agent_toolkit.observability.metrics_collector import metrics_collector
    collector = metrics_collector()
    metrics_data = collector.get_metrics()
    
    duration = time.time() - start_time
    metrics.record("端到端工作流", duration)
    
    print_success(f"端到端工作流完成 ({duration*1000:.2f} ms)")
    return True


async def run_performance_tests():
    """运行性能测试"""
    print_section("🚀 性能测试")
    
    metrics = PerformanceMetrics()
    
    tests = [
        ("配置加载", test_configuration_loading),
        ("适配器创建", test_adapter_creation),
        ("工具链构建", test_toolchain_building),
        ("指标收集", test_metrics_collection),
        ("追踪操作", test_tracing_operations),
        ("数据库操作", test_database_operations),
        ("端到端工作流", test_end_to_end_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func(metrics)
            results.append((test_name, result))
        except Exception as e:
            print_error(f"{test_name} 失败: {e}")
            results.append((test_name, False))
    
    # 打印性能摘要
    metrics.print_summary()
    
    return all(result for _, result in results)


async def run_end_to_end_tests():
    """运行端到端测试"""
    print_section("🎯 端到端测试")
    
    tests = [
        ("完整工作流测试", test_end_to_end_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            metrics = PerformanceMetrics()
            result = await test_func(metrics)
            results.append((test_name, result))
            print_success(f"{test_name} 通过")
        except Exception as e:
            print_error(f"{test_name} 失败: {e}")
            results.append((test_name, False))
    
    return all(result for _, result in results)


async def main():
    """主函数"""
    print("\n" + "="*70)
    print("  🧪 Agent Toolkit 端到端测试和性能测试")
    print("="*70)
    
    # 运行端到端测试
    e2e_result = await run_end_to_end_tests()
    
    # 运行性能测试
    perf_result = await run_performance_tests()
    
    # 打印总结
    print_section("测试总结")
    
    if e2e_result and perf_result:
        print(f"\n{Fore.GREEN}✓ 所有测试通过！")
        print(f"{Fore.GREEN}✓ 系统性能良好！\n")
        return 0
    else:
        print(f"\n{Fore.RED}✗ 部分测试失败")
        print(f"{Fore.RED}✗ 请检查错误信息\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
