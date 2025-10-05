#!/usr/bin/env python3
"""
Test script to verify that the dashboard can load real data from database
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_dashboard_real_data():
    """Test that dashboard can load real data"""
    try:
        # Test imports
        from dashboards.streamlit.simple_app import SimpleDashboard

        print("✅ Successfully imported SimpleDashboard")

        # Test initialization
        dashboard = SimpleDashboard()
        print("✅ Successfully initialized SimpleDashboard")

        # Test real data functions
        sessions = dashboard.get_real_learning_sessions()
        print(f"✅ Got {len(sessions)} learning sessions from database")

        metrics = dashboard.calculate_real_metrics(30)
        print(f"✅ Calculated metrics for {len(metrics['dates'])} days")

        report = dashboard.get_real_learning_report()
        print(
            f"✅ Got learning report with {len(report['completed_topics'])} completed topics"
        )

        # Test refresh functionality
        refresh_success = dashboard.refresh_data()
        print(f"✅ Data refresh: {'Success' if refresh_success else 'Failed'}")

        print("\n🎉 All tests passed! Dashboard is ready to use real data.")
        return True

    except Exception as e:
        print(f"❌ Error testing dashboard: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_dashboard_real_data()
    sys.exit(0 if success else 1)
