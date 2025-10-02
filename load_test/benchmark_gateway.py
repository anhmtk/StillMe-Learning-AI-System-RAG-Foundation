#!/usr/bin/env python3
"""
StillMe Gateway Performance Benchmark
Author: StillMe AI Assistant
Date: 2025-09-22

Tests:
- Latency comparison (with/without gateway)
- Throughput testing
- Error rate analysis
- Cache effectiveness
"""

import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    endpoint: str
    latency_ms: float
    status_code: int
    response_size: int
    timestamp: float

class GatewayBenchmark:
    """Comprehensive benchmark for StillMe Gateway"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.gateway_url = "http://localhost:8080"
        self.direct_urls = {
            "stillme": "http://localhost:1216",
            "ollama": "http://localhost:11434"
        }

    async def run_benchmark(self):
        """Run complete benchmark suite"""
        logger.info("🚀 Starting StillMe Gateway Benchmark")

        # Test scenarios
        scenarios = [
            ("Chat API - Gateway", self.test_chat_gateway),
            ("Chat API - Direct", self.test_chat_direct),
            ("Ollama API - Gateway", self.test_ollama_gateway),
            ("Ollama API - Direct", self.test_ollama_direct),
            ("Health Check - Gateway", self.test_health_gateway),
            ("Concurrent Load Test", self.test_concurrent_load),
            ("Cache Effectiveness", self.test_cache_effectiveness),
        ]

        for name, test_func in scenarios:
            logger.info(f"📊 Running: {name}")
            try:
                await test_func()
            except Exception as e:
                logger.error(f"❌ {name} failed: {e}")

        # Generate report
        self.generate_report()

    async def test_chat_gateway(self, num_requests: int = 50):
        """Test chat endpoint through gateway"""
        async with aiohttp.ClientSession() as session:
            for i in range(num_requests):
                start_time = time.time()

                payload = {
                    "message": f"Test message {i}",
                    "user_id": "benchmark_user",
                    "use_cache": True
                }

                try:
                    async with session.post(
                        f"{self.gateway_url}/api/chat",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        latency = (time.time() - start_time) * 1000
                        response_text = await response.text()

                        self.results.append(TestResult(
                            endpoint="chat_gateway",
                            latency_ms=latency,
                            status_code=response.status,
                            response_size=len(response_text),
                            timestamp=time.time()
                        ))

                except Exception as e:
                    logger.warning(f"Chat gateway request {i} failed: {e}")

    async def test_chat_direct(self, num_requests: int = 50):
        """Test chat endpoint directly"""
        async with aiohttp.ClientSession() as session:
            for i in range(num_requests):
                start_time = time.time()

                payload = {
                    "message": f"Test message {i}",
                    "user_id": "benchmark_user"
                }

                try:
                    async with session.post(
                        f"{self.direct_urls['stillme']}/chat",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        latency = (time.time() - start_time) * 1000
                        response_text = await response.text()

                        self.results.append(TestResult(
                            endpoint="chat_direct",
                            latency_ms=latency,
                            status_code=response.status,
                            response_size=len(response_text),
                            timestamp=time.time()
                        ))

                except Exception as e:
                    logger.warning(f"Chat direct request {i} failed: {e}")

    async def test_ollama_gateway(self, num_requests: int = 20):
        """Test Ollama endpoint through gateway"""
        async with aiohttp.ClientSession() as session:
            for i in range(num_requests):
                start_time = time.time()

                payload = {
                    "model": "gemma2:2b",
                    "prompt": f"Hello, this is test {i}",
                    "stream": False
                }

                try:
                    async with session.post(
                        f"{self.gateway_url}/api/ollama",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        latency = (time.time() - start_time) * 1000
                        response_text = await response.text()

                        self.results.append(TestResult(
                            endpoint="ollama_gateway",
                            latency_ms=latency,
                            status_code=response.status,
                            response_size=len(response_text),
                            timestamp=time.time()
                        ))

                except Exception as e:
                    logger.warning(f"Ollama gateway request {i} failed: {e}")

    async def test_ollama_direct(self, num_requests: int = 20):
        """Test Ollama endpoint directly"""
        async with aiohttp.ClientSession() as session:
            for i in range(num_requests):
                start_time = time.time()

                payload = {
                    "model": "gemma2:2b",
                    "prompt": f"Hello, this is test {i}",
                    "stream": False
                }

                try:
                    async with session.post(
                        f"{self.direct_urls['ollama']}/api/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        latency = (time.time() - start_time) * 1000
                        response_text = await response.text()

                        self.results.append(TestResult(
                            endpoint="ollama_direct",
                            latency_ms=latency,
                            status_code=response.status,
                            response_size=len(response_text),
                            timestamp=time.time()
                        ))

                except Exception as e:
                    logger.warning(f"Ollama direct request {i} failed: {e}")

    async def test_health_gateway(self, num_requests: int = 100):
        """Test health endpoint through gateway"""
        async with aiohttp.ClientSession() as session:
            for i in range(num_requests):
                start_time = time.time()

                try:
                    async with session.get(
                        f"{self.gateway_url}/health",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        latency = (time.time() - start_time) * 1000
                        response_text = await response.text()

                        self.results.append(TestResult(
                            endpoint="health_gateway",
                            latency_ms=latency,
                            status_code=response.status,
                            response_size=len(response_text),
                            timestamp=time.time()
                        ))

                except Exception as e:
                    logger.warning(f"Health gateway request {i} failed: {e}")

    async def test_concurrent_load(self, num_requests: int = 100, concurrency: int = 10):
        """Test concurrent load handling"""
        semaphore = asyncio.Semaphore(concurrency)

        async def make_request(i: int):
            async with semaphore:
                start_time = time.time()

                payload = {
                    "message": f"Concurrent test {i}",
                    "user_id": "load_test_user",
                    "use_cache": True
                }

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.gateway_url}/api/chat",
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            latency = (time.time() - start_time) * 1000
                            response_text = await response.text()

                            self.results.append(TestResult(
                                endpoint="concurrent_load",
                                latency_ms=latency,
                                status_code=response.status,
                                response_size=len(response_text),
                                timestamp=time.time()
                            ))

                except Exception as e:
                    logger.warning(f"Concurrent request {i} failed: {e}")

        # Run concurrent requests
        tasks = [make_request(i) for i in range(num_requests)]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def test_cache_effectiveness(self, num_requests: int = 20):
        """Test cache effectiveness with repeated requests"""
        message = "Cache test message"

        async with aiohttp.ClientSession() as session:
            # First request (cache miss)
            start_time = time.time()
            payload = {
                "message": message,
                "user_id": "cache_test_user",
                "use_cache": True
            }

            try:
                async with session.post(
                    f"{self.gateway_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    latency = (time.time() - start_time) * 1000
                    response_text = await response.text()

                    self.results.append(TestResult(
                        endpoint="cache_miss",
                        latency_ms=latency,
                        status_code=response.status,
                        response_size=len(response_text),
                        timestamp=time.time()
                    ))

            except Exception as e:
                logger.warning(f"Cache miss request failed: {e}")

            # Subsequent requests (cache hits)
            for i in range(num_requests - 1):
                start_time = time.time()

                try:
                    async with session.post(
                        f"{self.gateway_url}/api/chat",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        latency = (time.time() - start_time) * 1000
                        response_text = await response.text()

                        self.results.append(TestResult(
                            endpoint="cache_hit",
                            latency_ms=latency,
                            status_code=response.status,
                            response_size=len(response_text),
                            timestamp=time.time()
                        ))

                except Exception as e:
                    logger.warning(f"Cache hit request {i} failed: {e}")

    def generate_report(self):
        """Generate comprehensive performance report"""
        logger.info("📊 Generating Performance Report")

        # Group results by endpoint
        endpoint_results = {}
        for result in self.results:
            if result.endpoint not in endpoint_results:
                endpoint_results[result.endpoint] = []
            endpoint_results[result.endpoint].append(result)

        # Calculate statistics
        report = {
            "summary": {
                "total_requests": len(self.results),
                "successful_requests": len([r for r in self.results if r.status_code == 200]),
                "failed_requests": len([r for r in self.results if r.status_code != 200]),
                "success_rate": len([r for r in self.results if r.status_code == 200]) / len(self.results) * 100 if self.results else 0
            },
            "endpoints": {}
        }

        for endpoint, results in endpoint_results.items():
            if not results:
                continue

            latencies = [r.latency_ms for r in results]
            successful_results = [r for r in results if r.status_code == 200]

            report["endpoints"][endpoint] = {
                "total_requests": len(results),
                "successful_requests": len(successful_results),
                "success_rate": len(successful_results) / len(results) * 100,
                "latency_stats": {
                    "min_ms": min(latencies),
                    "max_ms": max(latencies),
                    "avg_ms": statistics.mean(latencies),
                    "median_ms": statistics.median(latencies),
                    "p95_ms": self._percentile(latencies, 95),
                    "p99_ms": self._percentile(latencies, 99)
                },
                "response_size": {
                    "avg_bytes": statistics.mean([r.response_size for r in results]),
                    "total_bytes": sum([r.response_size for r in results])
                }
            }

        # Save report
        with open("load_test/benchmark_report.json", "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        self._print_summary(report)

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _print_summary(self, report: Dict[str, Any]):
        """Print performance summary"""
        print("\n" + "="*80)
        print("🚀 STILLME GATEWAY PERFORMANCE BENCHMARK REPORT")
        print("="*80)

        summary = report["summary"]
        print(f"📊 Total Requests: {summary['total_requests']}")
        print(f"✅ Successful: {summary['successful_requests']}")
        print(f"❌ Failed: {summary['failed_requests']}")
        print(f"📈 Success Rate: {summary['success_rate']:.2f}%")

        print("\n📊 ENDPOINT PERFORMANCE:")
        print("-" * 80)

        for endpoint, stats in report["endpoints"].items():
            print(f"\n🔗 {endpoint.upper()}:")
            print(f"   Requests: {stats['total_requests']} (Success: {stats['success_rate']:.1f}%)")

            latency = stats["latency_stats"]
            print(f"   Latency: Avg={latency['avg_ms']:.1f}ms, P95={latency['p95_ms']:.1f}ms, P99={latency['p99_ms']:.1f}ms")
            print(f"   Response Size: {stats['response_size']['avg_bytes']:.0f} bytes avg")

        # Latency comparison
        print("\n⚡ LATENCY COMPARISON:")
        print("-" * 80)

        if "chat_gateway" in report["endpoints"] and "chat_direct" in report["endpoints"]:
            gateway_avg = report["endpoints"]["chat_gateway"]["latency_stats"]["avg_ms"]
            direct_avg = report["endpoints"]["chat_direct"]["latency_stats"]["avg_ms"]
            overhead = gateway_avg - direct_avg
            overhead_pct = (overhead / direct_avg) * 100 if direct_avg > 0 else 0

            print(f"Chat API - Gateway: {gateway_avg:.1f}ms")
            print(f"Chat API - Direct:  {direct_avg:.1f}ms")
            print(f"Gateway Overhead:   {overhead:.1f}ms ({overhead_pct:+.1f}%)")

        if "ollama_gateway" in report["endpoints"] and "ollama_direct" in report["endpoints"]:
            gateway_avg = report["endpoints"]["ollama_gateway"]["latency_stats"]["avg_ms"]
            direct_avg = report["endpoints"]["ollama_direct"]["latency_stats"]["avg_ms"]
            overhead = gateway_avg - direct_avg
            overhead_pct = (overhead / direct_avg) * 100 if direct_avg > 0 else 0

            print(f"Ollama API - Gateway: {gateway_avg:.1f}ms")
            print(f"Ollama API - Direct:  {direct_avg:.1f}ms")
            print(f"Gateway Overhead:     {overhead:.1f}ms ({overhead_pct:+.1f}%)")

        # Cache effectiveness
        if "cache_miss" in report["endpoints"] and "cache_hit" in report["endpoints"]:
            miss_avg = report["endpoints"]["cache_miss"]["latency_stats"]["avg_ms"]
            hit_avg = report["endpoints"]["cache_hit"]["latency_stats"]["avg_ms"]
            improvement = miss_avg - hit_avg
            improvement_pct = (improvement / miss_avg) * 100 if miss_avg > 0 else 0

            print("\n💾 CACHE EFFECTIVENESS:")
            print(f"Cache Miss: {miss_avg:.1f}ms")
            print(f"Cache Hit:  {hit_avg:.1f}ms")
            print(f"Improvement: {improvement:.1f}ms ({improvement_pct:.1f}% faster)")

        print("\n" + "="*80)

async def main():
    """Main benchmark function"""
    benchmark = GatewayBenchmark()
    await benchmark.run_benchmark()

if __name__ == "__main__":
    asyncio.run(main())
