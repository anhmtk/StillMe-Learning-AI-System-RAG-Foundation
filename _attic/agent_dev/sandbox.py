#!/usr/bin/env python3
"""
FS Sandbox helpers for AgentDev Sprint 1
Safe file operations with path traversal protection
"""

import os
import stat
from pathlib import Path

from agent_dev.schemas import PolicyViolation


def safe_join(root: str | Path, *paths: str) -> Path:
    """
    Safely join paths within a root directory.
    Prevents path traversal attacks.

    Args:
        root: Root directory path
        *paths: Path components to join

    Returns:
        Resolved path within root

    Raises:
        PolicyViolation: If path traversal is detected
    """
    root_path = Path(root).resolve()

    # Check for path traversal patterns
    for path_component in paths:
        if (
            ".." in path_component
            or path_component.startswith("/")
            or path_component.startswith("C:")
        ):
            raise PolicyViolation(f"Path traversal detected: {path_component}")

    # Join and resolve
    joined_path = root_path.joinpath(*paths).resolve()

    # Ensure result is within root
    if not is_within_root(joined_path, root_path):
        raise PolicyViolation(f"Path outside root directory: {joined_path}")

    return joined_path


def is_within_root(path: str | Path, root: str | Path) -> bool:
    """
    Check if path is within root directory.

    Args:
        path: Path to check
        root: Root directory

    Returns:
        True if path is within root
    """
    try:
        path_resolved = Path(path).resolve()
        root_resolved = Path(root).resolve()

        # Check if path is within root
        return str(path_resolved).startswith(str(root_resolved))
    except (OSError, ValueError):
        return False


def deny_symlink(path: str | Path) -> None:
    """
    Check if path is a symlink and raise error if so.

    Args:
        path: Path to check

    Raises:
        PolicyViolation: If path is a symlink
    """
    path_obj = Path(path)

    if path_obj.exists() and path_obj.is_symlink():
        raise PolicyViolation(f"Symlink not allowed: {path}")


def mkdir_sandbox(sandbox_path: str | Path) -> Path:
    """
    Create sandbox directory with proper permissions.

    Args:
        sandbox_path: Path for sandbox directory

    Returns:
        Created sandbox path

    Raises:
        PolicyViolation: If path traversal or permission issues
    """
    sandbox = Path(sandbox_path).resolve()

    # Check for path traversal and home expansion
    sandbox_str = str(sandbox)
    original_path = str(sandbox_path)
    if (
        ".." in original_path
        or original_path.startswith("~")
        or original_path.startswith("/")
    ):
        raise PolicyViolation("Path traversal or home expansion not allowed")

    # Create directory
    sandbox.mkdir(parents=True, exist_ok=True)

    # Set restrictive permissions (owner only)
    os.chmod(sandbox, stat.S_IRWXU)

    return sandbox


def safe_write_file(
    file_path: str | Path, content: str, root: str | Path, max_size_kb: int = 1024
) -> Path:
    """
    Safely write content to file within sandbox.

    Args:
        file_path: Target file path
        content: Content to write
        root: Sandbox root directory
        max_size_kb: Maximum file size in KB

    Returns:
        Written file path

    Raises:
        PolicyViolation: If path traversal or size limit exceeded
    """
    # Resolve safe path
    safe_path = safe_join(root, str(file_path))

    # Check file size
    content_size_kb = len(content.encode("utf-8")) / 1024
    if content_size_kb > max_size_kb:
        raise PolicyViolation(
            f"File size {content_size_kb:.1f}KB exceeds limit {max_size_kb}KB"
        )

    # Check for symlinks in parent directories
    current_path = safe_path.parent
    while current_path != Path(root).resolve():
        deny_symlink(current_path)
        current_path = current_path.parent

    # Create parent directories
    safe_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Set restrictive permissions
    os.chmod(safe_path, stat.S_IRUSR | stat.S_IWUSR)

    return safe_path


def safe_read_file(
    file_path: str | Path, root: str | Path, max_size_kb: int = 1024
) -> str:
    """
    Safely read file content within sandbox.

    Args:
        file_path: File path to read
        root: Sandbox root directory
        max_size_kb: Maximum file size in KB

    Returns:
        File content

    Raises:
        PolicyViolation: If path traversal or size limit exceeded
    """
    # Resolve safe path
    safe_path = safe_join(root, str(file_path))

    # Check if file exists
    if not safe_path.exists():
        raise PolicyViolation(f"File not found: {safe_path}")

    # Check file size
    file_size_kb = safe_path.stat().st_size / 1024
    if file_size_kb > max_size_kb:
        raise PolicyViolation(
            f"File size {file_size_kb:.1f}KB exceeds limit {max_size_kb}KB"
        )

    # Check for symlinks
    deny_symlink(safe_path)

    # Read file
    with open(safe_path, encoding="utf-8") as f:
        return f.read()


def list_sandbox_files(sandbox_path: str | Path, pattern: str = "*") -> list[Path]:
    """
    List files in sandbox directory.

    Args:
        sandbox_path: Sandbox directory path
        pattern: File pattern to match

    Returns:
        List of file paths

    Raises:
        PolicyViolation: If path traversal detected
    """
    sandbox = Path(sandbox_path).resolve()

    if not sandbox.exists():
        return []

    if not sandbox.is_dir():
        raise PolicyViolation(f"Path is not a directory: {sandbox}")

    files = []
    for file_path in sandbox.glob(pattern):
        # Check for symlinks
        deny_symlink(file_path)

        # Ensure file is within sandbox
        if is_within_root(file_path, sandbox):
            files.append(file_path)

    return files


def cleanup_sandbox(sandbox_path: str | Path) -> None:
    """
    Clean up sandbox directory.

    Args:
        sandbox_path: Sandbox directory to clean
    """
    import shutil

    sandbox = Path(sandbox_path)

    if sandbox.exists() and sandbox.is_dir():
        shutil.rmtree(sandbox, ignore_errors=True)


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
