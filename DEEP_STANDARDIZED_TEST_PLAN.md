# Agent Toolkit 深度标准化测试计划

## 📋 文档信息
- **项目**: Agent Toolkit
- **版本**: 0.1.0
- **日期**: 2026-05-20
- **状态**: 深度测试进行中
- **执行标准**: 严格按照用户提出的8步标准化流程

---

## 🎯 一、基准定调

### 1.1 设计文档基准
根据已有的 `ARCHITECTURE_AND_TEST_COVERAGE.md` 和设计文档，基准包括：
- 三层解耦架构（编排层、适配层、工具层）
- 7个内置健康检查（database, memory, disk, cpu, registry, adapter, orchestrator）
- 4种Metrics类型（Counter, Gauge, Histogram, Summary）
- 3个中间件（Metrics, Resource, RateLimit）
- 4个自定义异常类型
- 12+个API端点

### 1.2 代码实际逻辑
代码实现与设计文档基本一致，主要偏差：
- 部分路由在main.py中被注释掉（需要数据库的模块）
- 增加了详细的日志追踪
- Metrics限制为1000条记录

---

## 🔍 二、测试前置动作

### 2.1 代码分层拆解

#### 2.1.1 应用层 (Application Layer)
**文件**: `main.py`
- 职责: FastAPI应用创建、路由注册、全局异常处理、CORS配置
- 关键组件:
  - `create_app()` - 工厂函数
  - 4个异常处理器
  - 路由注册（健康检查、Metrics、Dashboard）

#### 2.1.2 中间件层 (Middleware Layer)
**文件**: `middleware.py`
- 组件1: `MetricsMiddleware` - Prometheus和内部Metrics收集
- 组件2: `LoggingMiddleware` - 请求日志
- 组件3: `RateLimitMiddleware` - 速率限制（10000次/分钟）
- 组件4: `ResourceMonitorMiddleware` - 资源监控

#### 2.1.3 业务逻辑层 (Business Logic Layer)
**文件**: `health_check.py`
- `HealthCheckRegistry` - 健康检查注册中心
- 7个健康检查项
- 状态历史记录

**文件**: `metrics_api.py`
- `MetricsCollector` - Metrics收集器
- 4种指标操作
- 12个API端点

#### 2.1.4 共享层 (Shared Layer)
**文件**: `structured_logging.py` - 结构化日志
**文件**: `custom_exceptions.py` - 自定义异常
**文件**: `application_settings.py` - 配置管理

### 2.2 模块依赖关系图

```
main.py
  ├── middleware.py (4个中间件)
  │   ├── metrics_api.py
  │   └── structured_logging.py
  ├── health_check.py
  │   └── structured_logging.py
  ├── metrics_api.py
  │   └── structured_logging.py
  ├── custom_exceptions.py
  └── application_settings.py
```

### 2.3 调用链路分析

#### 2.3.1 正常请求链路
```
客户端请求
  ↓
CORS (FastAPI内置)
  ↓
RateLimitMiddleware
  ↓
ResourceMonitorMiddleware
  ↓
LoggingMiddleware
  ↓
MetricsMiddleware
  ↓
路由处理器 (health/metrics)
  ↓
业务逻辑处理
  ↓
MetricsMiddleware (finally)
  ↓
LoggingMiddleware (finally)
  ↓
响应返回
```

#### 2.3.2 异常请求链路
```
客户端请求
  ↓
... 经过所有中间件 ...
  ↓
业务逻辑抛出异常
  ↓
MetricsMiddleware (记录错误)
  ↓
LoggingMiddleware (记录错误)
  ↓
全局异常处理器
  ↓
JSON响应返回
```

---

### 2.4 入口与出口分析

#### 2.4.1 主要入口点

