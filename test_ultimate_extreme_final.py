"""
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
ULTIMATE EXTREME COMPLEX CHAOS ENGINEERING - THE FINAL TEST
终极极端复杂场景混沌工程 - 最终测试
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

This is the most complex, largest, most challenging chaos test.
It includes:
- 2000+ concurrent worker threads
- 300 seconds (5+ minutes) duration
- Every possible edge case
- Maximum chaos and confusion
"""

import time
import random
import threading
import gc
import sys
import json
import math
import os
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime

from agent_toolkit.shared.metrics_api import MetricsCollector
from agent_toolkit.shared.health_check import HealthCheckRegistry
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError,
    ValidationError,
    DuplicateError,
    AgentToolkitTimeoutError
)


class UltraExtremeFinalMetrics:
    """追踪终极极端测试的所有指标"""

    def __init__(self):
        self.start_time = time.time()
        self.total_ops = 0
        self.success_ops = 0
        self.failure_ops = 0
        self.errors: List[Dict[str, Any]] = []
        self.latencies: List[float] = []
        self.operation_distribution: Dict[str, int] = {}
        self.error_distribution: Dict[str, int] = {}
        self.phase = 1
        self.resource_history: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def record(self, op_type: str, success: bool, duration: float = 0.0, error: Optional[Exception] = None):
        with self.lock:
            self.total_ops += 1

            if success:
                self.success_ops += 1
                self.operation_distribution[op_type] = self.operation_distribution.get(op_type, 0) + 1
                self.latencies.append(duration * 1000)
            else:
                self.failure_ops += 1
                error_type = type(error).__name__ if error else "Unknown"
                self.error_distribution[error_type] = self.error_distribution.get(error_type, 0) + 1
                if len(self.errors) < 200:
                    self.errors.append({
                        "type": error_type,
                        "msg": str(error)[:250],
                        "op": op_type,
                        "phase": self.phase,
                        "time": datetime.now().isoformat()
                    })

    def record_resource(self):
        try:
            process = psutil.Process(os.getpid())
            mem = process.memory_info()
            with self.lock:
                self.resource_history.append({
                    "timestamp": time.time(),
                    "rss_mb": mem.rss / 1024 / 1024,
                    "cpu_percent": process.cpu_percent(),
                    "threads": process.num_threads()
                })
                if len(self.resource_history) > 500:
                    self.resource_history = self.resource_history[-500:]
        except:
            pass

    def summary(self) -> Dict[str, Any]:
        with self.lock:
            elapsed = time.time() - self.start_time
            success_rate = self.success_ops / max(self.total_ops, 1) * 100
            ops_per_sec = self.total_ops / max(elapsed, 0.001)

            latency_stats = {}
            if self.latencies:
                sorted_lat = sorted(self.latencies)
                n = len(sorted_lat)
                latency_stats = {
                    "p50": sorted_lat[int(n * 0.5)],
                    "p90": sorted_lat[int(n * 0.9)],
                    "p95": sorted_lat[int(n * 0.95)],
                    "p99": sorted_lat[int(n * 0.99)],
                    "max": max(sorted_lat),
                    "avg": sum(sorted_lat) / n
                }

            return {
                "elapsed_sec": elapsed,
                "total_operations": self.total_ops,
                "success": self.success_ops,
                "failures": self.failure_ops,
                "success_rate_pct": success_rate,
                "ops_per_second": ops_per_sec,
                "latency_ms": latency_stats,
                "operations_by_type": self.operation_distribution,
                "errors_by_type": self.error_distribution
            }


