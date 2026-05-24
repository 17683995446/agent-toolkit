"""
🔥🔥🔥 ULTRA EXTREME COMPLEX SCENARIO TEST
🔥🔥🔥 超大规模复杂场景混沌测试

测试内容：
1. 超长时间运行（3-5分钟）
2. 超大规模并发（1500+ Workers）
3. 极度错综复杂的组合操作
4. 极高难度边界值
5. 高度混乱的操作时序
"""

import time
import random
import threading
import gc
import sys
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
import math

from agent_toolkit.shared.metrics_api import MetricsCollector
from agent_toolkit.shared.health_check import HealthCheckRegistry
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError,
    ValidationError,
    DuplicateError,
    AgentToolkitTimeoutError
)


class UltraComplexChaosMetrics:
    """追踪超复杂混沌测试的详细指标"""

    def __init__(self):
        self.start_time = time.time()
        self.total_ops = 0
        self.success_ops = 0
        self.failure_ops = 0
        self.errors: List[Dict[str, Any]] = []
        self.latencies: List[float] = []
        self.operation_distribution: Dict[str, int] = {}
        self.error_distribution: Dict[str, int] = {}
        self.lock = threading.Lock()
        self.phase = 1

    def record(self, op_type: str, success: bool, duration: float = 0.0, error: Optional[Exception] = None):
        """记录一次操作结果"""
        with self.lock:
            self.total_ops += 1

            if success:
                self.success_ops += 1
                self.operation_distribution[op_type] = self.operation_distribution.get(op_type, 0) + 1
                self.latencies.append(duration * 1000)
            else:
                self.failure_ops += 1
                error_type = type(error).__name__ if error else "UnknownError"
                self.error_distribution[error_type] = self.error_distribution.get(error_type, 0) + 1
                if len(self.errors) < 100:
                    self.errors.append({
                        "type": error_type,
                        "msg": str(error)[:200],
                        "op": op_type,
                        "phase": self.phase,
                        "time": datetime.now().isoformat()
                    })

    def summary(self) -> Dict[str, Any]:
        """获取总结信息"""
        with self.lock:
            elapsed = time.time() - self.start_time
            success_rate = self.success_ops / max(self.total_ops, 1) * 100
            ops_per_second = self.total_ops / max(elapsed, 0.001)

            latency_stats = {}
            if self.latencies:
                sorted_lat = sorted(self.latencies)
                latency_stats = {
                    "p50": sorted_lat[int(len(sorted_lat) * 0.5)],
                    "p90": sorted_lat[int(len(sorted_lat) * 0.9)],
                    "p95": sorted_lat[int(len(sorted_lat) * 0.95)],
                    "p99": sorted_lat[int(len(sorted_lat) * 0.99)],
                    "max": max(sorted_lat),
                    "avg": sum(sorted_lat) / len(sorted_lat)
                }

            return {
                "elapsed": elapsed,
                "total_ops": self.total_ops,
                "success": self.success_ops,
                "failures": self.failure_ops,
                "success_rate": success_rate,
                "ops_per_sec": ops_per_second,
                "latency": latency_stats,
                "operations": self.operation_distribution,
                "errors": self.error_distribution
            }


