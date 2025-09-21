#!/usr/bin/env python3
"""
Final verification test for Smart Routing Solution
"""
import requests
import json
import time

def test_current_routing():
    """Test current routing (before fix)"""
    print("🔍 Testing CURRENT routing (before fix)...")
    
    simple_messages = ["xin chào", "2+2=?", "hello"]
    complex_messages = [
        "Hãy viết đoạn code Python đọc CSV, tính trung bình và in kết quả theo cột.",
        "Giải thích thuật toán quicksort và implement bằng Python"
    ]
    
    results = {"simple": [], "complex": []}
    
    # Test simple messages
    for msg in simple_messages:
        try:
            response = requests.post(
                'http://160.191.89.99:21568/chat',
                json={'message': msg, 'session_id': 'test-current'},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                results["simple"].append({
                    "message": msg,
                    "model": data.get('model', 'unknown'),
                    "success": True
                })
            else:
                results["simple"].append({
                    "message": msg,
                    "model": None,
                    "success": False
                })
        except Exception as e:
            results["simple"].append({
                "message": msg,
                "model": None,
                "success": False,
                "error": str(e)
            })
    
    # Test complex messages
    for msg in complex_messages:
        try:
            response = requests.post(
                'http://160.191.89.99:21568/chat',
                json={'message': msg, 'session_id': 'test-current'},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                results["complex"].append({
                    "message": msg,
                    "model": data.get('model', 'unknown'),
                    "success": True
                })
            else:
                results["complex"].append({
                    "message": msg,
                    "model": None,
                    "success": False
                })
        except Exception as e:
            results["complex"].append({
                "message": msg,
                "model": None,
                "success": False,
                "error": str(e)
            })
    
    return results

def analyze_results(results):
    """Analyze test results"""
    print("\n📊 ANALYSIS:")
    print("=" * 50)
    
    # Simple messages
    simple_models = [r['model'] for r in results["simple"] if r['success']]
    simple_success = len([r for r in results["simple"] if r['success']])
    simple_total = len(results["simple"])
    
    print(f"Simple messages: {simple_success}/{simple_total} success")
    print(f"Models used: {set(simple_models)}")
    
    if 'deepseek-chat' in simple_models:
        print("❌ PROBLEM: Simple messages using DeepSeek (expensive)")
    elif any('gemma' in str(m).lower() for m in simple_models):
        print("✅ GOOD: Simple messages using Gemma (local)")
    
    # Complex messages
    complex_models = [r['model'] for r in results["complex"] if r['success']]
    complex_success = len([r for r in results["complex"] if r['success']])
    complex_total = len(results["complex"])
    
    print(f"\nComplex messages: {complex_success}/{complex_total} success")
    print(f"Models used: {set(complex_models)}")
    
    if 'deepseek-chat' in complex_models:
        print("✅ GOOD: Complex messages using DeepSeek")
    elif complex_success < complex_total * 0.5:
        print("❌ PROBLEM: Complex messages failing/timeout")
    
    return {
        "simple_success_rate": simple_success / simple_total * 100,
        "complex_success_rate": complex_success / complex_total * 100,
        "simple_models": set(simple_models),
        "complex_models": set(complex_models)
    }

def generate_deployment_guide():
    """Generate deployment guide"""
    guide = """
🚀 STILLME GATEWAY SMART ROUTING - DEPLOYMENT GUIDE
==================================================

📋 FILES CREATED:
✅ deploy_smart_routing.sh - VPS deployment script
✅ gateway_integration_patch.py - Integration guide
✅ final_verification_test.py - This verification script

🔧 DEPLOYMENT STEPS:

1. COPY FILES TO VPS:
   scp deploy_smart_routing.sh root@160.191.89.99:/opt/stillme/
   scp gateway_integration_patch.py root@160.191.89.99:/opt/stillme/

2. RUN DEPLOYMENT SCRIPT:
   ssh root@160.191.89.99
   cd /opt/stillme
   chmod +x deploy_smart_routing.sh
   ./deploy_smart_routing.sh

3. UPDATE GATEWAY CODE:
   - Edit your gateway's chat endpoint
   - Add: from smart_router import route_message
   - Replace chat logic with smart routing

4. RESTART SERVICE:
   sudo systemctl restart stillme-gateway

5. VERIFY DEPLOYMENT:
   python final_verification_test.py

🔧 ROUTING CONTROLS:
- ROUTING_MODE=auto|force_gemma|force_cloud
- DISABLE_CLOUD=0|1
- GEMMA_TIMEOUT=2.5 (seconds)
- DEEPSEEK_TIMEOUT=10.0 (seconds)

📊 EXPECTED RESULTS AFTER FIX:
- Simple messages → gemma2:2b (local, fast, free)
- Complex messages → deepseek-chat (cloud, powerful, paid)
- Timeout fallback → gemma2:2b-fallback
- Success rates: Simple 90%+, Complex 80%+

🎯 SUCCESS CRITERIA:
✅ Simple messages use Gemma (not DeepSeek)
✅ Complex messages use DeepSeek (not timeout)
✅ Fallback works on timeout
✅ No sensitive data in logs
✅ Environment controls working

⚠️ TROUBLESHOOTING:
- If Gemma not working: Check Ollama service
- If DeepSeek failing: Check API key and network
- If routing wrong: Check ROUTING_MODE setting
- If timeout: Adjust timeout values in .env

📞 SUPPORT:
- Check logs: journalctl -u stillme-gateway -f
- Test scripts: /opt/stillme/tools/test_vps_gateway_*.sh
- Environment: cat /opt/stillme/.env | grep ROUTING
"""
    
    with open('DEPLOYMENT_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ Generated DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    print("🚀 FINAL VERIFICATION TEST")
    print("=" * 50)
    
    # Test current routing
    results = test_current_routing()
    
    # Analyze results
    analysis = analyze_results(results)
    
    # Generate deployment guide
    generate_deployment_guide()
    
    print("\n🎯 SUMMARY:")
    print(f"Simple success rate: {analysis['simple_success_rate']:.1f}%")
    print(f"Complex success rate: {analysis['complex_success_rate']:.1f}%")
    print(f"Simple models: {analysis['simple_models']}")
    print(f"Complex models: {analysis['complex_models']}")
    
    print("\n📋 NEXT STEPS:")
    print("1. Deploy smart routing using deploy_smart_routing.sh")
    print("2. Update gateway code using gateway_integration_patch.py")
    print("3. Restart gateway service")
    print("4. Run this test again to verify fix")
    print("5. Check DEPLOYMENT_GUIDE.md for detailed instructions")
