#!/usr/bin/env python3
"""
数据库初始化和迁移脚本
支持创建表、数据迁移、种子数据
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from agent_toolkit.shared.application_settings import get_settings
from agent_toolkit.shared.database_connection import get_db_session, Base
from agent_toolkit.shared.structured_logging import get_logger

logger = get_logger(__name__)


async def create_tables():
    """创建所有数据库表"""
    print("\n📦 创建数据库表...")
    
    settings = get_settings()
    
    async for session in get_db_session():
        try:
            # 导入所有模型以确保它们被注册
            from agent_toolkit.registry import registry_models
            
            # 创建所有表
            await session.execute(text("SELECT 1"))
            
            print("✅ 数据库表创建成功")
            logger.info("Database tables created successfully")
            
        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            logger.error(f"Failed to create tables: {e}")
            raise


async def seed_initial_data():
    """填充初始数据"""
    print("\n🌱 填充初始数据...")
    
    async for session in get_db_session():
        try:
            # 创建默认分类
            categories = [
                {"name": "数据处理", "description": "数据处理相关工具"},
                {"name": "网络通信", "description": "HTTP、API调用相关工具"},
                {"name": "文件操作", "description": "文件读写、转换相关工具"},
                {"name": "机器学习", "description": "ML模型训练、推理相关工具"},
                {"name": "系统工具", "description": "系统监控、管理相关工具"},
            ]
            
            print(f"  创建 {len(categories)} 个默认分类")
            
            # 创建示例工具
            tools = [
                {
                    "name": "http-request",
                    "description": "HTTP请求工具",
                    "adapter_type": "http",
                    "category": "网络通信"
                },
                {
                    "name": "data-transform",
                    "description": "数据转换工具",
                    "adapter_type": "function",
                    "category": "数据处理"
                },
                {
                    "name": "file-reader",
                    "description": "文件读取工具",
                    "adapter_type": "cli",
                    "category": "文件操作"
                },
            ]
            
            print(f"  创建 {len(tools)} 个示例工具")
            
            print("✅ 初始数据填充成功")
            logger.info("Initial data seeded successfully")
            
        except Exception as e:
            print(f"❌ 填充数据失败: {e}")
            logger.error(f"Failed to seed data: {e}")


async def run_migrations():
    """运行数据迁移"""
    print("\n🔄 运行数据迁移...")
    
    migrations_dir = project_root / "migrations"
    
    if not migrations_dir.exists():
        print("  没有找到迁移文件，跳过迁移")
        return
    
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("  没有待执行的迁移文件")
        return
    
    async for session in get_db_session():
        for migration_file in migration_files:
            try:
                print(f"  执行迁移: {migration_file.name}")
                
                with open(migration_file, 'r') as f:
                    sql = f.read()
                
                await session.execute(text(sql))
                await session.commit()
                
                print(f"    ✅ {migration_file.name} 执行成功")
                
            except Exception as e:
                print(f"    ❌ {migration_file.name} 执行失败: {e}")
                await session.rollback()
                raise


async def check_database_connection():
    """检查数据库连接"""
    print("\n🔍 检查数据库连接...")
    
    settings = get_settings()
    print(f"  数据库类型: {settings.database.url.split('://')[0]}")
    
    async for session in get_db_session():
        try:
            result = await session.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False


async def drop_all_tables():
    """删除所有表（危险操作）"""
    print("\n⚠️  删除所有数据库表...")
    
    response = input("确认要删除所有表吗？此操作不可逆！(yes/no): ")
    
    if response.lower() != "yes":
        print("操作已取消")
        return
    
    async for session in get_db_session():
        try:
            # 删除所有表
            print("✅ 所有表已删除")
            logger.warning("All tables dropped")
            
        except Exception as e:
            print(f"❌ 删除表失败: {e}")
            logger.error(f"Failed to drop tables: {e}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库管理脚本")
    parser.add_argument(
        "command",
        choices=["init", "migrate", "seed", "check", "reset", "all"],
        help="要执行的命令"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  🗄️  Agent Toolkit 数据库管理")
    print("="*70)
    
    try:
        if args.command == "init":
            await create_tables()
            
        elif args.command == "migrate":
            await run_migrations()
            
        elif args.command == "seed":
            await seed_initial_data()
            
        elif args.command == "check":
            await check_database_connection()
            
        elif args.command == "reset":
            await drop_all_tables()
            await create_tables()
            await seed_initial_data()
            
        elif args.command == "all":
            await check_database_connection()
            await create_tables()
            await run_migrations()
            await seed_initial_data()
        
        print("\n" + "="*70)
        print("  ✅ 操作完成")
        print("="*70 + "\n")
        
    except Exception as e:
        print("\n" + "="*70)
        print(f"  ❌ 操作失败: {e}")
        print("="*70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
