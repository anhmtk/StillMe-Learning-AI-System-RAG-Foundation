#!/usr/bin/env python3
"""
PHA 2 - Spec Proposal cho AgentDev interface
"""

import json


def create_spec_proposal():
    """Tạo spec proposal dựa trên bằng chứng từ PHA 1"""

    spec_methods = [
        {
            "name": "execute_task",
            "params": ["task", "mode=None"],
            "returns": "dict",
            "description": "Execute a task with optional mode parameter",
        },
        {
            "name": "run_session",
            "params": ["mode='critical-first'"],
            "returns": "dict",
            "description": "Run a complete AgentDev session",
        },
    ]

    helper_modules = ["advanced_fixer", "pattern_fixes", "symbol_index"]

    return {"spec_methods": spec_methods, "helper_modules": helper_modules}


if __name__ == "__main__":
    result = create_spec_proposal()
    print(json.dumps(result, indent=2))
