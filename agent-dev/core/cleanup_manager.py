#!/usr/bin/env python3
"""
Cleanup Manager - Senior Developer Cleanup Thinking Module
Tư duy dọn dẹp như dev chuyên nghiệp thật

Tính năng:
1. Redundant File Detection - Phát hiện file dư thừa
2. Dead Code Detection - Phát hiện code chết
3. Unused Import Detection - Phát hiện import không dùng
4. Duplicate Code Detection - Phát hiện code trùng lặp
5. Temporary File Cleanup - Dọn dẹp file tạm
6. Cache Cleanup - Dọn dẹp cache
7. Log File Management - Quản lý log files
8. Dependency Cleanup - Dọn dẹp dependencies
"""

import os
import re
import time
import shutil
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import ast
import subprocess

class CleanupType(Enum):
    """Loại dọn dẹp"""
    REDUNDANT_FILES = "redundant_files"
    DEAD_CODE = "dead_code"
    UNUSED_IMPORTS = "unused_imports"
    DUPLICATE_CODE = "duplicate_code"
    TEMP_FILES = "temp_files"
    CACHE_FILES = "cache_files"
    LOG_FILES = "log_files"
    UNUSED_DEPENDENCIES = "unused_dependencies"

class CleanupPriority(Enum):
    """Mức độ ưu tiên dọn dẹp"""
    CRITICAL = "critical"      # Cần dọn ngay
    HIGH = "high"             # Ưu tiên cao
    MEDIUM = "medium"         # Ưu tiên trung bình
    LOW = "low"               # Ưu tiên thấp
    OPTIONAL = "optional"     # Tùy chọn

@dataclass
class CleanupItem:
    """Item cần dọn dẹp"""
    item_type: CleanupType
    priority: CleanupPriority
    file_path: str
    description: str
    size_bytes: int
    last_accessed: float
    reason: str
    safe_to_delete: bool
    backup_required: bool
    dependencies: List[str]

@dataclass
class CleanupResult:
    """Kết quả dọn dẹp"""
    cleanup_type: CleanupType
    items_found: List[CleanupItem]
    items_cleaned: List[CleanupItem]
    space_saved: int
    errors: List[str]
    warnings: List[str]
    execution_time: float

@dataclass
class CleanupAnalysis:
    """Phân tích dọn dẹp"""
    total_items: int
    total_size: int
    cleanup_results: List[CleanupResult]
    recommendations: List[str]
    risk_assessment: str
    estimated_savings: int
    analysis_time: float

