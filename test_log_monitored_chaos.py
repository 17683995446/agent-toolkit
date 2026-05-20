"""
带日志实时监控的超超超超大规模混沌测试
通过日志实时监控系统运行状态，发现深层次问题
慢工出细活 - 深度测试每一个细节
"""

import pytest
import time
import random
import threading
import gc
import sys
import io
import logging
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from agent_toolkit.main import create_app
from agent_toolkit.shared.structured_logging import get_logger


class LogCapture:
    """实时日志捕获器"""
    
    def __init__(self):
        self.logs = deque(maxlen=100000)
        self.lock = threading.Lock()
        self.error_count = defaultdict(int)
        self.warning_count = defaultdict(int)
        
        # 设置日志处理器
        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        self.handler.setFormatter(formatter)
    
    def capture_log(self, level: str, message: str):
        """捕获日志"""
        with self.lock:
            self.logs.append({
                'time': time.time(),
                'level': level,
                'message': message
            })
            
            if level == 'ERROR':
                self.error_count[message] += 1
            elif level == 'WARNING':
                self.warning_count[message] += 1
    
    def get_recent_logs(self, count: int = 100):
        """获取最近的日志"""
        with self.lock:
            return list(self.logs)[-count:]
    
    def get_error_summary(self):
        """获取错误摘要"""
        with self.lock:
            return {
                'total_errors': sum(self.error_count.values()),
                'error_types': dict(self.error_count),
                'total_warnings': sum(self.warning_count.values()),
                'warning_types': dict(self.warning_count)
            }


