"""
Test Intelligent Pricing Engine
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_intelligent_pricing():
    """Test intelligent pricing engine"""
    try:
        from stillme_core.intelligent_pricing_engine import IntelligentPricingEngine
        
        print("🧪 Testing Intelligent Pricing Engine...")
        
        # Initialize pricing engine
        pricing_engine = IntelligentPricingEngine()
        print("✅ Intelligent Pricing Engine initialized")
        
        # Test pricing status
        print("💰 Testing pricing status...")
        status = await pricing_engine._get_pricing_status({})
        print(f"Pricing status: {status['status']}")
        print(f"Pricing optimization enabled: {status['data']['pricing_optimization_enabled']}")
        print(f"Dynamic pricing enabled: {status['data']['dynamic_pricing_enabled']}")
        print(f"Billing automation enabled: {status['data']['billing_automation_enabled']}")
        print(f"Compliance monitoring enabled: {status['data']['compliance_monitoring_enabled']}")
        print(f"Pricing strategies: {status['data']['pricing_strategies_count']}")
        print(f"Price points: {status['data']['price_points_count']}")
        print(f"Customer segments: {status['data']['customer_segments_count']}")
        print(f"Billing records: {status['data']['billing_records_count']}")
        print(f"Pricing reports: {status['data']['pricing_reports_count']}")
        
        # Test pricing strategies
        print("📋 Testing pricing strategies...")
        strategies = await pricing_engine._get_pricing_strategies({})
        print(f"Pricing strategies: {strategies['data']['total_strategies']}")
        for strategy in strategies['data']['pricing_strategies']:
            print(f"  - {strategy['name']}: ${strategy['base_price']}/{strategy['billing_cycle']}")
            print(f"    Model: {strategy['model']}, Features: {len(strategy['features'])}")
        
        # Test customer segments
        print("👥 Testing customer segments...")
        segments = await pricing_engine._get_customer_segments({})
        print(f"Customer segments: {segments['data']['total_segments']}")
        for segment in segments['data']['customer_segments']:
            print(f"  - {segment['name']}: WTP ${segment['willingness_to_pay']}, LTV ${segment['lifetime_value']}")
            print(f"    Price sensitivity: {segment['price_sensitivity']:.2f}, Value perception: {segment['value_perception']:.2f}")
        
        # Test billing records
        print("💳 Testing billing records...")
        billing = await pricing_engine._get_billing_records({})
        print(f"Billing records: {billing['data']['total_records']}")
        print(f"Total revenue: ${billing['data']['total_revenue']:.2f}")
        print(f"Paid records: {billing['data']['paid_records']}")
        print(f"Pending records: {billing['data']['pending_records']}")
        print(f"Payment success rate: {billing['data']['payment_success_rate']:.1%}")
        
        # Test price calculation
        print("🧮 Testing price calculation...")
        price_calc = await pricing_engine._calculate_price({
            "tier": "professional",
            "usage_metrics": {"api_calls": 7500, "storage": "8GB"},
            "customer_segment": "smb_segment"
        })
        print(f"Price calculation: {price_calc['status']}")
        if price_calc['status'] == 'success':
            calc_data = price_calc['data']['calculated_price']
            print(f"  Base price: ${calc_data['base_price']:.2f}")
            print(f"  Usage multiplier: {calc_data['usage_multiplier']:.2f}")
            print(f"  Segment multiplier: {calc_data['segment_multiplier']:.2f}")
            print(f"  Final price: ${calc_data['final_price']:.2f}")
            print(f"  Confidence: {calc_data['confidence_score']:.2f}")
        
        # Test pricing optimization
        print("🎯 Testing pricing optimization...")
        optimization = await pricing_engine._optimize_pricing({
            "goals": ["revenue_maximization"],
            "time_horizon": 12
        })
        print(f"Pricing optimization: {optimization['status']}")
        if optimization['status'] == 'success':
            opt_data = optimization['data']['optimization_result']
            print(f"  Optimal price: ${opt_data['optimal_price']:.2f}")
            print(f"  Expected revenue: ${opt_data['expected_revenue']:.2f}")
            print(f"  ROI: {opt_data['roi_percentage']:.1f}%")
        
        # Test different pricing scenarios
        print("🔄 Testing different pricing scenarios...")
        
        # Test startup pricing
        startup_calc = await pricing_engine._calculate_price({
            "tier": "basic",
            "usage_metrics": {"api_calls": 2000, "storage": "2GB"},
            "customer_segment": "startup_segment"
        })
        if startup_calc['status'] == 'success':
            startup_price = startup_calc['data']['calculated_price']['final_price']
            print(f"  Startup price: ${startup_price:.2f}")
        
        # Test enterprise pricing
        enterprise_calc = await pricing_engine._calculate_price({
            "tier": "enterprise",
            "usage_metrics": {"api_calls": 50000, "storage": "50GB"},
            "customer_segment": "enterprise_segment"
        })
        if enterprise_calc['status'] == 'success':
            enterprise_price = enterprise_calc['data']['calculated_price']['final_price']
            print(f"  Enterprise price: ${enterprise_price:.2f}")
        
        # Test different optimization goals
        print("🎯 Testing different optimization goals...")
        
        # Revenue maximization
        revenue_opt = await pricing_engine._optimize_pricing({
            "goals": ["revenue_maximization"],
            "time_horizon": 6
        })
        if revenue_opt['status'] == 'success':
            revenue_data = revenue_opt['data']['optimization_result']
            print(f"  Revenue optimization: ${revenue_data['optimal_price']:.2f} -> ${revenue_data['expected_revenue']:.2f}")
        
        # Customer acquisition
        acquisition_opt = await pricing_engine._optimize_pricing({
            "goals": ["customer_acquisition"],
            "time_horizon": 12
        })
        if acquisition_opt['status'] == 'success':
            acquisition_data = acquisition_opt['data']['optimization_result']
            print(f"  Acquisition optimization: ${acquisition_data['optimal_price']:.2f} -> {acquisition_data['expected_customers']} customers")
        
        # Profit maximization
        profit_opt = await pricing_engine._optimize_pricing({
            "goals": ["profit_maximization"],
            "time_horizon": 24
        })
        if profit_opt['status'] == 'success':
            profit_data = profit_opt['data']['optimization_result']
            print(f"  Profit optimization: ${profit_data['optimal_price']:.2f} -> ${profit_data['expected_profit']:.2f}")
        
        # Wait for some processing cycles
        print("⏳ Waiting for processing cycles...")
        await asyncio.sleep(5)
        
        # Test again after processing
        print("💰 Testing after processing...")
        status = await pricing_engine._get_pricing_status({})
        print(f"Updated billing records: {status['data']['billing_records_count']}")
        
        # Test updated billing records
        print("💳 Testing updated billing records...")
        billing = await pricing_engine._get_billing_records({})
        print(f"Updated billing records: {billing['data']['total_records']}")
        print(f"Updated total revenue: ${billing['data']['total_revenue']:.2f}")
        print(f"Updated payment success rate: {billing['data']['payment_success_rate']:.1%}")
        
        # Shutdown
        pricing_engine.shutdown()
        
        print("✅ Intelligent Pricing Engine test completed!")
        
    except Exception as e:
        print(f"❌ Error testing intelligent pricing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_intelligent_pricing())
