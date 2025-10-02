#!/usr/bin/env python3
"""
🚧 Quarantine Move Tool - Safe File Quarantine
Chỉ di chuyển file có risk=LOW từ primary inventory
Tạo manifest để có thể restore sau
"""

import argparse
import csv
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class QuarantineMover:
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self.reports_dir = self.repo_root / "reports"
        self.graveyard_dir = self.repo_root / "_graveyard"
        self.graveyard_dir.mkdir(exist_ok=True)

        # Load deletion candidates
        self.candidates = self.load_candidates()

        # Protected patterns (không được đụng)
        self.protected_patterns = {
            ".env", ".env.local", ".env.prod", ".env.dev",
            "policies/", "models/", "weights/", "checkpoints/",
            "data/", "deploy/", ".github/", "sandbox/"
        }

    def load_candidates(self) -> list[dict[str, Any]]:
        """Load deletion candidates từ CSV"""
        candidates_path = self.reports_dir / "deletion_candidates.csv"

        if not candidates_path.exists():
            print("❌ Deletion candidates not found. Please run find_candidates.py first.")
            return []

        candidates = []
        with open(candidates_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                candidates.append({
                    "path": row["path"],
                    "category": row["category"],
                    "reason": row["reason"],
                    "risk": row["risk"],
                    "size": int(row["size"]),
                    "ref_count": int(row["ref_count"]),
                    "last_commit": row["last_commit"],
                    "recommendation": row["recommendation"],
                    "source": row["source"]
                })

        return candidates

    def is_protected(self, file_path: str) -> bool:
        """Kiểm tra xem file có được bảo vệ không"""
        for pattern in self.protected_patterns:
            if pattern in file_path:
                return True
        return False

    def get_quarantine_candidates(self, risk_level: str = "LOW") -> list[dict[str, Any]]:
        """Lấy danh sách file có thể quarantine"""
        quarantine_candidates = []

        for candidate in self.candidates:
            if (candidate["risk"] == risk_level and
                candidate["source"] == "primary" and
                not self.is_protected(candidate["path"]) and
                candidate["recommendation"] == "QUARANTINE"):
                quarantine_candidates.append(candidate)

        return quarantine_candidates

    def create_quarantine_manifest(self, moved_files: list[dict[str, Any]]) -> None:
        """Tạo manifest file cho việc restore"""
        manifest = {
            "created_at": datetime.now().isoformat(),
            "total_files": len(moved_files),
            "total_size": sum(f["size"] for f in moved_files),
            "files": moved_files
        }

        manifest_path = self.reports_dir / "quarantine_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        print(f"📄 Quarantine manifest: {manifest_path}")

    def move_to_graveyard(self, file_path: str, candidate: dict[str, Any]) -> bool:
        """Di chuyển file vào graveyard"""
        try:
            source_path = self.repo_root / file_path
            if not source_path.exists():
                print(f"⚠️ File not found: {file_path}")
                return False

            # Tạo cấu trúc thư mục trong graveyard
            relative_path = Path(file_path)
            graveyard_path = self.graveyard_dir / relative_path
            graveyard_path.parent.mkdir(parents=True, exist_ok=True)

            # Di chuyển file
            shutil.move(str(source_path), str(graveyard_path))

            print(f"✅ Moved: {file_path} -> _graveyard/{file_path}")
            return True

        except Exception as e:
            print(f"❌ Error moving {file_path}: {e}")
            return False

    def quarantine_files(self, risk_level: str = "LOW", dry_run: bool = False) -> None:
        """Quarantine files với risk level cụ thể"""
        candidates = self.get_quarantine_candidates(risk_level)

        if not candidates:
            print(f"ℹ️ No {risk_level} risk files to quarantine.")
            return

        print(f"🚧 Found {len(candidates)} {risk_level} risk files to quarantine")

        if dry_run:
            print("🔍 DRY RUN - No files will be moved")
            for candidate in candidates:
                print(f"  - {candidate['path']} ({candidate['size']:,} bytes, {candidate['category']})")
            return

        # Confirm before moving
        total_size = sum(c["size"] for c in candidates)
        print(f"📊 Total size to quarantine: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")

        response = input("Do you want to proceed? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Quarantine cancelled.")
            return

        # Move files
        moved_files = []
        failed_files = []

        for candidate in candidates:
            if self.move_to_graveyard(candidate["path"], candidate):
                moved_files.append({
                    "original_path": candidate["path"],
                    "graveyard_path": f"_graveyard/{candidate['path']}",
                    "category": candidate["category"],
                    "reason": candidate["reason"],
                    "size": candidate["size"],
                    "moved_at": datetime.now().isoformat()
                })
            else:
                failed_files.append(candidate["path"])

        # Create manifest
        if moved_files:
            self.create_quarantine_manifest(moved_files)

        # Summary
        print("\n✅ Quarantine completed:")
        print(f"  - Moved: {len(moved_files)} files")
        print(f"  - Failed: {len(failed_files)} files")

        if failed_files:
            print("Failed files:")
            for f in failed_files:
                print(f"  - {f}")

    def list_quarantined_files(self) -> None:
        """Liệt kê các file đã quarantine"""
        manifest_path = self.reports_dir / "quarantine_manifest.json"

        if not manifest_path.exists():
            print("ℹ️ No quarantine manifest found.")
            return

        with open(manifest_path, encoding='utf-8') as f:
            manifest = json.load(f)

        print(f"📋 Quarantine Manifest (created: {manifest['created_at']})")
        print(f"Total files: {manifest['total_files']}")
        print(f"Total size: {manifest['total_size']:,} bytes ({manifest['total_size']/1024/1024:.1f} MB)")
        print("\nQuarantined files:")

        for file_info in manifest["files"]:
            print(f"  - {file_info['original_path']} ({file_info['size']:,} bytes, {file_info['category']})")

    def restore_from_graveyard(self, manifest_path: Optional[str] = None) -> None:
        """Restore files từ graveyard"""
        if manifest_path is None:
            manifest_path = str(self.reports_dir / "quarantine_manifest.json")

        if not Path(manifest_path).exists():
            print(f"❌ Manifest not found: {manifest_path}")
            return

        with open(manifest_path, encoding='utf-8') as f:
            manifest = json.load(f)

        print(f"🔄 Restoring {manifest['total_files']} files from quarantine...")

        restored_files = []
        failed_files = []

        for file_info in manifest["files"]:
            try:
                graveyard_path = self.repo_root / file_info["graveyard_path"]
                original_path = self.repo_root / file_info["original_path"]

                if not graveyard_path.exists():
                    print(f"⚠️ Graveyard file not found: {file_info['graveyard_path']}")
                    failed_files.append(file_info["original_path"])
                    continue

                # Tạo thư mục đích nếu cần
                original_path.parent.mkdir(parents=True, exist_ok=True)

                # Di chuyển file về vị trí cũ
                shutil.move(str(graveyard_path), str(original_path))

                print(f"✅ Restored: {file_info['original_path']}")
                restored_files.append(file_info["original_path"])

            except Exception as e:
                print(f"❌ Error restoring {file_info['original_path']}: {e}")
                failed_files.append(file_info["original_path"])

        # Summary
        print("\n✅ Restore completed:")
        print(f"  - Restored: {len(restored_files)} files")
        print(f"  - Failed: {len(failed_files)} files")

        if failed_files:
            print("Failed files:")
            for f in failed_files:
                print(f"  - {f}")

    def cleanup_graveyard(self) -> None:
        """Xóa hoàn toàn graveyard (không thể restore)"""
        if not self.graveyard_dir.exists():
            print("ℹ️ No graveyard found.")
            return

        # Count files
        total_files = 0
        total_size = 0

        for root, _dirs, files in os.walk(self.graveyard_dir):
            for file in files:
                file_path = Path(root) / file
                total_files += 1
                total_size += file_path.stat().st_size

        print(f"🗑️ Graveyard contains {total_files} files ({total_size:,} bytes)")

        response = input("Are you sure you want to permanently delete all quarantined files? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Cleanup cancelled.")
            return

        # Remove graveyard
        shutil.rmtree(self.graveyard_dir)

        # Remove manifest
        manifest_path = self.reports_dir / "quarantine_manifest.json"
        if manifest_path.exists():
            manifest_path.unlink()

        print("✅ Graveyard cleaned up.")

def main():
    parser = argparse.ArgumentParser(description="StillMe Quarantine Move Tool")
    parser.add_argument("--action", choices=["quarantine", "list", "restore", "cleanup"],
                       default="quarantine", help="Action to perform")
    parser.add_argument("--risk", choices=["LOW", "MEDIUM", "HIGH"],
                       default="LOW", help="Risk level to quarantine")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without actually doing it")
    parser.add_argument("--manifest", type=str,
                       help="Path to manifest file for restore action")

    args = parser.parse_args()

    mover = QuarantineMover()

    if args.action == "quarantine":
        mover.quarantine_files(args.risk, args.dry_run)
    elif args.action == "list":
        mover.list_quarantined_files()
    elif args.action == "restore":
        mover.restore_from_graveyard(args.manifest)
    elif args.action == "cleanup":
        mover.cleanup_graveyard()

if __name__ == "__main__":
    main()