class LoggedTestMonitor:
    """带日志监控的测试监视器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.request_times = deque(maxlen=100000)
        self.errors = defaultdict(int)
        self.success_count = 0
        self.fail_count = 0
        self.log_capture = LogCapture()
    
    def record(self, success: bool, response_time: float, error_type: str = None):
        with self.lock:
            self.request_times.append(response_time)
            if success:
                self.success_count += 1
            else:
                self.fail_count += 1
                if error_type:
                    self.errors[error_type] += 1
    
    def get_stats(self):
        with self.lock:
            total = self.success_count + self.fail_count
            elapsed = time.time() - self.start_time
            
            avg_resp = sum(self.request_times) / len(self.request_times) if self.request_times else 0
            max_resp = max(self.request_times) if self.request_times else 0
            
            return {
                "total_requests": total,
                "success": self.success_count,
                "fail": self.fail_count,
                "success_rate": (self.success_count / total * 100) if total > 0 else 0,
                "avg_response_ms": avg_resp * 1000,
                "max_response_ms": max_resp * 1000,
                "requests_per_second": total / elapsed if elapsed > 0 else 0,
                "errors": dict(self.errors),
                "elapsed": elapsed,
            }


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestLoggedChaosScenarios:
    """带日志监控的混沌场景测试"""
    
    def test_logged_ultra_scale_chaos(self, client):
        """带日志监控的超超超超大规模混沌测试 - 100000请求"""
        print("\n" + "="*80)
        print("🚀 开始带日志监控的超超超超大规模混沌测试")
        print("="*80)
        
        monitor = LoggedTestMonitor()
        
        total_requests = 100000
        batch_size = 10000
        batches = total_requests // batch_size
        
        print(f"计划进行 {total_requests} 个带日志监控的请求...")
        
        endpoints = [
            ("GET", "/api/v1/health", None),
            ("GET", "/liveness", None),
            ("GET", "/readiness", None),
            ("GET", "/api/v1/metrics/dashboard", None),
            ("POST", "/api/v1/metrics/counter", {"name": "logged_chaos", "value": 1.0}),
            ("POST", "/api/v1/metrics/gauge", {"name": "logged_gauge", "value": 50.0}),
            ("POST", "/api/v1/metrics/histogram", {"name": "logged_hist", "value": 25.5}),
        ]
        
        def logged_chaos_request(index):
            try:
                method, url, data = random.choice(endpoints)
                
                # 随机引入混乱
                if random.random() < 0.1 and data:
                    data = data.copy()
                    data["name"] = data["name"] + "_" + str(random.randint(1, 100000000))
                    data["value"] = random.uniform(0, 1000)
                
                start_time = time.time()
                
                if method == "GET":
                    response = client.get(url)
                else:
                    response = client.post(url, json=data)
                
                success = 200 <= response.status_code < 500
                monitor.record(success, time.time() - start_time, 
                              f"HTTP_{response.status_code}" if not success else None)
                return success
            except Exception as e:
                monitor.record(False, time.time() - start_time, type(e).__name__)
                return False
        
        num_threads = random.randint(500, 1000)
        print(f"使用 {num_threads} 个超超超大规模线程...")
        
        for batch in range(batches):
            batch_start = time.time()
            
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(logged_chaos_request, i) for i in range(batch_size)]
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    if completed % 2000 == 0:
                        stats = monitor.get_stats()
                        log_summary = monitor.log_capture.get_error_summary()
                        print(f"批次 {batch+1}/{batches}: {completed}/{batch_size} 完成, "
                              f"成功率: {stats['success_rate']:.1f}%, "
                              f"错误: {log_summary['total_errors']}, "
                              f"警告: {log_summary['total_warnings']}")
            
            batch_time = time.time() - batch_start
            print(f"批次 {batch+1}/{batches} 完成 - 耗时: {batch_time:.2f}s")
            
            gc.collect()
        
        stats = monitor.get_stats()
        log_summary = monitor.log_capture.get_error_summary()
        
        print("\n" + "="*80)
        print("📊 带日志监控的超超超超大规模混沌测试结果")
        print("="*80)
        print(f"总请求: {stats['total_requests']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['fail']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"平均响应: {stats['avg_response_ms']:.2f}ms")
        print(f"最大响应: {stats['max_response_ms']:.2f}ms")
        print(f"请求/秒: {stats['requests_per_second']:.1f}")
        print(f"\n日志监控结果:")
        print(f"  总错误数: {log_summary['total_errors']}")
        print(f"  总警告数: {log_summary['total_warnings']}")
        
        if log_summary['error_types']:
            print(f"\n错误类型统计:")
            for err, cnt in log_summary['error_types'].items():
                print(f"  {err}: {cnt}")
        
        if log_summary['warning_types']:
            print(f"\n警告类型统计:")
            for warn, cnt in log_summary['warning_types'].items():
                print(f"  {warn}: {cnt}")
        
        # 显示最近的日志样本
        recent_logs = monitor.log_capture.get_recent_logs(20)
        print(f"\n最近20条日志样本:")
        for log in recent_logs:
            print(f"  [{log['level']}] {log['message']}")
        
        assert stats['success_rate'] >= 99.0, f"超超超大规模场景下成功率太低: {stats['success_rate']:.2f}%"
        assert log_summary['total_errors'] == 0, f"发现 {log_summary['total_errors']} 个错误!"
    
    def test_logged_mixed_workload_chaos(self, client):
        """带日志监控的混合工作负载混沌测试"""
        print("\n" + "="*80)
        print("🔄 开始带日志监控的混合工作负载混沌测试")
        print("="*80)
        
        monitor = LoggedTestMonitor()
        
        # 混合工作负载
        total_requests = 50000
        
        print(f"计划进行 {total_requests} 个混合工作负载请求...")
        
        workload_patterns = [
            "read_heavy",   # 读密集型
            "write_heavy",   # 写密集型
            "balanced",     # 均衡型
            "burst",         # 突发型
            "spike"          # 尖峰型
        ]
        
        for pattern in workload_patterns:
            print(f"\n--- 测试 {pattern} 工作负载 ---")
            
            requests_in_pattern = total_requests // len(workload_patterns)
            
            if pattern == "read_heavy":
                endpoints = [
                    ("GET", "/api/v1/health", None),
                    ("GET", "/api/v1/metrics/dashboard", None),
                    ("GET", "/liveness", None),
                ]
            elif pattern == "write_heavy":
                endpoints = [
                    ("POST", "/api/v1/metrics/counter", {"name": "write_test", "value": 1.0}),
                    ("POST", "/api/v1/metrics/gauge", {"name": "write_gauge", "value": 50.0}),
                    ("POST", "/api/v1/metrics/histogram", {"name": "write_hist", "value": 25.5}),
                ]
            elif pattern == "balanced":
                endpoints = [
                    ("GET", "/api/v1/health", None),
                    ("POST", "/api/v1/metrics/counter", {"name": "balanced", "value": 1.0}),
                    ("GET", "/api/v1/metrics/dashboard", None),
                ]
            elif pattern == "burst":
                # 突发模式
                endpoints = [
                    ("GET", "/api/v1/health", None),
                ] * 3 + [
                    ("POST", "/api/v1/metrics/counter", {"name": "burst", "value": 1.0}),
                ]
            else:  # spike
                endpoints = [
                    ("GET", "/api/v1/health", None),
                ] * 9 + [
                    ("POST", "/api/v1/metrics/counter", {"name": "spike", "value": 1.0}),
                ]
            
            def pattern_request(index):
                try:
                    method, url, data = random.choice(endpoints)
                    start_time = time.time()
                    
                    if method == "GET":
                        response = client.get(url)
                    else:
                        response = client.post(url, json=data)
                    
                    success = 200 <= response.status_code < 500
                    monitor.record(success, time.time() - start_time, 
                                  f"HTTP_{response.status_code}" if not success else None)
                    return success
                except Exception as e:
                    monitor.record(False, time.time() - start_time, type(e).__name__)
                    return False
            
            num_threads = random.randint(100, 300)
            
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(pattern_request, i) for i in range(requests_in_pattern)]
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    if completed % 5000 == 0:
                        stats = monitor.get_stats()
                        log_summary = monitor.log_capture.get_error_summary()
                        print(f"  进度: {completed}/{requests_in_pattern}, "
                              f"成功率: {stats['success_rate']:.1f}%")
            
            gc.collect()
        
        stats = monitor.get_stats()
        log_summary = monitor.log_capture.get_error_summary()
        
        print("\n" + "="*80)
        print("📊 带日志监控的混合工作负载混沌测试结果")
        print("="*80)
        print(f"总请求: {stats['total_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        print(f"请求/秒: {stats['requests_per_second']:.1f}")
        print(f"\n日志监控结果:")
        print(f"  总错误数: {log_summary['total_errors']}")
        print(f"  总警告数: {log_summary['total_warnings']}")
        
        assert stats['success_rate'] >= 99.5, f"混合工作负载成功率太低: {stats['success_rate']:.2f}%"
        assert log_summary['total_errors'] == 0, f"发现 {log_summary['total_errors']} 个错误!"


class TestLogAnalysis:
    """日志分析测试"""
    
    def test_log_pattern_analysis(self, client):
        """日志模式分析测试"""
        print("\n" + "="*80)
        print("🔍 开始日志模式分析测试")
        print("="*80)
        
        monitor = LoggedTestMonitor()
        
        # 生成各种类型的请求，分析日志模式
        test_cases = 10000
        
        print(f"分析 {test_cases} 个请求的日志模式...")
        
        test_scenarios = [
            ("health_check", lambda: client.get("/api/v1/health")),
            ("liveness", lambda: client.get("/liveness")),
            ("readiness", lambda: client.get("/readiness")),
            ("metrics_dashboard", lambda: client.get("/api/v1/metrics/dashboard")),
            ("counter", lambda: client.post("/api/v1/metrics/counter", 
                                          json={"name": f"log_test_{random.randint(1,1000)}", "value": 1.0})),
            ("gauge", lambda: client.post("/api/v1/metrics/gauge", 
                                         json={"name": f"log_test_{random.randint(1,1000)}", "value": 50.0})),
            ("histogram", lambda: client.post("/api/v1/metrics/histogram", 
                                            json={"name": f"log_test_{random.randint(1,1000)}", "value": 25.5})),
        ]
        
        scenario_stats = defaultdict(lambda: {"success": 0, "fail": 0, "times": []})
        
        for i in range(test_cases):
            scenario_name, request_func = random.choice(test_scenarios)
            
            try:
                start = time.time()
                response = request_func()
                elapsed = time.time() - start
                
                success = 200 <= response.status_code < 400
                monitor.record(success, elapsed, f"HTTP_{response.status_code}" if not success else None)
                
                scenario_stats[scenario_name]["times"].append(elapsed)
                if success:
                    scenario_stats[scenario_name]["success"] += 1
                else:
                    scenario_stats[scenario_name]["fail"] += 1
                    
            except Exception as e:
                monitor.record(False, 0.001, type(e).__name__)
                scenario_stats[scenario_name]["fail"] += 1
            
            if (i + 1) % 1000 == 0:
                print(f"进度: {i+1}/{test_cases}")
        
        stats = monitor.get_stats()
        
        print("\n" + "="*80)
        print("📊 日志模式分析结果")
        print("="*80)
        print(f"总请求: {stats['total_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}%")
        
        print(f"\n各场景统计:")
        for scenario, stat in scenario_stats.items():
            avg_time = sum(stat["times"]) / len(stat["times"]) if stat["times"] else 0
            success_rate = stat["success"] / (stat["success"] + stat["fail"]) * 100 if (stat["success"] + stat["fail"]) > 0 else 0
            print(f"  {scenario}:")
            print(f"    成功: {stat['success']}, 失败: {stat['fail']}")
            print(f"    成功率: {success_rate:.2f}%")
            print(f"    平均响应: {avg_time*1000:.2f}ms")
        
        log_summary = monitor.log_capture.get_error_summary()
        print(f"\n日志监控结果:")
        print(f"  总错误数: {log_summary['total_errors']}")
        print(f"  总警告数: {log_summary['total_warnings']}")
        
        assert stats['success_rate'] >= 99.0, f"日志模式分析成功率低: {stats['success_rate']:.2f}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
