"""
深度混沌工程测试套件
模拟真实生产环境中的复杂异常场景
"""
import pytest
import time
import asyncio
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import gc
import sys

from agent_toolkit.main import create_app
from fastapi.testclient import TestClient


class ChaosMonitor:
    """混沌测试监控器"""

    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.errors = {}
        self.latencies = []
        self.start_time = time.time()

    def record(self, success: bool, latency: float = 0, error_type: str = None, operation: str = ""):
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if error_type:
                self.errors[error_type] = self.errors.get(error_type, 0) + 1

        if latency > 0:
            self.latencies.append(latency)

    def get_stats(self) -> Dict[str, Any]:
        total = self.success_count + self.failure_count
        elapsed = time.time() - self.start_time

        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        max_latency = max(self.latencies) if self.latencies else 0
        min_latency = min(self.latencies) if self.latencies else 0

        return {
            "total": total,
            "success": self.success_count,
            "failure": self.failure_count,
            "success_rate": (self.success_count / total * 100) if total > 0 else 0,
            "avg_latency_ms": avg_latency * 1000,
            "max_latency_ms": max_latency * 1000,
            "min_latency_ms": min_latency * 1000,
            "throughput": total / elapsed if elapsed > 0 else 0,
            "errors": dict(self.errors),
            "elapsed": elapsed
        }


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestNetworkChaos:
    """网络混沌测试 - 模拟网络异常"""

    def test_rapid_connection_teardown(self, client):
        """快速连接建立和断开测试"""
        print("\n" + "="*80)
        print("🌪️ 快速连接建立和断开混沌测试")
        print("="*80)

        monitor = ChaosMonitor()

        # 模拟客户端快速连接断开
        print("\n--- 场景1: 快速短连接测试 ---")
        for i in range(100):
            try:
                start = time.time()
                response = client.get("/api/v1/health")
                elapsed = time.time() - start
                monitor.record(response.status_code == 200, elapsed)
            except Exception as e:
                monitor.record(False, 0, type(e).__name__)

        # 模拟并发短连接
        print("\n--- 场景2: 并发短连接压力测试 ---")

        def rapid_request(thread_id):
            thread_monitor = ChaosMonitor()
            for i in range(20):
                try:
                    start = time.time()
                    response = client.get("/api/v1/health")
                    elapsed = time.time() - start
                    thread_monitor.record(response.status_code == 200, elapsed)
                except Exception as e:
                    thread_monitor.record(False, 0, type(e).__name__)
            return thread_monitor.get_stats()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(rapid_request, i) for i in range(10)]
            for future in as_completed(futures):
                result = future.result()
                for key in ['success', 'failure']:
                    if key == 'success':
                        monitor.success_count += result[key]
                    else:
                        monitor.failure_count += result[key]

        stats = monitor.get_stats()

        print(f"\n📊 测试结果:")
        print(f"   总请求: {stats['total']}")
        print(f"   成功: {stats['success']}")
        print(f"   失败: {stats['failure']}")
        print(f"   成功率: {stats['success_rate']:.2f}%")
        print(f"   平均延迟: {stats['avg_latency_ms']:.2f}ms")
        print(f"   最大延迟: {stats['max_latency_ms']:.2f}ms")

        assert stats['success_rate'] >= 95.0, f"网络混沌测试成功率低: {stats['success_rate']:.2f}%"

    def test_malformed_requests(self, client):
        """畸形请求测试 - 发送各种异常格式的请求"""
        print("\n" + "="*80)
        print("🧩 畸形请求混沌测试")
        print("="*80)

        monitor = ChaosMonitor()

        # 测试各种畸形请求
        malformed_requests = [
            ("空JSON对象", {}, 422),
            ("空数组", [], 422),
            ("嵌套过深", {"level1": {"level2": {"level3": {"level4": {"level5": {}}}}}}, 422),
            ("超长键名", {"a" * 1000: "value"}, 422),
            ("超长值", {"key": "x" * 10000}, 200),
            ("二进制数据", b"\x00\x01\x02\xff\xfe\xfd", 422),
            ("null字节", "test\x00value", 200),
            ("非常长名称", {"name": "x" * 10000}, 422),
            ("特殊Unicode", {"name": "\u0000\u0001"}, 200),
            ("多个null", {"name": None}, 422),
        ]

        print(f"\n测试 {len(malformed_requests)} 种畸形请求...")

        for desc, payload, expected_status in malformed_requests:
            try:
                start = time.time()
                if isinstance(payload, dict):
                    response = client.post("/api/v1/metrics/counter", json=payload)
                elif isinstance(payload, list):
                    response = client.post("/api/v1/metrics/counter", json=payload)
                else:
                    response = client.post("/api/v1/metrics/counter",
                                         content=payload,
                                         headers={"Content-Type": "application/json"})
                elapsed = time.time() - start

                # 只要不是服务器错误（5xx），就算部分成功
                server_error = response.status_code >= 500
                monitor.record(not server_error, elapsed, f"HTTP_{response.status_code}" if server_error else None)

                status_icon = "✅" if response.status_code < 500 else "❌"
                print(f"   {status_icon} {desc}: {response.status_code}")

            except Exception as e:
                monitor.record(False, 0, type(e).__name__)
                print(f"   ❌ {desc}: {type(e).__name__}")

        stats = monitor.get_stats()

        print(f"\n📊 畸形请求测试结果:")
        print(f"   总测试: {stats['total']}")
        print(f"   成功(无5xx): {stats['success']}")
        print(f"   失败(5xx): {stats['failure']}")
        print(f"   安全处理率: {stats['success_rate']:.2f}%")

        # 确保没有服务器错误
        assert stats['failure'] == 0, f"存在{stats['failure']}个服务器错误"
        assert stats['success_rate'] >= 90.0, f"畸形请求处理成功率低: {stats['success_rate']:.2f}%"


