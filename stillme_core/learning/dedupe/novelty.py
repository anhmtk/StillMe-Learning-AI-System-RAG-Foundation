"""
StillMe Novelty Detection
MinHash + embedding cosine similarity for content deduplication.
"""

import logging
import hashlib
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
import json
import pickle

from stillme_core.learning.parser.normalize import NormalizedContent

log = logging.getLogger(__name__)

@dataclass
class NoveltyResult:
    """Novelty detection result."""
    is_novel: bool
    novelty_score: float  # 0.0 = duplicate, 1.0 = completely novel
    similar_items: List[Dict]
    max_similarity: float
    confidence: float

class MinHashDeduplicator:
    """MinHash-based content deduplication."""
    
    def __init__(self, num_hashes: int = 128, shingle_size: int = 3):
        self.num_hashes = num_hashes
        self.shingle_size = shingle_size
        self.hash_functions = self._generate_hash_functions()
        self.content_hashes: Dict[str, Set[int]] = {}
        self.content_metadata: Dict[str, Dict] = {}
        
        log.info(f"MinHash deduplicator initialized with {num_hashes} hashes, shingle size {shingle_size}")
    
    def _generate_hash_functions(self) -> List[callable]:
        """Generate hash functions for MinHash."""
        hash_functions = []
        for i in range(self.num_hashes):
            # Simple hash function: hash(x + i) % large_prime
            def make_hash_func(seed):
                def hash_func(x):
                    return hash(str(x) + str(seed)) % (2**32 - 1)
                return hash_func
            hash_functions.append(make_hash_func(i))
        return hash_functions
    
    def _create_shingles(self, text: str) -> Set[str]:
        """Create shingles from text."""
        if not text:
            return set()
        
        # Clean and tokenize text
        import re
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        if len(words) < self.shingle_size:
            return {text}
        
        shingles = set()
        for i in range(len(words) - self.shingle_size + 1):
            shingle = ' '.join(words[i:i + self.shingle_size])
            shingles.add(shingle)
        
        return shingles
    
    def _compute_minhash(self, shingles: Set[str]) -> Set[int]:
        """Compute MinHash signature for shingles."""
        minhash_signature = set()
        
        for hash_func in self.hash_functions:
            min_hash = float('inf')
            for shingle in shingles:
                hash_value = hash_func(shingle)
                min_hash = min(min_hash, hash_value)
            minhash_signature.add(int(min_hash))
        
        return minhash_signature
    
    def _jaccard_similarity(self, set1: Set[int], set2: Set[int]) -> float:
        """Calculate Jaccard similarity between two sets."""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def add_content(self, content: NormalizedContent) -> str:
        """Add content to deduplication index."""
        # Create content ID
        content_id = hashlib.md5(f"{content.title}{content.url}".encode()).hexdigest()
        
        # Create shingles from title and content
        text = f"{content.title} {content.content}"
        shingles = self._create_shingles(text)
        
        # Compute MinHash signature
        minhash_signature = self._compute_minhash(shingles)
        
        # Store in index
        self.content_hashes[content_id] = minhash_signature
        self.content_metadata[content_id] = {
            'title': content.title,
            'url': content.url,
            'source': content.source,
            'domain': content.domain,
            'published_date': content.published_date,
            'word_count': content.word_count
        }
        
        return content_id
    
    def check_novelty(self, content: NormalizedContent, threshold: float = 0.8) -> NoveltyResult:
        """Check if content is novel compared to existing content."""
        # Create content ID
        content_id = hashlib.md5(f"{content.title}{content.url}".encode()).hexdigest()
        
        # Create shingles and MinHash signature
        text = f"{content.title} {content.content}"
        shingles = self._create_shingles(text)
        minhash_signature = self._compute_minhash(shingles)
        
        # Find similar content
        similar_items = []
        max_similarity = 0.0
        
        for existing_id, existing_signature in self.content_hashes.items():
            if existing_id == content_id:
                continue  # Skip self
            
            similarity = self._jaccard_similarity(minhash_signature, existing_signature)
            
            if similarity > 0.1:  # Only consider items with some similarity
                similar_items.append({
                    'content_id': existing_id,
                    'similarity': similarity,
                    'metadata': self.content_metadata[existing_id]
                })
                max_similarity = max(max_similarity, similarity)
        
        # Sort by similarity
        similar_items.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Determine novelty
        is_novel = max_similarity < threshold
        novelty_score = 1.0 - max_similarity
        
        return NoveltyResult(
            is_novel=is_novel,
            novelty_score=novelty_score,
            similar_items=similar_items[:5],  # Top 5 similar items
            max_similarity=max_similarity,
            confidence=0.8
        )
    
    def get_statistics(self) -> Dict:
        """Get deduplication statistics."""
        return {
            'total_content': len(self.content_hashes),
            'num_hashes': self.num_hashes,
            'shingle_size': self.shingle_size,
            'domains': list(set(meta['domain'] for meta in self.content_metadata.values())),
            'sources': list(set(meta['source'] for meta in self.content_metadata.values()))
        }
    
    def save_index(self, filepath: str):
        """Save deduplication index to file."""
        try:
            data = {
                'content_hashes': {k: list(v) for k, v in self.content_hashes.items()},
                'content_metadata': self.content_metadata,
                'num_hashes': self.num_hashes,
                'shingle_size': self.shingle_size
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            
            log.info(f"Deduplication index saved to {filepath}")
        except Exception as e:
            log.error(f"Failed to save deduplication index: {e}")
    
    def load_index(self, filepath: str):
        """Load deduplication index from file."""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.content_hashes = {k: set(v) for k, v in data['content_hashes'].items()}
            self.content_metadata = data['content_metadata']
            self.num_hashes = data.get('num_hashes', self.num_hashes)
            self.shingle_size = data.get('shingle_size', self.shingle_size)
            
            log.info(f"Deduplication index loaded from {filepath}")
        except Exception as e:
            log.error(f"Failed to load deduplication index: {e}")

class EmbeddingDeduplicator:
    """Embedding-based content deduplication using cosine similarity."""
    
    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedding_model = embedding_model
        self.embeddings: Dict[str, np.ndarray] = {}
        self.content_metadata: Dict[str, Dict] = {}
        self.model = None
        
        log.info(f"Embedding deduplicator initialized with model: {embedding_model}")
    
    def _load_model(self):
        """Load embedding model."""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.embedding_model)
                log.info("Embedding model loaded successfully")
            except ImportError:
                log.warning("sentence-transformers not available, using fallback")
                self.model = None
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for text."""
        if self.model is None:
            # Fallback: simple hash-based embedding
            return self._fallback_embedding(text)
        
        try:
            embedding = self.model.encode(text)
            return embedding
        except Exception as e:
            log.warning(f"Embedding computation failed: {e}, using fallback")
            return self._fallback_embedding(text)
    
    def _fallback_embedding(self, text: str) -> np.ndarray:
        """Fallback embedding using simple text features."""
        # Simple feature-based embedding
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
        for i in range(10):
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
        for i in range(10):
            if i < len(sorted_words):
                features.append(sorted_words[i][1])
            else:
                features.append(0)
        
        # Normalize features
        features = np.array(features, dtype=np.float32)
        if np.linalg.norm(features) > 0:
            features = features / np.linalg.norm(features)
        
        return features
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def add_content(self, content: NormalizedContent) -> str:
        """Add content to embedding index."""
        # Create content ID
        content_id = hashlib.md5(f"{content.title}{content.url}".encode()).hexdigest()
        
        # Create text for embedding
        text = f"{content.title} {content.content}"
        
        # Compute embedding
        embedding = self._compute_embedding(text)
        
        # Store in index
        self.embeddings[content_id] = embedding
        self.content_metadata[content_id] = {
            'title': content.title,
            'url': content.url,
            'source': content.source,
            'domain': content.domain,
            'published_date': content.published_date,
            'word_count': content.word_count
        }
        
        return content_id
    
    def check_novelty(self, content: NormalizedContent, threshold: float = 0.8) -> NoveltyResult:
        """Check if content is novel using embedding similarity."""
        # Create content ID
        content_id = hashlib.md5(f"{content.title}{content.url}".encode()).hexdigest()
        
        # Create text and compute embedding
        text = f"{content.title} {content.content}"
        embedding = self._compute_embedding(text)
        
        # Find similar content
        similar_items = []
        max_similarity = 0.0
        
        for existing_id, existing_embedding in self.embeddings.items():
            if existing_id == content_id:
                continue  # Skip self
            
            similarity = self._cosine_similarity(embedding, existing_embedding)
            
            if similarity > 0.1:  # Only consider items with some similarity
                similar_items.append({
                    'content_id': existing_id,
                    'similarity': similarity,
                    'metadata': self.content_metadata[existing_id]
                })
                max_similarity = max(max_similarity, similarity)
        
        # Sort by similarity
        similar_items.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Determine novelty
        is_novel = max_similarity < threshold
        novelty_score = 1.0 - max_similarity
        
        return NoveltyResult(
            is_novel=is_novel,
            novelty_score=novelty_score,
            similar_items=similar_items[:5],  # Top 5 similar items
            max_similarity=max_similarity,
            confidence=0.8
        )

class HybridDeduplicator:
    """Hybrid deduplicator combining MinHash and embedding approaches."""
    
    def __init__(self, minhash_hashes: int = 128, shingle_size: int = 3, 
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.minhash_dedup = MinHashDeduplicator(minhash_hashes, shingle_size)
        self.embedding_dedup = EmbeddingDeduplicator(embedding_model)
        
        log.info("Hybrid deduplicator initialized")
    
    def add_content(self, content: NormalizedContent) -> str:
        """Add content to both deduplication systems."""
        minhash_id = self.minhash_dedup.add_content(content)
        embedding_id = self.embedding_dedup.add_content(content)
        
        # IDs should be the same
        assert minhash_id == embedding_id, "Content IDs should match"
        
        return minhash_id
    
    def check_novelty(self, content: NormalizedContent, threshold: float = 0.8) -> NoveltyResult:
        """Check novelty using both approaches and combine results."""
        # Get results from both systems
        minhash_result = self.minhash_dedup.check_novelty(content, threshold)
        embedding_result = self.embedding_dedup.check_novelty(content, threshold)
        
        # Combine similarities (take maximum)
        combined_max_similarity = max(minhash_result.max_similarity, embedding_result.max_similarity)
        
        # Combine similar items
        combined_similar_items = minhash_result.similar_items + embedding_result.similar_items
        
        # Remove duplicates and sort
        seen_ids = set()
        unique_similar_items = []
        for item in combined_similar_items:
            if item['content_id'] not in seen_ids:
                unique_similar_items.append(item)
                seen_ids.add(item['content_id'])
        
        unique_similar_items.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Determine novelty
        is_novel = combined_max_similarity < threshold
        novelty_score = 1.0 - combined_max_similarity
        
        return NoveltyResult(
            is_novel=is_novel,
            novelty_score=novelty_score,
            similar_items=unique_similar_items[:5],
            max_similarity=combined_max_similarity,
            confidence=0.9  # Higher confidence due to hybrid approach
        )
    
    def get_statistics(self) -> Dict:
        """Get combined statistics."""
        minhash_stats = self.minhash_dedup.get_statistics()
        return {
            'minhash': minhash_stats,
            'embedding_model': self.embedding_dedup.embedding_model,
            'total_content': minhash_stats['total_content']
        }
    
    def save_index(self, filepath: str):
        """Save both deduplication indices."""
        minhash_path = f"{filepath}.minhash"
        embedding_path = f"{filepath}.embedding"
        
        self.minhash_dedup.save_index(minhash_path)
        # Note: Embedding deduplicator doesn't have save/load yet
    
    def load_index(self, filepath: str):
        """Load both deduplication indices."""
        minhash_path = f"{filepath}.minhash"
        
        self.minhash_dedup.load_index(minhash_path)
        # Note: Embedding deduplicator doesn't have save/load yet

# Global deduplicator instance
_deduplicator = None

def get_deduplicator() -> HybridDeduplicator:
    """Get global deduplicator instance."""
    global _deduplicator
    if _deduplicator is None:
        _deduplicator = HybridDeduplicator()
    return _deduplicator

def check_content_novelty(content: NormalizedContent, threshold: float = 0.8) -> NoveltyResult:
    """Convenience function to check content novelty."""
    deduplicator = get_deduplicator()
    return deduplicator.check_novelty(content, threshold)

def add_content_to_index(content: NormalizedContent) -> str:
    """Convenience function to add content to deduplication index."""
    deduplicator = get_deduplicator()
    return deduplicator.add_content(content)
