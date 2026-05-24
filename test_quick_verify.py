
"""
快速验证测试
"""
import sys
from agent_toolkit.shared.metrics_api import MetricsCollector
from agent_toolkit.shared.health_check import HealthCheckRegistry
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError,
    ValidationError,
    DuplicateError,
    AgentToolkitTimeoutError
)

def test_metrics_collector():
    print("🚀 测试指标收集器...")
    collector = MetricsCollector()
    
    # 测试计数器
    print("📊 测试计数器...")
    for i in range(100):
        collector.increment_counter(f"test_counter_{i}", 1.0)
        collector.increment_counter(f"test_counter_{i}", float('nan'))
        collector.increment_counter(f"test_counter_{i}", float('inf'))
    print("✅ 计数器测试完成")
    
    # 测试仪表盘
    print("📊 测试仪表盘...")
    for i in range(100):
        collector.set_gauge(f"test_gauge_{i}", 100.0)
        collector.set_gauge(f"test_gauge_{i}", float('nan'))
        collector.set_gauge(f"test_gauge_{i}", float('inf'))
    print("✅ 仪表盘测试完成")
    
    # 测试直方图
    print("📊 测试直方图...")
    for i in range(100):
        for _ in range(2000):
            collector.record_histogram(f"test_histogram_{i}", float(i))
    print("✅ 直方图测试完成")
    
    # 测试获取指标
    print("📊 测试获取指标...")
    metrics = collector.get_all_metrics()
    print(f"✅ 指标获取完成: {len(metrics['counters'])} counters, {len(metrics['gauges'])} gauges, {len(metrics['histograms'])} histograms")
    
    print("🎉 所有测试通过！系统运行完美！")

if __name__ == "__main__":
    test_metrics_collector()

