"""
Histogram数据流追踪测试
诊断Histogram记录丢失问题
"""
import sys
import time
from agent_toolkit.shared.metrics_api import metrics_collector

def test_histogram_direct():
    """直接测试Histogram collector"""
    print("="*80)
    print("🔍 Histogram数据流追踪测试")
    print("="*80)

    test_name = "diag_test"

    print(f"\n📝 Step 1: 记录前检查 histogram data")
    values_before = metrics_collector._histograms.get(test_name, [])
    print(f"   记录前数据量: {len(values_before)}")

    print(f"\n📝 Step 2: 记录10条Histogram数据")
    for i in range(10):
        metrics_collector.record_histogram(test_name, float(i))
        print(f"   记录 {i}: 成功, 当前数量={len(metrics_collector._histograms[test_name])}")

    print(f"\n📝 Step 3: 记录后检查 histogram data")
    values_after = metrics_collector._histograms.get(test_name, [])
    print(f"   记录后数据量: {len(values_after)}")
    print(f"   数据内容: {values_after}")

    print(f"\n📝 Step 4: 获取统计信息")
    stats = metrics_collector.get_histogram_stats(test_name)
    print(f"   统计结果: {stats}")

    print(f"\n📝 Step 5: 获取历史数据")
    history = metrics_collector.get_metric_history(test_name, limit=100)
    print(f"   历史记录数量: {len(history)}")

    print("\n" + "="*80)
    print("✅ 诊断测试完成")
    print("="*80)

def test_histogram_via_api():
    """通过API测试Histogram"""
    print("\n" + "="*80)
    print("🔍 Histogram API测试")
    print("="*80)

    from agent_toolkit.main import create_app
    from fastapi.testclient import TestClient

    app = create_app()
    client = TestClient(app)

    test_name = "api_test"

    print(f"\n📝 Step 1: 通过API记录10条数据")
    for i in range(10):
        response = client.post("/api/v1/metrics/histogram",
                              json={"name": test_name, "value": float(i)})
        print(f"   记录 {i}: 状态码={response.status_code}")

    print(f"\n📝 Step 2: 通过API获取统计信息")
    response = client.get(f"/api/v1/metrics/histograms/{test_name}")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   响应数据: {data}")
        stats = data.get('stats', {})
        print(f"   统计信息: {stats}")

    print("\n" + "="*80)
    print("✅ API测试完成")
    print("="*80)

if __name__ == "__main__":
    test_histogram_direct()
    test_histogram_via_api()
