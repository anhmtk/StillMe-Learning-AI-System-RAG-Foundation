#!/usr/bin/env python3
"""
📋 Plan F821 Fixes for P2
=========================

Tạo kế hoạch fix F821 errors theo ma trận.
"""

import json
from pathlib import Path


def load_analysis():
    """Load F821 analysis"""
    project_root = Path(__file__).parent.parent
    with open(project_root / "f821_analysis.json", encoding="utf-8") as f:
        return json.load(f)


def create_fix_plan():
    """Create fix plan based on analysis"""
    analysis = load_analysis()

    plan = {
        "stdlib_fixes": [],
        "core_reexports": [],
        "missing_implementations": [],
        "test_imports": [],
        "estimated_impact": {
            "stdlib_fixes": 0,
            "core_reexports": 0,
            "missing_implementations": 0,
            "test_imports": 0,
        },
    }

    # Categorize symbols
    for symbol, info in analysis["symbol_analysis"].items():
        if info["is_stdlib"]:
            plan["stdlib_fixes"].append(
                {
                    "symbol": symbol,
                    "import": info["suggested_import"],
                    "occurrences": info["occurrences"],
                    "files": info["files"],
                }
            )
            plan["estimated_impact"]["stdlib_fixes"] += info["occurrences"]

        elif info["in_core"]:
            plan["core_reexports"].append(
                {
                    "symbol": symbol,
                    "core_module": info["core_module"],
                    "import": info["suggested_import"],
                    "occurrences": info["occurrences"],
                    "files": info["files"],
                }
            )
            plan["estimated_impact"]["core_reexports"] += info["occurrences"]

        else:
            plan["missing_implementations"].append(
                {
                    "symbol": symbol,
                    "occurrences": info["occurrences"],
                    "files": info["files"],
                    "usage_context": "Need to analyze usage in tests",
                }
            )
            plan["estimated_impact"]["missing_implementations"] += info["occurrences"]

    return plan


def main():
    """Main function"""
    plan = create_fix_plan()

    print("📋 F821 FIX PLAN:")
    print(f"Total errors to fix: {sum(plan['estimated_impact'].values())}")
    print()

    print("📦 STDLIB FIXES (Priority 1):")
    for fix in plan["stdlib_fixes"][:5]:
        print(f"  {fix['symbol']}: {fix['import']} ({fix['occurrences']} occurrences)")
    print(
        f"  ... and {len(plan['stdlib_fixes']) - 5} more"
        if len(plan["stdlib_fixes"]) > 5
        else ""
    )
    print()

    print("🔄 CORE REEXPORTS (Priority 2):")
    for fix in plan["core_reexports"][:5]:
        print(f"  {fix['symbol']}: {fix['import']} ({fix['occurrences']} occurrences)")
    print(
        f"  ... and {len(plan['core_reexports']) - 5} more"
        if len(plan["core_reexports"]) > 5
        else ""
    )
    print()

    print("❌ MISSING IMPLEMENTATIONS (Priority 3):")
    for fix in plan["missing_implementations"][:5]:
        print(f"  {fix['symbol']}: {fix['occurrences']} occurrences")
    print(
        f"  ... and {len(plan['missing_implementations']) - 5} more"
        if len(plan["missing_implementations"]) > 5
        else ""
    )
    print()

    print("📊 ESTIMATED IMPACT:")
    for category, count in plan["estimated_impact"].items():
        print(f"  {category}: {count} errors")

    # Save plan
    project_root = Path(__file__).parent.parent
    with open(project_root / "f821_fix_plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print("\n💾 Fix plan saved to f821_fix_plan.json")


if __name__ == "__main__":
    main()
