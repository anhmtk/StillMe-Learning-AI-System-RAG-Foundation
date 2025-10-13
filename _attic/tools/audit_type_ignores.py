#!/usr/bin/env python3
"""
Tool để audit tất cả '# type: ignore' trong toàn bộ repository.
Không được bỏ qua bất kỳ file nào (trừ venv/.git).
"""

import csv
import os
from collections import defaultdict
from pathlib import Path

# from typing import Any  # Not used


def find_type_ignores(root_dir: str = ".") -> list[dict[str, str]]:
    """
    Tìm tất cả '# type: ignore' trong repository.

    Returns:
        List of dicts với keys: file, line_number, code_context
    """
    ignores: list[dict[str, str]] = []
    root_path = Path(root_dir)

    # Patterns để ignore
    ignore_patterns = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        "dist",
        "build",
        ".mypy_cache",
        ".ruff_cache",
    }

    # File extensions để scan
    code_extensions = {".py", ".pyi", ".ts", ".tsx", ".js", ".jsx"}

    for file_path in root_path.rglob("*"):
        # Skip directories
        if file_path.is_dir():
            continue

        # Skip ignored patterns
        if any(part in ignore_patterns for part in file_path.parts):
            continue

        # Skip non-code files
        if file_path.suffix not in code_extensions:
            continue

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Tìm '# type: ignore' (có thể có comment khác sau)
                # Nhưng không phải trong string literals hoặc docstrings
                stripped_line = line.strip()

                # Skip empty lines và comment-only lines
                if not stripped_line or stripped_line.startswith("#"):
                    continue

                # Skip docstrings (triple quotes)
                if '"""' in line or "'''" in line:
                    continue

                # Skip nếu '# type: ignore' nằm trong string literal
                # Tìm vị trí của '# type: ignore'
                ignore_pos = line.find("# type: ignore")
                if ignore_pos == -1:
                    continue

                # Kiểm tra xem có nằm trong string literal không
                before_ignore = line[:ignore_pos]
                quote_count_single = before_ignore.count("'") - before_ignore.count(
                    "\\'"
                )
                quote_count_double = before_ignore.count('"') - before_ignore.count(
                    '\\"'
                )

                # Nếu số quote lẻ thì đang trong string literal
                if quote_count_single % 2 == 1 or quote_count_double % 2 == 1:
                    continue

                # Tìm '# type: ignore' trong code thực sự
                # Lấy context (dòng code trước comment)
                code_context = line.split("#")[0].strip()
                if not code_context:
                    # Nếu dòng chỉ có comment, lấy dòng trước
                    if line_num > 1:
                        code_context = lines[line_num - 2].strip()

                ignores.append(
                    {
                        "file": str(file_path.relative_to(root_path)),
                        "line": str(line_num),
                        "code_context": code_context,
                        "full_line": line.strip(),
                    }
                )

        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            continue

    return ignores


def generate_csv_report(
    ignores: list[dict[str, str]], output_file: str = "artifacts/type_ignores.csv"
):
    """Tạo CSV report với tất cả type ignores."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        if ignores:
            writer = csv.DictWriter(
                f, fieldnames=["file", "line", "code_context", "full_line"]
            )
            writer.writeheader()
            writer.writerows(ignores)
        else:
            # Tạo file empty với header
            writer = csv.DictWriter(
                f, fieldnames=["file", "line", "code_context", "full_line"]
            )
            writer.writeheader()


def generate_summary_report(
    ignores: list[dict[str, str]],
    output_file: str = "artifacts/type_ignores_summary.md",
):
    """Tạo summary report theo thư mục và module."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Thống kê theo thư mục
    dir_counts: defaultdict[str, int] = defaultdict(int)
    file_counts: defaultdict[str, int] = defaultdict(int)

    for ignore in ignores:
        file_path = Path(ignore["file"])
        dir_name = str(file_path.parent) if file_path.parent != Path(".") else "root"
        dir_counts[dir_name] += 1
        file_counts[ignore["file"]] += 1

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Type Ignore Audit Summary\n\n")
        f.write(f"**Total # type: ignore found: {len(ignores)}**\n\n")

        if ignores:
            f.write("## By Directory\n\n")
            for dir_name, count in sorted(
                dir_counts.items(), key=lambda x: x[1], reverse=True
            ):
                f.write(f"- `{dir_name}/`: {count} ignores\n")

            f.write("\n## By File (Top 20)\n\n")
            for file_name, count in sorted(
                file_counts.items(), key=lambda x: x[1], reverse=True
            )[:20]:
                f.write(f"- `{file_name}`: {count} ignores\n")

            f.write("\n## All Ignores (First 50)\n\n")
            for i, ignore in enumerate(ignores[:50], 1):
                f.write(f"{i}. **{ignore['file']}:{ignore['line']}**\n")
                f.write(f"   ```\n   {ignore['full_line']}\n   ```\n\n")

            if len(ignores) > 50:
                f.write(
                    f"... and {len(ignores) - 50} more (see CSV for complete list)\n"
                )
        else:
            f.write("🎉 **No type ignores found!** Repository is clean.\n")


def main():
    """Main function để chạy audit."""
    print("🔍 Scanning repository for '# type: ignore'...")

    ignores = find_type_ignores()

    print(f"\n📊 Found {len(ignores)} '# type: ignore' statements")

    if ignores:
        print("\n📁 By directory:")
        dir_counts: defaultdict[str, int] = defaultdict(int)
        for ignore in ignores:
            file_path = Path(ignore["file"])
            dir_name: str = (
                str(file_path.parent) if file_path.parent != Path(".") else "root"
            )
            dir_counts[dir_name] += 1

        for dir_name, count in sorted(
            dir_counts.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {dir_name}/: {count}")

    # Generate reports
    generate_csv_report(ignores)
    generate_summary_report(ignores)

    print("\n📄 Reports generated:")
    print("  - artifacts/type_ignores.csv")
    print("  - artifacts/type_ignores_summary.md")

    if ignores:
        print(f"\n⚠️  Repository has {len(ignores)} type ignores that need to be fixed!")
        return 1
    else:
        print("\n✅ Repository is clean - no type ignores found!")
        return 0


if __name__ == "__main__":
    exit(main())
