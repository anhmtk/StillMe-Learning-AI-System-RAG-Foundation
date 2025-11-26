"""Test API directly to see what's happening"""
import requests
import json

# Test với Railway
api_url = "https://stillme-backend-production.up.railway.app"
# Hoặc test với local (uncomment)
# api_url = "http://localhost:8000"

print(f"Testing API: {api_url}")
print("=" * 60)

# Test 1: Health check
print("\n[1] Health Check...")
try:
    response = requests.get(f"{api_url}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   [OK] Backend is healthy")
    else:
        print(f"   [ERROR] Backend health check failed: {response.text}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")
    exit(1)

# Test 2: Simple question
print("\n[2] Testing simple question...")
payload = {
    "message": "What is the capital of France?",
    "user_id": "test_user",
    "use_rag": True,
    "context_limit": 3
}

try:
    response = requests.post(
        f"{api_url}/api/chat/rag",
        json=payload,
        timeout=30
    )
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data.get('response', '')[:200]}")
        print(f"   Confidence: {data.get('confidence_score', 0)}")
        print(f"   Has Citation: {data.get('has_citation', False)}")
        validation_info = data.get('validation_info')
        if validation_info:
            print(f"   Validation Passed: {validation_info.get('passed', False)}")
        else:
            print(f"   Validation Info: None")
        
        # Check if it's an error message
        response_text = data.get('response', '')
        if 'technical issue' in response_text.lower() or 'cannot provide' in response_text.lower():
            print("\n   [WARNING] API returned error message!")
            print("   This suggests API keys or backend configuration issue")
    else:
        print(f"   [ERROR] Error: {response.text[:500]}")
except Exception as e:
    print(f"   [ERROR] Exception: {e}")

# Test 3: Check environment (if local)
if "localhost" in api_url:
    print("\n[3] Checking local environment variables...")
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")
    }
    
    for key_name, key_value in keys.items():
        if key_value:
            print(f"   [OK] {key_name}: Found ({len(key_value)} chars)")
        else:
            print(f"   [MISSING] {key_name}: Not found")

print("\n" + "=" * 60)
print("Test complete!")

