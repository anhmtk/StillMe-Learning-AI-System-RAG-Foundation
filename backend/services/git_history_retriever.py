"""
Git History Retriever - Index and retrieve Git history for StillMe codebase

This module indexes:
- Commit messages
- Commit diffs (optional, for understanding changes)
- PR descriptions (if available)
- Issue discussions (if available)

Stores in ChromaDB collection: stillme_git_history
"""

import os
import re
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class GitHistoryRetriever:
    """
    Retrieves and indexes Git history for StillMe codebase.
    
    Features:
    - Index commit messages with metadata (author, date, files changed)
    - Support queries like "Why did we choose Redis for caching?"
    - Store in separate ChromaDB collection (stillme_git_history)
    - Support filtering by date range, author, file path
    """
    
    def __init__(self, chroma_client=None, embedding_service=None, repo_path: Optional[str] = None):
        """
        Initialize GitHistoryRetriever.
        
        Args:
            chroma_client: ChromaDB client instance
            embedding_service: EmbeddingService instance
            repo_path: Path to Git repository (default: project root)
        """
        self.repo_path = repo_path or self._find_repo_root()
        self.chroma_client = chroma_client
        self.embedding_service = embedding_service
        self.collection_name = "stillme_git_history"
        self._collection = None
        
        if not self.repo_path or not os.path.exists(os.path.join(self.repo_path, ".git")):
            logger.warning(f"⚠️ Git repository not found at {self.repo_path}")
            logger.warning("   Git history features will be disabled")
    
    def _find_repo_root(self) -> Optional[str]:
        """Find Git repository root by traversing up from current directory."""
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / ".git").exists():
                return str(parent)
        return None
    
    def _get_collection(self):
        """Get or create ChromaDB collection for Git history."""
        if self._collection:
            return self._collection
        
        if not self.chroma_client:
            raise RuntimeError("ChromaDB client not initialized")
        
        try:
            # Try to get existing collection
            self._collection = self.chroma_client.client.get_collection(
                name=self.collection_name
            )
            logger.info(f"✅ Found existing Git history collection '{self.collection_name}'")
            return self._collection
        except Exception:
            # Create new collection
            try:
                self._collection = self.chroma_client.client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Git history (commits, PRs, issues) for StillMe codebase",
                        "hnsw:space": "cosine"  # Use cosine distance for normalized embeddings
                    }
                )
                logger.info(f"✅ Created Git history collection '{self.collection_name}' with cosine distance")
                return self._collection
            except Exception as e:
                error_str = str(e).lower()
                if "already exists" in error_str or "duplicate" in error_str:
                    # Collection exists but get_collection failed, try again
                    logger.warning(f"Collection exists, getting it: {e}")
                    self._collection = self.chroma_client.client.get_collection(
                        name=self.collection_name
                    )
                    return self._collection
                else:
                    logger.error(f"❌ Failed to get/create Git history collection: {e}")
                    raise
    
    def get_commits(
        self,
        limit: int = 100,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get commit history from Git repository.
        
        Args:
            limit: Maximum number of commits to retrieve
            since: Start date (ISO format or relative like "1 month ago")
            until: End date (ISO format or relative)
            author: Filter by author email/name
            file_path: Filter by file path
            
        Returns:
            List of commit dictionaries with metadata
        """
        if not self.repo_path:
            logger.warning("⚠️ Git repository not available")
            return []
        
        try:
            # Build git log command
            cmd = ["git", "log", "--pretty=format:%H|%an|%ae|%ad|%s|%b", "--date=iso"]
            
            if limit:
                cmd.extend(["-n", str(limit)])
            
            if since:
                cmd.extend(["--since", since])
            
            if until:
                cmd.extend(["--until", until])
            
            if author:
                cmd.extend(["--author", author])
            
            if file_path:
                cmd.extend(["--", file_path])
            
            # Execute git log
            # Use UTF-8 encoding to handle special characters in commit messages
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid characters instead of failing
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Git log failed: {result.stderr}")
                return []
            
            # Parse commits
            commits = []
            if not result.stdout:
                logger.warning("⚠️ Git log returned empty output")
                return []
            
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                
                parts = line.split("|", 5)
                if len(parts) < 5:
                    continue
                
                commit_hash = parts[0]
                author_name = parts[1]
                author_email = parts[2]
                commit_date = parts[3]
                subject = parts[4]
                body = parts[5] if len(parts) > 5 else ""
                
                # Get files changed
                files_changed = self._get_commit_files(commit_hash)
                
                commits.append({
                    "hash": commit_hash,
                    "author_name": author_name,
                    "author_email": author_email,
                    "date": commit_date,
                    "subject": subject,
                    "body": body,
                    "files_changed": files_changed,
                    "full_message": f"{subject}\n{body}".strip()
                })
            
            logger.info(f"✅ Retrieved {len(commits)} commits from Git history")
            return commits
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Git log command timed out")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to get commits: {e}", exc_info=True)
            return []
    
    def _get_commit_files(self, commit_hash: str) -> List[str]:
        """Get list of files changed in a commit."""
        if not self.repo_path:
            return []
        
        try:
            result = subprocess.run(
                ["git", "show", "--name-only", "--pretty=format:", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
                return files
            return []
        except Exception as e:
            logger.debug(f"Failed to get files for commit {commit_hash}: {e}")
            return []
    
    def index_commits(
        self,
        limit: int = 500,
        since: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Index commits into ChromaDB.
        
        Args:
            limit: Maximum number of commits to index
            since: Start date (ISO format or relative)
            force: Force re-indexing (delete existing collection)
            
        Returns:
            Dictionary with indexing statistics
        """
        if not self.chroma_client or not self.embedding_service:
            raise RuntimeError("ChromaDB client and EmbeddingService must be initialized")
        
        collection = self._get_collection()
        
        # Check if already indexed
        if not force:
            count = collection.count()
            if count > 0:
                logger.info(f"ℹ️ Git history already indexed ({count} commits). Use force=True to re-index")
                return {
                    "status": "already_indexed",
                    "count": count,
                    "message": "Git history already indexed. Use force=True to re-index."
                }
        
        # Get commits
        commits = self.get_commits(limit=limit, since=since)
        
        if not commits:
            logger.warning("⚠️ No commits found to index")
            return {
                "status": "no_commits",
                "count": 0,
                "message": "No commits found to index"
            }
        
        # Delete existing collection if force
        if force:
            try:
                self.chroma_client.client.delete_collection(name=self.collection_name)
                logger.info(f"🗑️ Deleted existing collection '{self.collection_name}'")
                self._collection = None  # Reset cached collection
                collection = self._get_collection()  # Recreate
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete collection: {e}")
        
        # Index commits
        documents = []
        metadatas = []
        ids = []
        
        for commit in commits:
            # Create document text
            doc_text = f"Commit: {commit['subject']}\n"
            if commit['body']:
                doc_text += f"Description: {commit['body']}\n"
            doc_text += f"Files changed: {', '.join(commit['files_changed'][:10])}"  # Limit to 10 files
            
            documents.append(doc_text)
            metadatas.append({
                "commit_hash": commit['hash'],
                "author_name": commit['author_name'],
                "author_email": commit['author_email'],
                "date": commit['date'],
                "subject": commit['subject'],
                "files_changed": json.dumps(commit['files_changed']),
                "source": "git_commit"
            })
            ids.append(f"commit_{commit['hash']}")
        
        # Generate embeddings
        logger.info(f"📝 Generating embeddings for {len(documents)} commits...")
        # Use batch_encode for efficiency
        embeddings = self.embedding_service.batch_encode(documents, batch_size=32)
        
        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"✅ Indexed {len(commits)} commits into '{self.collection_name}' collection")
        
        return {
            "status": "success",
            "count": len(commits),
            "collection": self.collection_name,
            "message": f"Successfully indexed {len(commits)} commits"
        }
    
    def query_history(
        self,
        question: str,
        n_results: int = 5,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query Git history using semantic search.
        
        Args:
            question: Question about Git history (e.g., "Why did we choose Redis?")
            n_results: Number of results to return
            since: Filter by start date
            until: Filter by end date
            
        Returns:
            List of relevant commits with similarity scores
        """
        if not self.chroma_client or not self.embedding_service:
            raise RuntimeError("ChromaDB client and EmbeddingService must be initialized")
        
        collection = self._get_collection()
        
        # Check if collection is empty
        if collection.count() == 0:
            logger.warning("⚠️ Git history collection is empty. Run index_commits() first")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_service.encode_text(question)
        
        # Build where clause for date filtering
        where = {}
        if since or until:
            # Note: ChromaDB doesn't support date range queries directly
            # We'll filter results after retrieval
            pass
        
        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results * 2,  # Get more results for filtering
            where=where if where else None
        )
        
        # Parse results
        commits = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i, commit_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if 'distances' in results else None
                document = results['documents'][0][i]
                
                # Filter by date if specified
                if since or until:
                    commit_date = metadata.get('date', '')
                    # Simple date comparison (can be improved)
                    if since and commit_date < since:
                        continue
                    if until and commit_date > until:
                        continue
                
                commits.append({
                    "commit_hash": metadata.get('commit_hash', ''),
                    "author_name": metadata.get('author_name', ''),
                    "date": metadata.get('date', ''),
                    "subject": metadata.get('subject', ''),
                    "files_changed": json.loads(metadata.get('files_changed', '[]')),
                    "document": document,
                    "distance": distance,
                    "similarity": 1 - distance if distance else None
                })
                
                if len(commits) >= n_results:
                    break
        
        logger.info(f"✅ Found {len(commits)} relevant commits for query: '{question[:50]}...'")
        return commits
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the Git history collection."""
        if not self.chroma_client:
            raise RuntimeError("ChromaDB client not initialized")
        
        try:
            collection = self._get_collection()
            count = collection.count()
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "status": "ready" if count > 0 else "empty"
            }
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {e}")
            return {
                "collection_name": self.collection_name,
                "document_count": 0,
                "status": "error",
                "error": str(e)
            }


