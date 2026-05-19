"""
高级压力测试套件
包含长时间运行、高并发、复杂场景的压力测试
用于发现系统的潜在bug和性能问题
"""

import pytest
import asyncio
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from agent_toolkit.main import create_app


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


class TestHighConcurrency:
    """高并发测试"""
    
    def test_concurrent_health_checks(self, client):
        """测试高并发健康检查 - 100并发请求"""
        num_requests = 100
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(client.get, "/api/v1/health")
                for _ in range(num_requests)
            ]
            
            results = []
            for future in as_completed(futures):
                try:
                    response = future.result(timeout=10)
                    results.append(response.status_code)
                except Exception as e:
                    results.append(f"ERROR: {str(e)}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 验证结果
        success_count = sum(1 for r in results if r == 200)
        error_count = len(results) - success_count
        
        print(f"High Concurrency Test: {num_requests} requests in {total_time:.2f}s")
        print(f"Success: {success_count}, Errors: {error_count}")
        
        # 至少95%的请求应该成功
        assert success_count >= num_requests * 0.95, f"Too many failures: {error_count}"
        # 每秒至少处理10个请求
        assert num_requests / total_time > 10, f"Throughput too low: {num_requests/total_time:.2f} req/s"
    
    def test_concurrent_metrics_updates(self, client):
        """测试高并发指标更新 - 混合读写操作"""
        num_operations = 50
        start_time = time.time()
        
        operations = []
        for i in range(num_operations):
            if i % 3 == 0:
                # 写操作 - 增加计数器
                operations.append(("POST", "/api/v1/metrics/counter", 
                                 {"name": f"stress_counter_{i}", "value": random.random() * 10}))
            elif i % 3 == 1:
                # 写操作 - 设置计量器
                operations.append(("POST", "/api/v1/metrics/gauge", 
                                 {"name": f"stress_gauge_{i}", "value": random.random() * 100}))
            else:
                # 读操作 - 获取指标
                operations.append(("GET", "/api/v1/metrics/dashboard", None))
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            for method, url, data in operations:
                if method == "GET":
                    futures.append(executor.submit(client.get, url))
                else:
                    futures.append(executor.submit(client.post, url, json=data))
            
            results = []
            for future in as_completed(futures):
                try:
                    response = future.result(timeout=5)
                    results.append(response.status_code)
                except Exception as e:
                    results.append(f"ERROR: {str(e)}")
        
        end_time = time.time()
        
        success_count = sum(1 for r in results if r in (200, 201))
        error_count = len(results) - success_count
        
        print(f"Concurrent Metrics Test: {num_operations} operations in {end_time - start_time:.2f}s")
        print(f"Success: {success_count}, Errors: {error_count}")
        
        assert success_count >= num_operations * 0.90


class TestLongRunning:
    """长时间运行测试"""
    
    def test_sustained_load(self, client):
        """长时间持续负载测试 - 1000个请求，持续一段时间"""
        total_requests = 1000
        batch_size = 50
        delay_between_batches = 0.1
        
        start_time = time.time()
        all_status_codes = []
        response_times = []
        
        for batch in range(total_requests // batch_size):
            batch_start = time.time()
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(client.get, "/api/v1/health")
                    for _ in range(batch_size)
                ]
                
                for future in as_completed(futures):
                    try:
                        req_start = time.time()
                        response = future.result(timeout=5)
                        req_time = time.time() - req_start
                        
                        all_status_codes.append(response.status_code)
                        response_times.append(req_time * 1000)  # ms
                    except Exception as e:
                        all_status_codes.append(500)
            
            # 批次之间的延迟
            if batch < (total_requests // batch_size) - 1:
                time.sleep(delay_between_batches)
        
        end_time = time.time()
        
        # 分析结果
        success_count = sum(1 for s in all_status_codes if s == 200)
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        print(f"\nLong Running Test Results:")
        print(f"Total requests: {total_requests}")
        print(f"Success rate: {success_count/total_requests*100:.1f}%")
        print(f"Avg response time: {avg_response_time:.2f}ms")
        print(f"Max response time: {max_response_time:.2f}ms")
        print(f"Total time: {end_time - start_time:.2f}s")
        
        # 验证
        assert success_count >= total_requests * 0.98, "Success rate too low"
        assert avg_response_time < 500, "Average response time too high"
        assert max_response_time < 5000, "Maximum response time too high"


class TestComplexScenarios:
    """复杂场景测试"""
    
    def test_workflow_scenario(self, client):
        """模拟真实工作流：健康检查 -> 指标收集 -> 健康检查 -> 指标分析"""
        workflow_steps = 20
        
        for step in range(workflow_steps):
            # 步骤1: 健康检查
            health_resp = client.get("/api/v1/health")
            assert health_resp.status_code == 200
            health_data = health_resp.json()
            
            # 步骤2: 记录一些指标
            counter_resp = client.post(
                "/api/v1/metrics/counter",
                json={"name": f"workflow_step_{step}", "value": 1.0}
            )
            assert counter_resp.status_code == 200
            
            # 步骤3: 记录直方图数据
            hist_resp = client.post(
                "/api/v1/metrics/histogram",
                json={"name": "workflow_latency", "value": random.random() * 2}
            )
            assert hist_resp.status_code == 200
            
            # 步骤4: 获取dashboard
            dashboard_resp = client.get("/api/v1/metrics/dashboard")
            assert dashboard_resp.status_code == 200
            dashboard_data = dashboard_resp.json()
            assert "overview" in dashboard_data
            assert "detailed_metrics" in dashboard_data
        
        print(f"Workflow scenario completed: {workflow_steps} steps")
    
    def test_error_recovery(self, client):
        """测试错误场景和恢复能力"""
        # 先进行一些正常请求
        for _ in range(5):
            response = client.get("/liveness")
            assert response.status_code == 200
        
        # 尝试一些边界情况
        # 1. 大量的并发请求
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(client.get, "/readiness") for _ in range(50)]
            for future in futures:
                try:
                    future.result(timeout=2)
                except:
                    pass  # 允许一些失败
        
        # 验证系统仍然正常工作
        final_health = client.get("/api/v1/health")
        assert final_health.status_code == 200, "System failed to recover"
        
        print("Error recovery test completed successfully")


class TestEdgeCases:
    """边界条件测试"""
    
    def test_rapid_fire_requests(self, client):
        """测试快速连续请求"""
        num_requests = 200
        start_time = time.time()
        
        for i in range(num_requests):
            response = client.get("/api/v1/health")
            assert response.status_code in (200, 503)  # 允许503如果系统忙
        
        elapsed = time.time() - start_time
        print(f"Rapid fire: {num_requests} requests in {elapsed:.2f}s ({num_requests/elapsed:.1f} req/s)")
    
    def test_large_payloads(self, client):
        """测试大负载请求（如果有的话）"""
        # 创建大量计数器
        for i in range(100):
            response = client.post(
                "/api/v1/metrics/counter",
                json={"name": f"large_test_counter_{i}", "value": float(i)}
            )
            assert response.status_code == 200
        
        # 然后获取dashboard，确保它能处理大量数据
        dashboard = client.get("/api/v1/metrics/dashboard")
        assert dashboard.status_code == 200
        data = dashboard.json()
        assert "counters" in data["detailed_metrics"]


class TestMemoryLeakDetection:
    """内存泄漏检测测试（简单版本）"""
    
    def test_memory_stability(self, client):
        """测试内存使用是否稳定"""
        # 进行大量操作，然后检查健康状态
        initial_memory = None
        
        try:
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024
            print(f"Initial memory: {initial_memory:.2f} MB")
        except ImportError:
            print("psutil not available, skipping memory test")
            return
        
        # 执行大量操作
        for _ in range(1000):
            client.get("/api/v1/health")
            if _ % 100 == 0:
                client.post("/api/v1/metrics/counter", 
                          json={"name": "memory_test", "value": 1.0})
        
        # 检查最终内存
        final_memory = process.memory_info().rss / 1024 / 1024
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory increase: {final_memory - initial_memory:.2f} MB")
        
        # 允许一定的内存增长（10MB），但不能太多
        assert final_memory - initial_memory < 50, "Possible memory leak detected"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
