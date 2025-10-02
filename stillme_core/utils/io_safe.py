"""
Safe I/O Operations for StillMe Core
===================================

Provides robust file reading operations that handle various encodings
and prevent crashes from Unicode issues.
"""

from pathlib import Path
from typing import Optional


def safe_read_text(path: Path, encoding: Optional[str] = None) -> str:
    """
    Đọc file văn bản an toàn với fallback encoding:
    - Ưu tiên UTF-8
    - Fallback cp1252/latin-1
    - Cuối cùng dùng errors='replace' để không crash

    Args:
        path: Đường dẫn file cần đọc
        encoding: Encoding cụ thể (nếu None thì auto-detect)

    Returns:
        Nội dung file dưới dạng string, không bao giờ raise UnicodeDecodeError
    """
    if encoding:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            # Fallback to replace mode
            with open(path, "rb") as f:
                return f.read().decode(encoding, errors="replace")

    # Auto-detect encoding
    encodings_to_try = ["utf-8", "cp1252", "latin-1", "utf-16", "ascii"]

    for enc in encodings_to_try:
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, FileNotFoundError):
            continue

    # Last resort: read as bytes and decode with replace
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8", errors="replace")
    except (FileNotFoundError, Exception):
        # Absolute fallback: return empty string
        return ""


def safe_read_lines(path: Path, encoding: Optional[str] = None) -> list[str]:
    """
    Đọc file theo dòng an toàn

    Args:
        path: Đường dẫn file
        encoding: Encoding cụ thể

    Returns:
        List các dòng trong file
    """
    content = safe_read_text(path, encoding)
    return content.splitlines()


def is_text_file(path: Path) -> bool:
    """
    Kiểm tra xem file có phải là text file không

    Args:
        path: Đường dẫn file

    Returns:
        True nếu là text file, False nếu binary
    """
    try:
        # Try to read first 1KB
        with open(path, 'rb') as f:
            chunk = f.read(1024)
            # Check for null bytes (binary indicator)
            return b'\x00' not in chunk
    except Exception:
        return False


def safe_decode(data: bytes) -> str:
    """
    Decode bytes to string with fallback encodings

    Args:
        data: Bytes to decode

    Returns:
        Decoded string, never raises UnicodeDecodeError
    """
    import locale

    # Preferred encodings in order
    encodings = [
        "utf-8",
        locale.getpreferredencoding(False),
        "cp1252",
        "latin-1",
        "utf-16"
    ]

    # Remove duplicates while preserving order
    unique_encodings = list(dict.fromkeys(encodings))

    for encoding in unique_encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue

    # Last resort: decode with replace
    return data.decode("utf-8", errors="replace")
