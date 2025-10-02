#!/usr/bin/env python3
"""
Simple StillMe Gateway Performance Test
Author: StillMe AI Assistant
Date: 2025-09-22
"""

import asyncio
import statistics
import time

import aiohttp
import pytest

# Skip async tests due to missing pytest-asyncio
pytest.skip("Async tests require pytest-asyncio", allow_module_level=True)

async def test_direct_backend():
    """Test direct StillMe backend"""
    print("🔗 Testing Direct StillMe Backend...")

    times = []
    for i in range(3):
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:1216/chat",
                    json={"message": f"Test message {i}"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        latency = (time.time() - start_time) * 1000
                        times.append(latency)
                        print(f"   Request {i+1}: {latency:.1f}ms")
        except Exception as e:
            print(f"   Request {i+1}: Failed - {e}")

    if times:
        avg_time = statistics.mean(times)
        print(f"   Average: {avg_time:.1f}ms")
        return avg_time
    return None

async def test_gateway():
    """Test through gateway"""
    print("\n🚀 Testing Through Gateway...")

    times = []
    for i in range(3):
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8080/chat",
                    json={
                        "message": f"Test message {i}",
                        "user_id": "test_user",
                        "use_cache": True
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        latency = (time.time() - start_time) * 1000
                        times.append(latency)
                        print(f"   Request {i+1}: {latency:.1f}ms")
        except Exception as e:
            print(f"   Request {i+1}: Failed - {e}")

    if times:
        avg_time = statistics.mean(times)
        print(f"   Average: {avg_time:.1f}ms")
        return avg_time
    return None

async def main():
    """Main test function"""
    print("🧪 StillMe Gateway Performance Test")
    print("=" * 50)

    # Test direct backend
    direct_avg = await test_direct_backend()

    # Test gateway (if running)
    gateway_avg = await test_gateway()

    # Compare results
    print("\n📊 RESULTS:")
    print("=" * 50)

    if direct_avg:
        print(f"Direct Backend: {direct_avg:.1f}ms average")
    else:
        print("Direct Backend: Failed to test")

    if gateway_avg:
        print(f"Gateway:        {gateway_avg:.1f}ms average")

        if direct_avg:
            overhead = gateway_avg - direct_avg
            overhead_pct = (overhead / direct_avg) * 100
            print(f"Overhead:       {overhead:.1f}ms ({overhead_pct:+.1f}%)")

            if overhead < 100:
                print("✅ Gateway overhead is acceptable")
            else:
                print("⚠️  Gateway overhead is high")
    else:
        print("Gateway:        Not running or failed")
        print("\n💡 To start the gateway:")
        print("   python fastapi_gateway.py")

if __name__ == "__main__":
    asyncio.run(main())