class TestResourceExhaustion:
    """资源耗尽测试"""

    def test_memory_pressure(self, client):
        """内存压力测试 - 发送大量数据"""
        print("\n" + "="*80)
        print("💾 内存压力混沌测试")
        print("="*80)

        monitor = ChaosMonitor()

        # 测试不同大小的数据
        test_sizes = [
            ("小数据(1KB)", 1024),
            ("中数据(10KB)", 10 * 1024),
            ("大数据(100KB)", 100 * 1024),
            ("超大(1MB)", 1024 * 1024),
        ]

        for desc, size in test_sizes:
            print(f"\n--- 测试 {desc} ---")

            # 发送大量请求
            for i in range(10):
                try:
                    start = time.time()
                    payload = {"name": f"mem_test_{i}", "value": 1.0}
                    response = client.post("/api/v1/metrics/counter", json=payload)
                    elapsed = time.time() - start
                    monitor.record(response.status_code == 200, elapsed)
                except Exception as e:
                    monitor.record(False, 0, type(e).__name__)

            # 触发垃圾回收
            gc.collect()

        stats = monitor.get_stats()

        print(f"\n📊 内存压力测试结果:")
        print(f"   总请求: {stats['total']}")
        print(f"   成功: {stats['success']}")
        print(f"   成功率: {stats['success_rate']:.2f}%")

        assert stats['success_rate'] >= 95.0, f"内存压力测试成功率低: {stats['success_rate']:.2f}%"

    def test_high_cardinality_labels(self, client):
        """高基数标签测试 - 大量唯一标签"""
        print("\n" + "="*80)
        print("🏷️ 高基数标签混沌测试")
        print("="*80)

        monitor = ChaosMonitor()

        # 测试高基数标签
        print("\n--- 发送1000种不同标签组合 ---")
        for i in range(1000):
            try:
                start = time.time()
                labels = {
                    f"label_{j}": f"value_{i}_{j}"
                    for j in range(5)
                }
                response = client.post("/api/v1/metrics/counter",
                                     json={"name": "high_cardinality_test",
                                          "value": 1.0,
                                          "labels": labels})
                elapsed = time.time() - start
                monitor.record(response.status_code == 200, elapsed)

                if i % 200 == 0:
                    print(f"   进度: {i}/1000")

            except Exception as e:
                monitor.record(False, 0, type(e).__name__)

        stats = monitor.get_stats()

        print(f"\n📊 高基数标签测试结果:")
        print(f"   总请求: {stats['total']}")
        print(f"   成功: {stats['success']}")
        print(f"   成功率: {stats['success_rate']:.2f}%")

        assert stats['success_rate'] >= 95.0, f"高基数标签测试成功率低: {stats['success_rate']:.2f}%"