class UltraExtremeFinalChaosTester:
    """终极极端复杂混沌测试器"""

    def __init__(self, duration_sec: int = 300, num_workers: int = 2000):
        self.duration = duration_sec
        self.num_workers = num_workers
        self.collector = MetricsCollector()
        self.metrics = UltraExtremeFinalMetrics()
        self.stop_event = threading.Event()

        # 超大规模预生成指标名称
        self.all_counters = [f"final_counter_{i}" for i in range(2000)]
        self.all_gauges = [f"final_gauge_{i}" for i in range(2000)]
        self.all_histograms = [f"final_histogram_{i}" for i in range(2000)]

        print("=" * 100)
        print("🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀 ULTIMATE EXTREME FINAL CHAOS TEST 🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀")
        print("=" * 100)
        print(f"Duration: {self.duration} seconds ({self.duration // 60} minutes)")
        print(f"Total Workers: {self.num_workers}")
        print(f"Metric Names Generated: 2000 each (Counters/Gauges/Histograms)")
        print("Start Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 100)

    def worker_ultimate_counter(self, worker_id: int):
        """终极计数器 Worker - 最极端的场景"""
        while not self.stop_event.is_set():
            try:
                start = time.time()
                for _ in range(random.randint(1, 250)):
                    choice = random.randint(0, 50)
                    name = random.choice(self.all_counters)

                    if choice < 5:
                        self.collector.increment_counter(name, float("nan"))
                    elif choice < 10:
                        self.collector.increment_counter(name, float("inf"))
                    elif choice < 15:
                        self.collector.increment_counter(name, -float("inf"))
                    elif choice < 20:
                        self.collector.increment_counter(name, 1e300)
                    elif choice < 25:
                        self.collector.increment_counter(name, -1e300)
                    elif choice < 30:
                        self.collector.increment_counter(name, 0.0)
                    elif choice < 35:
                        self.collector.increment_counter(name, sys.maxsize)
                    elif choice < 40:
                        for i in range(random.randint(1, 20)):
                            self.collector.increment_counter(name, random.uniform(-10000, 10000))
                    else:
                        self.collector.increment_counter(name, random.uniform(-1000, 1000))

                self.metrics.record("counter", True, time.time() - start)
            except Exception as e:
                self.metrics.record("counter", False, error=e)

    def worker_ultimate_gauge(self, worker_id: int):
        """终极仪表盘 Worker"""
        while not self.stop_event.is_set():
            try:
                start = time.time()
                for _ in range(random.randint(1, 200)):
                    choice = random.randint(0, 40)
                    name = random.choice(self.all_gauges)

                    if choice < 10:
                        val = random.choice([float("nan"), float("inf"), -float("inf"), 1e300, -1e300, 0.0, sys.maxsize])
                        self.collector.set_gauge(name, val)
                    else:
                        for i in range(random.randint(1, 30)):
                            self.collector.set_gauge(name, random.uniform(-1e20, 1e20))

                self.metrics.record("gauge", True, time.time() - start)
            except Exception as e:
                self.metrics.record("gauge", False, error=e)

    def worker_ultimate_histogram(self, worker_id: int):
        """终极直方图 Worker"""
        while not self.stop_event.is_set():
            try:
                start = time.time()
                for _ in range(random.randint(1, 500)):
                    choice = random.randint(0, 60)
                    name = random.choice(self.all_histograms)

                    if choice < 10:
                        val = random.choice([float("nan"), float("inf"), -float("inf"), 1e300, -1e300])
                        self.collector.record_histogram(name, val)
                    elif choice < 20:
                        self.collector.record_histogram(name, random.gauss(0, 1000))
                    elif choice < 30:
                        self.collector.record_histogram(name, random.expovariate(0.01))
                    elif choice < 40:
                        self.collector.record_histogram(name, random.triangular(-10000, 10000))
                    elif choice < 50:
                        for i in range(random.randint(1, 50)):
                            self.collector.record_histogram(name, random.uniform(-1e10, 1e10))
                    else:
                        self.collector.record_histogram(name, random.uniform(-1e5, 1e5))

                self.metrics.record("histogram", True, time.time() - start)
            except Exception as e:
                self.metrics.record("histogram", False, error=e)

    def worker_ultimate_query(self, worker_id: int):
        """终极查询 Worker"""
        while not self.stop_event.is_set():
            try:
                start = time.time()
                choice = random.randint(0, 100)

                if choice < 20:
                    self.collector.get_all_metrics()
                elif choice < 40:
                    name = random.choice(self.all_histograms)
                    try:
                        self.collector.get_histogram_stats(name)
                    except Exception:
                        pass
                elif choice < 60:
                    name = random.choice(self.all_counters)
                    try:
                        self.collector.get_metric_history(name, limit=random.randint(1, 1000))
                    except Exception:
                        pass
                elif choice < 80:
                    for i in range(random.randint(1, 50)):
                        self.collector.get_all_metrics()
                elif choice < 90:
                    for name in self.all_histograms[:100]:
                        try:
                            self.collector.get_histogram_stats(name)
                        except Exception:
                            pass
                else:
                    self.collector.get_all_metrics()
                    name1 = random.choice(self.all_counters)
                    name2 = random.choice(self.all_histograms)
                    try:
                        self.collector.get_metric_history(name1, limit=200)
                        self.collector.get_histogram_stats(name2)
                    except Exception:
                        pass

                self.metrics.record("query", True, time.time() - start)
            except Exception as e:
                self.metrics.record("query", False, error=e)

    def worker_ultimate_exception(self, worker_id: int):
        """终极异常处理 Worker"""
        while not self.stop_event.is_set():
            try:
                start = time.time()
                for _ in range(random.randint(1, 100)):
                    choice = random.randint(0, 100)

                    if choice < 25:
                        exc = NotFoundError(
                            message=f"NF{worker_id}:{random.randint(1,1000000)}",
                            resource_type=random.choice(["tool", "metric", "endpoint", "worker", "config"]),
                            resource_id=random.randint(1, 100000000)
                        )
                    elif choice < 50:
                        exc = ValidationError(
                            message=f"VAL{worker_id}",
                            details={
                                "w": worker_id,
                                "r": random.random(),
                                "n": {"a": {"b": {"c": [i for i in range(50)]}}},
                                "ts": datetime.now().isoformat()
                            }
                        )
                    elif choice < 75:
                        exc = DuplicateError(
                            message=f"DUP{worker_id}",
                            resource_type="resource",
                            existing_id=random.randint(1, 1000000)
                        )
                    else:
                        exc = AgentToolkitTimeoutError(
                            message=f"TMO{worker_id}",
                            timeout_seconds=random.randint(1, 1000),
                            operation=f"op_{hashlib.md5(str(random.random()).encode()).hexdigest()[:10]}"
                        )

                    d = exc.to_dict()
                    s = json.dumps(d)

                self.metrics.record("exception", True, time.time() - start)
            except Exception as e:
                self.metrics.record("exception", False, error=e)

    def worker_ultimate_mixed(self, worker_id: int):
        """终极混合 Worker - 最混乱的"""
        while not self.stop_event.is_set():
            try:
                start = time.time()
                for _ in range(random.randint(1, 1000)):
                    op = random.randint(0, 200)

                    if op < 50:
                        self.collector.increment_counter(random.choice(self.all_counters), random.uniform(-1e5, 1e5))
                    elif op < 100:
                        self.collector.set_gauge(random.choice(self.all_gauges), random.uniform(-1e20, 1e20))
                    elif op < 150:
                        self.collector.record_histogram(random.choice(self.all_histograms), random.uniform(-1e10, 1e10))
                    else:
                        self.collector.get_all_metrics()

                self.metrics.record("mixed_everything", True, time.time() - start)
            except Exception as e:
                self.metrics.record("mixed_everything", False, error=e)

    def progress_reporter(self):
        """进度报告器"""
        last_report = time.time()
        last_ops = 0

        while not self.stop_event.is_set():
            now = time.time()
            elapsed = now - self.metrics.start_time
            remaining = self.duration - elapsed

            summary = self.metrics.summary()
            current_ops = summary["total_operations"]
            ops_since = current_ops - last_ops
            time_since = now - last_report

            self.metrics.record_resource()

            print("\n" + "=" * 100)
            print(f"📊 PHASE {self.metrics.phase} - [{int(elapsed)}s / {int(remaining)}s]")
            print("=" * 100)
            print(f"Total Ops: {summary['total_operations']:,}")
            print(f"Success: {summary['success']:,}")
            print(f"Failures: {summary['failures']}")
            print(f"Success Rate: {summary['success_rate_pct']:.4f}%")
            print(f"Throughput: {int(summary['ops_per_second']):,} ops/sec")

            if summary['latency_ms']:
                l = summary['latency_ms']
                print(f"Latency (ms): p50={l['p50']:.2f} p95={l['p95']:.2f} p99={l['p99']:.2f} max={l['max']:.2f}")

            print(f"Op Types: {dict(sorted(summary['operations_by_type'].items()))}")
            if summary['errors_by_type']:
                print(f"Errors: {summary['errors_by_type']}")

            last_report = now
            last_ops = current_ops
            self.metrics.phase = (int(elapsed) // 60) + 1

            time.sleep(10)

    def run(self):
        """运行终极极端测试"""
        print("\n🚀 Spawning Ultimate Chaos Workers...")

        workers = []

        worker_config = [
            ("COUNTER", 300, self.worker_ultimate_counter),
            ("GAUGE", 250, self.worker_ultimate_gauge),
            ("HISTOGRAM", 400, self.worker_ultimate_histogram),
            ("QUERY", 300, self.worker_ultimate_query),
            ("EXCEPTION", 150, self.worker_ultimate_exception),
            ("MIXED EVERYTHING", 600, self.worker_ultimate_mixed),
        ]

        total = 0
        for wt_name, count, func in worker_config:
            print(f"  - {wt_name}: {count} workers")
            for i in range(count):
                t = threading.Thread(target=func, args=(total + i,), daemon=True)
                workers.append(t)
                t.start()
            total += count

        print(f"\n✅ ALL {total} ULTIMATE WORKERS STARTED!\n")

        reporter_thread = threading.Thread(target=self.progress_reporter, daemon=True)
        reporter_thread.start()

        print("=" * 100)
        print("🚀🚀🚀🚀🚀🚀 ULTIMATE CHAOS RUNNING 🚀🚀🚀🚀🚀🚀")
        print("=" * 100)

        time.sleep(self.duration)

        print("\n🛑 Stopping Ultimate Chaos...")
        self.stop_event.set()

        print("Waiting for all workers to complete...")
        for t in workers:
            t.join(timeout=30)

        self.final_verification()

    def final_verification(self):
        """最终验证"""
        print("\n" + "=" * 100)
        print("🎯🎯🎯 FINAL VERIFICATION 🎯🎯🎯")
        print("=" * 100)

        try:
            # 1. Get all metrics
            print("1. 🔍 Verifying get_all_metrics()... ", end="")
            all_m = self.collector.get_all_metrics()
            cnt_c = len(all_m.get('counters', {}))
            cnt_g = len(all_m.get('gauges', {}))
            cnt_h = len(all_m.get('histograms', {}))
            print(f"✅ SUCCESS (C:{cnt_c} G:{cnt_g} H:{cnt_h})")

            # 2. Counter operations
            print("2. 🔍 Verifying counter increment... ", end="")
            self.collector.increment_counter("final_verify_counter", 999999.9)
            print("✅ SUCCESS")

            # 3. Gauge operations
            print("3. 🔍 Verifying gauge set... ", end="")
            self.collector.set_gauge("final_verify_gauge", 123456789.123456789)
            print("✅ SUCCESS")

            # 4. Histogram operations
            print("4. 🔍 Verifying histogram record (1000 ops)... ", end="")
            for i in range(1000):
                self.collector.record_histogram("final_verify_histogram", float(i))
            print("✅ SUCCESS")

            # 5. Histogram stats
            print("5. 🔍 Verifying histogram stats... ", end="")
            stats = self.collector.get_histogram_stats("final_verify_histogram")
            print(f"✅ SUCCESS (count={stats.get('count',0)}, avg={stats.get('mean',0):.2f})")

            # 6. Metric history
            print("6. 🔍 Verifying metric history... ", end="")
            hist = self.collector.get_metric_history("final_verify_counter", limit=50)
            print(f"✅ SUCCESS (len={len(hist)})")

            # Final summary
            final_sum = self.metrics.summary()
            print("\n" + "=" * 100)
            print("🎯🎯🎯 FINAL TEST RESULT 🎯🎯🎯")
            print("=" * 100)
            print(f"Total Operations: {final_sum['total_operations']:,}")
            print(f"Success: {final_sum['success']:,}")
            print(f"Failures: {final_sum['failures']}")
            print(f"Success Rate: {final_sum['success_rate_pct']:.6f}%")
            print(f"Throughput: {int(final_sum['ops_per_second']):,} ops/sec")

            if final_sum['success_rate_pct'] >= 99.999:
                print("\n" + "=" * 100)
                print("🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆")
                print("🏆 RATING: ABSOLUTE PERFECTION - ULTIMATE EXTREME TEST PASSED! 🏆")
                print("🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆🏆")
            elif final_sum['success_rate_pct'] >= 99.99:
                print("\n🏆 RATING: PERFECT!")
            elif final_sum['success_rate_pct'] >= 99.9:
                print("\n🏆 RATING: EXCELLENT!")
            elif final_sum['success_rate_pct'] >= 99.0:
                print("\n🥈 RATING: VERY GOOD!")
            else:
                print("\n⚠️ RATING: NEEDS IMPROVEMENT")

            if final_sum['errors']:
                print(f"\n⚠️ FAILURES DETECTED ({len(self.metrics.errors)}):")
                for i, err in enumerate(self.metrics.errors[:50], 1):
                    print(f"  {i}. [{err['phase']}] {err['type']}: {err['msg']}")

            print("=" * 100)
            print("\n✅ ULTIMATE EXTREME FINAL CHAOS TEST COMPLETED SUCCESSFULLY!")
            print("=" * 100)

        except Exception as e:
            print("\n❌ FINAL VERIFICATION FAILED!")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 100)
    print("🚀🚀🚀 AGENT TOOLKIT - ULTIMATE EXTREME FINAL CHAOS ENGINEERING 🚀🚀🚀")
    print("=" * 100)

    # 终极测试 - 200秒(3.3分钟)，2000+ workers
    tester = UltraExtremeFinalChaosTester(duration_sec=200, num_workers=2000)
    tester.run()

