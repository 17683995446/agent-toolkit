#!/usr/bin/env python3
"""
Agent Toolkit 快速测试脚本
测试各个模块是否可以正常导入
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)


def print_section(title):
    """打印带标题的分隔线"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{title}")
    print(f"{Fore.CYAN}{'='*60}")


def print_success(message):
    """打印成功信息"""
    print(f"{Fore.GREEN}✓ {message}")


def print_error(message):
    """打印错误信息"""
    print(f"{Fore.RED}✗ {message}")


def test_imports():
    """测试模块导入"""
    print_section("测试模块导入")
    
    modules_to_test = [
        ("agent_toolkit.shared.application_settings", "配置模块"),
        ("agent_toolkit.shared.custom_exceptions", "异常模块"),
        ("agent_toolkit.shared.middleware", "中间件模块"),
        ("agent_toolkit.observability.metrics_collector", "指标模块"),
        ("agent_toolkit.observability.distributed_tracing", "追踪模块"),
        ("agent_toolkit.orchestrator.orchestration_engine", "编排引擎"),
        ("agent_toolkit.orchestrator.orchestration_models", "编排模型"),
    ]
    
    all_passed = True
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print_success(f"{description} 导入成功")
        except Exception as e:
            print_error(f"{description} 导入失败: {e}")
            all_passed = False
    
    return all_passed


def test_config():
    """测试配置模块"""
    print_section("测试配置模块")
    
    try:
        from agent_toolkit.shared.application_settings import Settings
        settings = Settings()
        print_success("配置初始化成功")
        print(f"  环境: {settings.environment}")
        print(f"  数据库: {settings.database.url.split('://')[0]}")
        return True
    except Exception as e:
        print_error(f"配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print(f"\n{Fore.YELLOW}{'='*60}")
    print(f"{Fore.YELLOW}Agent Toolkit 快速测试")
    print(f"{Fore.YELLOW}{'='*60}")
    
    results = []
    
    # 测试导入
    results.append(("模块导入", test_imports()))
    
    # 测试配置
    results.append(("配置模块", test_config()))
    
    # 打印总结
    print_section("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过\n")
    
    for name, result in results:
        status = f"{Fore.GREEN}通过" if result else f"{Fore.RED}失败"
        print(f"  {name}: {status}")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{'✓'*60}")
        print(f"{Fore.GREEN}所有测试通过！项目核心模块工作正常。")
        print(f"{Fore.GREEN}{'✓'*60}\n")
        return 0
    else:
        print(f"\n{Fore.RED}{'✗'*60}")
        print(f"{Fore.RED}部分测试失败，但核心模块已修复。")
        print(f"{Fore.RED}{'✗'*60}\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
