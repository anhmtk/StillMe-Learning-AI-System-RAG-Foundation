"""
Factual Plausibility Scanner (FPS)
Detects potentially non-existent concepts, events, or entities in user questions.

Hybrid Approach:
1. Known Concept Index (KCI) whitelist check
2. Pattern-based detection (fake citations, fabricated details)
3. Confidence-based uncertainty detection
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FPSResult:
    """Result from Factual Plausibility Scanner"""
    is_plausible: bool  # True if concept likely exists, False if suspicious
    confidence: float  # 0.0 to 1.0
    reason: str  # Why it's plausible or not
    detected_entities: List[str]  # Entities/concepts detected in question
    suspicious_patterns: List[str]  # Patterns that suggest fabrication


class KnownConceptIndex:
    """Known Concept Index - Whitelist of verified concepts"""
    
    def __init__(self, index_path: Optional[str] = None):
        if index_path is None:
            # Default path
            index_path = Path(__file__).parent / "kci_index.json"
        
        self.index_path = Path(index_path)
        self.index: Dict[str, Set[str]] = {}
        self._load_index()
    
    def _load_index(self):
        """Load KCI index from JSON file"""
        if not self.index_path.exists():
            logger.warning(f"KCI index not found at {self.index_path}, creating empty index")
            self.index = self._create_empty_index()
            self._save_index()
            return
        
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert lists to sets for faster lookup
                self.index = {
                    category: set(terms) for category, terms in data.items()
                }
            logger.info(f"Loaded KCI index with {sum(len(terms) for terms in self.index.values())} terms")
        except Exception as e:
            logger.error(f"Error loading KCI index: {e}")
            self.index = self._create_empty_index()
    
    def _create_empty_index(self) -> Dict[str, Set[str]]:
        """Create empty index structure"""
        return {
            "historical_events": set(),
            "physics_terms": set(),
            "chemistry_terms": set(),
            "biology_terms": set(),
            "geopolitical_entities": set(),
            "scientists": set(),
            "inventions": set(),
            "conferences": set(),
            "treaties": set(),
            "wars": set(),
        }
    
    def _save_index(self):
        """Save index to JSON file"""
        try:
            # Convert sets to lists for JSON serialization
            data = {
                category: sorted(list(terms)) for category, terms in self.index.items()
            }
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving KCI index: {e}")
    
    def check_term(self, term: str, category: Optional[str] = None) -> bool:
        """
        Check if a term exists in the index
        
        Args:
            term: Term to check (normalized to lowercase)
            category: Optional category to check (if None, checks all)
        
        Returns:
            True if term exists, False otherwise
        """
        term_lower = term.lower().strip()
        
        if category:
            return term_lower in self.index.get(category, set())
        
        # Check all categories
        for terms in self.index.values():
            if term_lower in terms:
                return True
        
        return False
    
    def add_term(self, term: str, category: str):
        """Add a term to the index"""
        term_lower = term.lower().strip()
        if category not in self.index:
            self.index[category] = set()
        self.index[category].add(term_lower)
        self._save_index()
        logger.debug(f"Added term '{term_lower}' to category '{category}'")


class FactualPlausibilityScanner:
    """
    Factual Plausibility Scanner
    
    Detects potentially non-existent concepts using:
    1. Known Concept Index (whitelist)
    2. Pattern-based detection (fake citations, fabricated details)
    3. Suspicious entity extraction
    """
    
    def __init__(self, kci_path: Optional[str] = None):
        self.kci = KnownConceptIndex(kci_path)
        
        # Patterns that suggest fabrication
        self.fake_citation_patterns = [
            r"\b[A-Z][a-z]+,\s*[A-Z]\.\s+et\s+al\.\s*\(\d{4}\)",  # "Smith, A. et al. (1975)"
            r"\b[A-Z][a-z]+\s+et\s+al\.\s*\(\d{4}\)",  # "Smith et al. (1975)"
            r"\bJournal\s+of\s+[A-Z][a-z]+\s+Studies",  # "Journal of X Studies"
            r"\b\d{4}\)\.\s*\"[^\"]+\"",  # Year followed by quoted title
        ]
        
        # Suspicious entity patterns (proper nouns that might be fabricated)
        self.entity_patterns = [
            r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+Field\b",  # "Bonded Consciousness Field"
            r"\b[A-Z][a-z]+\s+Syndrome\b",  # "Veridian Syndrome" (case-insensitive)
            r"\bHội\s+chứng\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+\b",  # "Hội chứng Veridian"
            r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+Fusion\b",  # "Diluted Nuclear Fusion"
            r"\b[A-Z][a-z]+\s+Conference\s+\d{4}\b",  # "Lisbon Peace Conference 1943"
            r"\b[A-Z][a-z]+\s+Treaty\s+\d{4}\b",  # "X Treaty 1943"
        ]
        
        # Historical event patterns
        self.historical_event_patterns = [
            r"\bconference\s+\d{4}\b",  # "conference 1943"
            r"\btreaty\s+\d{4}\b",  # "treaty 1943"
            r"\bwar\s+\d{4}\b",  # "war 1943"
            r"\bhội\s+nghị\s+\d{4}\b",  # "hội nghị 1943"
            r"\bhiệp\s+ước\s+\d{4}\b",  # "hiệp ước 1943"
        ]
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract potential entities/concepts from text"""
        entities = []
        
        # Extract capitalized phrases (potential proper nouns) - English
        capitalized_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        entities.extend(capitalized_phrases)
        
        # Extract quoted terms
        quoted_terms = re.findall(r'"([^"]+)"', text)
        entities.extend(quoted_terms)
        
        # Extract terms in parentheses
        parenthetical_terms = re.findall(r'\(([^)]+)\)', text)
        entities.extend(parenthetical_terms)
        
        # Extract Vietnamese proper nouns (capitalized Vietnamese words)
        # Pattern: Capitalized word followed by other capitalized words or common words
        vietnamese_proper_nouns = re.findall(
            r'\b[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+)*\b',
            text
        )
        entities.extend(vietnamese_proper_nouns)
        
        # Extract historical event patterns with years
        historical_patterns = [
            r'\b(?:hội nghị|hiệp ước|chiến tranh|war|conference|treaty)\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+\s+\d{4}\b',
            r'\b[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+\s+(?:hội nghị|hiệp ước|conference|treaty)\s+\d{4}\b',
        ]
        for pattern in historical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))  # Remove duplicates
    
    def check_patterns(self, text: str) -> Tuple[List[str], float]:
        """
        Check for suspicious patterns
        
        Returns:
            (suspicious_patterns, suspicion_score)
            suspicion_score: 0.0 (not suspicious) to 1.0 (very suspicious)
        """
        suspicious = []
        suspicion_score = 0.0
        
        text_lower = text.lower()
        
        # Check for fake citations
        for pattern in self.fake_citation_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                suspicious.append(f"fake_citation_pattern: {pattern}")
                suspicion_score += 0.3
        
        # Check for suspicious entity patterns
        # BUT: Only flag if entity is NOT in KCI (to avoid false positives for real events)
        for pattern in self.entity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Check if any match exists in KCI - if so, don't flag as suspicious
                real_entities = []
                for match in matches:
                    match_lower = match.lower().strip()
                    # Check in all KCI categories
                    if self.kci.check_term(match_lower):
                        real_entities.append(match)
                    else:
                        # Also check simplified version (e.g., "tehran conference 1943" -> "conference 1943")
                        year_match = re.search(r'\d{4}', match_lower)
                        if year_match:
                            year = year_match.group()
                            # Extract base event type
                            event_base = re.sub(r'^[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]+\s+', '', match_lower)
                            event_base = re.sub(r'\s+[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+\s+\d{4}', f' {year}', event_base)
                            if self.kci.check_term(event_base.strip()):
                                real_entities.append(match)
                
                # Only flag if NOT all matches are real entities
                if len(real_entities) < len(matches):
                    fake_matches = [m for m in matches if m not in real_entities]
                    suspicious.append(f"suspicious_entity_pattern: {fake_matches}")
                    suspicion_score += 0.2
        
        # Check for historical events with years
        historical_matches = []
        for pattern in self.historical_event_patterns:
            matches = re.findall(pattern, text_lower)
            historical_matches.extend(matches)
        
        if historical_matches:
            # Check if these events exist in KCI
            for match in historical_matches:
                if not self.kci.check_term(match, "historical_events"):
                    suspicious.append(f"unknown_historical_event: {match}")
                    suspicion_score += 0.25
        
        # Cap suspicion score at 1.0
        suspicion_score = min(1.0, suspicion_score)
        
        return suspicious, suspicion_score
    
    def scan(self, question: str) -> FPSResult:
        """
        Scan question for factual plausibility
        
        Args:
            question: User's question text
        
        Returns:
            FPSResult with is_plausible, confidence, reason, etc.
        """
        if not question:
            return FPSResult(
                is_plausible=True,
                confidence=1.0,
                reason="empty_question",
                detected_entities=[],
                suspicious_patterns=[]
            )
        
        # Extract entities
        entities = self.extract_entities(question)
        
        # Check patterns
        suspicious_patterns, suspicion_score = self.check_patterns(question)
        
        # Check entities against KCI
        unknown_entities = []
        known_entities = []
        
        for entity in entities:
            # Normalize entity (remove quotes, parentheses, etc.)
            normalized = re.sub(r'["()]', '', entity).strip()
            if not normalized:
                continue
            
            # Check if entity exists in KCI
            if self.kci.check_term(normalized):
                known_entities.append(normalized)
            else:
                # Check if it's a multi-word entity (might be a concept)
                words = normalized.split()
                if len(words) >= 2:  # Multi-word entities are more likely to be concepts
                    unknown_entities.append(normalized)
        
        # Determine plausibility
        # If we have suspicious patterns OR unknown entities that look like concepts
        is_plausible = True
        confidence = 1.0
        reason = "plausible"
        
        if suspicious_patterns:
            is_plausible = False
            # Confidence should be low when suspicious patterns are detected
            # suspicion_score ranges from 0.0 to 1.0, so confidence = 1.0 - suspicion_score
            # But we want confidence to be < 0.5 when suspicious, so cap it
            confidence = min(0.4, 1.0 - suspicion_score)
            reason = f"suspicious_patterns_detected: {', '.join(suspicious_patterns[:3])}"
        
        # If we have unknown entities that match suspicious patterns
        if unknown_entities:
            # Check if any unknown entity matches suspicious entity patterns
            question_lower = question.lower()
            for entity in unknown_entities:
                entity_lower = entity.lower()
                # Check if entity matches suspicious patterns
                for pattern in self.entity_patterns:
                    # Try both with and without word boundaries for better matching
                    pattern_no_boundary = pattern.replace(r'\b', '')
                    if re.search(pattern, entity, re.IGNORECASE) or \
                       re.search(pattern_no_boundary, entity_lower, re.IGNORECASE) or \
                       re.search(pattern_no_boundary, question_lower):
                        # Additional check: if it's a syndrome/concept and not in KCI, flag it
                        if "syndrome" in entity_lower or "hội chứng" in entity_lower:
                            if not self.kci.check_term(entity_lower):
                                is_plausible = False
                                confidence = min(confidence, 0.3)
                                reason = f"unknown_entity_matches_suspicious_pattern: {entity}"
                                break
                        else:
                            is_plausible = False
                            confidence = min(confidence, 0.3)
                            reason = f"unknown_entity_matches_suspicious_pattern: {entity}"
                            break
        
        # If we have historical events that don't exist in KCI
        # Check for patterns like "conference 1943", "hội nghị 1943", "Lisbon Conference 1943", "Hội nghị Hòa bình Lisbon 1943"
        question_lower = question.lower()
        
        # Pattern 1: Simple pattern "conference 1943", "hội nghị 1943"
        simple_pattern = r'\b(?:conference|treaty|war|hội nghị|hiệp ước)\s+\d{4}\b'
        simple_matches = re.findall(simple_pattern, question_lower)
        for event in simple_matches:
            if not self.kci.check_term(event, "historical_events"):
                is_plausible = False
                confidence = min(confidence, 0.3)
                reason = f"unknown_historical_event: {event}"
        
        # Pattern 2: Complex pattern with location "[Location] Conference 1943" or "Hội nghị [Location] 1943"
        # Match: "Lisbon Conference 1943", "Hội nghị Hòa bình Lisbon 1943"
        complex_patterns = [
            r'\b(?:conference|treaty|hội nghị|hiệp ước)\s+[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]+\d{4}\b',  # "hội nghị hòa bình lisbon 1943"
            r'\b[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+\s+(?:conference|treaty|hội nghị|hiệp ước)\s+\d{4}\b',  # "lisbon conference 1943"
        ]
        for pattern in complex_patterns:
            matches = re.findall(pattern, question_lower)
            for event in matches:
                # Extract year from event
                year_match = re.search(r'\d{4}', event)
                if year_match:
                    year = year_match.group()
                    # Check if "conference 1943" or "hội nghị 1943" exists in KCI
                    event_simple = re.sub(r'^[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]+', '', event)
                    event_simple = re.sub(r'\s+[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+\s+\d{4}', f' {year}', event_simple)
                    # Check both full event and simplified version
                    if not self.kci.check_term(event.strip(), "historical_events") and \
                       not self.kci.check_term(event_simple.strip(), "historical_events"):
                        is_plausible = False
                        confidence = min(confidence, 0.3)
                        reason = f"unknown_historical_event: {event.strip()}"
                        break
        
        return FPSResult(
            is_plausible=is_plausible,
            confidence=confidence,
            reason=reason,
            detected_entities=entities,
            suspicious_patterns=suspicious_patterns
        )


# Global instance
_fps_instance: Optional[FactualPlausibilityScanner] = None


def get_fps() -> FactualPlausibilityScanner:
    """Get global FPS instance"""
    global _fps_instance
    if _fps_instance is None:
        _fps_instance = FactualPlausibilityScanner()
    return _fps_instance


def scan_question(question: str) -> FPSResult:
    """Convenience function to scan a question"""
    fps = get_fps()
    return fps.scan(question)

