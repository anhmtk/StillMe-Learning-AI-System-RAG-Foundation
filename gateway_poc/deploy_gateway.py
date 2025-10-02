#!/usr/bin/env python3
"""
StillMe Gateway Deployment Script
Author: StillMe AI Assistant
Date: 2025-09-22

Quick deployment and testing of optimized gateway
"""

import asyncio
import subprocess
import sys
import time

import aiohttp


class GatewayDeployer:
    """Deploy and test StillMe Gateway"""

    def __init__(self):
        self.gateway_url = "http://localhost:8080"
        self.stillme_url = "http://localhost:1216"
        self.ollama_url = "http://localhost:11434"

    async def deploy_gateway(self):
        """Deploy FastAPI Gateway"""
        print("🚀 Deploying StillMe FastAPI Gateway...")

        try:
            # Start the gateway
            subprocess.Popen([
                sys.executable, "fastapi_gateway.py"
            ])

            # Wait for startup
            await asyncio.sleep(5)

            # Test health endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gateway_url}/health") as response:
                    if response.status == 200:
                        print("✅ Gateway deployed successfully")
                        return True
                    else:
                        print(f"❌ Gateway health check failed: {response.status}")
                        return False

        except Exception as e:
            print(f"❌ Gateway deployment failed: {e}")
            return False

    async def test_latency_comparison(self):
        """Compare latency between direct and gateway"""
        print("\n📊 Testing Latency Comparison...")

        test_message = "Hello, this is a latency test"

        # Test direct StillMe backend
        direct_times = []
        for i in range(5):
            start_time = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.stillme_url}/chat",
                        json={"message": f"{test_message} {i}"},
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            direct_times.append((time.time() - start_time) * 1000)
            except Exception as e:
                print(f"Direct request {i} failed: {e}")

        # Test through gateway
        gateway_times = []
        for i in range(5):
            start_time = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.gateway_url}/api/chat",
                        json={
                            "message": f"{test_message} {i}",
                            "user_id": "test_user",
                            "use_cache": True
                        },
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            gateway_times.append((time.time() - start_time) * 1000)
            except Exception as e:
                print(f"Gateway request {i} failed: {e}")

        # Calculate averages
        if direct_times and gateway_times:
            direct_avg = sum(direct_times) / len(direct_times)
            gateway_avg = sum(gateway_times) / len(gateway_times)
            overhead = gateway_avg - direct_avg
            overhead_pct = (overhead / direct_avg) * 100 if direct_avg > 0 else 0

            print("📈 LATENCY RESULTS:")
            print(f"   Direct Backend: {direct_avg:.1f}ms average")
            print(f"   Gateway:        {gateway_avg:.1f}ms average")
            print(f"   Overhead:       {overhead:.1f}ms ({overhead_pct:+.1f}%)")

            if overhead < 50:  # Less than 50ms overhead
                print("✅ Gateway overhead is acceptable")
            else:
                print("⚠️  Gateway overhead is high, needs optimization")
        else:
            print("❌ Could not complete latency test")

    async def test_cache_effectiveness(self):
        """Test cache effectiveness"""
        print("\n💾 Testing Cache Effectiveness...")

        message = "Cache test message"

        # First request (cache miss)
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.gateway_url}/api/chat",
                    json={
                        "message": message,
                        "user_id": "cache_test",
                        "use_cache": True
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        cache_miss_time = (time.time() - start_time) * 1000
                        print(f"   Cache Miss: {cache_miss_time:.1f}ms")
        except Exception as e:
            print(f"Cache miss test failed: {e}")
            return

        # Second request (cache hit)
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.gateway_url}/api/chat",
                    json={
                        "message": message,
                        "user_id": "cache_test",
                        "use_cache": True
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        cache_hit_time = (time.time() - start_time) * 1000
                        improvement = cache_miss_time - cache_hit_time
                        improvement_pct = (improvement / cache_miss_time) * 100

                        print(f"   Cache Hit:  {cache_hit_time:.1f}ms")
                        print(f"   Improvement: {improvement:.1f}ms ({improvement_pct:.1f}% faster)")

                        if improvement > 100:  # More than 100ms improvement
                            print("✅ Cache is working effectively")
                        else:
                            print("⚠️  Cache improvement is minimal")
        except Exception as e:
            print(f"Cache hit test failed: {e}")

    async def test_health_checks(self):
        """Test health check endpoints"""
        print("\n🏥 Testing Health Checks...")

        endpoints = [
            ("Gateway Health", f"{self.gateway_url}/health"),
            ("StillMe Backend", f"{self.stillme_url}/health"),
            ("Ollama Backend", f"{self.ollama_url}/api/tags")
        ]

        for name, url in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            print(f"   ✅ {name}: Healthy")
                        else:
                            print(f"   ❌ {name}: Unhealthy ({response.status})")
            except Exception as e:
                print(f"   ❌ {name}: Error - {e}")

    async def get_metrics(self):
        """Get gateway metrics"""
        print("\n📊 Gateway Metrics:")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gateway_url}/api/metrics") as response:
                    if response.status == 200:
                        metrics = await response.json()
                        print(f"   Total Requests: {metrics.get('total_requests', 0)}")
                        print(f"   Recent Requests: {metrics.get('recent_requests', 0)}")
                        print(f"   Avg Latency: {metrics.get('avg_latency_ms', 0):.1f}ms")
                        print(f"   Cache Hit Rate: {metrics.get('cache_hit_rate', 0):.1%}")
                    else:
                        print("   ❌ Could not retrieve metrics")
        except Exception as e:
            print(f"   ❌ Metrics error: {e}")

    async def run_full_test(self):
        """Run complete test suite"""
        print("🧪 StillMe Gateway - Full Test Suite")
        print("=" * 50)

        # Deploy gateway
        if not await self.deploy_gateway():
            print("❌ Gateway deployment failed, aborting tests")
            return

        # Run tests
        await self.test_health_checks()
        await self.test_latency_comparison()
        await self.test_cache_effectiveness()
        await self.get_metrics()

        print("\n" + "=" * 50)
        print("✅ Test suite completed!")

async def main():
    """Main function"""
    deployer = GatewayDeployer()
    await deployer.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())
