"""
Advanced Quality Scorer for StillMe V2
Provides sophisticated content quality analysis beyond simple length checks
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Quality metrics for content analysis"""
    overall_score: float
    trust_contribution: float
    semantic_quality: float
    title_quality: float
    content_quality: float
    relevance_score: float
    novelty_score: float
    readability_score: float
    technical_depth: float

class AdvancedQualityScorer:
    """Advanced content quality scoring system"""
    
    def __init__(self):
        """Initialize Advanced Quality Scorer"""
        # Quality keywords for different domains
        self.quality_keywords = {
            "ai_research": [
                "machine learning", "deep learning", "neural network", "algorithm",
                "artificial intelligence", "data science", "model", "training",
                "optimization", "performance", "accuracy", "evaluation"
            ],
            "technology": [
                "software", "development", "programming", "code", "application",
                "system", "architecture", "framework", "library", "api",
                "database", "security", "performance", "scalability"
            ],
            "general": [
                "analysis", "research", "study", "findings", "results",
                "evidence", "data", "statistics", "trend", "impact"
            ]
        }
        
        # Low quality indicators
        self.low_quality_indicators = [
            "clickbait", "viral", "shocking", "amazing", "incredible",
            "you won't believe", "this will blow your mind", "must read",
            "breaking", "urgent", "exclusive", "secret"
        ]
        
        # Technical depth indicators
        self.technical_indicators = [
            "algorithm", "methodology", "framework", "architecture",
            "implementation", "optimization", "analysis", "evaluation",
            "benchmark", "performance", "scalability", "efficiency"
        ]
        
        logger.info("Advanced Quality Scorer initialized")
    
    def calculate_quality_score(self, content: Dict[str, Any]) -> QualityMetrics:
        """Calculate comprehensive quality score for content"""
        try:
            # Get basic components
            title = content.get("title", "")
            content_text = content.get("content", "")
            source_trust = content.get("source_trust_score", 0.5)
            category = content.get("source_category", "general")
            
            # Calculate individual components
            trust_contribution = self._calculate_trust_contribution(source_trust)
            semantic_quality = self._calculate_semantic_quality(content_text, category)
            title_quality = self._calculate_title_quality(title)
            content_quality = self._calculate_content_quality(content_text)
            relevance_score = self._calculate_relevance_score(content_text, category)
            novelty_score = self._calculate_novelty_score(content_text)
            readability_score = self._calculate_readability_score(content_text)
            technical_depth = self._calculate_technical_depth(content_text)
            
            # Calculate overall score with weighted components
            overall_score = (
                trust_contribution * 0.25 +
                semantic_quality * 0.20 +
                title_quality * 0.15 +
                content_quality * 0.15 +
                relevance_score * 0.10 +
                novelty_score * 0.05 +
                readability_score * 0.05 +
                technical_depth * 0.05
            )
            
            # Ensure score is within bounds
            overall_score = max(0.0, min(1.0, overall_score))
            
            return QualityMetrics(
                overall_score=overall_score,
                trust_contribution=trust_contribution,
                semantic_quality=semantic_quality,
                title_quality=title_quality,
                content_quality=content_quality,
                relevance_score=relevance_score,
                novelty_score=novelty_score,
                readability_score=readability_score,
                technical_depth=technical_depth
            )
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return QualityMetrics(
                overall_score=0.5,
                trust_contribution=0.5,
                semantic_quality=0.5,
                title_quality=0.5,
                content_quality=0.5,
                relevance_score=0.5,
                novelty_score=0.5,
                readability_score=0.5,
                technical_depth=0.5
            )
    
    def _calculate_trust_contribution(self, trust_score: float) -> float:
        """Calculate trust score contribution to overall quality"""
        return trust_score * 0.3 + 0.5  # Scale to 0.5-0.8 range
    
    def _calculate_semantic_quality(self, content: str, category: str) -> float:
        """Calculate semantic quality based on content analysis"""
        if not content:
            return 0.3
        
        content_lower = content.lower()
        score = 0.5
        
        # Check for quality keywords
        quality_keywords = self.quality_keywords.get(category, self.quality_keywords["general"])
        keyword_matches = sum(1 for keyword in quality_keywords if keyword in content_lower)
        score += min(0.3, keyword_matches * 0.05)
        
        # Check for low quality indicators
        low_quality_matches = sum(1 for indicator in self.low_quality_indicators if indicator in content_lower)
        score -= min(0.2, low_quality_matches * 0.05)
        
        # Check for proper sentence structure
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) > 1:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 10 <= avg_sentence_length <= 25:
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_title_quality(self, title: str) -> float:
        """Calculate title quality score"""
        if not title:
            return 0.2
        
        score = 0.5
        
        # Length check
        title_length = len(title)
        if 20 <= title_length <= 200:
            score += 0.2
        elif title_length < 10:
            score -= 0.2
        
        # Check for clickbait indicators
        title_lower = title.lower()
        clickbait_count = sum(1 for indicator in self.low_quality_indicators if indicator in title_lower)
        score -= clickbait_count * 0.1
        
        # Check for proper capitalization
        if title[0].isupper() and not title.isupper():
            score += 0.1
        
        # Check for question marks (often indicate low quality)
        if title.count('?') > 1:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_content_quality(self, content: str) -> float:
        """Calculate content quality score"""
        if not content:
            return 0.2
        
        score = 0.5
        
        # Length check
        content_length = len(content)
        if content_length > 100:
            score += 0.2
        elif content_length < 50:
            score -= 0.2
        
        # Word count check
        word_count = len(content.split())
        if word_count > 20:
            score += 0.1
        elif word_count < 10:
            score -= 0.1
        
        # Check for repetition
        words = content.lower().split()
        if len(words) > 0:
            unique_words = len(set(words))
            repetition_ratio = unique_words / len(words)
            if repetition_ratio > 0.7:
                score += 0.1
            elif repetition_ratio < 0.5:
                score -= 0.1
        
        # Check for proper punctuation
        if content.count('.') > 0 or content.count('!') > 0 or content.count('?') > 0:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_relevance_score(self, content: str, category: str) -> float:
        """Calculate relevance score for learning"""
        if not content:
            return 0.3
        
        score = 0.5
        content_lower = content.lower()
        
        # Check for learning-relevant keywords
        learning_keywords = [
            "learn", "study", "research", "analysis", "findings",
            "discover", "understand", "knowledge", "insight", "trend"
        ]
        
        keyword_matches = sum(1 for keyword in learning_keywords if keyword in content_lower)
        score += min(0.3, keyword_matches * 0.05)
        
        # Category-specific relevance
        if category in ["ai_research", "technology", "science"]:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_novelty_score(self, content: str) -> float:
        """Calculate novelty score (how new/unique the content is)"""
        if not content:
            return 0.3
        
        score = 0.5
        content_lower = content.lower()
        
        # Check for novelty indicators
        novelty_indicators = [
            "new", "latest", "recent", "emerging", "breakthrough",
            "innovative", "cutting-edge", "state-of-the-art", "novel"
        ]
        
        novelty_matches = sum(1 for indicator in novelty_indicators if indicator in content_lower)
        score += min(0.3, novelty_matches * 0.05)
        
        # Check for date references
        if re.search(r'\b(2024|2025|2026)\b', content):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score"""
        if not content:
            return 0.3
        
        score = 0.5
        
        # Simple readability metrics
        sentences = re.split(r'[.!?]+', content)
        words = content.split()
        
        if len(sentences) > 0 and len(words) > 0:
            avg_sentence_length = len(words) / len(sentences)
            
            # Optimal sentence length is 15-20 words
            if 15 <= avg_sentence_length <= 20:
                score += 0.2
            elif avg_sentence_length > 30:
                score -= 0.1
            
            # Check for complex words (longer than 6 characters)
            complex_words = sum(1 for word in words if len(word) > 6)
            complexity_ratio = complex_words / len(words)
            
            if complexity_ratio < 0.3:
                score += 0.1
            elif complexity_ratio > 0.5:
                score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_technical_depth(self, content: str) -> float:
        """Calculate technical depth score"""
        if not content:
            return 0.3
        
        score = 0.5
        content_lower = content.lower()
        
        # Check for technical indicators
        technical_matches = sum(1 for indicator in self.technical_indicators if indicator in content_lower)
        score += min(0.3, technical_matches * 0.05)
        
        # Check for numbers and statistics
        number_count = len(re.findall(r'\d+', content))
        if number_count > 3:
            score += 0.1
        
        # Check for technical terms
        technical_terms = [
            "algorithm", "methodology", "framework", "architecture",
            "implementation", "optimization", "analysis", "evaluation"
        ]
        
        term_matches = sum(1 for term in technical_terms if term in content_lower)
        score += min(0.2, term_matches * 0.05)
        
        return max(0.0, min(1.0, score))
    
    def get_quality_breakdown(self, content: Dict[str, Any]) -> Dict[str, float]:
        """Get detailed quality breakdown for content"""
        metrics = self.calculate_quality_score(content)
        
        return {
            "overall_score": metrics.overall_score,
            "trust_contribution": metrics.trust_contribution,
            "semantic_quality": metrics.semantic_quality,
            "title_quality": metrics.title_quality,
            "content_quality": metrics.content_quality,
            "relevance_score": metrics.relevance_score,
            "novelty_score": metrics.novelty_score,
            "readability_score": metrics.readability_score,
            "technical_depth": metrics.technical_depth
        }

# Global advanced quality scorer instance
advanced_quality_scorer = AdvancedQualityScorer()
