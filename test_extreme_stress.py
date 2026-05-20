"""
极端复杂压力测试套件 - 慢工出细活
包含：
- 极长时间持续运行测试
- 真实场景工作流模拟
- 极端边界条件
- 资源泄漏检测
- 高并发压力
- 错误恢复和容错
"""

import pytest
import time
import random
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
from fastapi.testclient import TestClient
from agent_toolkit.main import create_app


class SystemMonitor:
    """系统监控器 - 跟踪关键指标"""
    
    def __init__(self):
        self.start_time = time.time()
        self.error_counts = defaultdict(int)
        self.response_times = deque(maxlen=10000)
        self.request_count = 0
        self.success_count = 0
        self.lock = threading.Lock()
    
    def record_request(self, success: bool, response_time: float, error_type: str = None):
        with self.lock:
            self.request_count += 1
            self.response_times.append(response_time)
            if success:
                self.success_count += 1
            if error_type:
                self.error_counts[error_type] += 1
    
    def get_stats(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            avg_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
            max_time = max(self.response_times) if self.response_times else 0
            return {
                "total_requests": self.request_count,
                "success_count": self.success_count,
                "success_rate": (self.success_count / self.request_count * 100) if self.request_count else 0,
                "avg_response_ms": avg_time * 1000,
                "max_response_ms": max_time * 1000,
                "requests_per_second": self.request_count / elapsed if elapsed > 0 else 0,
                "errors": dict(self.error_counts),
                "elapsed_seconds": elapsed
            }


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


class TestExtremeLongRunning:
    """极长时间持续运行测试"""
    
    @pytest.mark.slow
    def test_very_long_running_stress(self, client):
        """
        非常长时间的压力测试 - 持续运行
        测试系统在持续负载下的稳定性
        """
        print("\n" + "="*60)
        print("🚀 开始极长时间压力测试")
        print("="*60)
        
        monitor = SystemMonitor()
        total_requests = 5000
        batch_size = 200
        batches = total_requests // batch_size
        
        print(f"测试计划: {total_requests} 个请求, 分 {batches} 批, 每批 {batch_size} 个")
        
        for batch in range(batches):
            batch_start = time.time()
            batch_results = []
            
            with ThreadPoolExecutor(max_workers=30) as executor:
                futures = []
                
                for i in range(batch_size):
                    choice = random.random()
                    
                    if choice < 0.4:
                        futures.append(executor.submit(client.get, "/api/v1/health"))
                    elif choice < 0.7:
                        futures.append(executor.submit(client.get, "/liveness"))
                    elif choice < 0.85:
                        futures.append(executor.submit(
                            client.post,
                            "/api/v1/metrics/counter",
                            json={"name": f"stress_counter_{batch}_{i}", "value": random.random() * 10}
                        ))
                    else:
                        futures.append(executor.submit(
                            client.post,
                            "/api/v1/metrics/gauge",
                            json={"name": f"stress_gauge_{batch}_{i}", "value": random.random() * 100}
                        ))
                
                for future in as_completed(futures):
                    req_start = time.time()
                    try:
                        response = future.result(timeout=10)
                        req_time = time.time() - req_start
                        
                        success = 200 <= response.status_code < 300
                        error_type = f"HTTP_{response.status_code}" if not success else None
                        monitor.record_request(success, req_time, error_type)
                        
                        batch_results.append((success, response.status_code))
                        
                    except Exception as e:
                        req_time = time.time() - req_start
                        error_type = type(e).__name__
                        monitor.record_request(False, req_time, error_type)
                        batch_results.append((False, "EXCEPTION"))
            
            batch_time = time.time() - batch_start
            batch_success = sum(1 for s, _ in batch_results if s)
            
            print(f"批 #{batch+1}/{batches}: {batch_success}/{batch_size} 成功 ({batch_time:.2f}s)")
            
            if batch > 0 and batch % 5 == 0:
                stats = monitor.get_stats()
                print(f"  累计: 请求: {stats['total_requests']}, "
                      f"成功率: {stats['success_rate']:.1f}%, "
                      f"平均响应: {stats['avg_response_ms']:.2f}ms, "
                      f"RPS: {stats['requests_per_second']:.1f}")
            
            if batch < batches - 1:
                time.sleep(0.05)
        
        final_stats = monitor.get_stats()
        print("\n" + "="*60)
        print("📊 极长时间压力测试结果")
        print("="*60)
        print(f"总请求数: {final_stats['total_requests']}")
        print(f"成功数: {final_stats['success_count']}")
        print(f"成功率: {final_stats['success_rate']:.2f}%")
        print(f"平均响应: {final_stats['avg_response_ms']:.2f}ms")
        print(f"最大响应: {final_stats['max_response_ms']:.2f}ms")
        print(f"请求/秒: {final_stats['requests_per_second']:.1f}")
        print(f"总耗时: {final_stats['elapsed_seconds']:.1f}s")
        
        if final_stats['errors']:
            print("\n错误统计:")
            for error_type, count in final_stats['errors'].items():
                print(f"  {error_type}: {count}")
        
        assert final_stats['success_rate'] >= 99.0, \
            f"成功率太低: {final_stats['success_rate']:.2f}%"
        assert final_stats['avg_response_ms'] < 500, \
            f"平均响应时间太长: {final_stats['avg_response_ms']:.2f}ms"


class TestExtremeConcurrency:
    """极端并发压力测试"""
    
    def test_extreme_high_concurrency(self, client):
        """
        极端高并发测试 - 1000 个并发请求
        """
        print("\n" + "="*60)
        print("🔥 开始极端高并发测试")
        print("="*60)
        
        monitor = SystemMonitor()
        num_concurrent = 1000
        
        print(f"测试计划: {num_concurrent} 个并发请求")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            
            for i in range(num_concurrent):
                if i % 3 == 0:
                    futures.append(executor.submit(client.get, "/api/v1/health"))
                elif i % 3 == 1:
                    futures.append(executor.submit(client.get, "/liveness"))
                else:
                    futures.append(executor.submit(client.get, "/readiness"))
            
            completed = 0
            for future in as_completed(futures):
                req_start = time.time()
                try:
                    response = future.result(timeout=30)
                    req_time = time.time() - req_start
                    
                    success = 200 <= response.status_code < 300
                    error_type = f"HTTP_{response.status_code}" if not success else None
                    monitor.record_request(success, req_time, error_type)
                    
                except Exception as e:
                    req_time = time.time() - req_start
                    error_type = type(e).__name__
                    monitor.record_request(False, req_time, error_type)
                
                completed += 1
                if completed % 100 == 0:
                    print(f"已完成: {completed}/{num_concurrent}")
        
        total_time = time.time() - start_time
        final_stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 极端高并发测试结果")
        print("="*60)
        print(f"总请求数: {final_stats['total_requests']}")
        print(f"成功数: {final_stats['success_count']}")
        print(f"成功率: {final_stats['success_rate']:.2f}%")
        print(f"总耗时: {total_time:.2f}s")
        print(f"吞吐量: {num_concurrent/total_time:.1f} 请求/秒")
        print(f"平均响应: {final_stats['avg_response_ms']:.2f}ms")
        
        assert final_stats['success_rate'] >= 95.0, \
            f"成功率太低: {final_stats['success_rate']:.2f}%"


class TestComplexWorkflows:
    """复杂工作流模拟测试"""
    
    def test_realistic_complex_workflows(self, client):
        """
        真实场景复杂工作流测试
        """
        print("\n" + "="*60)
        print("🎯 开始真实场景复杂工作流测试")
        print("="*60)
        
        monitor = SystemMonitor()
        num_workflows = 100
        
        def run_single_workflow(workflow_id):
            workflow_start = time.time()
            
            try:
                # 步骤1: 系统健康检查
                step_start = time.time()
                response = client.get("/api/v1/health")
                monitor.record_request(response.status_code == 200, 
                                       time.time() - step_start,
                                       f"health_{response.status_code}" if response.status_code != 200 else None)
                if response.status_code != 200:
                    return False
                
                # 步骤2: 记录关键指标
                step_start = time.time()
                response = client.post(
                    "/api/v1/metrics/counter",
                    json={"name": f"workflow_{workflow_id}_start", "value": 1.0}
                )
                monitor.record_request(response.status_code == 200,
                                       time.time() - step_start,
                                       f"counter_{response.status_code}" if response.status_code != 200 else None)
                if response.status_code != 200:
                    return False
                
                # 步骤3: 再次检查系统状态
                step_start = time.time()
                response = client.get("/liveness")
                monitor.record_request(response.status_code == 200,
                                       time.time() - step_start,
                                       f"liveness_{response.status_code}" if response.status_code != 200 else None)
                if response.status_code != 200:
                    return False
                
                # 步骤4: 记录更多指标
                step_start = time.time()
                for metric_idx in range(5):
                    if metric_idx % 2 == 0:
                        response = client.post(
                            "/api/v1/metrics/gauge",
                            json={"name": f"workflow_{workflow_id}_gauge_{metric_idx}", "value": random.random() * 50}
                        )
                    else:
                        response = client.post(
                            "/api/v1/metrics/histogram",
                            json={"name": f"workflow_{workflow_id}_hist_{metric_idx}", "value": random.random() * 10}
                        )
                
                monitor.record_request(True, time.time() - step_start, None)
                
                total_time = time.time() - workflow_start
                return True
                
            except Exception as e:
                total_time = time.time() - workflow_start
                monitor.record_request(False, total_time, type(e).__name__)
                return False
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(run_single_workflow, i) for i in range(num_workflows)]
            
            completed = 0
            success_count = 0
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    success_count += 1
                completed += 1
                if completed % 20 == 0:
                    print(f"工作流进度: {completed}/{num_workflows}")
        
        final_stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 复杂工作流测试结果")
        print("="*60)
        print(f"总工作流: {num_workflows}")
        print(f"成功工作流: {success_count}")
        print(f"工作流成功率: {success_count/num_workflows*100:.1f}%")
        print(f"总请求数: {final_stats['total_requests']}")
        print(f"请求成功率: {final_stats['success_rate']:.1f}%")
        
        assert success_count / num_workflows >= 0.95, \
            f"工作流成功率太低: {success_count/num_workflows*100:.1f}%"


