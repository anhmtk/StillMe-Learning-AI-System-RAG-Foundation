#!/usr/bin/env python3
"""
🗑️ Deletion Candidates Finder - Updated for Two-Phase Approach
Phát hiện file rác, trùng lặp, và candidates để xóa/quarantine
Chỉ đọc từ primary inventory, không đề xuất xóa excluded files
"""

import os
import json
import csv
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict

class DeletionCandidatesFinder:
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self.reports_dir = self.repo_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Load inventory data
        self.primary_inventory = self.load_primary_inventory()
        self.excluded_inventory = self.load_excluded_inventory()
        
        # Protected patterns (không được đụng)
        self.protected_patterns = {
            ".env", ".env.local", ".env.prod", ".env.dev",
            "policies/", "models/", "weights/", "checkpoints/",
            "data/", "deploy/", ".github/", "sandbox/"
        }
        
        # Junk patterns (chỉ áp dụng cho primary files)
        self.junk_patterns = {
            "backup": ["backup", "bak", "old", "archive", "temp", "tmp", "cache", "log"],
            "build": ["/build/", "/dist/", "/target/", "/out/", "/bin/", "/obj/", "/.pytest_cache/", "/__pycache__/"],
            "test_artifacts": [".coverage", "/coverage/", "/htmlcov/", "/reports/coverage/", "/.nyc_output/"],
            "ide": ["/.vscode/", "/.idea/", "*.swp", "*.swo", "*~", ".DS_Store", "Thumbs.db"],
            "node": ["/node_modules/", "npm-debug.log*", "yarn-error.log*", "package-lock.json"],
            "python": ["*.pyc", "*.pyo", "*.pyd", "/__pycache__/", "/.pytest_cache/", "*.egg-info/"],
            "logs": ["*.log", "/logs/", "*.out", "*.err", "debug.log", "error.log"]
        }
        
        # Duplicate detection
        self.file_hashes = defaultdict(list)
        self.duplicate_groups = []

    def load_primary_inventory(self) -> List[Dict[str, Any]]:
        """Load primary inventory từ CSV"""
        inventory_path = self.reports_dir / "primary_inventory.csv"
        
        if not inventory_path.exists():
            print("❌ Primary inventory not found. Please run repo_inventory.py --mode primary first.")
            return []
        
        inventory = []
        with open(inventory_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory.append({
                    "path": row["path"],
                    "size": int(row["size"]),
                    "type": row["type"],
                    "last_commit": row["last_commit"],
                    "ref_count": int(row["ref_count"]),
                    "bin_guess": row["bin_guess"] == "True",
                    "hash": row["hash"]
                })
        
        return inventory

    def load_excluded_inventory(self) -> List[Dict[str, Any]]:
        """Load excluded inventory từ CSV (optional reference)"""
        inventory_path = self.reports_dir / "excluded_inventory.csv"
        
        if not inventory_path.exists():
            return []
        
        inventory = []
        with open(inventory_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory.append({
                    "path": row["path"],
                    "size": int(row["size"]),
                    "type": row["type"],
                    "last_commit": row["last_commit"],
                    "ref_count": int(row["ref_count"]),
                    "bin_guess": row["bin_guess"] == "True",
                    "hash": row["hash"]
                })
        
        return inventory

    def is_protected(self, file_path: str) -> bool:
        """Kiểm tra xem file có được bảo vệ không"""
        for pattern in self.protected_patterns:
            if pattern in file_path:
                return True
        return False

    def classify_junk_candidates(self) -> List[Dict[str, Any]]:
        """Phân loại file rác theo patterns (chỉ từ primary inventory)"""
        candidates = []
        
        for item in self.primary_inventory:
            if self.is_protected(item["path"]):
                continue
            
            file_path = item["path"]
            file_name = Path(file_path).name.lower()
            dir_path = str(Path(file_path).parent).lower()
            
            # Check against junk patterns
            for category, patterns in self.junk_patterns.items():
                for pattern in patterns:
                    matched = False
                    
                    if pattern.startswith("/") and pattern.endswith("/"):
                        # Directory pattern (e.g., "/build/", "/dist/")
                        dir_pattern = pattern[1:-1]  # Remove leading and trailing slashes
                        if f"/{dir_pattern}/" in f"/{dir_path}/" or f"/{dir_pattern}/" in f"/{file_path}/":
                            matched = True
                    elif pattern.startswith("*"):
                        # Wildcard pattern (e.g., "*.pyc", "*.log")
                        if file_name.endswith(pattern[1:]):
                            matched = True
                    elif pattern.endswith("/"):
                        # Directory pattern without leading slash
                        dir_pattern = pattern.rstrip("/")
                        if f"/{dir_pattern}/" in f"/{dir_path}/" or f"/{dir_pattern}/" in f"/{file_path}/":
                            matched = True
                    else:
                        # Exact match pattern
                        if pattern in file_name or pattern in dir_path or pattern in file_path:
                            matched = True
                    
                    if matched:
                        candidates.append({
                            "path": file_path,
                            "category": category,
                            "reason": f"Matches pattern: {pattern}",
                            "risk": self.get_risk_level(category, item),
                            "size": item["size"],
                            "ref_count": item["ref_count"],
                            "last_commit": item["last_commit"],
                            "recommendation": self.get_recommendation(category, item),
                            "source": "primary"
                        })
                        break
        
        return candidates

    def find_duplicates(self) -> List[Dict[str, Any]]:
        """Tìm file trùng lặp dựa trên hash (chỉ từ primary inventory)"""
        # Group by hash
        hash_groups = defaultdict(list)
        
        for item in self.primary_inventory:
            if item["hash"] and not self.is_protected(item["path"]):
                hash_groups[item["hash"]].append(item)
        
        # Find groups with duplicates
        duplicate_candidates = []
        
        for file_hash, items in hash_groups.items():
            if len(items) > 1:
                # Sort by ref_count (keep most referenced)
                items.sort(key=lambda x: x["ref_count"], reverse=True)
                
                # Keep the first one, mark others for deletion
                for i, item in enumerate(items[1:], 1):
                    duplicate_candidates.append({
                        "path": item["path"],
                        "category": "duplicate",
                        "reason": f"Duplicate of {items[0]['path']} (hash: {file_hash[:8]})",
                        "risk": "LOW" if item["ref_count"] == 0 else "MEDIUM",
                        "size": item["size"],
                        "ref_count": item["ref_count"],
                        "last_commit": item["last_commit"],
                        "recommendation": "QUARANTINE" if item["ref_count"] == 0 else "REVIEW",
                        "duplicate_of": items[0]["path"],
                        "source": "primary"
                    })
        
        return duplicate_candidates

    def find_unreferenced_files(self) -> List[Dict[str, Any]]:
        """Tìm file không được reference (chỉ từ primary inventory)"""
        candidates = []
        
        for item in self.primary_inventory:
            if (self.is_protected(item["path"]) or 
                item["ref_count"] > 0 or 
                item["type"] in ["config", "doc"]):
                continue
            
            # Skip if it's a main entry point
            if any(main_file in item["path"] for main_file in ["main.py", "app.py", "index.js", "main.dart"]):
                continue
            
            candidates.append({
                "path": item["path"],
                "category": "unreferenced",
                "reason": f"No references found (ref_count: {item['ref_count']})",
                "risk": "LOW" if item["type"] in ["test", "bin"] else "MEDIUM",
                "size": item["size"],
                "ref_count": item["ref_count"],
                "last_commit": item["last_commit"],
                "recommendation": "QUARANTINE" if item["type"] in ["test", "bin"] else "REVIEW",
                "source": "primary"
            })
        
        return candidates

    def find_large_files(self) -> List[Dict[str, Any]]:
        """Tìm file lớn có thể cần xử lý (chỉ từ primary inventory)"""
        candidates = []
        
        for item in self.primary_inventory:
            if self.is_protected(item["path"]):
                continue
            
            size_mb = item["size"] / (1024 * 1024)
            
            if size_mb > 10:  # > 10MB
                candidates.append({
                    "path": item["path"],
                    "category": "large_file",
                    "reason": f"Large file: {size_mb:.1f}MB",
                    "risk": "MEDIUM" if item["type"] == "bin" else "HIGH",
                    "size": item["size"],
                    "ref_count": item["ref_count"],
                    "last_commit": item["last_commit"],
                    "recommendation": "REVIEW" if item["type"] == "bin" else "QUARANTINE",
                    "source": "primary"
                })
        
        return candidates

    def find_old_files(self) -> List[Dict[str, Any]]:
        """Tìm file cũ không được sử dụng (chỉ từ primary inventory)"""
        candidates = []
        cutoff_date = datetime.now() - timedelta(days=90)  # 90 days ago
        
        for item in self.primary_inventory:
            if (self.is_protected(item["path"]) or 
                item["ref_count"] > 0 or
                item["type"] in ["config", "doc"]):
                continue
            
            # Try to parse last commit date
            try:
                if item["last_commit"] != "unknown":
                    # This is simplified - in reality, we'd parse the actual date
                    # For now, we'll use a heuristic based on file type and size
                    if item["type"] in ["test", "bin"] and item["size"] < 1024 * 1024:
                        candidates.append({
                            "path": item["path"],
                            "category": "old_file",
                            "reason": f"Old file with no references (type: {item['type']})",
                            "risk": "LOW",
                            "size": item["size"],
                            "ref_count": item["ref_count"],
                            "last_commit": item["last_commit"],
                            "recommendation": "QUARANTINE",
                            "source": "primary"
                        })
            except:
                pass
        
        return candidates

    def get_risk_level(self, category: str, item: Dict[str, Any]) -> str:
        """Xác định mức độ rủi ro"""
        if item["ref_count"] > 0:
            return "HIGH"
        
        risk_map = {
            "backup": "LOW",
            "build": "LOW", 
            "test_artifacts": "LOW",
            "ide": "LOW",
            "node": "LOW",
            "python": "LOW",
            "logs": "LOW"
        }
        
        return risk_map.get(category, "MEDIUM")

    def get_recommendation(self, category: str, item: Dict[str, Any]) -> str:
        """Đưa ra khuyến nghị"""
        if item["ref_count"] > 0:
            return "REVIEW"
        
        if category in ["backup", "build", "test_artifacts", "ide", "node", "python", "logs"]:
            return "QUARANTINE"
        
        return "REVIEW"

    def generate_report(self, all_candidates: List[Dict[str, Any]]) -> None:
        """Tạo báo cáo deletion candidates"""
        report_path = self.reports_dir / "deletion_candidates.md"
        
        # Group by category
        by_category = defaultdict(list)
        for candidate in all_candidates:
            by_category[candidate["category"]].append(candidate)
        
        # Group by risk
        by_risk = defaultdict(list)
        for candidate in all_candidates:
            by_risk[candidate["risk"]].append(candidate)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 🗑️ Deletion Candidates Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            f.write("## 📊 Summary\n\n")
            f.write(f"- **Total candidates**: {len(all_candidates)}\n")
            f.write(f"- **By risk level**:\n")
            for risk in ["LOW", "MEDIUM", "HIGH"]:
                count = len(by_risk[risk])
                f.write(f"  - {risk}: {count}\n")
            f.write(f"- **By category**:\n")
            for category, items in by_category.items():
                f.write(f"  - {category}: {len(items)}\n")
            
            # Risk-based sections
            for risk in ["LOW", "MEDIUM", "HIGH"]:
                if not by_risk[risk]:
                    continue
                
                f.write(f"\n## 🔴 {risk} Risk Candidates\n\n")
                
                for candidate in by_risk[risk]:
                    f.write(f"### {candidate['path']}\n")
                    f.write(f"- **Category**: {candidate['category']}\n")
                    f.write(f"- **Reason**: {candidate['reason']}\n")
                    f.write(f"- **Size**: {candidate['size']:,} bytes\n")
                    f.write(f"- **References**: {candidate['ref_count']}\n")
                    f.write(f"- **Last commit**: {candidate['last_commit']}\n")
                    f.write(f"- **Recommendation**: {candidate['recommendation']}\n")
                    f.write(f"- **Source**: {candidate['source']}\n\n")
            
            # Category-based sections
            f.write("\n## 📁 By Category\n\n")
            for category, items in by_category.items():
                f.write(f"### {category.title()} ({len(items)} items)\n\n")
                
                # Sort by size (largest first)
                items.sort(key=lambda x: x["size"], reverse=True)
                
                for item in items[:10]:  # Show top 10
                    f.write(f"- `{item['path']}` ({item['size']:,} bytes, {item['risk']} risk)\n")
                
                if len(items) > 10:
                    f.write(f"- ... and {len(items) - 10} more\n")
                f.write("\n")
        
        print(f"📄 Deletion candidates report: {report_path}")

    def generate_csv_report(self, all_candidates: List[Dict[str, Any]]) -> None:
        """Tạo CSV report cho quarantine tool"""
        csv_path = self.reports_dir / "deletion_candidates.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["path", "category", "reason", "risk", "size", "ref_count", "last_commit", "recommendation", "source"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for candidate in all_candidates:
                writer.writerow({
                    "path": candidate["path"],
                    "category": candidate["category"],
                    "reason": candidate["reason"],
                    "risk": candidate["risk"],
                    "size": candidate["size"],
                    "ref_count": candidate["ref_count"],
                    "last_commit": candidate["last_commit"],
                    "recommendation": candidate["recommendation"],
                    "source": candidate["source"]
                })
        
        print(f"📊 CSV report: {csv_path}")

    def run(self):
        """Chạy tìm kiếm candidates"""
        print("🗑️ Finding deletion candidates...")
        
        if not self.primary_inventory:
            print("❌ No primary inventory data found. Please run repo_inventory.py --mode primary first.")
            return
        
        print(f"📋 Primary inventory: {len(self.primary_inventory)} files")
        if self.excluded_inventory:
            print(f"📋 Excluded inventory: {len(self.excluded_inventory)} files (reference only)")
        
        # Find different types of candidates
        print("  🔍 Finding junk files...")
        junk_candidates = self.classify_junk_candidates()
        
        print("  🔍 Finding duplicates...")
        duplicate_candidates = self.find_duplicates()
        
        print("  🔍 Finding unreferenced files...")
        unreferenced_candidates = self.find_unreferenced_files()
        
        print("  🔍 Finding large files...")
        large_candidates = self.find_large_files()
        
        print("  🔍 Finding old files...")
        old_candidates = self.find_old_files()
        
        # Combine all candidates
        all_candidates = (junk_candidates + duplicate_candidates + 
                         unreferenced_candidates + large_candidates + old_candidates)
        
        # Remove duplicates
        seen_paths = set()
        unique_candidates = []
        for candidate in all_candidates:
            if candidate["path"] not in seen_paths:
                seen_paths.add(candidate["path"])
                unique_candidates.append(candidate)
        
        # Generate reports
        self.generate_report(unique_candidates)
        self.generate_csv_report(unique_candidates)
        
        # Print summary
        print(f"\n✅ Found {len(unique_candidates)} deletion candidates")
        
        by_risk = defaultdict(int)
        for candidate in unique_candidates:
            by_risk[candidate["risk"]] += 1
        
        print("By risk level:")
        for risk in ["LOW", "MEDIUM", "HIGH"]:
            print(f"  {risk}: {by_risk[risk]}")
        
        return unique_candidates

if __name__ == "__main__":
    finder = DeletionCandidatesFinder()
    finder.run()