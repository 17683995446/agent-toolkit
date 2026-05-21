"""
Agent Toolkit - Chaos Engineering & Complex Scenarios Test Suite
深度混沌工程测试 - 模拟真实世界的混乱场景
"""

import pytest
import asyncio
import time
import random
import threading
import gc
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from typing import Dict, List, Any, Optional
import signal

from fastapi.testclient import TestClient
from agent_toolkit.main import create_app
from agent_toolkit.shared.metrics_api import MetricsCollector
from agent_toolkit.shared.health_check import HealthCheckRegistry
from agent_toolkit.shared.custom_exceptions import (
    AgentToolkitException,
    NotFoundError,
    ValidationError,
    DuplicateError,
    AgentToolkitTimeoutError,
    ErrorCode
)


class ChaosTestMetrics:
    """混沌测试专用指标收集器"""
    
    def __init__(self):
        self.operations = 0
        self.errors = []
        self.warnings = []
        self.successes = []
        self.thread_states = defaultdict(int)
        self.timing_data = []
        
    def record_success(self, operation: str, duration: float):
        self.successes.append({
            "operation": operation,
            "duration": duration,
            "timestamp": time.time()
        })
        self.operations += 1
        
    def record_error(self, operation: str, error: Exception, context: Dict[str, Any]):
        self.errors.append({
            "operation": operation,
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context,
            "timestamp": time.time(),
            "traceback": traceback.format_exc()
        })
        
    def record_warning(self, message: str, context: Dict[str, Any]):
        self.warnings.append({
            "message": message,
            "context": context,
            "timestamp": time.time()
        })
        
    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_operations": self.operations,
            "success_count": len(self.successes),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "success_rate": len(self.successes) / self.operations if self.operations > 0 else 0,
            "error_rate": len(self.errors) / self.operations if self.operations > 0 else 0
        }


