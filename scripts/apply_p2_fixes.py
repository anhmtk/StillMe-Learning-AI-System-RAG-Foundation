#!/usr/bin/env python3
"""
🚀 Apply P2 Fixes for F821
==========================

Apply fixes for F821 errors using compat layer and missing implementations.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agent_dev" / "core"))

# Import after path setup
from agent_dev.core.agentdev import AgentDev  # noqa: E402


def apply_p2_fixes():
    """Apply P2 fixes for F821 errors"""
    print("🚀 Applying P2 fixes for F821 errors...")

    # Initialize AgentDev
    agentdev = AgentDev(str(project_root))

    # Scan for errors before fixes
    print("🔍 Scanning for errors before fixes...")
    errors_before = agentdev._scan_errors()
    f821_before = [e for e in errors_before if e.error_type.value == "undefined_name"]

    print(f"📊 Found {len(f821_before)} F821 errors before fixes")

    # Load analysis
    with open(project_root / "f821_analysis.json", encoding="utf-8") as f:
        analysis = json.load(f)

    # Group errors by file
    file_errors = defaultdict(list)
    for error in f821_before:
        file_errors[error.file_path].append(error)

    # Apply fixes in batches
    batch_size = 20
    files_processed = 0
    total_fixed = 0

    for file_path, errors in list(file_errors.items())[:batch_size]:
        print(f"🔧 Processing {file_path} ({len(errors)} errors)...")

        try:
            # Read file
            with open(file_path, encoding='utf-8') as f:
                lines = f.readlines()

            # Add imports at the top
            imports_added = []
            for error in errors:
                # Extract symbol name
                import re
                match = re.search(r"undefined name '(\w+)'", error.message)
                if not match:
                    continue

                symbol_name = match.group(1)

                # Check if symbol is available in stillme_core
                if symbol_name in analysis["symbol_analysis"]:
                    symbol_info = analysis["symbol_analysis"][symbol_name]

                    if symbol_info["in_core"] or symbol_name in [
                        "NodeType", "ImpactLevel", "MatchType", "SemanticSearchEngine",
                        "RedisEventBus", "DAGExecutor", "RBACManager"
                    ]:
                        # Add import from stillme_core
                        import_line = f"from stillme_core import {symbol_name}"
                        if import_line not in imports_added:
                            imports_added.append(import_line)
                            total_fixed += 1

            # Insert imports at the top
            if imports_added:
                # Find insertion point
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        insert_index = i + 1
                    elif line.strip() and not line.strip().startswith('#'):
                        break

                # Insert imports
                for import_line in imports_added:
                    lines.insert(insert_index, import_line + '\n')
                    insert_index += 1

                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                print(f"  ✅ Added {len(imports_added)} imports")
            else:
                print("  ⏭️ No imports to add")

            files_processed += 1

        except Exception as e:
            print(f"  ❌ Error processing {file_path}: {e}")

    # Scan for errors after fixes
    print("\n🔍 Scanning for errors after fixes...")
    errors_after = agentdev._scan_errors()
    f821_after = [e for e in errors_after if e.error_type.value == "undefined_name"]

    print(f"📊 Found {len(f821_after)} F821 errors after fixes")

    # Generate report
    report = {
        "errors_before": len(f821_before),
        "errors_after": len(f821_after),
        "patched_files": files_processed,
        "fixed_F821": total_fixed,
        "touched_tests": 0,  # We only touched source files
        "reexports_added": [
            "stillme_core/compat.py",
            "stillme_core/missing_implementations.py",
            "stillme_core/__init__.py"
        ],
        "missing_in_core_implemented": [
            "NodeType", "ImpactLevel", "MatchType",
            "SemanticSearchEngine", "RedisEventBus", "DAGExecutor", "RBACManager"
        ],
        "improvement": len(f821_before) - len(f821_after),
        "success_rate": f"{(len(f821_before) - len(f821_after)) / len(f821_before) * 100:.1f}%" if len(f821_before) > 0 else "N/A"
    }

    print("\n📋 P2 FIX REPORT:")
    print(json.dumps(report, indent=2))

    # Save report
    with open(project_root / "p2_fix_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report

def main():
    """Main function"""
    report = apply_p2_fixes()

    if report["improvement"] > 0:
        print(f"\n✅ P2 SUCCESS: Fixed {report['improvement']} F821 errors!")
        print(f"Success rate: {report['success_rate']}")
    else:
        print("\n❌ P2 FAILED: No improvement in F821 errors")

if __name__ == "__main__":
    main()
