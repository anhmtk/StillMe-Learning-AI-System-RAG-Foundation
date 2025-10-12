#!/usr/bin/env python3
"""
Reflection Controller Test Runner
Trình chạy kiểm thử Reflection Controller

PURPOSE / MỤC ĐÍCH:
- Run comprehensive test suite for Reflection Controller
- Chạy bộ kiểm thử toàn diện cho Reflection Controller
- Generate test reports
- Tạo báo cáo kiểm thử
- Performance benchmarking
- Điểm chuẩn hiệu suất
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def run_tests():
    """Run all reflection controller tests / Chạy tất cả kiểm thử reflection controller"""
    print("🧪 Running Reflection Controller Test Suite...")
    print("🧪 Chạy bộ kiểm thử Reflection Controller...")

    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Test results
    test_results = {"timestamp": datetime.now().isoformat(), "tests": {}, "summary": {}}

    # Run unit tests
    print("\n📋 Running unit tests...")
    print("📋 Chạy kiểm thử đơn vị...")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_reflection_controller.py",
                "--timeout=60",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        test_results["tests"]["unit_tests"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

        if result.returncode == 0:
            print("✅ Unit tests passed")
            print("✅ Kiểm thử đơn vị đã qua")
        else:
            print("❌ Unit tests failed")
            print("❌ Kiểm thử đơn vị thất bại")
            print(f"Error: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("⏰ Unit tests timed out")
        print("⏰ Kiểm thử đơn vị hết thời gian")
        test_results["tests"]["unit_tests"] = {
            "returncode": -1,
            "stdout": "",
            "stderr": "Timeout after 300 seconds",
            "success": False,
        }
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        test_results["tests"]["unit_tests"] = {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
        }

    # Run integration tests
    print("\n🔗 Running integration tests...")
    print("🔗 Chạy kiểm thử tích hợp...")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_reflection_integration.py",
                "--timeout=120",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )

        test_results["tests"]["integration_tests"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

        if result.returncode == 0:
            print("✅ Integration tests passed")
            print("✅ Kiểm thử tích hợp đã qua")
        else:
            print("❌ Integration tests failed")
            print("❌ Kiểm thử tích hợp thất bại")
            print(f"Error: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("⏰ Integration tests timed out")
        print("⏰ Kiểm thử tích hợp hết thời gian")
        test_results["tests"]["integration_tests"] = {
            "returncode": -1,
            "stdout": "",
            "stderr": "Timeout after 600 seconds",
            "success": False,
        }
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        test_results["tests"]["integration_tests"] = {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
        }

    # Run smoke tests
    print("\n💨 Running smoke tests...")
    print("💨 Chạy kiểm thử smoke...")

    try:
        smoke_result = run_smoke_tests()
        test_results["tests"]["smoke_tests"] = smoke_result

        if smoke_result["success"]:
            print("✅ Smoke tests passed")
            print("✅ Kiểm thử smoke đã qua")
        else:
            print("❌ Smoke tests failed")
            print("❌ Kiểm thử smoke thất bại")

    except Exception as e:
        print(f"❌ Error running smoke tests: {e}")
        test_results["tests"]["smoke_tests"] = {"success": False, "error": str(e)}

    # Generate summary
    total_tests = len(test_results["tests"])
    passed_tests = sum(
        1 for test in test_results["tests"].values() if test.get("success", False)
    )

    test_results["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
    }

    # Save test results
    results_file = logs_dir / "reflection_test_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n📊 Test Summary / Tóm tắt kiểm thử:")
    print(f"📊 Total tests: {total_tests}")
    print(f"📊 Passed: {passed_tests}")
    print(f"📊 Failed: {total_tests - passed_tests}")
    print(f"📊 Success rate: {test_results['summary']['success_rate']:.1%}")

    print(f"\n📄 Detailed results saved to: {results_file}")
    print(f"📄 Kết quả chi tiết đã lưu vào: {results_file}")

    return test_results["summary"]["success_rate"] > 0.8


def run_smoke_tests():
    """Run smoke tests / Chạy kiểm thử smoke"""
    try:
        # Import components
        from stillme_core.reflection_controller import get_default_controller
        from stillme_core.reflection_scorer import get_default_scorer
        from stillme_core.secrecy_filter import get_default_filter

        # Test basic functionality
        controller = get_default_controller()
        scorer = get_default_scorer()
        filter_instance = get_default_filter()

        # Test should_reflect
        assert controller.should_reflect("Hello") is False
        assert controller.should_reflect("How to install Python?") is True

        # Test scoring
        result = scorer.score_response("Test response", "Test query")
        assert result.total_score >= 0.0

        # Test filtering
        filter_result = filter_instance.filter_content("Safe content", "Normal query")
        assert filter_result.is_safe is True

        return {"success": True, "message": "All smoke tests passed"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def run_performance_benchmarks():
    """Run performance benchmarks / Chạy điểm chuẩn hiệu suất"""
    print("\n⚡ Running performance benchmarks...")
    print("⚡ Chạy điểm chuẩn hiệu suất...")

    try:
        import asyncio

        from stillme_core.reflection_controller import get_default_controller

        controller = get_default_controller()

        # Benchmark queries
        benchmark_queries = [
            "How to install Python?",
            "What is machine learning?",
            "How to optimize code?",
            "Best practices for API design?",
            "How to debug Python?",
        ]

        # Run benchmarks
        start_time = time.time()

        async def run_benchmark():
            tasks = []
            for query in benchmark_queries:
                task = controller.enhance_response("Test response", query)
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            return results

        results = asyncio.run(run_benchmark())
        total_time = time.time() - start_time

        # Calculate metrics
        avg_time = total_time / len(benchmark_queries)
        total_improvements = sum(result.improvement for result in results)
        avg_improvement = total_improvements / len(results)

        benchmark_results = {
            "total_queries": len(benchmark_queries),
            "total_time": total_time,
            "avg_time_per_query": avg_time,
            "avg_improvement": avg_improvement,
            "success": True,
        }

        print("⚡ Benchmark Results / Kết quả điểm chuẩn:")
        print(f"⚡ Total queries: {len(benchmark_queries)}")
        print(f"⚡ Total time: {total_time:.2f}s")
        print(f"⚡ Average time per query: {avg_time:.2f}s")
        print(f"⚡ Average improvement: {avg_improvement:.3f}")

        return benchmark_results

    except Exception as e:
        print(f"❌ Error running benchmarks: {e}")
        return {"success": False, "error": str(e)}


def generate_test_report():
    """Generate comprehensive test report / Tạo báo cáo kiểm thử toàn diện"""
    print("\n📋 Generating test report...")
    print("📋 Tạo báo cáo kiểm thử...")

    # Read test results
    results_file = Path("logs/reflection_test_results.json")
    if not results_file.exists():
        print("❌ No test results found")
        return

    with open(results_file, encoding="utf-8") as f:
        test_results = json.load(f)

    # Generate report
    report = f"""
