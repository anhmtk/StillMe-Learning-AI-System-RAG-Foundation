"""
Knowledge Consolidation Service for StillMe V2
Manages knowledge consolidation, deduplication, and compression
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeItem:
    """Individual knowledge item"""
    id: str
    title: str
    content: str
    source: str
    category: str
    quality_score: float
    trust_score: float
    created_at: str
    last_accessed: str
    access_count: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class ConsolidatedKnowledge:
    """Consolidated knowledge cluster"""
    cluster_id: str
    topic: str
    summary: str
    key_points: List[str]
    sources: List[str]
    knowledge_items: List[str]  # IDs of knowledge items
    confidence_score: float
    created_at: str
    last_updated: str
    access_count: int = 0

class KnowledgeConsolidationService:
    """Service for consolidating and managing knowledge"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize Knowledge Consolidation Service"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.knowledge_file = self.data_dir / "knowledge_base.json"
        self.consolidated_file = self.data_dir / "consolidated_knowledge.json"
        self.index_file = self.data_dir / "knowledge_index.json"
        
        # Load existing data
        self.knowledge_items = self._load_knowledge_items()
        self.consolidated_clusters = self._load_consolidated_knowledge()
        self.knowledge_index = self._load_knowledge_index()
        
        # Consolidation parameters
        self.similarity_threshold = 0.7
        self.min_cluster_size = 2
        self.max_cluster_size = 10
        self.compression_ratio = 0.3  # Keep 30% of original content
        
        logger.info("Knowledge Consolidation Service initialized")
    
    def _load_knowledge_items(self) -> Dict[str, KnowledgeItem]:
        """Load knowledge items from file"""
        if not self.knowledge_file.exists():
            return {}
        
        try:
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            knowledge_items = {}
            for item_id, item_data in data.items():
                knowledge_items[item_id] = KnowledgeItem(**item_data)
            
            return knowledge_items
        except Exception as e:
            logger.error(f"Failed to load knowledge items: {e}")
            return {}
    
    def _load_consolidated_knowledge(self) -> Dict[str, ConsolidatedKnowledge]:
        """Load consolidated knowledge from file"""
        if not self.consolidated_file.exists():
            return {}
        
        try:
            with open(self.consolidated_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            consolidated = {}
            for cluster_id, cluster_data in data.items():
                consolidated[cluster_id] = ConsolidatedKnowledge(**cluster_data)
            
            return consolidated
        except Exception as e:
            logger.error(f"Failed to load consolidated knowledge: {e}")
            return {}
    
    def _load_knowledge_index(self) -> Dict[str, List[str]]:
        """Load knowledge index from file"""
        if not self.index_file.exists():
            return {}
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load knowledge index: {e}")
            return {}
    
    def _save_knowledge_items(self):
        """Save knowledge items to file"""
        try:
            data = {
                item_id: asdict(item) 
                for item_id, item in self.knowledge_items.items()
            }
            
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save knowledge items: {e}")
    
    def _save_consolidated_knowledge(self):
        """Save consolidated knowledge to file"""
        try:
            data = {
                cluster_id: asdict(cluster) 
                for cluster_id, cluster in self.consolidated_clusters.items()
            }
            
            with open(self.consolidated_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save consolidated knowledge: {e}")
    
    def _save_knowledge_index(self):
        """Save knowledge index to file"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_index, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save knowledge index: {e}")
    
    def add_knowledge_item(self, title: str, content: str, source: str, 
                          category: str, quality_score: float, trust_score: float) -> str:
        """Add a new knowledge item"""
        try:
            # Generate unique ID
            item_id = self._generate_knowledge_id(title, content, source)
            
            # Check for duplicates
            if item_id in self.knowledge_items:
                logger.debug(f"Knowledge item already exists: {item_id}")
                return item_id
            
            # Create knowledge item
            knowledge_item = KnowledgeItem(
                id=item_id,
                title=title,
                content=content,
                source=source,
                category=category,
                quality_score=quality_score,
                trust_score=trust_score,
                created_at=datetime.now().isoformat(),
                last_accessed=datetime.now().isoformat(),
                access_count=0,
                tags=self._extract_tags(title, content)
            )
            
            # Add to knowledge base
            self.knowledge_items[item_id] = knowledge_item
            
            # Update index
            self._update_index(knowledge_item)
            
            # Save data
            self._save_knowledge_items()
            self._save_knowledge_index()
            
            logger.info(f"Added knowledge item: {item_id}")
            return item_id
            
        except Exception as e:
            logger.error(f"Failed to add knowledge item: {e}")
            return ""
    
    def _generate_knowledge_id(self, title: str, content: str, source: str) -> str:
        """Generate unique ID for knowledge item"""
        content_hash = hashlib.md5(f"{title}|{content[:100]}|{source}".encode()).hexdigest()[:12]
        return f"kb_{content_hash}"
    
    def _extract_tags(self, title: str, content: str) -> List[str]:
        """Extract tags from title and content"""
        tags = set()
        
        # Extract from title
        title_words = re.findall(r'\b\w+\b', title.lower())
        tags.update([word for word in title_words if len(word) > 3])
        
        # Extract from content (first 200 chars)
        content_words = re.findall(r'\b\w+\b', content[:200].lower())
        tags.update([word for word in content_words if len(word) > 3])
        
        # Limit to 10 tags
        return list(tags)[:10]
    
    def _update_index(self, knowledge_item: KnowledgeItem):
        """Update knowledge index"""
        # Index by category
        if knowledge_item.category not in self.knowledge_index:
            self.knowledge_index[knowledge_item.category] = []
        
        if knowledge_item.id not in self.knowledge_index[knowledge_item.category]:
            self.knowledge_index[knowledge_item.category].append(knowledge_item.id)
        
        # Index by tags
        for tag in knowledge_item.tags:
            if tag not in self.knowledge_index:
                self.knowledge_index[tag] = []
            
            if knowledge_item.id not in self.knowledge_index[tag]:
                self.knowledge_index[tag].append(knowledge_item.id)
    
    def consolidate_knowledge(self) -> Dict[str, Any]:
        """Consolidate knowledge items into clusters"""
        try:
            logger.info("Starting knowledge consolidation...")
            
            # Group by category first
            category_groups = defaultdict(list)
            for item in self.knowledge_items.values():
                category_groups[item.category].append(item)
            
            consolidation_results = {
                "clusters_created": 0,
                "items_consolidated": 0,
                "items_removed": 0,
                "compression_ratio": 0.0
            }
            
            total_items_before = len(self.knowledge_items)
            
            # Process each category
            for category, items in category_groups.items():
                if len(items) < self.min_cluster_size:
                    continue
                
                # Find similar items
                clusters = self._find_similar_clusters(items)
                
                # Consolidate each cluster
                for cluster_items in clusters:
                    if len(cluster_items) >= self.min_cluster_size:
                        consolidated = self._create_consolidated_cluster(cluster_items)
                        if consolidated:
                            self.consolidated_clusters[consolidated.cluster_id] = consolidated
                            consolidation_results["clusters_created"] += 1
                            consolidation_results["items_consolidated"] += len(cluster_items)
                            
                            # Remove original items
                            for item in cluster_items:
                                if item.id in self.knowledge_items:
                                    del self.knowledge_items[item.id]
                                    consolidation_results["items_removed"] += len(cluster_items)
            
            # Calculate compression ratio
            total_items_after = len(self.knowledge_items)
            if total_items_before > 0:
                consolidation_results["compression_ratio"] = 1.0 - (total_items_after / total_items_before)
            
            # Save consolidated data
            self._save_knowledge_items()
            self._save_consolidated_knowledge()
            
            logger.info(f"Knowledge consolidation completed: {consolidation_results}")
            return consolidation_results
            
        except Exception as e:
            logger.error(f"Knowledge consolidation failed: {e}")
            return {"error": str(e)}
    
    def _find_similar_clusters(self, items: List[KnowledgeItem]) -> List[List[KnowledgeItem]]:
        """Find clusters of similar knowledge items"""
        clusters = []
        used_items = set()
        
        for i, item1 in enumerate(items):
            if item1.id in used_items:
                continue
            
            cluster = [item1]
            used_items.add(item1.id)
            
            for j, item2 in enumerate(items[i+1:], i+1):
                if item2.id in used_items:
                    continue
                
                if self._calculate_similarity(item1, item2) >= self.similarity_threshold:
                    cluster.append(item2)
                    used_items.add(item2.id)
                    
                    if len(cluster) >= self.max_cluster_size:
                        break
            
            if len(cluster) >= self.min_cluster_size:
                clusters.append(cluster)
        
        return clusters
    
    def _calculate_similarity(self, item1: KnowledgeItem, item2: KnowledgeItem) -> float:
        """Calculate similarity between two knowledge items"""
        # Title similarity
        title_sim = self._text_similarity(item1.title, item2.title)
        
        # Content similarity (first 500 chars)
        content_sim = self._text_similarity(item1.content[:500], item2.content[:500])
        
        # Tag similarity
        tag_sim = self._tag_similarity(item1.tags, item2.tags)
        
        # Weighted similarity
        similarity = (title_sim * 0.4 + content_sim * 0.4 + tag_sim * 0.2)
        return similarity
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using Jaccard similarity"""
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _tag_similarity(self, tags1: List[str], tags2: List[str]) -> float:
        """Calculate tag similarity"""
        if not tags1 and not tags2:
            return 1.0
        
        set1 = set(tags1)
        set2 = set(tags2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _create_consolidated_cluster(self, items: List[KnowledgeItem]) -> Optional[ConsolidatedKnowledge]:
        """Create consolidated knowledge cluster from items"""
        try:
            # Generate cluster ID
            cluster_id = f"cluster_{hashlib.md5('|'.join([item.id for item in items]).encode()).hexdigest()[:8]}"
            
            # Extract topic from most common words in titles
            all_titles = [item.title for item in items]
            topic = self._extract_topic(all_titles)
            
            # Create summary
            summary = self._create_summary(items)
            
            # Extract key points
            key_points = self._extract_key_points(items)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(items)
            
            # Get sources
            sources = list(set([item.source for item in items]))
            
            # Create consolidated knowledge
            consolidated = ConsolidatedKnowledge(
                cluster_id=cluster_id,
                topic=topic,
                summary=summary,
                key_points=key_points,
                sources=sources,
                knowledge_items=[item.id for item in items],
                confidence_score=confidence_score,
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                access_count=0
            )
            
            return consolidated
            
        except Exception as e:
            logger.error(f"Failed to create consolidated cluster: {e}")
            return None
    
    def _extract_topic(self, titles: List[str]) -> str:
        """Extract topic from titles"""
        # Count word frequency
        word_counts = Counter()
        for title in titles:
            words = re.findall(r'\b\w+\b', title.lower())
            word_counts.update([word for word in words if len(word) > 3])
        
        # Get most common words
        common_words = [word for word, count in word_counts.most_common(3)]
        return " ".join(common_words) if common_words else "General Topic"
    
    def _create_summary(self, items: List[KnowledgeItem]) -> str:
        """Create summary from knowledge items"""
        # Combine content from all items
        all_content = " ".join([item.content for item in items])
        
        # Extract key sentences (simple approach)
        sentences = re.split(r'[.!?]+', all_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Take first few sentences as summary
        summary_sentences = sentences[:3]
        summary = ". ".join(summary_sentences)
        
        # Limit length
        if len(summary) > 500:
            summary = summary[:500] + "..."
        
        return summary
    
    def _extract_key_points(self, items: List[KnowledgeItem]) -> List[str]:
        """Extract key points from knowledge items"""
        key_points = []
        
        # Extract from titles
        for item in items:
            if len(item.title) > 10:
                key_points.append(item.title)
        
        # Extract from content (first sentence of each item)
        for item in items:
            first_sentence = re.split(r'[.!?]+', item.content)[0].strip()
            if len(first_sentence) > 20 and first_sentence not in key_points:
                key_points.append(first_sentence)
        
        # Limit to 5 key points
        return key_points[:5]
    
    def _calculate_confidence_score(self, items: List[KnowledgeItem]) -> float:
        """Calculate confidence score for consolidated cluster"""
        if not items:
            return 0.0
        
        # Average quality and trust scores
        avg_quality = sum(item.quality_score for item in items) / len(items)
        avg_trust = sum(item.trust_score for item in items) / len(items)
        
        # Bonus for multiple sources
        source_bonus = min(0.2, len(set(item.source for item in items)) * 0.05)
        
        confidence = (avg_quality * 0.4 + avg_trust * 0.4 + source_bonus)
        return min(1.0, confidence)
    
    def search_knowledge(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        try:
            results = []
            query_lower = query.lower()
            
            # Search in knowledge items
            for item in self.knowledge_items.values():
                if category and item.category != category:
                    continue
                
                score = 0.0
                
                # Title match
                if query_lower in item.title.lower():
                    score += 0.5
                
                # Content match
                if query_lower in item.content.lower():
                    score += 0.3
                
                # Tag match
                for tag in item.tags:
                    if query_lower in tag.lower():
                        score += 0.2
                
                if score > 0:
                    results.append({
                        "type": "knowledge_item",
                        "id": item.id,
                        "title": item.title,
                        "content": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                        "source": item.source,
                        "category": item.category,
                        "score": score,
                        "created_at": item.created_at
                    })
            
            # Search in consolidated clusters
            for cluster in self.consolidated_clusters.values():
                if category and not any(cat in cluster.topic.lower() for cat in [category]):
                    continue
                
                score = 0.0
                
                # Topic match
                if query_lower in cluster.topic.lower():
                    score += 0.4
                
                # Summary match
                if query_lower in cluster.summary.lower():
                    score += 0.3
                
                # Key points match
                for point in cluster.key_points:
                    if query_lower in point.lower():
                        score += 0.3
                
                if score > 0:
                    results.append({
                        "type": "consolidated_cluster",
                        "id": cluster.cluster_id,
                        "title": cluster.topic,
                        "content": cluster.summary,
                        "sources": cluster.sources,
                        "key_points": cluster.key_points,
                        "score": score,
                        "created_at": cluster.created_at
                    })
            
            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:20]  # Limit to 20 results
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            stats = {
                "total_knowledge_items": len(self.knowledge_items),
                "total_consolidated_clusters": len(self.consolidated_clusters),
                "categories": len(set(item.category for item in self.knowledge_items.values())),
                "sources": len(set(item.source for item in self.knowledge_items.values())),
                "avg_quality_score": 0.0,
                "avg_trust_score": 0.0,
                "total_tags": len(self.knowledge_index)
            }
            
            if self.knowledge_items:
                stats["avg_quality_score"] = sum(item.quality_score for item in self.knowledge_items.values()) / len(self.knowledge_items)
                stats["avg_trust_score"] = sum(item.trust_score for item in self.knowledge_items.values()) / len(self.knowledge_items)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get knowledge stats: {e}")
            return {}

# Global knowledge consolidation service instance
knowledge_consolidation_service = KnowledgeConsolidationService()
