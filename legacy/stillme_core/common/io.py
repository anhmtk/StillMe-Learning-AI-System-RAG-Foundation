#!/usr/bin/env python3
"""
I/O Utilities for StillMe AI Framework
Tiện ích I/O cho StillMe AI Framework

This module provides file I/O utilities with error handling and validation.
Module này cung cấp các tiện ích file I/O với xử lý lỗi và xác thực.
"""

import csv
import hashlib
import json
import pickle
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles
import yaml

from .errors import StillMeException, ValidationError
from .logging import get_module_logger

logger = get_module_logger("io")


class FileFormat(Enum):
    """File formats - Các định dạng file"""

    JSON = "json"
    YAML = "yaml"
    YML = "yml"
    CSV = "csv"
    TXT = "txt"
    PICKLE = "pickle"
    BINARY = "binary"


@dataclass
class FileInfo:
    """File information - Thông tin file"""

    path: str
    size: int
    modified_time: float
    format: FileFormat
    checksum: str | None = None
    exists: bool = False


@dataclass
class FileOperation:
    """File operation configuration - Cấu hình thao tác file"""

    source: str
    destination: str | None = None
    backup: bool = False
    create_dirs: bool = True
    overwrite: bool = False
    validate: bool = True


class FileManager:
    """
    File management utilities with error handling and validation
    Tiện ích quản lý file với xử lý lỗi và xác thực
    """

    def __init__(self, base_path: str | None = None):
        """
        Initialize file manager - Khởi tạo file manager

        Args:
            base_path: Base directory for file operations
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        logger.info("File manager initialized", base_path=str(self.base_path))

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve file path - Giải quyết đường dẫn file"""
        path = Path(path)
        if not path.is_absolute():
            path = self.base_path / path
        return path.resolve()

    def _get_file_format(self, path: Path) -> FileFormat:
        """Detect file format - Phát hiện định dạng file"""
        suffix = path.suffix.lower()
        if suffix == ".json":
            return FileFormat.JSON
        elif suffix in [".yaml", ".yml"]:
            return FileFormat.YAML
        elif suffix == ".csv":
            return FileFormat.CSV
        elif suffix == ".txt":
            return FileFormat.TXT
        elif suffix == ".pickle":
            return FileFormat.PICKLE
        else:
            return FileFormat.BINARY

    def _calculate_checksum(self, path: Path) -> str:
        """Calculate file checksum - Tính checksum file"""
        hash_md5 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_file_info(self, path: str | Path) -> FileInfo:
        """
        Get file information - Lấy thông tin file

        Args:
            path: File path

        Returns:
            File information
        """
        path = self._resolve_path(path)

        if not path.exists():
            return FileInfo(
                path=str(path),
                size=0,
                modified_time=0,
                format=self._get_file_format(path),
                exists=False,
            )

        stat = path.stat()
        checksum = self._calculate_checksum(path) if path.is_file() else None

        return FileInfo(
            path=str(path),
            size=stat.st_size,
            modified_time=stat.st_mtime,
            format=self._get_file_format(path),
            checksum=checksum,
            exists=True,
        )

    def ensure_directory(self, path: str | Path) -> Path:
        """
        Ensure directory exists - Đảm bảo thư mục tồn tại

        Args:
            path: Directory path

        Returns:
            Resolved directory path
        """
        path = self._resolve_path(path)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug("Directory ensured", path=str(path))
        return path

    def backup_file(self, path: str | Path, backup_suffix: str = ".backup") -> Path:
        """
        Create backup of file - Tạo backup file

        Args:
            path: File path
            backup_suffix: Backup file suffix

        Returns:
            Backup file path
        """
        path = self._resolve_path(path)
        if not path.exists():
            raise StillMeException(f"File not found: {path}")

        backup_path = path.with_suffix(path.suffix + backup_suffix)
        shutil.copy2(path, backup_path)

        logger.info("File backed up", original=str(path), backup=str(backup_path))
        return backup_path

    def safe_write(self, path: str | Path, data: Any, operation: FileOperation) -> None:
        """
        Safely write data to file - Ghi data an toàn vào file

        Args:
            path: File path
            data: Data to write
            operation: File operation configuration
        """
        path = self._resolve_path(path)

        # Create backup if requested and file exists
        if operation.backup and path.exists():
            self.backup_file(path)

        # Ensure directory exists
        if operation.create_dirs:
            self.ensure_directory(path.parent)

        # Check if file exists and overwrite is not allowed
        if path.exists() and not operation.overwrite:
            raise StillMeException(
                f"File already exists and overwrite is not allowed: {path}"
            )

        # Write to temporary file first
        temp_path = path.with_suffix(path.suffix + ".tmp")
        try:
            self._write_data(temp_path, data, self._get_file_format(path))

            # Validate if requested
            if operation.validate:
                self._validate_file(temp_path, self._get_file_format(path))

            # Move temporary file to final location
            shutil.move(str(temp_path), str(path))

            logger.info(
                "File written successfully", path=str(path), size=len(str(data))
            )

        except Exception as e:
            # Clean up temporary file
            if temp_path.exists():
                temp_path.unlink()
            raise StillMeException(f"Failed to write file {path}: {e!s}") from e

    def _write_data(self, path: Path, data: Any, format_type: FileFormat) -> None:
        """Write data to file based on format - Ghi data vào file theo định dạng"""
        if format_type == FileFormat.JSON:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format_type == FileFormat.YAML:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        elif format_type == FileFormat.CSV:
            if isinstance(data, list) and data and isinstance(data[0], dict):
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
            else:
                raise ValidationError("CSV data must be a list of dictionaries")
        elif format_type == FileFormat.TXT:
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(data))
        elif format_type == FileFormat.PICKLE:
            with open(path, "wb") as f:
                pickle.dump(data, f)
        else:
            # Binary data
            if isinstance(data, bytes):
                with open(path, "wb") as f:
                    f.write(data)
            else:
                raise ValidationError("Binary format requires bytes data")

    def _validate_file(self, path: Path, format_type: FileFormat) -> None:
        """Validate file content - Xác thực nội dung file"""
        try:
            if format_type == FileFormat.JSON:
                with open(path, encoding="utf-8") as f:
                    json.load(f)
            elif format_type == FileFormat.YAML:
                with open(path, encoding="utf-8") as f:
                    yaml.safe_load(f)
            elif format_type == FileFormat.CSV:
                with open(path, encoding="utf-8") as f:
                    csv.reader(f)
            # Other formats don't need validation
        except Exception as e:
            raise ValidationError(f"File validation failed: {e!s}") from e

    def read_file(self, path: str | Path, format_type: FileFormat | None = None) -> Any:
        """
        Read file content - Đọc nội dung file

        Args:
            path: File path
            format_type: File format (auto-detected if None)

        Returns:
            File content
        """
        path = self._resolve_path(path)

        if not path.exists():
            raise StillMeException(f"File not found: {path}")

        if format_type is None:
            format_type = self._get_file_format(path)

        try:
            return self._read_data(path, format_type)
        except Exception as e:
            raise StillMeException(f"Failed to read file {path}: {e!s}") from e

    def _read_data(self, path: Path, format_type: FileFormat) -> Any:
        """Read data from file based on format - Đọc data từ file theo định dạng"""
        if format_type == FileFormat.JSON:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        elif format_type == FileFormat.YAML:
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        elif format_type == FileFormat.CSV:
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        elif format_type == FileFormat.TXT:
            with open(path, encoding="utf-8") as f:
                return f.read()
        elif format_type == FileFormat.PICKLE:
            with open(path, "rb") as f:
                return pickle.load(f)
        else:
            # Binary data
            with open(path, "rb") as f:
                return f.read()

    async def async_read_file(
        self, path: str | Path, format_type: FileFormat | None = None
    ) -> Any:
        """
        Async read file content - Đọc nội dung file bất đồng bộ

        Args:
            path: File path
            format_type: File format (auto-detected if None)

        Returns:
            File content
        """
        path = self._resolve_path(path)

        if not path.exists():
            raise StillMeException(f"File not found: {path}")

        if format_type is None:
            format_type = self._get_file_format(path)

        try:
            return await self._async_read_data(path, format_type)
        except Exception as e:
            raise StillMeException(f"Failed to read file {path}: {e!s}") from e

    async def _async_read_data(self, path: Path, format_type: FileFormat) -> Any:
        """Async read data from file - Đọc data từ file bất đồng bộ"""
        if format_type == FileFormat.JSON:
            async with aiofiles.open(path, encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
        elif format_type == FileFormat.YAML:
            async with aiofiles.open(path, encoding="utf-8") as f:
                content = await f.read()
                return yaml.safe_load(content)
        elif format_type == FileFormat.TXT:
            async with aiofiles.open(path, encoding="utf-8") as f:
                return await f.read()
        else:
            # For other formats, use sync version
            return self._read_data(path, format_type)

    async def async_write_file(
        self, path: str | Path, data: Any, operation: FileOperation
    ) -> None:
        """
        Async write data to file - Ghi data vào file bất đồng bộ

        Args:
            path: File path
            data: Data to write
            operation: File operation configuration
        """
        path = self._resolve_path(path)

        # Create backup if requested and file exists
        if operation.backup and path.exists():
            self.backup_file(path)

        # Ensure directory exists
        if operation.create_dirs:
            self.ensure_directory(path.parent)

        # Check if file exists and overwrite is not allowed
        if path.exists() and not operation.overwrite:
            raise StillMeException(
                f"File already exists and overwrite is not allowed: {path}"
            )

        # Write to temporary file first
        temp_path = path.with_suffix(path.suffix + ".tmp")
        try:
            await self._async_write_data(temp_path, data, self._get_file_format(path))

            # Validate if requested
            if operation.validate:
                self._validate_file(temp_path, self._get_file_format(path))

            # Move temporary file to final location
            shutil.move(str(temp_path), str(path))

            logger.info(
                "File written successfully", path=str(path), size=len(str(data))
            )

        except Exception as e:
            # Clean up temporary file
            if temp_path.exists():
                temp_path.unlink()
            raise StillMeException(f"Failed to write file {path}: {e!s}") from e

    async def _async_write_data(
        self, path: Path, data: Any, format_type: FileFormat
    ) -> None:
        """Async write data to file - Ghi data vào file bất đồng bộ"""
        if format_type == FileFormat.JSON:
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        elif format_type == FileFormat.YAML:
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(
                    yaml.dump(data, default_flow_style=False, allow_unicode=True)
                )
        elif format_type == FileFormat.TXT:
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(str(data))
        else:
            # For other formats, use sync version
            self._write_data(path, data, format_type)

    def copy_file(
        self,
        source: str | Path,
        destination: str | Path,
        operation: FileOperation,
    ) -> None:
        """
        Copy file - Sao chép file

        Args:
            source: Source file path
            destination: Destination file path
            operation: File operation configuration
        """
        source = self._resolve_path(source)
        destination = self._resolve_path(destination)

        if not source.exists():
            raise StillMeException(f"Source file not found: {source}")

        # Ensure destination directory exists
        if operation.create_dirs:
            self.ensure_directory(destination.parent)

        # Check if destination exists and overwrite is not allowed
        if destination.exists() and not operation.overwrite:
            raise StillMeException(
                f"Destination file already exists and overwrite is not allowed: {destination}"
            )

        # Create backup if requested
        if operation.backup and destination.exists():
            self.backup_file(destination)

        try:
            shutil.copy2(source, destination)
            logger.info(
                "File copied successfully",
                source=str(source),
                destination=str(destination),
            )
        except Exception as e:
            raise StillMeException(
                f"Failed to copy file from {source} to {destination}: {e!s}"
            ) from e

    def move_file(
        self,
        source: str | Path,
        destination: str | Path,
        operation: FileOperation,
    ) -> None:
        """
        Move file - Di chuyển file

        Args:
            source: Source file path
            destination: Destination file path
            operation: File operation configuration
        """
        source = self._resolve_path(source)
        destination = self._resolve_path(destination)

        if not source.exists():
            raise StillMeException(f"Source file not found: {source}")

        # Ensure destination directory exists
        if operation.create_dirs:
            self.ensure_directory(destination.parent)

        # Check if destination exists and overwrite is not allowed
        if destination.exists() and not operation.overwrite:
            raise StillMeException(
                f"Destination file already exists and overwrite is not allowed: {destination}"
            )

        # Create backup if requested
        if operation.backup and destination.exists():
            self.backup_file(destination)

        try:
            shutil.move(str(source), str(destination))
            logger.info(
                "File moved successfully",
                source=str(source),
                destination=str(destination),
            )
        except Exception as e:
            raise StillMeException(
                f"Failed to move file from {source} to {destination}: {e!s}"
            ) from e

    def delete_file(self, path: str | Path, backup: bool = False) -> None:
        """
        Delete file - Xóa file

        Args:
            path: File path
            backup: Create backup before deletion
        """
        path = self._resolve_path(path)

        if not path.exists():
            logger.warning("File not found for deletion", path=str(path))
            return

        # Create backup if requested
        if backup:
            self.backup_file(path)

        try:
            path.unlink()
            logger.info("File deleted successfully", path=str(path))
        except Exception as e:
            raise StillMeException(f"Failed to delete file {path}: {e!s}") from e

    def list_files(
        self, directory: str | Path, pattern: str = "*", recursive: bool = False
    ) -> list[FileInfo]:
        """
        List files in directory - Liệt kê files trong thư mục

        Args:
            directory: Directory path
            pattern: File pattern
            recursive: Search recursively

        Returns:
            List of file information
        """
        directory = self._resolve_path(directory)

        if not directory.exists():
            raise StillMeException(f"Directory not found: {directory}")

        files = []
        if recursive:
            for path in directory.rglob(pattern):
                if path.is_file():
                    files.append(self.get_file_info(path))
        else:
            for path in directory.glob(pattern):
                if path.is_file():
                    files.append(self.get_file_info(path))

        logger.debug("Files listed", directory=str(directory), count=len(files))
        return files


# Convenience functions - Các hàm tiện ích


def read_json(path: str | Path) -> dict[str, Any]:
    """
    Read JSON file - Đọc file JSON

    Args:
        path: File path

    Returns:
        Parsed JSON data
    """
    manager = FileManager()
    return manager.read_file(path, FileFormat.JSON)


def write_json(
    path: str | Path,
    data: dict[str, Any],
    backup: bool = False,
    overwrite: bool = True,
) -> None:
    """
    Write JSON file - Ghi file JSON

    Args:
        path: File path
        data: Data to write
        backup: Create backup
        overwrite: Allow overwrite
    """
    manager = FileManager()
    operation = FileOperation(
        source=str(path),
        backup=backup,
        overwrite=overwrite,
        create_dirs=True,
        validate=True,
    )
    manager.safe_write(path, data, operation)


def read_yaml(path: str | Path) -> dict[str, Any]:
    """
    Read YAML file - Đọc file YAML

    Args:
        path: File path

    Returns:
        Parsed YAML data
    """
    manager = FileManager()
    return manager.read_file(path, FileFormat.YAML)


def write_yaml(
    path: str | Path,
    data: dict[str, Any],
    backup: bool = False,
    overwrite: bool = True,
) -> None:
    """
    Write YAML file - Ghi file YAML

    Args:
        path: File path
        data: Data to write
        backup: Create backup
        overwrite: Allow overwrite
    """
    manager = FileManager()
    operation = FileOperation(
        source=str(path),
        backup=backup,
        overwrite=overwrite,
        create_dirs=True,
        validate=True,
    )
    manager.safe_write(path, data, operation)


async def async_read_json(path: str | Path) -> dict[str, Any]:
    """
    Async read JSON file - Đọc file JSON bất đồng bộ

    Args:
        path: File path

    Returns:
        Parsed JSON data
    """
    manager = FileManager()
    return await manager.async_read_file(path, FileFormat.JSON)


async def async_write_json(
    path: str | Path,
    data: dict[str, Any],
    backup: bool = False,
    overwrite: bool = True,
) -> None:
    """
    Async write JSON file - Ghi file JSON bất đồng bộ

    Args:
        path: File path
        data: Data to write
        backup: Create backup
        overwrite: Allow overwrite
    """
    manager = FileManager()
    operation = FileOperation(
        source=str(path),
        backup=backup,
        overwrite=overwrite,
        create_dirs=True,
        validate=True,
    )
    await manager.async_write_file(path, data, operation)
