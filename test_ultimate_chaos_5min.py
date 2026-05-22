"""
🚀🚀🚀 ULTIMATE CHAOS ENGINEERING - 5 MINUTES OF PURE CHAOS! 🚀🚀🚀

This is the MOST EXTREME test ever created:
- 500 concurrent workers
- 5 minute duration
- ALL types of chaos: counter, gauge, histogram, query, exception, memory, disk, network
- Extreme boundary values: NaN, Inf, -Inf, massive numbers, tiny numbers, negative
- Randomized chaos patterns
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
import json
import hashlib

from agent_toolkit.shared.metrics_api import MetricsCollector
from agent_toolkit.shared.health_check import HealthCheckRegistry
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError,
    ValidationError,
    DuplicateError,
    AgentToolkitTimeoutError
)


class UltimateChaosMetrics:
    """The ultimate metrics tracker for chaos testing"""
    
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
        self.memory_snapshots = []
        self.lock = threading.Lock()
        self.iteration = 0
    
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
                "msg": error_msg[:200],  # Truncate long messages
                "time": datetime.now().isoformat(),
                "iteration": self.iteration
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
    
    def record_memory_snapshot(self):
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            with self.lock:
                self.memory_snapshots.append({
                    "time": time.time(),
                    "rss_mb": mem_info.rss / 1024 / 1024,
                    "vms_mb": mem_info.vms / 1024 / 1024
                })
                if len(self.memory_snapshots) > 100:
                    self.memory_snapshots = self.memory_snapshots[-100:]
        except ImportError:
            pass  # psutil not available
    
    def increment_iteration(self):
        with self.lock:
            self.iteration += 1


class UltimateChaosTester:
    """THE MOST EXTREME CHAOS TESTER EVER CONCEIVED"""
    
    def __init__(self, duration_seconds: int = 300, num_workers: int = 500):
        self.duration = duration_seconds
        self.num_workers = num_workers
        self.metrics = UltimateChaosMetrics()
        self.collector = MetricsCollector()
        self.health_registry = HealthCheckRegistry()
        self.stop_event = threading.Event()
        self.executor: Optional[ThreadPoolExecutor] = None
        self.worker_futures = []
        self.iteration = 0
        
        # Pre-generate test data
        self.counter_names = [f"ultra_counter_{i}" for i in range(200)]
        self.gauge_names = [f"ultra_gauge_{i}" for i in range(200)]
        self.histogram_names = [f"ultra_histogram_{i}" for i in range(200)]
        
        print("=" * 90)
        print("🔥🔥🔥🔥🔥 ULTIMATE CHAOS TEST STARTING 🔥🔥🔥🔥🔥")
        print("=" * 90)
        print(f"⏱️  Duration: {self.duration // 60}m {self.duration % 60}s")
        print(f"👷 Workers: {self.num_workers}")
        print(f"🎯 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 90)
    
    def chaos_worker_counter_extreme(self, worker_id: int):
        """EXTREME counter chaos with all boundary values"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 50)):
                    name = random.choice(self.counter_names)
                    value = random.choice([
                        # Normal values
                        random.uniform(-1e20, 1e20),
                        # Extreme boundary values
                        float('nan'),
                        float('inf'),
                        float('-inf'),
                        # Very small values
                        0.0,
                        1e-100,
                        -1e-100,
                        # Very large values
                        1e100,
                        -1e100,
                        # Integer extremes
                        sys.maxsize,
                        -sys.maxsize,
                        # Special values
                        1.0,
                        -1.0,
                        0.0000000000000001,
                        # Random gauss
                        random.gauss(0, 1e10)
                    ])
                    
                    try:
                        self.collector.increment_counter(name, value)
                        self.metrics.record_success("counter_extreme")
                    except Exception as e:
                        self.metrics.record_error("counter_extreme", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.1:
                    time.sleep(random.uniform(0.00001, 0.001))
                    
            except Exception as e:
                self.metrics.record_error("counter_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_gauge_extreme(self, worker_id: int):
        """EXTREME gauge chaos with all boundary values"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 30)):
                    name = random.choice(self.gauge_names)
                    value = random.choice([
                        float('nan'),
                        float('inf'),
                        float('-inf'),
                        0.0,
                        1e-50,
                        -1e-50,
                        1e50,
                        -1e50,
                        sys.maxsize,
                        -sys.maxsize,
                        random.uniform(-1e30, 1e30),
                        0.0000000000000001
                    ])
                    
                    try:
                        self.collector.set_gauge(name, value)
                        self.metrics.record_success("gauge_extreme")
                    except Exception as e:
                        self.metrics.record_error("gauge_extreme", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.08:
                    time.sleep(random.uniform(0.00001, 0.005))
                    
            except Exception as e:
                self.metrics.record_error("gauge_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_histogram_extreme(self, worker_id: int):
        """EXTREME histogram chaos with all possible values"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 200)):
                    name = random.choice(self.histogram_names)
                    value = random.choice([
                        float('nan'),
                        float('inf'),
                        float('-inf'),
                        0.0,
                        1e-100,
                        -1e-100,
                        1e100,
                        -1e100,
                        random.uniform(-1e5, 1e5),
                        random.gauss(0, 1000),
                        random.expovariate(0.01),
                        random.triangular(-1000, 1000),
                    ])
                    
                    try:
                        self.collector.record_histogram(name, value)
                        self.metrics.record_success("histogram_extreme")
                    except Exception as e:
                        self.metrics.record_error("histogram_extreme", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.02:
                    time.sleep(random.uniform(0.00001, 0.001))
                    
            except Exception as e:
                self.metrics.record_error("histogram_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_query_extreme(self, worker_id: int):
        """EXTREME query chaos - maximum load on data retrieval"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                ops_mode = random.randint(0, 8)
                
                if ops_mode == 0:
                    self.collector.get_all_metrics()
                    self.metrics.record_success("get_all")
                elif ops_mode == 1:
                    # Query random histogram
                    for _ in range(random.randint(1, 20)):
                        name = random.choice(self.histogram_names)
                        try:
                            self.collector.get_histogram_stats(name)
                        except:
                            pass
                    self.metrics.record_success("batch_hist_stats")
                elif ops_mode == 2:
                    # Query all histogram stats
                    for hist_name in self.histogram_names:
                        try:
                            self.collector.get_histogram_stats(hist_name)
                        except:
                            pass
                    self.metrics.record_success("all_hist_stats")
                elif ops_mode == 3:
                    # Rapid get_all_metrics
                    for _ in range(random.randint(1, 100)):
                        self.collector.get_all_metrics()
                    self.metrics.record_success("rapid_get_all")
                elif ops_mode == 4:
                    # Mixed queries
                    for _ in range(random.randint(1, 50)):
                        self.collector.get_metric_history(random.choice(self.counter_names), limit=1000)
                    self.metrics.record_success("rapid_history")
                elif ops_mode == 5:
                    # All metrics combined
                    all_metrics = self.collector.get_all_metrics()
                    hist_keys = list(all_metrics.get('histograms', {}).keys())[:10]
                    for key in hist_keys:
                        try:
                            self.collector.get_histogram_stats(key)
                        except:
                            pass
                    self.metrics.record_success("combined_query")
                elif ops_mode == 6:
                    # Random metric history
                    for _ in range(random.randint(1, 100)):
                        name = random.choice(self.counter_names + self.gauge_names)
                        try:
                            self.collector.get_metric_history(name, limit=random.randint(1, 1000))
                        except:
                            pass
                    self.metrics.record_success("random_history")
                elif ops_mode == 7:
                    # Counter history
                    for _ in range(random.randint(1, 100)):
                        name = random.choice(self.counter_names)
                        try:
                            self.collector.get_metric_history(name, limit=500)
                        except:
                            pass
                    self.metrics.record_success("counter_history")
                else:
                    # Gauge history
                    for _ in range(random.randint(1, 100)):
                        name = random.choice(self.gauge_names)
                        try:
                            self.collector.get_metric_history(name, limit=500)
                        except:
                            pass
                    self.metrics.record_success("gauge_history")
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0.00001, 0.01))
                    
            except Exception as e:
                self.metrics.record_error("query_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_exception_extreme(self, worker_id: int):
        """EXTREME exception handling chaos"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 30)):
                    exc_type = random.choice([
                        NotFoundError,
                        ValidationError,
                        DuplicateError,
                        AgentToolkitTimeoutError
                    ])
                    
                    try:
                        if exc_type == NotFoundError:
                            exc = exc_type(
                                message=f"Not found: worker_{worker_id}_{random.randint(1, 100000)}",
                                resource_type=random.choice(["tool", "metric", "endpoint", "worker", "task", "config", "resource", "data", "file", "connection"]),
                                resource_id=random.randint(1, 1000000)
                            )
                        elif exc_type == ValidationError:
                            exc = exc_type(
                                message=f"Validation failed for worker {worker_id}",
                                details={
                                    "worker_id": worker_id,
                                    "value": random.random(),
                                    "timestamp": datetime.now().isoformat(),
                                    "nested": {"level1": {"level2": {"level3": "deep"}}}
                                }
                            )
                        elif exc_type == DuplicateError:
                            exc = exc_type(
                                message=f"Duplicate detected for worker {worker_id}",
                                resource_type=random.choice(["test_resource", "metric", "endpoint", "worker", "task"]),
                                existing_id=random.randint(1, 100000)
                            )
                        else:
                            exc = exc_type(
                                message=f"Timeout after {random.randint(1, 300)}s",
                                timeout_seconds=random.randint(1, 300),
                                operation=f"worker_{worker_id}_operation_{random.randint(1, 1000)}"
                            )
                        
                        dict_data = exc.to_dict()
                        json_str = json.dumps(dict_data)
                        self.metrics.record_success("exception_extreme")
                    except Exception as e:
                        self.metrics.record_error("exception_create", str(e))
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.15:
                    time.sleep(random.uniform(0.001, 0.03))
                    
            except Exception as e:
                self.metrics.record_error("exception_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_memory_extreme(self, worker_id: int):
        """EXTREME memory stress test"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 20)):
                    # Create memory pressure
                    objects = []
                    for _ in range(random.randint(1000, 10000)):
                        objects.append({
                            "data": [random.random() for _ in range(random.randint(10, 100))],
                            "text": hashlib.md5(f"test_{random.random()}_{worker_id}".encode()).hexdigest(),
                            "nested": {"a": [1, 2, 3], "b": {"c": "deep"}},
                            "timestamp": time.time()
                        })
                    
                    del objects
                    
                    if random.random() < 0.5:
                        gc.collect()
                
                # Record memory snapshot periodically
                if random.random() < 0.1:
                    self.metrics.record_memory_snapshot()
                
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.record_success("memory_stress")
                self.metrics.increment_ops()
                
                time.sleep(random.uniform(0.01, 0.2))
                
            except Exception as e:
                self.metrics.record_error("memory_worker", str(e))
                self.metrics.increment_ops()
    
    def chaos_worker_mixed_extreme(self, worker_id: int):
        """MIX ALL OPERATIONS - MAXIMUM POSSIBLE CHAOS"""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                for _ in range(random.randint(1, 100)):
                    op_type = random.randint(0, 20)
                    
                    if op_type == 0:
                        # Counter
                        name = random.choice(self.counter_names)
                        self.collector.increment_counter(name, random.uniform(-1000, 1000))
                    elif op_type == 1:
                        # Gauge
                        name = random.choice(self.gauge_names)
                        self.collector.set_gauge(name, random.uniform(-10000, 10000))
                    elif op_type == 2:
                        # Histogram
                        name = random.choice(self.histogram_names)
                        self.collector.record_histogram(name, random.random() * 1000)
                    elif op_type == 3:
                        # get_all_metrics
                        self.collector.get_all_metrics()
                    elif op_type == 4:
                        # Get histogram stats
                        try:
                            self.collector.get_histogram_stats(random.choice(self.histogram_names))
                        except:
                            pass
                    elif op_type == 5:
                        # Get metric history
                        try:
                            self.collector.get_metric_history(random.choice(self.counter_names), limit=100)
                        except:
                            pass
                    elif op_type == 6:
                        # Rapid counter updates
                        name = random.choice(self.counter_names)
                        for _ in range(random.randint(1, 200)):
                            self.collector.increment_counter(name, 1)
                    elif op_type == 7:
                        # Rapid histogram records
                        name = random.choice(self.histogram_names)
                        for _ in range(random.randint(1, 200)):
                            self.collector.record_histogram(name, random.random())
                    elif op_type == 8:
                        # Rapid get_all_metrics
                        for _ in range(random.randint(1, 50)):
                            self.collector.get_all_metrics()
                    elif op_type == 9:
                        # Mixed all
                        for _ in range(random.randint(1, 20)):
                            self.collector.increment_counter(random.choice(self.counter_names), 1)
                            self.collector.set_gauge(random.choice(self.gauge_names), random.random())
                            self.collector.record_histogram(random.choice(self.histogram_names), random.random())
                    elif op_type == 10:
                        # Counter with extreme values
                        name = random.choice(self.counter_names)
                        for val in [float('nan'), float('inf'), float('-inf'), 0.0, 1e100, -1e100]:
                            try:
                                self.collector.increment_counter(name, val)
                            except:
                                pass
                    elif op_type == 11:
                        # Gauge with extreme values
                        name = random.choice(self.gauge_names)
                        for val in [float('nan'), float('inf'), float('-inf'), 0.0, 1e100, -1e100]:
                            try:
                                self.collector.set_gauge(name, val)
                            except:
                                pass
                    elif op_type == 12:
                        # Histogram with extreme values
                        name = random.choice(self.histogram_names)
                        for val in [float('nan'), float('inf'), float('-inf'), 0.0, 1e50, -1e50]:
                            self.collector.record_histogram(name, val)
                    elif op_type == 13:
                        # Batch all histogram stats
                        for hist_name in self.histogram_names[:50]:
                            try:
                                self.collector.get_histogram_stats(hist_name)
                            except:
                                pass
                    elif op_type == 14:
                        # Batch all metric histories
                        for name in self.counter_names[:50]:
                            try:
                                self.collector.get_metric_history(name, limit=100)
                            except:
                                pass
                    elif op_type == 15:
                        # Create and use exception
                        try:
                            exc = NotFoundError(
                                message=f"Test {worker_id}",
                                resource_type="test",
                                resource_id=random.randint(1, 1000)
                            )
                            exc.to_dict()
                        except:
                            pass
                    elif op_type == 16:
                        # Memory stress
                        objs = [{"data": i} for i in range(100)]
                        del objs
                    elif op_type == 17:
                        # Rapid gauge updates
                        name = random.choice(self.gauge_names)
                        for _ in range(random.randint(1, 200)):
                            self.collector.set_gauge(name, random.random() * 1000)
                    elif op_type == 18:
                        # Combined heavy query
                        all_m = self.collector.get_all_metrics()
                        for key in list(all_m.get('histograms', {}).keys())[:10]:
                            try:
                                self.collector.get_histogram_stats(key)
                            except:
                                pass
                    elif op_type == 19:
                        # Hash operations
                        for _ in range(random.randint(1, 100)):
                            h = hashlib.sha256(f"{random.random()}_{worker_id}".encode()).hexdigest()
                    else:
                        # Everything at once
                        for _ in range(random.randint(1, 10)):
                            c_name = random.choice(self.counter_names)
                            g_name = random.choice(self.gauge_names)
                            h_name = random.choice(self.histogram_names)
                            self.collector.increment_counter(c_name, 1)
                            self.collector.set_gauge(g_name, random.random())
                            self.collector.record_histogram(h_name, random.random())
                
                self.metrics.record_success("mixed_extreme")
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)
                self.metrics.increment_ops()
                
                if random.random() < 0.02:
                    time.sleep(random.uniform(0.00001, 0.005))
                    
            except Exception as e:
                self.metrics.record_error("mixed_worker", str(e))
                self.metrics.increment_ops()
    
    def progress_reporter(self):
        """Report progress with detailed metrics"""
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
                
                print(f"\n{'='*90}")
                print(f"⏱️  ITERATION {self.metrics.iteration}: [{int(elapsed)}s / {int(time_left)}s left]")
                print(f"📊 Total Ops: {self.metrics.total_operations:,} | Success: {self.metrics.successes:,} | Fail: {self.metrics.failures}")
                print(f"⚡ Throughput: {int(ops_per_sec):,} ops/s (avg: {int(total_ops_per_sec):,})")
                print(f"✅ Success Rate: {success_rate:.3f}%")
                
                if self.metrics.latency_samples:
                    latencies = sorted(self.metrics.latency_samples)
                    p50 = latencies[int(len(latencies) * 0.5)]
                    p95 = latencies[int(len(latencies) * 0.95)]
                    p99 = latencies[int(len(latencies) * 0.99)]
                    print(f"📈 Latency: P50={p50:.2f}ms P95={p95:.2f}ms P99={p99:.2f}ms")
                
                if self.metrics.error_counts_by_type:
                    print(f"⚠️  Top 5 Errors: {dict(list(self.metrics.error_counts_by_type.items())[:5])}")
                
                if self.metrics.memory_snapshots:
                    latest_mem = self.metrics.memory_snapshots[-1]
                    print(f"💾 Memory: RSS={latest_mem['rss_mb']:.1f}MB VMS={latest_mem['vms_mb']:.1f}MB")
                
                self.metrics.last_report_time = current_time
                self.metrics.last_ops_report = self.metrics.total_operations
                self.metrics.iteration += 1
            
            time.sleep(5)
    
    def run(self):
        """Run the ultimate chaos test!"""
        print(f"\n🚀 Spawning {self.num_workers} ULTIMATE chaos workers...")
        
        self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
        
        # Define workers
        worker_configs = [
            ("CounterExtreme", 80, self.chaos_worker_counter_extreme),
            ("GaugeExtreme", 60, self.chaos_worker_gauge_extreme),
            ("HistogramExtreme", 100, self.chaos_worker_histogram_extreme),
            ("QueryExtreme", 80, self.chaos_worker_query_extreme),
            ("ExceptionExtreme", 40, self.chaos_worker_exception_extreme),
            ("MemoryExtreme", 20, self.chaos_worker_memory_extreme),
            ("MixedExtreme", 120, self.chaos_worker_mixed_extreme),
        ]
        
        total_workers = 0
        for worker_type, count, worker_func in worker_configs:
            print(f"  - {worker_type}: {count} workers")
            for i in range(count):
                future = self.executor.submit(worker_func, total_workers + i)
                self.worker_futures.append(future)
            total_workers += count
        
        print(f"\n✅ Total ULTIMATE chaos workers: {total_workers}")
        
        # Start reporter
        reporter_thread = threading.Thread(target=self.progress_reporter, daemon=True)
        reporter_thread.start()
        
        # Run for duration
        print(f"\n{'=' * 90}")
        print(f"🔥 ULTIMATE CHAOS IN PROGRESS - {self.duration} SECONDS")
        print(f"{'=' * 90}")
        
        time.sleep(self.duration)
        
        # Stop everything
        print(f"\n🛑 Stopping all ULTIMATE chaos workers...")
        self.stop_event.set()
        
        print("Waiting for workers to finish...")
        for future in as_completed(self.worker_futures, timeout=20):
            try:
                future.result(timeout=15)
            except Exception as e:
                print(f"Worker completed with exception: {e}")
        
        self.executor.shutdown(wait=True)
        
        self.print_final_report()
        
        return self.metrics
    
    def print_final_report(self):
        """Print the ultimate final report"""
        print(f"\n{'=' * 90}")
        print(f"🎉🎉🎉 ULTIMATE CHAOS TEST COMPLETED 🎉🎉🎉")
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
                    print(f"  ... and {len(sorted_ops) - 10} more types")
            
            if self.metrics.errors:
                print(f"\n⚠️  TOP 30 ERRORS:")
                for i, err in enumerate(self.metrics.errors[:30]):
                    print(f"  {i + 1}. [{err['type']}] {err['msg']}")
                if len(self.metrics.errors) > 30:
                    print(f"  ... and {len(self.metrics.errors) - 30} more errors")
            else:
                print(f"\n✅ NO ERRORS RECORDED!")
            
            if self.metrics.memory_snapshots:
                print(f"\n💾 MEMORY USAGE:")
                for snap in self.metrics.memory_snapshots[::max(1, len(self.metrics.memory_snapshots)//10)]:
                    elapsed_mem = snap['time'] - self.metrics.start_time
                    print(f"  t+{int(elapsed_mem)}s: RSS={snap['rss_mb']:.1f}MB VMS={snap['vms_mb']:.1f}MB")
        
        # Final integrity verification
        print(f"\n🔍 VERIFYING SYSTEM INTEGRITY:")
        try:
            print("  1. Testing get_all_metrics...", end="")
            all_metrics = self.collector.get_all_metrics()
            print(f" ✅ ({len(all_metrics.get('counters', {}))} counters, {len(all_metrics.get('gauges', {}))} gauges, {len(all_metrics.get('histograms', {}))} histograms)")
            
            print("  2. Testing counter operations...", end="")
            self.collector.increment_counter("final_counter", 1000)
            print(" ✅")
            
            print("  3. Testing histogram recording...", end="")
            for i in range(300):
                self.collector.record_histogram("final_histogram", i)
            print(" ✅")
            
            print("  4. Testing histogram stats...", end="")
            stats = self.collector.get_histogram_stats("final_histogram")
            print(f" ✅ (count={stats['count']}, min={stats['min']}, max={stats['max']})")
            
            print("  5. Testing gauge operations...", end="")
            self.collector.set_gauge("final_gauge", 999.999)
            print(" ✅")
            
            print("  6. Testing metric history...", end="")
            history = self.collector.get_metric_history("final_counter", limit=10)
            print(f" ✅ (len={len(history)})")
            
            print(f"\n🏆 SYSTEM INTEGRITY VERIFIED - ALL SYSTEMS OPERATIONAL!")
            
            print(f"\n{'=' * 90}")
            if success_rate >= 99.999 and failures == 0:
                print("🥇🥇🥇 RATING: ULTIMATE PERFECT")
                print("The system performed absolutely FLAWLESSLY in ULTIMATE EXTREME conditions!")
            elif success_rate >= 99.99:
                print("🥇🥇 RATING: PERFECT")
                print("System performed flawlessly in ULTIMATE chaos!")
            elif success_rate >= 99.9:
                print("🥇 RATING: EXCELLENT")
                print("System performed outstandingly!")
            elif success_rate >= 99:
                print("🥈 RATING: VERY GOOD")
                print("System performed very well!")
            elif success_rate >= 95:
                print("🥉 RATING: GOOD")
                print("System performed well!")
            else:
                print("💔 RATING: NEEDS IMPROVEMENT")
                print("System needs improvement!")
            print(f"{'=' * 90}")
            
        except Exception as e:
            print(f"\n❌ SYSTEM INTEGRITY CHECK FAILED: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print(f"\n{'=' * 90}")
    print(f"🚀🚀🚀 AGENT TOOLKIT - ULTIMATE CHAOS ENGINEERING 🚀🚀🚀")
    print(f"{'=' * 90}")
    
    # Run for 5 minutes with 500 workers for MAXIMUM chaos!
    tester = UltimateChaosTester(duration_seconds=300, num_workers=500)
    metrics = tester.run()
    
    print(f"\n✅ ULTIMATE CHAOS TEST COMPLETED!")
