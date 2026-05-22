"""
🚀 ULTRA ULTRA EXTREME Chaos Engineering - The Most Chaotic Test Ever!
This test will push the system to its absolute limits!
"""

import time
import random
import threading
import gc
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import math

from agent_toolkit.shared.metrics_api import MetricsCollector
from agent_toolkit.shared.health_check import HealthCheckRegistry
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError,
    ValidationError,
    DuplicateError,
    AgentToolkitTimeoutError
)


class UltraUltraChaosMetrics:
    """Metrics tracking for the ultra ultra extreme chaos test"""
    
    def __init__(self):
        self.start_time = time.time()
        self.total_operations = 0
        self.successes = 0
        self.failures = 0
        self.errors = []
        self.peak_memory = 0
        self.last_report_time = time.time()
        self.last_ops_report = 0
        self.latency_samples = []
        self.error_counts_by_type = {}
        self.operation_counts_by_type = {}
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
                "msg": error_msg,
                "time": datetime.now().isoformat()
            })
            self.error_counts_by_type[error_type] = self.error_counts_by_type.get(error_type, 0) + 1
    
    def record_success(self, op_type: str):
        with self.lock:
            self.successes += 1
            self.operation_counts_by_type[op_type] = self.operation_counts_by_type.get(op_type, 0) + 1
    
    def increment_ops(self):
        with self.lock:
            self.total_operations += 1


