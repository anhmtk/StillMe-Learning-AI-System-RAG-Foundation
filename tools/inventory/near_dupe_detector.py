#!/usr/bin/env python3
"""
Near-Duplicate Code Detector
Detects near-duplicate code using AST normalization and cosine similarity
"""

import os
import ast
import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
import hashlib

def normalize_ast_code(code: str) -> str:
    """Normalize code by removing variable names and literals"""
    try:
        tree = ast.parse(code)
        normalized_tokens = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                normalized_tokens.append(f"def_{len(node.args.args)}")
            elif isinstance(node, ast.ClassDef):
                normalized_tokens.append("class_def")
            elif isinstance(node, ast.If):
                normalized_tokens.append("if_stmt")
            elif isinstance(node, ast.For):
                normalized_tokens.append("for_loop")
            elif isinstance(node, ast.While):
                normalized_tokens.append("while_loop")
            elif isinstance(node, ast.Try):
                normalized_tokens.append("try_except")
            elif isinstance(node, ast.Return):
                normalized_tokens.append("return_stmt")
            elif isinstance(node, ast.Assign):
                normalized_tokens.append("assign_stmt")
            elif isinstance(node, ast.Call):
                normalized_tokens.append("function_call")
            elif isinstance(node, ast.Import):
                normalized_tokens.append("import_stmt")
            elif isinstance(node, ast.ImportFrom):
                normalized_tokens.append("from_import_stmt")
            elif isinstance(node, ast.List):
                normalized_tokens.append("list_literal")
            elif isinstance(node, ast.Dict):
                normalized_tokens.append("dict_literal")
            elif isinstance(node, ast.Set):
                normalized_tokens.append("set_literal")
            elif isinstance(node, ast.Tuple):
                normalized_tokens.append("tuple_literal")
        
        return " ".join(normalized_tokens)
    except SyntaxError:
        return ""

def get_file_loc(file_path: str) -> int:
    """Get lines of code for a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return len([line for line in f if line.strip() and not line.strip().startswith('#')])
    except Exception:
        return 0

def should_exclude_path(file_path: str) -> bool:
    """Check if path should be excluded"""
    excludes = [
        ".git/", ".github/", ".venv/", "venv/", "env/", "site-packages/",
        "dist/", "build/", "node_modules/", "artifacts/", "reports/",
        "htmlcov", "__pycache__/", "*.egg-info/", ".sandbox/"
    ]
    
    path = Path(file_path).as_posix()
    for exclude in excludes:
        if exclude.endswith('/') and f"/{exclude}" in path:
            return True
        elif exclude.startswith('*') and path.endswith(exclude[1:]):
            return True
        elif exclude in path:
            return True
    return False

def is_meaningful_file(file_path: str, min_loc: int = 30) -> bool:
    """Check if file is meaningful (not just docstrings/comments)"""
    loc = get_file_loc(file_path)
    if loc < min_loc:
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Skip files that are mostly docstrings/comments
        lines = content.split('\n')
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        
        if len(code_lines) < min_loc:
            return False
            
        # Skip files that are mostly docstrings
        docstring_lines = 0
        for line in lines:
            if '"""' in line or "'''" in line:
                docstring_lines += 1
                
        if docstring_lines > len(lines) * 0.7:
            return False
            
        return True
    except Exception:
        return False

def calculate_cosine_similarity(tokens1: str, tokens2: str) -> float:
    """Calculate cosine similarity between two token strings"""
    if not tokens1 or not tokens2:
        return 0.0
    
    # Simple word frequency approach
    words1 = tokens1.split()
    words2 = tokens2.split()
    
    # Create vocabulary
    vocab = set(words1 + words2)
    if not vocab:
        return 0.0
    
    # Create frequency vectors
    vec1 = [words1.count(word) for word in vocab]
    vec2 = [words2.count(word) for word in vocab]
    
    # Calculate cosine similarity
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)

