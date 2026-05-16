# Agent Toolkit 项目贡献指南

感谢您考虑为 Agent Toolkit 项目做出贡献！

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/agent-toolkit/agent-toolkit.git
cd agent-toolkit
```

### 2. 创建虚拟环境

```bash
# 使用 Python 内置模块
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 或使用 poetry
poetry install
poetry shell
```

### 3. 安装开发依赖

```bash
# 使用 pip
pip install -e ".[dev,database,observability]"

# 或使用 poetry
poetry install --with dev,docs
```

### 4. 设置 pre-commit hooks

```bash
pre-commit install
pre-commit run --all-files
```

### 5. 运行开发服务器

```bash
# Registry 服务
uvicorn agent_toolkit.registry.main:app --reload --port 8000

# Adapter 服务
uvicorn agent_toolkit.adapter.api:app --reload --port 8001
```

## 代码规范

### Python 代码规范

- 遵循 PEP 8
- 使用 type hints
- 使用 docstrings
- 遵循项目命名约定

### 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 模块 | 小写下划线 | `tool_registry.py` |
| 类 | 大驼峰 | `ToolRegistry` |
| 函数 | 小写下划线 | `get_tool()` |
| 常量 | 全大写下划线 | `MAX_RETRIES` |
| 私有方法 | 前导下划线 | `_private_method()` |

### Import 顺序

1. 标准库
2. 第三方库
3. 本地应用
4. 相关导入

使用 `isort` 自动排序。

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest agent_toolkit/registry/tests/

# 运行带覆盖率的测试
pytest --cov=agent_toolkit --cov-report=html

# 运行特定测试
pytest -k "test_tool_creation"
```

### 编写测试

```python
import pytest
from agent_toolkit.registry.models import Tool

@pytest.mark.asyncio
async def test_tool_creation(async_session):
    """测试创建工具"""
    tool = Tool(name="test_tool", ...)
    async_session.add(tool)
    await async_session.commit()
    
    assert tool.id is not None
    assert tool.name == "test_tool"
```

## Git 工作流

### 分支命名

- `feature/` - 新功能
- `fix/` - Bug 修复
- `docs/` - 文档更新
- `refactor/` - 代码重构
- `test/` - 测试相关

示例：
- `feature/user-authentication`
- `fix/tool-execution-timeout`
- `docs/api-documentation`

### 提交规范

使用 Conventional Commits：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

类型：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

示例：
```
feat(registry): add tool versioning support

- Add create_version method
- Add list_versions method
- Update API endpoints

Closes #123
```

### Pull Request 流程

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 确保所有测试通过
5. 运行 linting 和类型检查
6. 提交 PR
7. 等待代码审查
8. 合并到主分支

## 文档

### API 文档

API 文档使用 docstrings：

```python
async def get_tool(tool_id: int) -> Tool:
    """获取工具详情。

    Args:
        tool_id: 工具ID

    Returns:
        Tool: 工具对象

    Raises:
        NotFoundError: 如果工具不存在
    """
```

### README 文档

更新 README 时：
- 保持格式一致
- 包含使用示例
- 说明配置选项
- 提供故障排除

## 许可

通过提交代码，您同意您的贡献将根据 Apache 2.0 许可证获得许可。
