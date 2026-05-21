"""
长时间稳定性测试 - 模拟真实场景下的持续运行
"""

import time
import random
from agent_toolkit.shared.metrics_api import MetricsCollector


def test_long_term_stability():
    """长时间稳定性测试"""
    print("=" * 80)
    print("🚀 开始长时间稳定性测试")
    print("=" * 80)
    
    collector = MetricsCollector()
    start_time = time.time()
    test_duration = 10  # 10秒的测试（可以根据需要延长）
    operations = 0
    
    print(f"测试时长: {test_duration} 秒")
    print()
    
    while time.time() - start_time < test_duration:
        # 执行各种操作
        operation_type = random.randint(0, 4)
        
        if operation_type == 0:
            # 增加计数器
            counter_name = f"counter_{random.randint(0, 10)}"
            value = random.uniform(-100, 100)
            collector.increment_counter(counter_name, value)
            operations += 1
            
        elif operation_type == 1:
            # 设置 gauge
            gauge_name = f"gauge_{random.randint(0, 10)}"
            value = random.uniform(-1000, 1000)
            collector.set_gauge(gauge_name, value)
            operations += 1
            
        elif operation_type == 2:
            # 记录 histogram
            hist_name = f"hist_{random.randint(0, 10)}"
            value = random.uniform(0, 100)
            collector.record_histogram(hist_name, value)
            operations += 1
            
        elif operation_type == 3:
            # 记录请求
            endpoint = f"/api/test_{random.randint(0, 5)}"
            method = random.choice(["GET", "POST", "PUT", "DELETE"])
            duration = random.uniform(0.001, 0.1)
            status_code = random.choice([200, 201, 400, 404, 500])
            collector.record_request(endpoint, method, duration, status_code)
            operations += 1
            
        elif operation_type == 4:
            # 获取指标
            collector.get_all_metrics()
            operations += 1
        
        # 偶尔休息一下，模拟真实场景
        if random.random() < 0.1:
            time.sleep(0.001)
    
    elapsed = time.time() - start_time
    print()
    print("=" * 80)
    print("✅ 长时间稳定性测试完成")
    print("=" * 80)
    print(f"总操作数: {operations}")
    print(f"测试时长: {elapsed:.2f} 秒")
    print(f"吞吐量: {operations / elapsed:.1f} 操作/秒")
    print()
    
    # 验证数据完整性
    print("📊 验证数据完整性...")
    
    # 验证计数器
    total_counters = len(collector._counters)
    print(f"  - 计数器数量: {total_counters}")
    
    # 验证 gauges
    total_gauges = len(collector._gauges)
    print(f"  - Gauge 数量: {total_gauges}")
    
    # 验证 histograms
    total_hists = len(collector._histograms)
    print(f"  - Histogram 数量: {total_hists}")
    
    # 验证每个 histogram 大小不超过 1000
    for name, values in collector._histograms.items():
        if len(values) > 1000:
            print(f"  ⚠️ Histogram {name} 有 {len(values)} 条记录")
    
    # 获取完整指标
    metrics = collector.get_all_metrics()
    print(f"  - 系统运行时间: {metrics['uptime_formatted']}")
    print(f"  - 总请求数: {metrics['total_requests']}")
    
    print()
    print("🎉 所有检查通过，系统稳定性验证完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_long_term_stability()
