"""
Runtime 模块使用示例

展示如何执行工具和安全管理执行环境。
"""

import asyncio
from datetime import datetime

from agent_toolkit.runtime.base_executor import ExecutorConfig, ExecutionStatus
from agent_toolkit.runtime.docker_executor_implementation import DockerExecutor, DockerExecutorConfig
from agent_toolkit.runtime.sandbox_manager import SandboxManager, SandboxConfig, SandboxType
from agent_toolkit.runtime.resource_manager import ResourceManager, ResourceLimit


async def basic_execution_example():
    """
    示例：基础工具执行

    展示如何使用执行器执行工具。
    """
    print("=" * 60)
    print("示例 1: 基础工具执行")
    print("=" * 60)

    config = ExecutorConfig(
        timeout=60,
        max_retries=3,
        retry_delay=1.0,
        enable_sandbox=True,
        cpu_limit="1",
        memory_limit="512Mi"
    )

    print("\n执行器配置:")
    print(f"  超时: {config.timeout}秒")
    print(f"  最大重试: {config.max_retries}")
    print(f"  启用沙箱: {config.enable_sandbox}")

    print("\n模拟执行:")
    input_data = {
        "tool_id": "test_tool",
        "command": "echo 'Hello World'"
    }

    print(f"  输入数据: {input_data}")
    print(f"  模拟执行成功!")


async def docker_execution_example():
    """
    示例：Docker 容器执行

    展示如何在 Docker 容器中安全执行工具。
    """
    print("\n" + "=" * 60)
    print("示例 2: Docker 容器执行")
    print("=" * 60)

    config = DockerExecutorConfig(
        image="python:3.12-slim",
        timeout=60,
        max_retries=2,
        network="bridge",
        auto_remove=True
    )

    executor = DockerExecutor(config)

    print("\nDocker 配置:")
    print(f"  镜像: {config.image}")
    print(f"  网络模式: {config.network}")
    print(f"  自动清理: {config.auto_remove}")

    try:
        await executor.initialize()
        print("✓ Docker 执行器初始化成功!")

        print("\n执行工具:")
        result = await executor.execute(
            tool_id="docker_test",
            input_data={"script": "print('Hello from Docker!')"}
        )

        print(f"  执行ID: {result.execution_id}")
        print(f"  状态: {result.status}")
        print(f"  退出码: {result.exit_code}")

    except Exception as e:
        print(f"  Docker 执行需要 Docker 守护进程运行")
        print(f"  错误: {str(e)[:100]}")

    finally:
        await executor.cleanup()


async def sandbox_example():
    """
    示例：沙箱管理

    展示如何创建和管理安全沙箱。
    """
    print("\n" + "=" * 60)
    print("示例 3: 沙箱管理")
    print("=" * 60)

    manager = SandboxManager()

    print("\n3.1 创建沙箱:")

    sandbox_config = SandboxConfig(
        sandbox_type=SandboxType.DOCKER,
        network_enabled=False,
        filesystem_readonly=True,
        max_memory_mb=256,
        max_cpu_percent=50,
        timeout_seconds=60
    )

    sandbox = await manager.create_sandbox(
        sandbox_id="secure_sandbox_001",
        config=sandbox_config
    )

    print(f"✓ 沙箱创建成功!")
    print(f"  ID: {sandbox.instance_id}")
    print(f"  类型: {sandbox.config.sandbox_type}")
    print(f"  状态: {sandbox.status}")

    print("\n3.2 获取沙箱状态:")
    stats = await manager.get_sandbox_stats(sandbox.instance_id)
    print(f"  进程数: {stats.get('process_count', 0)}")
    print(f"  创建时间: {datetime.fromtimestamp(stats.get('created_at', 0))}")

    print("\n3.3 列出所有沙箱:")
    sandboxes = await manager.list_sandboxes()
    print(f"  总数: {len(sandboxes)}")

    print("\n3.4 销毁沙箱:")
    await manager.destroy_sandbox(sandbox.instance_id)
    print(f"✓ 沙箱已销毁")


