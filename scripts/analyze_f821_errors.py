#!/usr/bin/env python3
"""
🔍 Analyze F821 Errors for P2
=============================

Phân loại F821 errors để tạo kế hoạch fix.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agent_dev" / "core"))

# Import after path setup
from symbol_index import SymbolIndex  # noqa: E402
from agent_dev.core.agentdev import AgentDev  # noqa: E402


def analyze_f821_errors():
    """Analyze F821 errors and categorize them"""
    print("🔍 Analyzing F821 errors...")

    # Initialize components
    agentdev = AgentDev(str(project_root))
    symbol_index = SymbolIndex(str(project_root))

    # Build symbol index
    print("📚 Building symbol index...")
    stats = symbol_index.build_index(force_rebuild=True)
    print(f"✅ Symbol index: {stats['files_scanned']} files, {stats['symbols_found']} symbols")

    # Scan for errors
    print("🔍 Scanning for errors...")
    errors = agentdev._scan_errors()
    f821_errors = [e for e in errors if e.error_type.value == "undefined_name"]

    print(f"📊 Found {len(f821_errors)} F821 errors")

    # Categorize errors
    analysis = {
        "total_f821_errors": len(f821_errors),
        "src_vs_tests": {"src": 0, "tests": 0},
        "symbols": defaultdict(list),
        "top_missing_symbols": [],
        "symbol_analysis": {}
    }

    for error in f821_errors:
        # Extract symbol name
        match = re.search(r"undefined name '(\w+)'", error.message)
        if not match:
            continue

        symbol_name = match.group(1)

        # Categorize by location
        if "tests/" in error.file_path:
            analysis["src_vs_tests"]["tests"] += 1
        else:
            analysis["src_vs_tests"]["src"] += 1

        # Group by symbol
        analysis["symbols"][symbol_name].append({
            "file": error.file_path,
            "line": error.line_number,
            "location": "tests" if "tests/" in error.file_path else "src"
        })

    # Analyze each symbol
    for symbol_name, occurrences in analysis["symbols"].items():
        # Check if symbol exists in core
        core_symbols = symbol_index.find_symbol(symbol_name)
        core_symbols = [s for s in core_symbols if 'stillme_core' in s.module_path]

        # Check if it's stdlib
        stdlib_symbols = {
            'time', 'json', 'os', 'sys', 're', 'datetime', 'asyncio', 'threading',
            'queue', 'subprocess', 'logging', 'pathlib', 'typing', 'dataclasses',
            'asdict', 'enum', 'collections', 'itertools', 'functools', 'operator'
        }

        is_stdlib = symbol_name in stdlib_symbols or symbol_name in ['asdict', 'Path']

        analysis["symbol_analysis"][symbol_name] = {
            "occurrences": len(occurrences),
            "files": len({occ["file"] for occ in occurrences}),
            "in_core": len(core_symbols) > 0,
            "is_stdlib": is_stdlib,
            "core_module": core_symbols[0].module_path if core_symbols else None,
            "suggested_import": None
        }

        # Generate suggested import
        if is_stdlib:
            if symbol_name == 'asdict':
                analysis["symbol_analysis"][symbol_name]["suggested_import"] = "from dataclasses import asdict"
            elif symbol_name == 'Path':
                analysis["symbol_analysis"][symbol_name]["suggested_import"] = "from pathlib import Path"
            else:
                analysis["symbol_analysis"][symbol_name]["suggested_import"] = f"import {symbol_name}"
        elif core_symbols:
            module_path = core_symbols[0].module_path.replace('/', '.').replace('\\', '.')
            if module_path.endswith('.py'):
                module_path = module_path[:-3]
            analysis["symbol_analysis"][symbol_name]["suggested_import"] = f"from {module_path} import {symbol_name}"

    # Get top missing symbols
    symbol_counts = Counter({symbol: len(occurrences) for symbol, occurrences in analysis["symbols"].items()})
    analysis["top_missing_symbols"] = [{"symbol": symbol, "count": count} for symbol, count in symbol_counts.most_common(10)]

    return analysis

def main():
    """Main function"""
    analysis = analyze_f821_errors()

    print("\n📋 ANALYSIS RESULTS:")
    print(f"Total F821 errors: {analysis['total_f821_errors']}")
    print(f"Source vs Tests: {analysis['src_vs_tests']}")
    print(f"Top missing symbols: {analysis['top_missing_symbols'][:5]}")

    # Save detailed analysis
    with open(project_root / "f821_analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print("\n💾 Detailed analysis saved to f821_analysis.json")

    # Print symbol analysis
    print("\n🔍 SYMBOL ANALYSIS:")
    for symbol, info in list(analysis["symbol_analysis"].items())[:10]:
        status = "✅ CORE" if info["in_core"] else "📦 STDLIB" if info["is_stdlib"] else "❌ MISSING"
        print(f"  {symbol}: {status} ({info['occurrences']} occurrences)")
        if info["suggested_import"]:
            print(f"    → {info['suggested_import']}")

if __name__ == "__main__":
    main()
