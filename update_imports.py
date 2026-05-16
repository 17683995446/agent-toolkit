#!/usr/bin/env python3
"""
批量更新导入路径脚本
将旧的导入路径更新为新的文件名
"""

import os
import re
from pathlib import Path

# 定义旧文件名到新文件名的映射
OLD_TO_NEW = {
    'config': 'application_settings',
    'database': 'database_connection',
    'exceptions': 'custom_exceptions',
    'logging': 'structured_logging',
}

def update_imports_in_file(file_path):
    """更新单个文件中的导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换导入语句
        for old_name, new_name in OLD_TO_NEW.items():
            # 匹配 from agent_toolkit.xxx import ... from agent_toolkit.xxx.old_name import
            pattern = rf'from agent_toolkit\.(\w+)\.{old_name} import'
            replacement = rf'from agent_toolkit.\1.{new_name} import'
            content = re.sub(pattern, replacement, content)
            
            # 匹配 import agent_toolkit.xxx.old_name
            pattern = rf'import agent_toolkit\.(\w+)\.{old_name}'
            replacement = rf'import agent_toolkit.\1.{new_name}'
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
        
        # 跳过已重命名的文件本身
        if file_path.name in ['application_settings.py', 'database_connection.py', 
                             'custom_exceptions.py', 'structured_logging.py']:
            continue
        
        if update_imports_in_file(file_path):
            updated_count += 1
    
    print(f"\n总计更新了 {updated_count} 个文件")

if __name__ == "__main__":
    main()