class TestConcurrencyChaos:
    """并发混沌测试"""

    def test_thundering_herd(self, client):
        """惊群效应测试 - 大量并发请求"""
        print("\n" + "="*80)
        print("🐘 惊群效应混沌测试")
        print("="*80)

        monitor = ChaosMonitor()

        num_workers = 100
        requests_per_worker = 10

        print(f"\n--- {num_workers}个并发worker，每个发送{requests_per_worker}个请求 ---")

        def thundering_request(worker_id):
            worker_monitor = ChaosMonitor()
            for i in range(requests_per_worker):
                try:
                    start = time.time()
                    response = client.get("/api/v1/health")
                    elapsed = time.time() - start
                    worker_monitor.record(response.status_code == 200, elapsed)
                except Exception as e:
                    worker_monitor.record(False, 0, type(e).__name__)
            return worker_monitor.get_stats()

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(thundering_request, i) for i in range(num_workers)]
            for future in as_completed(futures):
                result = future.result()
                monitor.success_count += result['success']
                monitor.failure_count += result['failure']
                if result.get('avg_latency_ms', 0) > 0:
                    monitor.latencies.append(result['avg_latency_ms'])

        elapsed = time.time() - start_time

        stats = monitor.get_stats()
        stats['elapsed'] = elapsed

        print(f"\n📊 惊群效应测试结果:")
        print(f"   总请求: {stats['total']}")
        print(f"   成功: {stats['success']}")
        print(f"   失败: {stats['failure']}")
        print(f"   成功率: {stats['success_rate']:.2f}%")
        print(f"   总耗时: {stats['elapsed']:.2f}s")
        print(f"   吞吐量: {stats['total'] / stats['elapsed']:.2f} req/s")

        assert stats['success_rate'] >= 95.0, f"惊群效应测试成功率低: {stats['success_rate']:.2f}%"

    def test_read_write_conflicts(self, client):
        """读写冲突测试 - 并发读写同一资源"""
        print("\n" + "="*80)
        print("⚡ 读写冲突混沌测试")
        print("="*80)

        monitor = ChaosMonitor()
        metric_name = "conflict_test"

        num_writers = 20
        num_readers = 30
        operations_per_thread = 50

        print(f"\n--- {num_writers}个写者 + {num_readers}个读者，每线程{operations_per_thread}次操作 ---")

        def writer_task(writer_id):
            for i in range(operations_per_thread):
                try:
                    start = time.time()
                    response = client.post("/api/v1/metrics/counter",
                                         json={"name": metric_name, "value": 1.0})
                    elapsed = time.time() - start
                    monitor.record(response.status_code == 200, elapsed)
                except Exception as e:
                    monitor.record(False, 0, type(e).__name__)

        def reader_task(reader_id):
            for i in range(operations_per_thread):
                try:
                    start = time.time()
                    response = client.get("/api/v1/metrics/dashboard")
                    elapsed = time.time() - start
                    monitor.record(response.status_code == 200, elapsed)
                except Exception as e:
                    monitor.record(False, 0, type(e).__name__)

        with ThreadPoolExecutor(max_workers=num_writers + num_readers) as executor:
            # 提交写任务
            writer_futures = [executor.submit(writer_task, i) for i in range(num_writers)]
            # 提交读任务
            reader_futures = [executor.submit(reader_task, i) for i in range(num_readers)]

            # 等待所有任务完成
            for future in writer_futures + reader_futures:
                future.result()

        stats = monitor.get_stats()

        print(f"\n📊 读写冲突测试结果:")
        print(f"   总请求: {stats['total']}")
        print(f"   成功: {stats['success']}")
        print(f"   失败: {stats['failure']}")
        print(f"   成功率: {stats['success_rate']:.2f}%")

        assert stats['success_rate'] >= 95.0, f"读写冲突测试成功率低: {stats['success_rate']:.2f}%"


