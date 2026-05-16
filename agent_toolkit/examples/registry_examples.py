"""
Registry 模块使用示例

展示如何注册、搜索和管理工具。
"""

import asyncio
from datetime import datetime

from agent_toolkit.shared.database_connection import get_db_session_context, init_db
from agent_toolkit.registry.registry_service import ToolService, ToolCategoryService
from agent_toolkit.registry.registry_schemas import ToolCreate, ToolCategoryCreate


async def register_http_tool_example():
    """
    示例：注册一个 HTTP API 工具

    展示如何注册一个调用外部 API 的工具。
    """
    print("=" * 60)
    print("示例 1: 注册 HTTP API 工具")
    print("=" * 60)

    tool_data = ToolCreate(
        name="weather_api",
        description="获取指定城市的天气信息",
        version="1.0.0",
        category_id=1,
        status="active",
        adapter_type="http",
        adapter_config={
            "base_url": "https://api.weather.example.com",
            "endpoint": "/v1/weather",
            "method": "GET",
            "timeout": 30,
            "headers": {
                "Content-Type": "application/json"
            }
        },
        input_schema={
            "type": "object",
            "required": ["city"],
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                },
                "country": {
                    "type": "string",
                    "description": "国家代码（如 CN, US）",
                    "default": "CN"
                }
            }
        },
        output_schema={
            "type": "object",
            "properties": {
                "temperature": {"type": "number"},
                "humidity": {"type": "number"},
                "description": {"type": "string"}
            }
        },
        metadata={
            "provider": "WeatherAPI",
            "rate_limit": "100/hour",
            "documentation": "https://docs.weather.example.com"
        },
        tags=["weather", "api", "real-time"],
        author="WeatherAPI Team",
        license="MIT"
    )

    async with get_db_session_context() as session:
        service = ToolService(session)
        tool = await service.create_tool(tool_data)
        print(f"✓ 工具创建成功!")
        print(f"  ID: {tool.id}")
        print(f"  名称: {tool.name}")
        print(f"  版本: {tool.version}")
        print(f"  状态: {tool.status}")

    return tool


async def register_cli_tool_example():
    """
    示例：注册一个 CLI 工具

    展示如何注册一个命令行工具。
    """
    print("\n" + "=" * 60)
    print("示例 2: 注册 CLI 工具")
    print("=" * 60)

    tool_data = ToolCreate(
        name="git_status",
        description="检查 Git 仓库状态",
        version="1.0.0",
        adapter_type="cli",
        adapter_config={
            "command": "git status",
            "working_dir": "/repo",
            "timeout": 30,
            "shell": True
        },
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Git 仓库路径"
                }
            }
        },
        tags=["git", "vcs", "cli"],
        author="DevTools Team",
        license="MIT"
    )

    async with get_db_session_context() as session:
        service = ToolService(session)
        tool = await service.create_tool(tool_data)
        print(f"✓ CLI 工具创建成功!")
        print(f"  名称: {tool.name}")
        print(f"  命令: git status")

    return tool


async def search_tools_example():
    """
    示例：搜索和管理工具

    展示如何搜索、过滤和管理已注册的工具。
    """
    print("\n" + "=" * 60)
    print("示例 3: 搜索工具")
    print("=" * 60)

    async with get_db_session_context() as session:
        service = ToolService(session)

        print("\n3.1 按分类搜索:")
        tools, total = await service.list_tools(
            category_id=1,
            page=1,
            page_size=10
        )
        print(f"  找到 {total} 个工具")

        print("\n3.2 按标签搜索:")
        tools, total = await service.list_tools(
            tags=["api", "weather"],
            page=1,
            page_size=10
        )
        print(f"  找到 {total} 个带有 'api' 或 'weather' 标签的工具")

        print("\n3.3 全文搜索:")
        tools, total = await service.list_tools(
            search="weather",
            page=1,
            page_size=10
        )
        print(f"  找到 {total} 个匹配 'weather' 的工具")

        print("\n3.4 按状态过滤:")
        tools, total = await service.list_tools(
            status="active",
            page=1,
            page_size=10
        )
        print(f"  找到 {total} 个活跃状态的工具")


async def tool_version_management_example():
    """
    示例：工具版本管理

    展示如何创建和管理工具版本。
    """
    print("\n" + "=" * 60)
    print("示例 4: 工具版本管理")
    print("=" * 60)

    from agent_toolkit.registry.registry_service import ToolVersionService
    from agent_toolkit.registry.registry_schemas import ToolVersionCreate

    async with get_db_session_context() as session:
        tool_service = ToolService(session)
        version_service = ToolVersionService(session)

        tool = await tool_service.get_tool_by_name("weather_api")

        print(f"\n当前版本: {tool.version}")

        print("\n4.1 创建新版本:")
        new_version = ToolVersionCreate(
            version="1.1.0",
            changelog="""
            - 添加空气质量指数支持
            - 优化响应速度
            - 修复时区问题
            """,
            breaking_changes=False
        )
        version = await version_service.create_version(tool.id, new_version)
        print(f"✓ 创建新版本 {version.version} 成功!")

        print("\n4.2 列出所有版本:")
        versions = await version_service.list_versions(tool.id)
        for v in versions:
            print(f"  - v{v.version} (下载: {v.download_count})")

        print("\n4.3 获取最新版本:")
        latest = await version_service.get_latest_version(tool.id)
        print(f"  最新版本: v{latest.version}")


async def category_management_example():
    """
    示例：分类管理

    展示如何创建和管理工具分类。
    """
    print("\n" + "=" * 60)
    print("示例 5: 分类管理")
    print("=" * 60)

    async with get_db_session_context() as session:
        service = ToolCategoryService(session)

        print("\n5.1 创建分类:")
        category_data = ToolCategoryCreate(
            name="data_processing",
            description="数据处理和分析工具",
            metadata={"icon": "database"}
        )
        category = await service.create_category(category_data)
        print(f"✓ 创建分类 '{category.name}' 成功 (ID: {category.id})")

        print("\n5.2 列出所有分类:")
        categories = await service.list_categories()
        for cat in categories:
            print(f"  - {cat.name}: {cat.description or '无描述'}")

        print("\n5.3 获取分类详情:")
        cat = await service.get_category(category.id)
        print(f"  分类: {cat.name}")
        print(f"  描述: {cat.description}")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("Agent Toolkit Registry 模块示例")
    print("=" * 60)

    await init_db()

    try:
        await register_http_tool_example()
    except Exception as e:
        print(f"示例1跳过（可能已存在）: {e}")

    try:
        await register_cli_tool_example()
    except Exception as e:
        print(f"示例2跳过: {e}")

    await category_management_example()
    await search_tools_example()

    try:
        await tool_version_management_example()
    except Exception as e:
        print(f"示例4跳过: {e}")

    print("\n" + "=" * 60)
    print("示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
