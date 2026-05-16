#!/usr/bin/env python3
"""
全面修复所有剩余的导入路径问题
"""

import os
import re
from pathlib import Path

# 定义所有模块的旧文件名到新文件名的映射
MODULE_MAPPINGS = {
    'shared': {
        'config': 'application_settings',
        'database': 'database_connection',
        'exceptions': 'custom_exceptions',
        'logging': 'structured_logging',
    },
    'adapter': {
        'base': 'base_adapter',
        'api': 'adapter_api_routes',
        'cli': 'adapter_cli_commands',
        'registry': 'adapter_registry',
        'cli_adapter': 'cli_adapter_implementation',
        'function_adapter': 'function_adapter_implementation',
        'http_adapter': 'http_adapter_implementation',
        'sdk_adapter': 'sdk_adapter_implementation',
    },
    'runtime': {
        'base': 'base_executor',
        'api': 'runtime_api_routes',
        'cli': 'runtime_cli_commands',
        'docker_executor': 'docker_executor_implementation',
        'kubernetes_executor': 'kubernetes_executor_implementation',
        'lifecycle': 'execution_lifecycle_manager',
        'sandbox': 'sandbox_manager',
    },
    'orchestrator': {
        'api': 'orchestrator_api_routes',
        'cli': 'orchestrator_cli_commands',
        'engine': 'orchestration_engine',
        'executor': 'task_executor',
        'flow_control': 'flow_control_strategy',
        'models': 'orchestration_models',
        'scheduler': 'task_scheduler',
    },
    'observability': {
        'api': 'observability_api_routes',
        'cli': 'observability_cli_commands',
        'logging': 'observability_logging',
        'metrics': 'metrics_collector',
        'tracing': 'distributed_tracing',
        'alerts': 'alert_manager',
    },
    'registry': {
        'api': 'registry_api_routes',
        'cli': 'registry_cli_commands',
        'config': 'registry_config',
        'main': 'registry_main',
        'models': 'registry_models',
        'schemas': 'registry_schemas',
        'service': 'registry_service',
        'repository': 'registry_repository',
    },
}

def update_imports_in_file(file_path):
    """更新单个文件中的所有导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 对每个模块进行替换
        for module_name, file_mappings in MODULE_MAPPINGS.items():
            for old_name, new_name in file_mappings.items():
                # 匹配 from agent_toolkit.module.old_name import
                pattern = rf'from agent_toolkit\.{module_name}\.{old_name} import'
                replacement = rf'from agent_toolkit.{module_name}.{new_name} import'
                content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error updating {file_path}: {e}")
        return False

def main():
    """主函数"""
    project_root = Path('/workspace/agent-toolkit')
    
    # 扫描所有 Python 文件
    python_files = list(project_root.rglob('*.py'))
    
    updated_count = 0
    for file_path in python_files:
        # 跳过 __pycache__ 目录
        if '__pycache__' in str(file_path):
            continue
        
        # 跳过更新脚本本身
        if 'update_' in file_path.name:
            continue
        
        if update_imports_in_file(file_path):
            updated_count += 1
    
    print(f"\n总计更新了 {updated_count} 个文件")

if __name__ == "__main__":
    main()