| 路径 | 方法 | 模块 | 功能 |
|------|------|------|------|
| `/` | GET | main.py | 根路径，服务信息 |
| `/dashboard` | GET | main.py | 监控Dashboard |
| `/docs` | GET | FastAPI | Swagger文档 |
| `/redoc` | GET | FastAPI | ReDoc文档 |
| `/health` | GET | main.py | 简化健康检查 |
| `/liveness` | GET | health_check.py | Kubernetes存活探针 |
| `/readiness` | GET | health_check.py | Kubernetes就绪探针 |
| `/api/v1/health` | GET | health_check.py | 完整健康检查 |
| `/api/v1/metrics` | 多种 | metrics_api.py | Metrics API |

#### 2.4.2 主要出口点
- JSON响应（正常/异常）
- 结构化日志
- Prometheus指标
- Metrics历史记录
- 健康检查历史

---

## 📊 二、测试前置动作（续）

### 2.5 参数规则提取

#### 2.5.1 Metrics API 参数规则

**Counter递增 - POST /api/v1/metrics/counter**
```python
class CounterIncrementRequest:
    name: str
      - 最小长度: 1
      - 最大长度: 1000
      - 不能为空
    value: float
      - 不能为 NaN
      - 不能为 Infinity
      - 必须是数字类型
    labels: Optional[Dict[str, str]]
      - 可选
```

**Gauge设置 - POST /api/v1/metrics/gauge**
```python
class GaugeSetRequest:
    name: str (同Counter)
    value: float (同Counter)
    labels: Optional[Dict[str, str]]
```

**Histogram记录 - POST /api/v1/metrics/histogram**
```python
class HistogramRecordRequest:
    name: str (同Counter)
    value: float (同Counter)
    labels: Optional[Dict[str, str]]
```

#### 2.5.2 健康检查参数规则
- 无参数，所有健康检查都是无参调用
- 默认超时: 5秒（数据库检查）
- 阈值: 内存/磁盘/CPU > 90% = WARNING

#### 2.5.3 速率限制参数规则
```python
RateLimitMiddleware:
    calls: int = 10000  # 默认10000次/分钟
    period: int = 60    # 默认60秒
    exempt_paths: list  # 豁免路径列表
```

### 2.6 判断条件与分支分析

#### 2.6.1 MetricsCollector判断条件

**increment_counter()**
```python
def increment_counter(name, value, labels):
    # 分支1: 名称验证 (通过Pydantic)
    # 分支2: 值验证 (通过Pydantic)
    # 分支3: 正常处理
    self._counters[name] += value
    self._record_point(...)
```

**record_histogram()**
```python
def record_histogram(name, value, labels):
    self._histograms[name].append(value)
    # 判断条件: 长度是否超过1000
    if len(self._histograms[name]) > 1000:
        # 分支: 超过限制，trim到1000条
        self._histograms[name] = self._histograms[name][-1000:]
    self._record_point(...)
```

**get_histogram_stats()**
```python
def get_histogram_stats(name):
    values = self._histograms.get(name, [])
    # 判断条件: 是否有数据
    if not values:
        return {}  # 空返回
    # 分支: 有数据，计算统计
    values_sorted = sorted(values)
    n = len(values_sorted)
    # 返回: count, min, max, mean, p50, p95, p99
```

#### 2.6.2 健康检查判断条件

**get_overall_health()**
```python
def get_overall_health():
    checks = await run_all_checks()
    failed = sum(1 for c in checks if c.status == UNHEALTHY)
    warnings = sum(1 for c in checks if c.status == WARNING)
    # 判断条件1: 是否有失败
    if failed > 0:
        overall_status = UNHEALTHY
    # 判断条件2: 是否有警告
    elif warnings > 0:
        overall_status = WARNING
    # 分支: 全部正常
    else:
        overall_status = HEALTHY
```

#### 2.6.3 中间件判断条件

**RateLimitMiddleware.dispatch()**
```python
async def dispatch(request, call_next):
    # 判断条件1: 是否是豁免路径
    for exempt_path in self.exempt_paths:
        if path.startswith(exempt_path):
            return await call_next(request)  # 直接放行
    # 判断条件2: 是否超过速率限制
    if len(self.clients[client_ip]) >= self.calls:
        return JSONResponse(429, ...)  # 限流
    # 分支: 正常处理
    self.clients[client_ip].append(current_time)
    return await call_next(request)
```

