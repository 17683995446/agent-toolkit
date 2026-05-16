# 环境配置示例

本目录包含 Agent Toolkit 的环境配置文件示例。

## 文件说明

### 1. development.yaml
开发环境配置，用于本地开发。

### 2. staging.yaml
预发布环境配置，用于测试。

### 3. production.yaml
生产环境配置，用于正式部署。

## 配置优先级

Agent Toolkit 使用以下配置优先级（从高到低）：

1. **环境变量** (AGENT_TOOLKIT_* 前缀)
2. **命令行参数** (--config)
3. **YAML 配置文件** (根据 environment 环境变量选择)
4. **默认值** (代码中的默认值)

## 环境变量示例

```bash
# 数据库配置
export AGENT_TOOLKIT_DATABASE__URL="postgresql+asyncpg://user:pass@localhost:5432/agent_toolkit"

# Redis 配置
export AGENT_TOOLKIT_REDIS__HOST="localhost"
export AGENT_TOOLKIT_REDIS__PORT="6379"
export AGENT_TOOLKIT_REDIS__PASSWORD="your_password"

# 安全配置
export AGENT_TOOLKIT_SECURITY__SECRET_KEY="your-secret-key-change-in-production"

# 日志配置
export AGENT_TOOLKIT_LOGGING__LEVEL="DEBUG"
export AGENT_TOOLKIT_LOGGING__FORMAT="text"

# 环境模式
export AGENT_TOOLKIT_ENVIRONMENT="development"
```

## 常用配置项

### 数据库配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| database.url | 数据库连接URL | sqlite+aiosqlite:///./agent_toolkit.db |
| database.pool_size | 连接池大小 | 10 |
| database.max_overflow | 最大溢出连接 | 20 |
| database.echo | 是否打印SQL | false |

### Redis 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| redis.host | Redis主机 | localhost |
| redis.port | Redis端口 | 6379 |
| redis.db | 数据库编号 | 0 |
| redis.password | 密码 | 无 |
| redis.ssl | 是否使用SSL | false |

### 运行时配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| runtime.executor_type | 执行器类型 | docker |
| runtime.default_timeout | 默认超时时间 | 300秒 |
| runtime.max_concurrent_executions | 最大并发执行数 | 100 |

### 安全配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| security.secret_key | 密钥 | change-me-in-production |
| security.algorithm | JWT算法 | HS256 |
| security.access_token_expire_minutes | Token过期时间 | 30分钟 |

## 配置验证

启动应用前可以验证配置：

```python
from agent_toolkit.shared.config import get_settings

settings = get_settings()
print(f"Environment: {settings.environment}")
print(f"Database URL: {settings.get_database_url()}")
print(f"Redis URL: {settings.get_redis_url()}")
```