# Reflection Controller Test Report
# Báo cáo kiểm thử Reflection Controller

## Test Summary / Tóm tắt kiểm thử
- **Timestamp / Thời gian:** {test_results['timestamp']}
- **Total Tests / Tổng kiểm thử:** {test_results['summary']['total_tests']}
- **Passed / Đã qua:** {test_results['summary']['passed_tests']}
- **Failed / Thất bại:** {test_results['summary']['failed_tests']}
- **Success Rate / Tỷ lệ thành công:** {test_results['summary']['success_rate']:.1%}

## Test Details / Chi tiết kiểm thử
"""

    for test_name, test_result in test_results["tests"].items():
        status = "✅ PASSED" if test_result.get("success", False) else "❌ FAILED"
        report += f"\n### {test_name.replace('_', ' ').title()}\n"
        report += f"- **Status / Trạng thái:** {status}\n"

        if "returncode" in test_result:
            report += f"- **Return Code / Mã trả về:** {test_result['returncode']}\n"

        if test_result.get("stderr"):
            report += f"- **Error / Lỗi:** {test_result['stderr'][:200]}...\n"

    # Save report
    report_file = Path("reports/reflection_test_report.md")
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📄 Test report saved to: {report_file}")
    print(f"📄 Báo cáo kiểm thử đã lưu vào: {report_file}")


if __name__ == "__main__":
    print("🚀 Reflection Controller Test Runner")
    print("🚀 Trình chạy kiểm thử Reflection Controller")
    print("=" * 50)

    # Run tests
    success = run_tests()

    # Run benchmarks
    benchmark_results = run_performance_benchmarks()

    # Generate report
    generate_test_report()

    # Exit with appropriate code
    if success:
        print("\n🎉 All tests completed successfully!")
        print("🎉 Tất cả kiểm thử đã hoàn thành thành công!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        print("❌ Một số kiểm thử thất bại!")
        sys.exit(1)