class ChaosScenario1_ExtremeConcurrencyAndRaceConditions:
    """
    混沌场景1：极端并发与竞态条件
    测试系统在高并发下的行为和竞态条件处理
    """
    
    def __init__(self):
        self.metrics = ChaosTestMetrics()
        self.running = True
        self.collector = MetricsCollector()
        
    def test_extreme_concurrent_counter_operations(self):
        """极端并发计数器操作测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景1.1: 极端并发计数器操作")
        print("="*80)
        
        self.collector = MetricsCollector()
        thread_count = 50
        operations_per_thread = 100
        
        def counter_worker(thread_id: int):
            for i in range(operations_per_thread):
                try:
                    start = time.time()
                    counter_name = f"chaos_counter_{thread_id % 10}"
                    value = random.uniform(-10, 10)
                    self.collector.increment_counter(counter_name, value)
                    duration = time.time() - start
                    self.metrics.record_success(f"counter_{thread_id}", duration)
                except Exception as e:
                    self.metrics.record_error(f"counter_{thread_id}", e, {"iteration": i})
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [executor.submit(counter_worker, i) for i in range(thread_count)]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"线程执行失败: {e}")
        
        elapsed = time.time() - start_time
        
        print(f"\n📊 测试结果:")
        print(f"  - 线程数: {thread_count}")
        print(f"  - 每线程操作: {operations_per_thread}")
        print(f"  - 总操作数: {thread_count * operations_per_thread}")
        print(f"  - 耗时: {elapsed:.2f}秒")
        print(f"  - 吞吐量: {(thread_count * operations_per_thread) / elapsed:.1f} 操作/秒")
        
        summary = self.metrics.get_summary()
        print(f"  - 成功: {summary['success_count']}")
        print(f"  - 失败: {summary['error_count']}")
        print(f"  - 成功率: {summary['success_rate']:.2%}")
        
        # 验证数据完整性
        final_counters = dict(self.collector._counters)
        print(f"\n✅ 计数器最终状态验证:")
        for i in range(10):
            counter_name = f"chaos_counter_{i}"
            if counter_name in final_counters:
                print(f"  - {counter_name}: {final_counters[counter_name]}")
        
        assert summary['success_rate'] > 0.99, "成功率必须超过99%"
        
    def test_concurrent_gauge_and_histogram_races(self):
        """并发 Gauge 和 Histogram 竞态测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景1.2: 并发 Gauge 和 Histogram 竞态测试")
        print("="*80)
        
        self.collector = MetricsCollector()
        operations = 1000
        
        def gauge_worker():
            for i in range(operations):
                try:
                    gauge_name = f"chaos_gauge_{random.randint(0, 5)}"
                    value = random.uniform(-1000, 1000)
                    self.collector.set_gauge(gauge_name, value)
                    self.metrics.record_success("gauge_set", time.time() - time.time())
                except Exception as e:
                    self.metrics.record_error("gauge_set", e, {})
        
        def histogram_worker():
            for i in range(operations):
                try:
                    hist_name = f"chaos_hist_{random.randint(0, 5)}"
                    value = random.uniform(0, 1000)
                    self.collector.record_histogram(hist_name, value)
                    self.metrics.record_success("histogram_record", time.time() - time.time())
                except Exception as e:
                    self.metrics.record_error("histogram_record", e, {})
        
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=gauge_worker))
            threads.append(threading.Thread(target=histogram_worker))
        
        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.time() - start_time
        
        print(f"\n📊 测试结果:")
        print(f"  - Gauge 操作: {operations * 5}")
        print(f"  - Histogram 操作: {operations * 5}")
        print(f"  - 耗时: {elapsed:.2f}秒")
        
        summary = self.metrics.get_summary()
        print(f"  - 成功率: {summary['success_rate']:.2%}")
        
        # 验证 Histogram trim 正确性
        for i in range(5):
            hist_name = f"chaos_hist_{i}"
            if hist_name in self.collector._histograms:
                hist_len = len(self.collector._histograms[hist_name])
                print(f"  - {hist_name}: {hist_len} 条记录 (最大1000)")
                assert hist_len <= 1000, f"Histogram 超过1000条限制!"
        
        assert summary['success_rate'] > 0.99, "成功率必须超过99%"


