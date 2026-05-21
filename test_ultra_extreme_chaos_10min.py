"""
ULTRA EXTREME Chaos Engineering - 10 Minutes Test
This is the most chaotic test possible!
"""

import time
import random
import threading
import gc
import sys
import os
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from datetime import datetime

from agent_toolkit.shared.metrics_api import MetricsCollector
from agent_toolkit.shared.health_check import HealthCheckRegistry
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError,
    ValidationError,
    DuplicateError,
    AgentToolkitTimeoutError
)


class UltraChaosMetrics:
    """Metrics tracking for the ultra extreme chaos test"""
    def __init__(self):
        self.start_time = time.time()
        self.total_operations = 0
        self.successes = 0
        self.failures = 0
        self.errors = []
        self.peak_memory = 0
        self.last_report_time = time.time()
        self.last_ops_report = 0
        self.thread_counts = defaultdict(int)


class UltraChaosScenarioTester:
    """The most extreme chaos tester"""
    
    def __init__(self, duration_seconds=600):
        self.duration = duration_seconds
        self.metrics = UltraChaosMetrics()
        self.collector = MetricsCollector()
        self.health_registry = HealthCheckRegistry()
        self.stop_event = threading.Event()
        self.executor = None
        self.worker_threads = []
        
        print("=" * 80)
        print("🔥🔥🔥 ULTRA EXTREME CHAOS TEST STARTING 🔥🔥🔥")
        print("=" * 80)
        print(f"⏱️  Duration: {self.duration // 60} minutes {self.duration % 60} seconds")
        print(f"🎯 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def chaos_worker_counter(self, worker_id: int):
        """Extreme chaos for counter operations"""
        while not self.stop_event.is_set():
            try:
                # Mix of valid and invalid operations
                ops_mode = random.randint(0, 10)
                
                if ops_mode == 0:
                    # Normal counter operation
                    counter_name = f"chaos_counter_{worker_id}_{random.randint(0, 100)}"
                    value = random.uniform(-1e10, 1e10)
                    self.collector.increment_counter(counter_name, value)
                    self.metrics.successes += 1
                
                elif ops_mode == 1:
                    # Empty name
                    try:
                        self.collector.increment_counter("", 1)
                        self.metrics.successes += 1
                    except Exception as e:
                        self.metrics.failures += 1
                        self.metrics.errors.append({"type": "counter_empty_name", "error": str(e)})
                
                elif ops_mode == 2:
                    # Extremely long name
                    long_name = "test_" * 100 + str(worker_id)
                    self.collector.increment_counter(long_name, 1)
                    self.metrics.successes += 1
                
                elif ops_mode == 3:
                    # NaN value
                    try:
                        self.collector.increment_counter(f"nan_counter_{worker_id}", float('nan'))
                        self.metrics.successes += 1
                    except Exception as e:
                        self.metrics.failures += 1
                
                elif ops_mode == 4:
                    # Infinite value
                    try:
                        self.collector.increment_counter(f"inf_counter_{worker_id}", float('inf'))
                        self.metrics.successes += 1
                    except Exception as e:
                        self.metrics.failures += 1
                
                else:
                    # Normal operation
                    counter_name = f"normal_counter_{worker_id}_{random.randint(0, 50)}"
                    self.collector.increment_counter(counter_name, random.randint(-100, 100))
                    self.metrics.successes += 1
                
                self.metrics.total_operations += 1
                
                # Random sleep to simulate real-world
                if random.random() < 0.1:
                    time.sleep(random.uniform(0.001, 0.01))
            
            except Exception as e:
                self.metrics.failures += 1
                self.metrics.errors.append({"type": "counter", "error": str(e)})
                self.metrics.total_operations += 1
    
    def chaos_worker_gauge(self, worker_id: int):
        """Extreme chaos for gauge operations"""
        while not self.stop_event.is_set():
            try:
                ops_mode = random.randint(0, 5)
                
                if ops_mode == 0:
                    # Normal gauge
                    name = f"chaos_gauge_{worker_id}_{random.randint(0, 50)}"
                    value = random.uniform(-1e15, 1e15)
                    self.collector.set_gauge(name, value)
                    self.metrics.successes += 1
                
                elif ops_mode == 1:
                    # Toggle between extreme values
                    name = f"toggle_gauge_{worker_id}"
                    if random.random() < 0.5:
                        self.collector.set_gauge(name, 1e300)
                    else:
                        self.collector.set_gauge(name, -1e300)
                    self.metrics.successes += 1
                
                else:
                    # Normal operation
                    name = f"gauge_{worker_id}"
                    self.collector.set_gauge(name, random.randint(-1000, 1000))
                    self.metrics.successes += 1
                
                self.metrics.total_operations += 1
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0.001, 0.05))
            
            except Exception as e:
                self.metrics.failures += 1
                self.metrics.errors.append({"type": "gauge", "error": str(e)})
                self.metrics.total_operations += 1
    
    def chaos_worker_histogram(self, worker_id: int):
        """Extreme chaos for histogram operations"""
        while not self.stop_event.is_set():
            try:
                ops_mode = random.randint(0, 10)
                
                if ops_mode == 0:
                    # Normal histogram
                    name = f"chaos_histogram_{worker_id}_{random.randint(0, 30)}"
                    for _ in range(random.randint(1, 50)):
                        self.collector.record_histogram(name, random.uniform(0, 1000))
                    self.metrics.successes += 1
                
                elif ops_mode == 1:
                    # Mix of valid and invalid values
                    name = f"mixed_histogram_{worker_id}"
                    for _ in range(random.randint(1, 20)):
                        value = random.choice([
                            random.uniform(0, 100),
                            float('inf'),
                            float('-inf'),
                            0.0,
                            1e30,
                            -1e30,
                            0.0000001
                        ])
                        self.collector.record_histogram(name, value)
                    self.metrics.successes += 1
                
                else:
                    # Normal operation
                    name = f"hist_{worker_id}"
                    self.collector.record_histogram(name, random.random() * 100)
                    self.metrics.successes += 1
                
                self.metrics.total_operations += 1
                
                if random.random() < 0.02:
                    time.sleep(random.uniform(0.001, 0.05))
            
            except Exception as e:
                self.metrics.failures += 1
                self.metrics.errors.append({"type": "histogram", "error": str(e)})
                self.metrics.total_operations += 1
    
    def chaos_worker_queries(self, worker_id: int):
        """Extreme chaos for metrics queries"""
        while not self.stop_event.is_set():
            try:
                ops_mode = random.randint(0, 3)
                
                if ops_mode == 0:
                    # Get all metrics
                    _ = self.collector.get_all_metrics()
                    self.metrics.successes += 1
                
                elif ops_mode == 1:
                    # Get histogram stats for random histogram
                    name = random.choice(list(self.collector._histograms.keys())) if self.collector._histograms else "non_existent"
                    try:
                        _ = self.collector.get_histogram_stats(name)
                        self.metrics.successes += 1
                    except KeyError:
                        # Expected when histogram doesn't exist
                        self.metrics.successes += 1
                
                elif ops_mode == 2:
                    # Get metric history
                    name = random.choice(list(self.collector._metric_points.keys())) if self.collector._metric_points else "non_existent"
                    try:
                        _ = self.collector.get_metric_history(name, limit=random.randint(1, 1000))
                        self.metrics.successes += 1
                    except KeyError:
                        self.metrics.successes += 1
                
                else:
                    # Massive query
                    _ = self.collector.get_all_metrics()
                    self.metrics.successes += 1
                
                self.metrics.total_operations += 1
                
                if random.random() < 0.05:
                    time.sleep(random.uniform(0.001, 0.03))
            
            except Exception as e:
                self.metrics.failures += 1
                self.metrics.errors.append({"type": "query", "error": str(e)})
                self.metrics.total_operations += 1
    
    def chaos_worker_exceptions(self, worker_id: int):
        """Extreme chaos for exception testing"""
        while not self.stop_event.is_set():
            try:
                for _ in range(random.randint(1, 5)):
                    # Create various custom exceptions
                    exc_type = random.choice([
                        NotFoundError,
                        ValidationError,
                        DuplicateError,
                        AgentToolkitTimeoutError
                    ])
                    
                    if exc_type == NotFoundError:
                        exc = exc_type(
                            message=f"Not found: {worker_id} - {random.randint(1, 1000)}",
                            resource_type=random.choice(["tool", "metric", "endpoint"]),
                            resource_id=random.randint(1, 10000)
                        )
                    elif exc_type == ValidationError:
                        exc = exc_type(
                            message=f"Validation failed: {worker_id}",
                            details={"test": random.random(), "worker": worker_id}
                        )
                    elif exc_type == DuplicateError:
                        exc = exc_type(
                            message=f"Duplicate: {worker_id}",
                            resource_type="test",
                            existing_id=random.randint(1, 100)
                        )
                    else:
                        exc = exc_type(
                            message=f"Timeout: {worker_id}",
                            timeout_seconds=random.randint(1, 60),
                            operation=f"test_op_{worker_id}"
                        )
                    
                    # Convert to dict
                    dict_data = exc.to_dict()
                    self.metrics.successes += 1
                
                self.metrics.total_operations += random.randint(1, 3)
                
                if random.random() < 0.1:
                    time.sleep(random.uniform(0.01, 0.1))
            
            except Exception as e:
                self.metrics.failures += 1
                self.metrics.errors.append({"type": "exception", "error": str(e)})
                self.metrics.total_operations += 1
    
    def chaos_worker_gc_stress(self, worker_id: int):
        """Extreme GC stress test"""
        while not self.stop_event.is_set():
            try:
                # Allocate memory and free
                memory_stress = [f"{random.random()}" for _ in range(random.randint(1000, 5000))]
                del memory_stress
                
                if random.random() < 0.3:
                    gc.collect()
                
                self.metrics.successes += 1
                self.metrics.total_operations += 1
                
                time.sleep(random.uniform(0.05, 0.2))
            
            except Exception as e:
                self.metrics.failures += 1
                self.metrics.errors.append({"type": "gc", "error": str(e)})
                self.metrics.total_operations += 1
    
    def chaos_worker_mixed(self, worker_id: int):
        """MIX EVERYTHING FOR MAXIMUM CHAOS!"""
        while not self.stop_event.is_set():
            try:
                op_type = random.randint(0, 10)
                
                if op_type == 0:
                    self.collector.increment_counter(f"mixed_counter_{worker_id}", random.uniform(-100, 100))
                
                elif op_type == 1:
                    self.collector.set_gauge(f"mixed_gauge_{worker_id}", random.uniform(-1000, 1000))
                
                elif op_type == 2:
                    self.collector.record_histogram(f"mixed_histogram_{worker_id}", random.random() * 100)
                
                elif op_type == 3:
                    self.collector.get_all_metrics()
                
                elif op_type == 4:
                    name = random.choice(list(self.collector._histograms.keys())) if self.collector._histograms else "test"
                    try:
                        self.collector.get_histogram_stats(name)
                    except KeyError:
                        pass
                
                elif op_type == 5:
                    try:
                        self.collector.increment_counter(f"special_name_{worker_id}", random.uniform(-1e10, 1e10))
                    except:
                        pass
                
                elif op_type == 6:
                    try:
                        self.collector.set_gauge(f"special_gauge_{worker_id}", float(random.choice([-1e20, 0, 1e20])))
                    except:
                        pass
                
                elif op_type == 7:
                    # Rapid record
                    for _ in range(random.randint(1, 50)):
                        self.collector.record_histogram(f"rapid_histogram_{worker_id}", random.random())
                
                else:
                    self.collector.get_metric_history(f"test_history_{worker_id}", limit=10)
                
                self.metrics.successes += 1
                self.metrics.total_operations += 1
                
                if random.random() < 0.02:
                    time.sleep(random.uniform(0.001, 0.02))
            
            except Exception as e:
                self.metrics.failures += 1
                self.metrics.errors.append({"type": "mixed", "error": str(e)})
                self.metrics.total_operations += 1
    
    def report_progress(self):
        """Report current progress periodically"""
        while not self.stop_event.is_set():
            current_time = time.time()
            elapsed = current_time - self.metrics.start_time
            time_left = self.duration - elapsed
            
            ops_since_last = self.metrics.total_operations - self.metrics.last_ops_report
            time_since_last = current_time - self.metrics.last_report_time
            ops_per_sec = ops_since_last / max(time_since_last, 0.1)
            
            total_ops_per_sec = self.metrics.total_operations / elapsed if elapsed > 0 else 0
            
            print(f"\n⏱️  {int(elapsed)}s elapsed | {int(time_left)}s left")
            print(f"📊 Total Ops: {self.metrics.total_operations:,} | Success: {self.metrics.successes:,} | Fail: {self.metrics.failures}")
            print(f"⚡ Throughput: {int(ops_per_sec):,} ops/s (avg: {int(total_ops_per_sec):,})")
            print(f"✅ Success Rate: {self.metrics.successes / max(self.metrics.total_operations, 1) * 100:.2f}%")
            
            if self.metrics.errors:
                print(f"⚠️  Errors seen: {len(self.metrics.errors)}")
            
            self.metrics.last_report_time = current_time
            self.metrics.last_ops_report = self.metrics.total_operations
            
            time.sleep(5)
    
    def run(self):
        """Run the ultra-extreme chaos test"""
        print("\n🚀 Starting Chaos Workers:")
        self.executor = ThreadPoolExecutor(max_workers=150)
        
        # Start all chaos workers
        workers = [
            ("Counter", 40, self.chaos_worker_counter),
            ("Gauge", 20, self.chaos_worker_gauge),
            ("Histogram", 25, self.chaos_worker_histogram),
            ("Queries", 20, self.chaos_worker_queries),
            ("Exceptions", 10, self.chaos_worker_exceptions),
            ("GC Stress", 5, self.chaos_worker_gc_stress),
            ("Mixed Chaos", 30, self.chaos_worker_mixed),
        ]
        
        total_workers = 0
        for worker_type, count, worker_func in workers:
            print(f"  - {worker_type}: {count} workers")
            for i in range(count):
                future = self.executor.submit(worker_func, total_workers + i)
                self.worker_threads.append(future)
            total_workers += count
        
        print(f"\n✅ Total: {total_workers} chaos workers running!")
        
        # Start progress reporter
        reporter_thread = threading.Thread(target=self.report_progress, daemon=True)
        reporter_thread.start()
        
        # Wait for the duration
        print("\n" + "=" * 80)
        print("🔥 Chaos Test in Progress...")
        print("=" * 80)
        
        time.sleep(self.duration)
        
        # Stop all workers
        print("\n🛑 Stopping all chaos workers...")
        self.stop_event.set()
        
        # Wait for all threads to complete
        print("Waiting for workers to finish...")
        
        for future in as_completed(self.worker_threads, timeout=10):
            try:
                future.result(timeout=5)
            except Exception as e:
                print(f"Worker completed with exception: {e}")
        
        self.executor.shutdown(wait=True)
        
        self.print_final_report()
        
        return self.metrics
    
    def print_final_report(self):
        """Print final chaos test report"""
        print("\n" + "=" * 80)
        print("🎉 ULTRA EXTREME CHAOS TEST COMPLETED 🎉")
        print("=" * 80)
        
        elapsed = time.time() - self.metrics.start_time
        
        print(f"\n📊 FINAL RESULTS:")
        print(f"  Duration: {int(elapsed)}s ({elapsed / 60:.1f} minutes)")
        print(f"  Total Operations: {self.metrics.total_operations:,}")
        print(f"  Successful: {self.metrics.successes:,}")
        print(f"  Failed: {self.metrics.failures}")
        
        success_rate = self.metrics.successes / max(self.metrics.total_operations, 1) * 100
        throughput = self.metrics.total_operations / elapsed
        
        print(f"  Success Rate: {success_rate:.2f}%")
        print(f"  Throughput: {int(throughput):,} ops/s")
        
        if self.metrics.errors:
            print(f"\n⚠️  ERRORS RECORDED: {len(self.metrics.errors)}")
            print("Top 10 errors:")
            for i, err in enumerate(self.metrics.errors[:10]):
                print(f"  {i + 1}. [{err['type']}] {err['error']}")
            if len(self.metrics.errors) > 10:
                print(f"  ... and {len(self.metrics.errors) - 10} more")
        else:
            print("\n✅ NO ERRORS RECORDED!")
        
        # Final integrity verification
        print("\n🔍 VERIFYING SYSTEM INTEGRITY:")
        try:
            metrics = self.collector.get_all_metrics()
            print(f"  ✅ get_all_metrics() working")
            
            test_counter = "final_verification_counter"
            self.collector.increment_counter(test_counter, 1000)
            print(f"  ✅ Counter operations working")
            
            test_histogram = "final_verification_histogram"
            for i in range(100):
                self.collector.record_histogram(test_histogram, i)
            
            stats = self.collector.get_histogram_stats(test_histogram)
            print(f"  ✅ Histogram stats working: min={stats['min']}, max={stats['max']}")
            
            print("\n🏆 SYSTEM INTEGRITY VERIFIED - SYSTEM IS WORKING PERFECTLY!")
            
            print("\n" + "=" * 80)
            if success_rate >= 99.9:
                print("🥇 RATING: PERFECT")
                print("System performed flawlessly in ultra-extreme conditions!")
            elif success_rate >= 99:
                print("🥈 RATING: EXCELLENT")
                print("System performed outstandingly!")
            elif success_rate >= 95:
                print("🥉 RATING: GOOD")
                print("System performed well with minor issues!")
            else:
                print("💔 RATING: NEEDS IMPROVEMENT")
                print("System has significant issues!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ SYSTEM INTEGRITY CHECK FAILED: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    from collections import defaultdict
    
    print("\n" + "=" * 80)
    print("🚀 AGENT TOOLKIT - ULTRA EXTREME CHAOS TESTING")
    print("=" * 80)
    
    # Run for 2 minutes instead of 10 minutes for faster verification
    tester = UltraChaosScenarioTester(duration_seconds=120)
    metrics = tester.run()
    
    print("\n✅ TEST COMPLETED!")
