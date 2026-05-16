"""
Orchestrator 模块使用示例

展示如何编排和执行工具链。
"""

import asyncio
from datetime import datetime

from agent_toolkit.orchestrator.orchestration_models import (
    ToolChain,
    ChainNode,
    ChainEdge,
    NodeType,
    ExecutionMode,
    RetryPolicy
)
from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine
from agent_toolkit.orchestrator.task_scheduler import Scheduler, ScheduleType


async def sequential_chain_example():
    """
    示例：顺序执行工具链

    展示如何定义和执行一个顺序执行的工具链。
    """
    print("=" * 60)
    print("示例 1: 顺序执行工具链")
    print("=" * 60)

    print("\n1.1 定义工具链:")

    nodes = [
        ChainNode(
            id="input",
            type=NodeType.INPUT,
            name="输入节点",
            config={"schema": {"type": "object", "properties": {"query": {"type": "string"}}}}
        ),
        ChainNode(
            id="search",
            type=NodeType.TOOL,
            name="搜索工具",
            config={"tool_id": "web_search", "adapter": "http"},
            inputs={"query": "input.query"},
            outputs=["results"]
        ),
        ChainNode(
            id="process",
            type=NodeType.TOOL,
            name="数据处理",
            config={"tool_id": "data_processor", "operation": "filter"},
            inputs={"data": "search.results"},
            outputs=["processed"]
        ),
        ChainNode(
            id="output",
            type=NodeType.OUTPUT,
            name="输出节点",
            inputs={"result": "process.processed"}
        )
    ]

    edges = [
        ChainEdge(source="input", target="search"),
        ChainEdge(source="search", target="process"),
        ChainEdge(source="process", target="output")
    ]

    chain = ToolChain(
        id="simple_chain_001",
        name="简单搜索处理链",
        description="搜索并处理数据的示例链",
        version="1.0.0",
        nodes=nodes,
        edges=edges,
        execution_mode=ExecutionMode.SEQUENTIAL
    )

    print(f"✓ 工具链定义完成")
    print(f"  ID: {chain.id}")
    print(f"  名称: {chain.name}")
    print(f"  节点数: {len(chain.nodes)}")
    print(f"  执行模式: {chain.execution_mode.value}")

    print("\n1.2 验证工具链:")
    is_valid, errors = chain.validate()
    if is_valid:
        print(f"  ✓ 工具链结构有效")
    else:
        print(f"  ✗ 验证失败: {errors}")

    print("\n1.3 拓扑排序结果:")
    sorted_nodes = chain.topological_sort()
    for i, node in enumerate(sorted_nodes, 1):
        print(f"  {i}. {node.name} ({node.id})")

    print("\n1.4 执行工具链 (模拟):")
    engine = OrchestrationEngine()

    initial_inputs = {
        "query": "Python 异步编程"
    }

    print(f"  输入: {initial_inputs}")
    print(f"  模拟执行完成!")


async def parallel_chain_example():
    """
    示例：并行执行工具链

    展示如何定义和执行一个并行执行的工具链。
    """
    print("\n" + "=" * 60)
    print("示例 2: 并行执行工具链")
    print("=" * 60)

    print("\n2.1 定义并行工具链:")

    nodes = [
        ChainNode(id="start", type=NodeType.INPUT, name="开始"),
        ChainNode(id="parallel_1", type=NodeType.TOOL, name="任务A", config={"tool": "task_a"}),
        ChainNode(id="parallel_2", type=NodeType.TOOL, name="任务B", config={"tool": "task_b"}),
        ChainNode(id="parallel_3", type=NodeType.TOOL, name="任务C", config={"tool": "task_c"}),
        ChainNode(id="merge", type=NodeType.MERGE, name="合并结果"),
        ChainNode(id="end", type=NodeType.OUTPUT, name="结束")
    ]

    edges = [
        ChainEdge(source="start", target="parallel_1"),
        ChainEdge(source="start", target="parallel_2"),
        ChainEdge(source="start", target="parallel_3"),
        ChainEdge(source="parallel_1", target="merge"),
        ChainEdge(source="parallel_2", target="merge"),
        ChainEdge(source="parallel_3", target="merge"),
        ChainEdge(source="merge", target="end")
    ]

    chain = ToolChain(
        id="parallel_chain_001",
        name="并行任务链",
        description="三个任务并行执行的示例",
        version="1.0.0",
        nodes=nodes,
        edges=edges,
        execution_mode=ExecutionMode.PARALLEL
    )

    print(f"✓ 并行工具链定义完成")
    print(f"  执行模式: {chain.execution_mode.value}")
    print(f"  任务节点: 3个")

    print("\n2.2 执行并行链 (模拟):")
    print("  任务A, B, C 将并行执行...")
    print("  等待所有任务完成后合并结果")


