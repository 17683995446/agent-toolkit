"""
EXTREME Chaos Engineering Testing - The Ultimate Stress Test
This test simulates the most chaotic real-world scenarios possible!
"""

import time
import random
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from datetime import datetime
import gc

from agent_toolkit.shared.metrics_api import MetricsCollector
from agent_toolkit.shared.health_check import HealthCheckRegistry
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError, ValidationError, DuplicateError, AgentToolkitTimeoutError
)


class ExtremeChaosMetrics:
    """Metrics for the extreme chaos test"""
    def __init__(self):
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.warnings = 0
        self.errors: List[Dict] = []
        self.start_time = time.time()
        self.thread_states: Dict[int, int] = {}


class ExtremeChaosEngine:
    """The ultimate chaos engine!"""
    
    def __init__(self, test_duration: int = 120):
        self.test_duration = test_duration
        self.metrics = ExtremeChaosMetrics()
        self.collector = MetricsCollector()
        self.health_registry = HealthCheckRegistry()
        self.running = True
        self.stop_event = threading.Event()
        print("🔥🔥🔥 EXTREME CHAOS ENGINE INITIALIZED 🔥🔥🔥")
    
    def chaos_counter_worker(self, thread_id: int, chaos_level: int):
        """Chaotic counter operations with extreme values"""
        try:
            self.metrics.thread_states[thread_id] = 1
            
            for _ in range(random.randint(100, 1000)):
                if self.stop_event.is_set():
                    break
                
                try:
                    # Extreme chaos: random operations with crazy values
                    value = random.choice([
                        random.uniform(-1e30, 1e30),
                        random.randint(-10000, 10000),
                        1.0,
                        -1.0,
                        0.0,
                        float('inf'),
                        float('-inf'),
                        1e-30,
                        1e30,
                    ])
                    
                    name = f"chaos_counter_{thread_id}_{random.randint(0, 100)}"
                    
                    # Randomly add weird characters
                    if random.random() < 0.1:
                        name += "_!@#$%^&*()"
                    elif random.random() < 0.1:
                        name += "_中文测试"
                    elif random.random() < 0.1:
                        name += "_\t\n\r"
                    
                    self.collector.increment_counter(name, value)
                    self.metrics.successful_operations += 1
                    self.metrics.total_operations += 1
                    
                except Exception as e:
                    self.metrics.failed_operations += 1
                    self.metrics.total_operations += 1
                    self.metrics.errors.append({
                        "type": "counter",
                        "error": str(e),
                        "thread": thread_id
                    })
                    
        finally:
            self.metrics.thread_states[thread_id] = 0
    
    def chaos_gauge_worker(self, thread_id: int, chaos_level: int):
        """Chaotic gauge operations"""
        try:
            self.metrics.thread_states[thread_id + 100] = 1
            
            for _ in range(random.randint(100, 1000)):
                if self.stop_event.is_set():
                    break
                
                try:
                    value = random.choice([
                        random.uniform(-1e30, 1e30),
                        0.0,
                        float('inf'),
                        float('-inf'),
                        random.randint(-1000, 1000),
                    ])
                    
                    name = f"chaos_gauge_{thread_id}_{random.randint(0, 50)}"
                    self.collector.set_gauge(name, value)
                    self.metrics.successful_operations += 1
                    self.metrics.total_operations += 1
                    
                except Exception as e:
                    self.metrics.failed_operations += 1
                    self.metrics.total_operations += 1
                    self.metrics.errors.append({
                        "type": "gauge",
                        "error": str(e),
                        "thread": thread_id
                    })
        finally:
            self.metrics.thread_states[thread_id + 100] = 0
    
    def chaos_histogram_worker(self, thread_id: int, chaos_level: int):
        """Chaotic histogram operations"""
        try:
            self.metrics.thread_states[thread_id + 200] = 1
            
            for _ in range(random.randint(100, 1000)):
                if self.stop_event.is_set():
                    break
                
                try:
                    for __ in range(random.randint(1, 100)):
                        value = random.choice([
                            random.uniform(0, 1000),
                            0.0,
                            1e30,
                            float('inf'),
                            float('-inf'),
                        ])
                        
                        name = f"chaos_histogram_{thread_id}_{random.randint(0, 30)}"
                        self.collector.record_histogram(name, value)
                        self.metrics.successful_operations += 1
                        self.metrics.total_operations += 1
                        
                except Exception as e:
                    self.metrics.failed_operations += 1
                    self.metrics.total_operations += 1
                    self.metrics.errors.append({
                        "type": "histogram",
                        "error": str(e),
                        "thread": thread_id
                    })
        finally:
            self.metrics.thread_states[thread_id + 200] = 0
    
    def chaos_metric_history_worker(self, thread_id: int, chaos_level: int):
        """Chaotic metric history queries"""
        try:
            self.metrics.thread_states[thread_id + 300] = 1
            
            for _ in range(random.randint(50, 200)):
                if self.stop_event.is_set():
                    break
                
                try:
                    name = f"chaos_counter_{random.randint(0, 1000)}"
                    limit = random.randint(1, 1000)
                    
                    history = self.collector.get_metric_history(name, limit)
                    self.metrics.successful_operations += 1
                    self.metrics.total_operations += 1
                    
                except Exception as e:
                    self.metrics.failed_operations += 1
                    self.metrics.total_operations += 1
                    self.metrics.errors.append({
                        "type": "history",
                        "error": str(e),
                        "thread": thread_id
                    })
        finally:
            self.metrics.thread_states[thread_id + 300] = 0
    
    def chaos_stats_worker(self, thread_id: int, chaos_level: int):
        """Chaotic statistics queries"""
        try:
            self.metrics.thread_states[thread_id + 400] = 1
            
            for _ in range(random.randint(50, 200)):
                if self.stop_event.is_set():
                    break
                
                try:
                    name = f"chaos_histogram_{random.randint(0, 1000)}"
                    stats = self.collector.get_histogram_stats(name)
                    self.metrics.successful_operations += 1
                    self.metrics.total_operations += 1
                    
                except Exception as e:
                    self.metrics.failed_operations += 1
                    self.metrics.total_operations += 1
                    self.metrics.errors.append({
                        "type": "stats",
                        "error": str(e),
                        "thread": thread_id
                    })
        finally:
            self.metrics.thread_states[thread_id + 400] = 0
    
    def chaos_exception_worker(self, thread_id: int, chaos_level: int):
        """Chaotic exception testing"""
        try:
            self.metrics.thread_states[thread_id + 500] = 1
            
            for _ in range(random.randint(20, 100)):
                if self.stop_event.is_set():
                    break
                
                try:
                    # Randomly trigger various custom exceptions
                    exception_type = random.choice([
                        NotFoundError,
                        ValidationError,
                        DuplicateError,
                        AgentToolkitTimeoutError,
                    ])
                    
                    if exception_type == NotFoundError:
                        exc = exception_type(
                            message=f"Chaos not found: {thread_id}",
                            resource_type="test",
                            resource_id=random.randint(1, 1000)
                        )
                    elif exception_type == ValidationError:
                        exc = exception_type(
                            message=f"Chaos validation: {thread_id}",
                            details={"field": f"chaos_field_{thread_id}", "value": random.random()}
                        )
                    elif exception_type == DuplicateError:
                        exc = exception_type(
                            message=f"Chaos duplicate: {thread_id}",
                            resource_type="test",
                            existing_id=random.randint(1, 1000)
                        )
                    elif exception_type == AgentToolkitTimeoutError:
                        exc = exception_type(
                            message=f"Chaos timeout: {thread_id}",
                            timeout_seconds=random.randint(1, 100),
                            operation=f"chaos_operation_{thread_id}"
                        )
                    
                    # Convert to dict to simulate serialization
                    dict_data = exc.to_dict()
                    self.metrics.successful_operations += 1
                    self.metrics.total_operations += 1
                    
                except Exception as e:
                    self.metrics.failed_operations += 1
                    self.metrics.total_operations += 1
                    self.metrics.errors.append({
                        "type": "exception",
                        "error": str(e),
                        "thread": thread_id
                    })
        finally:
            self.metrics.thread_states[thread_id + 500] = 0
    
    def chaos_get_all_worker(self, thread_id: int, chaos_level: int):
        """Chaotic get all metrics"""
        try:
            self.metrics.thread_states[thread_id + 600] = 1
            
            for _ in range(random.randint(10, 50)):
                if self.stop_event.is_set():
                    break
                
                try:
                    all_metrics = self.collector.get_all_metrics()
                    self.metrics.successful_operations += 1
                    self.metrics.total_operations += 1
                    
                except Exception as e:
                    self.metrics.failed_operations += 1
                    self.metrics.total_operations += 1
                    self.metrics.errors.append({
                        "type": "get_all",
                        "error": str(e),
                        "thread": thread_id
                    })
        finally:
            self.metrics.thread_states[thread_id + 600] = 0
    
    def chaos_gc_worker(self, thread_id: int, chaos_level: int):
        """Chaotic garbage collection stress"""
        try:
            self.metrics.thread_states[thread_id + 700] = 1
            
            for _ in range(random.randint(5, 20)):
                if self.stop_event.is_set():
                    break
                
                try:
                    # Random GC stress
                    gc.collect()
                    self.metrics.successful_operations += 1
                    self.metrics.total_operations += 1
                    time.sleep(random.uniform(0.1, 0.5))
                    
                except Exception as e:
                    self.metrics.failed_operations += 1
                    self.metrics.total_operations += 1
                    self.metrics.errors.append({
                        "type": "gc",
                        "error": str(e),
                        "thread": thread_id
                    })
        finally:
            self.metrics.thread_states[thread_id + 700] = 0
    
    def chaos_mixed_worker(self, thread_id: int, chaos_level: int):
        """Mix everything together for maximum chaos!"""
        try:
            self.metrics.thread_states[thread_id + 800] = 1
            
            for _ in range(random.randint(50, 300)):
                if self.stop_event.is_set():
                    break
                
                # 90% chance to do some operation, 10% to sleep
                if random.random() < 0.9:
                    operation_type = random.randint(0, 4)
                    
                    if operation_type == 0:
                        try:
                            value = random.uniform(-1000, 1000)
                            name = f"mixed_counter_{thread_id}"
                            self.collector.increment_counter(name, value)
                            self.metrics.successful_operations += 1
                            self.metrics.total_operations += 1
                        except Exception as e:
                            self.metrics.failed_operations += 1
                            self.metrics.total_operations += 1
                            
                    elif operation_type == 1:
                        try:
                            value = random.uniform(-1000, 1000)
                            name = f"mixed_gauge_{thread_id}"
                            self.collector.set_gauge(name, value)
                            self.metrics.successful_operations += 1
                            self.metrics.total_operations += 1
                        except Exception as e:
                            self.metrics.failed_operations += 1
                            self.metrics.total_operations += 1
                            
                    elif operation_type == 2:
                        try:
                            value = random.uniform(0, 100)
                            name = f"mixed_histogram_{thread_id}"
                            self.collector.record_histogram(name, value)
                            self.metrics.successful_operations += 1
                            self.metrics.total_operations += 1
                        except Exception as e:
                            self.metrics.failed_operations += 1
                            self.metrics.total_operations += 1
                            
                    elif operation_type == 3:
                        try:
                            stats = self.collector.get_histogram_stats(f"mixed_histogram_{thread_id}")
                            self.metrics.successful_operations += 1
                            self.metrics.total_operations += 1
                        except Exception as e:
                            self.metrics.failed_operations += 1
                            self.metrics.total_operations += 1
                            
                    elif operation_type == 4:
                        try:
                            all_metrics = self.collector.get_all_metrics()
                            self.metrics.successful_operations += 1
                            self.metrics.total_operations += 1
                        except Exception as e:
                            self.metrics.failed_operations += 1
                            self.metrics.total_operations += 1
                else:
                    time.sleep(random.uniform(0.001, 0.01))
                    
        finally:
            self.metrics.thread_states[thread_id + 800] = 0
    
    def run_extreme_chaos_test(self):
        """Run the extreme chaos test for the specified duration!"""
        print("\n" + "=" * 80)
        print("🔥🔥🔥 EXTREME CHAOS TEST STARTING 🔥🔥🔥")
        print("=" * 80)
        
        print(f"\n📋 TEST CONFIGURATION:")
        print(f"   Duration: {self.test_duration} seconds")
        print(f"   Thread Count: 100 threads")
        print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n")
        
        # Start time
        test_start = time.time()
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            
            # Counter workers (20)
            for i in range(20):
                futures.append(executor.submit(self.chaos_counter_worker, i, 5))
            
            # Gauge workers (15)
            for i in range(15):
                futures.append(executor.submit(self.chaos_gauge_worker, i, 5))
            
            # Histogram workers (15)
            for i in range(15):
                futures.append(executor.submit(self.chaos_histogram_worker, i, 5))
            
            # History workers (10)
            for i in range(10):
                futures.append(executor.submit(self.chaos_metric_history_worker, i, 5))
            
            # Stats workers (10)
            for i in range(10):
                futures.append(executor.submit(self.chaos_stats_worker, i, 5))
            
            # Exception workers (10)
            for i in range(10):
                futures.append(executor.submit(self.chaos_exception_worker, i, 5))
            
            # Get all workers (10)
            for i in range(10):
                futures.append(executor.submit(self.chaos_get_all_worker, i, 5))
            
            # GC workers (5)
            for i in range(5):
                futures.append(executor.submit(self.chaos_gc_worker, i, 5))
            
            # Mixed workers (5)
            for i in range(5):
                futures.append(executor.submit(self.chaos_mixed_worker, i, 5))
            
            # Wait for the test duration, then signal stop
            elapsed = time.time() - test_start
            while elapsed < self.test_duration:
                time.sleep(1)
                elapsed = time.time() - test_start
                
                # Print progress every 5 seconds
                if int(elapsed) % 5 == 0 and elapsed > 0:
                    self._print_progress(elapsed, test_start)
            
            # Stop all workers
            self.stop_event.set()
            print("\n🛑 Stopping all workers...")
            
            # Wait for all futures to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"⚠️ Worker exception: {e}")
        
        # Final results
        self._print_final_results(test_start)
        return self.metrics
    
    def _print_progress(self, elapsed: float, start_time: float):
        """Print progress update"""
        ops_per_sec = self.metrics.total_operations / elapsed if elapsed > 0 else 0
        success_rate = self.metrics.successful_operations / self.metrics.total_operations * 100 if self.metrics.total_operations > 0 else 100
        
        print(f"⏱️  Progress: {int(elapsed)}s/{self.test_duration}s | "
              f"Ops: {self.metrics.total_operations:,} | "
              f"Throughput: {int(ops_per_sec):,} ops/s | "
              f"Success: {success_rate:.2f}% | "
              f"Errors: {self.metrics.failed_operations}")
    
    def _print_final_results(self, start_time: float):
        """Print final test results"""
        total_elapsed = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("🎉 EXTREME CHAOS TEST COMPLETED 🎉")
        print("=" * 80)
        
        print("\n📊 FINAL RESULTS:")
        print(f"   Duration: {total_elapsed:.2f} seconds")
        print(f"   Total Operations: {self.metrics.total_operations:,}")
        print(f"   Successful: {self.metrics.successful_operations:,}")
        print(f"   Failed: {self.metrics.failed_operations:,}")
        
        success_rate = self.metrics.successful_operations / self.metrics.total_operations * 100 if self.metrics.total_operations > 0 else 100
        ops_per_sec = self.metrics.total_operations / total_elapsed
        
        print(f"   Success Rate: {success_rate:.2f}%")
        print(f"   Throughput: {int(ops_per_sec):,} ops/s")
        
        if self.metrics.errors:
            print(f"\n❌ ERRORS FOUND: {len(self.metrics.errors)}")
            for error in self.metrics.errors[:10]:  # Print first 10 errors
                print(f"   - [{error['type']}] {error['error']} (Thread {error['thread']})")
            
            if len(self.metrics.errors) > 10:
                print(f"   ... and {len(self.metrics.errors) - 10} more")
        else:
            print("\n✅ NO ERRORS FOUND! 100% success!")
        
        # Verify system is still working
        print("\n🔍 VERIFYING SYSTEM INTEGRITY:")
        
        try:
            # Check we can still get metrics
            all_metrics = self.collector.get_all_metrics()
            print(f"   ✅ Can retrieve all metrics")
            
            # Check counter operations still work
            test_name = "final_verification_counter"
            self.collector.increment_counter(test_name, 100)
            counter_value = self.collector._counters[test_name]
            print(f"   ✅ Counter operations work: {test_name} = {counter_value}")
            
            print("\n🏆 SYSTEM INTEGRITY VERIFIED!")
            return True
            
        except Exception as e:
            print(f"\n❌ SYSTEM INTEGRITY CHECK FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Run the extreme chaos test!"""
    print("🚀🚀🚀 AGENT TOOLKIT - EXTREME CHAOS ENGINEERING TEST 🚀🚀🚀")
    print("=" * 80)
    print("\n📋 OVERVIEW:")
    print("   This test will simulate extreme real-world chaos scenarios.")
    print("   Multiple threads will perform chaotic operations for 120 seconds.")
    
    # Run the test
    engine = ExtremeChaosEngine(test_duration=30)
    metrics = engine.run_extreme_chaos_test()
    
    # Generate report
    print("\n" + "=" * 80)
    print("📄 FINAL REPORT:")
    print("=" * 80)
    
    success_rate = metrics.successful_operations / metrics.total_operations * 100 if metrics.total_operations > 0 else 100
    
    if success_rate >= 99.9:
        print("\n🏆 RATING: EXCELLENT")
        print("   The system performed flawlessly under extreme chaos!")
    elif success_rate >= 95:
        print("\n👍 RATING: GOOD")
        print("   The system performed well, with minor issues.")
    elif success_rate >= 80:
        print("\n⚠️ RATING: FAIR")
        print("   The system had significant issues under stress.")
    else:
        print("\n❌ RATING: POOR")
        print("   The system needs major improvements.")
    
    print(f"\n💾 TOTAL OPERATIONS: {metrics.total_operations:,}")
    print(f"✅ SUCCESS RATE: {success_rate:.2f}%")
    print(f"❌ ERROR COUNT: {metrics.failed_operations}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