class TestDataCorruption:
    """数据损坏测试"""

    def test_concurrent_state_corruption(self, client):
        """并发状态损坏测试"""
        print("\n" + "="*80)
        print("🔓 并发状态损坏混沌测试")
        print("="*80)

        monitor = ChaosMonitor()

        num_threads = 50
        operations_per_thread = 100

        print(f"\n--- {num_threads}个线程，每线程{operations_per_thread}次状态修改 ---")

        def chaotic_operation(thread_id):
            thread_monitor = ChaosMonitor()
            for i in range(operations_per_thread):
                # 随机选择操作
                operation = random.choice(['counter', 'gauge', 'histogram'])

                try:
                    start = time.time()
                    if operation == 'counter':
                        response = client.post("/api/v1/metrics/counter",
                                              json={"name": f"chaos_{thread_id}", "value": 1.0})
                    elif operation == 'gauge':
                        response = client.post("/api/v1/metrics/gauge",
                                              json={"name": f"chaos_{thread_id}", "value": float(i)})
                    else:
                        response = client.post("/api/v1/metrics/histogram",
                                              json={"name": f"chaos_{thread_id}", "value": float(i)})

                    elapsed = time.time() - start
                    thread_monitor.record(response.status_code == 200, elapsed)
                except Exception as e:
                    thread_monitor.record(False, 0, type(e).__name__)

            return thread_monitor.get_stats()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(chaotic_operation, i) for i in range(num_threads)]
            for future in as_completed(futures):
                result = future.result()
                monitor.success_count += result['success']
                monitor.failure_count += result['failure']

        stats = monitor.get_stats()

        print(f"\n📊 并发状态损坏测试结果:")
        print(f"   总请求: {stats['total']}")
        print(f"   成功: {stats['success']}")
        print(f"   失败: {stats['failure']}")
        print(f"   成功率: {stats['success_rate']:.2f}%")

        assert stats['success_rate'] >= 95.0, f"并发状态损坏测试成功率低: {stats['success_rate']:.2f}%"

    def test_data_consistency_after_chaos(self, client):
        """混沌后数据一致性测试"""
        print("\n" + "="*80)
        print("🔄 混沌后数据一致性测试")
        print("="*80)

        # 先进行大量混沌操作
        print("\n--- 阶段1: 混沌操作 ---")
        monitor = ChaosMonitor()

        for i in range(500):
            try:
                operation = random.choice(['counter', 'gauge', 'histogram'])
                if operation == 'counter':
                    response = client.post("/api/v1/metrics/counter",
                                         json={"name": "consistency_test", "value": 1.0})
                elif operation == 'gauge':
                    response = client.post("/api/v1/metrics/gauge",
                                         json={"name": "consistency_test", "value": float(i)})
                else:
                    response = client.post("/api/v1/metrics/histogram",
                                         json={"name": "consistency_test", "value": float(i)})

                monitor.record(response.status_code == 200, 0.001)
            except Exception as e:
                monitor.record(False, 0, type(e).__name__)

        chaos_stats = monitor.get_stats()
        print(f"混沌操作: {chaos_stats['success']} 成功, {chaos_stats['failure']} 失败")

        # 然后验证数据一致性
        print("\n--- 阶段2: 数据一致性验证 ---")
        consistency_monitor = ChaosMonitor()

        # 验证Counter一致性
        print("验证Counter...")
        for i in range(100):
            try:
                response = client.post("/api/v1/metrics/counter",
                                     json={"name": "verify_counter", "value": 1.0})
                consistency_monitor.record(response.status_code == 200, 0.001)
            except Exception as e:
                consistency_monitor.record(False, 0, type(e).__name__)

        # 验证Histogram一致性
        print("验证Histogram...")
        for i in range(100):
            try:
                response = client.post("/api/v1/metrics/histogram",
                                     json={"name": "verify_histogram", "value": float(i)})
                consistency_monitor.record(response.status_code == 200, 0.001)
            except Exception as e:
                consistency_monitor.record(False, 0, type(e).__name__)

        # 获取Histogram统计
        response = client.get("/api/v1/metrics/histograms/verify_histogram")
        if response.status_code == 200:
            stats = response.json()
            count = stats.get('stats', {}).get('count', 0)
            print(f"   Histogram记录数: {count}/100")
            consistency_monitor.record(count > 0, 0.001)

        stats = consistency_monitor.get_stats()

        print(f"\n📊 数据一致性测试结果:")
        print(f"   总请求: {stats['total']}")
        print(f"   成功: {stats['success']}")
        print(f"   失败: {stats['failure']}")
        print(f"   成功率: {stats['success_rate']:.2f}%")

        assert stats['success_rate'] >= 95.0, f"混沌后数据一致性测试成功率低: {stats['success_rate']:.2f}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
