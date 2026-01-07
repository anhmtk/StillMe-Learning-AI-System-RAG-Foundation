"""
Document Usage Tracker for Meta-Learning (Stage 2)

Tracks which documents from ChromaDB are actually used in responses.
This enables retention-based source trust adjustment.

Part of Stage 2: Meta-Learning - "AI improves HOW it learns"
"""

import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class DocumentUsageRecord:
    """Single record of document usage in a response"""
    timestamp: str  # ISO format
    query: str  # User query
    doc_id: str  # ChromaDB document ID
    source: str  # Source name (RSS feed URL, arXiv, Wikipedia, etc.)
    title: Optional[str] = None  # Document title
    used_in_response: bool = True  # Whether document was actually used (default: True if retrieved)
    similarity_score: Optional[float] = None  # Similarity score when retrieved
    response_confidence: Optional[float] = None  # Response confidence score
    validation_passed: Optional[bool] = None  # Whether validation passed


class DocumentUsageTracker:
    """
    Tracks document usage in responses for retention analysis.
    
    This is the foundation for Stage 2: Meta-Learning - retention-based
    source trust adjustment.
    """
    
    def __init__(self, persist_to_file: bool = True, usage_file: Optional[str] = None):
        """
        Initialize document usage tracker
        
        Args:
            persist_to_file: Whether to persist records to file
            usage_file: Path to usage file (default: data/document_usage.jsonl)
        """
        self.persist_to_file = persist_to_file
        self.usage_file = usage_file or "data/document_usage.jsonl"
        
        # In-memory storage: list of DocumentUsageRecord
        self._records: List[DocumentUsageRecord] = []
        
        # Ensure data directory exists
        if self.persist_to_file:
            Path(self.usage_file).parent.mkdir(parents=True, exist_ok=True)
            self._load_records()
        
        logger.info(f"DocumentUsageTracker initialized (persist={persist_to_file}, file={self.usage_file})")
    
    def _load_records(self):
        """Load usage records from file"""
        try:
            if Path(self.usage_file).exists():
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            record = DocumentUsageRecord(**data)
                            self._records.append(record)
                logger.info(f"Loaded {len(self._records)} document usage records from {self.usage_file}")
        except Exception as e:
            logger.warning(f"Failed to load document usage records from {self.usage_file}: {e}")
    
    def _save_record(self, record: DocumentUsageRecord):
        """Save a single record to file"""
        if self.persist_to_file:
            try:
                with open(self.usage_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"Failed to save document usage record to {self.usage_file}: {e}")
    
    def record_usage(
        self,
        query: str,
        doc_id: str,
        source: str,
        title: Optional[str] = None,
        used_in_response: bool = True,
        similarity_score: Optional[float] = None,
        response_confidence: Optional[float] = None,
        validation_passed: Optional[bool] = None
    ) -> None:
        """
        Record that a document was used in a response
        
        Args:
            query: User query
            doc_id: ChromaDB document ID
            source: Source name (RSS feed URL, arXiv, Wikipedia, etc.)
            title: Document title (optional)
            used_in_response: Whether document was actually used (default: True)
            similarity_score: Similarity score when retrieved (optional)
            response_confidence: Response confidence score (optional)
            validation_passed: Whether validation passed (optional)
        """
        record = DocumentUsageRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            query=query[:500],  # Truncate long queries
            doc_id=doc_id,
            source=source,
            title=title[:200] if title else None,  # Truncate long titles
            used_in_response=used_in_response,
            similarity_score=similarity_score,
            response_confidence=response_confidence,
            validation_passed=validation_passed
        )
        
        self._records.append(record)
        self._save_record(record)
        
        logger.debug(f"Recorded document usage: doc_id={doc_id[:50]}, source={source[:50]}, used={used_in_response}")
    
    def record_batch_usage(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        response_confidence: Optional[float] = None,
        validation_passed: Optional[bool] = None
    ) -> None:
        """
        Record usage for multiple documents at once
        
        Args:
            query: User query
            documents: List of document dicts with 'id', 'metadata', 'similarity' keys
            response_confidence: Response confidence score (optional)
            validation_passed: Whether validation passed (optional)
        """
        for doc in documents:
            doc_id = doc.get("id", "")
            if not doc_id:
                continue
            
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "") or metadata.get("source_url", "") or "unknown"
            title = metadata.get("title", "")
            similarity_score = doc.get("similarity") or doc.get("distance")
            
            # Convert distance to similarity if needed
            if similarity_score and similarity_score > 1.0:
                # It's a distance, convert to similarity
                similarity_score = 1.0 - (similarity_score / 2.0) if similarity_score < 2.0 else 0.0
            
            self.record_usage(
                query=query,
                doc_id=doc_id,
                source=source,
                title=title,
                used_in_response=True,  # If retrieved, assume used
                similarity_score=similarity_score,
                response_confidence=response_confidence,
                validation_passed=validation_passed
            )
    
    def calculate_retention_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate retention metrics per source
        
        Retention = (Documents used in responses) / (Total documents learned)
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with retention metrics per source:
            {
                "source_name": {
                    "total_learned": 1000,  # Total documents from this source
                    "total_used": 300,      # Documents used in responses
                    "retention_rate": 0.30, # 30% retention
                    "avg_similarity": 0.75, # Average similarity when used
                    "avg_confidence": 0.85,  # Average response confidence
                    "validation_pass_rate": 0.90  # Validation pass rate
                },
                ...
            }
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        recent_records = [
            r for r in self._records
            if datetime.fromisoformat(r.timestamp) >= cutoff_time
        ]
        
        if not recent_records:
            return {}
        
        # Get total documents learned per source (from learning metrics)
        # Note: For now, we use total_used as a proxy for total_learned
        # In production, this would query learning_metrics.jsonl to get actual learned counts
        source_totals: Dict[str, int] = {}
        try:
            # Try to get from learning metrics file if available
            learning_metrics_file = Path("data/learning_metrics.jsonl")
            if learning_metrics_file.exists():
                # Parse learning_metrics.jsonl to get total learned per source
                # This is a simplified version - in production, would use a proper parser
                import json
                with open(learning_metrics_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                source = data.get("source", "")
                                entries_added = data.get("entries_added", 0)
                                if source and entries_added:
                                    source_totals[source] = source_totals.get(source, 0) + entries_added
                            except Exception:
                                continue
        except Exception as e:
            logger.debug(f"Could not get total learned documents from learning_metrics.jsonl: {e}")
        
        # Aggregate usage by source
        source_stats: Dict[str, Dict[str, Any]] = {}
        
        for record in recent_records:
            source = record.source or "unknown"
            
            if source not in source_stats:
                source_stats[source] = {
                    "total_used": 0,
                    "total_learned": 0,  # Will be filled from learning metrics
                    "similarity_scores": [],
                    "confidence_scores": [],
                    "validation_passed_count": 0,
                    "validation_total_count": 0
                }
            
            stats = source_stats[source]
            stats["total_used"] += 1
            
            if record.similarity_score is not None:
                stats["similarity_scores"].append(record.similarity_score)
            
            if record.response_confidence is not None:
                stats["confidence_scores"].append(record.response_confidence)
            
            if record.validation_passed is not None:
                stats["validation_total_count"] += 1
                if record.validation_passed:
                    stats["validation_passed_count"] += 1
        
        # Calculate derived metrics
        for source, stats in source_stats.items():
            total_used = stats["total_used"]
            total_learned = stats.get("total_learned", total_used)  # Fallback: assume all used were learned
            
            # Calculate retention rate
            if total_learned > 0:
                stats["retention_rate"] = total_used / total_learned
            else:
                stats["retention_rate"] = 0.0
            
            # Calculate averages
            if stats["similarity_scores"]:
                stats["avg_similarity"] = sum(stats["similarity_scores"]) / len(stats["similarity_scores"])
            else:
                stats["avg_similarity"] = None
            
            if stats["confidence_scores"]:
                stats["avg_confidence"] = sum(stats["confidence_scores"]) / len(stats["confidence_scores"])
            else:
                stats["avg_confidence"] = None
            
            # Calculate validation pass rate
            if stats["validation_total_count"] > 0:
                stats["validation_pass_rate"] = stats["validation_passed_count"] / stats["validation_total_count"]
            else:
                stats["validation_pass_rate"] = None
            
            # Clean up lists (keep only counts)
            stats.pop("similarity_scores", None)
            stats.pop("confidence_scores", None)
        
        return source_stats
    
    def get_source_retention_rates(self, days: int = 30) -> Dict[str, float]:
        """
        Get retention rates per source (simplified version)
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary mapping source name to retention rate (0.0-1.0)
        """
        metrics = self.calculate_retention_metrics(days=days)
        return {
            source: stats.get("retention_rate", 0.0)
            for source, stats in metrics.items()
        }


# Global tracker instance (singleton pattern)
_usage_tracker_instance: Optional[DocumentUsageTracker] = None


def get_document_usage_tracker() -> DocumentUsageTracker:
    """Get global DocumentUsageTracker instance"""
    global _usage_tracker_instance
    if _usage_tracker_instance is None:
        _usage_tracker_instance = DocumentUsageTracker()
    return _usage_tracker_instance

