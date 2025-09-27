"""
StillMe Vector Store
FAISS/LanceDB-based vector storage for content embeddings.
"""

import logging
import numpy as np
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import pickle

from stillme_core.learning.parser.normalize import NormalizedContent

log = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """Vector document with metadata."""
    id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    source: str
    created_at: str

class SimpleVectorStore:
    """Simple in-memory vector store with FAISS-like interface."""
    
    def __init__(self, embedding_dim: int = 384, index_file: str = "data/vector_index.pkl"):
        self.embedding_dim = embedding_dim
        self.index_file = Path(index_file)
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage
        self.embeddings: List[np.ndarray] = []
        self.documents: List[VectorDocument] = []
        self.id_to_index: Dict[str, int] = {}
        
        # Load existing index if available
        self._load_index()
        
        log.info(f"Vector store initialized with {len(self.documents)} documents")
    
    def _load_index(self):
        """Load vector index from file."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'rb') as f:
                    data = pickle.load(f)
                
                self.embeddings = data['embeddings']
                self.documents = data['documents']
                self.id_to_index = data['id_to_index']
                
                log.info(f"Loaded vector index with {len(self.documents)} documents")
            except Exception as e:
                log.error(f"Failed to load vector index: {e}")
    
    def _save_index(self):
        """Save vector index to file."""
        try:
            data = {
                'embeddings': self.embeddings,
                'documents': self.documents,
                'id_to_index': self.id_to_index
            }
            
            with open(self.index_file, 'wb') as f:
                pickle.dump(data, f)
            
            log.info(f"Saved vector index with {len(self.documents)} documents")
        except Exception as e:
            log.error(f"Failed to save vector index: {e}")
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for text."""
        # Simple fallback embedding using text features
        # In production, this would use a proper embedding model
        
        # Create feature vector
        features = []
        
        # Text length features
        features.append(len(text))
        features.append(len(text.split()))
        
        # Character frequency features
        char_counts = {}
        for char in text.lower():
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Add top character frequencies
        sorted_chars = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)
        for i in range(50):  # Use more features for better embedding
            if i < len(sorted_chars):
                features.append(sorted_chars[i][1])
            else:
                features.append(0)
        
        # Word frequency features
        words = text.lower().split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        for i in range(50):
            if i < len(sorted_words):
                features.append(sorted_words[i][1])
            else:
                features.append(0)
        
        # Pad or truncate to embedding dimension
        while len(features) < self.embedding_dim:
            features.append(0)
        features = features[:self.embedding_dim]
        
        # Normalize
        features = np.array(features, dtype=np.float32)
        if np.linalg.norm(features) > 0:
            features = features / np.linalg.norm(features)
        
        return features
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def add_document(self, content: NormalizedContent, chunk_size: int = 512) -> List[str]:
        """Add content to vector store, chunking if necessary."""
        document_ids = []
        
        # Create content text
        full_text = f"{content.title}\n\n{content.content}"
        
        # Chunk content if it's too long
        if len(full_text) > chunk_size:
            chunks = self._chunk_text(full_text, chunk_size)
        else:
            chunks = [full_text]
        
        for i, chunk in enumerate(chunks):
            # Create document ID
            chunk_id = hashlib.md5(f"{content.url}_{i}".encode()).hexdigest()
            
            # Compute embedding
            embedding = self._compute_embedding(chunk)
            
            # Create metadata
            metadata = {
                'title': content.title,
                'url': content.url,
                'source': content.source,
                'domain': content.domain,
                'author': content.author,
                'published_date': content.published_date,
                'content_type': content.content_type,
                'tags': content.tags,
                'license': content.license,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'word_count': len(chunk.split())
            }
            
            # Create document
            document = VectorDocument(
                id=chunk_id,
                content=chunk,
                embedding=embedding,
                metadata=metadata,
                source=content.source,
                created_at=content.metadata.get('normalization_timestamp', '')
            )
            
            # Add to store
            self._add_document_to_index(document)
            document_ids.append(chunk_id)
        
        # Save index
        self._save_index()
        
        log.info(f"Added {len(document_ids)} chunks from {content.title}")
        return document_ids
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Chunk text into smaller pieces."""
        words = text.split()
        chunks = []
        
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) + 1 > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _add_document_to_index(self, document: VectorDocument):
        """Add document to in-memory index."""
        if document.id in self.id_to_index:
            # Update existing document
            index = self.id_to_index[document.id]
            self.embeddings[index] = document.embedding
            self.documents[index] = document
        else:
            # Add new document
            index = len(self.documents)
            self.embeddings.append(document.embedding)
            self.documents.append(document)
            self.id_to_index[document.id] = index
    
    def search(self, query: str, top_k: int = 10, min_similarity: float = 0.0) -> List[Dict]:
        """Search for similar documents."""
        if not self.documents:
            return []
        
        # Compute query embedding
        query_embedding = self._compute_embedding(query)
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            if similarity >= min_similarity:
                similarities.append((i, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k results
        results = []
        for i, similarity in similarities[:top_k]:
            doc = self.documents[i]
            results.append({
                'id': doc.id,
                'content': doc.content,
                'similarity': similarity,
                'metadata': doc.metadata,
                'source': doc.source,
                'created_at': doc.created_at
            })
        
        return results
    
    def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID."""
        if doc_id in self.id_to_index:
            index = self.id_to_index[doc_id]
            return self.documents[index]
        return None
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document by ID."""
        if doc_id not in self.id_to_index:
            return False
        
        index = self.id_to_index[doc_id]
        
        # Remove from lists
        del self.embeddings[index]
        del self.documents[index]
        
        # Update ID mapping
        del self.id_to_index[doc_id]
        
        # Rebuild ID mapping
        self.id_to_index = {doc.id: i for i, doc in enumerate(self.documents)}
        
        # Save index
        self._save_index()
        
        log.info(f"Deleted document {doc_id}")
        return True
    
    def get_statistics(self) -> Dict:
        """Get vector store statistics."""
        if not self.documents:
            return {
                'total_documents': 0,
                'embedding_dimension': self.embedding_dim,
                'domains': [],
                'sources': [],
                'content_types': []
            }
        
        domains = list(set(doc.metadata.get('domain', '') for doc in self.documents))
        sources = list(set(doc.source for doc in self.documents))
        content_types = list(set(doc.metadata.get('content_type', '') for doc in self.documents))
        
        return {
            'total_documents': len(self.documents),
            'embedding_dimension': self.embedding_dim,
            'domains': domains,
            'sources': sources,
            'content_types': content_types,
            'index_file': str(self.index_file)
        }
    
    def clear(self):
        """Clear all documents from the store."""
        self.embeddings.clear()
        self.documents.clear()
        self.id_to_index.clear()
        self._save_index()
        log.info("Vector store cleared")

class FAISSVectorStore:
    """FAISS-based vector store (requires faiss-cpu package)."""
    
    def __init__(self, embedding_dim: int = 384, index_file: str = "data/faiss_index"):
        self.embedding_dim = embedding_dim
        self.index_file = Path(index_file)
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            log.error("FAISS not available, falling back to SimpleVectorStore")
            self.faiss = None
            self.fallback_store = SimpleVectorStore(embedding_dim, f"{index_file}.pkl")
            return
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(embedding_dim)  # Inner product (cosine similarity)
        self.documents: List[VectorDocument] = []
        self.id_to_index: Dict[str, int] = {}
        
        # Load existing index if available
        self._load_index()
        
        log.info(f"FAISS vector store initialized with {len(self.documents)} documents")
    
    def _load_index(self):
        """Load FAISS index from file."""
        if self.faiss is None:
            return
        
        index_path = f"{self.index_file}.faiss"
        metadata_path = f"{self.index_file}.pkl"
        
        if Path(index_path).exists() and Path(metadata_path).exists():
            try:
                # Load FAISS index
                self.index = self.faiss.read_index(index_path)
                
                # Load metadata
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                
                self.documents = data['documents']
                self.id_to_index = data['id_to_index']
                
                log.info(f"Loaded FAISS index with {len(self.documents)} documents")
            except Exception as e:
                log.error(f"Failed to load FAISS index: {e}")
    
    def _save_index(self):
        """Save FAISS index to file."""
        if self.faiss is None:
            return
        
        index_path = f"{self.index_file}.faiss"
        metadata_path = f"{self.index_file}.pkl"
        
        try:
            # Save FAISS index
            self.faiss.write_index(self.index, index_path)
            
            # Save metadata
            data = {
                'documents': self.documents,
                'id_to_index': self.id_to_index
            }
            
            with open(metadata_path, 'wb') as f:
                pickle.dump(data, f)
            
            log.info(f"Saved FAISS index with {len(self.documents)} documents")
        except Exception as e:
            log.error(f"Failed to save FAISS index: {e}")
    
    def add_document(self, content: NormalizedContent, chunk_size: int = 512) -> List[str]:
        """Add content to FAISS vector store."""
        if self.faiss is None:
            return self.fallback_store.add_document(content, chunk_size)
        
        # Implementation similar to SimpleVectorStore but using FAISS
        # This is a simplified version - full implementation would be more complex
        
        document_ids = []
        full_text = f"{content.title}\n\n{content.content}"
        
        if len(full_text) > chunk_size:
            chunks = self._chunk_text(full_text, chunk_size)
        else:
            chunks = [full_text]
        
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{content.url}_{i}".encode()).hexdigest()
            
            # Compute embedding (would use proper embedding model in production)
            embedding = self._compute_embedding(chunk)
            
            # Add to FAISS index
            self.index.add(embedding.reshape(1, -1))
            
            # Store metadata
            metadata = {
                'title': content.title,
                'url': content.url,
                'source': content.source,
                'domain': content.domain,
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
            
            document = VectorDocument(
                id=chunk_id,
                content=chunk,
                embedding=embedding,
                metadata=metadata,
                source=content.source,
                created_at=content.metadata.get('normalization_timestamp', '')
            )
            
            self.documents.append(document)
            self.id_to_index[chunk_id] = len(self.documents) - 1
            document_ids.append(chunk_id)
        
        self._save_index()
        return document_ids
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Chunk text into smaller pieces."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) + 1 > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for text."""
        # Simple fallback embedding
        features = []
        features.append(len(text))
        features.append(len(text.split()))
        
        char_counts = {}
        for char in text.lower():
            char_counts[char] = char_counts.get(char, 0) + 1
        
        sorted_chars = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)
        for i in range(self.embedding_dim - 2):
            if i < len(sorted_chars):
                features.append(sorted_chars[i][1])
            else:
                features.append(0)
        
        features = np.array(features, dtype=np.float32)
        if np.linalg.norm(features) > 0:
            features = features / np.linalg.norm(features)
        
        return features
    
    def search(self, query: str, top_k: int = 10, min_similarity: float = 0.0) -> List[Dict]:
        """Search for similar documents using FAISS."""
        if self.faiss is None:
            return self.fallback_store.search(query, top_k, min_similarity)
        
        if self.index.ntotal == 0:
            return []
        
        # Compute query embedding
        query_embedding = self._compute_embedding(query)
        
        # Search FAISS index
        similarities, indices = self.index.search(query_embedding.reshape(1, -1), top_k)
        
        results = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            if idx >= 0 and similarity >= min_similarity:
                doc = self.documents[idx]
                results.append({
                    'id': doc.id,
                    'content': doc.content,
                    'similarity': float(similarity),
                    'metadata': doc.metadata,
                    'source': doc.source,
                    'created_at': doc.created_at
                })
        
        return results

# Global vector store instance
_vector_store = None

def get_vector_store(use_faiss: bool = True) -> Any:
    """Get global vector store instance."""
    global _vector_store
    if _vector_store is None:
        if use_faiss:
            _vector_store = FAISSVectorStore()
        else:
            _vector_store = SimpleVectorStore()
    return _vector_store

def add_content_to_vector_store(content: NormalizedContent, 
                               chunk_size: int = 512) -> List[str]:
    """Convenience function to add content to vector store."""
    store = get_vector_store()
    return store.add_document(content, chunk_size)

def search_vector_store(query: str, top_k: int = 10, 
                       min_similarity: float = 0.0) -> List[Dict]:
    """Convenience function to search vector store."""
    store = get_vector_store()
    return store.search(query, top_k, min_similarity)