**ResourceMonitorMiddleware.dispatch()**
```python
async def dispatch(request, call_next):
    current_time = time.time()
    # 判断条件: 是否需要更新资源指标
    if current_time - self.last_update > self.update_interval:
        self._update_resource_metrics()
        self.last_update = current_time
    return await call_next(request)
```

### 2.7 边界阈值识别

#### 2.7.1 Metrics边界
- 名称: 1-1000字符
- 值: 任何有效浮点数（除了NaN/Infinity）
- Histogram: 最多1000条记录
- Metric Points: 最多1000条记录

#### 2.7.2 健康检查边界
- 内存: >90% → WARNING
- 磁盘: >90% → WARNING
- CPU: >90% → WARNING
- 数据库超时: 5秒

#### 2.7.3 速率限制边界
- 默认限制: 10000次/分钟
- 豁免路径: /health, /liveness, /readiness, /api/v1/health, /api/v1/metrics
- 错误跟踪: 最多1000条错误

#### 2.7.4 中间件边界
- 资源更新间隔: 10秒

### 2.8 默认逻辑提取

#### 2.8.1 MetricsCollector默认值
```python
def __init__(self):
    self._counters: Dict[str, float] = defaultdict(float)  # 默认0.0
    self._gauges: Dict[str, float] = defaultdict(float)    # 默认0.0
    self._histograms: Dict[str, List[float]] = defaultdict(list)  # 默认空列表
    self._metric_points: Dict[str, List[MetricPoint]] = defaultdict(list)  # 默认空列表
    self._start_time = time.time()
```

#### 2.8.2 速率限制默认值
```python
def __init__(self, app, calls: int = 1000, period: int = 60):
    # 注意: 在setup_middlewares中设置为10000
    self.calls = calls or 1000
    self.period = period or 60
    self.clients = {}
    self.exempt_paths = [...]  # 固定列表
```

### 2.9 异常捕获与处理

#### 2.9.1 全局异常处理
```python
@app.exception_handler(NotFoundError) → 404
@app.exception_handler(DuplicateError) → 409
@app.exception_handler(ValidationError) → 422
@app.exception_handler(AgentToolkitException) → 500
# 其他未捕获异常 → FastAPI默认处理（500）
```

#### 2.9.2 内部异常捕获
```python
# MetricsMiddleware
try:
    response = await call_next(request)
except Exception as e:
    # 记录错误到追踪器
    # 增加错误计数
    # 增加内部错误计数器
    raise  # 重新抛出，让全局异常处理器处理
finally:
    # 清理
    ...
```

```python
# HealthCheckRegistry.run_all_checks()
for name, check_func in self._checks.items():
    try:
        success, details = await check_func()
        ...
    except Exception as e:
        results.append(HealthCheckResult(
            status=UNHEALTHY,
            error=str(e)
        ))
```

---

### 2.10 数据流向梳理

#### 2.10.1 Counter数据流向
```
POST /counter
  ↓
Pydantic验证 (名称、值)
  ↓
metrics_collector.increment_counter()
  ↓
self._counters[name] += value  # 更新内存状态
  ↓
self._record_point()  # 添加到历史记录
  ↓
判断: 历史记录>1000? → trim
  ↓
返回: 200 OK, 当前值
```

#### 2.10.2 健康检查数据流向
```
GET /api/v1/health
  ↓
health_router.get('/')
  ↓
registry.run_all_checks()
  ↓
每个健康检查函数执行
  ↓
registry.get_overall_health()
  ↓
判断: failed>0? → UNHEALTHY
判断: warnings>0? → WARNING
否则 → HEALTHY
  ↓
构建响应对象
  ↓
添加到健康历史记录
  ↓
返回: 200 OK, 完整状态
```

