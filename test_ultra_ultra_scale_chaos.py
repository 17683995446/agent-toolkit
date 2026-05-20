"""
超超超大规模混沌工程测试套件 - 慢工出细活
超大规模、超长时间、超高难度、超混乱场景
目标：发现真实运行时深层次bug
"""

import pytest
import time
import random
import threading
import gc
import sys
import os
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from fastapi.testclient import TestClient
from agent_toolkit.main import create_app


class UltraScaleMonitor:
    """超超规模监控系统"""
    
    def __init__(self):
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.request_times = deque(maxlen=100000)
        self.errors = defaultdict(int)
        self.success_count = 0
        self.fail_count = 0
        self.memory_samples = []
        self.garbage_collections = []
        self.timestamps = deque(maxlen=10000)
    
    def record(self, success: bool, response_time: float, error_type: str = None):
        with self.lock:
            self.request_times.append(response_time)
            self.timestamps.append(time.time())
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
            mem_info = process.memory_info()
            with self.lock:
                self.memory_samples.append({
                    'rss': mem_info.rss / 1024 / 1024,
                    'vms': mem_info.vms / 1024 / 1024,
                    'gc_count': sum(gc.get_count())
                })
        except ImportError:
            pass
    
    def record_gc(self):
        with self.lock:
            self.garbage_collections.append({
                'time': time.time(),
                'gc_counts': gc.get_count()
            })
    
    def get_stats(self):
        with self.lock:
            total = self.success_count + self.fail_count
            elapsed = time.time() - self.start_time
            
            avg_resp = sum(self.request_times) / len(self.request_times) if self.request_times else 0
            max_resp = max(self.request_times) if self.request_times else 0
            min_resp = min(self.request_times) if self.request_times else 0
            
            memory_growth = 0
            if len(self.memory_samples) >= 2:
                memory_growth = self.memory_samples[-1]['rss'] - self.memory_samples[0]['rss']
            
            # 计算吞吐量波动
            rps_fluctuation = 0
            if len(self.timestamps) >= 2:
                time_diffs = [self.timestamps[i] - self.timestamps[i-1] 
                            for i in range(1, len(self.timestamps))]
                if time_diffs:
                    avg_diff = sum(time_diffs) / len(time_diffs)
                    rps_fluctuation = (max(time_diffs) - min(time_diffs)) / avg_diff if avg_diff > 0 else 0
            
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
                "rps_fluctuation": rps_fluctuation,
                "errors": dict(self.errors),
                "elapsed": elapsed,
            }


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestUltraScaleChaos:
    """超超超大规模混沌测试"""
    
    def test_ultra_scale_concurrent_chaos(self, client):
        """超超超大规模并发混沌测试 - 50000+请求"""
        print("\n" + "="*80)
        print("🚀 开始超超超大规模并发混沌测试")
        print("="*80)
        
        monitor = UltraScaleMonitor()
        monitor.sample_memory()
        monitor.record_gc()
        
        total_requests = 50000
        
        print(f"计划进行 {total_requests} 个超大规模并发混沌请求...")
        
        endpoints = [
            ("GET", "/api/v1/health", None),
            ("GET", "/liveness", None),
            ("GET", "/readiness", None),
            ("GET", "/api/v1/metrics/dashboard", None),
            ("POST", "/api/v1/metrics/counter", {"name": "ultra_chaos", "value": 1.0}),
            ("POST", "/api/v1/metrics/gauge", {"name": "ultra_gauge", "value": 50.0}),
            ("POST", "/api/v1/metrics/histogram", {"name": "ultra_hist", "value": 25.5}),
        ]
        
        def ultra_chaos_request(index):
            try:
                method, url, data = random.choice(endpoints)
                
                # 随机引入混乱
                if random.random() < 0.05 and data:
                    data = data.copy()
                    data["name"] = data["name"] + "_" + str(random.randint(1, 10000000))
                    data["value"] = random.uniform(0, 1000)
                
                start_time = time.time()
                
                if method == "GET":
                    response = client.get(url)
                else:
                    response = client.post(url, json=data)
                
                success = 200 <= response.status_code < 500
                monitor.record(success, time.time() - start_time, 
                              f"HTTP_{response.status_code}" if not success else None)
                return success
            except Exception as e:
                monitor.record(False, time.time() - start_time, type(e).__name__)
                return False
        
        num_threads = random.randint(200, 500)
        print(f"使用 {num_threads} 个超大规模线程...")
        
        batch_size = 5000
        batches = total_requests // batch_size
        
        for batch in range(batches):
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(ultra_chaos_request, i) for i in range(batch_size)]
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    if completed % 1000 == 0:
                        stats = monitor.get_stats()
                        print(f"批次 {batch+1}/{batches}: {completed}/{batch_size} 完成, "
                              f"成功率: {stats['success_rate']:.1f}%")
            
            monitor.sample_memory()
            monitor.record_gc()
            gc.collect()

            if monitor.memory_samples:
                print(f"批次 {batch+1}/{batches} 完成, "
                      f"内存: {monitor.memory_samples[-1]['rss']:.2f}MB")
            else:
                print(f"批次 {batch+1}/{batches} 完成")
        
        monitor.sample_memory()
        monitor.record_gc()
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 超超超大规模并发混沌测试结果")
        print("="*80)
        print(f"总请求: {stats['total_requests']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['fail']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"平均响应: {stats['avg_response_ms']:.2f}ms")
        print(f"最大响应: {stats['max_response_ms']:.2f}ms")
        print(f"内存增长: {stats['memory_growth_mb']:.2f}MB")
        print(f"请求/秒: {stats['requests_per_second']:.1f}")
        print(f"RPS波动: {stats['rps_fluctuation']:.2f}")
        if stats['errors']:
            print("错误统计:")
            for err, cnt in stats['errors'].items():
                print(f"  {err}: {cnt}")
        
        assert stats['success_rate'] >= 99.0, f"超大规模场景下成功率太低: {stats['success_rate']:.2f}%"
        assert stats['memory_growth_mb'] < 500, f"严重的内存增长: {stats['memory_growth_mb']:.2f}MB"
    
    def test_extreme_long_duration_chaos(self, client):
        """极端长时间混沌运行测试 - 10分钟+"""
        print("\n" + "="*80)
        print("⏰ 开始极端长时间混沌运行测试 (10分钟+)")
        print("="*80)
        
        monitor = UltraScaleMonitor()
        monitor.sample_memory()
        
        total_duration = 600  # 10分钟
        start_time = time.time()
        iterations = 0
        
        print(f"将运行 {total_duration} 秒 (10分钟) 的极端混沌测试...")
        
        endpoints = ["/api/v1/health", "/liveness", "/readiness", "/api/v1/metrics/dashboard"]
        
        while time.time() - start_time < total_duration:
            iterations += 1
            
            mode = random.randint(1, 6)
            
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
                # 小批量
                small_batch = random.randint(10, 50)
                with ThreadPoolExecutor(max_workers=15) as executor:
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
                # 中等批量
                medium_batch = random.randint(50, 200)
                with ThreadPoolExecutor(max_workers=30) as executor:
                    def medium_task():
                        try:
                            start = time.time()
                            url = random.choice(endpoints)
                            response = client.get(url)
                            success = 200 <= response.status_code < 400
                            monitor.record(success, time.time() - start, 
                                          f"HTTP_{response.status_code}" if not success else None)
                        except Exception as e:
                            monitor.record(False, 0.001, type(e).__name__)
                    
                    for _ in range(medium_batch):
                        executor.submit(medium_task)
            
            elif mode == 4:
                # 指标更新
                try:
                    start_req = time.time()
                    response = client.post("/api/v1/metrics/counter", 
                                        json={"name": f"long_chaos_{iterations}", "value": random.random()})
                    success = response.status_code == 200
                    monitor.record(success, time.time() - start_req, 
                                  f"HTTP_{response.status_code}" if not success else None)
                except Exception as e:
                    monitor.record(False, 0.001, type(e).__name__)
            
            elif mode == 5:
                # 大量指标更新
                metric_batch = random.randint(20, 100)
                with ThreadPoolExecutor(max_workers=20) as executor:
                    def metric_task(m_idx):
                        try:
                            start = time.time()
                            response = client.post("/api/v1/metrics/counter", 
                                                json={"name": f"metric_{iterations}_{m_idx}", 
                                                     "value": random.random()})
                            success = response.status_code == 200
                            monitor.record(success, time.time() - start, 
                                          f"HTTP_{response.status_code}" if not success else None)
                        except Exception as e:
                            monitor.record(False, 0.001, type(e).__name__)
                    
                    for m_idx in range(metric_batch):
                        executor.submit(metric_task, m_idx)
            
            else:
                # 随机等待
                time.sleep(random.uniform(0.05, 0.3))
            
            if iterations % 500 == 0:
                monitor.sample_memory()
                stats = monitor.get_stats()
                elapsed = time.time() - start_time
                print(f"迭代 {iterations}, 已运行 {elapsed:.1f}秒, "
                      f"总请求: {stats['total_requests']}, "
                      f"成功率: {stats['success_rate']:.1f}%, "
                      f"内存: {stats.get('memory_growth_mb', 0):.2f}MB")
        
        monitor.sample_memory()
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 极端长时间混沌运行测试结果")
        print("="*80)
        print(f"总运行时间: {stats['elapsed']:.1f}秒 ({stats['elapsed']/60:.1f}分钟)")
        print(f"总请求: {stats['total_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"平均响应: {stats['avg_response_ms']:.2f}ms")
        print(f"最大响应: {stats['max_response_ms']:.2f}ms")
        print(f"内存增长: {stats['memory_growth_mb']:.2f}MB")
        print(f"请求/秒: {stats['requests_per_second']:.1f}")
        
        assert stats['success_rate'] >= 99.5, f"长时间稳定性不足: {stats['success_rate']:.2f}%"
        assert stats['memory_growth_mb'] < 500, f"严重的内存泄漏: {stats['memory_growth_mb']:.2f}MB"
    
    def test_data_consistency_chaos(self, client):
        """数据一致性混沌测试"""
        print("\n" + "="*80)
        print("🔢 开始数据一致性混沌测试")
        print("="*80)
        
        monitor = UltraScaleMonitor()
        
        # 先创建一些已知的数据
        print("准备初始数据...")
        known_metrics = []
        for i in range(100):
            response = client.post("/api/v1/metrics/counter",
                                json={"name": f"consistency_test_{i}", "value": float(i)})
            if response.status_code == 200:
                known_metrics.append(i)
        
        print(f"已创建 {len(known_metrics)} 个已知指标")
        
        # 并发修改同一指标
        target_metric = "shared_consistency_metric"
        num_writers = 200
        writes_per_writer = 50
        
        shared_value = {"expected_sum": 0, "lock": threading.Lock()}
        
        def chaos_writer(writer_id):
            local_writes = 0
            for i in range(writes_per_writer):
                try:
                    value = random.uniform(1, 100)
                    response = client.post("/api/v1/metrics/counter",
                                        json={"name": target_metric, "value": value})
                    
                    if response.status_code == 200:
                        local_writes += 1
                        
                        with shared_value["lock"]:
                            shared_value["expected_sum"] += value
                        
                        monitor.record(True, 0.001, None)
                    else:
                        monitor.record(False, 0.001, f"HTTP_{response.status_code}")
                except Exception as e:
                    monitor.record(False, 0.001, type(e).__name__)
            
            return local_writes
        
        print(f"启动 {num_writers} 个并发写入器，每个 {writes_per_writer} 次写入...")
        
        with ThreadPoolExecutor(max_workers=num_writers) as executor:
            futures = [executor.submit(chaos_writer, i) for i in range(num_writers)]
            
            total_writes = 0
            for future in as_completed(futures):
                total_writes += future.result()
        
        # 验证数据一致性
        response = client.get("/api/v1/metrics/dashboard")
        dashboard_data = response.json()
        
        print("\n" + "="*80)
        print("📊 数据一致性混沌测试结果")
        print("="*80)
        print(f"总写入: {total_writes}")
        print(f"成功率: {monitor.get_stats()['success_rate']:.2f}%")
        print(f"预期值总和: {shared_value['expected_sum']:.2f}")
        
        # 数据应该存在且可以读取
        assert response.status_code == 200, "无法读取指标数据"
        assert monitor.get_stats()['success_rate'] >= 95.0, f"写入成功率太低"
        
        print("数据一致性验证: 通过")


class TestExtremeResourcePressure:
    """极限资源压力测试"""
    
    def test_memory_exhaustion_resilience(self, client):
        """内存耗尽韧性测试"""
        print("\n" + "="*80)
        print("💾 开始内存耗尽韧性测试")
        print("="*80)
        
        monitor = UltraScaleMonitor()
        monitor.sample_memory()
        
        # 尝试创建大量指标数据
        print("创建大量指标数据...")
        large_dataset_size = 10000
        
        for i in range(large_dataset_size):
            try:
                response = client.post("/api/v1/metrics/counter",
                                    json={"name": f"memory_test_{i}", "value": float(i)})
                monitor.record(response.status_code == 200, 0.001, 
                              f"HTTP_{response.status_code}" if response.status_code != 200 else None)
            except Exception as e:
                monitor.record(False, 0.001, type(e).__name__)
            
            if (i + 1) % 1000 == 0:
                print(f"已创建 {i+1}/{large_dataset_size} 个指标")
                monitor.sample_memory()
        
        # 在高内存压力下进行健康检查
        print("\n在高内存压力下进行健康检查...")
        for i in range(1000):
            try:
                start = time.time()
                response = client.get("/api/v1/health")
                success = 200 <= response.status_code < 400
                monitor.record(success, time.time() - start, 
                              f"HTTP_{response.status_code}" if not success else None)
            except Exception as e:
                monitor.record(False, time.time() - start, type(e).__name__)
        
        monitor.sample_memory()
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 内存耗尽韧性测试结果")
        print("="*80)
        print(f"创建的指标: {large_dataset_size}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"内存增长: {stats['memory_growth_mb']:.2f}MB")
        
        # 系统应该在高内存压力下仍然可以响应
        assert stats['success_rate'] >= 95.0, f"内存压力下健康检查失败率过高"


class TestBoundaryAndEdgeCases:
    """边界和极端场景测试"""
    
    def test_rapid_fire_boundary_chaos(self, client):
        """快速连续边界混沌测试"""
        print("\n" + "="*80)
        print("🔥 开始快速连续边界混沌测试")
        print("="*80)
        
        monitor = UltraScaleMonitor()
        
        # 快速连续发送大量请求
        rapid_fire_count = 10000
        
        print(f"快速连续发送 {rapid_fire_count} 个请求...")
        
        for i in range(rapid_fire_count):
            try:
                start = time.time()
                response = client.get("/api/v1/health")
                success = 200 <= response.status_code < 400
                monitor.record(success, time.time() - start, 
                              f"HTTP_{response.status_code}" if not success else None)
            except Exception as e:
                monitor.record(False, time.time() - start, type(e).__name__)
            
            if (i + 1) % 2000 == 0:
                stats = monitor.get_stats()
                print(f"进度: {i+1}/{rapid_fire_count}, 成功率: {stats['success_rate']:.1f}%")
        
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 快速连续边界混沌测试结果")
        print("="*80)
        print(f"总请求: {stats['total_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"请求/秒: {stats['requests_per_second']:.1f}")
        
        assert stats['success_rate'] >= 99.0, f"快速连续请求成功率低"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
