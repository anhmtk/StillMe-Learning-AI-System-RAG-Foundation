#!/usr/bin/env python3
"""
PHA 1 - Thu thập bằng chứng cho AgentDev interface
"""

import os
import re
from pathlib import Path


def analyze_agentdev_interface():
    """Phân tích usages của AgentDev để suy luận interface"""

    # Tìm tất cả Python files
    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv', 'env', 'artifacts', 'reports', 'dist', 'build', 'agentdev_backups']]

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    # Patterns để tìm AgentDev usages
    patterns = [
        r'AgentDev\(',
        r'\.execute_task\(',
        r'\.run_session\(',
        r'\.scan_errors\(',
        r'\.apply_fixes\(',
        r'\.schedule_job\(',
        r'\.execute_workflow\(',
        r'agentdev\.execute_task',
        r'agentdev\.run_session',
        r'agentdev\.scan_errors',
        r'agentdev\.apply_fixes'
    ]

    usages = []

    for file_path in python_files:
        try:
            with open(file_path, encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Lấy 3 dòng context
                        start_line = max(0, line_num - 2)
                        end_line = min(len(lines), line_num + 1)
                        context_lines = []

                        for i in range(start_line, end_line):
                            line_content = lines[i].rstrip()
                            prefix = "+" if i == line_num - 1 else "-"
                            context_lines.append(f"{prefix}{i+1}:{line_content}")

                        # Xác định symbol
                        symbol = "AgentDev" if "AgentDev(" in line else pattern.replace(r'\.', '').replace(r'\(', '')

                        usages.append({
                            "file": file_path,
                            "line": line_num,
                            "context": context_lines,
                            "symbol": symbol
                        })

        except Exception as e:
            continue

    # Suy luận spec từ usages
    spec_methods = []
    method_evidence = {}

    for usage in usages:
        symbol = usage["symbol"]
        if symbol != "AgentDev":
            if symbol not in method_evidence:
                method_evidence[symbol] = []
            method_evidence[symbol].append(usage)

    # Phân tích từng method
    for method_name, method_usages in method_evidence.items():
        # Suy luận params và returns từ context
        params = []
        returns = "Unknown"
        confidence = 0.5

        for usage in method_usages:
            context_text = '\n'.join(usage["context"])

            # Tìm params
            if "task" in context_text.lower():
                params.append("task")
            if "context" in context_text.lower():
                params.append("context?")
            if "timeout" in context_text.lower():
                params.append("timeout?")
            if "mode" in context_text.lower():
                params.append("mode?")
            if "max_iters" in context_text.lower():
                params.append("max_iters?")

            # Tìm returns
            if "TaskResult" in context_text:
                returns = "TaskResult"
                confidence = 0.8
            elif "SessionReport" in context_text:
                returns = "SessionReport"
                confidence = 0.8
            elif "assert" in context_text and "result" in context_text:
                returns = "dict|bool"
                confidence = 0.7
            elif "result" in context_text:
                returns = "dict|bool|None"
                confidence = 0.6

        # Tăng confidence dựa trên số usage
        confidence = min(0.9, confidence + (len(method_usages) * 0.1))

        spec_methods.append({
            "name": method_name,
            "params": params if params else ["..."],
            "returns": returns,
            "confidence": confidence
        })

    # Tìm first blocker
    first_blocker = None
    for usage in usages:
        if usage["symbol"] == "execute_task" and "integration/test_workflows.py" in usage["file"]:
            first_blocker = {
                "file": usage["file"],
                "line": usage["line"],
                "symbol": usage["symbol"]
            }
            break

    # Tính confidence tổng thể
    total_confidence = 0.8 if spec_methods else 0.1

    return {
        "agentdev_usages": usages,
        "spec_minimal": {
            "class": "AgentDev",
            "methods": spec_methods,
            "confidence": total_confidence
        },
        "first_blocker": first_blocker
    }

if __name__ == "__main__":
    import json
    result = analyze_agentdev_interface()
    print(json.dumps(result, indent=2))