#### 2.10.3 请求数据流向
```
客户端请求
  ↓
FastAPI接收
  ↓
Middleware栈 (4个中间件)
  ↓
MetricsMiddleware:
  - ACTIVE_REQUESTS.inc()
  - metrics_collector.set_gauge("active_connections", ...)
  ↓
路由处理
  ↓
MetricsMiddleware.finally:
  - ACTIVE_REQUESTS.dec()
  - metrics_collector.set_gauge("active_connections", ...)
  - metrics_collector.record_request()
  - metrics_collector.record_histogram("request_duration")
  - metrics_collector.increment_counter("total_requests")
  ↓
响应返回
```

### 2.11 状态变更追踪

#### 2.11.1 Metrics状态
- `self._counters` - 递增/递减
- `self._gauges` - 设置值
- `self._histograms` - 追加/trim
- `self._metric_points` - 追加/trim

#### 2.11.2 健康检查状态
- `self._health_history` - 追加
- `self._checks` - 静态（注册后不变）

#### 2.11.3 中间件状态
- `RateLimitMiddleware.clients` - 动态增长/清理
- `ErrorTracker.errors` - 追加/trim
- `ResourceMonitorMiddleware.last_update` - 更新

### 2.12 隐藏隐性规则识别

#### 2.12.1 Metrics隐性规则
1. **默认值**: 使用defaultdict，首次访问自动初始化为0/空列表
2. **Trim策略**: 保留最新的1000条（不是最旧的）
3. **Labels处理**: 记录到metric_points，但不参与统计计算
4. **Dashboard依赖**: request_duration histogram需要被记录，否则p50/p95/p99为0

#### 2.12.2 健康检查隐性规则
1. **异步要求**: 所有健康检查函数必须是async
2. **返回格式**: 必须返回 (success: bool, details: Any)
3. **DEGRADED状态**: 在代码中定义但未在判断逻辑中使用

#### 2.12.3 速率限制隐性规则
1. **路径匹配**: 使用startswith，所以/api/v1/metrics/...都会被豁免
2. **清理策略**: 每次请求都会清理过期记录
3. **client_ip**: 如果request.client为None，使用'unknown'

#### 2.12.4 中间件隐性规则
1. **执行顺序**: 在setup_middlewares中的顺序很重要
2. **MetricsMiddleware活跃连接**: 计算方式可能不准确（使用len(ACTIVE_REQUESTS._value.get())）
3. **ResourceMonitor**: 如果psutil不可用，使用fallback值0

---

## 🧪 三、标准化全流程测试

### 3.1 静态代码核验

#### 3.1.1 代码风格检查
- [ ] PEP8合规性
- [ ] 类型注解完整性
- [ ] 文档字符串完整性
- [ ] 命名规范一致性

#### 3.1.2 逻辑合理性检查
- [ ] 无死代码
- [ ] 无无限循环风险
- [ ] 边界条件处理完整
- [ ] 异常处理合理
- [ ] 资源释放/清理正确

#### 3.1.3 安全隐患检查
- [ ] 输入验证完整
- [ ] 无SQL注入风险
- [ ] 无XSS风险
- [ ] 无路径遍历风险
- [ ] 无敏感信息泄露

#### 3.1.4 性能隐患检查
- [ ] 无O(n²)算法
- [ ] 数据结构选择合理
- [ ] 缓存使用得当
- [ ] 无内存泄漏

### 3.2 单元全覆盖测试

#### 3.2.1 MetricsCollector测试覆盖
| 测试项 | 覆盖分支 | 优先级 |
|--------|----------|--------|
| increment_counter 基本 | 正常路径 | P0 |
| increment_counter 多次 | 累加逻辑 | P0 |
| increment_counter 负值 | 负值处理 | P1 |
| set_gauge 基本 | 正常路径 | P0 |
| set_gauge 更新 | 更新逻辑 | P0 |
| record_histogram 基本 | 正常路径 | P0 |
| record_histogram 1000条 | trim逻辑 | P0 |
| record_histogram 1500条 | 超过限制 | P0 |
| get_histogram_stats 空 | 空数据 | P1 |
| get_histogram_stats 有数据 | 统计计算 | P0 |
| get_metric_history 基本 | 历史记录 | P1 |
| get_all_metrics | 汇总逻辑 | P1 |

