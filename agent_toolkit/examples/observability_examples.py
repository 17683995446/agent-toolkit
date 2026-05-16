"""
Observability 模块使用示例

展示如何收集指标和进行链路追踪。
"""

import asyncio
import time
from datetime import datetime

from agent_toolkit.observability.metrics_collector import MetricsCollector, metrics_collector
from agent_toolkit.observability.distributed_tracing import TracingManager, traced, SpanContext


async def metrics_collection_example():
    """
    示例：指标收集

    展示如何使用 Prometheus 指标收集执行数据。
    """
    print("=" * 60)
    print("示例 1: 指标收集")
    print("=" * 60)

    collector = metrics_collector()

    print("\n1.1 记录工具执行:")
    for i in range(5):
        await asyncio.sleep(0.1)
        collector.record_execution(
            tool_name="search_api",
            status="success" if i % 4 != 0 else "failure",
            duration_ms=100 + i * 10
        )
    print(f"  ✓ 记录了 5 次执行")

    print("\n1.2 记录适配器请求:")
    collector.record_adapter_request(
        adapter_type="http",
        status="success",
        duration_ms=50.5
    )
    collector.record_adapter_request(
        adapter_type="cli",
        status="success",
        duration_ms=120.3
    )
    print(f"  ✓ 记录了 2 次适配器请求")

    print("\n1.3 更新活跃执行数:")
    collector.update_active_executions(10)
    print(f"  ✓ 活跃执行数: 10")

    print("\n1.4 更新资源使用:")
    collector.update_resource_usage("cpu", 45.5)
    collector.update_resource_usage("memory", 1024)
    print(f"  ✓ 资源使用已更新")

    print("\n1.5 获取指标 (Prometheus 格式):")
    metrics_output = collector.get_metrics()
    print(f"  指标数据大小: {len(metrics_output)} bytes")
    print(f"  前 500 字符:")
    print(f"  {metrics_output.decode()[:500]}")


async def custom_metrics_example():
    """
    示例：自定义指标

    展示如何创建和使用自定义业务指标。
    """
    print("\n" + "=" * 60)
    print("示例 2: 自定义指标")
    print("=" * 60)

    collector = metrics_collector()

    print("\n2.1 模拟业务指标收集:")

    user_actions = ["login", "search", "execute_tool", "logout"]
    for i, action in enumerate(user_actions):
        await asyncio.sleep(0.1)
        print(f"  记录操作: {action}")
        time.sleep(0.05)

    print("\n2.2 队列大小监控:")
    collector.update_queue_size("execution_queue", 15)
    collector.update_queue_size("result_queue", 8)
    print(f"  ✓ 执行队列: 15")
    print(f"  ✓ 结果队列: 8")


async def tracing_example():
    """
    示例：链路追踪

    展示如何使用 OpenTelemetry 进行分布式追踪。
    """
    print("\n" + "=" * 60)
    print("示例 2: 链路追踪")
    print("=" * 60)

    manager = TracingManager()
    manager.initialize(service_name="agent-toolkit-demo")

    print("\n2.1 创建追踪跨度:")

    with SpanContext("parent_operation", {"component": "demo"}) as span_ctx:
        print(f"  父跨度已创建")

        with SpanContext("child_operation_1", {"task": "search"}) as child1:
            print(f"    子跨度1: 搜索操作")
            await asyncio.sleep(0.1)

        with SpanContext("child_operation_2", {"task": "process"}) as child2:
            print(f"    子跨度2: 处理操作")
            await asyncio.sleep(0.1)

    print(f"  ✓ 追踪跨度已完成")


async def traced_decorator_example():
    """
    示例：追踪装饰器

    展示如何使用 @traced 装饰器自动追踪函数。
    """
    print("\n" + "=" * 60)
    print("示例 3: 追踪装饰器")
    print("=" * 60)

    @traced(name="demo_function", attributes={"category": "example"})
    async def async_task(duration: float):
        """模拟异步任务"""
        await asyncio.sleep(duration)
        return {"status": "completed", "duration": duration}

    @traced(name="sync_function")
    def sync_task(value: int):
        """模拟同步任务"""
        time.sleep(0.1)
        return value * 2

    print("\n3.1 执行异步追踪函数:")
    result = await async_task(0.2)
    print(f"  结果: {result}")

    print("\n3.2 执行同步追踪函数:")
    result = sync_task(21)
    print(f"  结果: {result}")


async def span_context_propagation_example():
    """
    示例：跨度上下文传播

    展示如何在调用链中传播追踪上下文。
    """
    print("\n" + "=" * 60)
    print("示例 4: 上下文传播")
    print("=" * 60)

    manager = TracingManager()
    manager.initialize()

    print("\n4.1 创建并获取追踪上下文:")
    with SpanContext("main_operation") as span_ctx:
        context_headers = manager.create_span_context()
        print(f"  上下文头部: {context_headers}")

    print("\n4.2 模拟跨服务调用:")
    print("  假设这是来自外部的请求头:")
    simulated_headers = {
        "traceparent": "00-abc123-def456-01"
    }
    print(f"  接收到的头部: {simulated_headers}")

    extracted_context = manager.extract_span_context(simulated_headers)
    print(f"  ✓ 上下文提取完成")


async def health_monitoring_example():
    """
    示例：健康监控

    展示如何实现服务健康监控。
    """
    print("\n" + "=" * 60)
    print("示例 5: 健康监控")
    print("=" * 60)

    print("\n5.1 定义健康检查:")

    def check_database():
        return True

    def check_cache():
        return True

    def check_external_api():
        return True

    checks = {
        "database": check_database,
        "cache": check_cache,
        "external_api": check_external_api
    }

    print("\n5.2 执行健康检查:")
    results = {}
    for name, check_func in checks.items():
        try:
            is_healthy = check_func()
            results[name] = {"status": "healthy" if is_healthy else "unhealthy"}
            status_icon = "✓" if is_healthy else "✗"
            print(f"  {status_icon} {name}: {results[name]['status']}")
        except Exception as e:
            results[name] = {"status": "unhealthy", "error": str(e)}
            print(f"  ✗ {name}: {results[name]['status']} - {e}")

    overall_health = all(
        r["status"] == "healthy" for r in results.values()
    )

    print("\n5.3 总体状态:")
    if overall_health:
        print(f"  ✓ 所有服务健康")
    else:
        unhealthy = [
            name for name, result in results.items()
            if result["status"] != "healthy"
        ]
        print(f"  ✗ 不健康的服务: {', '.join(unhealthy)}")


async def main():
    """运行所有可观测性示例"""
    print("\n" + "=" * 60)
    print("Agent Toolkit Observability 模块示例")
    print("=" * 60)

    await metrics_collection_example()
    await tracing_example()
    await traced_decorator_example()
    await span_context_propagation_example()
    await health_monitoring_example()

    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
