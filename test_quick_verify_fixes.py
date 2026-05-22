"""Quickly verify that our fixes work correctly"""

from agent_toolkit.shared.metrics_api import MetricsCollector

print("=" * 80)
print("🚀 Verifying our Bug Fixes")
print("=" * 80)

collector = MetricsCollector()

print("\n1️⃣  Testing counter with nan/inf values...")
# Test counter with nan and inf
collector.increment_counter("test_counter", 10)
print(f"   After +10: {collector._counters['test_counter']}")

collector.increment_counter("test_counter", float('nan'))
print(f"   After +nan: {collector._counters['test_counter']} (should still be 10)")

collector.increment_counter("test_counter", 5)
print(f"   After +5: {collector._counters['test_counter']} (should be 15)")

collector.increment_counter("test_counter", float('inf'))
print(f"   After +inf: {collector._counters['test_counter']} (should still be 15)")


print("\n2️⃣  Testing gauge with nan/inf values...")
collector.set_gauge("test_gauge", 100)
print(f"   After set 100: {collector._gauges['test_gauge']}")

collector.set_gauge("test_gauge", float('nan'))
print(f"   After set nan: {collector._gauges['test_gauge']} (should still be 100)")

collector.set_gauge("test_gauge", 50)
print(f"   After set 50: {collector._gauges['test_gauge']} (should be 50)")


print("\n3️⃣  Testing get_all_metrics includes histograms...")
all_metrics = collector.get_all_metrics()
has_histograms = 'histograms' in all_metrics
print(f"   Has 'histograms' key: {has_histograms}")


print("\n4️⃣  Testing histogram stats with mixed values...")
for i in range(5):
    collector.record_histogram("test_mixed_hist", i * 10)
collector.record_histogram("test_mixed_hist", float('inf'))
collector.record_histogram("test_mixed_hist", float('-inf'))
collector.record_histogram("test_mixed_hist", 100)

stats = collector.get_histogram_stats("test_mixed_hist")
print(f"   Histogram stats: {stats}")
print(f"   Mean is valid number: {stats.get('mean', -1) == stats.get('mean', -2)}")


print("\n" + "=" * 80)
if (
    collector._counters['test_counter'] == 15 and
    collector._gauges['test_gauge'] == 50 and
    has_histograms and
    stats.get('mean', -1) == 30.0
):
    print("✅ ALL FIXES VERIFIED!")
else:
    print("❌ Some fixes failed!")
print("=" * 80)