#### 3.2.2 HealthCheckRegistry测试覆盖
| 测试项 | 覆盖分支 | 优先级 |
|--------|----------|--------|
| register_check | 注册功能 | P1 |
| run_all_checks 成功 | 全部通过 | P0 |
| run_all_checks 失败 | 异常处理 | P0 |
| get_overall_health 健康 | HEALTHY分支 | P0 |
| get_overall_health 警告 | WARNING分支 | P0 |
| get_overall_health 失败 | UNHEALTHY分支 | P0 |

#### 3.2.3 中间件测试覆盖
| 测试项 | 覆盖分支 | 优先级 |
|--------|----------|--------|
| RateLimitMiddleware 正常 | 不限流 | P0 |
| RateLimitMiddleware 超限 | 限流429 | P0 |
| RateLimitMiddleware 豁免 | 豁免路径 | P0 |
| MetricsMiddleware 成功 | 成功路径 | P0 |
| MetricsMiddleware 失败 | 错误路径 | P0 |
| ResourceMonitorMiddleware 更新 | 资源更新 | P1 |

### 3.3 模块集成联调

#### 3.3.1 健康检查 + Metrics集成
- [ ] 健康检查触发Metrics记录
- [ ] 健康检查状态影响Dashboard显示

#### 3.3.2 中间件 + Metrics集成
- [ ] 请求计数正确记录
- [ ] 响应时间正确记录
- [ ] 活跃请求正确追踪
- [ ] 错误计数正确记录

#### 3.3.3 路由 + 异常处理集成
- [ ] 404错误正确返回
- [ ] 422验证错误正确返回
- [ ] 500错误正确返回

### 3.4 接口全量遍历

#### 3.4.1 GET端点测试
| 端点 | 正常请求 | 异常请求 |
|------|----------|----------|
| `/` | 200 OK | - |
| `/dashboard` | 200 HTML | - |
| `/health` | 200 OK | - |
| `/liveness` | 200 OK | - |
| `/readiness` | 200 OK | - |
| `/api/v1/health` | 200 OK | - |
| `/api/v1/metrics` | 200 OK | - |
| `/api/v1/metrics/counters` | 200 OK | - |
| `/api/v1/metrics/gauges` | 200 OK | - |
| `/api/v1/metrics/histograms/{name}` | 200 OK | 空名称 |
| `/api/v1/metrics/history/{name}` | 200 OK | 空名称 |
| `/api/v1/metrics/dashboard` | 200 OK | - |

#### 3.4.2 POST端点测试
| 端点 | 正常请求 | 空名称 | 超长名称 | NaN值 | Infinity值 | 空JSON | 无效JSON |
|------|----------|--------|----------|-------|------------|--------|----------|
| `/api/v1/metrics/counter` | 200 | 422 | 422 | 422 | 422 | 422 | 422 |
| `/api/v1/metrics/gauge` | 200 | 422 | 422 | 422 | 422 | 422 | 422 |
| `/api/v1/metrics/histogram` | 200 | 422 | 422 | 422 | 422 | 422 | 422 |
| `/api/v1/metrics/summary` | 200 | 422 | 422 | 422 | 422 | 422 | 422 |

### 3.5 业务场景闭环

#### 3.5.1 正向业务场景
| 场景 | 步骤 | 预期结果 |
|------|------|----------|
| 正常监控流程 | 1. 启动服务<br>2. 访问健康检查<br>3. 记录Metrics<br>4. 查看Dashboard | 1. 服务启动成功<br>2. 健康检查通过<br>3. Metrics正确记录<br>4. Dashboard显示正常 |
| 高并发监控 | 1. 1000并发请求<br>2. 记录请求<br>3. 查看Metrics | 1. 所有请求成功<br>2. Metrics准确<br>3. 无崩溃 |

