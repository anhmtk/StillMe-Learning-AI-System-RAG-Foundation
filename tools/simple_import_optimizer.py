#!/usr/bin/env python3
"""
Simple Import Optimizer

A safer version that only makes minimal changes to avoid syntax errors.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class SimpleImportOptimizer:
    """Simple and safe import optimizer"""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.optimized_files: List[str] = []

    def analyze_imports(self, file_path: Path) -> Dict[str, any]:
        """Analyze imports in a file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            imports = []
            from_imports = []
            total_lines = len(content.splitlines())
            code_lines = len(
                [
                    line
                    for line in content.splitlines()
                    if line.strip() and not line.strip().startswith("#")
                ]
            )

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        from_imports.append(f"{module}.{alias.name}")

            return {
                "file": str(file_path),
                "total_imports": len(imports) + len(from_imports),
                "imports": imports,
                "from_imports": from_imports,
                "total_lines": total_lines,
                "code_lines": code_lines,
                "import_density": (len(imports) + len(from_imports))
                / max(code_lines, 1)
                * 100,
            }
        except Exception as e:
            return {"file": str(file_path), "error": str(e)}

    def safe_optimize_file(self, file_path: Path) -> Tuple[bool, str]:
        """Safely optimize imports in a single file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Only make very safe changes - remove duplicate imports
            lines = content.splitlines()
            seen_imports = set()
            new_lines = []

            for line in lines:
                stripped = line.strip()
                if stripped.startswith(
                    ("import ", "from ")
                ) and not stripped.startswith("#"):
                    if stripped not in seen_imports:
                        seen_imports.add(stripped)
                        new_lines.append(line)
                    # Skip duplicate imports
                else:
                    new_lines.append(line)

            new_content = "\n".join(new_lines)

            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True, "Removed duplicates"
            else:
                return False, "No changes needed"

        except Exception as e:
            return False, f"Error: {e}"

    def optimize_directory(self, directory: Path) -> Dict[str, int]:
        """Optimize imports in all Python files in directory"""
        stats = {
            "total_files": 0,
            "optimized_files": 0,
            "error_files": 0,
            "no_change_files": 0,
        }

        for py_file in directory.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            stats["total_files"] += 1
            optimized, status = self.safe_optimize_file(py_file)

            if optimized:
                stats["optimized_files"] += 1
                self.optimized_files.append(str(py_file))
                print(f"✅ {status}: {py_file.relative_to(self.root_path)}")
            elif "Error" in status:
                stats["error_files"] += 1
                print(f"❌ {status}: {py_file.relative_to(self.root_path)}")
            else:
                stats["no_change_files"] += 1
                print(f"➡️ {status}: {py_file.relative_to(self.root_path)}")

        return stats

    def generate_report(self, target_dirs: List[Path]) -> None:
        """Generate optimization report"""
        print("🔍 Simple Import Analysis Report")
        print("=" * 50)

        high_density_files = []

        for target_dir in target_dirs:
            print(f"\n📂 Analyzing {target_dir.relative_to(self.root_path)}...")

            for py_file in target_dir.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                analysis = self.analyze_imports(py_file)
                if "error" not in analysis:
                    if analysis["import_density"] > 15:  # High density threshold
                        high_density_files.append(
                            {
                                "file": analysis["file"],
                                "density": analysis["import_density"],
                                "imports": analysis["total_imports"],
                            }
                        )

        if high_density_files:
            print(f"\n⚠️ High Import Density Files ({len(high_density_files)}):")
            for file_info in sorted(
                high_density_files, key=lambda x: x["density"], reverse=True
            ):
                print(
                    f"   * {file_info['file']} (density: {file_info['density']:.1f}%, imports: {file_info['imports']})"
                )
        else:
            print("\n✅ No high import density files found!")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print(
            "Usage: python tools/simple_import_optimizer.py <comma_separated_target_dirs> [root_path]"
        )
        sys.exit(1)

    target_dirs_str = sys.argv[1]
    root_path_str = sys.argv[2] if len(sys.argv) > 2 else "."

    root_path = Path(root_path_str).resolve()
    target_dirs = [root_path / d for d in target_dirs_str.split(",")]

    print(f"🔧 Simple import optimization in: {target_dirs_str}")
    print(f"📁 Root path: {root_path}")

    optimizer = SimpleImportOptimizer(root_path)

    # Generate report first
    optimizer.generate_report(target_dirs)

    # Optimize files
    print("\n🔧 Optimizing files...")
    total_stats = {
        "total_files": 0,
        "optimized_files": 0,
        "error_files": 0,
        "no_change_files": 0,
    }

    for target_dir in target_dirs:
        if not target_dir.exists():
            print(f"⚠️ Directory {target_dir} not found, skipping...")
            continue

        print(f"\n📂 Processing {target_dir.relative_to(root_path)}...")
        stats = optimizer.optimize_directory(target_dir)

        for key in total_stats:
            total_stats[key] += stats[key]

    print("\n📊 Summary:")
    print(f"   - Total files processed: {total_stats['total_files']}")
    print(f"   - Files optimized: {total_stats['optimized_files']}")
    print(f"   - Files with errors: {total_stats['error_files']}")
    print(f"   - Files unchanged: {total_stats['no_change_files']}")

    if optimizer.optimized_files:
        print("\n✅ Optimized files:")
        for file_path in optimizer.optimized_files:
            print(f"   * {file_path}")


if __name__ == "__main__":
    main()
