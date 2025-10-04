#!/usr/bin/env python3
"""
Stress Test for AgentDev Phase 4
=================================

Concurrent stress test with 100 tasks including rule violations and valid tasks.
"""

import json
import os
import random
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from agent_dev.core.agentdev import AgentDev


class StressTestPhase4:
    """Stress test for AgentDev Phase 4 persistent capabilities"""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "stress_test.db")
        self.agent = AgentDev(db_path=self.db_path)
        self.results: list[dict[str, Any]] = []

    def cleanup(self):
        """Clean up temporary resources"""
        try:
            if hasattr(self.agent, "session"):
                self.agent.session.close()
            if hasattr(self.agent, "engine"):
                self.agent.engine.dispose()
            os.remove(self.db_path)
            os.rmdir(self.temp_dir)
        except Exception as e:
            print(f"Cleanup warning: {e}")

    def generate_task(self, task_id: int) -> dict[str, Any]:
        """Generate a test task"""
        task_types = [
            # Valid tasks (should PASS)
            ("fix_bug", "development", "PASS"),
            ("optimize_code", "development", "PASS"),
            ("refactor_module", "development", "PASS"),
            ("add_tests", "development", "PASS"),
            ("update_docs", "development", "PASS"),
            # Rule violation tasks (should BLOCK)
            ("claim", "production", "BLOCK"),  # test_before_claim rule
            ("claim", "development", "BLOCK"),  # test_before_claim rule
            ("rm -rf /tmp/*", "production", "BLOCK"),  # forbid_dangerous_shell rule
            ("rm -rf /", "production", "BLOCK"),  # forbid_dangerous_shell rule
            (
                "sudo rm -rf /var/log/*",
                "production",
                "BLOCK",
            ),  # forbid_dangerous_shell rule
        ]

        task, mode, expected = random.choice(task_types)
        return {"task_id": task_id, "task": task, "mode": mode, "expected": expected}

    def execute_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a single task and measure performance"""
        start_time = time.time()

        try:
            # Execute task
            result = self.agent.execute(task_data["task"], mode=task_data["mode"])

            # Determine classification
            if "BLOCKED" in result or "BLOCK" in result:
                classification = "BLOCK"
            elif "completed" in result or "success" in result:
                classification = "PASS"
            else:
                classification = "FAIL"

            # Record feedback (randomly)
            if random.random() < 0.3:  # 30% chance of feedback
                feedback_types = [
                    "Great work!",
                    "The system is slow",
                    "There was an error",
                    "Security issue detected",
                    "General feedback",
                ]
                feedback = random.choice(feedback_types)
                self.agent.receive_feedback(f"user_{task_data['task_id']}", feedback)

        except Exception as e:
            classification = "FAIL"
            result = f"Exception: {str(e)}"

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        return {
            "task_id": task_data["task_id"],
            "input_summary": f"{task_data['task']} (mode: {task_data['mode']})",
            "classification": classification,
            "latency_ms": round(latency_ms, 2),
            "result": result[:100] if len(result) > 100 else result,
            "expected": task_data["expected"],
        }

    def run_stress_test(
        self, num_tasks: int = 100, max_workers: int = 10
    ) -> dict[str, Any]:
        """Run concurrent stress test"""
        print(f"Starting stress test with {num_tasks} tasks, {max_workers} workers...")

        # Generate tasks
        tasks = [self.generate_task(i) for i in range(num_tasks)]

        # Execute tasks concurrently
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.execute_task, task): task for task in tasks
            }

            # Collect results as they complete
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception as e:
                    task = future_to_task[future]
                    self.results.append(
                        {
                            "task_id": task["task_id"],
                            "input_summary": f"{task['task']} (mode: {task['mode']})",
                            "classification": "FAIL",
                            "latency_ms": 0.0,
                            "result": f"Execution error: {str(e)}",
                            "expected": task["expected"],
                        }
                    )

        end_time = time.time()
        total_time = end_time - start_time

        # Calculate statistics
        classifications = [r["classification"] for r in self.results]
        latencies = [r["latency_ms"] for r in self.results]

        stats = {
            "total_tasks": num_tasks,
            "total_time_seconds": round(total_time, 2),
            "tasks_per_second": round(num_tasks / total_time, 2),
            "classifications": {
                "PASS": classifications.count("PASS"),
                "FAIL": classifications.count("FAIL"),
                "BLOCK": classifications.count("BLOCK"),
            },
            "latency_stats": {
                "avg_ms": round(sum(latencies) / len(latencies), 2),
                "min_ms": round(min(latencies), 2),
                "max_ms": round(max(latencies), 2),
            },
            "concurrency_evidence": {
                "max_workers": max_workers,
                "concurrent_execution": True,
                "thread_pool_used": True,
            },
        }

        return stats

    def get_detailed_results(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get detailed results for first N tasks"""
        return self.results[:limit]


def main():
    """Run stress test and output results"""
    stress_test = StressTestPhase4()

    try:
        # Run stress test
        stats = stress_test.run_stress_test(num_tasks=100, max_workers=10)

        # Get detailed results for first 20 tasks
        detailed_results = stress_test.get_detailed_results(20)

        # Output results
        print("\n" + "=" * 50)
        print("STRESS TEST RESULTS")
        print("=" * 50)

        print("\nOverall Statistics:")
        print(f"Total tasks: {stats['total_tasks']}")
        print(f"Total time: {stats['total_time_seconds']}s")
        print(f"Tasks/second: {stats['tasks_per_second']}")

        print("\nClassification Results:")
        for classification, count in stats["classifications"].items():
            print(f"  {classification}: {count}")

        print("\nLatency Statistics:")
        print(f"  Average: {stats['latency_stats']['avg_ms']}ms")
        print(f"  Min: {stats['latency_stats']['min_ms']}ms")
        print(f"  Max: {stats['latency_stats']['max_ms']}ms")

        print("\nConcurrency Evidence:")
        print(f"  Max workers: {stats['concurrency_evidence']['max_workers']}")
        print(
            f"  Concurrent execution: {stats['concurrency_evidence']['concurrent_execution']}"
        )
        print(
            f"  Thread pool used: {stats['concurrency_evidence']['thread_pool_used']}"
        )

        # Save detailed results to JSON
        output_data = {"statistics": stats, "detailed_results": detailed_results}

        with open("stress_tasks.json", "w") as f:
            json.dump(output_data, f, indent=2)

        print("\nDetailed results saved to stress_tasks.json")
        print(f"First {len(detailed_results)} task details:")
        for result in detailed_results:
            print(
                f"  Task {result['task_id']}: {result['input_summary']} -> {result['classification']} ({result['latency_ms']}ms)"
            )

    finally:
        stress_test.cleanup()


if __name__ == "__main__":
    main()