class ChaosScenario2_ResourceExhaustionAndMemoryPressure:
    """
    混沌场景2：资源耗尽与内存压力
    测试系统在资源紧张时的行为
    """
    
    def test_histogram_memory_pressure(self):
        """Histogram 内存压力测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景2.1: Histogram 内存压力测试")
        print("="*80)
        
        collector = MetricsCollector()
        initial_memory = self._get_memory_usage()
        
        print(f"初始内存: {initial_memory:.2f} MB")
        
        # 创建大量 histogram
        histogram_count = 100
        points_per_histogram = 1000
        
        print(f"创建 {histogram_count} 个 histogram，每个 {points_per_histogram} 条记录...")
        
        for i in range(histogram_count):
            hist_name = f"pressure_hist_{i}"
            for j in range(points_per_histogram):
                collector.record_histogram(hist_name, j)
            
            if (i + 1) % 10 == 0:
                current_memory = self._get_memory_usage()
                print(f"  已创建 {i + 1} 个 histogram, 内存: {current_memory:.2f} MB")
        
        final_memory = self._get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        print(f"\n📊 内存使用:")
        print(f"  - 初始: {initial_memory:.2f} MB")
        print(f"  - 最终: {final_memory:.2f} MB")
        print(f"  - 增长: {memory_increase:.2f} MB")
        
        # 验证 histogram 自动 trim
        total_histograms = len(collector._histograms)
        print(f"\n✅ Histogram 统计:")
        print(f"  - 总 histogram 数: {total_histograms}")
        
        over_limit = 0
        for name, values in collector._histograms.items():
            if len(values) > 1000:
                over_limit += 1
        
        print(f"  - 超过限制的 histogram: {over_limit}")
        
        assert over_limit == 0, "不应该有 histogram 超过1000条限制"
        
    def test_massive_metric_accumulation(self):
        """大规模指标累积测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景2.2: 大规模指标累积测试")
        print("="*80)
        
        collector = MetricsCollector()
        metric_count = 10000
        
        print(f"创建 {metric_count} 个独立指标...")
        start_time = time.time()
        
        for i in range(metric_count):
            collector.increment_counter(f"massive_counter_{i}", 1)
            collector.set_gauge(f"massive_gauge_{i}", i)
            collector.record_histogram(f"massive_hist_{i}", i % 100)
        
        elapsed = time.time() - start_time
        
        print(f"\n📊 测试结果:")
        print(f"  - 创建指标数: {metric_count}")
        print(f"  - 耗时: {elapsed:.2f}秒")
        print(f"  - 吞吐量: {metric_count / elapsed:.1f} 指标/秒")
        
        print(f"\n✅ 数据完整性:")
        print(f"  - Counter 数量: {len(collector._counters)}")
        print(f"  - Gauge 数量: {len(collector._gauges)}")
        print(f"  - Histogram 数量: {len(collector._histograms)}")
        
        # 验证数据完整性 - MetricsCollector.__init__ 不创建系统指标
        actual_counter_count = len(collector._counters)
        actual_gauge_count = len(collector._gauges)
        
        # 注意：我们创建了 metric_count 个指标
        assert actual_counter_count == metric_count, f"Counter 数量: 期望 {metric_count}, 实际 {actual_counter_count}"
        assert actual_gauge_count == metric_count, f"Gauge 数量: 期望 {metric_count}, 实际 {actual_gauge_count}"
        # Histogram 会额外创建一个 metrics_collection_histogram
        assert len(collector._histograms) >= metric_count, f"Histogram 数量: 期望 >= {metric_count}, 实际 {len(collector._histograms)}"
        
        assert actual_counter_count == metric_count, f"Counter 数量不正确: 期望 {metric_count}, 实际 {actual_counter_count}"
        assert actual_gauge_count == metric_count, f"Gauge 数量不正确: 期望 {metric_count}, 实际 {actual_gauge_count}"
        assert len(collector._histograms) == metric_count, "Histogram 数量不正确"
        
        # 获取所有指标应该很快
        get_start = time.time()
        all_metrics = collector.get_all_metrics()
        get_elapsed = time.time() - get_start
        
        print(f"  - 获取所有指标耗时: {get_elapsed:.3f}秒")
        assert get_elapsed < 5, "获取所有指标应该很快"
        
    def _get_memory_usage(self) -> float:
        """获取当前内存使用 (MB)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0


class ChaosScenario3_ExceptionChainsAndCascadingFailures:
    """
    混沌场景3：异常链与级联失败
    测试系统在异常情况下的表现
    """
    
    def test_exception_throwing_and_handling(self):
        """异常抛出和处理测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景3.1: 异常抛出和处理测试")
        print("="*80)
        
        # 测试各种异常
        test_cases = [
            (NotFoundError, {"message": "Resource not found", "resource_type": "tool", "resource_id": 999}),
            (ValidationError, {"message": "Validation failed", "details": {"field": "name"}}),
            (DuplicateError, {"message": "Already exists", "resource_type": "tool", "existing_id": 1}),
            (AgentToolkitTimeoutError, {"message": "Operation timed out", "timeout_seconds": 30, "operation": "database_query"}),
        ]
        
        print(f"测试 {len(test_cases)} 种异常类型:")
        
        for exc_class, kwargs in test_cases:
            try:
                exc = exc_class(**kwargs)
                print(f"\n✅ {exc_class.__name__}:")
                print(f"   - 消息: {exc.message}")
                print(f"   - 错误码: {exc.error_code}")
                print(f"   - 详情: {exc.details}")
                
                # 验证异常可以序列化
                exc_dict = exc.to_dict()
                print(f"   - 序列化成功: {len(exc_dict)} 字段")
                
                assert exc.message == kwargs["message"], "消息不匹配"
                
            except Exception as e:
                print(f"\n❌ {exc_class.__name__} 创建失败: {e}")
                raise
        
    def test_error_code_coverage(self):
        """错误码完整覆盖测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景3.2: 错误码完整覆盖测试")
        print("="*80)
        
        from agent_toolkit.shared.custom_exceptions import ErrorCode
        
        print(f"测试 {len(ErrorCode)} 种错误码:")
        
        for code in ErrorCode:
            try:
                # 创建使用该错误码的异常
                exc = AgentToolkitException(
                    error_code=code,
                    message=f"Test error for {code.value}",
                    details={"test": True}
                )
                
                assert exc.error_code == code, f"错误码不匹配: {code}"
                assert exc.to_dict()["error_code"] == code.value, f"序列化错误码不匹配"
                
                print(f"  ✅ {code.value}")
                
            except Exception as e:
                print(f"  ❌ {code.value}: {e}")
                raise
        
        print(f"\n✅ 所有 {len(ErrorCode)} 种错误码测试通过")


class ChaosScenario4_NetworkSimulatedFailures:
    """
    混沌场景4：网络模拟失败
    测试系统在网络问题时的表现
    """
    
    def test_rapid_connect_disconnect(self):
        """快速连接断开测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景4.1: 快速连接断开测试")
        print("="*80)
        
        app = create_app()
        
        print("测试 100 次快速请求:")
        success_count = 0
        error_count = 0
        
        for i in range(100):
            try:
                client = TestClient(app)
                response = client.get("/health")
                
                if response.status_code in [200, 503]:
                    success_count += 1
                else:
                    error_count += 1
                    print(f"  ⚠️ 请求 {i} 返回 {response.status_code}")
                    
            except Exception as e:
                error_count += 1
                print(f"  ❌ 请求 {i} 异常: {e}")
        
        print(f"\n📊 测试结果:")
        print(f"  - 成功: {success_count}")
        print(f"  - 失败: {error_count}")
        print(f"  - 成功率: {success_count / 100:.2%}")
        
        assert success_count == 100, "所有请求应该成功"
        
    def test_malformed_requests(self):
        """畸形请求测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景4.2: 畸形请求测试")
        print("="*80)
        
        app = create_app()
        client = TestClient(app)
        
        malformed_requests = [
            {"name": "", "value": 10},  # 空名称
            {"name": "x" * 1001, "value": 10},  # 超长名称
            {"name": "test"},  # 缺少 value (Counter 有默认值)
            {"value": 100},  # 缺少 name
            {"name": "test", "value": "not_a_number"},  # 非数字 value
            {"name": "test", "value": float('nan')},  # NaN
            {"name": "test", "value": float('inf')},  # Infinity
        ]
        
        print(f"测试 {len(malformed_requests)} 种畸形请求:")
        
        for i, payload in enumerate(malformed_requests):
            try:
                response = client.post("/api/v1/metrics/counter", json=payload)
                
                if response.status_code in [200, 422]:
                    print(f"  ✅ 请求 {i}: {response.status_code}")
                else:
                    print(f"  ⚠️ 请求 {i}: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ 请求 {i}: {type(e).__name__}: {e}")
        
        print(f"\n✅ 畸形请求处理测试完成")


class ChaosScenario5_TimeBasedRaceConditions:
    """
    混沌场景5：时间相关的竞态条件
    测试时间相关的复杂场景
    """
    
    def test_timestamp_dependent_operations(self):
        """时间戳相关操作测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景5.1: 时间戳相关操作测试")
        print("="*80)
        
        collector = MetricsCollector()
        
        # 快速连续记录时间戳
        print("快速连续记录10000个时间戳:")
        start_time = time.time()
        
        for i in range(10000):
            collector.record_histogram("timestamp_test", i)
        
        elapsed = time.time() - start_time
        
        print(f"  - 耗时: {elapsed:.2f}秒")
        print(f"  - 吞吐量: {10000 / elapsed:.1f} 操作/秒")
        
        # 验证 histogram 时间顺序
        hist_values = collector._histograms["timestamp_test"]
        is_sorted = all(hist_values[i] <= hist_values[i+1] for i in range(len(hist_values)-1))
        print(f"  - 值是否有序: {is_sorted}")
        
        assert is_sorted, "Histogram 值应该保持插入顺序"
        
    def test_uptime_calculation_stress(self):
        """运行时间计算压力测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景5.2: 运行时间计算压力测试")
        print("="*80)
        
        from agent_toolkit.shared.metrics_api import format_uptime
        from agent_toolkit.shared.health_check import format_uptime as health_format_uptime
        
        # 测试各种 uptime 值
        test_cases = [
            (0, "0秒"),
            (1, "1秒"),
            (59, "59秒"),
            (60, "1分钟"),
            (3600, "1小时"),
            (86400, "1天"),
            (90061, "1天1小时1分钟1秒"),
            (7 * 86400 + 3 * 3600 + 15 * 60 + 42, "1周多"),
            (365 * 86400, "1年"),
        ]
        
        print(f"测试 {len(test_cases)} 种 uptime 格式:")
        
        for seconds, description in test_cases:
            result1 = format_uptime(seconds)
            result2 = health_format_uptime(seconds)
            
            print(f"  {description}: '{result1}'")
            assert result1 == result2, f"两个 format_uptime 函数结果不一致!"
        
        print(f"\n✅ 所有 uptime 格式测试通过")


class ChaosScenario6_DataIntegrityAndConsistency:
    """
    混沌场景6：数据完整性与一致性
    测试复杂数据场景
    """
    
    def test_complex_counter_operations(self):
        """复杂计数器操作测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景6.1: 复杂计数器操作测试")
        print("="*80)
        
        collector = MetricsCollector()
        
        # 正向和负向操作混合
        operations = [
            ("counter1", 10),
            ("counter1", -5),
            ("counter1", 3),
            ("counter1", -8),
            ("counter2", 100),
            ("counter2", -50),
            ("counter2", 25),
            ("counter2", -25),
        ]
        
        print("执行混合正负操作:")
        for name, value in operations:
            collector.increment_counter(name, value)
            print(f"  {name} += {value} -> {collector._counters[name]}")
        
        print(f"\n✅ 最终结果:")
        print(f"  counter1: {collector._counters['counter1']} (预期: 0)")
        print(f"  counter2: {collector._counters['counter2']} (预期: 50)")
        
        assert collector._counters['counter1'] == 0, "counter1 应该为 0"
        assert collector._counters['counter2'] == 50, "counter2 应该为 50"
        
    def test_histogram_statistics_accuracy(self):
        """Histogram 统计准确性测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景6.2: Histogram 统计准确性测试")
        print("="*80)
        
        collector = MetricsCollector()
        
        # 记录已知分布的数据
        test_values = list(range(1, 101))  # 1 到 100
        for value in test_values:
            collector.record_histogram("stats_test", value)
        
        # 获取统计信息
        stats = collector.get_histogram_stats("stats_test")
        
        print(f"输入数据: 1 到 100 的整数")
        print(f"\n📊 统计结果:")
        print(f"  - Count: {stats['count']} (预期: 100)")
        print(f"  - Min: {stats['min']} (预期: 1)")
        print(f"  - Max: {stats['max']} (预期: 100)")
        print(f"  - Mean: {stats['mean']:.2f} (预期: 50.5)")
        print(f"  - P50: {stats['p50']} (预期: ~50)")
        print(f"  - P95: {stats['p95']} (预期: ~95)")
        print(f"  - P99: {stats['p99']} (预期: ~99)")
        
        assert stats['count'] == 100, "Count 不正确"
        assert stats['min'] == 1, "Min 不正确"
        assert stats['max'] == 100, "Max 不正确"
        assert abs(stats['mean'] - 50.5) < 0.1, "Mean 不正确"
        
        print(f"\n✅ Histogram 统计准确性测试通过")


class ChaosScenario7_LongRunningStressTests:
    """
    混沌场景7：长时间压力测试
    测试系统在长时间运行下的表现
    """
    
    def test_30_second_sustained_load(self):
        """30秒持续负载测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景7.1: 30秒持续负载测试")
        print("="*80)
        
        collector = MetricsCollector()
        start_time = time.time()
        duration = 30  # 30秒
        operations = 0
        errors = 0
        
        print(f"运行 {duration} 秒持续负载测试...")
        
        while time.time() - start_time < duration:
            try:
                # 随机操作
                op_type = random.randint(0, 4)
                
                if op_type == 0:
                    collector.increment_counter("stress_counter", random.uniform(-1, 1))
                elif op_type == 1:
                    collector.set_gauge("stress_gauge", random.uniform(-1000, 1000))
                elif op_type == 2:
                    collector.record_histogram("stress_hist", random.uniform(0, 100))
                elif op_type == 3:
                    collector.get_all_metrics()
                elif op_type == 4:
                    collector.get_histogram_stats("stress_hist")
                
                operations += 1
                
                # 偶尔打印进度
                elapsed = time.time() - start_time
                if int(elapsed) % 5 == 0 and elapsed > 1:
                    print(f"  进度: {elapsed:.0f}s, 操作: {operations}, 速率: {operations/elapsed:.1f}/s")
                    
            except Exception as e:
                errors += 1
                print(f"  ❌ 错误: {e}")
        
        final_elapsed = time.time() - start_time
        
        print(f"\n📊 最终结果:")
        print(f"  - 总耗时: {final_elapsed:.2f}秒")
        print(f"  - 总操作: {operations}")
        print(f"  - 错误数: {errors}")
        print(f"  - 吞吐量: {operations / final_elapsed:.1f} 操作/秒")
        print(f"  - 成功率: {(operations - errors) / operations * 100:.2f}%")
        
        # 验证数据完整性
        print(f"\n✅ 数据完整性:")
        print(f"  - Counter 数量: {len(collector._counters)}")
        print(f"  - Gauge 数量: {len(collector._gauges)}")
        print(f"  - Histogram 数量: {len(collector._histograms)}")
        
        assert errors == 0, f"不应该有错误，但有 {errors} 个"
        assert operations > 10000, f"操作数太少: {operations}"


