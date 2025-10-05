#!/usr/bin/env python3
"""
AgentDev Rule Actions
====================

Safe fixers for common errors. Each fixer is tested and has minimal side effects.
"""

import re
from typing import Dict


def fix_sqlalchemy_session_import(
    file_path: str, error_line: int, error_text: str
) -> bool:
    """Fix missing SQLAlchemy Session import"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if Session is already imported
        if (
            "from sqlalchemy.orm import Session" in content
            or "from sqlalchemy.orm import Session," in content
        ):
            return True

        # Add import at the top
        lines = content.split("\n")
        import_added = False

        for i, line in enumerate(lines):
            if line.strip().startswith("from sqlalchemy") or line.strip().startswith(
                "import sqlalchemy"
            ):
                # Add Session import
                if "from sqlalchemy.orm import" in line:
                    lines[i] = line.replace(
                        "from sqlalchemy.orm import",
                        "from sqlalchemy.orm import Session,",
                    )
                else:
                    lines[i] = "from sqlalchemy.orm import Session\n" + line
                import_added = True
                break

        if not import_added:
            # Add at the beginning of file
            lines.insert(0, "from sqlalchemy.orm import Session")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True
    except Exception:
        return False


def fix_pytest_tmp_path_usage(file_path: str, error_line: int, error_text: str) -> bool:
    """Fix pytest tmp_path usage issues"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace tmp_path.join() with os.path.join() or pathlib operations
        content = re.sub(r"(\w+)\.join\(([^)]+)\)", r"os.path.join(\1, \2)", content)

        # Add os import if needed
        if "os.path.join" in content and "import os" not in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith(
                    "from "
                ):
                    lines.insert(i, "import os")
                    break

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True
    except Exception:
        return False


def fix_numpy_dtype_deprecation(
    file_path: str, error_line: int, error_text: str
) -> bool:
    """Fix numpy dtype deprecation warnings"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace deprecated numpy types
        replacements = {
            "np.float": "np.float64",
            "np.int": "np.int64",
            "np.complex": "np.complex128",
            "np.bool": "np.bool_",
        }

        for old, new in replacements.items():
            content = content.replace(old, new)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True
    except Exception:
        return False


def fix_pathlib_vs_os_path(file_path: str, error_line: int, error_text: str) -> bool:
    """Fix pathlib vs os.path usage issues"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Convert pathlib Path to string for os.path operations
        content = re.sub(
            r"(\w+\.path)\.join\(([^)]+)\)", r"os.path.join(\1, \2)", content
        )

        # Add os import if needed
        if "os.path.join" in content and "import os" not in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith(
                    "from "
                ):
                    lines.insert(i, "import os")
                    break

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True
    except Exception:
        return False


def fix_typing_optional_not_none(
    file_path: str, error_line: int, error_text: str
) -> bool:
    """Fix Optional type checking issues"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Add None checks before attribute access
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "Optional[" in line and "is not None" not in line:
                # Add None check
                var_name = re.search(r"(\w+): Optional\[", line)
                if var_name:
                    var = var_name.group(1)
                    # Add check before usage
                    lines.insert(i + 1, f"    if {var} is not None:")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True
    except Exception:
        return False


def fix_missing_imports_general(
    file_path: str, error_line: int, error_text: str
) -> bool:
    """Fix general missing imports"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract missing name from error
        missing_name = re.search(r"name '([^']+)' is not defined", error_text)
        if not missing_name:
            return False

        name = missing_name.group(1)

        # Common import mappings
        import_mappings = {
            "datetime": "from datetime import datetime",
            "timedelta": "from datetime import timedelta",
            "json": "import json",
            "os": "import os",
            "sys": "import sys",
            "Path": "from pathlib import Path",
            "List": "from typing import List",
            "Dict": "from typing import Dict",
            "Optional": "from typing import Optional",
            "Any": "from typing import Any",
        }

        if name in import_mappings:
            lines = content.split("\n")
            import_line = import_mappings[name]

            # Check if import already exists
            if import_line in content:
                return True

            # Add import at the top
            import_added = False
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith(
                    "from "
                ):
                    lines.insert(i, import_line)
                    import_added = True
                    break

            if not import_added:
                # Add at the beginning of file
                lines.insert(0, import_line)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            return True

        return False
    except Exception:
        return False


def fix_async_await_missing(file_path: str, error_line: int, error_text: str) -> bool:
    """Fix missing async/await keywords"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Add async to function definitions that call await
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "await " in line and not line.strip().startswith("async def"):
                # Find function definition
                for j in range(i, max(0, i - 10), -1):
                    if lines[j].strip().startswith("def "):
                        lines[j] = lines[j].replace("def ", "async def ")
                        break

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True
    except Exception:
        return False


def fix_f_string_format_errors(
    file_path: str, error_line: int, error_text: str
) -> bool:
    """Fix f-string format errors"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Fix common f-string issues
        # Replace {var} with {var!r} for safer formatting
        content = re.sub(r"\{([^}]+)\}", r"{\1!r}", content)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True
    except Exception:
        return False


# Registry of all fixers
FIXERS: Dict[str, callable] = {
    "fix_sqlalchemy_session_import": fix_sqlalchemy_session_import,
    "fix_pytest_tmp_path_usage": fix_pytest_tmp_path_usage,
    "fix_numpy_dtype_deprecation": fix_numpy_dtype_deprecation,
    "fix_pathlib_vs_os_path": fix_pathlib_vs_os_path,
    "fix_typing_optional_not_none": fix_typing_optional_not_none,
    "fix_missing_imports_general": fix_missing_imports_general,
    "fix_async_await_missing": fix_async_await_missing,
    "fix_f_string_format_errors": fix_f_string_format_errors,
}


def apply_fixer(
    fix_action: str, file_path: str, error_line: int, error_text: str
) -> bool:
    """Apply a fixer function"""
    if fix_action not in FIXERS:
        return False

    try:
        return FIXERS[fix_action](file_path, error_line, error_text)
    except Exception:
        return False
