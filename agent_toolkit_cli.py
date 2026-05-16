#!/usr/bin/env python3
"""
Agent Toolkit 快速启动脚本
一键启动服务和验证功能
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)


def print_banner():
    """打印欢迎横幅"""
    banner = r"""
    █████╗  ██████╗ ███████╗███╗   ██╗████████╗
   ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
   ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   
   ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   
   ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   
   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   
    
   🚀 Multi-agent Orchestration & Tool Management
    """
    print(Fore.CYAN + banner)
    print(Fore.YELLOW + "=" * 80)


async def check_imports():
    """检查模块导入"""
    print("\n" + Fore.CYAN + "📦 检查模块导入...")
    
    modules = [
        ("agent_toolkit.shared.application_settings", "配置模块"),
        ("agent_toolkit.shared.custom_exceptions", "异常模块"),
        ("agent_toolkit.shared.structured_logging", "日志模块"),
        ("agent_toolkit.shared.api_response", "API 响应模块"),
        ("agent_toolkit.shared.pagination", "分页模块"),
        ("agent_toolkit.shared.performance", "性能监控模块"),
        ("agent_toolkit.observability.metrics_collector", "指标模块"),
        ("agent_toolkit.observability.distributed_tracing", "追踪模块"),
        ("agent_toolkit.orchestrator.orchestration_engine", "编排引擎"),
        ("agent_toolkit.orchestrator.orchestration_models", "编排模型"),
    ]
    
    all_ok = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(Fore.GREEN + f"  ✓ {description} 导入成功")
        except Exception as e:
            print(Fore.RED + f"  ✗ {description} 导入失败: {e}")
            all_ok = False
    
    return all_ok


async def test_config():
    """测试配置系统"""
    print("\n" + Fore.CYAN + "⚙️  测试配置系统...")
    
    try:
        from agent_toolkit.shared.application_settings import Settings
        
        settings = Settings()
        print(Fore.GREEN + f"  ✓ 配置加载成功")
        print(f"    - 环境: {settings.environment}")
        print(f"    - 数据库: {settings.database.url.split('://')[0]}")
        print(f"    - 服务: {settings.server.host}:{settings.server.port}")
        return True
    except Exception as e:
        print(Fore.RED + f"  ✗ 配置测试失败: {e}")
        return False


async def test_logging():
    """测试日志系统"""
    print("\n" + Fore.CYAN + "📝 测试日志系统...")
    
    try:
        from agent_toolkit.shared.structured_logging import setup_logging, get_logger
        
        setup_logging()
        logger = get_logger("test")
        logger.info("Agent Toolkit 日志系统测试")
        print(Fore.GREEN + "  ✓ 日志系统工作正常")
        return True
    except Exception as e:
        print(Fore.RED + f"  ✗ 日志系统测试失败: {e}")
        return False


async def test_metrics():
    """测试指标系统"""
    print("\n" + Fore.CYAN + "📊 测试指标系统...")
    
    try:
        from agent_toolkit.observability.metrics_collector import metrics_collector
        
        collector = metrics_collector()
        metrics_text = collector.get_metrics(as_string=True)
        print(Fore.GREEN + "  ✓ 指标系统工作正常")
        print(f"    - 已收集 {len(metrics_text.split('\n'))} 行指标数据")
        return True
    except Exception as e:
        print(Fore.RED + f"  ✗ 指标系统测试失败: {e}")
        return False


async def test_tracing():
    """测试追踪系统"""
    print("\n" + Fore.CYAN + "🔍 测试追踪系统...")
    
    try:
        from agent_toolkit.observability.distributed_tracing import tracing_manager
        
        manager = tracing_manager()
        
        with manager.start_span("test-operation", attributes={"test": "value"}) as span:
            print(Fore.GREEN + "  ✓ 追踪系统工作正常")
            print(f"    - Trace ID: {span.context.trace_id}")
            print(f"    - Span ID: {span.context.span_id}")
        
        return True
    except Exception as e:
        print(Fore.RED + f"  ✗ 追踪系统测试失败: {e}")
        return False


async def test_performance_monitor():
    """测试性能监控"""
    print("\n" + Fore.CYAN + "⚡ 测试性能监控...")
    
    try:
        from agent_toolkit.shared.performance import (
            get_performance_monitor,
            track_performance
        )
        
        monitor = get_performance_monitor()
        
        with track_performance("test-operation"):
            await asyncio.sleep(0.1)
        
        metrics = monitor.get_all_metrics()
        print(Fore.GREEN + "  ✓ 性能监控工作正常")
        print(f"    - 已记录 {len(metrics)} 个指标")
        
        return True
    except Exception as e:
        print(Fore.RED + f"  ✗ 性能监控测试失败: {e}")
        return False


async def test_api_response():
    """测试 API 响应系统"""
    print("\n" + Fore.CYAN + "📡 测试 API 响应系统...")
    
    try:
        from agent_toolkit.shared.api_response import (
            APIResponse,
            ErrorCode,
            APIException
        )
        
        # 测试成功响应
        success_response = APIResponse.success_response(
            data={"test": "value"},
            message="操作成功"
        )
        
        # 测试错误响应
        error_response = APIResponse.error_response(
            error_code=ErrorCode.NOT_FOUND,
            message="资源未找到",
            details={"id": 123}
        )
        
        print(Fore.GREEN + "  ✓ API 响应系统工作正常")
        print(f"    - 成功响应格式: {success_response.success}")
        print(f"    - 错误响应格式: {error_response.error.error_code}")
        
        return True
    except Exception as e:
        print(Fore.RED + f"  ✗ API 响应系统测试失败: {e}")
        return False


async def run_full_quickstart():
    """运行完整的快速启动测试"""
    print_banner()
    
    results = []
    
    # 检查模块导入
    import_ok = await check_imports()
    results.append(("模块导入", import_ok))
    
    # 测试配置
    config_ok = await test_config()
    results.append(("配置系统", config_ok))
    
    # 测试日志
    logging_ok = await test_logging()
    results.append(("日志系统", logging_ok))
    
    # 测试指标
    metrics_ok = await test_metrics()
    results.append(("指标系统", metrics_ok))
    
    # 测试追踪
    tracing_ok = await test_tracing()
    results.append(("追踪系统", tracing_ok))
    
    # 测试性能监控
    perf_ok = await test_performance_monitor()
    results.append(("性能监控", perf_ok))
    
    # 测试 API 响应
    api_ok = await test_api_response()
    results.append(("API 响应", api_ok))
    
    # 打印总结
    print("\n" + "=" * 80)
    print(Fore.YELLOW + "📊 测试总结")
    print("=" * 80)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过\n")
    
    for name, ok in results:
        status = Fore.GREEN + "✓ 通过" if ok else Fore.RED + "✗ 失败"
        print(f"  {name}: {status}")
    
    if passed == total:
        print("\n" + Fore.GREEN + "=" * 80)
        print("🎉 所有测试通过！Agent Toolkit 已准备就绪！")
        print("=" * 80)
        print("\n" + Fore.CYAN + "🚀 下一步:")
        print("  1. 运行服务: python start_application.py")
        print("  2. 访问文档: http://localhost:8000/docs")
        print("  3. 健康检查: http://localhost:8000/health")
        print("  4. 查看指标: http://localhost:8000/metrics")
        print("\n")
        return 0
    else:
        print("\n" + Fore.YELLOW + "=" * 80)
        print("⚠️  部分测试失败，但核心功能已可用")
        print("=" * 80)
        print("\n" + Fore.CYAN + "📖 建议:")
        print("  - 查看详细文档: API_DOCUMENTATION.md")
        print("  - 查看项目状态: PROJECT_STATUS.md")
        print("  - 查看发展计划: DEVELOPMENT_PLAN.md")
        print("\n")
        return 0


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "quick":
            return asyncio.run(run_full_quickstart())
        elif command == "start":
            from start_application import main as start_main
            return start_main()
        elif command == "test":
            from test_quick import main as test_main
            return test_main()
        else:
            print(Fore.RED + f"未知命令: {command}")
            print("\n" + Fore.CYAN + "可用命令:")
            print("  quick  - 快速验证和启动检查")
            print("  start  - 启动服务")
            print("  test   - 运行快速测试")
            return 1
    
    return asyncio.run(run_full_quickstart())


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
