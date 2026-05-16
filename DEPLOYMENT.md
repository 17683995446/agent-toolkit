# Agent Toolkit 部署指南

本指南提供在各种环境中部署 Agent Toolkit 的说明。

## 部署选项

### 1. Docker Compose (开发/测试)

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f registry

# 停止服务
docker-compose down
```

### 2. Kubernetes (生产)

使用 Helm 部署：

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
  --set registry.replicas=3 \
  --set registry.resources.limits.cpu=2 \
  --set registry.resources.limits.memory=2Gi
```

## 生产环境配置

### 数据库

生产环境建议使用 PostgreSQL：

```yaml
database:
  url: "postgresql+asyncpg://user:pass@db.example.com:5432/agent_toolkit"
  pool_size: 20
  max_overflow: 40
```

### Redis

```yaml
redis:
  host: "redis.example.com"
  port: 6379
  password: "${REDIS_PASSWORD}"
  ssl: true
  max_connections: 100
```

### 安全配置

```yaml
security:
  secret_key: "${SECRET_KEY}"  # 必须设置强密钥
  algorithm: "HS256"
  access_token_expire_minutes: 30
```

### 资源限制

```yaml
resources:
  limits:
    cpu: "2"
    memory: "2Gi"
  requests:
    cpu: "500m"
    memory: "1Gi"
```

## 健康检查

所有服务提供健康检查端点：

- `/health` - 基本健康检查
- `/ready` - 就绪检查
- `/metrics` - Prometheus 指标

## 监控

### Prometheus

配置 Prometheus 抓取指标：

```yaml
scrape_configs:
  - job_name: 'agent-toolkit'
    static_configs:
      - targets: ['registry:8000', 'adapter:8001']
    metrics_path: '/metrics'
```

### Grafana

导入预配置的仪表盘：
- 工具执行统计
- 适配器请求量
- 系统资源使用
- 错误率监控

## 日志管理

### 结构化日志

所有服务输出 JSON 格式日志：

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Tool executed successfully",
  "tool_id": "weather_api",
  "execution_time_ms": 150.5
}
```

### 日志聚合

使用 Loki 或 ELK Stack 聚合日志：

```yaml
logging:
  format: "json"
  output:
    - "stdout"
    - "loki"
  loki:
    endpoint: "http://loki:3100/loki/api/v1/push"
```

## 备份策略

### 数据库备份

```bash
# PostgreSQL 备份
pg_dump -h db.example.com -U agent_toolkit -d agent_toolkit > backup.sql

# 定时备份
0 2 * * * /usr/bin/pg_dump -h db.example.com -U agent_toolkit -d agent_toolkit | gzip > /backups/agent_toolkit_$(date +\%Y\%m\%d).sql.gz
```

### Redis 备份

```bash
# RDB 备份
redis-cli SAVE

# AOF 备份
redis-cli BGREWRITEAOF
```

## 灾难恢复

### 数据库恢复

```bash
# 从备份恢复
pg_restore -h db.example.com -U agent_toolkit -d agent_toolkit < backup.sql
```

### 服务恢复

```bash
# 使用 Helm 回滚
helm rollback agent-toolkit

# 或重新部署
helm upgrade agent-toolkit agent-toolkit/agent-toolkit -f production-values.yaml
```

## 性能优化

### 数据库优化

- 使用连接池
- 创建必要的索引
- 定期 VACUUM

### 缓存策略

- Redis 缓存热点数据
- API 响应缓存
- 工具元数据缓存

### 负载均衡

使用 Nginx 或云负载均衡器：

```nginx
upstream agent_toolkit {
    server registry-1:8000;
    server registry-2:8000;
    server registry-3:8000;
}
```

## 安全建议

1. 使用 HTTPS
2. 配置防火墙规则
3. 启用审计日志
4. 定期更新依赖
5. 使用密钥管理服务
6. 配置网络策略