class CleanupManager:
    """Senior Developer Cleanup Manager"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.temp_patterns = self._load_temp_patterns()
        self.cache_patterns = self._load_cache_patterns()
        self.log_patterns = self._load_log_patterns()
        self.redundant_patterns = self._load_redundant_patterns()
        
    def _load_temp_patterns(self) -> List[str]:
        """Load temporary file patterns"""
        return [
            r'\.tmp$', r'\.temp$', r'\.bak$', r'\.backup$',
            r'~$', r'\.swp$', r'\.swo$', r'\.orig$',
            r'\.pyc$', r'\.pyo$', r'__pycache__',
            r'\.DS_Store$', r'Thumbs\.db$',
            r'\.log$', r'\.out$', r'\.err$'
        ]
    
    def _load_cache_patterns(self) -> List[str]:
        """Load cache file patterns"""
        return [
            r'\.cache$', r'\.cache/.*', r'cache/.*',
            r'\.npm$', r'node_modules/.*',
            r'\.pip$', r'\.conda$',
            r'\.mypy_cache$', r'\.pytest_cache$',
            r'\.coverage$', r'htmlcov/.*'
        ]
    
    def _load_log_patterns(self) -> List[str]:
        """Load log file patterns"""
        return [
            r'\.log$', r'logs/.*', r'log/.*',
            r'debug\.log$', r'error\.log$', r'access\.log$',
            r'\.out$', r'\.err$', r'stderr\.log$', r'stdout\.log$'
        ]
    
    def _load_redundant_patterns(self) -> List[str]:
        """Load redundant file patterns"""
        return [
            r'\.old$', r'\.backup$', r'\.bak$',
            r'\.copy$', r'\.duplicate$', r'\.orig$',
            r'\.test$', r'\.spec$', r'\.example$',
            r'\.sample$', r'\.template$'
        ]
    
    def find_redundant_files(self) -> List[CleanupItem]:
        """Tìm file dư thừa"""
        redundant_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check if file matches redundant patterns
                for pattern in self.redundant_patterns:
                    if re.search(pattern, file, re.IGNORECASE):
                        stat = file_path.stat()
                        redundant_files.append(CleanupItem(
                            item_type=CleanupType.REDUNDANT_FILES,
                            priority=CleanupPriority.MEDIUM,
                            file_path=str(file_path),
                            description=f"Redundant file: {file}",
                            size_bytes=stat.st_size,
                            last_accessed=stat.st_atime,
                            reason=f"Matches pattern: {pattern}",
                            safe_to_delete=True,
                            backup_required=False,
                            dependencies=[]
                        ))
                        break
        
        return redundant_files
    
    def find_temp_files(self) -> List[CleanupItem]:
        """Tìm file tạm"""
        temp_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check if file matches temp patterns
                for pattern in self.temp_patterns:
                    if re.search(pattern, file, re.IGNORECASE):
                        stat = file_path.stat()
                        temp_files.append(CleanupItem(
                            item_type=CleanupType.TEMP_FILES,
                            priority=CleanupPriority.HIGH,
                            file_path=str(file_path),
                            description=f"Temporary file: {file}",
                            size_bytes=stat.st_size,
                            last_accessed=stat.st_atime,
                            reason=f"Matches temp pattern: {pattern}",
                            safe_to_delete=True,
                            backup_required=False,
                            dependencies=[]
                        ))
                        break
        
        return temp_files
    
    def find_cache_files(self) -> List[CleanupItem]:
        """Tìm file cache"""
        cache_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check if file matches cache patterns
                for pattern in self.cache_patterns:
                    if re.search(pattern, file, re.IGNORECASE):
                        stat = file_path.stat()
                        cache_files.append(CleanupItem(
                            item_type=CleanupType.CACHE_FILES,
                            priority=CleanupPriority.MEDIUM,
                            file_path=str(file_path),
                            description=f"Cache file: {file}",
                            size_bytes=stat.st_size,
                            last_accessed=stat.st_atime,
                            reason=f"Matches cache pattern: {pattern}",
                            safe_to_delete=True,
                            backup_required=False,
                            dependencies=[]
                        ))
                        break
        
        return cache_files
    
    def find_log_files(self) -> List[CleanupItem]:
        """Tìm file log"""
        log_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check if file matches log patterns
                for pattern in self.log_patterns:
                    if re.search(pattern, file, re.IGNORECASE):
                        stat = file_path.stat()
                        log_files.append(CleanupItem(
                            item_type=CleanupType.LOG_FILES,
                            priority=CleanupPriority.LOW,
                            file_path=str(file_path),
                            description=f"Log file: {file}",
                            size_bytes=stat.st_size,
                            last_accessed=stat.st_atime,
                            reason=f"Matches log pattern: {pattern}",
                            safe_to_delete=True,
                            backup_required=True,
                            dependencies=[]
                        ))
                        break
        
        return log_files
    
    def find_dead_code(self) -> List[CleanupItem]:
        """Tìm code chết"""
        dead_code_items = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Only process Python files
            files = [f for f in files if f.endswith('.py')]
            
            for file in files:
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse AST to find unused functions/classes
                    tree = ast.parse(content)
                    unused_items = self._find_unused_ast_nodes(tree, content)
                    
                    for item in unused_items:
                        dead_code_items.append(CleanupItem(
                            item_type=CleanupType.DEAD_CODE,
                            priority=CleanupPriority.MEDIUM,
                            file_path=str(file_path),
                            description=f"Unused {item['type']}: {item['name']}",
                            size_bytes=len(item['code']),
                            last_accessed=0,
                            reason="Code is defined but never used",
                            safe_to_delete=False,
                            backup_required=True,
                            dependencies=[]
                        ))
                
                except Exception as e:
                    continue
        
        return dead_code_items
    
    def _find_unused_ast_nodes(self, tree: ast.AST, content: str) -> List[Dict]:
        """Find unused AST nodes"""
        unused_items = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function is used
                if not self._is_function_used(node.name, content):
                    unused_items.append({
                        'type': 'function',
                        'name': node.name,
                        'code': ast.get_source_segment(content, node)
                    })
            
            elif isinstance(node, ast.ClassDef):
                # Check if class is used
                if not self._is_class_used(node.name, content):
                    unused_items.append({
                        'type': 'class',
                        'name': node.name,
                        'code': ast.get_source_segment(content, node)
                    })
        
        return unused_items
    
    def _is_function_used(self, func_name: str, content: str) -> bool:
        """Check if function is used"""
        # Simple heuristic: look for function calls
        pattern = rf'\b{func_name}\s*\('
        return bool(re.search(pattern, content))
    
    def _is_class_used(self, class_name: str, content: str) -> bool:
        """Check if class is used"""
        # Simple heuristic: look for class instantiation or inheritance
        patterns = [
            rf'\b{class_name}\s*\(',
            rf'class\s+\w+\s*\(\s*{class_name}',
            rf'from\s+\w+\s+import.*{class_name}',
            rf'import.*{class_name}'
        ]
        return any(re.search(pattern, content) for pattern in patterns)
    
    def find_unused_imports(self) -> List[CleanupItem]:
        """Tìm import không dùng"""
        unused_imports = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Only process Python files
            files = [f for f in files if f.endswith('.py')]
            
            for file in files:
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse AST to find imports
                    tree = ast.parse(content)
                    unused_imports_in_file = self._find_unused_imports_in_ast(tree, content)
                    
                    for import_item in unused_imports_in_file:
                        unused_imports.append(CleanupItem(
                            item_type=CleanupType.UNUSED_IMPORTS,
                            priority=CleanupPriority.LOW,
                            file_path=str(file_path),
                            description=f"Unused import: {import_item}",
                            size_bytes=len(import_item),
                            last_accessed=0,
                            reason="Import is not used in the code",
                            safe_to_delete=True,
                            backup_required=False,
                            dependencies=[]
                        ))
                
                except Exception as e:
                    continue
        
        return unused_imports
    
    def _find_unused_imports_in_ast(self, tree: ast.AST, content: str) -> List[str]:
        """Find unused imports in AST"""
        unused_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not self._is_import_used(alias.name, content):
                        unused_imports.append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if not self._is_import_used(alias.name, content):
                        unused_imports.append(alias.name)
        
        return unused_imports
    
    def _is_import_used(self, import_name: str, content: str) -> bool:
        """Check if import is used"""
        # Simple heuristic: look for usage
        pattern = rf'\b{import_name}\b'
        return bool(re.search(pattern, content))
    
    def find_duplicate_code(self) -> List[CleanupItem]:
        """Tìm code trùng lặp"""
        duplicate_items = []
        
        # Get all Python files
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            files = [f for f in files if f.endswith('.py')]
            for file in files:
                python_files.append(Path(root) / file)
        
        # Compare files for duplicates
        file_hashes = {}
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create hash of content
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                if content_hash in file_hashes:
                    # Found duplicate
                    original_file = file_hashes[content_hash]
                    stat = file_path.stat()
                    
                    duplicate_items.append(CleanupItem(
                        item_type=CleanupType.DUPLICATE_CODE,
                        priority=CleanupPriority.HIGH,
                        file_path=str(file_path),
                        description=f"Duplicate of {original_file}",
                        size_bytes=stat.st_size,
                        last_accessed=stat.st_atime,
                        reason="File content is identical to another file",
                        safe_to_delete=False,
                        backup_required=True,
                        dependencies=[original_file]
                    ))
                else:
                    file_hashes[content_hash] = str(file_path)
            
            except Exception as e:
                continue
        
        return duplicate_items
    
    def find_unused_dependencies(self) -> List[CleanupItem]:
        """Tìm dependencies không dùng"""
        unused_deps = []
        
        # Check requirements.txt
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    requirements = f.read().splitlines()
                
                for req in requirements:
                    if req.strip() and not req.startswith('#'):
                        package_name = req.split('==')[0].split('>=')[0].split('<=')[0]
                        if not self._is_package_used(package_name):
                            unused_deps.append(CleanupItem(
                                item_type=CleanupType.UNUSED_DEPENDENCIES,
                                priority=CleanupPriority.MEDIUM,
                                file_path=str(requirements_file),
                                description=f"Unused dependency: {package_name}",
                                size_bytes=len(req),
                                last_accessed=0,
                                reason="Package is not imported in the codebase",
                                safe_to_delete=True,
                                backup_required=False,
                                dependencies=[]
                            ))
            
            except Exception as e:
                pass
        
        return unused_deps
    
    def _is_package_used(self, package_name: str) -> bool:
        """Check if package is used in codebase"""
        # Simple heuristic: look for import statements
        for root, dirs, files in os.walk(self.project_root):
            files = [f for f in files if f.endswith('.py')]
            for file in files:
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if f'import {package_name}' in content or f'from {package_name}' in content:
                        return True
                
                except Exception as e:
                    continue
        
        return False
    
    def cleanup_items(self, items: List[CleanupItem], dry_run: bool = True) -> CleanupResult:
        """Dọn dẹp các items"""
        start_time = time.time()
        cleaned_items = []
        errors = []
        warnings = []
        space_saved = 0
        
        for item in items:
            if not item.safe_to_delete:
                warnings.append(f"Skipping unsafe item: {item.file_path}")
                continue
            
            try:
                if dry_run:
                    # Just simulate cleanup
                    cleaned_items.append(item)
                    space_saved += item.size_bytes
                else:
                    # Actually delete the file
                    if item.backup_required:
                        # Create backup
                        backup_path = f"{item.file_path}.backup"
                        shutil.copy2(item.file_path, backup_path)
                    
                    if os.path.exists(item.file_path):
                        os.remove(item.file_path)
                        cleaned_items.append(item)
                        space_saved += item.size_bytes
                    
            except Exception as e:
                errors.append(f"Failed to cleanup {item.file_path}: {str(e)}")
        
        execution_time = time.time() - start_time
        
        return CleanupResult(
            cleanup_type=CleanupType.REDUNDANT_FILES,  # Default type
            items_found=items,
            items_cleaned=cleaned_items,
            space_saved=space_saved,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time
        )
    
    def analyze_cleanup_opportunities(self) -> CleanupAnalysis:
        """Phân tích cơ hội dọn dẹp"""
        start_time = time.time()
        
        # Find all types of cleanup items
        redundant_files = self.find_redundant_files()
        temp_files = self.find_temp_files()
        cache_files = self.find_cache_files()
        log_files = self.find_log_files()
        dead_code = self.find_dead_code()
        unused_imports = self.find_unused_imports()
        duplicate_code = self.find_duplicate_code()
        unused_deps = self.find_unused_dependencies()
        
        # Combine all items
        all_items = redundant_files + temp_files + cache_files + log_files + dead_code + unused_imports + duplicate_code + unused_deps
        
        # Calculate totals
        total_items = len(all_items)
        total_size = sum(item.size_bytes for item in all_items)
        
        # Generate recommendations
        recommendations = []
        if temp_files:
            recommendations.append(f"Clean {len(temp_files)} temporary files to save {sum(f.size_bytes for f in temp_files)} bytes")
        if cache_files:
            recommendations.append(f"Clean {len(cache_files)} cache files to save {sum(f.size_bytes for f in cache_files)} bytes")
        if dead_code:
            recommendations.append(f"Remove {len(dead_code)} unused functions/classes to improve code quality")
        if duplicate_code:
            recommendations.append(f"Remove {len(duplicate_code)} duplicate files to reduce maintenance burden")
        
        # Risk assessment
        critical_items = [item for item in all_items if item.priority == CleanupPriority.CRITICAL]
        high_priority_items = [item for item in all_items if item.priority == CleanupPriority.HIGH]
        
        if critical_items:
            risk_assessment = "HIGH - Critical cleanup items found"
        elif high_priority_items:
            risk_assessment = "MEDIUM - High priority cleanup items found"
        else:
            risk_assessment = "LOW - Only low priority cleanup items found"
        
        analysis_time = time.time() - start_time
        
        return CleanupAnalysis(
            total_items=total_items,
            total_size=total_size,
            cleanup_results=[],  # Will be populated when cleanup is executed
            recommendations=recommendations,
            risk_assessment=risk_assessment,
            estimated_savings=total_size,
            analysis_time=analysis_time
        )

# Test function
if __name__ == "__main__":
    manager = CleanupManager()
    analysis = manager.analyze_cleanup_opportunities()
    
    print("=== CLEANUP ANALYSIS RESULT ===")
    print(f"Total Items: {analysis.total_items}")
    print(f"Total Size: {analysis.total_size} bytes")
    print(f"Risk Assessment: {analysis.risk_assessment}")
    print(f"Recommendations: {len(analysis.recommendations)}")
    print(f"Analysis Time: {analysis.analysis_time:.3f}s")
