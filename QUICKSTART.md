# Agent Toolkit 快速开始指南

## 项目概述

Agent Toolkit 是一个模块化的 Agent 工具集系统，采用三层解耦架构：
- **编排层 (Orchestration)**: 工具链编排、执行调度
- **适配层 (Adapter)**: 统一接口适配
- **运行时层 (Runtime)**: 工具执行环境

## 技术栈

- Python 3.11+
- FastAPI - Web框架
- SQLAlchemy 2.0 - 异步ORM
- Pydantic v2 - 数据验证
- Docker & Kubernetes - 容器化
- Prometheus & Grafana - 可观测性

## 项目结构

```
agent-toolkit/
├── agent_toolkit/
│   ├── shared/           # 共享组件（配置、日志、数据库）
│   ├── registry/        # 工具仓库模块
│   ├── adapter/         # 工具适配模块
│   ├── runtime/         # 工具运行时模块
│   ├── orchestrator/    # 工具编排模块
│   └── observability/   # 可观测性模块
├── configs/             # 配置文件
├── charts/              # Helm Charts
└── scripts/             # 运维脚本
```

## 安装

### 方式一：使用 pip（开发模式）

```bash
# 克隆项目
git clone https://github.com/agent-toolkit/agent-toolkit.git
cd agent-toolkit

# 安装依赖
pip install -e .

# 或安装所有依赖
pip install -e ".[dev,database,observability]"
```

### 方式二：使用 Poetry

```bash
# 安装 Poetry（如果没有）
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

## 运行服务

### 1. 工具仓库服务 (Registry)

```bash
# 使用 uvicorn
uvicorn agent_toolkit.registry.api:app --reload --port 8000

# 或使用 CLI
agent-toolkit-registry serve --port 8000
```

### 2. 适配器服务 (Adapter)

```bash
uvicorn agent_toolkit.adapter.api:app --reload --port 8001
```

### 3. 运行时服务 (Runtime)

```bash
uvicorn agent_toolkit.runtime.api:app --reload --port 8002
```

### 4. 编排器服务 (Orchestrator)

```bash
uvicorn agent_toolkit.orchestrator.api:app --reload --port 8003
```

### 5. 可观测性服务 (Observability)

```bash
uvicorn agent_toolkit.observability.api:app --reload --port 8004
```

## Docker 部署

### 构建镜像

```bash
# 构建所有镜像
docker-compose build

# 或单独构建
docker build -f Dockerfile.registry -t agent-toolkit-registry:latest .
```

### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## Kubernetes 部署

### 使用 Helm

```bash
# 添加 Helm 仓库
helm repo add agent-toolkit https://charts.agent-toolkit.dev
helm repo update

# 安装
helm install agent-toolkit agent-toolkit/agent-toolkit \
  --namespace agent-toolkit \
  --create-namespace

# 自定义配置
helm install agent-toolkit agent-toolkit/agent-toolkit \
  --namespace agent-toolkit \
  --set registry.port=8000 \
  --set registry.replicas=3
```

## 测试

### 运行所有测试

```bash
# 使用 pytest
pytest

# 带覆盖率
pytest --cov=agent_toolkit --cov-report=html

# 只运行单元测试
pytest tests/unit/

# 只运行集成测试
pytest tests/integration/
```

### 运行特定模块测试

```bash
# Registry 模块测试
pytest agent_toolkit/registry/tests/

# Adapter 模块测试
pytest agent_toolkit/adapter/tests/

# Runtime 模块测试
pytest agent_toolkit/runtime/tests/
```

## API 文档

启动服务后，访问自动生成的 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

## 配置

### 环境变量

```bash
# 数据库配置
AGENT_TOOLKIT_DATABASE__URL=postgresql+asyncpg://user:pass@localhost/db

# Redis 配置
AGENT_TOOLKIT_REDIS__HOST=localhost
AGENT_TOOLKIT_REDIS__PORT=6379

# 日志配置
AGENT_TOOLKIT_LOGGING__LEVEL=DEBUG

# 环境模式
AGENT_TOOLKIT_ENVIRONMENT=development
```

### 配置文件

编辑 `configs/development.yaml` 或 `configs/production.yaml` 来配置服务。

## CLI 命令

### 工具仓库 CLI

```bash
# 列出工具
agent-toolkit-registry tool list

# 查看工具详情
agent-toolkit-registry tool info <tool-name>

# 安装工具
agent-toolkit-registry tool install <tool-name>

# 搜索工具
agent-toolkit-registry tool search <query>
```

### 适配器 CLI

```bash
# 列出适配器
agent-toolkit-adapter adapter list

# 测试适配器
agent-toolkit-adapter adapter test <adapter-name>
```

### 运行时 CLI

```bash
# 列出执行器
agent-toolkit-runtime executor list

# 查看执行状态
agent-toolkit-runtime execution status <execution-id>
```

## 开发

### 代码规范

```bash
# 代码格式化
black agent_toolkit/

# Import 排序
isort agent_toolkit/

# Linting
ruff check agent_toolkit/

# 类型检查
mypy agent_toolkit/
```

### 提交代码

```bash
# 安装 pre-commit hooks
./scripts/setup-hooks.sh

# 提交
git add .
git commit -m "feat: add new feature"
```

## 监控

### Prometheus 指标

访问 `http://localhost:8004/metrics` 查看 Prometheus 指标。

### Grafana 仪表盘

访问 `http://localhost:3000` 查看预配置的仪表盘。

### 日志聚合

使用 Loki 查看日志：`http://localhost:3100`

### 链路追踪

使用 Jaeger 查看追踪：`http://localhost:16686`

## 故障排查

### 数据库连接问题

```bash
# 检查数据库连接
psql $DATABASE_URL
```

### Redis 连接问题

```bash
# 检查 Redis
redis-cli ping
```

### 查看服务日志

```bash
docker-compose logs -f registry
```

## 下一步

- 阅读 [完整文档](./docs/)
- 查看 [API 参考](./docs/api/)
- 了解 [架构设计](./docs/architecture.md)
- 查看 [示例](./examples/)

## 许可证

Apache 2.0