#### 3.5.2 逆向业务场景
| 场景 | 步骤 | 预期结果 |
|------|------|----------|
| 异常输入处理 | 1. 发送空名称<br>2. 发送超长名称<br>3. 发送NaN值 | 全部返回422验证错误 |
| 速率限制触发 | 1. 发送10001个请求<br>2. 检查响应 | 第10001个请求返回429 |

#### 3.5.3 中断场景
| 场景 | 步骤 | 预期结果 |
|------|------|----------|
| 请求中断 | 1. 发送请求<br>2. 模拟连接断开 | 中间件正确清理活跃计数 |
| 异常中断 | 1. 触发500错误<br>2. 检查系统状态 | 系统继续运行，Metrics正确记录 |

#### 3.5.4 重复操作场景
| 场景 | 步骤 | 预期结果 |
|------|------|----------|
| 重复递增 | 1. 100次increment<br>2. 检查最终值 | 值=100，准确 |
| 重复健康检查 | 1. 100次健康检查<br>2. 检查历史记录 | 历史记录完整 |

### 3.6 数据一致性校验

#### 3.6.1 Counter一致性
- [ ] 1次递增: 1→正确
- [ ] 100次递增: 100→正确
- [ ] 并发100线程×20次: 2000→正确
- [ ] 负值递增: 正确计算

#### 3.6.2 Histogram一致性
- [ ] 100条记录: count=100→正确
- [ ] 1500条记录: count=1000→正确
- [ ] 统计计算正确: min, max, mean, p50, p95, p99→正确
- [ ] Trim策略正确: 保留最新1000条→正确

#### 3.6.3 Metrics历史一致性
- [ ] 记录与历史一致
- [ ] Labels正确保存
- [ ] 时间戳正确

#### 3.6.4 请求计数一致性
- [ ] 发送1000个请求→总请求数=1000→正确
- [ ] 状态码计数正确
- [ ] 响应时间记录正确

### 3.7 异常容错测试

#### 3.7.1 超时处理
- [ ] 数据库超时→WARNING状态
- [ ] 响应超时→Metrics正确记录

#### 3.7.2 断连处理
- [ ] 客户端断开→中间件正确清理
- [ ] 数据库断连→健康检查失败

#### 3.7.3 错误兜底
- [ ] 未捕获异常→500响应
- [ ] 异常后系统继续运行
- [ ] 错误历史正确记录

#### 3.7.4 重试机制
- [ ] （当前无重试机制）
- [ ] （需要评估是否需要）

### 3.8 基础性能核验

#### 3.8.1 响应时间
- [ ] 100请求: 平均<10ms
- [ ] 1000请求: 平均<20ms
- [ ] 10000请求: 平均<50ms

#### 3.8.2 吞吐量
- [ ] 基准: >300 req/s
- [ ] 100并发: >250 req/s
- [ ] 1000并发: >200 req/s

#### 3.8.3 内存稳定性
- [ ] 10000请求: 增长<100MB
- [ ] 无内存泄漏
- [ ] GC正常工作

#### 3.8.4 无阻塞
- [ ] 长时间运行: 无死锁
- [ ] 高并发: 无饥饿
- [ ] 资源使用: 合理

---

## ✅ 四、判定验收标准

### 4.1 代码分支覆盖标准
- [ ] 所有if/else分支100%可执行
- [ ] 所有异常分支100%可测试
- [ ] 所有边界条件100%覆盖
- [ ] 所有默认路径100%验证

### 4.2 运行行为一致性标准
- [ ] 所有功能与代码定义完全一致
- [ ] 所有API响应符合规范
- [ ] 所有状态转换符合预期
- [ ] 所有日志输出符合预期

### 4.3 数据一致性标准
- [ ] 无数据丢失
- [ ] 无数据错乱
- [ ] 无数据冲突
- [ ] 数据回显100%正确

### 4.4 异常处理标准
- [ ] 无崩溃
- [ ] 无未捕获异常
- [ ] 所有异常优雅处理
- [ ] 错误信息完整准确

---

## 📝 附录

### A. 测试用例清单
### B. 测试数据准备
### C. 测试环境配置
### D. 缺陷跟踪表
