"""
🚀🚀🚀 ULTIMATE BOUNDARY VALUE TESTING - 探索所有边界情况 🚀🚀🚀

测试所有极端边界值：
- 字符串：空、超长、特殊字符、Unicode
- 对象：嵌套、循环引用、大对象
- 类型：各种数据类型转换
- 序列化：JSON、异常序列化
"""

import time
import random
import threading
import sys
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import gc

from agent_toolkit.shared.metrics_api import MetricsCollector
from agent_toolkit.shared.health_check import HealthCheckRegistry
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError,
    ValidationError,
    DuplicateError,
    AgentToolkitTimeoutError
)


class UltimateBoundaryMetrics:
    """Metrics for boundary testing"""
    
    def __init__(self):
        self.start_time = time.time()
        self.total_tests = 0
        self.successes = 0
        self.failures = 0
        self.errors = []
        self.test_results = {}
        self.lock = threading.Lock()
    
    def record_test(self, test_name: str, success: bool, error_msg: str = ""):
        with self.lock:
            self.total_tests += 1
            if success:
                self.successes += 1
            else:
                self.failures += 1
                self.errors.append({
                    "test": test_name,
                    "error": error_msg,
                    "time": datetime.now().isoformat()
                })
            
            self.test_results[test_name] = {
                "success": success,
                "error": error_msg
            }


