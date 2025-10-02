"""
Semantic Search for AgentDev
SEAL-GRADE Intelligent Code Understanding

Features:
- Local embeddings for code similarity
- Semantic search across codebase
- Related file discovery
- Code pattern matching
- Integration with AST analysis
"""

import ast
import hashlib
import json
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """Search type enumeration"""

    SIMILARITY = "similarity"
    PATTERN = "pattern"
    CONTEXT = "context"
    DEPENDENCY = "dependency"


class MatchType(Enum):
    """Match type enumeration"""

    EXACT = "exact"
    SEMANTIC = "semantic"
    PATTERN = "pattern"
    CONTEXTUAL = "contextual"


@dataclass
class SearchResult:
    """Search result"""

    file_path: str
    line_number: int
    content: str
    match_type: MatchType
    similarity_score: float
    context: str
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CodeEmbedding:
    """Code embedding representation"""

    file_path: str
    function_name: str
    embedding: list[float]
    content: str
    line_number: int
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SemanticSearchEngine:
    """SEAL-GRADE Semantic Search Engine"""

    def __init__(self, project_root: str = ".", embedding_dim: int = 128):
        self.project_root = Path(project_root).resolve()
        self.embedding_dim = embedding_dim
        self.embeddings: dict[str, CodeEmbedding] = {}
        self.file_contents: dict[str, str] = {}
        self.function_index: dict[str, list[str]] = defaultdict(list)
        self.pattern_cache: dict[str, list[SearchResult]] = {}
        self._similarity_cache: dict[tuple[str, str], float] = {}

    def build_index(
        self, include_patterns: list[str] = None, exclude_patterns: list[str] = None
    ) -> dict[str, Any]:
        """Build semantic search index"""
        if include_patterns is None:
            include_patterns = ["*.py"]
        if exclude_patterns is None:
            exclude_patterns = ["__pycache__", "*.pyc", ".git", "node_modules", "tests"]

        start_time = time.time()

        # Find all Python files
        python_files = self._find_python_files(include_patterns, exclude_patterns)

        # Process each file
        for file_path in python_files:
            try:
                self._process_file(file_path)
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")

        # Build embeddings
        self._build_embeddings()

        # Build function index
        self._build_function_index()

        build_time = time.time() - start_time

        return {
            "total_files": len(python_files),
            "total_embeddings": len(self.embeddings),
            "build_time": build_time,
            "index_size_mb": self._calculate_index_size(),
        }

    def _find_python_files(
        self, include_patterns: list[str], exclude_patterns: list[str]
    ) -> list[Path]:
        """Find Python files matching patterns"""
        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [
                d
                for d in dirs
                if not any(
                    self._match_pattern(pattern, d) for pattern in exclude_patterns
                )
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    # Check if file should be included
                    if any(
                        self._match_pattern(
                            pattern, str(file_path.relative_to(self.project_root))
                        )
                        for pattern in include_patterns
                    ):
                        python_files.append(file_path)

        return python_files

    def _match_pattern(self, pattern: str, text: str) -> bool:
        """Match pattern with proper escaping"""
        try:
            # Convert glob pattern to regex
            if "*" in pattern:
                # Escape special regex characters except *
                escaped = re.escape(pattern).replace(r"\*", ".*")
                return bool(re.match(escaped, text))
            else:
                return pattern == text
        except re.error:
            # Fallback to simple string matching
            return pattern == text

    def _process_file(self, file_path: Path):
        """Process a single file for indexing"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            self.file_contents[str(file_path)] = content

            # Extract functions and classes
            functions = self._extract_functions(content, file_path)

            # Store function information
            for func in functions:
                func_id = f"{file_path}:{func['name']}"
                self.function_index[func["name"]].append(func_id)

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    def _extract_functions(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """Extract function definitions from content"""
        import ast

        functions = []

        try:
            tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get function content
                    lines = content.split("\n")
                    func_lines = lines[node.lineno - 1 : node.end_lineno or node.lineno]
                    func_content = "\n".join(func_lines)

                    functions.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "end_line": node.end_lineno or node.lineno,
                            "content": func_content,
                            "args": [arg.arg for arg in node.args.args],
                            "decorators": [
                                self._get_decorator_name(dec)
                                for dec in node.decorator_list
                            ],
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    # Get class content
                    lines = content.split("\n")
                    class_lines = lines[
                        node.lineno - 1 : node.end_lineno or node.lineno
                    ]
                    class_content = "\n".join(class_lines)

                    functions.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "end_line": node.end_lineno or node.lineno,
                            "content": class_content,
                            "args": [],
                            "decorators": [
                                self._get_decorator_name(dec)
                                for dec in node.decorator_list
                            ],
                        }
                    )

        except Exception as e:
            logger.warning(f"Failed to parse AST for {file_path}: {e}")

        return functions

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}"
        else:
            return str(decorator)

    def _build_embeddings(self):
        """Build embeddings for all functions"""
        for file_path, content in self.file_contents.items():
            functions = self._extract_functions(content, Path(file_path))

            for func in functions:
                func_id = f"{file_path}:{func['name']}"

                # Create embedding from function content
                embedding = self._create_embedding(func["content"])

                self.embeddings[func_id] = CodeEmbedding(
                    file_path=file_path,
                    function_name=func["name"],
                    embedding=embedding,
                    content=func["content"],
                    line_number=func["line"],
                    metadata={
                        "args": func["args"],
                        "decorators": func["decorators"],
                        "end_line": func["end_line"],
                    },
                )

    def _create_embedding(self, content: str) -> list[float]:
        """Create embedding from code content"""
        # Simple hash-based embedding (in production, use proper embeddings)
        # This is a placeholder for a real embedding model

        # Normalize content
        normalized = re.sub(r"\s+", " ", content.lower())
        normalized = re.sub(r"[^\w\s]", " ", normalized)

        # Create hash
        content_hash = hashlib.sha256(normalized.encode()).hexdigest()

        # Convert hash to embedding vector
        embedding = []
        for i in range(0, len(content_hash), 2):
            hex_pair = content_hash[i : i + 2]
            embedding.append(int(hex_pair, 16) / 255.0)

        # Pad or truncate to embedding_dim
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)

        embedding = embedding[: self.embedding_dim]

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding

    def _build_function_index(self):
        """Build function name index"""
        # Already built in _process_file
        pass

    def _calculate_index_size(self) -> float:
        """Calculate index size in MB"""
        total_size = 0

        # Calculate embeddings size
        for embedding in self.embeddings.values():
            total_size += len(embedding.embedding) * 8  # 8 bytes per float

        # Calculate file contents size
        for content in self.file_contents.values():
            total_size += len(content.encode("utf-8"))

        return total_size / (1024 * 1024)  # Convert to MB

    def search_similar(
        self, query: str, limit: int = 10, threshold: float = 0.5
    ) -> list[SearchResult]:
        """Search for similar code"""
        # Create embedding for query
        query_embedding = self._create_embedding(query)

        # Calculate similarities
        similarities = []
        for func_id, embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding.embedding)
            if similarity >= threshold:
                similarities.append((func_id, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Convert to SearchResult
        results = []
        for func_id, similarity in similarities[:limit]:
            embedding = self.embeddings[func_id]

            # Get context
            context = self._get_context(embedding.file_path, embedding.line_number)

            results.append(
                SearchResult(
                    file_path=embedding.file_path,
                    line_number=embedding.line_number,
                    content=embedding.content,
                    match_type=MatchType.SEMANTIC,
                    similarity_score=similarity,
                    context=context,
                    metadata=embedding.metadata,
                )
            )

        return results

    def search_pattern(self, pattern: str, limit: int = 10) -> list[SearchResult]:
        """Search for code patterns"""
        if pattern in self.pattern_cache:
            return self.pattern_cache[pattern][:limit]

        results = []
        compiled_pattern = re.compile(pattern, re.IGNORECASE)

        for file_path, content in self.file_contents.items():
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if compiled_pattern.search(line):
                    # Get context
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 3)
                    context = "\n".join(lines[context_start:context_end])

                    results.append(
                        SearchResult(
                            file_path=file_path,
                            line_number=i + 1,
                            content=line.strip(),
                            match_type=MatchType.PATTERN,
                            similarity_score=1.0,
                            context=context,
                            metadata={"pattern": pattern},
                        )
                    )

        # Cache results
        self.pattern_cache[pattern] = results

        return results[:limit]

    def search_function(
        self, function_name: str, limit: int = 10
    ) -> list[SearchResult]:
        """Search for specific function"""
        results = []

        if function_name in self.function_index:
            for func_id in self.function_index[function_name]:
                embedding = self.embeddings[func_id]

                # Get context
                context = self._get_context(embedding.file_path, embedding.line_number)

                results.append(
                    SearchResult(
                        file_path=embedding.file_path,
                        line_number=embedding.line_number,
                        content=embedding.content,
                        match_type=MatchType.EXACT,
                        similarity_score=1.0,
                        context=context,
                        metadata=embedding.metadata,
                    )
                )

        return results[:limit]

    def search_contextual(
        self, file_path: str, line_number: int, limit: int = 10
    ) -> list[SearchResult]:
        """Search for contextually related code"""
        # Get the function at the given location
        target_func = None
        for _func_id, embedding in self.embeddings.items():
            if embedding.file_path == file_path:
                if (
                    embedding.line_number
                    <= line_number
                    <= embedding.metadata.get("end_line", embedding.line_number)
                ):
                    target_func = embedding
                    break

        if not target_func:
            return []

        # Find similar functions
        similar_results = self.search_similar(target_func.content, limit=limit + 1)

        # Remove the target function itself
        similar_results = [
            r
            for r in similar_results
            if r.file_path != file_path or r.line_number != line_number
        ]

        return similar_results[:limit]

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _get_context(
        self, file_path: str, line_number: int, context_lines: int = 3
    ) -> str:
        """Get context around a line"""
        if file_path not in self.file_contents:
            return ""

        lines = self.file_contents[file_path].split("\n")

        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)

        context_lines_list = lines[start:end]

        # Add line numbers
        numbered_context = []
        for i, line in enumerate(context_lines_list):
            actual_line = start + i + 1
            marker = ">>> " if actual_line == line_number else "    "
            numbered_context.append(f"{marker}{actual_line:4d}: {line}")

        return "\n".join(numbered_context)

    def find_related_files(
        self, file_path: str, limit: int = 5
    ) -> list[tuple[str, float]]:
        """Find files related to the given file"""
        # Get all functions in the file
        file_functions = []
        for _func_id, embedding in self.embeddings.items():
            if embedding.file_path == file_path:
                file_functions.append(embedding)

        if not file_functions:
            return []

        # Calculate similarity to other files
        file_similarities = defaultdict(float)
        file_counts = defaultdict(int)

        for func in file_functions:
            similar_results = self.search_similar(func.content, limit=50)

            for result in similar_results:
                if result.file_path != file_path:
                    file_similarities[result.file_path] += result.similarity_score
                    file_counts[result.file_path] += 1

        # Calculate average similarity per file
        file_avg_similarities = []
        for file_path, total_sim in file_similarities.items():
            avg_sim = total_sim / file_counts[file_path]
            file_avg_similarities.append((file_path, avg_sim))

        # Sort by similarity
        file_avg_similarities.sort(key=lambda x: x[1], reverse=True)

        return file_avg_similarities[:limit]

    def get_code_suggestions(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get code suggestions based on query"""
        # Search for similar code
        similar_results = self.search_similar(query, limit=limit)

        suggestions = []
        for result in similar_results:
            suggestion = {
                "file_path": result.file_path,
                "function_name": Path(result.file_path).stem,
                "line_number": result.line_number,
                "similarity": result.similarity_score,
                "snippet": result.content[:200] + "..."
                if len(result.content) > 200
                else result.content,
                "context": result.context,
            }
            suggestions.append(suggestion)

        return suggestions

    def export_index(self, output_file: str = "semantic_index.json"):
        """Export search index to JSON"""
        index_data = {
            "embeddings": {
                func_id: {
                    "file_path": emb.file_path,
                    "function_name": emb.function_name,
                    "embedding": emb.embedding,
                    "content": emb.content,
                    "line_number": emb.line_number,
                    "metadata": emb.metadata,
                }
                for func_id, emb in self.embeddings.items()
            },
            "function_index": dict(self.function_index),
            "index_metadata": {
                "project_root": str(self.project_root),
                "embedding_dim": self.embedding_dim,
                "total_embeddings": len(self.embeddings),
                "index_timestamp": time.time(),
            },
        }

        with open(output_file, "w") as f:
            json.dump(index_data, f, indent=2, default=str)

        logger.info(f"Semantic index exported to {output_file}")

    def get_metrics(self) -> dict[str, Any]:
        """Get search engine metrics"""
        return {
            "total_embeddings": len(self.embeddings),
            "total_files": len(self.file_contents),
            "function_index_size": len(self.function_index),
            "pattern_cache_size": len(self.pattern_cache),
            "similarity_cache_size": len(self._similarity_cache),
            "index_size_mb": self._calculate_index_size(),
            "average_embedding_dim": self.embedding_dim,
        }
