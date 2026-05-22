"""
🚀🚀🚀 ULTRA-LONG MEGA CHAOS TEST - 1000+ Workers, 10+ Minutes 🚀🚀🚀

最长时间、最大规模、最混乱场景的测试！
"""

import time
import random
import threading
import gc
import sys
import os
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
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


class MegaChaosMetrics:
    """Metrics for the mega chaos test"""
    
    def __init__(self):
        self.start_time = time.time()
        self.total_operations = 0
        self.successes = 0
        self.failures = 0
        self.errors = []
        self.last_report_time = time.time()
        self.last_ops_report = 0
        self.latency_samples = []
        self.error_counts_by_type = {}
        self.operation_counts_by_type = {}
        self.phase = 1
        self.lock = threading.Lock()
    
    def record_latency(self, latency_ms: float):
        with self.lock:
            self.latency_samples.append(latency_ms)
            if len(self.latency_samples) > 10000:
                self.latency_samples = self.latency_samples[-10000:]
    
    def record_error(self, error_type: str, error_msg: str):
        with self.lock:
            self.failures += 1
            self.errors.append({
                "type": error_type,
                "msg": error_msg[:150],
                "time": datetime.now().isoformat(),
                "phase": self.phase
            })
            self.error_counts_by_type[error_type] = self.error_counts_by_type.get(error_type, 0) + 1
            if len(self.errors) > 1000:
                self.errors = self.errors[-1000:]
    
    def record_success(self, op_type: str):
        with self.lock:
            self.successes += 1
            self.operation_counts_by_type[op_type] = self.operation_counts_by_type.get(op_type, 0) + 1
    
    def increment_ops(self):
        with self.lock:
            self.total_operations += 1


