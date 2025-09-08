"""
Test Usage Analytics Engine
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_usage_analytics():
    """Test usage analytics engine"""
    try:
        from stillme_core.usage_analytics_engine import UsageAnalyticsEngine
        
        print("🧪 Testing Usage Analytics Engine...")
        
        # Initialize usage analytics engine
        analytics_engine = UsageAnalyticsEngine()
        print("✅ Usage Analytics Engine initialized")
        
        # Test analytics status
        print("📊 Testing analytics status...")
        status = await analytics_engine._get_analytics_status({})
        print(f"Analytics status: {status['status']}")
        print(f"Usage tracking enabled: {status['data']['usage_tracking_enabled']}")
        print(f"Value quantification enabled: {status['data']['value_quantification_enabled']}")
        print(f"Cost analysis enabled: {status['data']['cost_analysis_enabled']}")
        print(f"Real-time analytics enabled: {status['data']['real_time_analytics_enabled']}")
        
        # Test usage analytics
        print("📈 Testing usage analytics...")
        usage = await analytics_engine._get_usage_analytics({})
        print(f"Usage analytics: {usage['data']['total_events']} events")
        print(f"Total value generated: ${usage['data']['total_value_generated']:.2f}")
        print(f"Total cost incurred: ${usage['data']['total_cost_incurred']:.2f}")
        print(f"Average duration: {usage['data']['average_duration']:.2f}s")
        print(f"Average value per event: ${usage['data']['average_value_per_event']:.2f}")
        print(f"Average cost per event: ${usage['data']['average_cost_per_event']:.2f}")
        
        # Test value analytics
        print("💰 Testing value analytics...")
        value = await analytics_engine._get_value_analytics({})
        print(f"Value analytics: {value['data']['total_metrics']} metrics")
        print(f"Total monetary value: ${value['data']['total_monetary_value']:.2f}")
        print(f"Average improvement: {value['data']['average_improvement_percentage']:.1f}%")
        print(f"Average confidence: {value['data']['average_confidence_score']:.2f}")
        
        # Test cost analytics
        print("💸 Testing cost analytics...")
        cost = await analytics_engine._get_cost_analytics({})
        print(f"Cost analytics: {cost['data']['total_analyses']} analyses")
        print(f"Total cost: ${cost['data']['total_cost']:.2f}")
        print(f"Total TCO: ${cost['data']['total_cost_of_ownership']:.2f}")
        print(f"Cost breakdown: {cost['data']['cost_breakdown']}")
        
        # Test analytics reports
        print("📋 Testing analytics reports...")
        reports = await analytics_engine._get_analytics_reports({})
        print(f"Analytics reports: {reports['data']['total_reports']}")
        
        # Test track usage event
        print("📝 Testing track usage event...")
        track = await analytics_engine._track_usage_event({
            "event_type": "feature_access",
            "module_name": "test_module",
            "feature_name": "test_feature",
            "duration": 1.5,
            "resource_usage": {"cpu": 0.2, "memory": 0.1},
            "context": {"test": True}
        })
        print(f"Track usage event: {track['status']}")
        
        # Wait for some tracking cycles
        print("⏳ Waiting for tracking cycles...")
        await asyncio.sleep(5)
        
        # Test again after tracking
        print("📊 Testing after tracking...")
        status = await analytics_engine._get_analytics_status({})
        print(f"Updated usage events: {status['data']['usage_events_count']}")
        print(f"Updated value metrics: {status['data']['value_metrics_count']}")
        print(f"Updated cost analyses: {status['data']['cost_analyses_count']}")
        print(f"Updated analytics reports: {status['data']['analytics_reports_count']}")
        
        # Test updated usage analytics
        print("📈 Testing updated usage analytics...")
        usage = await analytics_engine._get_usage_analytics({})
        print(f"Updated usage events: {usage['data']['total_events']}")
        if usage['data']['total_events'] > 0:
            print(f"Latest event: {usage['data']['usage_events'][-1]['event_type']}")
        
        # Test updated value analytics
        print("💰 Testing updated value analytics...")
        value = await analytics_engine._get_value_analytics({})
        print(f"Updated value metrics: {value['data']['total_metrics']}")
        if value['data']['total_metrics'] > 0:
            print(f"Latest metric: {value['data']['value_metrics'][-1]['metric_type']}")
        
        # Test updated cost analytics
        print("💸 Testing updated cost analytics...")
        cost = await analytics_engine._get_cost_analytics({})
        print(f"Updated cost analyses: {cost['data']['total_analyses']}")
        if cost['data']['total_analyses'] > 0:
            print(f"Latest analysis: {cost['data']['cost_analyses'][-1]['category']}")
        
        # Shutdown
        analytics_engine.shutdown()
        
        print("✅ Usage Analytics Engine test completed!")
        
    except Exception as e:
        print(f"❌ Error testing usage analytics: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_usage_analytics())
