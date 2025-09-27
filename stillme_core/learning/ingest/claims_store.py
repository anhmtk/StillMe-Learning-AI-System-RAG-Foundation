"""
StillMe Claims Store
SQLite-based storage for structured knowledge claims.
"""

import logging
import sqlite3
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from stillme_core.learning.parser.normalize import NormalizedContent

log = logging.getLogger(__name__)

@dataclass
class KnowledgeClaim:
    """Structured knowledge claim."""
    id: str
    subject: str
    predicate: str
    object: str
    source: str
    date: str
    confidence: float
    hash: str
    metadata: Dict[str, Any]

class ClaimsStore:
    """SQLite-based claims storage."""
    
    def __init__(self, db_file: str = "data/claims.db"):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        log.info(f"Claims store initialized: {self.db_file}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Create claims table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS claims (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    source TEXT NOT NULL,
                    date TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    hash TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for efficient querying
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject ON claims(subject)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_predicate ON claims(predicate)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_object ON claims(object)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON claims(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON claims(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash ON claims(hash)')
            
            # Create sources table for tracking content sources
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    author TEXT,
                    published_date TEXT,
                    content_type TEXT,
                    license TEXT,
                    word_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for sources
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_domain ON sources(domain)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_type ON sources(content_type)')
            
            conn.commit()
    
    def _generate_claim_id(self, subject: str, predicate: str, object: str, source: str) -> str:
        """Generate unique claim ID."""
        claim_text = f"{subject}|{predicate}|{object}|{source}"
        return hashlib.md5(claim_text.encode()).hexdigest()
    
    def _generate_claim_hash(self, subject: str, predicate: str, object: str) -> str:
        """Generate hash for claim content (without source)."""
        claim_text = f"{subject}|{predicate}|{object}"
        return hashlib.md5(claim_text.encode()).hexdigest()
    
    def add_source(self, content: NormalizedContent) -> str:
        """Add content source to database."""
        source_id = hashlib.md5(f"{content.url}{content.title}".encode()).hexdigest()
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Check if source already exists
            cursor.execute('SELECT id FROM sources WHERE id = ?', (source_id,))
            if cursor.fetchone():
                return source_id
            
            # Insert source
            cursor.execute('''
                INSERT INTO sources (id, title, url, domain, author, published_date, 
                                   content_type, license, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                source_id,
                content.title,
                content.url,
                content.domain,
                content.author,
                content.published_date,
                content.content_type,
                content.license,
                content.word_count
            ))
            
            conn.commit()
        
        return source_id
    
    def extract_claims(self, content: NormalizedContent) -> List[KnowledgeClaim]:
        """Extract structured claims from content."""
        claims = []
        
        # Simple claim extraction patterns
        text = f"{content.title} {content.content}"
        
        # Pattern 1: "X is Y" or "X are Y"
        is_patterns = [
            r'([A-Z][^.!?]*(?:is|are)\s+[^.!?]*[.!?])',
            r'([A-Z][^.!?]*(?:was|were)\s+[^.!?]*[.!?])',
        ]
        
        # Pattern 2: "X has Y" or "X have Y"
        has_patterns = [
            r'([A-Z][^.!?]*(?:has|have)\s+[^.!?]*[.!?])',
        ]
        
        # Pattern 3: "X can Y" or "X could Y"
        can_patterns = [
            r'([A-Z][^.!?]*(?:can|could|will|would|should|must|may|might)\s+[^.!?]*[.!?])',
        ]
        
        # Pattern 4: "X shows Y" or "X demonstrates Y"
        shows_patterns = [
            r'([A-Z][^.!?]*(?:shows?|demonstrates?|indicates?|suggests?|reveals?)\s+[^.!?]*[.!?])',
        ]
        
        all_patterns = is_patterns + has_patterns + can_patterns + shows_patterns
        
        import re
        for pattern in all_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                claim = self._parse_claim(match, content)
                if claim:
                    claims.append(claim)
        
        # Also extract from extracted_claims if available
        if hasattr(content, 'extracted_claims') and content.extracted_claims:
            for claim_text in content.extracted_claims:
                claim = self._parse_claim(claim_text, content)
                if claim:
                    claims.append(claim)
        
        return claims
    
    def _parse_claim(self, claim_text: str, content: NormalizedContent) -> Optional[KnowledgeClaim]:
        """Parse a claim text into structured format."""
        try:
            # Simple parsing - in production, this would be more sophisticated
            claim_text = claim_text.strip()
            
            # Extract subject, predicate, object
            words = claim_text.split()
            
            if len(words) < 3:
                return None
            
            # Find predicate (verb)
            predicate_words = ['is', 'are', 'was', 'were', 'has', 'have', 'can', 'could', 
                             'will', 'would', 'should', 'must', 'may', 'might', 'shows', 
                             'demonstrates', 'indicates', 'suggests', 'reveals']
            
            predicate_idx = -1
            predicate = ""
            
            for i, word in enumerate(words):
                if word.lower() in predicate_words:
                    predicate_idx = i
                    predicate = word.lower()
                    break
            
            if predicate_idx == -1 or predicate_idx == 0:
                return None
            
            subject = ' '.join(words[:predicate_idx])
            object_part = ' '.join(words[predicate_idx + 1:])
            
            # Clean up object (remove punctuation at end)
            object_part = object_part.rstrip('.!?')
            
            if not subject or not object_part:
                return None
            
            # Generate IDs
            claim_id = self._generate_claim_id(subject, predicate, object_part, content.source)
            claim_hash = self._generate_claim_hash(subject, predicate, object_part)
            
            # Create metadata
            metadata = {
                'original_text': claim_text,
                'source_title': content.title,
                'source_url': content.url,
                'source_domain': content.domain,
                'extraction_method': 'pattern_matching',
                'confidence_factors': {
                    'sentence_length': len(words),
                    'has_proper_noun': any(word[0].isupper() for word in words),
                    'has_verb': predicate_idx != -1
                }
            }
            
            # Calculate confidence
            confidence = self._calculate_confidence(claim_text, metadata)
            
            return KnowledgeClaim(
                id=claim_id,
                subject=subject,
                predicate=predicate,
                object=object_part,
                source=content.source,
                date=content.published_date or datetime.now().isoformat(),
                confidence=confidence,
                hash=claim_hash,
                metadata=metadata
            )
            
        except Exception as e:
            log.warning(f"Failed to parse claim: {e}")
            return None
    
    def _calculate_confidence(self, claim_text: str, metadata: Dict) -> float:
        """Calculate confidence score for a claim."""
        confidence = 0.5  # Base confidence
        
        # Adjust based on sentence length
        word_count = metadata['confidence_factors']['sentence_length']
        if 5 <= word_count <= 20:
            confidence += 0.2
        elif word_count > 20:
            confidence += 0.1
        
        # Adjust based on proper noun presence
        if metadata['confidence_factors']['has_proper_noun']:
            confidence += 0.1
        
        # Adjust based on verb presence
        if metadata['confidence_factors']['has_verb']:
            confidence += 0.1
        
        # Adjust based on source reputation
        domain = metadata['source_domain']
        if domain == 'arxiv.org':
            confidence += 0.2
        elif domain in ['openai.com', 'deepmind.com']:
            confidence += 0.15
        elif domain in ['github.com', 'stackoverflow.com']:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def add_claims(self, claims: List[KnowledgeClaim]) -> int:
        """Add claims to database."""
        if not claims:
            return 0
        
        added_count = 0
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            for claim in claims:
                try:
                    # Check if claim already exists (by hash)
                    cursor.execute('SELECT id FROM claims WHERE hash = ?', (claim.hash,))
                    if cursor.fetchone():
                        continue  # Skip duplicate
                    
                    # Insert claim
                    cursor.execute('''
                        INSERT INTO claims (id, subject, predicate, object, source, 
                                          date, confidence, hash, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        claim.id,
                        claim.subject,
                        claim.predicate,
                        claim.object,
                        claim.source,
                        claim.date,
                        claim.confidence,
                        claim.hash,
                        json.dumps(claim.metadata)
                    ))
                    
                    added_count += 1
                    
                except Exception as e:
                    log.warning(f"Failed to add claim {claim.id}: {e}")
                    continue
            
            conn.commit()
        
        log.info(f"Added {added_count} new claims to database")
        return added_count
    
    def ingest_content(self, content: NormalizedContent) -> Tuple[int, int]:
        """Ingest content and extract claims."""
        # Add source
        source_id = self.add_source(content)
        
        # Extract claims
        claims = self.extract_claims(content)
        
        # Add claims
        added_claims = self.add_claims(claims)
        
        return len(claims), added_claims
    
    def search_claims(self, subject: Optional[str] = None, 
                     predicate: Optional[str] = None,
                     object: Optional[str] = None,
                     source: Optional[str] = None,
                     min_confidence: float = 0.0,
                     limit: int = 100) -> List[KnowledgeClaim]:
        """Search for claims matching criteria."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Build query
            conditions = []
            params = []
            
            if subject:
                conditions.append('subject LIKE ?')
                params.append(f'%{subject}%')
            
            if predicate:
                conditions.append('predicate LIKE ?')
                params.append(f'%{predicate}%')
            
            if object:
                conditions.append('object LIKE ?')
                params.append(f'%{object}%')
            
            if source:
                conditions.append('source LIKE ?')
                params.append(f'%{source}%')
            
            conditions.append('confidence >= ?')
            params.append(min_confidence)
            
            where_clause = ' AND '.join(conditions) if conditions else '1=1'
            
            query = f'''
                SELECT id, subject, predicate, object, source, date, 
                       confidence, hash, metadata
                FROM claims
                WHERE {where_clause}
                ORDER BY confidence DESC, created_at DESC
                LIMIT ?
            '''
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            claims = []
            for row in rows:
                try:
                    metadata = json.loads(row[8]) if row[8] else {}
                    claim = KnowledgeClaim(
                        id=row[0],
                        subject=row[1],
                        predicate=row[2],
                        object=row[3],
                        source=row[4],
                        date=row[5],
                        confidence=row[6],
                        hash=row[7],
                        metadata=metadata
                    )
                    claims.append(claim)
                except Exception as e:
                    log.warning(f"Failed to parse claim from database: {e}")
                    continue
            
            return claims
    
    def get_statistics(self) -> Dict:
        """Get claims store statistics."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Get total claims
            cursor.execute('SELECT COUNT(*) FROM claims')
            total_claims = cursor.fetchone()[0]
            
            # Get total sources
            cursor.execute('SELECT COUNT(*) FROM sources')
            total_sources = cursor.fetchone()[0]
            
            # Get average confidence
            cursor.execute('SELECT AVG(confidence) FROM claims')
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            # Get top predicates
            cursor.execute('''
                SELECT predicate, COUNT(*) as count
                FROM claims
                GROUP BY predicate
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_predicates = cursor.fetchall()
            
            # Get top sources
            cursor.execute('''
                SELECT source, COUNT(*) as count
                FROM claims
                GROUP BY source
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_sources = cursor.fetchall()
            
            return {
                'total_claims': total_claims,
                'total_sources': total_sources,
                'average_confidence': round(avg_confidence, 3),
                'top_predicates': [{'predicate': p, 'count': c} for p, c in top_predicates],
                'top_sources': [{'source': s, 'count': c} for s, c in top_sources],
                'database_file': str(self.db_file)
            }
    
    def delete_claims_by_source(self, source: str) -> int:
        """Delete all claims from a specific source."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM claims WHERE source = ?', (source,))
            count = cursor.fetchone()[0]
            
            cursor.execute('DELETE FROM claims WHERE source = ?', (source,))
            conn.commit()
            
            log.info(f"Deleted {count} claims from source: {source}")
            return count

# Global claims store instance
_claims_store = None

def get_claims_store() -> ClaimsStore:
    """Get global claims store instance."""
    global _claims_store
    if _claims_store is None:
        _claims_store = ClaimsStore()
    return _claims_store

def ingest_content_claims(content: NormalizedContent) -> Tuple[int, int]:
    """Convenience function to ingest content and extract claims."""
    store = get_claims_store()
    return store.ingest_content(content)

def search_claims(subject: Optional[str] = None, 
                 predicate: Optional[str] = None,
                 object: Optional[str] = None,
                 source: Optional[str] = None,
                 min_confidence: float = 0.0,
                 limit: int = 100) -> List[KnowledgeClaim]:
    """Convenience function to search claims."""
    store = get_claims_store()
    return store.search_claims(subject, predicate, object, source, min_confidence, limit)
