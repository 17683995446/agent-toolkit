# Agent Toolkit API 文档

## 📚 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [API 路由](#api-路由)
4. [工具仓库 API](#工具仓库-api)
5. [适配器 API](#适配器-api)
6. [运行时 API](#运行时-api)
7. [编排器 API](#编排器-api)
8. [可观测性 API](#可观测性-api)
9. [错误处理](#错误处理)
10. [最佳实践](#最佳实践)

---

## 概述

Agent Toolkit 是一个多代理编排和工具管理系统，提供统一的工具管理、适配器接口、运行时执行和编排引擎。

### 核心特性

- **工具仓库管理**: 注册、版本控制、分类管理
- **多适配器支持**: HTTP、CLI、SDK、函数调用
- **容器化执行**: Docker、Kubernetes 运行时
- **工具链编排**: DAG编排、并行/顺序执行
- **可观测性**: Prometheus指标、分布式追踪、告警

---

## 快速开始

### 启动服务

```bash
# 开发模式
python start_application.py --mode development

# 生产模式（4个worker）
python start_application.py --mode production --workers 4

# 指定端口
python start_application.py --port 8080
```

### 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## API 路由

### 基础路径

所有 API 路由都以 `/api/v1` 为前缀：

```
/api/v1/tools          - 工具仓库管理
/api/v1/adapters       - 适配器管理
/api/v1/runtime        - 运行时管理
/api/v1/orchestrator   - 编排引擎
/api/v1/observability  - 可观测性
```

### 健康检查

```bash
# 服务健康检查
GET /health

# 根路径信息
GET /
```

---

## 工具仓库 API

### 1. 工具管理

#### 创建工具

```bash
POST /api/v1/tools
Content-Type: application/json

{
  "name": "data-processor",
  "description": "数据处理工具",
  "adapter_type": "function",
  "version": "1.0.0",
  "author": "team@example.com",
  "tags": ["data", "processing"],
  "category_id": 1,
  "config": {
    "timeout": 300,
    "retries": 3
  }
}
```

#### 列出工具

```bash
GET /api/v1/tools?page=1&page_size=20&category_id=1&status=active

响应:
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### 获取工具详情

```bash
GET /api/v1/tools/{tool_id}

响应:
{
  "id": 1,
  "name": "data-processor",
  "description": "数据处理工具",
  "version": "1.0.0",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 更新工具

```bash
PUT /api/v1/tools/{tool_id}
Content-Type: application/json

{
  "description": "更新后的描述",
  "tags": ["data", "processing", "updated"]
}
```

#### 删除工具

```bash
DELETE /api/v1/tools/{tool_id}
```

### 2. 工具版本管理

```bash
# 创建新版本
POST /api/v1/tools/{tool_id}/versions
{
  "version": "2.0.0",
  "changes": "重大更新",
  "config": {...}
}

# 列出版本
GET /api/v1/tools/{tool_id}/versions

# 获取最新版本
GET /api/v1/tools/{tool_id}/versions/latest
```

### 3. 工具分类

```bash
# 创建分类
POST /api/v1/categories
{
  "name": "数据处理",
  "description": "数据处理相关工具",
  "parent_id": null
}

# 列出分类
GET /api/v1/categories

# 获取分类树
GET /api/v1/categories/tree
```

---

## 适配器 API

### 1. 适配器管理

#### 列出所有适配器

```bash
GET /api/v1/adapters

响应:
{
  "success": true,
  "data": [
    {
      "name": "http-adapter",
      "type": "http",
      "status": "active",
      "endpoint": "https://api.example.com"
    }
  ],
  "total": 5
}
```

#### 获取适配器详情

```bash
GET /api/v1/adapters/{adapter_name}
```

#### 执行适配器

```bash
POST /api/v1/adapters/{adapter_name}/execute
Content-Type: application/json

{
  "input_data": {
    "param1": "value1",
    "param2": "value2"
  },
  "context": {
    "user_id": "user123",
    "session_id": "session456"
  }
}

响应:
{
  "success": true,
  "status": "success",
  "data": {...},
  "execution_time_ms": 150,
  "metadata": {...}
}
```

#### 适配器健康检查

```bash
GET /api/v1/adapters/{adapter_name}/health

响应:
{
  "success": true,
  "healthy": true
}
```

### 2. 适配器类型

```bash
# 获取支持的适配器类型
GET /api/v1/adapters/types

响应:
{
  "success": true,
  "types": ["http", "cli", "sdk", "function"]
}
```

---

## 运行时 API

### 1. 执行管理

#### 列出执行记录

```bash
GET /api/v1/runtime/executions?status_filter=running&limit=100

响应:
{
  "success": true,
  "data": [
    {
      "execution_id": "exec-123",
      "status": "running",
      "exit_code": null,
      "execution_time_ms": 5000,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 10
}
```

#### 获取执行状态

```bash
GET /api/v1/runtime/executions/{execution_id}

响应:
{
  "success": true,
  "execution_id": "exec-123",
  "status": "completed",
  "data": {
    "stdout": "...",
    "stderr": "",
    "exit_code": 0
  },
  "execution_time_ms": 1500
}
```

#### 取消执行

```bash
POST /api/v1/runtime/executions/{execution_id}/cancel

响应:
{
  "success": true,
  "message": "Execution cancelled successfully"
}
```

### 2. 运行时状态

```bash
GET /api/v1/runtime/status

响应:
{
  "success": true,
  "status": "healthy",
  "executor": {
    "type": "docker",
    "active_executions": 5,
    "total_executions": 100
  }
}
```

---

## 编排器 API

### 1. 工具链管理

#### 创建工具链

```bash
POST /api/v1/orchestrator/toolchains
Content-Type: application/json

{
  "name": "data-pipeline",
  "tasks": [
    {
      "id": "task-1",
      "name": "fetch-data",
      "adapter_name": "http-adapter",
      "input_data": {"url": "https://api.example.com/data"},
      "dependencies": [],
      "timeout": 300,
      "retries": 3
    },
    {
      "id": "task-2",
      "name": "process-data",
      "adapter_name": "function-adapter",
      "input_data": {"function": "process"},
      "dependencies": ["task-1"],
      "timeout": 600,
      "retries": 2
    }
  ],
  "execution_mode": "sequential"
}
```

#### 列出工具链

```bash
GET /api/v1/orchestrator/toolchains

响应:
{
  "success": true,
  "data": [
    {
      "id": "chain-123",
      "name": "data-pipeline",
      "node_count": 2,
      "execution_mode": "sequential"
    }
  ],
  "total": 5
}
```

#### 获取工具链详情

```bash
GET /api/v1/orchestrator/toolchains/{name}
```

#### 执行工具链

```bash
POST /api/v1/orchestrator/toolchains/{name}/execute

响应:
{
  "success": true,
  "execution_id": "exec-456",
  "toolchain_name": "data-pipeline",
  "status": "completed",
  "task_results": [
    {
      "task_id": "task-1",
      "task_name": "fetch-data",
      "success": true,
      "status": "success",
      "data": {...},
      "execution_time_ms": 500
    },
    {
      "task_id": "task-2",
      "task_name": "process-data",
      "success": true,
      "status": "success",
      "data": {...},
      "execution_time_ms": 800
    }
  ],
  "total_execution_time_ms": 1300
}
```

### 2. 编排器状态

```bash
GET /api/v1/orchestrator/status

响应:
{
  "success": true,
  "status": "healthy",
  "active_executions": 3,
  "toolchains_count": 10
}
```

---

## 可观测性 API

### 1. 指标监控

```bash
# Prometheus 指标
GET /metrics

# 指标信息
GET /api/v1/observability/metrics/info

响应:
{
  "success": true,
  "metrics": "Prometheus metrics available at /metrics endpoint",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. 分布式追踪

```bash
# 追踪状态
GET /api/v1/observability/tracing/status

响应:
{
  "success": true,
  "enabled": true,
  "service_name": "agent-toolkit",
  "version": "0.1.0"
}

# 创建追踪 span（测试用）
POST /api/v1/observability/tracing/span
{
  "name": "test-operation",
  "attributes": {"key": "value"}
}
```

### 3. 告警管理

```bash
# 列出告警
GET /api/v1/observability/alerts

# 创建告警规则
POST /api/v1/observability/alerts/rules
{
  "name": "high-error-rate",
  "condition": "error_rate > 0.1",
  "severity": "critical",
  "actions": ["notify", "scale"]
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": {
    "error_type": "NotFoundError",
    "message": "Tool not found",
    "error_code": "TOOL_NOT_FOUND",
    "details": {
      "tool_id": 123
    }
  }
}
```

### 常见错误码

- `400` - 请求参数错误
- `401` - 未授权
- `403` - 权限不足
- `404` - 资源不存在
- `409` - 资源冲突
- `422` - 数据验证失败
- `500` - 内部服务器错误
- `503` - 服务不可用

---

## 最佳实践

### 1. 工具设计

- 使用有意义的工具名称和描述
- 合理设置超时和重试次数
- 提供完整的输入/输出 schema
- 使用标签和分类组织工具

### 2. 工具链编排

- 合理设计任务依赖关系
- 避免循环依赖
- 设置合理的超时时间
- 使用并行执行提高性能

### 3. 错误处理

- 检查所有 API 响应的状态码
- 实现重试机制处理临时错误
- 记录详细的错误日志
- 使用健康检查监控服务状态

### 4. 性能优化

- 使用连接池复用连接
- 启用缓存减少重复计算
- 监控指标识别性能瓶颈
- 合理配置 worker 数量

---

## SDK 使用示例

### Python SDK

```python
from agent_toolkit import Settings
from agent_toolkit.registry.registry_service import ToolService
from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine

# 初始化
settings = Settings()
tool_service = ToolService()
engine = OrchestrationEngine()

# 创建工具
tool = await tool_service.create_tool(
    name="my-tool",
    description="My custom tool",
    adapter_type="function"
)

# 执行工具链
result = await engine.execute_toolchain(toolchain)
print(f"执行结果: {result}")
```

---

## 许可证

MIT License
