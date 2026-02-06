"""
Codebase Indexer for StillMe Codebase Assistant

Indexes source code files into ChromaDB for RAG-based code Q&A.
Implements chunking strategy: by file, by class, by function.
"""

import os
import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Global instance (singleton pattern)
_codebase_indexer_instance = None


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata"""
    file_path: str
    line_range: Tuple[int, int]  # (start_line, end_line)
    code_content: str
    code_type: str  # "file", "class", "function"
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    docstring: Optional[str] = None
    imports: List[str] = None
    dependencies: List[str] = None  # Used classes/functions from other modules
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []
        if self.dependencies is None:
            self.dependencies = []


class CodebaseIndexer:
    """
    Indexes StillMe codebase into ChromaDB for code Q&A.
    
    Chunking Strategy:
    - Small files (< 500 lines): 1 chunk per file
    - Medium files (500-2000 lines): 1 chunk per class
    - Large files (> 2000 lines): 1 chunk per function
    
    Safety: Read-only, no code modification.
    """
    
    def __init__(self, chroma_client, embedding_service):
        """
        Initialize codebase indexer.
        
        Args:
            chroma_client: ChromaDB client instance
            embedding_service: EmbeddingService instance
        """
        self.chroma_client = chroma_client
        self.embedding_service = embedding_service
        self.codebase_collection = None
        self._initialize_collection()
        
        # File extensions to index (Phase 1: Python only)
        self.supported_extensions = {'.py'}
        
        # Directories to index
        self.index_directories = [
            'backend',
            'stillme_core',
            'frontend'  # Python files in frontend (if any)
        ]
        
        # Directories to exclude
        self.exclude_patterns = [
            '__pycache__',
            '.git',
            'node_modules',
            'venv',
            'env',
            '.pytest_cache',
            'dist',
            'build',
            '*.pyc',
            '*.pyo'
        ]
    
    def _initialize_collection(self):
        """Initialize or get codebase collection in ChromaDB"""
        try:
            # Try to get existing collection
            self.codebase_collection = self.chroma_client.client.get_collection(
                name="stillme_codebase"
            )
            logger.info("✅ Found existing stillme_codebase collection")
        except Exception:
            # Create new collection
            try:
                self.codebase_collection = self.chroma_client.client.create_collection(
                    name="stillme_codebase",
                    metadata={
                        "description": "StillMe codebase for code Q&A and understanding",
                        "hnsw:space": "cosine"  # Use cosine distance for normalized embeddings
                    }
                )
                logger.info("✅ Created stillme_codebase collection with cosine distance")
            except Exception as e:
                error_str = str(e).lower()
                if "already exists" in error_str or "duplicate" in error_str:
                    # Collection exists but get_collection failed, try again
                    logger.warning(f"Collection exists, getting it: {e}")
                    self.codebase_collection = self.chroma_client.client.get_collection(
                        name="stillme_codebase"
                    )
                else:
                    raise
    
    def _should_index_file(self, file_path: Path) -> bool:
        """Check if file should be indexed"""
        # Check extension
        if file_path.suffix not in self.supported_extensions:
            return False
        
        # Check exclude patterns
        path_str = str(file_path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return False
        
        return True
    
    def _parse_python_file(self, file_path: Path) -> List[CodeChunk]:
        """
        Parse Python file and extract chunks.
        
        Returns:
            List of CodeChunk objects
        """
        chunks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(source_code, filename=str(file_path))
            except SyntaxError as e:
                logger.warning(f"⚠️ Syntax error in {file_path}: {e}. Skipping file.")
                return chunks
            
            # Get all lines for line number mapping
            lines = source_code.split('\n')
            file_lines = len(lines)
            
            # Strategy: Choose chunking based on file size
            if file_lines < 500:
                # Small file: 1 chunk per file
                docstring = ast.get_docstring(tree)
                imports = self._extract_imports(tree)
                
                chunk = CodeChunk(
                    file_path=str(file_path),
                    line_range=(1, file_lines),
                    code_content=source_code,
                    code_type="file",
                    docstring=docstring,
                    imports=imports
                )
                chunks.append(chunk)
            else:
                # Medium/Large file: chunk by class or function
                chunks.extend(self._extract_classes_and_functions(tree, file_path, lines))
            
        except Exception as e:
            logger.error(f"❌ Error parsing {file_path}: {e}")
        
        return chunks
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports
    
    def _extract_classes_and_functions(self, tree: ast.AST, file_path: Path, lines: List[str]) -> List[CodeChunk]:
        """Extract classes and functions as separate chunks"""
        chunks = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Extract class
                class_start = node.lineno
                class_end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
                
                # Get class code
                class_code = '\n'.join(lines[class_start - 1:class_end])
                docstring = ast.get_docstring(node)
                
                # Extract methods
                methods = []
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        methods.append(child.name)
                
                chunk = CodeChunk(
                    file_path=str(file_path),
                    line_range=(class_start, class_end),
                    code_content=class_code,
                    code_type="class",
                    class_name=node.name,
                    docstring=docstring,
                    dependencies=methods
                )
                chunks.append(chunk)
            
            elif isinstance(node, ast.FunctionDef):
                # Only extract top-level functions (not methods)
                # Check if this function is inside a class by traversing parent nodes
                is_method = False
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef):
                        # Check if node is in parent's body
                        if hasattr(parent, 'body'):
                            for child in parent.body:
                                if child == node:
                                    is_method = True
                                    break
                        if is_method:
                            break
                
                if not is_method:
                    func_start = node.lineno
                    func_end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
                    
                    func_code = '\n'.join(lines[func_start - 1:func_end])
                    docstring = ast.get_docstring(node)
                    
                    chunk = CodeChunk(
                        file_path=str(file_path),
                        line_range=(func_start, func_end),
                        code_content=func_code,
                        code_type="function",
                        function_name=node.name,
                        docstring=docstring
                    )
                    chunks.append(chunk)
        
        return chunks
    
    def _chunk_to_document(self, chunk: CodeChunk) -> Dict[str, Any]:
        """
        Convert CodeChunk to document format for ChromaDB.
        
        Returns:
            Dictionary with id, document, metadata
        """
        # Create unique ID
        chunk_id = f"{chunk.file_path}:{chunk.line_range[0]}-{chunk.line_range[1]}"
        
        # Build document text (code + metadata for better retrieval)
        doc_parts = []
        
        if chunk.docstring:
            doc_parts.append(f"# Docstring: {chunk.docstring}")
        
        if chunk.code_type == "class":
            doc_parts.append(f"# Class: {chunk.class_name}")
        elif chunk.code_type == "function":
            doc_parts.append(f"# Function: {chunk.function_name}")
        
        if chunk.imports:
            doc_parts.append(f"# Imports: {', '.join(chunk.imports[:5])}")  # Limit imports
        
        doc_parts.append("\n# Code:")
        doc_parts.append(chunk.code_content)
        
        document_text = "\n".join(doc_parts)
        
        # Build metadata
        metadata = {
            "file_path": chunk.file_path,
            "line_start": chunk.line_range[0],
            "line_end": chunk.line_range[1],
            "code_type": chunk.code_type,
        }
        
        if chunk.function_name:
            metadata["function_name"] = chunk.function_name
        if chunk.class_name:
            metadata["class_name"] = chunk.class_name
        if chunk.docstring:
            metadata["docstring"] = chunk.docstring[:500]  # Limit docstring length
        if chunk.imports:
            metadata["imports"] = ",".join(chunk.imports[:10])  # Limit imports
        
        return {
            "id": chunk_id,
            "document": document_text,
            "metadata": metadata
        }
    
    def index_file(self, file_path: Path) -> int:
        """
        Index a single file.
        
        Args:
            file_path: Path to file to index
            
        Returns:
            Number of chunks created
        """
        if not self._should_index_file(file_path):
            logger.debug(f"⏭️ Skipping {file_path} (not supported or excluded)")
            return 0
        
        logger.info(f"📄 Indexing {file_path}")
        
        # Parse file and extract chunks
        chunks = self._parse_python_file(file_path)
        
        if not chunks:
            logger.warning(f"⚠️ No chunks extracted from {file_path}")
            return 0
        
        # Convert chunks to documents
        documents = []
        for chunk in chunks:
            doc = self._chunk_to_document(chunk)
            documents.append(doc)
        
        # Generate embeddings
        texts = [doc["document"] for doc in documents]
        # Use batch_encode for efficiency (or encode_text if list is supported)
        if len(texts) == 1:
            embeddings = [self.embedding_service.encode_text(texts[0])]
        else:
            embeddings = self.embedding_service.batch_encode(texts)
        
        # Prepare data for ChromaDB
        ids = [doc["id"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        # Add to collection
        try:
            self.codebase_collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            logger.info(f"✅ Indexed {len(chunks)} chunks from {file_path}")
            return len(chunks)
        except Exception as e:
            logger.error(f"❌ Error adding chunks to ChromaDB: {e}")
            return 0
    
    def index_directory(self, directory: Path) -> Dict[str, int]:
        """
        Index all supported files in a directory recursively.
        
        Args:
            directory: Directory to index
            
        Returns:
            Dictionary with stats: {files_indexed, chunks_created}
        """
        stats = {"files_indexed": 0, "chunks_created": 0}
        
        if not directory.exists():
            logger.warning(f"⚠️ Directory does not exist: {directory}")
            return stats
        
        # Find all Python files
        for file_path in directory.rglob("*.py"):
            if self._should_index_file(file_path):
                chunks = self.index_file(file_path)
                if chunks > 0:
                    stats["files_indexed"] += 1
                    stats["chunks_created"] += chunks
        
        return stats
    
    def index_codebase(self) -> Dict[str, Any]:
        """
        Index entire StillMe codebase.
        
        Returns:
            Dictionary with indexing statistics
        """
        logger.info("🚀 Starting codebase indexing...")
        
        total_stats = {"files_indexed": 0, "chunks_created": 0, "directories": []}
        
        # Get project root (assume we're in project root or can find it)
        project_root = Path.cwd()
        
        for dir_name in self.index_directories:
            dir_path = project_root / dir_name
            if dir_path.exists():
                logger.info(f"📁 Indexing directory: {dir_name}")
                stats = self.index_directory(dir_path)
                total_stats["files_indexed"] += stats["files_indexed"]
                total_stats["chunks_created"] += stats["chunks_created"]
                total_stats["directories"].append({
                    "directory": dir_name,
                    "files": stats["files_indexed"],
                    "chunks": stats["chunks_created"]
                })
            else:
                logger.warning(f"⚠️ Directory not found: {dir_path}")
        
        logger.info(f"✅ Codebase indexing complete!")
        logger.info(f"   Files indexed: {total_stats['files_indexed']}")
        logger.info(f"   Chunks created: {total_stats['chunks_created']}")
        
        return total_stats
    
    def query_codebase(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query codebase using RAG.
        
        Args:
            query: Natural language query about code
            n_results: Number of results to return
            
        Returns:
            List of relevant code chunks with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_service.encode_text(query)
        
        # Search in ChromaDB
        results = self.codebase_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                result = {
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                }
                formatted_results.append(result)
        
        return formatted_results


def get_codebase_indexer():
    """
    Get or create CodebaseIndexer singleton instance.
    
    Tries to get from main_module first (when backend is running),
    otherwise initializes directly (for scripts/testing).
    
    Returns:
        CodebaseIndexer instance
    """
    global _codebase_indexer_instance
    
    if _codebase_indexer_instance is None:
        # Try to get from main module first (when backend is running)
        try:
            import backend.api.main as main_module
            
            if hasattr(main_module, 'chroma_client') and main_module.chroma_client is not None:
                if hasattr(main_module, 'embedding_service') and main_module.embedding_service is not None:
                    _codebase_indexer_instance = CodebaseIndexer(
                        chroma_client=main_module.chroma_client,
                        embedding_service=main_module.embedding_service
                    )
                    logger.info("✅ CodebaseIndexer initialized from main_module")
                    return _codebase_indexer_instance
        except (ImportError, AttributeError) as e:
            logger.debug(f"Could not get from main_module: {e}, initializing directly...")
        
        # Fallback: Initialize directly (for scripts/testing)
        try:
            from backend.vector_db.chroma_client import ChromaClient
            from backend.vector_db.embeddings import get_embedding_service
            
            logger.info("📦 Initializing ChromaDB client and EmbeddingService directly...")
            embedding_service = get_embedding_service()
            chroma_client = ChromaClient(embedding_service=embedding_service)
            
            _codebase_indexer_instance = CodebaseIndexer(
                chroma_client=chroma_client,
                embedding_service=embedding_service
            )
            logger.info("✅ CodebaseIndexer initialized directly (standalone mode)")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize CodebaseIndexer: {e}")
    
    return _codebase_indexer_instance

