#!/usr/bin/env python3
"""
🔍 Repository Inventory Tool - Two-Phase Approach
Phase 1: Primary files (production code, configs, docs)
Phase 2: Excluded files (artifacts, dependencies, build outputs)
"""

import argparse
import csv
import hashlib
import json
import mimetypes
import multiprocessing as mp
import os
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


def process_file_batch(
    file_paths: list[Path], repo_root: Path, with_hash: bool = False
) -> list[dict[str, Any]]:
    """Process a batch of files in parallel"""
    results = []

    for file_path in file_paths:
        try:
            # Get basic file info
            stat = file_path.stat()
            relative_path = file_path.relative_to(repo_root)

            # Get file type
            file_type = get_file_type(file_path)

            # Get file hash if requested and file is small enough
            file_hash = None
            if with_hash and stat.st_size < 64 * 1024 * 1024:  # 64MB limit
                try:
                    with open(file_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()[:16]
                except (OSError, FileNotFoundError):
                    pass

            # Get git info
            git_info = get_git_info(file_path, repo_root)

            results.append(
                {
                    "path": str(relative_path),
                    "size": stat.st_size,
                    "type": file_type,
                    "last_commit": git_info["last_commit"],
                    "last_author": git_info["last_author"],
                    "last_date": git_info["last_date"],
                    "ref_count": 0,  # Will be calculated separately
                    "bin_guess": is_binary_file(file_path),
                    "hash": file_hash,
                }
            )

        except (OSError, FileNotFoundError, PermissionError):
            continue

    return results


def get_file_type(file_path: Path) -> str:
    """Phân loại file theo extension và path"""
    file_str = str(file_path)

    # Check for test files
    if any(
        test_pattern in file_str.lower()
        for test_pattern in ["test_", "_test", ".test.", ".spec.", ".test.", "tests/"]
    ):
        return "test"

    # Check by extension
    suffix = file_path.suffix.lower()
    if suffix in {
        ".py",
        ".js",
        ".ts",
        ".dart",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".swift",
        ".kt",
    }:
        return "code"
    elif suffix in {".md", ".rst", ".txt", ".doc", ".docx", ".pdf", ".rtf"}:
        return "doc"
    elif suffix in {
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".xml",
        ".properties",
    }:
        return "config"
    elif suffix in {
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".bin",
        ".app",
        ".apk",
        ".ipa",
        ".deb",
        ".rpm",
    }:
        return "bin"
    elif suffix in {
        ".csv",
        ".tsv",
        ".json",
        ".xml",
        ".sql",
        ".db",
        ".sqlite",
        ".parquet",
    }:
        return "data"
    elif suffix in {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".mp4",
        ".mp3",
        ".wav",
        ".avi",
        ".mov",
    }:
        return "media"
    elif suffix in {
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".7z",
        ".rar",
        ".tar.gz",
        ".tar.bz2",
    }:
        return "archive"
    else:
        return "other"


def get_git_info(file_path: Path, repo_root: Path) -> dict[str, Any]:
    """Lấy thông tin Git cho file"""
    try:
        # Get last commit info
        result = subprocess.run(
            [
                "git",
                "log",
                "-1",
                "--format=%H|%an|%ae|%ad",
                "--date=iso",
                str(file_path),
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout.strip():
            commit_hash, author, email, date = result.stdout.strip().split("|", 3)
            return {
                "last_commit": commit_hash[:8],
                "last_author": author,
                "last_date": date,
            }
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
        pass

    return {"last_commit": "unknown", "last_author": "unknown", "last_date": "unknown"}


def is_binary_file(file_path: Path) -> bool:
    """Kiểm tra xem file có phải binary không"""
    try:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith("text/"):
            return False

        # Check first 1024 bytes for null bytes
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except (OSError, FileNotFoundError):
        return False


class RepoInventory:
    def __init__(
        self,
        repo_root: str = ".",
        mode: str = "primary",
        exclude_dirs: set[str] = None,
        include_exts: set[str] = None,
        workers: int = None,
        with_hash: bool = False,
    ):
        self.repo_root = Path(repo_root).resolve()
        self.reports_dir = self.repo_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)

        self.mode = mode
        self.with_hash = with_hash
        self.workers = workers or max(1, mp.cpu_count() - 1)

        # Default exclude directories (artifacts and dependencies)
        self.exclude_dirs = exclude_dirs or {
            "node_modules",
            ".venv",
            "__pycache__",
            "dist",
            "build",
            "logs",
            "reports",
            ".next",
            ".turbo",
            ".pytest_cache",
            ".cache",
            "coverage",
            "*.egg-info",
            ".gradle",
            ".idea",
            ".parcel-cache",
            ".git",
            ".vscode",
            ".vs",
        }

        # Default include extensions (production files)
        self.include_exts = include_exts or {
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".json",
            ".md",
            ".toml",
            ".yaml",
            ".yml",
            ".ini",
            ".sh",
            ".ps1",
            ".bat",
            ".kt",
            ".java",
            ".sql",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".swift",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
        }

        # Protected directories (không được đụng)
        self.protected_dirs = {
            ".env",
            ".env.local",
            ".env.prod",
            ".env.dev",
            "policies",
            "models",
            "weights",
            "checkpoints",
            "data",
            "deploy",
            ".github",
            "sandbox",
        }

    def should_include_file(self, file_path: Path) -> bool:
        """Kiểm tra xem file có nên được include không"""
        relative_path = file_path.relative_to(self.repo_root)
        path_str = str(relative_path)

        # Check if in protected directory
        for protected in self.protected_dirs:
            if protected in path_str:
                return False

        # Check if in exclude directory
        for exclude in self.exclude_dirs:
            if exclude in path_str:
                return False

        # Check extension
        if file_path.suffix.lower() not in self.include_exts:
            return False

        return True

    def should_include_excluded_file(self, file_path: Path) -> bool:
        """Kiểm tra xem file có nên được include trong excluded mode không"""
        relative_path = file_path.relative_to(self.repo_root)
        path_str = str(relative_path)

        # Check if in protected directory
        for protected in self.protected_dirs:
            if protected in path_str:
                return False

        # Check if in exclude directory
        for exclude in self.exclude_dirs:
            if exclude in path_str:
                return True

        return False

    def collect_files(self) -> list[Path]:
        """Collect files based on mode"""
        files = []

        print(f"🔍 Collecting files in {self.mode} mode...")

        for root, dirs, filenames in os.walk(self.repo_root):
            root_path = Path(root)

            # Skip hidden directories
            dirs[:] = [
                d for d in dirs if not d.startswith(".") or d in {".git", ".github"}
            ]

            for filename in filenames:
                file_path = root_path / filename

                # Skip hidden files
                if filename.startswith(".") and filename not in {
                    ".gitignore",
                    ".env.example",
                    ".env.template",
                }:
                    continue

                # Check if file should be included
                if self.mode == "primary":
                    if self.should_include_file(file_path):
                        files.append(file_path)
                elif self.mode == "excluded":
                    if self.should_include_excluded_file(file_path):
                        files.append(file_path)
                elif self.mode == "all":
                    if not any(
                        protected in str(file_path.relative_to(self.repo_root))
                        for protected in self.protected_dirs
                    ):
                        files.append(file_path)

        print(f"📄 Found {len(files)} files to process")
        return files

    def scan_repository(self) -> list[dict[str, Any]]:
        """Quét repository với multiprocessing"""
        files = self.collect_files()

        if not files:
            print("⚠️ No files found to process")
            return []

        print(f"🚀 Processing {len(files)} files with {self.workers} workers...")

        # Split files into batches
        batch_size = 256
        batches = [files[i : i + batch_size] for i in range(0, len(files), batch_size)]

        inventory = []
        start_time = time.time()

        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(
                    process_file_batch, batch, self.repo_root, self.with_hash
                ): batch
                for batch in batches
            }

            # Collect results
            for future in as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    inventory.extend(batch_results)

                    # Progress update
                    processed = len(inventory)
                    if processed % 1000 == 0:
                        elapsed = time.time() - start_time
                        rate = processed / elapsed if elapsed > 0 else 0
                        print(
                            f"  📊 Processed {processed}/{len(files)} files ({rate:.1f} files/sec)"
                        )

                except Exception as e:
                    print(f"❌ Error processing batch: {e}")

        elapsed = time.time() - start_time
        rate = len(inventory) / elapsed if elapsed > 0 else 0
        print(
            f"✅ Processed {len(inventory)} files in {elapsed:.1f}s ({rate:.1f} files/sec)"
        )

        return inventory

    def generate_large_files_report(self, inventory: list[dict[str, Any]]) -> None:
        """Tạo báo cáo file lớn"""
        large_files = sorted(inventory, key=lambda x: x["size"], reverse=True)[:1000]

        csv_path = self.reports_dir / f"{self.mode}_large_files.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["path", "size", "type", "last_commit", "ref_count"]
            )
            writer.writeheader()

            for item in large_files:
                writer.writerow(
                    {
                        "path": item["path"],
                        "size": item["size"],
                        "type": item["type"],
                        "last_commit": item["last_commit"],
                        "ref_count": item["ref_count"],
                    }
                )

        print(f"📊 Large files report: {csv_path}")

    def generate_dependency_graph(self, inventory: list[dict[str, Any]]) -> None:
        """Tạo đồ thị dependencies (chỉ cho primary mode)"""
        if self.mode != "primary":
            return

        dep_graph = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_files": len(inventory),
                "mode": self.mode,
            },
        }

        # Add nodes (files)
        for item in inventory:
            if item["type"] in ["code", "config"]:
                dep_graph["nodes"].append(
                    {
                        "id": item["path"],
                        "type": item["type"],
                        "size": item["size"],
                        "ref_count": item["ref_count"],
                    }
                )

        json_path = self.reports_dir / f"{self.mode}_dep_graph.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dep_graph, f, indent=2, ensure_ascii=False)

        print(f"🕸️  Dependency graph: {json_path}")

    def generate_inventory_csv(self, inventory: list[dict[str, Any]]) -> None:
        """Tạo CSV inventory chính"""
        csv_path = self.reports_dir / f"{self.mode}_inventory.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "path",
                "size",
                "type",
                "last_commit",
                "ref_count",
                "bin_guess",
                "hash",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for item in inventory:
                writer.writerow(
                    {
                        "path": item["path"],
                        "size": item["size"],
                        "type": item["type"],
                        "last_commit": item["last_commit"],
                        "ref_count": item["ref_count"],
                        "bin_guess": item["bin_guess"],
                        "hash": item["hash"],
                    }
                )

        print(f"📋 Main inventory: {csv_path}")

    def generate_summary_report(self, inventory: list[dict[str, Any]]) -> None:
        """Tạo báo cáo tóm tắt"""
        summary = {
            "mode": self.mode,
            "total_files": len(inventory),
            "total_size": sum(item["size"] for item in inventory),
            "by_type": {},
            "by_size_range": {
                "small": 0,  # < 1KB
                "medium": 0,  # 1KB - 1MB
                "large": 0,  # 1MB - 10MB
                "huge": 0,  # > 10MB
            },
            "unreferenced_files": 0,
            "binary_files": 0,
        }

        # Count by type
        for item in inventory:
            file_type = item["type"]
            summary["by_type"][file_type] = summary["by_type"].get(file_type, 0) + 1

            # Count by size
            size = item["size"]
            if size < 1024:
                summary["by_size_range"]["small"] += 1
            elif size < 1024 * 1024:
                summary["by_size_range"]["medium"] += 1
            elif size < 10 * 1024 * 1024:
                summary["by_size_range"]["large"] += 1
            else:
                summary["by_size_range"]["huge"] += 1

            # Count unreferenced
            if item["ref_count"] == 0:
                summary["unreferenced_files"] += 1

            # Count binary
            if item["bin_guess"]:
                summary["binary_files"] += 1

        # Save summary
        summary_path = self.reports_dir / f"{self.mode}_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"📊 Summary report: {summary_path}")

        # Print summary to console
        print("\n" + "=" * 60)
        print(f"📊 REPOSITORY INVENTORY SUMMARY ({self.mode.upper()})")
        print("=" * 60)
        print(f"Total files: {summary['total_files']:,}")
        print(f"Total size: {summary['total_size'] / (1024*1024):.1f} MB")
        print(f"Unreferenced files: {summary['unreferenced_files']:,}")
        print(f"Binary files: {summary['binary_files']:,}")
        print("\nBy type:")
        for file_type, count in sorted(summary["by_type"].items()):
            print(f"  {file_type}: {count:,}")
        print("\nBy size:")
        for size_range, count in summary["by_size_range"].items():
            print(f"  {size_range}: {count:,}")

    def run(self):
        """Chạy inventory scan"""
        print(f"🚀 Starting Repository Inventory Scan ({self.mode} mode)...")
        print(f"📁 Repository root: {self.repo_root}")
        print(f"📊 Reports will be saved to: {self.reports_dir}")
        print(f"🔧 Workers: {self.workers}")
        print(f"🔍 Hash calculation: {'enabled' if self.with_hash else 'disabled'}")

        # Scan repository
        inventory = self.scan_repository()

        if not inventory:
            print("⚠️ No files found to process")
            return []

        # Generate reports
        self.generate_inventory_csv(inventory)
        self.generate_large_files_report(inventory)
        self.generate_dependency_graph(inventory)
        self.generate_summary_report(inventory)

        print(f"\n✅ Repository inventory ({self.mode}) completed!")
        return inventory