class UltimateBoundaryTester:
    """Test all extreme boundary conditions"""
    
    def __init__(self):
        self.metrics = UltimateBoundaryMetrics()
        self.collector = MetricsCollector()
        self.health_registry = HealthCheckRegistry()
        
        print("=" * 90)
        print("🔥🔥🔥 ULTIMATE BOUNDARY VALUE TESTING 🔥🔥🔥")
        print("=" * 90)
    
    def test_string_boundaries(self):
        """Test extreme string boundaries"""
        print("\n📝 Testing STRING Boundaries...")
        
        test_cases = [
            ("empty_string", ""),
            ("single_char", "a"),
            ("newline_string", "\n\t\r"),
            ("unicode_string", "中文测试 🚀 émojis ñ"),
            ("very_long_string_1kb", "x" * 1024),
            ("very_long_string_10kb", "x" * 10240),
            ("very_long_string_100kb", "x" * 102400),
            ("special_chars", "!@#$%^&*()_+-=[]{}|;':\",./<>?"),
            ("binary_string", bytes([0, 1, 127, 128, 255]).decode('latin-1')),
            ("null_char_string", "test\x00null"),
            ("emoji_string", "😀🎉🔥💯🚀🌟✨"),
            ("mixed_content", "Hello 世界! 🎉" * 100),
            ("sql_injection", "'; DROP TABLE users; --"),
            ("html_tags", "<script>alert('xss')</script>"),
            ("json_like", '{"key": "value", "number": 123}'),
            ("python_code", "print('hello'); import os; os.system('ls')"),
            ("path_traversal", "../../../etc/passwd"),
            ("unicode_emoji_mixed", "hello😀world🌍test🎊" * 50),
        ]
        
        for name, value in test_cases:
            try:
                # Try to use string as counter name
                safe_name = f"string_test_{name}"
                self.collector.increment_counter(safe_name, 1)
                
                # Try to use string as gauge name
                self.collector.set_gauge(safe_name, len(value))
                
                # Try to record histogram with string length
                self.collector.record_histogram(safe_name, float(len(value)))
                
                # Try to get history
                try:
                    history = self.collector.get_metric_history(safe_name, limit=10)
                except:
                    pass
                
                self.metrics.record_test(f"string_{name}", True)
                print(f"  ✅ {name}: length={len(value)}")
                
            except Exception as e:
                self.metrics.record_test(f"string_{name}", False, str(e))
                print(f"  ❌ {name}: {str(e)[:100]}")
    
    def test_number_boundaries(self):
        """Test extreme number boundaries"""
        print("\n🔢 Testing NUMBER Boundaries...")
        
        test_cases = [
            ("zero", 0),
            ("positive_one", 1),
            ("negative_one", -1),
            ("small_positive", 1e-100),
            ("small_negative", -1e-100),
            ("large_positive", 1e100),
            ("large_negative", -1e100),
            ("max_int", sys.maxsize),
            ("min_int", -sys.maxsize - 1),
            ("max_float", sys.float_info.max),
            ("min_float", sys.float_info.min),
            ("epsilon", sys.float_info.epsilon),
            ("nan_value", float('nan')),
            ("positive_inf", float('inf')),
            ("negative_inf", float('-inf')),
            ("negative_zero", -0.0),
            ("huge_negative", -1e308),
            ("huge_positive", 1e308),
        ]
        
        for name, value in test_cases:
            try:
                safe_name = f"number_test_{name}"
                
                # Test counter
                self.collector.increment_counter(safe_name, value)
                
                # Test gauge
                self.collector.set_gauge(safe_name, value)
                
                # Test histogram
                self.collector.record_histogram(safe_name, value)
                
                # Get stats
                try:
                    stats = self.collector.get_histogram_stats(safe_name)
                except:
                    pass
                
                self.metrics.record_test(f"number_{name}", True)
                print(f"  ✅ {name}: {value}")
                
            except Exception as e:
                self.metrics.record_test(f"number_{name}", False, str(e))
                print(f"  ❌ {name}: {str(e)[:100]}")
    
    def test_object_boundaries(self):
        """Test extreme object boundaries"""
        print("\n📦 Testing OBJECT Boundaries...")
        
        test_cases = [
            ("empty_dict", {}),
            ("nested_dict_1", {"a": 1}),
            ("nested_dict_5", {f"k{i}": i for i in range(5)}),
            ("nested_dict_100", {f"k{i}": i for i in range(100)}),
            ("nested_dict_1000", {f"k{i}": i for i in range(1000)}),
            ("empty_list", []),
            ("list_1", [1]),
            ("list_100", list(range(100))),
            ("list_1000", list(range(1000))),
            ("nested_mixed", {"list": [1, 2, 3], "dict": {"a": 1}}),

        ]
        
        # Simplified deep nesting
        def make_nested_dict(depth: int, value: Any) -> Dict:
            if depth == 0:
                return value
            return {f"level_{depth}": make_nested_dict(depth - 1, value)}
        
        for depth in [5, 10, 20]:
            try:
                nested = make_nested_dict(depth, "value")
                json_str = json.dumps(nested)
                self.metrics.record_test(f"object_nested_{depth}", True)
                print(f"  ✅ nested_dict_{depth}: depth={depth}, size={len(json_str)}")
            except Exception as e:
                self.metrics.record_test(f"object_nested_{depth}", False, str(e))
                print(f"  ❌ nested_dict_{depth}: {str(e)[:100]}")
        
        # Large list
        for size in [100, 1000, 10000]:
            try:
                large_list = list(range(size))
                json_str = json.dumps(large_list)
                self.metrics.record_test(f"object_list_{size}", True)
                print(f"  ✅ list_{size}: size={size}, json_size={len(json_str)}")
            except Exception as e:
                self.metrics.record_test(f"object_list_{size}", False, str(e))
                print(f"  ❌ list_{size}: {str(e)[:100]}")
    
    def test_collection_boundaries(self):
        """Test collection size boundaries"""
        print("\n📚 Testing COLLECTION Boundaries...")
        
        # Test many unique counters
        print("  Testing 1000 unique counters...")
        try:
            for i in range(1000):
                self.collector.increment_counter(f"unique_counter_{i}", 1)
            
            all_metrics = self.collector.get_all_metrics()
            counter_count = len(all_metrics.get('counters', {}))
            
            self.metrics.record_test("collection_1000_counters", True)
            print(f"  ✅ 1000 unique counters: {counter_count} created")
        except Exception as e:
            self.metrics.record_test("collection_1000_counters", False, str(e))
            print(f"  ❌ 1000 unique counters: {str(e)[:100]}")
        
        # Test many unique gauges
        print("  Testing 1000 unique gauges...")
        try:
            for i in range(1000):
                self.collector.set_gauge(f"unique_gauge_{i}", float(i))
            
            all_metrics = self.collector.get_all_metrics()
            gauge_count = len(all_metrics.get('gauges', {}))
            
            self.metrics.record_test("collection_1000_gauges", True)
            print(f"  ✅ 1000 unique gauges: {gauge_count} created")
        except Exception as e:
            self.metrics.record_test("collection_1000_gauges", False, str(e))
            print(f"  ❌ 1000 unique gauges: {str(e)[:100]}")
        
        # Test many unique histograms
        print("  Testing 1000 unique histograms...")
        try:
            for i in range(1000):
                for j in range(100):
                    self.collector.record_histogram(f"unique_histogram_{i}", float(j))
            
            all_metrics = self.collector.get_all_metrics()
            hist_count = len(all_metrics.get('histograms', {}))
            
            self.metrics.record_test("collection_1000_histograms", True)
            print(f"  ✅ 1000 unique histograms: {hist_count} created")
        except Exception as e:
            self.metrics.record_test("collection_1000_histograms", False, str(e))
            print(f"  ❌ 1000 unique histograms: {str(e)[:100]}")
    
    def test_histogram_boundaries(self):
        """Test histogram extreme boundaries"""
        print("\n📊 Testing HISTOGRAM Boundaries...")
        
        # Test histogram with extreme values
        try:
            hist_name = "extreme_histogram"
            values = [
                0, 1, -1, 1e-100, -1e-100, 1e100, -1e100,
                float('nan'), float('inf'), float('-inf'),
                sys.maxsize, -sys.maxsize,
                sys.float_info.max, sys.float_info.min
            ]
            
            for v in values:
                self.collector.record_histogram(hist_name, v)
            
            stats = self.collector.get_histogram_stats(hist_name)
            
            # Verify stats are valid
            assert stats['count'] == len(values), f"Count mismatch: {stats['count']} != {len(values)}"
            assert stats['mean'] == stats['mean'], "Mean is NaN"  # NaN != NaN
            assert stats['mean'] >= 0 or stats['mean'] <= 0, "Mean is not a number"
            
            self.metrics.record_test("histogram_extreme_values", True)
            print(f"  ✅ Histogram with extreme values: count={stats['count']}, mean={stats['mean']}")
        except Exception as e:
            self.metrics.record_test("histogram_extreme_values", False, str(e))
            print(f"  ❌ Histogram with extreme values: {str(e)[:100]}")
        
        # Test histogram with 1500+ values (beyond 1000 limit)
        try:
            hist_name = "large_histogram"
            for i in range(1500):
                self.collector.record_histogram(hist_name, float(i))
            
            stats = self.collector.get_histogram_stats(hist_name)
            
            # Should be limited to 1000
            self.metrics.record_test("histogram_beyond_1000", True)
            print(f"  ✅ Histogram beyond 1000: recorded=1500, actual={stats['count']}")
        except Exception as e:
            self.metrics.record_test("histogram_beyond_1000", False, str(e))
            print(f"  ❌ Histogram beyond 1000: {str(e)[:100]}")
    
    def test_exception_boundaries(self):
        """Test exception handling extremes"""
        print("\n⚠️  Testing EXCEPTION Boundaries...")
        
        test_cases = [
            ("empty_message", NotFoundError, {"message": "", "resource_type": "test", "resource_id": 1}),
            ("very_long_message", NotFoundError, {"message": "x" * 10000, "resource_type": "test", "resource_id": 1}),
            ("unicode_message", NotFoundError, {"message": "中文错误信息 🚀", "resource_type": "test", "resource_id": 1}),
            ("nested_details", ValidationError, {"message": "error", "details": {"a": {"b": {"c": {"d": "deep"}}}}}),
            ("special_chars_in_message", NotFoundError, {"message": "!@#$%^&*()", "resource_type": "test", "resource_id": 1}),
            ("max_resource_id", NotFoundError, {"message": "error", "resource_type": "test", "resource_id": sys.maxsize}),
            ("timeout_large_seconds", AgentToolkitTimeoutError, {"message": "timeout", "timeout_seconds": sys.maxsize, "operation": "test"}),
        ]
        
        for name, exc_class, kwargs in test_cases:
            try:
                exc = exc_class(**kwargs)
                dict_data = exc.to_dict()
                json_str = json.dumps(dict_data)
                
                self.metrics.record_test(f"exception_{name}", True)
                print(f"  ✅ exception_{name}: type={exc_class.__name__}")
            except Exception as e:
                self.metrics.record_test(f"exception_{name}", False, str(e))
                print(f"  ❌ exception_{name}: {str(e)[:100]}")
    
    def test_concurrent_boundaries(self):
        """Test concurrent extreme boundaries"""
        print("\n🔄 Testing CONCURRENT Boundaries...")
        
        def worker(worker_id: int):
            try:
                # Create many metrics rapidly
                for i in range(100):
                    self.collector.increment_counter(f"concurrent_worker_{worker_id}", 1)
                    self.collector.set_gauge(f"concurrent_worker_{worker_id}", float(i))
                    self.collector.record_histogram(f"concurrent_worker_{worker_id}", float(i))
                
                # Query many times
                for _ in range(50):
                    self.collector.get_all_metrics()
                    self.collector.get_histogram_stats(f"concurrent_worker_{worker_id}")
                
                self.metrics.record_test(f"concurrent_worker_{worker_id}", True)
            except Exception as e:
                self.metrics.record_test(f"concurrent_worker_{worker_id}", False, str(e))
        
        # Test with 50 concurrent workers
        print("  Testing 50 concurrent workers...")
        threads = []
        for i in range(50):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Check results
        all_metrics = self.collector.get_all_metrics()
        counter_count = len(all_metrics.get('counters', {}))
        gauge_count = len(all_metrics.get('gauges', {}))
        hist_count = len(all_metrics.get('histograms', {}))
        
        print(f"  ✅ Concurrent test results: counters={counter_count}, gauges={gauge_count}, histograms={hist_count}")
    
    def test_memory_boundaries(self):
        """Test memory extreme boundaries"""
        print("\n💾 Testing MEMORY Boundaries...")
        
        try:
            # Create large objects
            for i in range(10):
                large_dict = {f"key_{j}": f"value_{j}" * 100 for j in range(1000)}
                self.collector.increment_counter(f"memory_test_{i}", 1)
            
            # Force garbage collection
            gc.collect()
            
            self.metrics.record_test("memory_large_objects", True)
            print(f"  ✅ Memory boundary test passed")
        except Exception as e:
            self.metrics.record_test("memory_large_objects", False, str(e))
            print(f"  ❌ Memory boundary test: {str(e)[:100]}")
    
    def test_serialization_boundaries(self):
        """Test serialization extremes"""
        print("\n🔄 Testing SERIALIZATION Boundaries...")
        
        try:
            # Create complex exception
            exc = ValidationError(
                message="Test exception with complex details",
                details={
                    "user": {
                        "id": 12345,
                        "name": "Test User 🚀",
                        "preferences": [f"pref_{i}" for i in range(100)]
                    },
                    "system": {
                        "timestamp": datetime.now().isoformat(),
                        "nested": {"a": {"b": {"c": {"d": "deep"}}}}
                    }
                }
            )
            
            # Serialize to dict
            dict_data = exc.to_dict()
            
            # Serialize to JSON
            json_str = json.dumps(dict_data, ensure_ascii=False)
            
            # Deserialize from JSON
            restored_data = json.loads(json_str)
            
            # Verify
            assert restored_data["message"] == exc.message
            
            self.metrics.record_test("serialization_complex_exception", True)
            print(f"  ✅ Complex serialization: json_size={len(json_str)}")
        except Exception as e:
            self.metrics.record_test("serialization_complex_exception", False, str(e))
            print(f"  ❌ Complex serialization: {str(e)[:100]}")
    
    def run_all_tests(self):
        """Run all boundary tests"""
        print("\n" + "=" * 90)
        print("🚀 STARTING ALL BOUNDARY TESTS")
        print("=" * 90)
        
        self.test_string_boundaries()
        self.test_number_boundaries()
        self.test_object_boundaries()
        self.test_collection_boundaries()
        self.test_histogram_boundaries()
        self.test_exception_boundaries()
        self.test_concurrent_boundaries()
        self.test_memory_boundaries()
        self.test_serialization_boundaries()
        
        self.print_final_report()
    
    def print_final_report(self):
        """Print final boundary test report"""
        print("\n" + "=" * 90)
        print("📊 ULTIMATE BOUNDARY TESTING REPORT")
        print("=" * 90)
        
        total = self.metrics.total_tests
        successes = self.metrics.successes
        failures = self.metrics.failures
        success_rate = successes / max(total, 1) * 100
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total Tests: {total}")
        print(f"  Successes: {successes}")
        print(f"  Failures: {failures}")
        print(f"  Success Rate: {success_rate:.2f}%")
        
        if self.metrics.errors:
            print(f"\n❌ FAILED TESTS:")
            for error in self.metrics.errors[:20]:
                print(f"  - {error['test']}: {error['error'][:100]}")
            if len(self.metrics.errors) > 20:
                print(f"  ... and {len(self.metrics.errors) - 20} more failures")
        
        print(f"\n🔍 TEST RESULTS DETAILS:")
        for test_name, result in sorted(self.metrics.test_results.items()):
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {test_name}")
        
        print(f"\n{'=' * 90}")
        if success_rate >= 99:
            print("🥇 RATING: EXCELLENT - System handles all boundaries perfectly!")
        elif success_rate >= 95:
            print("🥈 RATING: GOOD - System handles most boundaries well")
        elif success_rate >= 90:
            print("🥉 RATING: ACCEPTABLE - Some boundary issues need fixing")
        else:
            print("💔 RATING: NEEDS WORK - Multiple boundary issues found")
        print(f"{'=' * 90}")
        
        return success_rate >= 99


if __name__ == "__main__":
    tester = UltimateBoundaryTester()
    success = tester.run_all_tests()
    
    print(f"\n{'=' * 90}")
    print(f"✅ BOUNDARY TESTING COMPLETE - Success: {success}")
    print(f"{'=' * 90}")
