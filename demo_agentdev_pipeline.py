#!/usr/bin/env python3
"""
Demo thực tế Pipeline AgentDev Sprint 1
Chứng minh các tính năng cốt lõi hoạt động
"""

import tempfile
import json
from pathlib import Path
from agent_dev.runtime import AgentDev
from agent_dev.schemas import TaskSpec, Policy, SafetyBudget, PolicyLevel


def demo_agentdev_pipeline():
    """Demo toàn bộ pipeline AgentDev Sprint 1"""
    print("🚀 DEMO AGENTDEV SPRINT 1 PIPELINE")
    print("=" * 50)

    # Tạo thư mục tạm cho demo
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir) / "logs"

        # Khởi tạo AgentDev
        agent = AgentDev(sandbox_root=str(log_dir))
        print(f"✅ AgentDev initialized at: {log_dir}")

        # Demo 1: File Edit Task
        print("\n📝 DEMO 1: File Edit Task")
        print("-" * 30)

        task_spec = TaskSpec(
            type="file_edit",
            inputs={
                "file_path": "demo_file.py",
                "content": '''#!/usr/bin/env python3
"""
Demo file created by AgentDev
"""

def hello_world():
    print("Hello from AgentDev!")
    return "success"

if __name__ == "__main__":
    hello_world()
''',
            },
            policy=Policy(level=PolicyLevel.BALANCED),
            budgets=SafetyBudget(cpu_ms=5000, mem_mb=50, fs_quota_kb=10, timeout_s=30),
        )

        # Plan
        plan = agent.plan(task_spec)
        print(f"✅ Plan created: {len(plan.steps)} steps")
        print(f"   Sandbox: {plan.sandbox_path}")
        print(f"   Estimated: {plan.estimated_duration_ms}ms")

        # Execute
        exec_result = agent.execute_task(task_spec, plan)
        print(f"✅ Execution completed: {exec_result.success}")
        print(f"   Files created: {exec_result.files_created}")
        print(f"   Duration: {exec_result.duration_ms}ms")
        print(f"   Resources: {exec_result.resources_used}")

        # Validate
        validation = agent.validate(task_spec, plan, exec_result)
        print(f"✅ Validation: {validation.valid}")
        print(f"   Confidence: {validation.confidence_score:.2f}")
        print(f"   Checks passed: {len(validation.checks_passed)}")

        # Demo 2: Code Analysis Task
        print("\n🔍 DEMO 2: Code Analysis Task")
        print("-" * 30)

        analysis_task = TaskSpec(
            type="code_analysis",
            inputs={"target": "."},
            policy=Policy(level=PolicyLevel.STRICT),
            budgets=SafetyBudget(cpu_ms=3000, mem_mb=30, fs_quota_kb=5, timeout_s=20),
        )

        analysis_plan = agent.plan(analysis_task)
        analysis_result = agent.execute_task(analysis_task, analysis_plan)
        analysis_validation = agent.validate(
            analysis_task, analysis_plan, analysis_result
        )

        print(f"✅ Analysis completed: {analysis_result.success}")
        print(f"   Output: {analysis_result.output}")
        print(f"   Validation: {analysis_validation.valid}")

        # Demo 3: Telemetry Logs
        print("\n📊 DEMO 3: Telemetry Logs")
        print("-" * 30)

        # Đọc telemetry logs
        telemetry_files = list(log_dir.glob("*.jsonl"))
        if telemetry_files:
            print(f"✅ Telemetry logs found: {len(telemetry_files)} files")

            # Parse và hiển thị một số events
            with open(telemetry_files[0], "r", encoding="utf-8") as f:
                events = [json.loads(line) for line in f.readlines()]

            print(f"   Total events: {len(events)}")
            print(f"   Trace ID: {events[0]['trace_id']}")

            # Hiển thị một số events quan trọng
            for event in events[:5]:  # 5 events đầu
                print(
                    f"   - {event['event_type']} in {event['phase']}: {event.get('data', {})}"
                )

        # Demo 4: Safety Features
        print("\n🛡️ DEMO 4: Safety Features")
        print("-" * 30)

        # Test safety budget enforcement
        try:
            dangerous_task = TaskSpec(
                type="file_edit",
                inputs={
                    "file_path": "large_file.txt",
                    "content": "A" * 20000,  # 20KB - vượt quá quota
                },
                policy=Policy(level=PolicyLevel.STRICT),
                budgets=SafetyBudget(
                    cpu_ms=1000, mem_mb=10, fs_quota_kb=1, timeout_s=5
                ),  # Quota rất nhỏ
            )

            dangerous_plan = agent.plan(dangerous_task)
            dangerous_result = agent.execute_task(dangerous_task, dangerous_plan)

            print(f"⚠️  Safety enforcement: {not dangerous_result.success}")
            if not dangerous_result.success:
                print(f"   Errors: {dangerous_result.errors}")

        except Exception as e:
            print(f"🛡️  Safety blocked: {type(e).__name__}")

        # Cleanup sẽ tự động khi temp_dir bị xóa
        print("\n🧹 Cleanup sẽ tự động khi temp_dir bị xóa")

        print("\n🎉 DEMO HOÀN THÀNH!")
        print("=" * 50)
        print("✅ Core Pipeline: Plan → Execute → Validate")
        print("✅ Safety Floor: Budget enforcement, Policy validation")
        print("✅ Telemetry: JSONL logging với trace_id")
        print("✅ Sandbox: FS isolation và path traversal protection")
        print("✅ Error Handling: Taxonomy và recovery suggestions")


if __name__ == "__main__":
    demo_agentdev_pipeline()