class UltraComplexScenarioTester:
    """超复杂场景混沌测试器"""

    def __init__(self, duration_sec: int = 200, num_workers: int = 1500):
        self.duration = duration_sec
        self.num_workers = num_workers
        self.collector = MetricsCollector()
        self.metrics = UltraComplexChaosMetrics()
        self.stop_event = threading.Event()

        # 预生成大量指标名称，制造更大的混乱
        self.all_counters = [f"chaos_counter_{i}" for i in range(800)]
        self.all_gauges = [f"chaos_gauge_{i}" for i in range(800)]
        self.all_histograms = [f"chaos_hist_{i}" for i in range(800)]

        print("=" * 95)
        print("🔥🔥🔥 ULTRA EXTREME COMPLEX SCENARIO CHAOS TEST")
        print("🔥🔥🔥 超大规模复杂场景混沌测试")
        print("=" * 95)
        print(f"Duration: {self.duration} sec | Workers: {self.num_workers}")
        print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 95)

    def worker_ultra_complex_counter(self, worker_id: int):
        """Worker: 超复杂计数器操作组合"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                for _ in range(random.randint(1, 40)):
                    # 选择极其混乱的组合
                    choice = random.randint(0, 15)
                    if choice == 0:
                        # 快速递增
                        for __ in range(random.randint(1, 15)):
                            self.collector.increment_counter(random.choice(self.all_counters), random.uniform(1, 10))
                    elif choice == 1:
                        # 递减
                        for __ in range(random.randint(1, 15)):
                            self.collector.increment_counter(random.choice(self.all_counters), -random.uniform(1, 10))
                    elif choice == 2:
                        # NaN 值
                        self.collector.increment_counter(random.choice(self.all_counters), float('nan'))
                    elif choice == 3:
                        # Infinity 值
                        self.collector.increment_counter(random.choice(self.all_counters), float('inf'))
                    elif choice == 4:
                        # -Infinity 值
                        self.collector.increment_counter(random.choice(self.all_counters), -float('inf'))
                    elif choice == 5:
                        # 零值
                        self.collector.increment_counter(random.choice(self.all_counters), 0.0)
                    elif choice == 6:
                        # 极小值
                        self.collector.increment_counter(random.choice(self.all_counters), 1e-300)
                    elif choice == 7:
                        # 极大值
                        self.collector.increment_counter(random.choice(self.all_counters), 1e300)
                    elif choice == 8:
                        # sys.maxsize
                        self.collector.increment_counter(random.choice(self.all_counters), sys.maxsize)
                    elif choice == 9:
                        # -sys.maxsize
                        self.collector.increment_counter(random.choice(self.all_counters), -sys.maxsize)
                    elif choice == 10:
                        # 混合复杂操作组
                        name = random.choice(self.all_counters)
                        self.collector.increment_counter(name, 1.0)
                        self.collector.increment_counter(name, float('nan'))
                        self.collector.increment_counter(name, 2.0)
                    elif choice == 11:
                        # 连续递增
                        name = random.choice(self.all_counters)
                        for __ in range(random.randint(1, 50)):
                            self.collector.increment_counter(name, random.uniform(0.01, 1))
                    else:
                        # 标准操作
                        self.collector.increment_counter(random.choice(self.all_counters), random.uniform(-100, 100))

                self.metrics.record("counter", True, time.time() - start_time)
            except Exception as e:
                self.metrics.record("counter", False, error=e)

    def worker_ultra_complex_gauge(self, worker_id: int):
        """Worker: 超复杂仪表盘操作组合"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                for _ in range(random.randint(1, 30)):
                    choice = random.randint(0, 12)
                    if choice == 0:
                        self.collector.set_gauge(random.choice(self.all_gauges), random.uniform(-1000, 1000))
                    elif choice == 1:
                        self.collector.set_gauge(random.choice(self.all_gauges), float('nan'))
                    elif choice == 2:
                        self.collector.set_gauge(random.choice(self.all_gauges), float('inf'))
                    elif choice == 3:
                        self.collector.set_gauge(random.choice(self.all_gauges), -float('inf'))
                    elif choice == 4:
                        self.collector.set_gauge(random.choice(self.all_gauges), 0.0)
                    elif choice == 5:
                        self.collector.set_gauge(random.choice(self.all_gauges), 1e100)
                    elif choice == 6:
                        self.collector.set_gauge(random.choice(self.all_gauges), -1e100)
                    elif choice == 7:
                        # 混合操作
                        name = random.choice(self.all_gauges)
                        self.collector.set_gauge(name, 100)
                        self.collector.set_gauge(name, float('nan'))
                        self.collector.set_gauge(name, 200)
                    else:
                        # 连续设置
                        name = random.choice(self.all_gauges)
                        for __ in range(random.randint(1, 40)):
                            self.collector.set_gauge(name, random.random() * 1000)

                self.metrics.record("gauge", True, time.time() - start_time)
            except Exception as e:
                self.metrics.record("gauge", False, error=e)

    def worker_ultra_complex_histogram(self, worker_id: int):
        """Worker: 超复杂直方图操作组合"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                for _ in range(random.randint(1, 200)):
                    choice = random.randint(0, 20)
                    if choice == 0:
                        self.collector.record_histogram(random.choice(self.all_histograms), random.random())
                    elif choice == 1:
                        self.collector.record_histogram(random.choice(self.all_histograms), float('nan'))
                    elif choice == 2:
                        self.collector.record_histogram(random.choice(self.all_histograms), float('inf'))
                    elif choice == 3:
                        self.collector.record_histogram(random.choice(self.all_histograms), -float('inf'))
                    elif choice == 4:
                        self.collector.record_histogram(random.choice(self.all_histograms), 0.0)
                    elif choice == 5:
                        self.collector.record_histogram(random.choice(self.all_histograms), 1e200)
                    elif choice == 6:
                        self.collector.record_histogram(random.choice(self.all_histograms), -1e200)
                    elif choice == 7:
                        # 混合复杂值
                        name = random.choice(self.all_histograms)
                        self.collector.record_histogram(name, 5.0)
                        self.collector.record_histogram(name, float('nan'))
                        self.collector.record_histogram(name, 10.0)
                    elif choice == 8:
                        # 正态分布
                        name = random.choice(self.all_histograms)
                        for __ in range(random.randint(1, 100)):
                            self.collector.record_histogram(name, random.gauss(0, 100))
                    elif choice == 9:
                        # 指数分布
                        name = random.choice(self.all_histograms)
                        for __ in range(random.randint(1, 100)):
                            self.collector.record_histogram(name, random.expovariate(0.1))
                    elif choice == 10:
                        # 三角分布
                        name = random.choice(self.all_histograms)
                        for __ in range(random.randint(1, 100)):
                            self.collector.record_histogram(name, random.triangular(-1000, 1000))
                    else:
                        # 极快速记录
                        name = random.choice(self.all_histograms)
                        for __ in range(random.randint(1, 200)):
                            self.collector.record_histogram(name, random.uniform(-1000, 1000))

                self.metrics.record("histogram", True, time.time() - start_time)
            except Exception as e:
                self.metrics.record("histogram", False, error=e)

    def worker_ultra_complex_query(self, worker_id: int):
        """Worker: 超复杂查询操作组合"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                choice = random.randint(0, 20)

                if choice == 0:
                    self.collector.get_all_metrics()
                elif choice == 1:
                    name = random.choice(self.all_histograms)
                    try:
                        self.collector.get_histogram_stats(name)
                    except Exception:
                        pass
                elif choice == 2:
                    name = random.choice(self.all_counters)
                    try:
                        self.collector.get_metric_history(name, limit=random.randint(1, 2000))
                    except Exception:
                        pass
                elif choice == 3:
                    # 批量查询直方图
                    for name in self.all_histograms[:100]:
                        try:
                            self.collector.get_histogram_stats(name)
                        except Exception:
                            pass
                elif choice == 4:
                    # 超快速 get_all_metrics
                    for __ in range(random.randint(1, 200)):
                        self.collector.get_all_metrics()
                elif choice == 5:
                    # 混合查询
                    self.collector.get_all_metrics()
                    name1 = random.choice(self.all_histograms)
                    try:
                        self.collector.get_histogram_stats(name1)
                    except Exception:
                        pass
                    name2 = random.choice(self.all_counters)
                    try:
                        self.collector.get_metric_history(name2)
                    except Exception:
                        pass
                else:
                    # 标准查询
                    self.collector.get_all_metrics()
                    for name in self.all_histograms[:10]:
                        try:
                            self.collector.get_histogram_stats(name)
                        except Exception:
                            pass

                self.metrics.record("query", True, time.time() - start_time)
            except Exception as e:
                self.metrics.record("query", False, error=e)

    def worker_ultra_complex_exception(self, worker_id: int):
        """Worker: 超复杂异常操作组合"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                for _ in range(random.randint(1, 50)):
                    choice = random.randint(0, 15)
                    if choice == 0:
                        # NotFoundError
                        exc = NotFoundError(
                            message=f"Not found worker {worker_id} object {random.randint(1, 1000000)}",
                            resource_type=random.choice(["tool", "metric", "endpoint", "worker", "task"]),
                            resource_id=random.randint(1, 10000000)
                        )
                        dict_data = exc.to_dict()
                        json_str = json.dumps(dict_data)
                    elif choice == 1:
                        # ValidationError
                        exc = ValidationError(
                            message=f"Validation failed for worker {worker_id}",
                            details={
                                "worker_id": worker_id,
                                "random_val": random.random(),
                                "nested": {"a": {"b": {"c": {"d": {"e": [1, 2, 3]}}}}},
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                        dict_data = exc.to_dict()
                        json_str = json.dumps(dict_data)
                    elif choice == 2:
                        # DuplicateError
                        exc = DuplicateError(
                            message=f"Duplicate {random.randint(1, 1000)} detected",
                            resource_type="test_resource",
                            existing_id=random.randint(1, 1000000)
                        )
                        dict_data = exc.to_dict()
                        json_str = json.dumps(dict_data)
                    elif choice == 3:
                        # AgentToolkitTimeoutError
                        exc = AgentToolkitTimeoutError(
                            message=f"Timeout {random.randint(1, 600)}s",
                            timeout_seconds=random.randint(1, 600),
                            operation=f"worker_{worker_id}_op_{hashlib.sha256(f'{random.random()}'.encode()).hexdigest()[:10]}"
                        )
                        dict_data = exc.to_dict()
                        json_str = json.dumps(dict_data)
                    else:
                        # 随机混合
                        exc_class = random.choice([
                            NotFoundError,
                            ValidationError,
                            DuplicateError,
                            AgentToolkitTimeoutError
                        ])
                        if exc_class == NotFoundError:
                            exc = exc_class(
                                message=f"Random error {random.randint(1, 1000)}",
                                resource_type="random",
                                resource_id=random.randint(1, 1000)
                            )
                        elif exc_class == ValidationError:
                            exc = exc_class(message="Random validation", details={})
                        elif exc_class == DuplicateError:
                            exc = exc_class(message="Random duplicate", resource_type="r", existing_id=0)
                        else:
                            exc = exc_class(message="Random timeout", timeout_seconds=1, operation="r")
                        exc.to_dict()

                self.metrics.record("exception", True, time.time() - start_time)
            except Exception as e:
                self.metrics.record("exception", False, error=e)

    def worker_ultra_complex_mixed_everything(self, worker_id: int):
        """Worker: 混合一切 - 最混乱的组合操作"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                for _ in range(random.randint(1, 300)):
                    # 随机选择1-10种操作组合！
                    for __ in range(random.randint(1, 10)):
                        op = random.randint(0, 50)

                        if op < 10:
                            # Counters
                            self.collector.increment_counter(random.choice(self.all_counters), random.uniform(-100, 100))
                        elif op < 20:
                            # Gauges
                            self.collector.set_gauge(random.choice(self.all_gauges), random.uniform(-1000, 1000))
                        elif op < 30:
                            # Histograms
                            self.collector.record_histogram(random.choice(self.all_histograms), random.random())
                        elif op < 40:
                            # Queries
                            self.collector.get_all_metrics()
                            name = random.choice(self.all_histograms)
                            try:
                                self.collector.get_histogram_stats(name)
                            except Exception:
                                pass
                        else:
                            # EXTREME 混合：一次性执行10-50种操作！
                            for ___ in range(random.randint(10, 50)):
                                self.collector.increment_counter(random.choice(self.all_counters), random.random())
                                self.collector.set_gauge(random.choice(self.all_gauges), random.random())
                                self.collector.record_histogram(random.choice(self.all_histograms), random.random())

                self.metrics.record("mixed_everything", True, time.time() - start_time)
            except Exception as e:
                self.metrics.record("mixed_everything", False, error=e)

    def progress_reporter(self):
        """进度报告"""
        last_report = time.time()
        last_ops = 0

        while not self.stop_event.is_set():
            current_time = time.time()
            elapsed = current_time - self.metrics.start_time
            time_left = self.duration - elapsed

            summary = self.metrics.summary()
            current_ops = summary["total_ops"]
            ops_since_last = current_ops - last_ops
            time_since_last = current_time - last_report

            print(f"\n{'=' * 95}")
            print(f"⏱️ Phase {self.metrics.phase} [{int(elapsed)}s / {int(time_left)}s]")
            print(f"📊 Total: {current_ops:,} | Success: {summary['success']:,} | Fail: {summary['failures']}")
            print(f"⚡ Throughput: {int(ops_since_last / max(time_since_last, 0.001)):,} ops/sec (avg: {int(summary['ops_per_sec']):,})")
            print(f"✅ Success: {summary['success_rate']:.2f}%")
            if summary["latency"]:
                print(f"📈 Latency: p50={summary['latency']['p50']:.2f}ms p95={summary['latency']['p95']:.2f}ms p99={summary['latency']['p99']:.2f}ms")
            if summary["errors"]:
                print(f"⚠️ Errors: {summary['errors']}")

            last_report = current_time
            last_ops = current_ops
            self.metrics.phase = int(elapsed / 60) + 1

            time.sleep(5)

    def run(self):
        """运行超复杂场景测试"""
        print(f"\n🚀 Starting {self.num_workers} workers...")

        workers = []
        worker_types = [
            ("Counter", 200, self.worker_ultra_complex_counter),
            ("Gauge", 180, self.worker_ultra_complex_gauge),
            ("Histogram", 300, self.worker_ultra_complex_histogram),
            ("Query", 200, self.worker_ultra_complex_query),
            ("Exception", 120, self.worker_ultra_complex_exception),
            ("Mixed", 500, self.worker_ultra_complex_mixed_everything),
        ]

        total = 0
        for name, count, func in worker_types:
            print(f"  - {name}: {count}")
            for i in range(count):
                t = threading.Thread(target=func, args=(total + i,), daemon=True)
                workers.append(t)
                t.start()
            total += count

        print(f"\n✅ All {total} workers started!")

        # 启动报告线程
        reporter = threading.Thread(target=self.progress_reporter, daemon=True)
        reporter.start()

        print(f"\n{'=' * 95}")
        print(f"🔥🔥🔥 ULTRA COMPLEX CHAOS IN PROGRESS - {self.duration} SEC 🔥🔥🔥")
        print(f"{'=' * 95}")

        # 运行指定时长
        time.sleep(self.duration)

        print(f"\n🛑 Stopping all workers...")
        self.stop_event.set()

        print("Waiting for threads to finish...")
        for t in workers:
            t.join(timeout=10)

        # 最终验证
        print(f"\n{'=' * 95}")
        print(f"📋 FINAL VERIFICATION")
        print(f"{'=' * 95}")

        try:
            print("1. Testing get_all_metrics...", end="")
            all_metrics = self.collector.get_all_metrics()
            print(f" ✅ (counters={len(all_metrics['counters'])}, gauges={len(all_metrics['gauges'])}, histograms={len(all_metrics['histograms'])})")

            print("2. Testing counter increment...", end="")
            self.collector.increment_counter("final_test_counter", 1000)
            print(" ✅")

            print("3. Testing gauge set...", end="")
            self.collector.set_gauge("final_test_gauge", 999.999)
            print(" ✅")

            print("4. Testing histogram record...", end="")
            for i in range(500):
                self.collector.record_histogram("final_test_histogram", float(i))
            print(" ✅")

            print("5. Testing histogram stats...", end="")
            stats = self.collector.get_histogram_stats("final_test_histogram")
            print(f" ✅ (count={stats['count']}, mean={stats['mean']:.2f})")

            print("6. Testing metric history...", end="")
            history = self.collector.get_metric_history("final_test_counter", limit=10)
            print(f" ✅ (len={len(history)})")

            final_summary = self.metrics.summary()
            print(f"\n🎉 SUCCESS RATE: {final_summary['success_rate']:.3f}%")
            print(f"🎉 TOTAL OPERATIONS: {final_summary['total_ops']:,}")

            if final_summary["success_rate"] >= 99.999:
                print(f"\n🥇🥇🥇 RATING: ABSOLUTELY PERFECT!")
                print("🥇🥇🥇 The system performed flawlessly in ultra complex scenarios!")
            elif final_summary["success_rate"] >= 99.99:
                print(f"\n🥇 RATING: FLAWLESS!")
            elif final_summary["success_rate"] >= 99.9:
                print(f"\n🥈 RATING: EXCELLENT!")
            elif final_summary["success_rate"] >= 99:
                print(f"\n🥉 RATING: VERY GOOD!")
            else:
                print(f"\n⚠️ RATING: NEEDS IMPROVEMENT")

            if final_summary["errors"]:
                print(f"\n⚠️ FAILURES RECORDED (top errors): {final_summary['errors']}")
                print(f"\n⚠️ FAILURE DETAILS (first 20):")
                for i, err in enumerate(self.metrics.errors[:20]):
                    print(f"  {i+1}. Phase {err['phase']}: [{err['type']}] {err['msg']}")

            print(f"\n{'=' * 95}")

        except Exception as e:
            print(f"\n❌ FINAL VERIFICATION FAILED: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    tester = UltraComplexScenarioTester(duration_sec=120, num_workers=1200)
    tester.run()
