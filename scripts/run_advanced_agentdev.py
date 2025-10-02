#!/usr/bin/env python3
"""
🚀 Advanced AgentDev Runner
===========================

Chạy AgentDev với P1 improvements và validation.
"""

import json
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agent_dev" / "core"))

from advanced_fixer import AdvancedFixer
from symbol_index import SymbolIndex

from agent_dev.core.agentdev import AgentDev


def main():
    """Main function"""
    print("🚀 Starting Advanced AgentDev with P1 improvements...")

    # Initialize components
    agentdev = AgentDev(str(project_root))

    # Build symbol index
    print("📚 Building symbol index...")
    symbol_index = SymbolIndex(str(project_root))
    stats = symbol_index.build_index(force_rebuild=True)
    print(
        f"✅ Symbol index built: {stats['files_scanned']} files, {stats['symbols_found']} symbols"
    )

    # Scan for errors (only stillme_core/)
    print("🔍 Scanning for errors in stillme_core/...")
    errors = agentdev._scan_errors()
    print(f"📊 Found {len(errors)} errors")

    if not errors:
        print("✅ No errors found!")
        return

    # Group errors by type
    f821_errors = [e for e in errors if e.error_type.value == "undefined_name"]
    other_errors = [e for e in errors if e.error_type.value != "undefined_name"]

    print("📋 Error breakdown:")
    print(f"  - F821 undefined name: {len(f821_errors)}")
    print(f"  - Other errors: {len(other_errors)}")

    # Fix F821 errors in batches
    if f821_errors:
        print("\n🔧 Fixing F821 errors in batches of 20...")
        advanced_fixer = AdvancedFixer(str(project_root))

        batch_size = 20
        total_fixed = 0
        total_failed = 0

        for i in range(0, len(f821_errors), batch_size):
            batch = f821_errors[i : i + batch_size]
            print(f"  Processing batch {i//batch_size + 1} ({len(batch)} errors)...")

            try:
                results, validation = advanced_fixer.fix_batch(batch, max_files=20)

                # Count results
                fixed = len([r for r in results if r.status.value == "success"])
                failed = len([r for r in results if r.status.value == "failed"])
                skipped = len([r for r in results if r.status.value == "skipped"])

                total_fixed += fixed
                total_failed += failed

                print(
                    f"    ✅ Fixed: {fixed}, ❌ Failed: {failed}, ⏭️ Skipped: {skipped}"
                )
                print(
                    f"    Validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}"
                )

                if not validation["valid"]:
                    print(
                        f"    ⚠️ Validation failed: {validation.get('errors', [])[:3]}"
                    )
                    break

            except Exception as e:
                print(f"    ❌ Batch failed: {e}")
                break

        print("\n📊 F821 Fix Summary:")
        print(f"  - Total fixed: {total_fixed}")
        print(f"  - Total failed: {total_failed}")
        print(
            f"  - Success rate: {total_fixed/(total_fixed+total_failed)*100:.1f}%"
            if (total_fixed + total_failed) > 0
            else "  - Success rate: N/A"
        )

    # Final validation
    print("\n🔍 Final validation...")
    final_errors = agentdev._scan_errors()
    print(f"📊 Final error count: {len(final_errors)}")

    # Generate summary
    summary = {
        "files_scanned": stats["files_scanned"],
        "symbols_found": stats["symbols_found"],
        "errors_before": len(errors),
        "errors_after": len(final_errors),
        "f821_fixed": total_fixed if "total_fixed" in locals() else 0,
        "f821_failed": total_failed if "total_failed" in locals() else 0,
        "fix_success_rate": f"{total_fixed/(total_fixed+total_failed)*100:.1f}%"
        if "total_fixed" in locals() and (total_fixed + total_failed) > 0
        else "N/A",
        "improvement": len(errors) - len(final_errors),
    }

    print("\n📋 FINAL SUMMARY:")
    print(json.dumps(summary, indent=2))

    # Save summary to file
    with open(project_root / "agentdev_scan.log", "w", encoding="utf-8") as f:
        f.write(f"Advanced AgentDev Run - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n")
        f.write(json.dumps(summary, indent=2))
        f.write("\n\n")

        if final_errors:
            f.write("Remaining errors:\n")
            for error in final_errors[:10]:  # First 10 errors
                f.write(f"  {error.file_path}:{error.line_number} - {error.message}\n")


if __name__ == "__main__":
    main()
