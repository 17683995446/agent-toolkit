#!/usr/bin/env python3
"""
Agent Toolkit 生产环境启动脚本
支持多worker、自动重载、配置管理
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from agent_toolkit.shared.application_settings import Settings, get_settings
from agent_toolkit.shared.structured_logging import setup_logging, get_logger


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Agent Toolkit - 多代理编排和工具管理系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 开发模式启动
  python start_application.py --mode development
  
  # 生产模式启动（4个worker）
  python start_application.py --mode production --workers 4
  
  # 指定配置文件
  python start_application.py --config /path/to/config.yaml
  
  # 指定端口
  python start_application.py --port 8080
        """
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["development", "staging", "production"],
        default="development",
        help="运行模式 (default: development)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="绑定主机地址 (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="绑定端口 (default: 8000)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数量 (default: 1)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="配置文件路径 (YAML格式)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载 (仅开发模式)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        default="info",
        help="日志级别 (default: info)"
    )
    
    return parser.parse_args()


def display_startup_info(settings, args):
    """显示启动信息"""
    print("\n" + "="*70)
    print("  🚀 Agent Toolkit 启动中...")
    print("="*70)
    print(f"  📦 版本:        0.1.0")
    print(f"  🌍 环境:        {settings.environment}")
    print(f"  🌐 服务地址:    http://{args.host or settings.server.host}:{args.port or settings.server.port}")
    print(f"  📚 API 文档:    http://{args.host or settings.server.host}:{args.port or settings.server.port}/docs")
    print(f"  📊 指标监控:    http://{args.host or settings.server.host}:{args.port or settings.server.port}/metrics")
    print(f"  🔧 工作进程:    {args.workers}")
    print(f"  📝 日志级别:    {args.log_level}")
    print("="*70)
    print("\n  可用的 API 路由:")
    print("  ├─ /api/v1/tools          - 工具仓库管理")
    print("  ├─ /api/v1/adapters       - 适配器管理")
    print("  ├─ /api/v1/runtime        - 运行时管理")
    print("  ├─ /api/v1/orchestrator   - 编排引擎")
    print("  └─ /api/v1/observability  - 可观测性")
    print("\n" + "="*70 + "\n")


def main():
    """主函数"""
    args = parse_arguments()
    
    # 加载配置
    settings_kwargs = {}
    if args.config:
        settings_kwargs["config_file"] = args.config
    
    settings = Settings(**settings_kwargs)
    
    # 覆盖环境设置
    if args.mode:
        settings.environment = args.mode
    
    # 确定主机和端口
    host = args.host or settings.server.host
    port = args.port or settings.server.port
    
    # 初始化日志
    setup_logging(settings.logging)
    logger = get_logger(__name__)
    
    # 显示启动信息
    display_startup_info(settings, args)
    
    # 启动配置
    uvicorn_config = {
        "app": "agent_toolkit.main:app",
        "host": host,
        "port": port,
        "log_level": args.log_level,
        "access_log": True,
    }
    
    # 开发模式配置
    if args.mode == "development" or args.reload:
        uvicorn_config.update({
            "reload": True,
            "reload_dirs": [str(project_root)],
            "workers": 1,
        })
    else:
        # 生产模式配置
        uvicorn_config.update({
            "workers": args.workers,
            "reload": False,
        })
    
    # 启动服务
    try:
        logger.info(
            "Starting Agent Toolkit server",
            environment=settings.environment,
            host=host,
            port=port,
            workers=uvicorn_config.get("workers", 1)
        )
        
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        print("\n\n👋 Agent Toolkit 已停止\n")
        
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        print(f"\n❌ 启动失败: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
