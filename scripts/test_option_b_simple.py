"""
Simple Option B Test - Debug script

Tests a single question to verify Option B pipeline is working.
"""

import os
import sys
import requests
import json

# Fix encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Get API base from environment or use default
API_BASE = os.getenv("STILLME_API_BASE", "http://localhost:8000")
API_KEY = os.getenv("STILLME_API_KEY", "")

def normalize_api_base(url: str) -> str:
    """Normalize API base URL"""
    if not url.startswith(("http://", "https://")):
        if "railway.app" in url or "localhost" not in url:
            return f"https://{url}"
        else:
            return f"http://{url}"
    return url

def test_question(question: str, use_option_b: bool = True):
    """Test a single question"""
    print("=" * 80)
    print(f"Testing: {question[:60]}...")
    print(f"Option B: {'ENABLED' if use_option_b else 'DISABLED'}")
    print("=" * 80)
    
    url = f"{normalize_api_base(API_BASE)}/api/chat/rag"
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    payload = {
        "message": question,
        "use_rag": True,
        "context_limit": 5,
        "use_option_b": use_option_b
    }
    
    try:
        import time
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        elapsed = time.time() - start_time
        
        print(f"\n⏱️  Latency: {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "")
            processing_steps = data.get("processing_steps", [])
            timing_logs = data.get("timing_logs", {})
            
            print(f"\n📝 Response length: {len(answer)} chars")
            print(f"📋 Processing steps: {len(processing_steps)}")
            
            # Check if Option B ran
            has_option_b = any("Option B" in step for step in processing_steps)
            print(f"\n🚀 Option B detected: {'YES' if has_option_b else 'NO'}")
            
            if processing_steps:
                print("\n📋 Processing steps:")
                for i, step in enumerate(processing_steps[:10], 1):  # Show first 10
                    print(f"  {i}. {step}")
            
            if timing_logs:
                print("\n⏱️  Timing logs:")
                for key, value in timing_logs.items():
                    print(f"  - {key}: {value}")
            
            # Show first 500 chars of response
            print(f"\n📄 Response preview (first 500 chars):")
            print("-" * 80)
            print(answer[:500])
            print("-" * 80)
            
            # Check for EPD-Fallback indicators
            answer_lower = answer.lower()
            has_fallback = any(phrase in answer_lower for phrase in [
                "không tìm thấy", "not found", "no source", "không có nguồn",
                "có vẻ giả định", "seems hypothetical"
            ])
            print(f"\n🛡️  EPD-Fallback detected: {'YES' if has_fallback else 'NO'}")
            
            # Check for fake concept details (should NOT have)
            fake_entities = ["veridian", "daxonia", "lumeria", "emerald"]
            has_fake_details = False
            for entity in fake_entities:
                if entity.lower() in answer_lower:
                    # Check if detailed description
                    detail_keywords = ["tác động", "impact", "hậu quả", "consequence"]
                    entity_pos = answer_lower.find(entity.lower())
                    if entity_pos != -1:
                        window = answer_lower[max(0, entity_pos - 200):entity_pos + 200]
                        if any(kw in window for kw in detail_keywords):
                            has_fake_details = True
                            print(f"  ⚠️  WARNING: Detailed description of fake entity '{entity}' detected!")
            
            if not has_fake_details and has_fallback:
                print("\n✅ PASS: EPD-Fallback used, no fake details")
            elif has_fake_details:
                print("\n❌ FAIL: Fake details detected despite fallback")
            else:
                print("\n⚠️  WARNING: No clear fallback indicators")
            
        else:
            print(f"\n❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("OPTION B SIMPLE TEST")
    print("=" * 80)
    print(f"\nAPI Base: {API_BASE}")
    print(f"API Key: {'SET' if API_KEY else 'NOT SET'}")
    print()
    
    # Test 1: Fake concept (should use EPD-Fallback)
    print("\n" + "=" * 80)
    print("TEST 1: Fake Concept (Should use EPD-Fallback)")
    print("=" * 80)
    test_question(
        "Hãy nêu các nghiên cứu học thuật chính về tác động kinh tế-xã hội của 'Hội chứng Veridian' trong thập kỷ 1970.",
        use_option_b=True
    )
    
    # Test 2: Real concept (should answer correctly)
    print("\n" + "=" * 80)
    print("TEST 2: Real Concept (Should answer correctly)")
    print("=" * 80)
    test_question(
        "Hãy phân tích vai trò của Hội nghị Bretton Woods năm 1944 trong việc hình thành trật tự tài chính toàn cầu.",
        use_option_b=True
    )