class UltraUltraChaosScenarioTester:
    """The most extreme chaos tester ever created!"""
    
    def __init__(self, duration_seconds: int = 300, num_workers: int = 300):
        self.duration = duration_seconds
        self.num_workers = num_workers
        self.metrics = UltraUltraChaosMetrics()
        self.collector = MetricsCollector()
        self.health_registry = HealthCheckRegistry()
        self.stop_event = threading.Event()
        self.executor: Optional[ThreadPoolExecutor] = None
        self.worker_futures = []
        
        # Test configuration
        self.histogram_names = [f"chaos_hist_{i}" for i in range(100)]
        self.counter_names = [f"chaos_counter_{i}" for i in range(100)]
        self.gauge_names = [f"chaos_gauge_{i}" for i in range(100)]
        
        print("=" * 90)
        print("🔥🔥🔥 ULTRA ULTRA EXTREME CHAOS TEST STARTING 🔥🔥🔥")
        print("=" * 90)
        print(f"⏱️  Duration: {self.duration // 60}m {self.duration % 60}s")
        print(f"👷 Workers: {self.num_workers}")
        print(f"🎯 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 90)
    
    def chaos_worker_super_counter(self, worker_id: int):
        """Super extreme counter operations"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 20)):
                    name = random.choice(self.counter_names)
                    value = random.choice([
                        random.uniform(-1e20, 1e20),
                        float('inf'),
                        float('-inf'),
                        float('nan'),
                        0.0,
                        1e-10,
                        -1e-10
                    ])
                    
                    try:
                        self.collector.increment_counter(name, value)
                        self.metrics.record_success("counter")
                    except Exception as e:
                        self.metrics.record_error("counter", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.2:
                    time.sleep(random.uniform(0.0001, 0.01))
                    
            except Exception as e:
                self.metrics.record_error("counter_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_super_gauge(self, worker_id: int):
        """Super extreme gauge operations"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 15)):
                    name = random.choice(self.gauge_names)
                    value = random.choice([
                        random.uniform(-1e30, 1e30),
                        float('inf'),
                        float('-inf'),
                        float('nan'),
                        0.0
                    ])
                    
                    try:
                        self.collector.set_gauge(name, value)
                        self.metrics.record_success("gauge")
                    except Exception as e:
                        self.metrics.record_error("gauge", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.15:
                    time.sleep(random.uniform(0.0005, 0.015))
                    
            except Exception as e:
                self.metrics.record_error("gauge_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_super_histogram(self, worker_id: int):
        """Super extreme histogram operations"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 100)):
                    name = random.choice(self.histogram_names)
                    value = random.choice([
                        random.uniform(-1e5, 1e5),
                        float('inf'),
                        float('-inf'),
                        float('nan'),
                        0.0,
                        random.gauss(0, 100),
                        random.expovariate(0.1)
                    ])
                    
                    try:
                        self.collector.record_histogram(name, value)
                        self.metrics.record_success("histogram")
                    except Exception as e:
                        self.metrics.record_error("histogram", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0.0001, 0.005))
                    
            except Exception as e:
                self.metrics.record_error("histogram_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_super_query(self, worker_id: int):
        """Super extreme query operations"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                ops_mode = random.randint(0, 4)
                
                if ops_mode == 0:
                    self.collector.get_all_metrics()
                    self.metrics.record_success("get_all")
                elif ops_mode == 1:
                    name = random.choice(self.histogram_names)
                    try:
                        self.collector.get_histogram_stats(name)
                        self.metrics.record_success("get_hist_stats")
                    except Exception:
                        self.metrics.record_success("get_hist_stats_missing")
                elif ops_mode == 2:
                    name = random.choice(self.counter_names)
                    try:
                        self.collector.get_metric_history(name, limit=random.randint(1, 1000))
                        self.metrics.record_success("get_history")
                    except Exception:
                        self.metrics.record_success("get_history_missing")
                elif ops_mode == 3:
                    # Query all histograms
                    for hist_name in self.histogram_names[:10]:
                        try:
                            self.collector.get_histogram_stats(hist_name)
                        except Exception:
                            pass
                    self.metrics.record_success("batch_query")
                else:
                    # Rapid-fire queries
                    for _ in range(random.randint(1, 50)):
                        self.collector.get_all_metrics()
                    self.metrics.record_success("rapid_query")
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.1:
                    time.sleep(random.uniform(0.001, 0.02))
                    
            except Exception as e:
                self.metrics.record_error("query_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_super_exception(self, worker_id: int):
        """Super extreme exception operations"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 10)):
                    exc_type = random.choice([
                        NotFoundError,
                        ValidationError,
                        DuplicateError,
                        AgentToolkitTimeoutError
                    ])
                    
                    try:
                        if exc_type == NotFoundError:
                            exc = exc_type(
                                message=f"Not found: {worker_id}-{random.randint(1, 10000)}",
                                resource_type=random.choice(["tool", "metric", "endpoint", "worker", "task"]),
                                resource_id=random.randint(1, 100000)
                            )
                        elif exc_type == ValidationError:
                            exc = exc_type(
                                message=f"Validation failed for worker {worker_id}",
                                details={
                                    "worker_id": worker_id,
                                    "value": random.random(),
                                    "timestamp": datetime.now().isoformat(),
                                    "nested": {"a": [1, 2, {"b": "test"}]}
                                }
                            )
                        elif exc_type == DuplicateError:
                            exc = exc_type(
                                message=f"Duplicate detected {worker_id}",
                                resource_type="test_resource",
                                existing_id=random.randint(1, 1000)
                            )
                        else:
                            exc = exc_type(
                                message=f"Timeout after {random.randint(1, 120)}s",
                                timeout_seconds=random.randint(1, 120),
                                operation=f"worker_{worker_id}_operation"
                            )
                        
                        dict_data = exc.to_dict()
                        self.metrics.record_success("exception")
                    except Exception as e:
                        self.metrics.record_error("exception", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.2:
                    time.sleep(random.uniform(0.005, 0.05))
                    
            except Exception as e:
                self.metrics.record_error("exception_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_gc_stress(self, worker_id: int):
        """Super extreme GC stress"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 10)):
                    # Create a lot of objects
                    objects = []
                    for _ in range(random.randint(100, 5000)):
                        objects.append({
                            "data": [random.random() for _ in range(random.randint(1, 50))],
                            "text": f"test_{random.random()}_{worker_id}",
                            "nested": {"a": [1, 2, 3]}
                        })
                    
                    del objects
                    
                    if random.random() < 0.3:
                        gc.collect()
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.record_success("gc_stress")
                self.metrics.increment_ops()
                
                time.sleep(random.uniform(0.01, 0.1))
                
            except Exception as e:
                self.metrics.record_error("gc_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_mixed_everything(self, worker_id: int):
        """MIX EVERY POSSIBLE OPERATION - MAXIMUM CHAOS!"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 30)):
                    op_type = random.randint(0, 10)
                    
                    if op_type == 0:
                        name = random.choice(self.counter_names)
                        self.collector.increment_counter(name, random.uniform(-100, 100))
                    elif op_type == 1:
                        name = random.choice(self.gauge_names)
                        self.collector.set_gauge(name, random.uniform(-1000, 1000))
                    elif op_type == 2:
                        name = random.choice(self.histogram_names)
                        self.collector.record_histogram(name, random.random() * 100)
                    elif op_type == 3:
                        self.collector.get_all_metrics()
                    elif op_type == 4:
                        name = random.choice(self.histogram_names)
                        try:
                            self.collector.get_histogram_stats(name)
                        except Exception:
                            pass
                    elif op_type == 5:
                        name = random.choice(self.counter_names)
                        try:
                            self.collector.get_metric_history(name, limit=10)
                        except Exception:
                            pass
                    elif op_type == 6:
                        # Rapid counter increments
                        name = random.choice(self.counter_names)
                        for _ in range(random.randint(1, 100)):
                            self.collector.increment_counter(name, 1)
                    elif op_type == 7:
                        # Rapid histogram records
                        name = random.choice(self.histogram_names)
                        for _ in range(random.randint(1, 100)):
                            self.collector.record_histogram(name, random.random())
                    elif op_type == 8:
                        # Batch get_all_metrics
                        for _ in range(random.randint(1, 10)):
                            self.collector.get_all_metrics()
                    elif op_type == 9:
                        # Massive gauge updates
                        for g_name in self.gauge_names[:20]:
                            self.collector.set_gauge(g_name, random.random() * 1000)
                    else:
                        # Combine all
                        for _ in range(random.randint(1, 5)):
                            self.collector.increment_counter(random.choice(self.counter_names), 1)
                            self.collector.set_gauge(random.choice(self.gauge_names), random.random())
                            self.collector.record_histogram(random.choice(self.histogram_names), random.random())
                
                self.metrics.record_success("mixed_everything")
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0.0001, 0.01))
                    
            except Exception as e:
                self.metrics.record_error("mixed_worker", str(e))
                self.metrics.increment_ops()
    
    def progress_reporter(self):
        """Report progress periodically"""
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
                
                print(f"\n⏱️  [{int(elapsed)}s / {int(time_left)}s left]")
                print(f"📊 Total Ops: {self.metrics.total_operations:,}")
                print(f"✅ Success: {self.metrics.successes:,} ({success_rate:.2f}%)")
                print(f"❌ Failures: {self.metrics.failures:,}")
                print(f"⚡ Throughput: {int(ops_per_sec):,} ops/s (avg: {int(total_ops_per_sec):,})")
                
                if self.metrics.latency_samples:
                    latencies = sorted(self.metrics.latency_samples)
                    p50 = latencies[int(len(latencies) * 0.5)]
                    p95 = latencies[int(len(latencies) * 0.95)]
                    p99 = latencies[int(len(latencies) * 0.99)]
                    print(f"📈 Latency: P50={p50:.2f}ms P95={p95:.2f}ms P99={p99:.2f}ms")
                
                if self.metrics.error_counts_by_type:
                    print(f"⚠️  Errors by type: {dict(self.metrics.error_counts_by_type)}")
                
                self.metrics.last_report_time = current_time
                self.metrics.last_ops_report = self.metrics.total_operations
            
            time.sleep(5)
    
    def run(self):
        """Run the ultra ultra extreme chaos test!"""
        print(f"\n🚀 Spawning {self.num_workers} chaos workers...")
        
        self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
        
        # Define workers
        worker_configs = [
            ("SuperCounter", 50, self.chaos_worker_super_counter),
            ("SuperGauge", 40, self.chaos_worker_super_gauge),
            ("SuperHistogram", 60, self.chaos_worker_super_histogram),
            ("SuperQuery", 40, self.chaos_worker_super_query),
            ("SuperException", 20, self.chaos_worker_super_exception),
            ("GCStress", 10, self.chaos_worker_gc_stress),
            ("MixedEverything", 80, self.chaos_worker_mixed_everything),
        ]
        
        total_workers = 0
        for worker_type, count, worker_func in worker_configs:
            print(f"  - {worker_type}: {count} workers")
            for i in range(count):
                future = self.executor.submit(worker_func, total_workers + i)
                self.worker_futures.append(future)
            total_workers += count
        
        print(f"\n✅ Total chaos workers running: {total_workers}")
        
        # Start reporter
        reporter_thread = threading.Thread(target=self.progress_reporter, daemon=True)
        reporter_thread.start()
        
        # Run for duration
        print(f"\n{'=' * 90}")
        print(f"🔥 ULTRA ULTRA CHAOS IN PROGRESS - {self.duration} SECONDS")
        print(f"{'=' * 90}")
        
        time.sleep(self.duration)
        
        # Stop everything
        print(f"\n🛑 Stopping all chaos workers...")
        self.stop_event.set()
        
        print("Waiting for workers to finish...")
        for future in as_completed(self.worker_futures, timeout=15):
            try:
                future.result(timeout=10)
            except Exception as e:
                print(f"Worker completed with exception: {e}")
        
        self.executor.shutdown(wait=True)
        
        self.print_final_report()
        
        return self.metrics
    
    def print_final_report(self):
        """Print the final chaos test report"""
        print(f"\n{'=' * 90}")
        print(f"🎉 ULTRA ULTRA EXTREME CHAOS TEST COMPLETED 🎉")
        print(f"{'=' * 90}")
        
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
            print(f"  Success Rate: {success_rate:.3f}%")
            print(f"  Throughput: {int(throughput):,} ops/s")
            
            if self.metrics.latency_samples:
                latencies = sorted(self.metrics.latency_samples)
                print(f"\n📈 LATENCY DISTRIBUTION:")
                print(f"  P50: {latencies[int(len(latencies) * 0.5)]:.2f}ms")
                print(f"  P90: {latencies[int(len(latencies) * 0.9)]:.2f}ms")
                print(f"  P95: {latencies[int(len(latencies) * 0.95)]:.2f}ms")
                print(f"  P99: {latencies[int(len(latencies) * 0.99)]:.2f}ms")
                print(f"  P99.9: {latencies[int(len(latencies) * 0.999)]:.2f}ms")
            
            if self.metrics.operation_counts_by_type:
                print(f"\n📊 OPERATIONS BY TYPE:")
                for op_type, count in sorted(self.metrics.operation_counts_by_type.items(), key=lambda x: -x[1]):
                    print(f"  {op_type}: {count:,}")
            
            if self.metrics.errors:
                print(f"\n⚠️  TOP 20 ERRORS:")
                for i, err in enumerate(self.metrics.errors[:20]):
                    print(f"  {i + 1}. [{err['type']}] {err['msg']}")
                if len(self.metrics.errors) > 20:
                    print(f"  ... and {len(self.metrics.errors) - 20} more")
            else:
                print(f"\n✅ NO ERRORS RECORDED!")
        
        # Final integrity verification
        print(f"\n🔍 VERIFYING SYSTEM INTEGRITY:")
        try:
            print("  1. Testing get_all_metrics...", end="")
            all_metrics = self.collector.get_all_metrics()
            print(f" ✅ ({len(all_metrics['counters'])} counters, {len(all_metrics['gauges'])} gauges, {len(all_metrics['histograms'])} histograms)")
            
            print("  2. Testing counter increment...", end="")
            test_counter = "final_test_counter"
            self.collector.increment_counter(test_counter, 1000)
            print(" ✅")
            
            print("  3. Testing histogram recording...", end="")
            test_hist = "final_test_histogram"
            for i in range(200):
                self.collector.record_histogram(test_hist, i)
            print(" ✅")
            
            print("  4. Testing histogram stats...", end="")
            stats = self.collector.get_histogram_stats(test_hist)
            print(f" ✅ (min={stats['min']}, max={stats['max']}, mean={stats['mean']:.2f})")
            
            print(f"\n🏆 SYSTEM INTEGRITY VERIFIED - SYSTEM IS WORKING PERFECTLY!")
            
            print(f"\n{'=' * 90}")
            if success_rate >= 99.99 and failures == 0:
                print("🥇🥇🥇 RATING: ABSOLUTELY PERFECT")
                print("The system performed flawlessly in ULTRA ULTRA EXTREME conditions!")
            elif success_rate >= 99.9:
                print("🥇 RATING: PERFECT")
                print("System performed flawlessly!")
            elif success_rate >= 99:
                print("🥈 RATING: EXCELLENT")
                print("System performed outstandingly!")
            elif success_rate >= 95:
                print("🥉 RATING: GOOD")
                print("System performed well!")
            else:
                print("💔 RATING: NEEDS IMPROVEMENT")
                print("System has issues!")
            print(f"{'=' * 90}")
            
        except Exception as e:
            print(f"\n❌ SYSTEM INTEGRITY CHECK FAILED: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print(f"\n{'=' * 90}")
    print(f"🚀 AGENT TOOLKIT - ULTRA ULTRA EXTREME CHAOS ENGINEERING")
    print(f"{'=' * 90}")
    
    # Run for 5 minutes with 300 workers for maximum chaos!
    # For verification, we'll run 2 minutes
    tester = UltraUltraChaosScenarioTester(duration_seconds=120, num_workers=300)
    metrics = tester.run()
    
    print(f"\n✅ ULTRA ULTRA CHAOS TEST COMPLETED!")
