#!/usr/bin/env python3
"""
Encoding and line ending normalization tool
Converts test files to UTF-8 (no BOM) with LF line endings
"""

import sys
from pathlib import Path

import chardet


def detect_encoding(file_path):
    """Detect file encoding"""
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()

        # Check for BOM
        if raw_data.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig", True
        elif raw_data.startswith(b"\xff\xfe"):
            return "utf-16le", True
        elif raw_data.startswith(b"\xfe\xff"):
            return "utf-16be", True

        # Detect encoding
        detected = chardet.detect(raw_data)
        return detected["encoding"], False
    except Exception:
        return None, False


def normalize_file(file_path):
    """Normalize a single file to UTF-8 with LF endings"""
    try:
        # Detect current encoding
        encoding, has_bom = detect_encoding(file_path)
        if not encoding:
            return False, "Could not detect encoding"

        # Read file content
        with open(file_path, encoding=encoding) as f:
            content = f.read()

        # Check if already normalized
        if (
            encoding.lower() in ["utf-8", "utf8"]
            and not has_bom
            and "\r\n" not in content
        ):
            return False, "Already normalized"

        # Normalize line endings (CRLF -> LF)
        normalized_content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Write back as UTF-8 (no BOM) with LF
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(normalized_content)

        return (
            True,
            f"Converted from {encoding} (BOM: {has_bom}) to UTF-8 (no BOM) with LF",
        )

    except Exception as e:
        return False, f"Error: {e}"


def scan_and_normalize():
    """Scan and normalize all test-related files"""
    target_paths = [
        Path("tests/"),
        Path("pytest.ini"),
        Path("tests/conftest.py"),
        Path("tox.ini"),
        Path("Makefile"),
        Path("package.json"),
    ]

    processed_files = []
    converted_files = []
    error_files = []

    for target_path in target_paths:
        if not target_path.exists():
            continue

        if target_path.is_file():
            # Single file
            success, message = normalize_file(target_path)
            processed_files.append(
                {"path": str(target_path), "success": success, "message": message}
            )

            if success:
                converted_files.append(str(target_path))
            elif "Error:" in message:
                error_files.append(str(target_path))
        else:
            # Directory - scan all Python files
            for py_file in target_path.rglob("*.py"):
                success, message = normalize_file(py_file)
                processed_files.append(
                    {"path": str(py_file), "success": success, "message": message}
                )

                if success:
                    converted_files.append(str(py_file))
                elif "Error:" in message:
                    error_files.append(str(py_file))

    return processed_files, converted_files, error_files


def generate_report(processed_files, converted_files, error_files):
    """Generate normalization report"""
    report_path = Path("reports/encoding_normalize.txt")
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("Encoding and Line Ending Normalization Report\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Total files processed: {len(processed_files)}\n")
        f.write(f"Files converted: {len(converted_files)}\n")
        f.write(f"Files with errors: {len(error_files)}\n\n")

        if converted_files:
            f.write("CONVERTED FILES:\n")
            f.write("-" * 20 + "\n")
            for file_path in converted_files:
                f.write(f"✅ {file_path}\n")
            f.write("\n")

        if error_files:
            f.write("FILES WITH ERRORS:\n")
            f.write("-" * 20 + "\n")
            for file_path in error_files:
                f.write(f"❌ {file_path}\n")
            f.write("\n")

        f.write("DETAILED RESULTS:\n")
        f.write("-" * 20 + "\n")
        for file_info in processed_files:
            status = (
                "✅"
                if file_info["success"]
                else "ℹ️"
                if "Already normalized" in file_info["message"]
                else "❌"
            )
            f.write(f"{status} {file_info['path']}: {file_info['message']}\n")

    return report_path


def main():
    """Main normalization function"""
    print("🔧 Normalizing encoding and line endings...")

    # Scan and normalize
    processed_files, converted_files, error_files = scan_and_normalize()

    # Generate report
    report_path = generate_report(processed_files, converted_files, error_files)

    print(f"📊 Processed {len(processed_files)} files")
    print(f"✅ Converted {len(converted_files)} files")
    if error_files:
        print(f"❌ {len(error_files)} files had errors")

    print(f"📄 Report saved to: {report_path}")

    if converted_files:
        print("\n🔄 Converted files:")
        for file_path in converted_files:
            print(f"  - {file_path}")

    return len(error_files)


if __name__ == "__main__":
    sys.exit(main())
