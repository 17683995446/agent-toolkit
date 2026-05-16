#!/usr/bin/env python3
"""
Agent Toolkit 最终验证脚本
验证所有核心功能是否正常工作
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


async def verify_configuration_system():
    """验证配置系统"""
    print_info("验证配置系统...")
    
    try:
        from agent_toolkit.shared.application_settings import Settings, get_settings
        
        # 测试默认配置
        settings = Settings()
        assert settings.environment == "development"
        
        # 测试全局配置
        global_settings = get_settings()
        assert global_settings is not None
        
        print_success("配置系统验证通过")
        return True
    except Exception as e:
        print_error(f"配置系统验证失败: {e}")
        return False


async def verify_logging_system():
    """验证日志系统"""
    print_info("验证日志系统...")
    
    try:
        from agent_toolkit.shared.structured_logging import setup_logging, get_logger, LoggerMixin
        from agent_toolkit.shared.application_settings import Settings
        
        settings = Settings()
        setup_logging(settings.logging)
        
        logger = get_logger("test")
        logger.info("测试日志消息")
        
        print_success("日志系统验证通过")
        return True
    except Exception as e:
        print_error(f"日志系统验证失败: {e}")
        return False


async def verify_exception_system():
    """验证异常系统"""
    print_info("验证异常系统...")
    
    try:
        from agent_toolkit.shared.custom_exceptions import (
            AgentToolkitException,
            ValidationError,
            NotFoundError,
            DuplicateError,
            ConfigurationError,
        )
        
        # 测试异常创建
        try:
            raise NotFoundError("测试异常", resource_type="Test", resource_id="123")
        except AgentToolkitException as e:
            assert e.message == "测试异常"
        
        print_success("异常系统验证通过")
        return True
    except Exception as e:
        print_error(f"异常系统验证失败: {e}")
        return False


async def verify_metrics_system():
    """验证指标系统"""
    print_info("验证指标系统...")
    
    try:
        from agent_toolkit.observability.metrics_collector import metrics_collector
        
        collector = metrics_collector()
        metrics = collector.get_metrics()
        
        assert metrics is not None
        
        print_success("指标系统验证通过")
        return True
    except Exception as e:
        print_error(f"指标系统验证失败: {e}")
        return False


async def verify_tracing_system():
    """验证追踪系统"""
    print_info("验证追踪系统...")
    
    try:
        from agent_toolkit.observability.distributed_tracing import tracing_manager
        
        manager = tracing_manager()
        
        # 创建测试 span
        with manager.start_span("verification-test") as span:
            assert span is not None
        
        print_success("追踪系统验证通过")
        return True
    except Exception as e:
        print_error(f"追踪系统验证失败: {e}")
        return False


async def verify_orchestrator_system():
    """验证编排系统"""
    print_info("验证编排系统...")
    
    try:
        from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine
        from agent_toolkit.orchestrator.orchestration_models import (
            ToolChain,
            ChainNode,
            NodeType,
            ExecutionMode,
            ChainStatus,
        )
        
        # 创建编排引擎
        engine = OrchestrationEngine()
        assert engine is not None
        
        # 验证枚举值
        assert ChainStatus.PENDING.value == "pending"
        assert ExecutionMode.SEQUENTIAL.value == "sequential"
        
        print_success("编排系统验证通过")
        return True
    except Exception as e:
        print_error(f"编排系统验证失败: {e}")
        return False


async def verify_adapter_system():
    """验证适配器系统"""
    print_info("验证适配器系统...")
    
    try:
        from agent_toolkit.adapter.base_adapter import (
            BaseAdapter,
            AdapterType,
            AdapterConfig,
            AdapterResult,
            ExecutionStatus,
        )
        
        # 验证枚举值
        assert AdapterType.HTTP.value == "http"
        assert ExecutionStatus.SUCCESS.value == "success"
        
        # 验证配置
        config = AdapterConfig()
        assert config.timeout == 300
        
        print_success("适配器系统验证通过")
        return True
    except Exception as e:
        print_error(f"适配器系统验证失败: {e}")
        return False


async def verify_runtime_system():
    """验证运行时系统"""
    print_info("验证运行时系统...")
    
    try:
        from agent_toolkit.runtime.base_executor import (
            BaseExecutor,
            ExecutionStatus,
            ExecutionResult,
        )
        
        # 验证枚举值
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.FAILED.value == "failed"
        
        print_success("运行时系统验证通过")
        return True
    except Exception as e:
        print_error(f"运行时系统验证失败: {e}")
        return False


async def verify_main_application():
    """验证主应用"""
    print_info("验证主应用...")
    
    try:
        from agent_toolkit.main import create_app
        from agent_toolkit.shared.application_settings import Settings
        
        # 创建应用
        app = create_app(Settings())
        assert app is not None
        
        # 验证路由
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes
        
        print_success("主应用验证通过")
        return True
    except Exception as e:
        print_error(f"主应用验证失败: {e}")
        return False


async def main():
    """主函数"""
    print("\n" + "="*70)
    print("  🎯 Agent Toolkit 最终验证")
    print("="*70)
    
    print_section("核心系统验证")
    
    verification_tasks = [
        ("配置系统", verify_configuration_system),
        ("日志系统", verify_logging_system),
        ("异常系统", verify_exception_system),
        ("指标系统", verify_metrics_system),
        ("追踪系统", verify_tracing_system),
        ("编排系统", verify_orchestrator_system),
        ("适配器系统", verify_adapter_system),
        ("运行时系统", verify_runtime_system),
        ("主应用", verify_main_application),
    ]
    
    results = []
    
    for name, verify_func in verification_tasks:
        try:
            result = await verify_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"{name} 验证异常: {e}")
            results.append((name, False))
    
    # 打印总结
    print_section("验证总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 验证通过\n")
    
    for name, result in results:
        status = f"{Fore.GREEN}✓ 通过" if result else f"{Fore.RED}✗ 失败"
        print(f"  {name}: {status}")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{'='*70}")
        print(f"{Fore.GREEN}  🎉 所有验证通过！Agent Toolkit 已准备就绪！")
        print(f"{Fore.GREEN}{'='*70}\n")
        
        print(f"{Fore.CYAN}快速开始:")
        print(f"{Fore.CYAN}  1. 启动服务: python start_application.py")
        print(f"{Fore.CYAN}  2. 访问文档: http://localhost:8000/docs")
        print(f"{Fore.CYAN}  3. 健康检查: http://localhost:8000/health")
        print(f"{Fore.CYAN}  4. 指标监控: http://localhost:8000/metrics\n")
        
        return 0
    else:
        print(f"\n{Fore.RED}{'='*70}")
        print(f"{Fore.RED}  ⚠️  部分验证失败，请检查错误信息")
        print(f"{Fore.RED}{'='*70}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
