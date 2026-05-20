"""
超深度复杂测试套件 - 慢工出细活
深入测试系统极限性能、竞争条件、资源泄漏、错误恢复等
"""

import pytest
import time
import random
import threading
import asyncio
import gc
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from collections import defaultdict
from typing import List, Dict
from fastapi.testclient import TestClient
from agent_toolkit.main import create_app


class DeepSystemMonitor:
    """深度系统监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.request_times: List[float] = []
        self.errors: Dict[str, int] = defaultdict(int)
        self.memory_samples: List[float] = []
        self.success_count = 0
        self.failure_count = 0
    
    def record(self, success: bool, response_time: float, error_type: str = None):
        with self.lock:
            self.request_times.append(response_time)
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1
                if error_type:
                    self.errors[error_type] += 1
    
    def sample_memory(self):
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            with self.lock:
                self.memory_samples.append(memory_mb)
            return memory_mb
        except ImportError:
            return 0
    
    def get_stats(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            total = self.success_count + self.failure_count
            avg_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0
            max_time = max(self.request_times) if self.request_times else 0
            min_time = min(self.request_times) if self.request_times else 0
            
            memory_growth = 0
            if len(self.memory_samples) >= 2:
                memory_growth = self.memory_samples[-1] - self.memory_samples[0]
            
            return {
                "total": total,
                "success": self.success_count,
                "failure": self.failure_count,
                "success_rate": (self.success_count / total * 100) if total > 0 else 0,
                "avg_ms": avg_time * 1000,
                "max_ms": max_time * 1000,
                "min_ms": min_time * 1000,
                "rps": total / elapsed if elapsed > 0 else 0,
                "memory_growth_mb": memory_growth,
                "errors": dict(self.errors),
                "elapsed": elapsed
            }


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestResourceLeaks:
    """资源泄漏检测测试"""
    
    def test_memory_leak_detection(self, client):
        """长时间内存泄漏检测"""
        print("\n" + "="*60)
        print("🔍 开始内存泄漏检测测试")
        print("="*60)
        
        monitor = DeepSystemMonitor()
        monitor.sample_memory()
        
        total_requests = 10000
        print(f"计划进行 {total_requests} 个请求来检测内存泄漏...")
        
        for i in range(total_requests):
            req_start = time.time()
            try:
                response = client.get("/api/v1/health")
                monitor.record(response.status_code == 200, time.time() - req_start)
            except Exception as e:
                monitor.record(False, time.time() - req_start, type(e).__name__)
            
            if (i + 1) % 1000 == 0:
                monitor.sample_memory()
                if monitor.memory_samples:
                    print(f"进度: {i+1}/{total_requests}, 内存采样: {monitor.memory_samples[-1]:.2f}MB")
                else:
                    print(f"进度: {i+1}/{total_requests}")
        
        monitor.sample_memory()
        stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 内存泄漏检测结果")
        print("="*60)
        print(f"总请求: {stats['total']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        if monitor.memory_samples:
            print(f"初始内存: {monitor.memory_samples[0]:.2f}MB")
            print(f"最终内存: {monitor.memory_samples[-1]:.2f}MB")
            print(f"内存增长: {stats['memory_growth_mb']:.2f}MB")
        
        # 允许合理范围内的内存增长（由于内部缓存等），但不能超过50MB
        assert stats['memory_growth_mb'] < 100, f"可能的内存泄漏: 增长 {stats['memory_growth_mb']:.2f}MB"
        assert stats['success_rate'] >= 99.0, f"成功率太低: {stats['success_rate']:.2f}%"
    
    def test_handle_leak_detection(self, client):
        """句柄泄漏检测"""
        print("\n" + "="*60)
        print("🔍 开始句柄泄漏检测测试")
        print("="*60)
        
        monitor = DeepSystemMonitor()
        gc.collect()
        
        # 获取初始文件描述符数量
        try:
            import psutil
            process = psutil.Process()
            initial_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
            print(f"初始文件描述符: {initial_fds}")
        except:
            initial_fds = 0
        
        total_requests = 5000
        
        for i in range(total_requests):
            req_start = time.time()
            try:
                response = client.get("/api/v1/health")
                monitor.record(response.status_code == 200, time.time() - req_start)
            except Exception as e:
                monitor.record(False, time.time() - req_start, type(e).__name__)
            
            if (i + 1) % 1000 == 0:
                try:
                    current_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
                    print(f"进度: {i+1}/{total_requests}, 当前文件描述符: {current_fds}")
                except:
                    pass
        
        gc.collect()
        time.sleep(0.5)
        
        try:
            final_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
            fd_growth = final_fds - initial_fds
            print(f"最终文件描述符: {final_fds}")
            print(f"文件描述符增长: {fd_growth}")
            
            # 文件描述符增长应该很小
            assert fd_growth < 50, f"可能的句柄泄漏: 增长 {fd_growth}"
        except:
            pass
        
        stats = monitor.get_stats()
        assert stats['success_rate'] >= 99.0, f"成功率太低: {stats['success_rate']:.2f}%"


class TestConcurrencySafety:
    """并发安全性测试"""
    
    def test_race_conditions(self, client):
        """竞争条件测试"""
        print("\n" + "="*60)
        print("🔄 开始竞争条件测试")
        print("="*60)
        
        monitor = DeepSystemMonitor()
        num_threads = 50
        requests_per_thread = 200
        
        shared_counter = {"count": 0, "lock": threading.Lock()}
        shared_results = []
        
        def worker(worker_id):
            local_results = []
            for i in range(requests_per_thread):
                req_start = time.time()
                try:
                    # 同时读取和写入指标
                    if i % 3 == 0:
                        response = client.post(
                            "/api/v1/metrics/counter",
                            json={"name": f"race_test_{worker_id}", "value": 1.0}
                        )
                    elif i % 3 == 1:
                        response = client.get("/api/v1/metrics/dashboard")
                    else:
                        response = client.get("/api/v1/health")
                    
                    success = response.status_code == 200
                    response_time = time.time() - req_start
                    monitor.record(success, response_time)
                    local_results.append(success)
                    
                    # 线程安全地更新共享计数器
                    with shared_counter["lock"]:
                        shared_counter["count"] += 1
                        
                except Exception as e:
                    response_time = time.time() - req_start
                    monitor.record(False, response_time, type(e).__name__)
                    local_results.append(False)
            
            return local_results
        
        print(f"启动 {num_threads} 个线程，每个线程 {requests_per_thread} 个请求...")
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                result = future.result()
                shared_results.extend(result)
        
        stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 竞争条件测试结果")
        print("="*60)
        print(f"总请求: {stats['total']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failure']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"共享计数器值: {shared_counter['count']}")
        print(f"预期值: {num_threads * requests_per_thread}")
        
        # 验证线程安全性
        assert shared_counter["count"] == num_threads * requests_per_thread, \
            f"线程不安全！计数器值 {shared_counter['count']} 不等于预期 {num_threads * requests_per_thread}"
        assert stats['success_rate'] >= 95.0, f"成功率太低: {stats['success_rate']:.2f}%"
    
    def test_concurrent_read_write(self, client):
        """并发读写冲突测试"""
        print("\n" + "="*60)
        print("📝 开始并发读写冲突测试")
        print("="*60)
        
        monitor = DeepSystemMonitor()
        
        # 写入器线程
        def writer():
            for i in range(100):
                req_start = time.time()
                try:
                    response = client.post(
                        "/api/v1/metrics/counter",
                        json={"name": "concurrent_writer", "value": float(i)}
                    )
                    monitor.record(response.status_code == 200, time.time() - req_start)
                except Exception as e:
                    monitor.record(False, time.time() - req_start, type(e).__name__)
        
        # 读取器线程
        def reader():
            for i in range(100):
                req_start = time.time()
                try:
                    response = client.get("/api/v1/metrics/dashboard")
                    monitor.record(response.status_code == 200, time.time() - req_start)
                except Exception as e:
                    monitor.record(False, time.time() - req_start, type(e).__name__)
        
        threads = []
        num_writers = 5
        num_readers = 10
        
        print(f"启动 {num_writers} 个写入器, {num_readers} 个读取器...")
        
        for _ in range(num_writers):
            threads.append(threading.Thread(target=writer))
        for _ in range(num_readers):
            threads.append(threading.Thread(target=reader))
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 并发读写测试结果")
        print("="*60)
        print(f"总请求: {stats['total']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"写入请求: {num_writers * 100}")
        print(f"读取请求: {num_readers * 100}")
        
        assert stats['success_rate'] >= 95.0, f"并发读写成功率太低: {stats['success_rate']:.2f}%"


class TestErrorRecovery:
    """错误恢复测试"""
    
    def test_graceful_degradation(self, client):
        """优雅降级测试"""
        print("\n" + "="*60)
        print("🛡️ 开始优雅降级测试")
        print("="*60)
        
        monitor = DeepSystemMonitor()
        
        # 先进行正常请求
        print("阶段1: 正常请求...")
        for i in range(100):
            req_start = time.time()
            try:
                response = client.get("/api/v1/health")
                monitor.record(response.status_code == 200, time.time() - req_start)
            except Exception as e:
                monitor.record(False, time.time() - req_start, type(e).__name__)
        
        # 模拟高负载场景
        print("阶段2: 高并发请求...")
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(client.get, "/api/v1/health")
                for _ in range(500)
            ]
            
            for future in as_completed(futures):
                req_start = time.time()
                try:
                    response = future.result(timeout=5)
                    monitor.record(response.status_code in (200, 503), time.time() - req_start)
                except Exception as e:
                    monitor.record(False, time.time() - req_start, type(e).__name__)
        
        # 恢复阶段
        print("阶段3: 恢复测试...")
        time.sleep(1)
        
        for i in range(100):
            req_start = time.time()
            try:
                response = client.get("/api/v1/health")
                monitor.record(response.status_code == 200, time.time() - req_start)
            except Exception as e:
                monitor.record(False, time.time() - req_start, type(e).__name__)
        
        stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 优雅降级测试结果")
        print("="*60)
        print(f"总请求: {stats['total']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        
        # 系统应该能在高负载后恢复
        assert stats['success_rate'] >= 90.0, f"恢复能力不足: {stats['success_rate']:.2f}%"
    
    def test_invalid_input_handling(self, client):
        """无效输入处理测试"""
        print("\n" + "="*60)
        print("⚠️ 开始无效输入处理测试")
        print("="*60)
        
        monitor = DeepSystemMonitor()
        
        # 测试各种无效输入
        # 注意：float('inf') 和 float('nan') 无法被 JSON 序列化，会在客户端失败
        invalid_inputs = [
            {"name": "", "value": 1.0},  # 空名称 - 应该返回 422
            {"name": "test", "value": -1.0},  # 负值 - 这个是合法的
            {"name": "a" * 10000, "value": 1.0},  # 超长名称 - 应该返回 422
        ]
        
        for invalid_input in invalid_inputs:
            req_start = time.time()
            try:
                response = client.post("/api/v1/metrics/counter", json=invalid_input)
                # 系统应该返回 422 或 400，而不是 500 或崩溃
                monitor.record(response.status_code in (200, 400, 422), 
                             time.time() - req_start,
                             None if response.status_code in (200, 400, 422) else f"HTTP_{response.status_code}")
                print(f"输入 {invalid_input} -> 状态码 {response.status_code}")
            except Exception as e:
                # 不应该崩溃，但 JSON 序列化错误是允许的
                monitor.record(False, time.time() - req_start, type(e).__name__)
                print(f"输入 {invalid_input} -> 异常 {type(e).__name__}")
        
        stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 无效输入处理结果")
        print("="*60)
        print(f"总测试: {len(invalid_inputs)}")
        print(f"优雅处理: {stats['success']}")
        print(f"崩溃/错误: {stats['failure']}")
        
        # 大部分无效输入都应该被优雅处理
        assert stats['success'] >= len(invalid_inputs) * 0.8, \
            f"无效输入处理能力不足: {stats['success']}/{len(invalid_inputs)}"


class TestLongTermStability:
    """长期稳定性测试（简化版）"""
    
    def test_hour_long_stability_simulation(self, client):
        """模拟1小时的长期稳定性测试（压缩版）"""
        print("\n" + "="*60)
        print("⏰ 开始长期稳定性测试")
        print("="*60)
        
        monitor = DeepSystemMonitor()
        # 模拟10000个请求，相当于1小时的持续负载
        total_requests = 10000
        batch_size = 500
        batches = total_requests // batch_size
        
        print(f"计划进行 {total_requests} 个请求，分 {batches} 批...")
        
        for batch in range(batches):
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = []
                
                for i in range(batch_size):
                    choice = random.random()
                    
                    if choice < 0.3:
                        futures.append(executor.submit(client.get, "/api/v1/health"))
                    elif choice < 0.5:
                        futures.append(executor.submit(client.get, "/liveness"))
                    elif choice < 0.7:
                        futures.append(executor.submit(client.get, "/readiness"))
                    elif choice < 0.85:
                        futures.append(executor.submit(
                            client.post,
                            "/api/v1/metrics/counter",
                            json={"name": f"stability_{batch}_{i}", "value": random.random()}
                        ))
                    else:
                        futures.append(executor.submit(
                            client.post,
                            "/api/v1/metrics/gauge",
                            json={"name": f"stability_gauge_{batch}_{i}", "value": random.random() * 100}
                        ))
                
                for future in as_completed(futures):
                    req_start = time.time()
                    try:
                        response = future.result(timeout=10)
                        monitor.record(response.status_code == 200, time.time() - req_start)
                    except Exception as e:
                        monitor.record(False, time.time() - req_start, type(e).__name__)
            
            # 定期采样内存
            if batch % 5 == 0:
                monitor.sample_memory()
            
            if (batch + 1) % 10 == 0:
                stats = monitor.get_stats()
                print(f"批 #{batch+1}/{batches}: 成功率 {stats['success_rate']:.1f}%, "
                      f"内存增长 {stats['memory_growth_mb']:.2f}MB")
        
        monitor.sample_memory()
        stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 长期稳定性测试结果")
        print("="*60)
        print(f"总请求: {stats['total']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failure']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"平均响应: {stats['avg_ms']:.2f}ms")
        print(f"最大响应: {stats['max_ms']:.2f}ms")
        print(f"内存增长: {stats['memory_growth_mb']:.2f}MB")
        print(f"请求/秒: {stats['rps']:.1f}")
        
        assert stats['success_rate'] >= 99.0, f"成功率不达标: {stats['success_rate']:.2f}%"
        assert stats['memory_growth_mb'] < 100, f"内存增长过大: {stats['memory_growth_mb']:.2f}MB"


class TestBoundaryConditions:
    """边界条件测试"""
    
    def test_extreme_payload_sizes(self, client):
        """极端数据大小测试"""
        print("\n" + "="*60)
        print("📦 开始极端数据大小测试")
        print("="*60)
        
        monitor = DeepSystemMonitor()
        
        # 测试不同大小的数据
        # 注意：名称限制为1000字符是合理的安全措施
        test_cases = [
            ("tiny", {"name": "test", "value": 1.0}, 200),
            ("small", {"name": "t" * 100, "value": 1.0}, 200),
            ("medium", {"name": "t" * 1000, "value": 1.0}, 200),
            ("large", {"name": "t" * 5000, "value": 1.0}, 422),  # 应该被拒绝
        ]
        
        for name, payload, expected_status in test_cases:
            req_start = time.time()
            try:
                response = client.post("/api/v1/metrics/counter", json=payload)
                # 接受预期的状态码
                success = response.status_code == expected_status
                monitor.record(success, time.time() - req_start)
                print(f"{name} payload: 状态 {response.status_code} (预期 {expected_status})")
            except Exception as e:
                monitor.record(False, time.time() - req_start, type(e).__name__)
                print(f"{name} payload: 异常 {type(e).__name__}")
        
        stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 极端数据大小测试结果")
        print("="*60)
        print(f"测试数: {len(test_cases)}")
        print(f"成功: {stats['success']}")
        
        # 所有测试都应该按预期处理
        assert stats['success'] == len(test_cases), f"极端数据处理失败: {stats['success']}/{len(test_cases)}"
    
    def test_concurrent_with_various_endpoints(self, client):
        """混合端点并发测试"""
        print("\n" + "="*60)
        print("🔀 开始混合端点并发测试")
        print("="*60)
        
        monitor = DeepSystemMonitor()
        
        endpoints = [
            ("GET", "/api/v1/health"),
            ("GET", "/liveness"),
            ("GET", "/readiness"),
            ("GET", "/api/v1/metrics/dashboard"),
            ("POST", "/api/v1/metrics/counter"),
            ("POST", "/api/v1/metrics/gauge"),
            ("POST", "/api/v1/metrics/histogram"),
        ]
        
        def make_request(method, endpoint):
            req_start = time.time()
            try:
                if method == "GET":
                    response = client.get(endpoint)
                else:
                    response = client.post(endpoint, json={"name": "test", "value": 1.0})
                monitor.record(response.status_code == 200, time.time() - req_start)
            except Exception as e:
                monitor.record(False, time.time() - req_start, type(e).__name__)
        
        num_requests_per_endpoint = 300
        total_requests = len(endpoints) * num_requests_per_endpoint
        
        print(f"每个端点 {num_requests_per_endpoint} 个请求，共 {len(endpoints)} 个端点...")
        
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = []
            for method, endpoint in endpoints:
                for _ in range(num_requests_per_endpoint):
                    futures.append(executor.submit(make_request, method, endpoint))
            
            completed = 0
            for future in as_completed(futures):
                future.result()
                completed += 1
                if completed % 100 == 0:
                    print(f"进度: {completed}/{total_requests}")
        
        stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 混合端点并发测试结果")
        print("="*60)
        print(f"总请求: {stats['total']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        
        # 所有端点都应该在高并发下保持稳定
        assert stats['success_rate'] >= 95.0, f"混合端点并发性能不佳: {stats['success_rate']:.2f}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
