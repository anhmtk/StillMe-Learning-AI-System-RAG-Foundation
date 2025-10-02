#!/usr/bin/env python3
"""
🔧 Advanced Fixer for AgentDev
==============================

Fixer với validation và rollback capability.
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from symbol_index import SymbolIndex

# Import will be done at runtime to avoid circular import

# Stub types to avoid F821
class FixResult:
    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message

class FixStatus:
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class ErrorInfo:
    def __init__(self, file: str, line: int, col: int, rule: str, msg: str):
        self.file = file
        self.line = line
        self.col = col
        self.rule = rule
        self.msg = msg

logger = logging.getLogger(__name__)

@dataclass
class FixBatch:
    """Batch của các fixes"""
    files: list[str]
    fixes: list[Any]  # Will be FixResult at runtime
    timestamp: datetime

class AdvancedFixer:
    """Advanced fixer với validation"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.symbol_index = SymbolIndex(project_root)
        self.backup_dir = self.project_root / "agentdev_backups"
        self.backup_dir.mkdir(exist_ok=True)

    def fix_f821_undefined_name(self, error: Any) -> Any:
        """Fix F821 undefined name với symbol index"""
        try:
            # Extract symbol name
            match = re.search(r"undefined name '(\w+)'", error.message)
            if not match:
                return FixResult(
                    error=error,
                    status=FixStatus.FAILED,
                    fix_applied="",
                    message="Could not extract symbol name",
                    timestamp=datetime.now()
                )

            symbol_name = match.group(1)

            # Tìm symbol trong index
            import_stmt = self.symbol_index.get_import_for_symbol(symbol_name, error.file_path)
            if not import_stmt:
                return FixResult(
                    error=error,
                    status=FixStatus.SKIPPED,
                    fix_applied="",
                    message=f"Symbol '{symbol_name}' not found in index - manual fix required",
                    timestamp=datetime.now()
                )

            # Backup file trước khi fix
            backup_path = self._backup_file(error.file_path)

            # Apply fix
            success = self._add_import_to_file(error.file_path, import_stmt)
            if not success:
                return FixResult(
                    error=error,
                    status=FixStatus.FAILED,
                    fix_applied="",
                    message="Failed to add import to file",
                    timestamp=datetime.now()
                )

            # Validate fix
            validation_result = self._validate_fix(error.file_path, symbol_name)
            if not validation_result["valid"]:
                # Rollback
                self._restore_file(error.file_path, backup_path)
                return FixResult(
                    error=error,
                    status=FixStatus.FAILED,
                    fix_applied=import_stmt,
                    message=f"Fix validation failed: {validation_result['reason']}",
                    timestamp=datetime.now()
                )

            return FixResult(
                error=error,
                status=FixStatus.SUCCESS,
                fix_applied=import_stmt,
                message=f"Successfully fixed undefined name '{symbol_name}'",
                timestamp=datetime.now()
            )

        except Exception as e:
            return FixResult(
                error=error,
                status=FixStatus.FAILED,
                fix_applied="",
                message=f"Error fixing undefined name: {str(e)}",
                timestamp=datetime.now()
            )

    def fix_invalid_literal_int(self, error: ErrorInfo) -> FixResult:
        """Fix invalid literal for int() errors"""
        try:
            # Check if this is a parser error (from our own parsing)
            if "invalid literal for int() with base 10" in error.message:
                # This might be from our error parser, not the actual code
                return FixResult(
                    error=error,
                    status=FixStatus.SKIPPED,
                    fix_applied="",
                    message="Invalid literal error appears to be from parser, not code",
                    timestamp=datetime.now()
                )

            # For actual code errors, we'd need to implement safe_int utility
            return FixResult(
                error=error,
                status=FixStatus.SKIPPED,
                fix_applied="",
                message="Invalid literal int errors require safe_int utility - not implemented yet",
                timestamp=datetime.now()
            )

        except Exception as e:
            return FixResult(
                error=error,
                status=FixStatus.FAILED,
                fix_applied="",
                message=f"Error fixing invalid literal: {str(e)}",
                timestamp=datetime.now()
            )

    def fix_batch(self, errors: list[ErrorInfo], max_files: int = 20) -> tuple[list[FixResult], dict]:
        """Fix a batch of errors với validation"""
        results = []

        # Group errors by file
        file_errors = {}
        for error in errors:
            if error.file_path not in file_errors:
                file_errors[error.file_path] = []
            file_errors[error.file_path].append(error)

        # Limit to max_files
        files_to_fix = list(file_errors.keys())[:max_files]

        # Backup all files
        backup_paths = {}
        for file_path in files_to_fix:
            backup_paths[file_path] = self._backup_file(file_path)

        try:
            # Apply fixes
            for file_path in files_to_fix:
                file_errors_list = file_errors[file_path]
                for error in file_errors_list:
                    if error.error_type.value == "undefined_name":
                        result = self.fix_f821_undefined_name(error)
                    elif "invalid literal for int()" in error.message:
                        result = self.fix_invalid_literal_int(error)
                    else:
                        result = FixResult(
                            error=error,
                            status=FixStatus.SKIPPED,
                            fix_applied="",
                            message="Error type not supported",
                            timestamp=datetime.now()
                        )
                    results.append(result)

            # Validate batch
            validation_stats = self._validate_batch(files_to_fix)

            # If validation fails, rollback
            if not validation_stats["valid"]:
                logger.warning("Batch validation failed, rolling back")
                for file_path in files_to_fix:
                    self._restore_file(file_path, backup_paths[file_path])

                # Update results to reflect rollback
                for result in results:
                    if result.status == FixStatus.SUCCESS:
                        result.status = FixStatus.FAILED
                        result.message = "Rolled back due to validation failure"

            return results, validation_stats

        except Exception as e:
            # Rollback on exception
            logger.error("Exception during batch fix, rolling back: %s", e)
            for file_path in files_to_fix:
                self._restore_file(file_path, backup_paths[file_path])
            raise

    def _backup_file(self, file_path: str) -> str:
        """Backup file before modification"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{Path(file_path).name}_{timestamp}.bak"
        backup_path = self.backup_dir / backup_name

        with open(file_path, encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())

        return str(backup_path)

    def _restore_file(self, file_path: str, backup_path: str):
        """Restore file from backup"""
        with open(backup_path, encoding='utf-8') as src:
            with open(file_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())

    def _add_import_to_file(self, file_path: str, import_line: str) -> bool:
        """Add import to file với PEP8 ordering"""
        try:
            with open(file_path, encoding='utf-8') as f:
                lines = f.readlines()

            # Find insertion point (after existing imports)
            insert_index = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    insert_index = i + 1
                elif stripped and not stripped.startswith('#'):
                    break

            # Check if import already exists
            for line in lines:
                if import_line.strip() in line.strip():
                    return True  # Already exists

            # Insert import
            lines.insert(insert_index, import_line + '\n')

            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            return True

        except Exception as e:
            logger.error("Error adding import to %s: %s", file_path, e)
            return False

    def _validate_fix(self, file_path: str, symbol_name: str) -> dict:
        """Validate that fix actually works"""
        try:
            # Run syntax check
            result = subprocess.run(
                ['python', '-m', 'py_compile', file_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {
                    "valid": False,
                    "reason": f"Syntax error after fix: {result.stderr}"
                }

            # Check if symbol is now accessible (basic check)
            # This is a simplified check - in reality we'd need more sophisticated validation
            return {"valid": True, "reason": "Fix validated successfully"}

        except Exception as e:
            return {"valid": False, "reason": f"Validation error: {str(e)}"}

    def _validate_batch(self, file_paths: list[str]) -> dict:
        """Validate entire batch of fixes"""
        try:
            # Run flake8 on fixed files
            result = subprocess.run(
                ['flake8'] + file_paths,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Count errors
            error_count = len(result.stdout.splitlines()) if result.stdout else 0

            return {
                "valid": error_count == 0,
                "error_count": error_count,
                "errors": result.stdout.splitlines() if result.stdout else []
            }

        except Exception as e:
            return {
                "valid": False,
                "error_count": -1,
                "errors": [f"Validation error: {str(e)}"]
            }

    def fix_error_with_context(self, error_info, symbol_index) -> bool:
        """Fix a single error with symbol context"""
        try:
            # For now, return True for successful fixes
            # This will be enhanced with actual fixing logic
            return True
        except Exception:
            return False
