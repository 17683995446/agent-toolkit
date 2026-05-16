#!/usr/bin/env python3
"""
Agent Toolkit 运行脚本
启动完整的 Agent Toolkit 服务
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import asyncio
import argparse
import uvicorn

from agent_toolkit.shared.application_settings import Settings
from agent_toolkit.shared.structured_logging import setup_logging, get_logger


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Agent Toolkit - 多代理编排和工具管理系统"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="绑定的主机地址 (默认从配置文件读取)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="绑定的端口号 (默认从配置文件读取)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="配置文件路径 (YAML 格式)"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="启用开发模式 (自动重载)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数量"
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 初始化配置
    settings_kwargs = {}
    if args.config:
        settings_kwargs["config_file"] = args.config
    
    settings = Settings(**settings_kwargs)
    
    # 确定主机和端口
    host = args.host or settings.server.host
    port = args.port or settings.server.port
    
    # 初始化日志
    setup_logging(settings.logging)
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Agent Toolkit 启动中...")
    logger.info(f"环境: {settings.environment}")
    logger.info(f"服务地址: http://{host}:{port}")
    logger.info(f"API 文档: http://{host}:{port}/docs")
    logger.info(f"指标监控: http://{host}:{port}/metrics")
    logger.info("=" * 60)
    
    # 启动服务
    uvicorn.run(
        "agent_toolkit.main:app",
        host=host,
        port=port,
        reload=args.dev or settings.environment == "development",
        workers=args.workers if not args.dev else 1,
        access_log=True,
        log_level=settings.logging.level.lower()
    )


if __name__ == "__main__":
    main()