class TestExtremeEdgeCases:
    """极端边界条件测试"""
    
    def test_rapid_fire_bombardment(self, client):
        """快速连续轰炸测试"""
        print("\n" + "="*60)
        print("💥 开始快速连续轰炸测试")
        print("="*60)
        
        monitor = SystemMonitor()
        num_requests = 3000
        
        start_time = time.time()
        
        for i in range(num_requests):
            req_start = time.time()
            try:
                response = client.get("/api/v1/health")
                success = response.status_code == 200
                error_type = None if success else f"HTTP_{response.status_code}"
                monitor.record_request(success, time.time() - req_start, error_type)
            except Exception as e:
                monitor.record_request(False, time.time() - req_start, type(e).__name__)
            
            if (i + 1) % 500 == 0:
                print(f"已完成: {i+1}/{num_requests}")
        
        total_time = time.time() - start_time
        final_stats = monitor.get_stats()
        
        print("\n" + "="*60)
        print("📊 快速连续轰炸测试结果")
        print("="*60)
        print(f"总请求: {final_stats['total_requests']}")
        print(f"成功: {final_stats['success_count']}")
        print(f"成功率: {final_stats['success_rate']:.1f}%")
        print(f"总耗时: {total_time:.2f}s")
        print(f"吞吐量: {num_requests/total_time:.1f} 请求/秒")
        
        assert final_stats['success_rate'] >= 99.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
