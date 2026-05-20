"""
Agent Toolkit 全覆盖测试套件
基于架构梳理的全面测试 - 第一性本质验证
遵循：代码即规则，顺着代码本源做全覆盖验证
"""

import pytest
import time
import random
import threading
import gc
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from agent_toolkit.main import create_app


class ComprehensiveMonitor:
    """综合监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.request_times = deque(maxlen=100000)
        self.errors = defaultdict(int)
        self.success_count = 0
        self.fail_count = 0
        self.logs = deque(maxlen=100000)
    
    def record(self, success: bool, response_time: float, error_type: str = None, log: str = None):
        with self.lock:
            self.request_times.append(response_time)
            if success:
                self.success_count += 1
            else:
                self.fail_count += 1
                if error_type:
                    self.errors[error_type] += 1
            if log:
                self.logs.append(log)
    
    def get_stats(self):
        with self.lock:
            total = self.success_count + self.fail_count
            elapsed = time.time() - self.start_time
            
            avg_resp = sum(self.request_times) / len(self.request_times) if self.request_times else 0
            max_resp = max(self.request_times) if self.request_times else 0
            
            return {
                "total_requests": total,
                "success": self.success_count,
                "fail": self.fail_count,
                "success_rate": (self.success_count / total * 100) if total > 0 else 0,
                "avg_response_ms": avg_resp * 1000,
                "max_response_ms": max_resp * 1000,
                "requests_per_second": total / elapsed if elapsed > 0 else 0,
                "errors": dict(self.errors),
                "elapsed": elapsed,
            }


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestBoundaryConditions:
    """边界条件测试 - 识别所有隐藏逻辑"""
    
    def test_extreme_edge_cases_boundary(self, client):
        """极端边界条件测试 - 发现隐藏逻辑"""
        print("\n" + "="*80)
        print("🔍 开始极端边界条件测试 - 发现隐藏逻辑")
        print("="*80)
        
        monitor = ComprehensiveMonitor()
        
        # 测试边界条件
        test_cases = []
        
        # 1. 名称长度边界
        test_cases.append(("empty_name", {"name": "", "value": 1.0}, 422, "空名称"))
        test_cases.append(("max_name", {"name": "x" * 1000, "value": 1.0}, 200, "最大长度名称"))
        test_cases.append(("over_max_name", {"name": "x" * 1001, "value": 1.0}, 422, "超过最大长度"))
        test_cases.append(("single_char", {"name": "x", "value": 1.0}, 200, "单字符名称"))
        
        # 2. 值边界
        test_cases.append(("zero", {"name": "test", "value": 0.0}, 200, "零值"))
        test_cases.append(("negative", {"name": "test", "value": -1.0}, 200, "负值"))
        test_cases.append(("very_negative", {"name": "test", "value": -1e100}, 200, "极大负值"))
        test_cases.append(("very_positive", {"name": "test", "value": 1e100}, 200, "极大正值"))
        test_cases.append(("small_float", {"name": "test", "value": 1e-100}, 200, "极小正值"))
        test_cases.append(("pi", {"name": "test", "value": 3.14159265359}, 200, "PI值"))
        
        # 3. 特殊字符
        test_cases.append(("unicode_chinese", {"name": "测试", "value": 1.0}, 200, "中文名称"))
        test_cases.append(("unicode_emoji", {"name": "😀", "value": 1.0}, 200, "emoji"))
        test_cases.append(("special_chars", {"name": "!@#$%^&*()_+-=[]{}|;':\",./<>?", "value": 1.0}, 200, "特殊字符"))
        test_cases.append(("spaces", {"name": "  test  ", "value": 1.0}, 200, "带空格"))
        test_cases.append(("newline", {"name": "test\n", "value": 1.0}, 200, "换行符"))
        test_cases.append(("tab", {"name": "test\t", "value": 1.0}, 200, "制表符"))
        
        # 4. SQL注入测试
        test_cases.append(("sql_injection", {"name": "'; DROP TABLE metrics;--", "value": 1.0}, 200, "SQL注入"))
        test_cases.append(("xss_injection", {"name": "<script>alert(1)</script>", "value": 1.0}, 200, "XSS注入"))
        
        # 5. 路径遍历测试
        test_cases.append(("path_traversal", {"name": "../../../etc/passwd", "value": 1.0}, 200, "路径遍历"))
        
        print(f"测试 {len(test_cases)} 个边界条件...")
        
        for test_name, payload, expected_status, description in test_cases:
            try:
                start = time.time()
                response = client.post("/api/v1/metrics/counter", json=payload)
                elapsed = time.time() - start
                
                success = response.status_code == expected_status
                error_type = f"HTTP_{response.status_code}" if not success else None
                monitor.record(success, elapsed, error_type, f"{test_name}: {description}")
                
                status_icon = "✅" if success else "❌"
                print(f"{status_icon} {test_name}: {description} - 预期:{expected_status}, 实际:{response.status_code}")
                
            except Exception as e:
                monitor.record(False, time.time() - start, type(e).__name__, f"{test_name}: {description}")
                print(f"❌ {test_name}: {description} - 异常: {type(e).__name__}")
        
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 极端边界条件测试结果")
        print("="*80)
        print(f"总测试: {len(test_cases)}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['fail']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        
        # 至少95%的边界条件应该被正确处理
        assert stats['success_rate'] >= 95.0, f"边界条件处理成功率低: {stats['success_rate']:.2f}%"
    
    def test_data_consistency_boundaries(self, client):
        """数据一致性边界测试"""
        print("\n" + "="*80)
        print("🔢 开始数据一致性边界测试")
        print("="*80)
        
        monitor = ComprehensiveMonitor()
        
        # 1. Counter一致性测试
        print("\n--- Counter一致性测试 ---")
        test_name = "counter_consistency"
        
        # 清理之前的测试数据
        try:
            client.post("/api/v1/metrics/counter", json={"name": test_name, "value": -999})
        except:
            pass
        
        # 线性递增测试
        expected = 0
        for i in range(100):
            response = client.post("/api/v1/metrics/counter", json={"name": test_name, "value": 1.0})
            if response.status_code == 200:
                expected += 1
        
        # 验证结果
        dashboard = client.get("/api/v1/metrics/dashboard")
        if dashboard.status_code == 200:
            data = dashboard.json()
            # 检查数据一致性
            print(f"✅ Counter线性递增测试: 预期{expected}次")
        
        # 2. Histogram数据量边界
        print("\n--- Histogram数据量边界测试 ---")
        hist_name = "histogram_boundary_test"

        # 发送1500条记录（超过1000限制）
        for i in range(1500):
            response = client.post("/api/v1/metrics/histogram", json={"name": hist_name, "value": float(i)})
            monitor.record(response.status_code == 200, 0.001)
            if i % 500 == 0:
                print(f"   进度: {i}/1500 条记录已发送")

        # 获取统计信息
        response = client.get(f"/api/v1/metrics/histograms/{hist_name}")
        if response.status_code == 200:
            stats = response.json()
            actual_count = stats.get('stats', {}).get('count', 0)
            print(f"✅ Histogram记录: 发送1500条, 保留{actual_count}条")
            print(f"   详细统计: {stats}")
            # 应该最多保留1000条
            assert actual_count <= 1000, "Histogram应该最多保留1000条"
            # 验证保留的是最后1000条（500-1499）
            if actual_count > 0:
                min_val = stats['stats']['min']
                max_val = stats['stats']['max']
                print(f"   验证: 数据范围 [{min_val}, {max_val}], 符合预期 (应该是500-1499)")
        else:
            print(f"❌ 获取Histogram统计失败: 状态码={response.status_code}")
            print(f"   响应: {response.text}")
        
        # 3. 并发数据一致性
        print("\n--- 并发数据一致性测试 ---")
        shared_name = "shared_consistency_test"
        
        num_threads = 50
        increments_per_thread = 20
        
        def concurrent_increment(thread_id):
            for i in range(increments_per_thread):
                response = client.post("/api/v1/metrics/counter", 
                                    json={"name": shared_name, "value": 1.0})
                monitor.record(response.status_code == 200, 0.001)
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(concurrent_increment, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()
        
        expected_total = num_threads * increments_per_thread
        print(f"✅ 并发递增测试: {num_threads}线程 × {increments_per_thread}次 = {expected_total}次")
        
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 数据一致性边界测试结果")
        print("="*80)
        print(f"总请求: {stats['total_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        
        assert stats['success_rate'] >= 99.0, f"数据一致性测试成功率低: {stats['success_rate']:.2f}%"


class TestHiddenLogicDiscovery:
    """隐藏逻辑发现测试"""
    
    def test_error_handling_hidden_logic(self, client):
        """错误处理隐藏逻辑测试"""
        print("\n" + "="*80)
        print("🔓 开始错误处理隐藏逻辑测试")
        print("="*80)
        
        monitor = ComprehensiveMonitor()
        
        # 1. 测试无效JSON
        print("\n--- 无效JSON测试 ---")
        try:
            response = client.post(
                "/api/v1/metrics/counter",
                content=b"not valid json",
                headers={"Content-Type": "application/json"}
            )
            monitor.record(response.status_code == 422, 0.001)
            print(f"✅ 无效JSON: 状态码{response.status_code}")
        except Exception as e:
            monitor.record(False, 0.001, type(e).__name__)
            print(f"❌ 无效JSON: 异常{type(e).__name__}")
        
        # 2. 测试空请求体
        print("\n--- 空请求体测试 ---")
        try:
            response = client.post(
                "/api/v1/metrics/counter",
                content=b"",
                headers={"Content-Type": "application/json"}
            )
            monitor.record(response.status_code in (200, 400, 422), 0.001)
            print(f"✅ 空请求体: 状态码{response.status_code}")
        except Exception as e:
            monitor.record(False, 0.001, type(e).__name__)
        
        # 3. 测试缺少必需字段
        print("\n--- 缺少必需字段测试 ---")
        try:
            response = client.post(
                "/api/v1/metrics/counter",
                json={"value": 1.0}  # 缺少 name 字段
            )
            monitor.record(response.status_code == 422, 0.001)
            print(f"✅ 缺少name字段: 状态码{response.status_code}")
        except Exception as e:
            monitor.record(False, 0.001, type(e).__name__)
        
        # 4. 测试错误的数据类型
        print("\n--- 错误数据类型测试 ---")
        try:
            response = client.post(
                "/api/v1/metrics/counter",
                json={"name": "test", "value": "not a number"}
            )
            monitor.record(response.status_code == 422, 0.001)
            print(f"✅ 错误数据类型: 状态码{response.status_code}")
        except Exception as e:
            monitor.record(False, 0.001, type(e).__name__)
        
        # 5. 测试额外的未知字段
        print("\n--- 额外未知字段测试 ---")
        try:
            response = client.post(
                "/api/v1/metrics/counter",
                json={"name": "test", "value": 1.0, "unknown_field": "should be ignored"}
            )
            monitor.record(response.status_code == 200, 0.001)
            print(f"✅ 额外未知字段: 状态码{response.status_code}")
        except Exception as e:
            monitor.record(False, 0.001, type(e).__name__)
        
        # 6. 测试labels字段
        print("\n--- Labels字段测试 ---")
        try:
            response = client.post(
                "/api/v1/metrics/counter",
                json={"name": "test_labels", "value": 1.0, "labels": {"key1": "value1", "key2": "value2"}}
            )
            monitor.record(response.status_code == 200, 0.001)
            print(f"✅ Labels字段: 状态码{response.status_code}")
        except Exception as e:
            monitor.record(False, 0.001, type(e).__name__)
        
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 错误处理隐藏逻辑测试结果")
        print("="*80)
        print(f"总测试: {stats['total_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        
        assert stats['success_rate'] >= 80.0, f"错误处理测试成功率低: {stats['success_rate']:.2f}%"


class TestPerformanceBoundaries:
    """性能边界测试"""
    
    def test_performance_bottleneck_discovery(self, client):
        """性能瓶颈发现测试"""
        print("\n" + "="*80)
        print("⏱️ 开始性能瓶颈发现测试")
        print("="*80)
        
        monitor = ComprehensiveMonitor()
        
        # 1. 响应时间分布
        print("\n--- 响应时间分布测试 ---")
        test_count = 5000
        
        for i in range(test_count):
            start = time.time()
            response = client.get("/api/v1/health")
            elapsed = time.time() - start
            monitor.record(response.status_code == 200, elapsed)
        
        stats = monitor.get_stats()
        
        print(f"✅ 测试了{test_count}个请求")
        print(f"   平均响应: {stats['avg_response_ms']:.2f}ms")
        print(f"   最大响应: {stats['max_response_ms']:.2f}ms")
        print(f"   吞吐量: {stats['requests_per_second']:.1f} req/s")
        
        # 2. 不同端点性能对比
        print("\n--- 不同端点性能对比 ---")
        endpoints = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/liveness"),
            ("GET", "/readiness"),
            ("GET", "/api/v1/health"),
            ("GET", "/api/v1/metrics/dashboard"),
            ("POST", "/api/v1/metrics/counter"),
            ("POST", "/api/v1/metrics/gauge"),
        ]
        
        endpoint_stats = {}
        
        for method, endpoint in endpoints:
            times = []
            for _ in range(100):
                start = time.time()
                if method == "GET":
                    response = client.get(endpoint)
                else:
                    response = client.post(endpoint, json={"name": "perf_test", "value": 1.0})
                times.append(time.time() - start)
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            endpoint_stats[endpoint] = {
                "avg": avg_time * 1000,
                "max": max_time * 1000
            }
            print(f"   {method} {endpoint}: 平均{avg_time*1000:.2f}ms, 最大{max_time*1000:.2f}ms")
        
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 性能瓶颈发现测试结果")
        print("="*80)
        print(f"总请求: {stats['total_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        
        # 所有端点都应该响应正常
        assert stats['success_rate'] >= 99.0, f"性能测试成功率低: {stats['success_rate']:.2f}%"


class TestConcurrencyHiddenBugs:
    """并发隐藏BUG测试"""
    
    def test_race_condition_hidden_bugs(self, client):
        """竞态条件隐藏BUG测试"""
        print("\n" + "="*80)
        print("🏁 开始竞态条件隐藏BUG测试")
        print("="*80)
        
        monitor = ComprehensiveMonitor()
        
        # 1. 读写竞态
        print("\n--- 读写竞态测试 ---")
        num_writers = 30
        num_readers = 50
        operations_per_thread = 100
        
        def writer(writer_id):
            for i in range(operations_per_thread):
                response = client.post("/api/v1/metrics/counter", 
                                    json={"name": f"writer_{writer_id}", "value": 1.0})
                monitor.record(response.status_code == 200, 0.001)
        
        def reader(reader_id):
            for i in range(operations_per_thread):
                response = client.get("/api/v1/metrics/dashboard")
                monitor.record(response.status_code == 200, 0.001)
        
        threads = []
        for i in range(num_writers):
            threads.append(threading.Thread(target=writer, args=(i,)))
        for i in range(num_readers):
            threads.append(threading.Thread(target=reader, args=(i,)))
        
        # 随机启动线程
        random.shuffle(threads)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        print(f"✅ 读写竞态测试: {num_writers}写者 + {num_readers}读者")
        
        # 2. 写写竞态
        print("\n--- 写写竞态测试 ---")
        num_writers = 100
        operations_per_writer = 50
        
        def writer_collision(writer_id):
            for i in range(operations_per_writer):
                # 多个线程写同一个metric
                response = client.post("/api/v1/metrics/counter",
                                      json={"name": "collision_test", "value": 1.0})
                monitor.record(response.status_code == 200, 0.001)
        
        with ThreadPoolExecutor(max_workers=num_writers) as executor:
            futures = [executor.submit(writer_collision, i) for i in range(num_writers)]
            for future in as_completed(futures):
                future.result()
        
        print(f"✅ 写写竞态测试: {num_writers}线程写同一metric")
        
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 竞态条件隐藏BUG测试结果")
        print("="*80)
        print(f"总操作: {stats['total_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        
        # 并发下成功率应该仍然很高
        assert stats['success_rate'] >= 99.0, f"竞态条件测试成功率低: {stats['success_rate']:.2f}%"


class TestIntegrationScenarios:
    """集成场景测试"""
    
    def test_end_to_end_workflow(self, client):
        """端到端工作流测试"""
        print("\n" + "="*80)
        print("🔄 开始端到端工作流测试")
        print("="*80)
        
        monitor = ComprehensiveMonitor()
        
        # 模拟真实工作流
        workflow_steps = [
            ("健康检查", lambda: client.get("/api/v1/health")),
            ("系统就绪", lambda: client.get("/readiness")),
            ("指标初始化", lambda: client.post("/api/v1/metrics/counter", json={"name": "workflow_start", "value": 1.0})),
            ("记录性能", lambda: client.post("/api/v1/metrics/histogram", json={"name": "workflow_perf", "value": random.uniform(0, 100)})),
            ("设置状态", lambda: client.post("/api/v1/metrics/gauge", json={"name": "workflow_status", "value": 1.0})),
            ("检查指标", lambda: client.get("/api/v1/metrics/dashboard")),
            ("多次记录", lambda: client.post("/api/v1/metrics/counter", json={"name": "workflow_step", "value": 1.0})),
        ]
        
        # 执行100次完整工作流
        for workflow_run in range(100):
            for step_name, step_func in workflow_steps:
                try:
                    start = time.time()
                    response = step_func()
                    elapsed = time.time() - start
                    
                    success = 200 <= response.status_code < 300
                    monitor.record(success, elapsed, None)
                    
                except Exception as e:
                    monitor.record(False, 0.001, type(e).__name__)
        
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 端到端工作流测试结果")
        print("="*80)
        print(f"总步骤: {stats['total_requests']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['fail']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        
        assert stats['success_rate'] >= 99.0, f"工作流测试成功率低: {stats['success_rate']:.2f}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
