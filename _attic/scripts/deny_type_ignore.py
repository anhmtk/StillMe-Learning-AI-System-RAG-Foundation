#!/usr/bin/env python3
"""
Script to deny type: ignore comments unless explicitly allowed.
This enforces proper typing practices and prevents hiding errors.
"""

import pathlib
import sys

# Whitelist of allowed type: ignore comments with reasons
# Format: "path/to/file.py:line_number" = "reason for allowing"
ALLOW: set[str] = set()


def check_file(file_path: str) -> list[str]:
    """Check a single file for forbidden type: ignore comments."""
    bad_lines = []

    # Skip checking this script itself
    if "deny_type_ignore.py" in file_path:
        return bad_lines

    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, start=1):
                if "type: ignore" in line:
                    file_line_key = f"{file_path}:{line_num}"
                    if file_line_key not in ALLOW:
                        bad_lines.append(file_line_key)
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)

    return bad_lines


def main():
    """Main function to check all provided files."""
    if len(sys.argv) < 2:
        print("Usage: python deny_type_ignore.py <file1> <file2> ...")
        sys.exit(1)

    all_bad_lines = []

    for file_path in sys.argv[1:]:
        if pathlib.Path(file_path).exists():
            bad_lines = check_file(file_path)
            all_bad_lines.extend(bad_lines)

    if all_bad_lines:
        print("Forbidden 'type: ignore' found:")
        for bad_line in all_bad_lines:
            print(f"  {bad_line}")
        print(
            "\nTo allow a specific type: ignore, add it to the ALLOW set in this script with a reason."
        )
        sys.exit(1)
    else:
        print("No forbidden 'type: ignore' comments found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
