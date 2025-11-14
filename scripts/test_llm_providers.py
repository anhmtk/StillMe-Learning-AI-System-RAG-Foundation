#!/usr/bin/env python3
"""
Test script for LLM provider support
Tests all supported LLM providers (DeepSeek, OpenAI, Claude, Gemini, Ollama, Custom)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

import asyncio
import httpx
from typing import Dict, Any

API_BASE = os.getenv("STILLME_API_BASE", "http://localhost:8000")


async def test_provider(
    provider: str,
    api_key: str = None,
    api_url: str = None,
    model_name: str = None
) -> Dict[str, Any]:
    """Test a specific LLM provider"""
    print(f"\n{'='*60}")
    print(f"Testing provider: {provider}")
    print(f"{'='*60}")
    
    payload = {
        "message": "Hello! Please respond with just 'OK' to confirm you're working.",
        "use_rag": False,  # Disable RAG for simple test
        "llm_provider": provider
    }
    
    if api_key:
        payload["llm_api_key"] = api_key
    if api_url:
        payload["llm_api_url"] = api_url
    if model_name:
        payload["llm_model_name"] = model_name
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_BASE}/api/chat/rag",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "provider": provider,
                    "status": "success",
                    "response": data.get("response", "")[:100],
                    "confidence": data.get("confidence_score")
                }
            else:
                return {
                    "provider": provider,
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
    except Exception as e:
        return {
            "provider": provider,
            "status": "error",
            "error": str(e)
        }


async def main():
    """Run tests for all providers"""
    print("StillMe LLM Provider Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: DeepSeek (if API key available)
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        result = await test_provider("deepseek", api_key=deepseek_key)
        results.append(result)
    else:
        print("\n⚠️  DEEPSEEK_API_KEY not set, skipping DeepSeek test")
    
    # Test 2: OpenAI (if API key available)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        result = await test_provider("openai", api_key=openai_key, model_name="gpt-3.5-turbo")
        results.append(result)
    else:
        print("\n⚠️  OPENAI_API_KEY not set, skipping OpenAI test")
    
    # Test 3: Claude (if API key available)
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    if claude_key:
        result = await test_provider("claude", api_key=claude_key)
        results.append(result)
    else:
        print("\n⚠️  ANTHROPIC_API_KEY not set, skipping Claude test")
    
    # Test 4: Gemini (if API key available)
    gemini_key = os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        result = await test_provider("gemini", api_key=gemini_key)
        results.append(result)
    else:
        print("\n⚠️  GOOGLE_API_KEY not set, skipping Gemini test")
    
    # Test 5: Ollama (local, no API key needed)
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    result = await test_provider("ollama", api_url=ollama_url, model_name="llama2")
    results.append(result)
    
    # Print summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    total_count = len(results)
    
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['provider']}: {result['status']}")
        if result["status"] == "success":
            print(f"   Response: {result['response']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n{'='*60}")
    print(f"Results: {success_count}/{total_count} providers working")
    print(f"{'='*60}")
    
    if success_count == 0:
        print("\n⚠️  No providers are working. Please check:")
        print("   1. API keys are set in environment variables")
        print("   2. Backend is running at", API_BASE)
        print("   3. Network connectivity")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

