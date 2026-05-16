"""
Adapter 模块使用示例

展示如何使用不同类型的适配器执行工具。
"""

import asyncio
from datetime import datetime

from agent_toolkit.adapter.base_adapter import ToolMetadata, AdapterType
from agent_toolkit.adapter.http_adapter_implementation import HTTPAdapter, HTTPAdapterConfig
from agent_toolkit.adapter.cli_adapter_implementation import CLIAdapter, CLIAdapterConfig
from agent_toolkit.adapter.sdk_adapter_implementation import SDKAdapter, SDKAdapterConfig


async def http_adapter_usage_example():
    """
    示例：使用 HTTP 适配器

    展示如何配置和使用 HTTP 适配器调用 REST API。
    """
    print("=" * 60)
    print("示例 1: HTTP 适配器使用")
    print("=" * 60)

    config = HTTPAdapterConfig(
        base_url="https://jsonplaceholder.typicode.com",
        endpoint="/posts/1",
        method="GET",
        timeout=30,
        headers={
            "Accept": "application/json"
        }
    )

    adapter = HTTPAdapter(config)
    await adapter.initialize()

    print("\n配置信息:")
    print(f"  基础URL: {config.base_url}")
    print(f"  端点: {config.endpoint}")
    print(f"  方法: {config.method}")

    print("\n执行请求:")
    result = await adapter.execute({})

    if result.is_success:
        print(f"✓ 请求成功!")
        print(f"  状态: {result.status}")
        print(f"  执行时间: {result.execution_time_ms:.2f}ms")
        print(f"  数据: {result.data}")
    else:
        print(f"✗ 请求失败: {result.error}")

    await adapter.cleanup()


async def http_adapter_post_example():
    """
    示例：使用 HTTP POST 请求

    展示如何发送 POST 请求和上传数据。
    """
    print("\n" + "=" * 60)
    print("示例 2: HTTP POST 请求")
    print("=" * 60)

    config = HTTPAdapterConfig(
        base_url="https://jsonplaceholder.typicode.com",
        endpoint="/posts",
        method="POST",
        timeout=30
    )

    adapter = HTTPAdapter(config)
    await adapter.initialize()

    input_data = {
        "title": "测试文章",
        "body": "这是测试内容",
        "userId": 1
    }

    print(f"\n发送数据: {input_data}")

    result = await adapter.execute(input_data)

    if result.is_success:
        print(f"✓ POST 请求成功!")
        print(f"  响应数据: {result.data}")
    else:
        print(f"✗ POST 请求失败: {result.error}")

    await adapter.cleanup()


async def cli_adapter_usage_example():
    """
    示例：使用 CLI 适配器

    展示如何执行命令行工具。
    """
    print("\n" + "=" * 60)
    print("示例 3: CLI 适配器使用")
    print("=" * 60)

    config = CLIAdapterConfig(
        command="echo",
        args=["Hello, Agent Toolkit!"],
        timeout=10,
        shell=False
    )

    adapter = CLIAdapter(config)
    await adapter.initialize()

    print("\n执行命令:")
    print(f"  命令: {' '.join([config.command] + config.args)}")

    result = await adapter.execute({})

    if result.is_success:
        print(f"✓ 命令执行成功!")
        print(f"  标准输出: {result.data.get('stdout', '').strip()}")
        print(f"  退出码: {result.data.get('returncode', 0)}")
    else:
        print(f"✗ 命令执行失败: {result.error}")

    await adapter.cleanup()


async def cli_adapter_with_env_example():
    """
    示例：带环境变量的 CLI 执行

    展示如何传递环境变量给 CLI 命令。
    """
    print("\n" + "=" * 60)
    print("示例 4: CLI 环境变量")
    print("=" * 60)

    config = CLIAdapterConfig(
        command="printenv",
        args=["MY_VAR"],
        env_vars={
            "MY_VAR": "Hello from Environment!",
            "APP_NAME": "AgentToolkit"
        },
        timeout=10
    )

    adapter = CLIAdapter(config)
    await adapter.initialize()

    print("\n环境变量:")
    for key, value in config.env_vars.items():
        print(f"  {key}={value}")

    result = await adapter.execute({})

    if result.is_success:
        print(f"\n✓ 命令执行成功!")
        print(f"  输出: {result.data.get('stdout', '').strip()}")
    else:
        print(f"✗ 命令执行失败: {result.error}")

    await adapter.cleanup()


async def cli_adapter_timeout_example():
    """
    示例：CLI 超时处理

    展示如何处理长时间运行的命令超时。
    """
    print("\n" + "=" * 60)
    print("示例 5: CLI 超时处理")
    print("=" * 60)

    config = CLIAdapterConfig(
        command="sleep",
        args=["10"],
        timeout=2
    )

    adapter = CLIAdapter(config)
    await adapter.initialize()

    print("\n执行长时间命令 (sleep 10秒，超时2秒):")

    result = await adapter.execute({})

    if result.status.value == "timeout":
        print(f"✓ 超时处理正确!")
        print(f"  状态: {result.status}")
        print(f"  错误: {result.error}")
    else:
        print(f"  状态: {result.status}")

    await adapter.cleanup()


async def adapter_with_retry_example():
    """
    示例：带重试机制的适配器

    展示如何配置自动重试。
    """
    print("\n" + "=" * 60)
    print("示例 6: 适配器重试机制")
    print("=" * 60)

    from agent_toolkit.adapter.base_adapter import AdapterConfig

    config = HTTPAdapterConfig(
        base_url="https://httpstat.us",
        endpoint="/200",
        method="GET",
        timeout=30
    )

    base_config = AdapterConfig(
        timeout=30,
        retry_count=3,
        retry_delay=1.0
    )

    adapter = HTTPAdapter(config, base_config)
    adapter._config = base_config
    await adapter.initialize()

    print("\n重试配置:")
    print(f"  最大重试次数: {base_config.retry_count}")
    print(f"  重试延迟: {base_config.retry_delay}秒")

    print("\n执行请求:")
    result = await adapter._execute_with_retry({})

    print(f"  最终状态: {result.status}")
    if result.is_success:
        print(f"  ✓ 请求成功 (可能在重试后)")
    else:
        print(f"  ✗ 请求失败: {result.error}")

    await adapter.cleanup()


async def main():
    """运行所有适配器示例"""
    print("\n" + "=" * 60)
    print("Agent Toolkit Adapter 模块示例")
    print("=" * 60)

    await http_adapter_usage_example()
    await http_adapter_post_example()
    await cli_adapter_usage_example()
    await cli_adapter_with_env_example()
    await cli_adapter_timeout_example()
    await adapter_with_retry_example()

    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