def main():
    parser = argparse.ArgumentParser(
        description="Repository Inventory Tool - Two-Phase Approach"
    )
    parser.add_argument("--base-dir", default=".", help="Base directory to scan")
    parser.add_argument(
        "--mode",
        choices=["primary", "excluded", "all"],
        default="primary",
        help="Scan mode: primary (production files), excluded (artifacts), all (everything)",
    )
    parser.add_argument(
        "--exclude", help="Comma-separated list of directories to exclude"
    )
    parser.add_argument(
        "--include-ext", help="Comma-separated list of file extensions to include"
    )
    parser.add_argument("--workers", type=int, help="Number of worker processes")
    parser.add_argument(
        "--with-hash", action="store_true", help="Calculate file hashes (slower)"
    )

    args = parser.parse_args()

    # Parse exclude directories
    exclude_dirs = None
    if args.exclude:
        exclude_dirs = set(args.exclude.split(","))

    # Parse include extensions
    include_exts = None
    if args.include_ext:
        include_exts = set(args.include_ext.split(","))

    # Create inventory instance
    inventory = RepoInventory(
        repo_root=args.base_dir,
        mode=args.mode,
        exclude_dirs=exclude_dirs,
        include_exts=include_exts,
        workers=args.workers,
        with_hash=args.with_hash,
    )

    # Run inventory
    inventory.run()


if __name__ == "__main__":
    main()