async def conditional_chain_example():
    """
    示例：条件分支工具链

    展示如何定义包含条件分支的工具链。
    """
    print("\n" + "=" * 60)
    print("示例 3: 条件分支工具链")
    print("=" * 60)

    print("\n3.1 定义条件分支:")

    nodes = [
        ChainNode(id="input", type=NodeType.INPUT, name="输入"),
        ChainNode(
            id="check",
            type=NodeType.CONDITION,
            name="类型检查",
            condition="input.type == 'premium'"
        ),
        ChainNode(id="basic", type=NodeType.TOOL, name="基础处理", config={"tier": "basic"}),
        ChainNode(id="premium", type=NodeType.TOOL, name="高级处理", config={"tier": "premium"}),
        ChainNode(id="output", type=NodeType.OUTPUT, name="输出")
    ]

    edges = [
        ChainEdge(source="input", target="check"),
        ChainEdge(source="check", target="basic", condition="result == False"),
        ChainEdge(source="check", target="premium", condition="result == True"),
        ChainEdge(source="basic", target="output"),
        ChainEdge(source="premium", target="output")
    ]

    chain = ToolChain(
        id="conditional_chain_001",
        name="条件分支链",
        description="根据条件选择处理路径",
        nodes=nodes,
        edges=edges
    )

    print(f"✓ 条件分支链定义完成")

    print("\n3.2 条件逻辑:")
    print("  如果 input.type == 'premium' → 高级处理")
    print("  否则 → 基础处理")


async def retry_and_timeout_example():
    """
    示例：重试和超时配置

    展示如何配置节点的重试策略和超时。
    """
    print("\n" + "=" * 60)
    print("示例 4: 重试和超时配置")
    print("=" * 60)

    print("\n4.1 配置重试策略:")

    retry_policy = RetryPolicy(
        max_attempts=3,
        retry_delay=2.0,
        backoff_multiplier=2.0,
        retry_on_errors=["ConnectionError", "Timeout"]
    )

    print(f"  最大尝试次数: {retry_policy.max_attempts}")
    print(f"  重试延迟: {retry_policy.retry_delay}秒")
    print(f"  退避倍数: {retry_policy.backoff_multiplier}")
    print(f"  重试错误类型: {', '.join(retry_policy.retry_on_errors)}")

    print("\n4.2 应用到节点:")

    unreliable_node = ChainNode(
        id="unreliable_api",
        type=NodeType.TOOL,
        name="不可靠API",
        config={"url": "https://api.example.com"},
        retry_policy=retry_policy,
        timeout=30
    )

    print(f"  节点: {unreliable_node.name}")
    print(f"  超时: {unreliable_node.timeout}秒")
    print(f"  重试策略: 已配置")


async def scheduler_example():
    """
    示例：调度器使用

    展示如何调度工具链定期执行。
    """
    print("\n" + "=" * 60)
    print("示例 5: 工具链调度")
    print("=" * 60)

    scheduler = Scheduler()

    print("\n5.1 创建立即执行调度:")
    schedule1 = scheduler.create_schedule(
        schedule_id="immediate_001",
        chain=ToolChain(
            id="quick_chain",
            name="快速执行链",
            nodes=[],
            edges=[]
        ),
        initial_inputs={"param": "value"},
        schedule_type=ScheduleType.IMMEDIATE
    )
    print(f"  ✓ 调度创建成功")
    print(f"  调度ID: {schedule1.schedule_id}")
    print(f"  类型: {schedule1.schedule_type.value}")

    print("\n5.2 创建定时执行调度:")
    from datetime import datetime, timedelta
    run_at = datetime.utcnow() + timedelta(hours=1)

    schedule2 = scheduler.create_schedule(
        schedule_id="delayed_001",
        chain=ToolChain(
            id="hourly_chain",
            name="每小时执行链",
            nodes=[],
            edges=[]
        ),
        schedule_type=ScheduleType.DELAYED,
        run_at=run_at
    )
    print(f"  ✓ 定时调度创建成功")
    print(f"  执行时间: {run_at.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n5.3 调度统计:")
    stats = scheduler.get_stats()
    print(f"  总调度数: {stats['total_schedules']}")
    print(f"  启用数: {stats['enabled_schedules']}")
    print(f"  等待执行数: {stats['due_schedules']}")


async def main():
    """运行所有 Orchestrator 示例"""
    print("\n" + "=" * 60)
    print("Agent Toolkit Orchestrator 模块示例")
    print("=" * 60)

    await sequential_chain_example()
    await parallel_chain_example()
    await conditional_chain_example()
    await retry_and_timeout_example()
    await scheduler_example()

    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