def find_near_duplicates(root_path: str = ".", similarity_threshold: float = 0.90) -> Dict[str, Any]:
    """Find near-duplicate files using AST normalization and cosine similarity"""
    
    print("🔍 Scanning Python files for near-duplicates...")
    
    # Collect all Python files
    python_files = []
    for root, dirs, files in os.walk(root_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not should_exclude_path(os.path.join(root, d))]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_path)
                
                if should_exclude_path(rel_path):
                    continue
                    
                if is_meaningful_file(file_path):
                    python_files.append(rel_path)
    
    print(f"📊 Found {len(python_files)} meaningful Python files")
    
    # Normalize code for each file
    file_tokens = {}
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            normalized = normalize_ast_code(content)
            if normalized:
                file_tokens[file_path] = normalized
        except Exception as e:
            print(f"⚠️ Could not process {file_path}: {e}")
    
    print(f"📝 Normalized {len(file_tokens)} files")
    
    # Find near-duplicates by comparing files in the same directory
    near_dupe_clusters = {}
    cluster_id = 0
    
    # Group files by parent directory
    dir_files = defaultdict(list)
    for file_path in file_tokens.keys():
        parent_dir = str(Path(file_path).parent)
        dir_files[parent_dir].append(file_path)
    
    # Compare files within each directory
    for parent_dir, files in dir_files.items():
        if len(files) < 2:
            continue
            
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                similarity = calculate_cosine_similarity(
                    file_tokens[file1], 
                    file_tokens[file2]
                )
                
                if similarity >= similarity_threshold:
                    # Create or add to cluster
                    cluster_key = f"cluster_{cluster_id}"
                    if cluster_key not in near_dupe_clusters:
                        near_dupe_clusters[cluster_key] = {
                            "files": [],
                            "similarity_scores": {},
                            "parent_dir": parent_dir
                        }
                        cluster_id += 1
                    
                    near_dupe_clusters[cluster_key]["files"].extend([file1, file2])
                    near_dupe_clusters[cluster_key]["similarity_scores"][f"{file1}__{file2}"] = similarity
    
    # Remove duplicates and calculate canonical files
    for cluster_key, cluster_data in near_dupe_clusters.items():
        cluster_data["files"] = list(set(cluster_data["files"]))
        
        # Choose canonical file (heuristic: most recent, most touched, or alphabetically first)
        canonical = min(cluster_data["files"])
        cluster_data["canonical"] = canonical
        cluster_data["non_canonical"] = [f for f in cluster_data["files"] if f != canonical]
    
    return {
        "near_dupe_clusters": near_dupe_clusters,
        "total_files_scanned": len(python_files),
        "total_files_normalized": len(file_tokens),
        "total_clusters": len(near_dupe_clusters),
        "similarity_threshold": similarity_threshold
    }

def main():
    """Main function"""
    print("🎯 Starting near-duplicate detection...")
    
    # Ensure artifacts directory exists
    os.makedirs("artifacts", exist_ok=True)
    
    # Find near-duplicates
    results = find_near_duplicates()
    
    # Save results
    output_file = "artifacts/near_dupes.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Results:")
    print(f"  - Files scanned: {results['total_files_scanned']}")
    print(f"  - Files normalized: {results['total_files_normalized']}")
    print(f"  - Near-duplicate clusters: {results['total_clusters']}")
    print(f"  - Output saved to: {output_file}")
    
    # Show top clusters
    if results['near_dupe_clusters']:
        print(f"\n🔍 Top near-duplicate clusters:")
        for i, (cluster_key, cluster_data) in enumerate(list(results['near_dupe_clusters'].items())[:5]):
            print(f"  {i+1}. {cluster_key} ({len(cluster_data['files'])} files)")
            print(f"     Canonical: {cluster_data['canonical']}")
            print(f"     Non-canonical: {', '.join(cluster_data['non_canonical'][:2])}")
            if len(cluster_data['non_canonical']) > 2:
                print(f"     ... and {len(cluster_data['non_canonical']) - 2} more")

if __name__ == "__main__":
    main()