def get_git_history_retriever(
    chroma_client=None,
    embedding_service=None,
    repo_path: Optional[str] = None
) -> GitHistoryRetriever:
    """
    Get or create GitHistoryRetriever instance.
    
    Args:
        chroma_client: ChromaDB client (if None, will try to get from backend)
        embedding_service: EmbeddingService (if None, will try to get from backend)
        repo_path: Path to Git repository
        
    Returns:
        GitHistoryRetriever instance
    """
    # Try to get from backend if not provided
    if not chroma_client:
        try:
            from backend.api.main import chroma_client as backend_chroma_client
            if backend_chroma_client is not None:
                chroma_client = backend_chroma_client
        except (ImportError, AttributeError):
            pass
        
        # If still None, initialize directly (standalone mode)
        if chroma_client is None:
            from backend.vector_db import ChromaClient
            chroma_client = ChromaClient()
            logger.info("📦 Initializing ChromaDB client directly (standalone mode)")
    
    if not embedding_service:
        try:
            from backend.api.main import embedding_service as backend_embedding_service
            if backend_embedding_service is not None:
                embedding_service = backend_embedding_service
        except (ImportError, AttributeError):
            pass
        
        # If still None, initialize directly (standalone mode)
        if embedding_service is None:
            from backend.vector_db.embeddings import get_embedding_service
            embedding_service = get_embedding_service()
            logger.info("📦 Initializing EmbeddingService directly (standalone mode)")
    
    return GitHistoryRetriever(
        chroma_client=chroma_client,
        embedding_service=embedding_service,
        repo_path=repo_path
    )

