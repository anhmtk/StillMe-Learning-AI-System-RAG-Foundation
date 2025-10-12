#!/usr/bin/env python3
"""
Near-Duplicate Detector for StillMe Cleanup
Detects near-duplicate code files based on AST tokenization and cosine similarity.
"""

import os
import json
import ast
from pathlib import Path
import logging
from collections import defaultdict
from typing import List, Dict, Any
import numpy as np

# Try to import sklearn, fallback to simple implementation if not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available. Install with: pip install scikit-learn")

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent

def get_file_loc(file_path: Path) -> int:
    """Returns the number of lines of code in a file, ignoring comments and blank lines."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        loc = 0
        for line in lines:
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith('#'):
                loc += 1
        return loc
    except Exception:
        return 0

def _should_exclude_path(file_path: str, global_excludes: list) -> bool:
    """Checks if a file path should be excluded based on global exclude patterns."""
    path = Path(file_path).as_posix()
    for exclude in global_excludes:
        if Path(exclude).is_absolute():
            if Path(path) == Path(exclude) or Path(path).is_relative_to(Path(exclude)):
                return True
        else:
            if exclude.startswith('*') and path.endswith(exclude[1:]):
                return True
            if exclude.endswith('/') and f"/{exclude.strip('/')}/" in path:
                return True
            if exclude in path:
                return True
    return False

class ASTNormalizer(ast.NodeVisitor):
    """Normalizes AST nodes by replacing variable names and literals with placeholders."""
    def __init__(self):
        self.tokens = []
        self.name_map = {}
        self.counter = 0

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Param)):
            if node.id not in self.name_map:
                self.name_map[node.id] = f"VAR_{self.counter}"
                self.counter += 1
            self.tokens.append(self.name_map[node.id])
        else:
            self.tokens.append(node.id) # Keep original name for loaded variables
        self.generic_visit(node)

    def visit_Constant(self, node):
        self.tokens.append(f"LITERAL_{type(node.value).__name__.upper()}")
        self.generic_visit(node)

    def visit_Str(self, node): # For Python < 3.8
        self.tokens.append("LITERAL_STR")
        self.generic_visit(node)

    def visit_Num(self, node): # For Python < 3.8
        self.tokens.append("LITERAL_NUM")
        self.generic_visit(node)

    def visit_Bytes(self, node): # For Python < 3.8
        self.tokens.append("LITERAL_BYTES")
        self.generic_visit(node)

    def generic_visit(self, node):
        self.tokens.append(node.__class__.__name__)
        super().generic_visit(node)

    def normalize(self, tree):
        self.tokens = []
        self.name_map = {}
        self.counter = 0
        self.visit(tree)
        return " ".join(self.tokens)

def get_normalized_tokens(file_path: Path) -> str:
    """Parses a Python file and returns a normalized sequence of AST node types and masked identifiers."""
    try:
        content = file_path.read_text(encoding='utf-8')
        tree = ast.parse(content)
        normalizer = ASTNormalizer()
        return normalizer.normalize(tree)
    except (SyntaxError, UnicodeDecodeError, Exception) as e:
        logger.debug(f"Could not parse {file_path}: {e}")
        return ""

def simple_cosine_similarity(text1: str, text2: str) -> float:
    """Simple cosine similarity implementation without sklearn."""
    # Tokenize
    tokens1 = set(text1.split())
    tokens2 = set(text2.split())
    
    # Calculate intersection and union
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def detect_near_duplicates(
    root_paths: List[str],
    global_excludes: List[str],
    output_file: Path,
    min_loc: int = 30,
    similarity_threshold: float = 0.90
) -> Dict[str, Any]:
    """
    Detects near-duplicate Python files based on normalized AST tokens and cosine similarity.
    """
    file_data = {}
    all_files = []

    for root_path_str in root_paths:
        current_root = REPO_ROOT / root_path_str
        if not current_root.is_dir():
            logger.warning(f"Root path not found or not a directory: {current_root}. Skipping.")
            continue

        for file_path in current_root.rglob("*.py"):
            rel_path = str(file_path.relative_to(REPO_ROOT).as_posix())
            if _should_exclude_path(rel_path, global_excludes) or file_path.name == "__init__.py":
                logger.debug(f"Excluding file: {rel_path}")
                continue
            
            loc = get_file_loc(file_path)
            if loc < min_loc:
                logger.debug(f"Excluding small file: {rel_path} (LOC: {loc})")
                continue

            normalized_tokens = get_normalized_tokens(file_path)
            if normalized_tokens:
                file_data[rel_path] = {
                    'path': rel_path,
                    'loc': loc,
                    'tokens': normalized_tokens,
                    'parent_dir': str(file_path.parent.relative_to(REPO_ROOT).as_posix())
                }
                all_files.append(rel_path)
    
    logger.info(f"📊 Found {len(file_data)} meaningful Python files")
    
    if not file_data:
        logger.info("No files to analyze for near-duplicates.")
        results = {"near_dupe_clusters": {}}
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        return results

    # Group files by parent directory to limit comparisons
    files_by_parent = defaultdict(list)
    for rel_path, data in file_data.items():
        files_by_parent[data['parent_dir']].append(rel_path)

    near_dupe_clusters = {}
    cluster_id_counter = 0
    processed_files = set()

    for parent_dir, files_in_dir in files_by_parent.items():
        if len(files_in_dir) < 2:
            continue

        # Create similarity matrix for files in the current directory
        corpus = [file_data[f]['tokens'] for f in files_in_dir]
        if not corpus:
            continue
        
        # Calculate similarity matrix
        similarity_matrix = []
        for i in range(len(files_in_dir)):
            row = []
            for j in range(len(files_in_dir)):
                if i == j:
                    row.append(1.0)
                else:
                    if SKLEARN_AVAILABLE:
                        # Use sklearn if available
                        vectorizer = TfidfVectorizer()
                        try:
                            tfidf_matrix = vectorizer.fit_transform([corpus[i], corpus[j]])
                            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                        except ValueError:
                            similarity = simple_cosine_similarity(corpus[i], corpus[j])
                    else:
                        similarity = simple_cosine_similarity(corpus[i], corpus[j])
                    row.append(similarity)
            similarity_matrix.append(row)

        for i in range(len(files_in_dir)):
            file1_path = files_in_dir[i]
            if file1_path in processed_files:
                continue

            current_cluster_files = {file1_path}
            
            for j in range(i + 1, len(files_in_dir)):
                file2_path = files_in_dir[j]
                if file2_path in processed_files:
                    continue

                if similarity_matrix[i][j] >= similarity_threshold:
                    current_cluster_files.add(file2_path)
            
            if len(current_cluster_files) > 1:
                cluster_id = f"cluster_{cluster_id_counter}"
                near_dupe_clusters[cluster_id] = {
                    'files': sorted(list(current_cluster_files)),
                    'similarity_threshold': similarity_threshold,
                    'min_loc': min_loc
                }
                processed_files.update(current_cluster_files)
                cluster_id_counter += 1
    
    # Determine canonical files (placeholder for now, will be enriched with import/git data later)
    final_clusters = {}
    for cluster_id, cluster_data in near_dupe_clusters.items():
        files_in_cluster = cluster_data['files']
        
        # For now, just pick the first file as canonical.
        # This will be refined in redundant_score.py with actual import/git data.
        canonical_file = files_in_cluster[0] 
        non_canonical_files = [f for f in files_in_cluster if f != canonical_file]
        
        final_clusters[cluster_id] = {
            'canonical': canonical_file,
            'non_canonical': non_canonical_files,
            'files': files_in_cluster,
            'similarity_threshold': similarity_threshold,
            'min_loc': min_loc
        }

    results = {"near_dupe_clusters": final_clusters}

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📊 Results:")
    logger.info(f"  - Files scanned: {len(file_data)}")
    logger.info(f"  - Files normalized: {len([f for f_data in file_data.values() if f_data['tokens']])}")
    logger.info(f"  - Near-duplicate clusters: {len(final_clusters)}")
    logger.info(f"  - Output saved to: {output_file}")
    
    logger.info(f"\n🔍 Top near-duplicate clusters:")
    for i, (cluster_id, cluster_data) in enumerate(list(final_clusters.items())[:5]): # Print top 5 for brevity
        logger.info(f"  {i+1}. {cluster_id} ({len(cluster_data['files'])} files)")
        logger.info(f"     Canonical: {cluster_data['canonical']}")
        for nc_file in cluster_data['non_canonical']:
            logger.info(f"     Non-canonical: {nc_file}")

    return results

def main():
    """Main function to detect near-duplicates"""
    ROOT_PACKAGES = ["stillme_core", "stillme_ethical_core"]
    GLOBAL_EXCLUDES = [
        ".git/", ".github/", ".venv/", "venv/", "env/", "site-packages/", "dist/", 
        "build/", "node_modules/", "artifacts/", "reports/", "htmlcov", 
        "__pycache__/", "*.egg-info/", ".sandbox/", "_attic/"
    ]
    OUTPUT_FILE = REPO_ROOT / "artifacts" / "near_dupes.json"
    
    logger.info("🎯 Starting near-duplicate detection...")
    detect_near_duplicates(ROOT_PACKAGES, GLOBAL_EXCLUDES, OUTPUT_FILE)

if __name__ == "__main__":
    main()
