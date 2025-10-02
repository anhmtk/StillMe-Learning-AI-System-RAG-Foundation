#!/usr/bin/env python3
"""
Script to automatically fix E402 errors (import not at top of file)
by moving import statements to the correct position.
"""


def fix_e402_errors_in_file(file_path: str) -> bool:
    """Fix E402 errors in a single file"""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        if not lines:
            return False

        # Find the first non-comment, non-docstring line
        first_import_line = -1
        docstring_end = -1

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            # Check for docstring start
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Find docstring end
                for j in range(i + 1, len(lines)):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        docstring_end = j
                        break
                continue

            # Check for import statement
            if stripped.startswith(("import ", "from ")):
                first_import_line = i
                break

        if first_import_line == -1:
            return False  # No imports found

        # If imports are already at the top (after shebang and docstring), no fix needed
        if first_import_line <= 2:  # Allow for shebang and docstring
            return False

        # Collect all import statements
        import_lines = []
        non_import_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")) or (
                stripped.startswith("#") and "import" in stripped
            ):
                import_lines.append(line)
            else:
                non_import_lines.append((i, line))

        if not import_lines:
            return False

        # Reconstruct file content
        new_lines = []

        # Add shebang if present
        if lines[0].startswith("#!"):
            new_lines.append(lines[0])
            start_idx = 1
        else:
            start_idx = 0

        # Add docstring if present
        if lines[start_idx].strip().startswith(('"""', "'''")):
            # Find docstring end
            for i in range(start_idx, len(lines)):
                new_lines.append(lines[i])
                if '"""' in lines[i] or "'''" in lines[i]:
                    if i > start_idx:  # Multi-line docstring
                        start_idx = i + 1
                        break
                    else:
                        start_idx = i + 1
                        break

        # Add empty line after docstring if needed
        if new_lines and new_lines[-1].strip():
            new_lines.append("")

        # Add all import statements
        for import_line in import_lines:
            new_lines.append(import_line)

        # Add empty line after imports if needed
        if new_lines and new_lines[-1].strip():
            new_lines.append("")

        # Add remaining non-import lines
        for i, line in non_import_lines:
            if i >= start_idx:  # Skip lines we've already processed
                new_lines.append(line)

        # Write back to file
        new_content = "\n".join(new_lines)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Main function to fix E402 errors in all Python files"""
    print("Starting E402 error fixes...")

    # Get list of files with E402 errors
    import subprocess

    try:
        result = subprocess.run(
            ["ruff", "check", ".", "--select", "E402", "--output-format=json"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("Failed to get E402 error list")
            return

        import json

        errors = json.loads(result.stdout)

        files_to_fix = set()
        for error in errors:
            if error.get("code") == "E402":
                files_to_fix.add(error["filename"])

        print(f"Found {len(files_to_fix)} files with E402 errors")

        fixed_count = 0
        for file_path in files_to_fix:
            if fix_e402_errors_in_file(file_path):
                print(f"Fixed: {file_path}")
                fixed_count += 1
            else:
                print(f"Skipped: {file_path}")

        print(f"Fixed {fixed_count}/{len(files_to_fix)} files")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
