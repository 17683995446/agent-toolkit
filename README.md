# Agent Toolkit

现代化 Agent 工具集系统 - 模块化的多 Agent 编排和工具管理平台

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![CI](https://github.com/agent-toolkit/agent-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-toolkit/agent-toolkit/actions)

## 项目概述

Agent Toolkit 是一个高度模块化的 Agent 工具集系统，采用**三层解耦架构**设计，提供工具的统一管理、标准化适配、灵活编排和全链路可观测性。

### 核心特性

- **🔧 工具仓库** - 工具元数据管理、版本控制、分类检索、依赖解析
- **🔄 适配层** - HTTP/CLI/SDK/本地函数统一接口适配
- **⚡ 运行时** - Docker/Kubernetes 安全沙箱执行
- **🔗 编排引擎** - 工具链可视化编排、并行/串行执行
- **📊 可观测性** - Prometheus 指标、OpenTelemetry 链路追踪

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     编排层 (Orchestration)                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ 工具发现 │  │ 权限控制 │  │ 流量控制 │  │ 错误重试 │     │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ 工具链编排│  │ 并行执行 │  │ 结果聚合 │  │ 日志追踪 │     │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
├───────────────────────────────────────────────────────────┤
│                     适配层 (Adapter)                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ HTTP适配 │  │ CLI适配  │  │ SDK适配  │  │ 本地函数 │     │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ 输入转换 │  │ 输出标准化│  │ 异常统一 │  │ 认证代理 │     │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
├───────────────────────────────────────────────────────────┤
│                     工具层 (Tools)                         │
│  搜索类  代码类  文档类  数据类  多媒体类  系统类  通信类 │
│  (基于成熟开源项目集成，非自研核心功能)                      │
└───────────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **基础框架** | FastAPI + Pydantic v2 | 高性能 Web 框架 + 数据验证 |
| **异步编程** | Python 3.11+ asyncio | 异步 I/O 优先 |
| **数据库** | PostgreSQL + Redis | 主数据库 + 缓存/队列 |
| **容器化** | Docker + Kubernetes | 沙箱隔离 + 编排部署 |
| **可观测性** | Prometheus + Grafana + Jaeger | 指标 + 日志 + 链路追踪 |
| **任务队列** | Celery + Redis | 异步任务执行 |

## 快速开始

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/agent-toolkit/agent-toolkit.git
cd agent-toolkit

# 使用 pip 安装
pip install -e .

# 或使用 Poetry
poetry install
```

### 启动服务

```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d

# 或手动启动各个服务
uvicorn agent_toolkit.registry.api:app --reload --port 8000
```

### 运行测试

```bash
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=agent_toolkit --cov-report=html
```

## 项目结构

```
agent-toolkit/
├── agent_toolkit/
│   ├── shared/            # 共享组件（配置、日志、数据库、异常）
│   ├── registry/         # 工具仓库模块
│   ├── adapter/          # 工具适配模块
│   ├── runtime/          # 工具运行时模块
│   ├── orchestrator/     # 工具编排模块
│   ├── observability/    # 可观测性模块
│   └── examples/         # 使用示例
├── configs/              # 配置文件
├── charts/               # Helm Charts
├── scripts/              # 运维脚本
├── tests/                # 测试套件
└── docs/                 # 文档
```

## 核心模块

### 1. 工具仓库 (Registry)

工具元数据管理系统，支持：

- 工具 CRUD 操作
- 版本管理
- 分类和标签管理
- 全文搜索
- 依赖解析

```python
from agent_toolkit.registry.service import ToolService
from agent_toolkit.registry.schemas import ToolCreate

# 注册新工具
tool = await service.create_tool(ToolCreate(
    name="weather_api",
    description="天气查询工具",
    version="1.0.0",
    adapter_type="http",
    adapter_config={"base_url": "https://api.weather.com"}
))
```

### 2. 适配器 (Adapter)

统一工具接口适配层，支持：

- **HTTP 适配器** - REST API 调用
- **CLI 适配器** - 命令行工具执行
- **SDK 适配器** - Python SDK 集成
- **函数适配器** - 本地函数调用

```python
from agent_toolkit.adapter.http_adapter import HTTPAdapter, HTTPAdapterConfig

# 使用 HTTP 适配器
adapter = HTTPAdapter(HTTPAdapterConfig(
    base_url="https://api.example.com",
    endpoint="/search",
    method="GET"
))
result = await adapter.execute({"query": "Python"})
```

### 3. 运行时 (Runtime)

安全的工具执行环境：

- **Docker 执行器** - 容器化隔离
- **Kubernetes 执行器** - Pod 级隔离
- **沙箱管理** - gVisor/seccomp
- **资源管理** - CPU/内存/磁盘限制
- **生命周期钩子** - 完整生命周期事件

```python
from agent_toolkit.runtime.docker_executor import DockerExecutor, DockerExecutorConfig

executor = DockerExecutor(DockerExecutorConfig(
    image="python:3.12-slim",
    timeout=60
))
result = await executor.execute("my_tool", {"input": "data"})
```

### 4. 编排器 (Orchestrator)

复杂工具链编排引擎：

- **DAG 编排** - 有向无环图执行
- **并行执行** - 多任务并行处理
- **条件分支** - 动态执行路径
- **调度器** - Cron/Interval 定时执行

```python
from agent_toolkit.orchestrator.engine import OrchestrationEngine
from agent_toolkit.orchestrator.models import ToolChain, ExecutionMode

chain = ToolChain(
    id="my_chain",
    name="数据处理链",
    execution_mode=ExecutionMode.SEQUENTIAL,
    nodes=[...],
    edges=[...]
)
context = await engine.execute_chain(chain, {"initial": "data"})
```

### 5. 可观测性 (Observability)

完整的监控和追踪：

- **Prometheus 指标** - 执行计数、延迟分布
- **OpenTelemetry 追踪** - 分布式链路追踪
- **结构化日志** - JSON 格式日志聚合
- **告警管理** - 自定义告警规则

```python
from agent_toolkit.observability.metrics import metrics_collector

collector = metrics_collector()
collector.record_execution(
    tool_name="my_tool",
    status="success",
    duration_ms=150.5
)
```

## API 文档

启动服务后访问自动生成的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## CLI 命令

```bash
# 工具仓库 CLI
agent-toolkit-registry tool list
agent-toolkit-registry tool create --name my_tool
agent-toolkit-registry tool info 1

# 编排器 CLI
agent-toolkit-orchestrator chain list
agent-toolkit-orchestrator chain execute my_chain

# 可观测性 CLI
agent-toolkit-observability metrics
agent-toolkit-observability health
```

## 部署方式

### Docker Compose (开发/测试)

```bash
docker-compose up -d
```

### Kubernetes (生产)

```bash
helm install agent-toolkit ./charts/agent-toolkit \
  --namespace agent-toolkit \
  --create-namespace \
  --set registry.replicas=3
```

## 配置管理

支持多环境配置和 YAML 文件：

```bash
# 环境变量
export AGENT_TOOLKIT_DATABASE__URL="postgresql://..."
export AGENT_TOOLKIT_REDIS__HOST="redis-host"

# 或使用配置文件
export AGENT_TOOLKIT_ENVIRONMENT=production
```

## 测试

```bash
# 运行所有测试
pytest

# 单元测试
pytest agent_toolkit/registry/tests/

# 集成测试
pytest tests/integration/

# 带覆盖率
pytest --cov=agent_toolkit --cov-report=term-missing
```

## 贡献指南

欢迎贡献代码！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与项目开发。

## 文档

- [快速开始指南](QUICKSTART.md)
- [部署指南](DEPLOYMENT.md)
- [贡献指南](CONTRIBUTING.md)
- [实施计划](AGENT_TOOLKIT_IMPLEMENTATION_PLAN.md)

## 路线图

- [ ] v0.2.0 - 完善适配器模板库
- [ ] v0.3.0 - 可视化工具链编辑器
- [ ] v1.0.0 - 生产就绪版本
- [ ] v1.1.0 - 多租户支持

## 许可证

本项目基于 Apache 2.0 许可证开源 - 详见 [LICENSE](LICENSE) 文件。

## 联系方式

- GitHub Issues: https://github.com/agent-toolkit/agent-toolkit/issues
- 邮箱: team@agent-toolkit.dev
