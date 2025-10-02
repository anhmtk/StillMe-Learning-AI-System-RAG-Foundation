#!/usr/bin/env python3
"""
StillMe CI Check - Skip Not Cancel
Kiểm tra Skip behavior không gọi cancel()

Purpose: CI check để đảm bảo Skip = Diagnose, không phải Cancel
Usage: python ci/check_skip_not_cancel.py
"""

import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml


def load_interaction_policy() -> dict[str, Any]:
    """Load INTERACTION_POLICY.yaml policy"""
    policy_path = Path("policies/INTERACTION_POLICY.yaml")

    if not policy_path.exists():
        print("❌ INTERACTION_POLICY.yaml not found")
        sys.exit(1)

    try:
        with open(policy_path, encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load policy: {e}")
        sys.exit(1)

def find_skip_handlers() -> list[tuple[str, int, str]]:
    """Find all Skip button handlers in code"""
    skip_handlers = []

    # Search patterns for Skip handlers
    patterns = [
        r'onSkip\s*[:=]\s*',
        r'on_skip\s*[:=]\s*',
        r'handleSkip\s*[:=]\s*',
        r'handle_skip\s*[:=]\s*',
        r'@skip\s*',
        r'@on_skip\s*',
        r'Skip\s*[:=]\s*',
        r'skip\s*[:=]\s*'
    ]

    # File extensions to search
    extensions = ['.py', '.ts', '.tsx', '.js', '.jsx', '.dart']

    for root, _dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip_dir in root for skip_dir in ['.git', '__pycache__', 'node_modules', '.venv']):
            continue

        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, encoding='utf-8') as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, 1):
                        for pattern in patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                skip_handlers.append((file_path, line_num, line.strip()))

                except Exception:
                    continue  # Skip files that can't be read

    return skip_handlers

def find_cancel_calls() -> list[tuple[str, int, str]]:
    """Find all cancel() calls in code"""
    cancel_calls = []

    # Search patterns for cancel calls
    patterns = [
        r'\.cancel\s*\(',
        r'cancel\s*\(',
        r'\.abort\s*\(',
        r'abort\s*\(',
        r'\.stop\s*\(',
        r'stop\s*\('
    ]

    # File extensions to search
    extensions = ['.py', '.ts', '.tsx', '.js', '.jsx', '.dart']

    for root, _dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip_dir in root for skip_dir in ['.git', '__pycache__', 'node_modules', '.venv']):
            continue

        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, encoding='utf-8') as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, 1):
                        for pattern in patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                cancel_calls.append((file_path, line_num, line.strip()))

                except Exception:
                    continue  # Skip files that can't be read

    return cancel_calls

def check_skip_diagnose_implementation() -> bool:
    """Check if skip diagnose functions are implemented"""
    required_files = [
        'runtime/skip_diagnose.py',
        'runtime/skip_diagnose.ts'
    ]

    found_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            found_files.append(file_path)

    if not found_files:
        print("❌ Skip diagnose functions not found")
        print("💡 Create runtime/skip_diagnose.py or .ts")
        return False

    print(f"✅ Skip diagnose functions found: {', '.join(found_files)}")
    return True

def check_policy_compliance(policy: dict[str, Any]) -> bool:
    """Check if policy is compliant"""
    skip_config = policy.get('skip', {})

    # Check skip semantics
    if skip_config.get('semantics') != 'diagnose':
        print(f"❌ Invalid skip semantics: {skip_config.get('semantics')}")
        print("💡 Should be 'diagnose'")
        return False

    # Check cancel_on_skip
    if skip_config.get('cancel_on_skip') is not False:
        print(f"❌ Invalid cancel_on_skip: {skip_config.get('cancel_on_skip')}")
        print("💡 Should be false")
        return False

    # Check required outputs
    required_outputs = ['COMPLETED', 'RUNNING', 'STALLED', 'UNKNOWN']
    outputs = skip_config.get('outputs', [])
    for output in required_outputs:
        if output not in outputs:
            print(f"❌ Missing required skip output: {output}")
            return False

    print("✅ Policy is compliant")
    return True

def analyze_skip_handlers(skip_handlers: list[tuple[str, int, str]]) -> bool:
    """Analyze Skip handlers for compliance"""
    if not skip_handlers:
        print("⚠️ No Skip handlers found")
        return True

    print(f"🔍 Found {len(skip_handlers)} Skip handlers:")

    violations = []
    for file_path, line_num, line in skip_handlers:
        print(f"  - {file_path}:{line_num} - {line}")

        # Check if handler calls cancel()
        if any(call in line.lower() for call in ['cancel(', 'abort(', 'stop(']):
            violations.append((file_path, line_num, line))

    if violations:
        print("\n❌ Skip handlers calling cancel/abort/stop:")
        for file_path, line_num, line in violations:
            print(f"  - {file_path}:{line_num} - {line}")
        print("💡 Skip should call diagnose, not cancel")
        return False

    print("✅ Skip handlers are compliant")
    return True

def analyze_cancel_calls(cancel_calls: list[tuple[str, int, str]]) -> bool:
    """Analyze cancel calls for context"""
    if not cancel_calls:
        print("✅ No cancel calls found")
        return True

    print(f"🔍 Found {len(cancel_calls)} cancel/abort/stop calls:")

    # Group by file
    by_file = {}
    for file_path, line_num, line in cancel_calls:
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append((line_num, line))

    for file_path, calls in by_file.items():
        print(f"\n📁 {file_path}:")
        for line_num, line in calls:
            print(f"  {line_num}: {line}")

    print("\n💡 These calls should be in Cancel/Abort handlers, not Skip handlers")
    return True

def main():
    """Main CI check function"""
    print("🔍 StillMe CI Check - Skip Not Cancel")
    print("=" * 50)

    # Load policy
    try:
        policy = load_interaction_policy()
        print(f"📋 Policy version: {policy['version']}")
        print(f"📝 Skip semantics: {policy['skip']['semantics']}")
        print(f"🚫 Cancel on skip: {policy['skip']['cancel_on_skip']}")
    except Exception as e:
        print(f"❌ Failed to load policy: {e}")
        sys.exit(1)

    # Run checks
    checks = [
        ("Policy compliance", lambda: check_policy_compliance(policy)),
        ("Skip diagnose implementation", check_skip_diagnose_implementation),
        ("Skip handlers analysis", lambda: analyze_skip_handlers(find_skip_handlers())),
        ("Cancel calls analysis", lambda: analyze_cancel_calls(find_cancel_calls()))
    ]

    passed = 0
    total = len(checks)

    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"❌ Check failed: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} checks passed")

    if passed == total:
        print("✅ All checks passed!")
        print("🎯 Skip behavior is compliant: Skip = Diagnose, not Cancel")
        sys.exit(0)
    else:
        print("❌ Some checks failed!")
        print("💡 Fix Skip handlers to use diagnose instead of cancel")
        sys.exit(1)

if __name__ == "__main__":
    main()