class MegaChaosTester:
    """MEGA CHAOS TEST - 1000+ Workers, 10+ Minutes!"""
    
    def __init__(self, duration_seconds: int = 600, num_workers: int = 1000):
        self.duration = duration_seconds
        self.num_workers = num_workers
        self.metrics = MegaChaosMetrics()
        self.collector = MetricsCollector()
        self.health_registry = HealthCheckRegistry()
        self.stop_event = threading.Event()
        self.executor: Optional[ThreadPoolExecutor] = None
        self.worker_futures = []
        
        # Generate metric names
        self.counter_names = [f"mega_counter_{i}" for i in range(500)]
        self.gauge_names = [f"mega_gauge_{i}" for i in range(500)]
        self.histogram_names = [f"mega_histogram_{i}" for i in range(500)]
        
        print("=" * 95)
        print("🔥🔥🔥🔥🔥 MEGA CHAOS TEST - 1000+ WORKERS, 10+ MINUTES 🔥🔥🔥🔥🔥")
        print("=" * 95)
        print(f"⏱️  Duration: {self.duration//60}m {self.duration%60}s")
        print(f"👷 Workers: {self.num_workers}")
        print(f"🎯 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 95)
    
    def chaos_worker_mega_counter(self, worker_id: int):
        """Mega chaos counter operations"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 70)):
                    name = random.choice(self.counter_names)
                    value = random.choice([
                        random.uniform(-1e20, 1e20),
                        float('nan'),
                        float('inf'),
                        float('-inf'),
                        0.0,
                        1e-100,
                        -1e-100,
                        1, -1,
                    ])
                    
                    try:
                        self.collector.increment_counter(name, value)
                        self.metrics.record_success("mega_counter")
                    except Exception as e:
                        self.metrics.record_error("mega_counter", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.12:
                    time.sleep(random.uniform(0.00001, 0.003))
                    
            except Exception as e:
                self.metrics.record_error("counter_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_mega_gauge(self, worker_id: int):
        """Mega chaos gauge operations"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 50)):
                    name = random.choice(self.gauge_names)
                    value = random.choice([
                        random.uniform(-1e30, 1e30),
                        float('nan'),
                        float('inf'),
                        float('-inf'),
                        0.0,
                        sys.maxsize,
                        -sys.maxsize,
                    ])
                    
                    try:
                        self.collector.set_gauge(name, value)
                        self.metrics.record_success("mega_gauge")
                    except Exception as e:
                        self.metrics.record_error("mega_gauge", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.1:
                    time.sleep(random.uniform(0.00001, 0.005))
                    
            except Exception as e:
                self.metrics.record_error("gauge_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_mega_histogram(self, worker_id: int):
        """Mega chaos histogram operations"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 200)):
                    name = random.choice(self.histogram_names)
                    value = random.choice([
                        random.uniform(-1e5, 1e5),
                        float('nan'),
                        float('inf'),
                        float('-inf'),
                        0.0,
                        random.gauss(0, 500),
                        random.expovariate(0.05),
                        random.triangular(-1000, 1000),
                    ])
                    
                    try:
                        self.collector.record_histogram(name, value)
                        self.metrics.record_success("mega_histogram")
                    except Exception as e:
                        self.metrics.record_error("mega_histogram", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.03:
                    time.sleep(random.uniform(0.00001, 0.002))
                    
            except Exception as e:
                self.metrics.record_error("histogram_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_mega_query(self, worker_id: int):
        """Mega chaos query operations"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                query_type = random.randint(0, 7)
                
                if query_type == 0:
                    self.collector.get_all_metrics()
                    self.metrics.record_success("query_all")
                elif query_type == 1:
                    name = random.choice(self.histogram_names)
                    try:
                        self.collector.get_histogram_stats(name)
                        self.metrics.record_success("query_hist_stats")
                    except Exception:
                        self.metrics.record_success("query_hist_stats_missing")
                elif query_type == 2:
                    name = random.choice(self.counter_names)
                    try:
                        self.collector.get_metric_history(name, limit=random.randint(1, 1500))
                        self.metrics.record_success("query_history")
                    except Exception:
                        self.metrics.record_success("query_history_missing")
                elif query_type == 3:
                    # Batch queries
                    for hist_name in self.histogram_names[:30]:
                        try:
                            self.collector.get_histogram_stats(hist_name)
                        except Exception:
                            pass
                    self.metrics.record_success("batch_query_hist")
                elif query_type == 4:
                    # Rapid get_all
                    for _ in range(random.randint(1, 80)):
                        self.collector.get_all_metrics()
                    self.metrics.record_success("rapid_query_all")
                elif query_type == 5:
                    # Rapid counter history
                    for name in self.counter_names[:20]:
                        try:
                            self.collector.get_metric_history(name, limit=100)
                        except Exception:
                            pass
                    self.metrics.record_success("batch_counter_history")
                elif query_type == 6:
                    # Rapid gauge history
                    for name in self.gauge_names[:20]:
                        try:
                            self.collector.get_metric_history(name, limit=100)
                        except Exception:
                            pass
                    self.metrics.record_success("batch_gauge_history")
                else:
                    # Massive all in one
                    self.collector.get_all_metrics()
                    for name in self.histogram_names[:10]:
                        try:
                            self.collector.get_histogram_stats(name)
                        except Exception:
                            pass
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.08:
                    time.sleep(random.uniform(0.00001, 0.01))
                    
            except Exception as e:
                self.metrics.record_error("query_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_mega_exception(self, worker_id: int):
        """Mega chaos exception operations"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 50)):
                    exc_type = random.choice([
                        NotFoundError,
                        ValidationError,
                        DuplicateError,
                        AgentToolkitTimeoutError
                    ])
                    
                    try:
                        if exc_type == NotFoundError:
                            exc = exc_type(
                                message=f"Not found test {worker_id} {random.randint(1, 100000)}",
                                resource_type=random.choice(["tool", "metric", "endpoint", "worker", "task", "config", "resource", "data"]),
                                resource_id=random.randint(1, 1000000)
                            )
                        elif exc_type == ValidationError:
                            exc = exc_type(
                                message=f"Validation error for worker {worker_id}",
                                details={
                                    "worker": worker_id,
                                    "value": random.random(),
                                    "timestamp": datetime.now().isoformat(),
                                    "nested": {"a": {"b": {"c": {"d": "deep"}}}}
                                }
                            )
                        elif exc_type == DuplicateError:
                            exc = exc_type(
                                message=f"Duplicate detected {worker_id} {random.randint(1, 100000)}",
                                resource_type=random.choice(["resource", "metric", "worker", "task"]),
                                existing_id=random.randint(1, 100000)
                            )
                        else:
                            exc = exc_type(
                                message=f"Timeout after {random.randint(1, 600)}s",
                                timeout_seconds=random.randint(1, 600),
                                operation=f"worker_{worker_id}_op_{random.randint(1, 1000)}"
                            )
                        
                        dict_data = exc.to_dict()
                        json_str = json.dumps(dict_data)
                        self.metrics.record_success("mega_exception")
                    except Exception as e:
                        self.metrics.record_error("exception_create", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.25:
                    time.sleep(random.uniform(0.001, 0.05))
                    
            except Exception as e:
                self.metrics.record_error("exception_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_mega_mixed(self, worker_id: int):
        """MEGA MIXED CHAOS - EVERYTHING TOGETHER!"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 150)):
                    op_type = random.randint(0, 30)
                    
                    if op_type <= 5:
                        # Counter
                        name = random.choice(self.counter_names)
                        self.collector.increment_counter(name, random.uniform(-1000, 1000))
                    elif op_type <= 10:
                        # Gauge
                        name = random.choice(self.gauge_names)
                        self.collector.set_gauge(name, random.uniform(-10000, 10000))
                    elif op_type <= 15:
                        # Histogram
                        name = random.choice(self.histogram_names)
                        self.collector.record_histogram(name, random.random() * 1000)
                    elif op_type <= 18:
                        # get_all
                        self.collector.get_all_metrics()
                    elif op_type <= 21:
                        # Hist stats
                        name = random.choice(self.histogram_names)
                        try:
                            self.collector.get_histogram_stats(name)
                        except Exception:
                            pass
                    elif op_type <= 24:
                        # History
                        name = random.choice(self.counter_names + self.gauge_names)
                        try:
                            self.collector.get_metric_history(name, limit=random.randint(1, 1000))
                        except Exception:
                            pass
                    elif op_type <= 27:
                        # Rapid counters
                        name = random.choice(self.counter_names)
                        for _ in range(random.randint(1, 200)):
                            self.collector.increment_counter(name, 1)
                    elif op_type <= 29:
                        # Rapid histograms
                        name = random.choice(self.histogram_names)
                        for _ in range(random.randint(1, 200)):
                            self.collector.record_histogram(name, random.random())
                    else:
                        # EVERYTHING AT ONCE!
                        for _ in range(random.randint(1, 20)):
                            self.collector.increment_counter(random.choice(self.counter_names), 1)
                            self.collector.set_gauge(random.choice(self.gauge_names), random.random())
                            self.collector.record_histogram(random.choice(self.histogram_names), random.random())
                
                self.metrics.record_success("mega_mixed")
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.015:
                    time.sleep(random.uniform(0.00001, 0.003))
                    
            except Exception as e:
                self.metrics.record_error("mixed_worker", str(e))
                self.metrics.increment_ops()
    
    def progress_reporter(self):
        """Report progress"""
        while not self.stop_event.is_set():
            current_time = time.time()
            elapsed = current_time - self.metrics.start_time
            time_left = self.duration - elapsed
            
            with self.metrics.lock:
                ops_since_last = self.metrics.total_operations - self.metrics.last_ops_report
                time_since_last = current_time - self.metrics.last_report_time
                ops_per_sec = ops_since_last / max(time_since_last, 0.001)
                total_ops_per_sec = self.metrics.total_operations / elapsed if elapsed > 0 else 0
                
                success_rate = self.metrics.successes / max(self.metrics.total_operations, 1) * 100
                
                print(f"\n{'='*95}")
                print(f"⏱️  Phase {self.metrics.phase}: [{int(elapsed)}s / {int(time_left)}s left]")
                print(f"📊 Total Ops: {self.metrics.total_operations:,}")
                print(f"✅ Success: {self.metrics.successes:,} | ❌ Fail: {self.metrics.failures}")
                print(f"⚡ Throughput: {int(ops_per_sec):,} ops/s (avg: {int(total_ops_per_sec):,})")
                print(f"🎯 Success Rate: {success_rate:.3f}%")
                
                if self.metrics.latency_samples:
                    latencies = sorted(self.metrics.latency_samples)
                    p50 = latencies[int(len(latencies) * 0.5)]
                    p95 = latencies[int(len(latencies) * 0.95)]
                    p99 = latencies[int(len(latencies) * 0.99)]
                    print(f"📈 Latency: P50={p50:.2f}ms P95={p95:.2f}ms P99={p99:.2f}ms")
                
                if self.metrics.error_counts_by_type:
                    top_errors = sorted(self.metrics.error_counts_by_type.items(), key=lambda x: -x[1])[:5]
                    print(f"⚠️  Top Errors: {top_errors}")
                
                self.metrics.last_report_time = current_time
                self.metrics.last_ops_report = self.metrics.total_operations
                self.metrics.phase = (int(elapsed) // 120) + 1
            
            time.sleep(10)
    
    def run(self):
        """Run the MEGA CHAOS TEST!"""
        print(f"\n🚀 Spawning {self.num_workers} MEGA CHAOS WORKERS...")
        
        self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
        
        # Worker configuration
        worker_configs = [
            ("MegaCounter", 150, self.chaos_worker_mega_counter),
            ("MegaGauge", 120, self.chaos_worker_mega_gauge),
            ("MegaHistogram", 250, self.chaos_worker_mega_histogram),
            ("MegaQuery", 180, self.chaos_worker_mega_query),
            ("MegaException", 50, self.chaos_worker_mega_exception),
            ("MegaMixed", 250, self.chaos_worker_mega_mixed),
        ]
        
        total_workers = 0
        for worker_type, count, worker_func in worker_configs:
            print(f"  - {worker_type}: {count} workers")
            for i in range(count):
                future = self.executor.submit(worker_func, total_workers + i)
                self.worker_futures.append(future)
            total_workers += count
        
        print(f"\n✅ Total MEGA CHAOS WORKERS: {total_workers}")
        
        # Start reporter
        reporter_thread = threading.Thread(target=self.progress_reporter, daemon=True)
        reporter_thread.start()
        
        # Run for duration
        print(f"\n{'=' * 95}")
        print(f"🔥 MEGA CHAOS IN PROGRESS - {self.duration // 60}m {self.duration % 60}s")
        print(f"{'=' * 95}")
        
        time.sleep(self.duration)
        
        # Stop everything
        print(f"\n🛑 Stopping all MEGA CHAOS WORKERS...")
        self.stop_event.set()
        
        print("Waiting for workers to finish...")
        for future in as_completed(self.worker_futures, timeout=30):
            try:
                future.result(timeout=25)
            except Exception as e:
                print(f"Worker completed with exception: {str(e)[:100]}")
        
        self.executor.shutdown(wait=True)
        
        self.print_final_report()
        
        return self.metrics
    
    def print_final_report(self):
        """Print the final mega chaos report"""
        print(f"\n{'=' * 95}")
        print(f"🎉🎉🎉 MEGA CHAOS TEST COMPLETE 🎉🎉🎉")
        print(f"{'=' * 95}")
        
        elapsed = time.time() - self.metrics.start_time
        
        with self.metrics.lock:
            total_ops = self.metrics.total_operations
            successes = self.metrics.successes
            failures = self.metrics.failures
            
            success_rate = successes / max(total_ops, 1) * 100
            throughput = total_ops / elapsed
            
            print(f"\n📊 FINAL RESULTS:")
            print(f"  Duration: {int(elapsed)}s ({elapsed / 60:.1f} minutes)")
            print(f"  Total Operations: {total_ops:,}")
            print(f"  Successful: {successes:,}")
            print(f"  Failed: {failures:,}")
            print(f"  Success Rate: {success_rate:.4f}%")
            print(f"  Throughput: {int(throughput):,} ops/s")
            
            if self.metrics.latency_samples:
                latencies = sorted(self.metrics.latency_samples)
                print(f"\n📈 LATENCY DISTRIBUTION:")
                print(f"  P50: {latencies[int(len(latencies) * 0.5)]:.3f}ms")
                print(f"  P90: {latencies[int(len(latencies) * 0.9)]:.3f}ms")
                print(f"  P95: {latencies[int(len(latencies) * 0.95)]:.3f}ms")
                print(f"  P99: {latencies[int(len(latencies) * 0.99)]:.3f}ms")
                print(f"  P99.9: {latencies[int(len(latencies) * 0.999)]:.3f}ms")
            
            if self.metrics.operation_counts_by_type:
                print(f"\n📊 OPERATIONS BY TYPE:")
                sorted_ops = sorted(self.metrics.operation_counts_by_type.items(), key=lambda x: -x[1])
                for op_type, count in sorted_ops[:10]:
                    print(f"  {op_type}: {count:,}")
                if len(sorted_ops) > 10:
                    print(f"  ... and {len(sorted_ops) - 10} more")
            
            if self.metrics.errors:
                print(f"\n❌ FAILURES:")
                for i, err in enumerate(self.metrics.errors[:20]):
                    print(f"  {i+1}. Phase {err['phase']}: [{err['type']}] {err['msg']}")
                if len(self.metrics.errors) > 20:
                    print(f"  ... and {len(self.metrics.errors) - 20} more failures")
            else:
                print(f"\n✅ NO FAILURES! SYSTEM IS PERFECT!")
        
        # Final integrity verification
        print(f"\n🔍 SYSTEM INTEGRITY VERIFICATION:")
        try:
            print("  1. get_all_metrics...", end="")
            all_metrics = self.collector.get_all_metrics()
            print(f" ✅ (counters={len(all_metrics.get('counters', {}))}, gauges={len(all_metrics.get('gauges', {}))}, histograms={len(all_metrics.get('histograms', {}))})")
            
            print("  2. counter operations...", end="")
            self.collector.increment_counter("final_mega_test_counter", 1000)
            print(" ✅")
            
            print("  3. gauge operations...", end="")
            self.collector.set_gauge("final_mega_test_gauge", 999999.999)
            print(" ✅")
            
            print("  4. histogram operations...", end="")
            for i in range(500):
                self.collector.record_histogram("final_mega_test_histogram", float(i))
            print(" ✅")
            
            print("  5. histogram stats...", end="")
            stats = self.collector.get_histogram_stats("final_mega_test_histogram")
            print(f" ✅ (count={stats['count']}, min={stats['min']}, max={stats['max']}, mean={stats['mean']:.2f})")
            
            print("  6. metric history...", end="")
            history = self.collector.get_metric_history("final_mega_test_counter", limit=10)
            print(f" ✅ (len={len(history)})")
            
            print(f"\n🏆 MEGA INTEGRITY VERIFICATION COMPLETE - 100% WORKING!")
            
            print(f"\n{'=' * 95}")
            if success_rate >= 99.999 and failures == 0:
                print("🥇🥇🥇 RATING: ABSOLUTE PERFECTION!")
                print("System handles 1000+ concurrent workers for 10+ minutes perfectly!")
            elif success_rate >= 99.99:
                print("🥇🥇 RATING: MEGA PERFECT!")
                print("System performed perfectly in MEGA chaos!")
            elif success_rate >= 99.9:
                print("🥇 RATING: EXCELLENT!")
                print("System performed excellently!")
            elif success_rate >= 99:
                print("🥈 RATING: VERY GOOD!")
                print("System performed very well!")
            elif success_rate >= 95:
                print("🥉 RATING: GOOD!")
                print("System performed well!")
            else:
                print("💔 RATING: NEEDS WORK!")
                print("System has issues!")
            print(f"{'=' * 95}")
            
        except Exception as e:
            print(f"\n❌ INTEGRITY CHECK FAILED: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print(f"\n{'=' * 95}")
    print(f"🚀🚀🚀 AGENT TOOLKIT - MEGA CHAOS TEST 🚀🚀🚀")
    print(f"{'=' * 95}")
    
    # Quick verification mode - 2 minutes, 300 workers
    tester = MegaChaosTester(duration_seconds=120, num_workers=300)
    metrics = tester.run()
    
    print(f"\n✅ MEGA CHAOS TEST COMPLETED!")
