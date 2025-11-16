"""
ConsistencyChecker - Checks consistency between claims and with knowledge base
Inspired by SSR (Socratic Self-Refine) for self-consistency validation
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class Claim:
    """Represents a factual claim extracted from response"""
    text: str
    citation: Optional[str]  # "[1]", "[2]", etc.
    entities: List[str]      # Extracted entities (StillMe, ChromaDB, etc.)
    values: Dict[str, str]   # Extracted values (time: "4 giờ", db: "ChromaDB")


class ConsistencyChecker:
    """Checks consistency between claims and with knowledge base"""
    
    def __init__(self):
        """Initialize consistency checker"""
        logger.info("ConsistencyChecker initialized")
        
        # Contradiction patterns
        self.time_patterns = [
            (r"(\d+)\s*giờ", "time_hours"),      # "4 giờ", "6 giờ"
            (r"mỗi\s+(\w+)", "frequency"),       # "mỗi 4 giờ", "mỗi ngày"
            (r"(\d+)\s*hours?", "time_hours_en"), # "4 hours", "6 hours"
        ]
        
        self.db_contradictions = [
            ("ChromaDB", "PostgreSQL"),
            ("ChromaDB", "MySQL"),
            ("vector database", "SQL database"),
            ("ChromaDB", "MongoDB"),
        ]
        
        self.model_contradictions = [
            ("DeepSeek", "GPT-5"),
            ("OpenAI", "GPT-5"),
            ("GPT-3.5", "GPT-4"),
        ]
    
    def extract_claims(self, response: str) -> List[Claim]:
        """
        Extract factual claims from response
        
        Looks for claims about StillMe (e.g., "StillMe học từ RSS", "StillMe sử dụng ChromaDB")
        
        Args:
            response: The response text to analyze
            
        Returns:
            List of Claim objects
        """
        if not response:
            return []
        
        claims = []
        seen_texts = set()  # Avoid duplicates
        
        # Strategy: Split by sentences first, then extract StillMe claims from each
        # This is more reliable than trying to match across sentence boundaries
        sentences = re.split(r'[\.\n]', response)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            
            # Check if sentence contains StillMe
            if not re.search(r'StillMe', sentence, re.IGNORECASE):
                continue
            
            # Extract claim from sentence
            # Pattern: StillMe followed by content until end of sentence or citation
            match = re.search(r"StillMe\s+(.+?)(?:\s*\[(\d+)\])?\s*$", sentence, re.IGNORECASE)
            if match:
                claim_text = match.group(1).strip()
                citation_group = match.group(2) if match.lastindex >= 2 and match.group(2) else None
                citation = f"[{citation_group}]" if citation_group else None
                
                # Skip if claim text is too short or duplicate
                if len(claim_text) < 5 or claim_text in seen_texts:
                    continue
                
                seen_texts.add(claim_text)
                
                # Extract entities and values
                entities = self._extract_entities(claim_text)
                values = self._extract_values(claim_text)
                
                claims.append(Claim(
                    text=claim_text,
                    citation=citation,
                    entities=entities,
                    values=values
                ))
        
        logger.debug(f"Extracted {len(claims)} claims from response")
        return claims
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        entities = []
        
        # Common entities in StillMe responses
        entity_patterns = [
            r"ChromaDB",
            r"PostgreSQL",
            r"MySQL",
            r"DeepSeek",
            r"OpenAI",
            r"GPT-\d+",
            r"RSS",
            r"arXiv",
            r"Wikipedia",
            r"Validation Chain",
            r"ValidatorChain",
        ]
        
        for pattern in entity_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = match.group(0)
                if entity not in entities:
                    entities.append(entity)
        
        return entities
    
    def _extract_values(self, text: str) -> Dict[str, str]:
        """Extract key-value pairs from text"""
        values = {}
        
        # Time values
        time_match = re.search(r"(\d+)\s*(giờ|hours?|h)", text, re.IGNORECASE)
        if time_match:
            values["time"] = time_match.group(0)
        
        # Frequency values
        freq_match = re.search(r"mỗi\s+(\w+)", text, re.IGNORECASE)
        if freq_match:
            values["frequency"] = freq_match.group(0)
        
        # Database values
        db_match = re.search(r"(ChromaDB|PostgreSQL|MySQL|MongoDB)", text, re.IGNORECASE)
        if db_match:
            values["database"] = db_match.group(0)
        
        # Model values
        model_match = re.search(r"(DeepSeek|OpenAI|GPT-\d+)", text, re.IGNORECASE)
        if model_match:
            values["model"] = model_match.group(0)
        
        return values
    
    def are_contradictory(self, claim1: Claim, claim2: Claim) -> bool:
        """
        Check if two claims contradict each other
        
        Args:
            claim1: First claim
            claim2: Second claim
            
        Returns:
            True if claims contradict, False otherwise
        """
        # Check time contradictions
        time1 = claim1.values.get("time")
        time2 = claim2.values.get("time")
        if time1 and time2:
            # Extract numbers
            num1 = re.search(r"(\d+)", time1)
            num2 = re.search(r"(\d+)", time2)
            if num1 and num2 and num1.group(1) != num2.group(1):
                # Check if same context (both about learning frequency, etc.)
                if self._same_context(claim1.text, claim2.text):
                    logger.debug(f"Time contradiction detected: {time1} vs {time2}")
                    return True
        
        # Check frequency contradictions
        freq1 = claim1.values.get("frequency")
        freq2 = claim2.values.get("frequency")
        if freq1 and freq2 and freq1 != freq2:
            if self._same_context(claim1.text, claim2.text):
                logger.debug(f"Frequency contradiction detected: {freq1} vs {freq2}")
                return True
        
        # Check database contradictions
        db1 = claim1.values.get("database")
        db2 = claim2.values.get("database")
        if db1 and db2:
            for db_pair in self.db_contradictions:
                if (db_pair[0] in db1 and db_pair[1] in db2) or \
                   (db_pair[1] in db1 and db_pair[0] in db2):
                    logger.debug(f"Database contradiction detected: {db1} vs {db2}")
                    return True
        
        # Check model contradictions
        model1 = claim1.values.get("model")
        model2 = claim2.values.get("model")
        if model1 and model2:
            for model_pair in self.model_contradictions:
                if (model_pair[0] in model1 and model_pair[1] in model2) or \
                   (model_pair[1] in model1 and model_pair[0] in model2):
                    logger.debug(f"Model contradiction detected: {model1} vs {model2}")
                    return True
        
        return False
    
    def _same_context(self, text1: str, text2: str) -> bool:
        """Check if two texts are about the same context"""
        # Common context keywords
        context_keywords = [
            "học", "learn", "lưu", "store", "sử dụng", "use",
            "embed", "tìm nạp", "fetch", "validation", "validate"
        ]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # Check if both texts contain similar context keywords
        for keyword in context_keywords:
            if keyword in text1_lower and keyword in text2_lower:
                return True
        
        return False
    
    def are_redundant(self, claim1: Claim, claim2: Claim) -> bool:
        """Check if two claims are redundant (say the same thing)"""
        # Simple check: if entities and values are very similar
        if set(claim1.entities) == set(claim2.entities) and \
           claim1.values == claim2.values:
            # Check text similarity (simple word overlap)
            words1 = set(claim1.text.lower().split())
            words2 = set(claim2.text.lower().split())
            overlap = len(words1.intersection(words2)) / max(len(words1), len(words2))
            if overlap > 0.7:  # 70% word overlap
                return True
        
        return False
    
    def check_pairwise_consistency(self, claims: List[Claim]) -> Dict[str, str]:
        """
        Check consistency between all pairs of claims
        
        Args:
            claims: List of claims to check
            
        Returns:
            Dictionary mapping claim pairs to consistency status
            ("CONTRADICTION", "REDUNDANT", or "CONSISTENT")
        """
        consistency_results = {}
        
        for i, claim1 in enumerate(claims):
            for j, claim2 in enumerate(claims[i+1:], start=i+1):
                if self.are_contradictory(claim1, claim2):
                    consistency_results[f"claim_{i}_vs_claim_{j}"] = "CONTRADICTION"
                elif self.are_redundant(claim1, claim2):
                    consistency_results[f"claim_{i}_vs_claim_{j}"] = "REDUNDANT"
                else:
                    consistency_results[f"claim_{i}_vs_claim_{j}"] = "CONSISTENT"
        
        contradictions = [k for k, v in consistency_results.items() if v == "CONTRADICTION"]
        if contradictions:
            logger.info(f"Detected {len(contradictions)} contradictions in claims")
        
        return consistency_results
    
    def check_kb_consistency(
        self,
        claim: Claim,
        ctx_docs: List[str]
    ) -> str:
        """
        Check if claim is consistent with knowledge base (RAG context)
        
        Args:
            claim: The claim to check
            ctx_docs: Context documents from RAG
            
        Returns:
            "CONSISTENT_WITH_KB", "PARTIALLY_CONSISTENT", "INCONSISTENT_WITH_KB", or "UNKNOWN"
        """
        if not ctx_docs:
            return "UNKNOWN"
        
        # Simple keyword overlap check
        claim_lower = claim.text.lower()
        context_text = " ".join(ctx_docs[:3]).lower()  # Use first 3 docs
        
        # Extract key terms from claim
        claim_words = set(claim_lower.split())
        context_words = set(context_text.split())
        
        # Filter stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'của', 'và', 'hoặc', 'nhưng', 'trong', 'trên', 'với', 'bởi', 'từ', 'đến', 'là', 'is', 'are'
        }
        claim_meaningful = claim_words - stop_words
        context_meaningful = context_words - stop_words
        
        # Calculate overlap
        if not claim_meaningful:
            return "UNKNOWN"
        
        overlap = len(claim_meaningful.intersection(context_meaningful)) / len(claim_meaningful)
        
        if overlap > 0.3:
            return "CONSISTENT_WITH_KB"
        elif overlap > 0.1:
            return "PARTIALLY_CONSISTENT"
        else:
            return "INCONSISTENT_WITH_KB"