async def resource_management_example():
    """
    示例：资源管理

    展示如何监控系统和管理执行资源。
    """
    print("\n" + "=" * 60)
    print("示例 4: 资源管理")
    print("=" * 60)

    manager = ResourceManager()

    print("\n4.1 分配资源:")
    limits = ResourceLimit(
        cpu_cores=2.0,
        memory_mb=1024,
        disk_mb=5120,
        max_processes=50
    )

    resource = await manager.allocate_resources(
        execution_id="exec_001",
        limits=limits
    )

    print(f"✓ 资源分配成功!")
    print(f"  执行ID: {resource.execution_id}")
    print(f"  CPU核心: {resource.limits.cpu_cores}")
    print(f"  内存限制: {resource.limits.memory_mb}MB")

    print("\n4.2 系统资源状态:")
    system_resources = await manager.get_system_resources()
    print(f"  CPU核心数: {system_resources['cpu']['count']}")
    print(f"  CPU使用率: {system_resources['cpu']['percent']:.1f}%")
    print(f"  内存总量: {system_resources['memory']['total'] / (1024**3):.2f}GB")
    print(f"  内存使用率: {system_resources['memory']['percent']:.1f}%")

    print("\n4.3 检查资源限制:")
    within_limits, violations = await manager.check_limits("exec_001")
    if within_limits:
        print(f"  ✓ 资源使用在限制范围内")
    else:
        print(f"  ✗ 资源超出限制:")
        for resource_type, info in violations.items():
            print(f"    - {resource_type}: {info['used']}/{info['limit']}")

    print("\n4.4 释放资源:")
    await manager.release_resources("exec_001")
    print(f"✓ 资源已释放")


async def lifecycle_hooks_example():
    """
    示例：生命周期钩子

    展示如何注册和使用执行生命周期钩子。
    """
    print("\n" + "=" * 60)
    print("示例 5: 生命周期钩子")
    print("=" * 60)

    from agent_toolkit.runtime.execution_lifecycle_manager import (
        LifecycleManager,
        LifecycleEvent,
        LifecycleContext
    )

    manager = LifecycleManager()

    async def pre_execute_hook(ctx: LifecycleContext):
        """执行前钩子"""
        print(f"  [钩子] 准备执行工具: {ctx.tool_id}")
        return {"status": "preparing"}

    async def post_execute_hook(ctx: LifecycleContext):
        """执行后钩子"""
        print(f"  [钩子] 工具执行完成: {ctx.tool_id}")
        return {"status": "completed"}

    async def error_hook(ctx: LifecycleContext):
        """错误处理钩子"""
        print(f"  [钩子] 捕获错误: {ctx.metadata.get('error', 'Unknown')}")
        return {"status": "error_handled"}

    print("\n5.1 注册钩子:")
    manager.register_hook(
        event=LifecycleEvent.PRE_EXECUTE,
        callback=pre_execute_hook,
        priority=10,
        timeout_seconds=5
    )
    print("  ✓ 注册 PRE_EXECUTE 钩子")

    manager.register_hook(
        event=LifecycleEvent.POST_EXECUTE,
        callback=post_execute_hook,
        priority=10
    )
    print("  ✓ 注册 POST_EXECUTE 钩子")

    manager.register_hook(
        event=LifecycleEvent.ON_ERROR,
        callback=error_hook,
        priority=20
    )
    print("  ✓ 注册 ON_ERROR 钩子")

    print("\n5.2 触发钩子:")
    context = LifecycleContext(
        execution_id="exec_001",
        tool_id="test_tool",
        event=LifecycleEvent.PRE_EXECUTE,
        metadata={"input": "test"}
    )

    await manager.trigger_event(LifecycleEvent.PRE_EXECUTE, context)
    print("  ✓ PRE_EXECUTE 钩子已触发")

    print("\n5.3 生命周期统计:")
    stats = manager.get_stats()
    for event, count in stats.items():
        print(f"  {event}: {count} 个钩子")


async def main():
    """运行所有 Runtime 示例"""
    print("\n" + "=" * 60)
    print("Agent Toolkit Runtime 模块示例")
    print("=" * 60)

    await basic_execution_example()
    await sandbox_example()
    await resource_management_example()
    await lifecycle_hooks_example()

    try:
        await docker_execution_example()
    except Exception as e:
        print(f"\n[跳过] Docker 示例需要 Docker 守护进程: {str(e)[:50]}")

    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
