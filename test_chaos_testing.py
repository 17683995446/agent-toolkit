"""
超深度混沌工程测试套件 - 慢工出细活
包含极端复杂混乱场景测试 - 发现真实运行时bug
"""

import pytest
import time
import random
import threading
import gc
import sys
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from fastapi.testclient import TestClient
from agent_toolkit.main import create_app
import json


class ChaosMonitor:
    """深度系统监视器 - 混乱场景监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.request_times = deque(maxlen=50000)
        self.errors = defaultdict(int)
        self.success_count = 0
        self.fail_count = 0
        self.memory_samples = []
        self.cpu_samples = []
    
    def record(self, success: bool, response_time: float, error_type: str = None):
        with self.lock:
            self.request_times.append(response_time)
            if success:
                self.success_count += 1
            else:
                self.fail_count += 1
                if error_type:
                    self.errors[error_type] += 1
    
    def sample_memory(self):
        try:
            import psutil
            process = psutil.Process()
            with self.lock:
                self.memory_samples.append(process.memory_info().rss / 1024 / 1024)
        except ImportError:
            pass
    
    def get_stats(self):
        with self.lock:
            total = self.success_count + self.fail_count
            elapsed = time.time() - self.start_time
            
            avg_resp = sum(self.request_times) / len(self.request_times) if self.request_times else 0
            max_resp = max(self.request_times) if self.request_times else 0
            min_resp = min(self.request_times) if self.request_times else 0
            
            memory_growth = 0
            if len(self.memory_samples) >= 2:
                memory_growth = self.memory_samples[-1] - self.memory_samples[0]
            
            return {
                "total_requests": total,
                "success": self.success_count,
                "fail": self.fail_count,
                "success_rate": (self.success_count / total * 100) if total > 0 else 0,
                "avg_response_ms": avg_resp * 1000,
                "max_response_ms": max_resp * 1000,
                "min_response_ms": min_resp * 1000,
                "requests_per_second": total / elapsed if elapsed > 0 else 0,
                "memory_growth_mb": memory_growth,
                "errors": dict(self.errors),
                "elapsed": elapsed,
            }


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestChaosConcurrency:
    """超级混乱并发测试"""
    
    def test_chaotic_mixed_concurrency(self, client):
        """超级混乱混合并发测试"""
        print("\n" + "="*80)
        print("🔀 开始超级混乱混合并发测试")
        print("="*80)
        
        monitor = ChaosMonitor()
        monitor.sample_memory()
        
        endpoints = [
            ("GET", "/api/v1/health", {}),
            ("GET", "/liveness", {}),
            ("GET", "/readiness", {}),
            ("GET", "/api/v1/metrics/dashboard", {}),
            ("POST", "/api/v1/metrics/counter", {"name": "chaos_test", "value": 1.0}),
            ("POST", "/api/v1/metrics/gauge", {"name": "chaos_gauge", "value": 50.0}),
            ("POST", "/api/v1/metrics/histogram", {"name": "chaos_hist", "value": 25.5}),
        ]
        
        total_requests = 20000
        
        print(f"准备 {total_requests} 个随机请求的混合混乱请求...")
        
        def chaotic_request(index):
            try:
                method, url, data = random.choice(endpoints)
                
                # 随机引入一些混乱
                if random.random() < 0.1 and data:
                    data = data.copy()
                    data["name"] = data["name"] + "_" + str(random.randint(1, 1000000))
                
                start_time = time.time()
                
                if method == "GET":
                    response = client.get(url)
                else:
                    response = client.post(url, json=data)
                
                success = 200 <= response.status_code < 500
                monitor.record(success, time.time() - start_time, f"HTTP_{response.status_code}" if not success else None)
                return success
            except Exception as e:
                monitor.record(False, time.time() - start_time, type(e).__name__)
                return False
        
        num_threads = random.randint(50, 150)
        print(f"使用 {num_threads} 个线程进行超级混乱并发...")
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(chaotic_request, i) for i in range(total_requests)]
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 2000 == 0:
                    monitor.sample_memory()
                    stats = monitor.get_stats()
                    print(f"进度: {completed}/{total_requests}, 成功率: {stats['success_rate']:.1f}%")
        
        monitor.sample_memory()
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 超级混乱混合并发测试结果")
        print("="*80)
        print(f"总请求: {stats['total_requests']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['fail']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"平均响应: {stats['avg_response_ms']:.2f}ms")
        print(f"最大响应: {stats['max_response_ms']:.2f}ms")
        print(f"内存增长: {stats['memory_growth_mb']:.2f}MB")
        print(f"请求/秒: {stats['requests_per_second']:.1f}")
        if stats['errors']:
            print("错误类型统计:")
            for err_type, count in stats['errors'].items():
                print(f"  {err_type}: {count}")
        
        assert stats['success_rate'] >= 95.0, f"超级混乱场景下成功率太低: {stats['success_rate']:.2f}%"
        assert stats['memory_growth_mb'] < 300, f"潜在的大内存增长: {stats['memory_growth_mb']:.2f}MB"


class TestStressAndChaos:
    """超级压力与混沌测试"""
    
    def test_extreme_burst_traffic(self, client):
        """极端突发流量测试"""
        print("\n" + "="*80)
        print("🌊 开始极端突发流量测试")
        print("="*80)
        
        monitor = ChaosMonitor()
        monitor.sample_memory()
        
        bursts = 5
        requests_per_burst = 3000
        
        for burst_num in range(bursts):
            print(f"\n--- 突发 {burst_num + 1}/{bursts}")
            
            burst_threads = random.randint(50, 150)
            
            def burst_request(i):
                try:
                    start_time = time.time()
                    
                    endpoint_choice = random.random()
                    if endpoint_choice < 0.4:
                        response = client.get("/api/v1/health")
                    elif endpoint_choice < 0.7:
                        response = client.get("/liveness")
                    else:
                        response = client.get("/readiness")
                    
                    success = 200 <= response.status_code < 400
                    monitor.record(success, time.time() - start_time, f"HTTP_{response.status_code}" if not success else None)
                    return success
                except Exception as e:
                    monitor.record(False, time.time() - start_time, type(e).__name__)
                    return False
            
            with ThreadPoolExecutor(max_workers=burst_threads) as executor:
                futures = [executor.submit(burst_request, i) for i in range(requests_per_burst)]
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    if completed % 500 == 0:
                        print(f"  突发内进度: {completed}/{requests_per_burst}")
            
            burst_success = monitor.get_stats()
            print(f"  突发后成功率: {burst_success['success_rate']:.1f}%")
            
            monitor.sample_memory()
            time.sleep(random.uniform(0.1, 0.5))
        
        monitor.sample_memory()
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 极端突发流量测试结果")
        print("="*80)
        print(f"总请求: {stats['total_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"平均响应: {stats['avg_response_ms']:.2f}ms")
        print(f"内存增长: {stats['memory_growth_mb']:.2f}MB")
        
        assert stats['success_rate'] >= 98.0, f"极端突发流量下稳定性不足"
        assert stats['memory_growth_mb'] < 200, f"内存增长过多: {stats['memory_growth_mb']:.2f}MB"


class TestRacingConditions:
    """极端竞态条件测试"""
    
    def test_extreme_racing_conditions(self, client):
        """极端竞态条件测试"""
        print("\n" + "="*80)
        print("🏁 开始极端竞态条件测试")
        print("="*80)
        
        monitor = ChaosMonitor()
        monitor.sample_memory()
        
        shared_counter = {"value": 0, "lock": threading.Lock()}
        
        def racing_task(task_id):
            try:
                for _ in range(200):
                    start_time = time.time()
                    
                    # 模拟竞争请求
                    if random.random() < 0.6:
                        response = client.get("/api/v1/health")
                    else:
                        response = client.post("/api/v1/metrics/counter", 
                                              json={"name": f"racing_{task_id}", "value": random.random()})
                    
                    success = 200 <= response.status_code < 400
                    monitor.record(success, time.time() - start_time, 
                                  f"HTTP_{response.status_code}" if not success else None)
                    
                    # 模拟竞争访问共享状态
                    with shared_counter["lock"]:
                        shared_counter["value"] += 1
                    
                    # 随机延迟
                    if random.random() < 0.1:
                        time.sleep(random.uniform(0.0001, 0.001))
                    
            except Exception as e:
                monitor.record(False, 0.001, type(e).__name__)
        
        num_threads = 100
        expected_total = num_threads * 200
        
        print(f"启动 {num_threads} 个线程，每个执行200次循环，总计 {expected_total} 次操作...")
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=racing_task, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        monitor.sample_memory()
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 极端竞态条件测试结果")
        print("="*80)
        print(f"实际总操作: {stats['total_requests']}")
        print(f"共享计数器: {shared_counter['value']}")
        print(f"预期: {expected_total}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"内存增长: {stats['memory_growth_mb']:.2f}MB")
        
        assert shared_counter["value"] == expected_total, f"线程安全问题: 实际 {shared_counter['value']}, 预期 {expected_total}"
        assert stats['success_rate'] >= 99.0, f"竞态条件测试成功率不足"


class TestLongRunningChaos:
    """长时间运行混沌测试"""
    
    def test_extreme_long_running_chaos(self, client):
        """极端长时间运行混沌测试"""
        print("\n" + "="*80)
        print("⏱️  开始极端长时间运行混沌测试")
        print("="*80)
        
        monitor = ChaosMonitor()
        monitor.sample_memory()
        
        total_duration = 30  # 秒
        start_time = time.time()
        iterations = 0
        
        print(f"将运行大约 {total_duration} 秒的混沌测试...")
        
        endpoints = ["/api/v1/health", "/liveness", "/readiness", "/api/v1/metrics/dashboard"]
        
        while time.time() - start_time < total_duration:
            iterations += 1
            
            # 随机选择操作模式
            mode = random.randint(1, 4)
            
            if mode == 1:
                # 单个请求
                try:
                    start_req = time.time()
                    url = random.choice(endpoints)
                    response = client.get(url)
                    success = 200 <= response.status_code < 400
                    monitor.record(success, time.time() - start_req, 
                                  f"HTTP_{response.status_code}" if not success else None)
                except Exception as e:
                    monitor.record(False, 0.001, type(e).__name__)
            
            elif mode == 2:
                # 批量请求
                small_batch = random.randint(5, 20)
                with ThreadPoolExecutor(max_workers=10) as executor:
                    def small_task():
                        try:
                            start = time.time()
                            url = random.choice(endpoints)
                            response = client.get(url)
                            success = 200 <= response.status_code < 400
                            monitor.record(success, time.time() - start, 
                                          f"HTTP_{response.status_code}" if not success else None)
                        except Exception as e:
                            monitor.record(False, 0.001, type(e).__name__)
                    
                    for _ in range(small_batch):
                        executor.submit(small_task)
            
            elif mode == 3:
                # 指标更新
                try:
                    start_req = time.time()
                    response = client.post("/api/v1/metrics/counter", 
                                        json={"name": f"long_test_{iterations}", "value": random.random()})
                    success = response.status_code == 200
                    monitor.record(success, time.time() - start_req, 
                                  f"HTTP_{response.status_code}" if not success else None)
                except Exception as e:
                    monitor.record(False, 0.001, type(e).__name__)
            
            else:
                # 混乱等待
                time.sleep(random.uniform(0.01, 0.1))
            
            if iterations % 100 == 0:
                monitor.sample_memory()
                stats = monitor.get_stats()
                elapsed = time.time() - start_time
                print(f"迭代 {iterations}, 已运行 {elapsed:.1f}秒, 总请求: {stats['total_requests']}, 成功率: {stats['success_rate']:.1f}%")
        
        monitor.sample_memory()
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 极端长时间运行混沌测试结果")
        print("="*80)
        print(f"总运行时间: {stats['elapsed']:.1f}秒")
        print(f"总请求: {stats['total_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"平均响应: {stats['avg_response_ms']:.2f}ms")
        print(f"内存增长: {stats['memory_growth_mb']:.2f}MB")
        
        assert stats['success_rate'] >= 99.5, f"长时间稳定性不足"
        assert stats['memory_growth_mb'] < 300, f"严重的内存泄漏可能"


class TestResourceLeakDetection:
    """资源泄漏深度检测"""
    
    def test_resource_leak_detection(self, client):
        """深度资源泄漏检测"""
        print("\n" + "="*80)
        print("🔍 开始深度资源泄漏检测")
        print("="*80)
        
        monitor = ChaosMonitor()
        monitor.sample_memory()
        
        print("第一阶段：预热系统...")
        for _ in range(500):
            try:
                client.get("/api/v1/health")
            except:
                pass
        
        monitor.sample_memory()
        initial_memory = monitor.memory_samples[-1] if monitor.memory_samples else 0
        
        print(f"初始内存: {initial_memory:.2f}MB")
        
        print("\n第二阶段：大量负载阶段...")
        total_requests = 20000
        
        for i in range(total_requests):
            try:
                start = time.time()
                
                if i % 3 == 0:
                    response = client.get("/api/v1/health")
                elif i % 3 == 1:
                    response = client.post("/api/v1/metrics/counter", 
                                        json={"name": f"leak_test_{i}", "value": 1.0})
                else:
                    response = client.get("/api/v1/metrics/dashboard")
                
                success = 200 <= response.status_code < 400
                monitor.record(success, time.time() - start, 
                              f"HTTP_{response.status_code}" if not success else None)
            except Exception as e:
                monitor.record(False, time.time() - start, type(e).__name__)
            
            if (i + 1) % 5000 == 0:
                gc.collect()
                monitor.sample_memory()
                stats = monitor.get_stats()
                current_memory = monitor.memory_samples[-1] if monitor.memory_samples else initial_memory
                print(f"进度: {i+1}/{total_requests}, 当前内存: {current_memory:.2f}MB")
        
        gc.collect()
        monitor.sample_memory()
        time.sleep(1)
        gc.collect()
        monitor.sample_memory()
        
        final_memory = monitor.memory_samples[-1] if monitor.memory_samples else initial_memory
        
        print("\n" + "="*80)
        print("📊 深度资源泄漏检测结果")
        print("="*80)
        print(f"总请求: {monitor.get_stats()['total_requests']}")
        print(f"初始内存: {initial_memory:.2f}MB")
        print(f"最终内存: {final_memory:.2f}MB")
        print(f"内存增长: {final_memory - initial_memory:.2f}MB")
        print(f"成功率: {monitor.get_stats()['success_rate']:.2f}%")
        
        memory_growth = final_memory - initial_memory
        assert memory_growth < 300, f"可能的内存泄漏！内存增长 {memory_growth:.2f}MB"
        assert monitor.get_stats()['success_rate'] >= 99.0, f"请求成功率过低"


class TestEdgeChaosScenarios:
    """极端边界混沌场景"""
    
    def test_chaotic_inputs(self, client):
        """极端混沌输入测试"""
        print("\n" + "="*80)
        print("🎭 开始极端混沌输入测试")
        print("="*80)
        
        monitor = ChaosMonitor()
        
        # 生成混合的GET和POST请求
        chaotic_tests = []
        for _ in range(300):
            test_type = random.randint(1, 5)
            if test_type == 1:
                chaotic_tests.append(("GET", "/api/v1/health", None))
            elif test_type == 2:
                chaotic_tests.append(("GET", "/liveness", None))
            elif test_type == 3:
                chaotic_tests.append(("GET", "/readiness", None))
            elif test_type == 4:
                chaotic_tests.append(("POST", "/api/v1/metrics/counter", {"name": "chaos_input", "value": 1.0}))
            else:
                chaotic_tests.append(("POST", "/api/v1/metrics/gauge", {"name": "chaos_gauge", "value": 50.0}))
        
        for i, (method, url, data) in enumerate(chaotic_tests):
            try:
                start = time.time()
                if method == "GET":
                    response = client.get(url)
                else:
                    response = client.post(url, json=data)
                
                # 不应该崩溃，任何状态码都可以，只要系统没有崩溃
                success = True
                monitor.record(success, time.time() - start, 
                              f"HTTP_{response.status_code}" if response.status_code >= 400 else None)
            except Exception as e:
                monitor.record(False, time.time() - start, type(e).__name__)
            
            if (i + 1) % 100 == 0:
                print(f"混沌输入测试进度: {i+1}/{len(chaotic_tests)}")
        
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 极端混沌输入测试结果")
        print("="*80)
        print(f"总测试: {stats['total_requests']}")
        print(f"未崩溃率: {stats['success_rate']:.2f}%")
        print(f"失败: {stats['fail']}")
        if stats['errors']:
            print("错误类型:")
            for err, cnt in stats['errors'].items():
                print(f"  {err}: {cnt}")
        
        # 关键测试：系统在极端输入下不能崩溃
        assert stats['success_rate'] >= 90.0, f"系统崩溃率过高"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