class ChaosScenario8_EdgeCaseMatrix:
    """
    混沌场景8：边界情况矩阵
    测试所有边界情况的组合
    """
    
    def test_extreme_value_combinations(self):
        """极端值组合测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景8.1: 极端值组合测试")
        print("="*80)
        
        collector = MetricsCollector()
        
        extreme_values = [
            ("extreme_very_large", 1e308),
            ("extreme_very_small", 1e-308),
            ("extreme_negative_large", -1e308),
            ("extreme_negative_small", -1e-308),
            ("extreme_zero", 0),
            ("extreme_near_zero_pos", 1e-320),
            ("extreme_near_zero_neg", -1e-320),
        ]
        
        print(f"测试 {len(extreme_values)} 种极端值:")
        
        for name, value in extreme_values:
            try:
                collector.set_gauge(name, value)
                stored_value = collector._gauges[name]
                print(f"  ✅ {name}: {value} -> {stored_value}")
            except Exception as e:
                print(f"  ❌ {name}: {value} -> 错误: {e}")
        
        print(f"\n✅ 极端值测试完成")
        
    def test_unicode_and_special_characters(self):
        """Unicode 和特殊字符测试"""
        print("\n" + "="*80)
        print("🔥 混沌场景8.2: Unicode 和特殊字符测试")
        print("="*80)
        
        collector = MetricsCollector()
        
        special_names = [
            "counter_中文",
            "counter_日本語",
            "counter_with_emoji_🎉",
            "counter_with_emoji_🚀",
            "counter_with_special_!@#$%",
            "counter_with_space ",
            "counter_with_underscore_",
            "counter___multiple__underscores___",
            "counter/with/slashes",
            "counter\\with\\backslashes",
        ]
        
        print(f"测试 {len(special_names)} 种特殊名称:")
        
        for name in special_names:
            try:
                collector.increment_counter(name, 1)
                print(f"  ✅ '{name}': {collector._counters[name]}")
            except Exception as e:
                print(f"  ❌ '{name}': {e}")
        
        print(f"\n✅ 特殊字符测试完成")


def run_all_chaos_tests():
    """运行所有混沌测试"""
    print("="*80)
    print("🚀 Agent Toolkit - 混沌工程测试套件")
    print("="*80)
    print("深度混沌工程测试 - 模拟真实世界的混乱场景")
    print("="*80)
    
    # 场景1: 极端并发
    print("\n" + "="*80)
    print("🎯 开始混沌场景1: 极端并发与竞态条件")
    print("="*80)
    
    scenario1 = ChaosScenario1_ExtremeConcurrencyAndRaceConditions()
    scenario1.test_extreme_concurrent_counter_operations()
    scenario1.test_concurrent_gauge_and_histogram_races()
    
    # 场景2: 资源压力
    print("\n" + "="*80)
    print("🎯 开始混沌场景2: 资源耗尽与内存压力")
    print("="*80)
    
    scenario2 = ChaosScenario2_ResourceExhaustionAndMemoryPressure()
    scenario2.test_histogram_memory_pressure()
    scenario2.test_massive_metric_accumulation()
    
    # 场景3: 异常处理
    print("\n" + "="*80)
    print("🎯 开始混沌场景3: 异常链与级联失败")
    print("="*80)
    
    scenario3 = ChaosScenario3_ExceptionChainsAndCascadingFailures()
    scenario3.test_exception_throwing_and_handling()
    scenario3.test_error_code_coverage()
    
    # 场景4: 网络模拟失败
    print("\n" + "="*80)
    print("🎯 开始混沌场景4: 网络模拟失败")
    print("="*80)
    
    scenario4 = ChaosScenario4_NetworkSimulatedFailures()
    scenario4.test_rapid_connect_disconnect()
    scenario4.test_malformed_requests()
    
    # 场景5: 时间相关
    print("\n" + "="*80)
    print("🎯 开始混沌场景5: 时间相关竞态条件")
    print("="*80)
    
    scenario5 = ChaosScenario5_TimeBasedRaceConditions()
    scenario5.test_timestamp_dependent_operations()
    scenario5.test_uptime_calculation_stress()
    
    # 场景6: 数据完整性
    print("\n" + "="*80)
    print("🎯 开始混沌场景6: 数据完整性与一致性")
    print("="*80)
    
    scenario6 = ChaosScenario6_DataIntegrityAndConsistency()
    scenario6.test_complex_counter_operations()
    scenario6.test_histogram_statistics_accuracy()
    
    # 场景7: 长时间压力
    print("\n" + "="*80)
    print("🎯 开始混沌场景7: 长时间压力测试")
    print("="*80)
    
    scenario7 = ChaosScenario7_LongRunningStressTests()
    scenario7.test_30_second_sustained_load()
    
    # 场景8: 边界情况
    print("\n" + "="*80)
    print("🎯 开始混沌场景8: 边界情况矩阵")
    print("="*80)
    
    scenario8 = ChaosScenario8_EdgeCaseMatrix()
    scenario8.test_extreme_value_combinations()
    scenario8.test_unicode_and_special_characters()
    
    print("\n" + "="*80)
    print("🎉 所有混沌工程测试完成!")
    print("="*80)


if __name__ == "__main__":
    run_all_chaos_tests()
