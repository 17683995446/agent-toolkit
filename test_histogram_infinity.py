"""
Test Histogram with Infinite Values
"""

from agent_toolkit.shared.metrics_api import MetricsCollector
import sys

def test_histogram_with_inf():
    print("Testing Histogram Stats with Infinite Values")
    print("=" * 60)
    
    collector = MetricsCollector()
    
    # Add various values including infinity
    test_values = [
        1.0, 2.0, 3.0, 
        float('inf'), float('-inf'),
        4.0, 5.0,
        float('inf'), float('-inf'),
        6.0
    ]
    
    print(f"\nAdding {len(test_values)} values to histogram:")
    for i, val in enumerate(test_values):
        print(f"  {i}: {val}")
        collector.record_histogram("test_inf_hist", val)
    
    print("\n" + "=" * 60)
    print("Getting histogram stats...")
    try:
        stats = collector.get_histogram_stats("test_inf_hist")
        print("✅ Successfully got stats!")
        print(f"\nStats: {stats}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_histogram_with_inf()
    sys.exit(0 if success else 1)
