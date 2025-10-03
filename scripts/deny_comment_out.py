#!/usr/bin/env python3
"""
Pre-commit hook: Deny comment-out code to avoid errors
Chặn comment-out code để né lỗi
"""

import re
import subprocess
import sys
from datetime import datetime


def check_comment_out():
    """Check for comment-out code in git diff"""

    # Get staged changes
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "-U0"],
            capture_output=True,
            text=True,
            check=True,
        )
        diff_content = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}")
        return False

    if not diff_content:
        return True

    # Parse diff hunks
    hunks = []
    current_hunk = []

    for line in diff_content.split("\n"):
        if line.startswith("@@"):
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = [line]
        elif line.startswith("+") or line.startswith("-") or line.startswith(" "):
            current_hunk.append(line)

    if current_hunk:
        hunks.append(current_hunk)

    violations = []

    for hunk in hunks:
        if not hunk:
            continue

        # Check if hunk has both deletions and new comments
        has_deletions = any(
            line.startswith("-") and not line.startswith("---") for line in hunk
        )
        has_new_comments = any(
            line.startswith("+")
            and line[1:].strip().startswith("#")
            and not line[1:].strip().startswith("# type: ignore")
            and not line[1:].strip().startswith("# noqa")
            and "TEMP_DISABLE" not in line
            for line in hunk
        )

        if has_deletions and has_new_comments:
            # Check if it's not a legitimate comment (like docstring, license, etc.)
            for line in hunk:
                if line.startswith("+") and line[1:].strip().startswith("#"):
                    comment_content = line[1:].strip()[1:].strip()

                    # Skip legitimate comments
                    if any(
                        keyword in comment_content.lower()
                        for keyword in [
                            "license",
                            "copyright",
                            "author",
                            "version",
                            "date",
                            "docstring",
                            "module",
                            "function",
                            "class",
                            "method",
                            "todo",
                            "fixme",
                            "note",
                            "warning",
                            "info",
                        ]
                    ):
                        continue

                    # Check for TEMP_DISABLE with valid expiration
                    if "TEMP_DISABLE" in line:
                        temp_disable_match = re.search(
                            r"TEMP_DISABLE\(reason=([^,]+),\s*expires=(\d{4}-\d{2}-\d{2})\)",
                            line,
                        )
                        if temp_disable_match:
                            reason = temp_disable_match.group(1)
                            expires = temp_disable_match.group(2)

                            try:
                                expire_date = datetime.strptime(expires, "%Y-%m-%d")
                                if expire_date > datetime.now():
                                    continue  # Valid temp disable
                            except ValueError:
                                pass  # Invalid date format

                    # This looks like commented-out code
                    violations.append(
                        {
                            "file": hunk[0] if hunk else "unknown",
                            "line": line,
                            "reason": "Potential commented-out code detected",
                        }
                    )

    if violations:
        print("❌ COMMENT-OUT CODE DETECTED:")
        print("=" * 50)

        for violation in violations:
            print(f"File: {violation['file']}")
            print(f"Line: {violation['line']}")
            print(f"Reason: {violation['reason']}")
            print()

        print("💡 SOLUTIONS:")
        print("1. Remove the commented code entirely")
        print("2. Use TEMP_DISABLE(reason=..., expires=YYYY-MM-DD) for temporary cases")
        print("3. Move to proper documentation if it's reference material")
        print()
        print("🚫 This commit will be rejected.")
        return False

    return True


def main():
    """Main function"""
    print("🔍 Checking for commented-out code...")

    if check_comment_out():
        print("✅ No commented-out code detected")
        sys.exit(0)
    else:
        print("❌ Commented-out code detected - commit rejected")
        sys.exit(1)


if __name__ == "__main__":
    main()
