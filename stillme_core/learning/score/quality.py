"""
StillMe Quality Scoring
Rubric-based quality scoring for content evaluation.
"""

import logging
import yaml
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib

from stillme_core.learning.parser.normalize import NormalizedContent

log = logging.getLogger(__name__)

@dataclass
class QualityScore:
    """Quality score breakdown."""
    overall_score: float  # 0.0 to 1.0
    reputation_score: float
    relevance_score: float
    novelty_score: float
    evidence_score: float
    tech_depth_score: float
    recency_score: float
    penalty_score: float
    breakdown: Dict[str, float]
    confidence: float

class QualityScorer:
    """Scores content quality using rubric-based approach."""
    
    def __init__(self, policy_file: str = "policies/learning_policy.yaml"):
        self.policy_file = Path(policy_file)
        self.policy = self._load_policy()
        self.weights = self._load_weights()
        self.reputation_scores = self._load_reputation_scores()
        self.learning_objectives = self._load_learning_objectives()
        
        log.info("Quality scorer initialized")
    
    def _load_policy(self) -> Dict:
        """Load learning policy."""
        try:
            if self.policy_file.exists():
                with open(self.policy_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                return self._get_default_policy()
        except Exception as e:
            log.error(f"Failed to load policy: {e}")
            return self._get_default_policy()
    
    def _get_default_policy(self) -> Dict:
        """Get default policy if file loading fails."""
        return {
            'quality_weights': {
                'reputation': 0.30,
                'relevance': 0.25,
                'novelty': 0.15,
                'evidence': 0.15,
                'tech_depth': 0.10,
                'recency': 0.05
            },
            'reputation_scores': {
                'arxiv.org': 0.95,
                'openai.com': 0.90,
                'deepmind.com': 0.90,
                'github.com': 0.80,
                'stackoverflow.com': 0.70,
                'medium.com': 0.50,
                'reddit.com': 0.30
            },
            'learning_objectives': [
                'artificial_intelligence', 'machine_learning', 'natural_language_processing',
                'computer_vision', 'robotics', 'ethics_in_ai', 'ai_safety', 'transparency',
                'explainability', 'bias_detection', 'privacy_preservation', 'security'
            ]
        }
    
    def _load_weights(self) -> Dict[str, float]:
        """Load quality scoring weights."""
        return self.policy.get('quality_weights', {
            'reputation': 0.30,
            'relevance': 0.25,
            'novelty': 0.15,
            'evidence': 0.15,
            'tech_depth': 0.10,
            'recency': 0.05
        })
    
    def _load_reputation_scores(self) -> Dict[str, float]:
        """Load domain reputation scores."""
        return self.policy.get('reputation_scores', {
            'arxiv.org': 0.95,
            'openai.com': 0.90,
            'deepmind.com': 0.90,
            'github.com': 0.80,
            'stackoverflow.com': 0.70,
            'medium.com': 0.50,
            'reddit.com': 0.30
        })
    
    def _load_learning_objectives(self) -> List[str]:
        """Load learning objectives for relevance scoring."""
        return self.policy.get('learning_objectives', [
            'artificial_intelligence', 'machine_learning', 'natural_language_processing',
            'computer_vision', 'robotics', 'ethics_in_ai', 'ai_safety', 'transparency',
            'explainability', 'bias_detection', 'privacy_preservation', 'security'
        ])
    
    def score_reputation(self, content: NormalizedContent) -> float:
        """Score content based on source reputation."""
        domain = content.domain
        base_score = self.reputation_scores.get(domain, 0.5)
        
        # Adjust based on content type
        if content.content_type == 'research':
            base_score *= 1.1  # Research content gets bonus
        elif content.content_type == 'blog':
            base_score *= 0.9  # Blog content gets slight penalty
        
        # Adjust based on author presence
        if content.author:
            base_score *= 1.05  # Author attribution gets bonus
        
        return min(base_score, 1.0)
    
    def score_relevance(self, content: NormalizedContent) -> float:
        """Score content relevance to StillMe objectives."""
        text = f"{content.title} {content.content} {content.summary}".lower()
        tags_text = ' '.join(content.tags).lower()
        combined_text = f"{text} {tags_text}"
        
        # Count matches with learning objectives
        matches = 0
        total_objectives = len(self.learning_objectives)
        
        for objective in self.learning_objectives:
            # Check for exact matches and variations
            objective_variations = [
                objective,
                objective.replace('_', ' '),
                objective.replace('_', '-'),
                objective.replace('_', '')
            ]
            
            for variation in objective_variations:
                if variation in combined_text:
                    matches += 1
                    break
        
        # Calculate relevance score
        relevance_score = matches / total_objectives
        
        # Bonus for high-quality keywords
        quality_keywords = ['algorithm', 'model', 'framework', 'method', 'approach', 'technique']
        quality_matches = sum(1 for keyword in quality_keywords if keyword in combined_text)
        relevance_score += min(quality_matches * 0.05, 0.2)  # Max 0.2 bonus
        
        return min(relevance_score, 1.0)
    
    def score_novelty(self, content: NormalizedContent, existing_content: List[NormalizedContent] = None) -> float:
        """Score content novelty compared to existing knowledge."""
        if not existing_content:
            # If no existing content, assume high novelty
            return 0.8
        
        # Simple novelty scoring based on title and content similarity
        content_text = f"{content.title} {content.content}".lower()
        content_hash = hashlib.md5(content_text.encode()).hexdigest()
        
        # Check for exact duplicates
        for existing in existing_content:
            existing_text = f"{existing.title} {existing.content}".lower()
            existing_hash = hashlib.md5(existing_text.encode()).hexdigest()
            
            if content_hash == existing_hash:
                return 0.0  # Exact duplicate
        
        # Check for title similarity
        title_words = set(content.title.lower().split())
        max_title_similarity = 0.0
        
        for existing in existing_content:
            existing_title_words = set(existing.title.lower().split())
            if title_words and existing_title_words:
                similarity = len(title_words.intersection(existing_title_words)) / len(title_words.union(existing_title_words))
                max_title_similarity = max(max_title_similarity, similarity)
        
        # Novelty decreases with similarity
        novelty_score = 1.0 - max_title_similarity
        
        # Bonus for recent content (assumes newer = more novel)
        if content.normalized_date:
            try:
                content_date = datetime.fromisoformat(content.normalized_date.replace('Z', '+00:00'))
                days_old = (datetime.now(content_date.tzinfo) - content_date).days
                
                if days_old <= 7:
                    novelty_score += 0.1  # Recent content bonus
                elif days_old <= 30:
                    novelty_score += 0.05  # Slight recent bonus
            except:
                pass
        
        return min(novelty_score, 1.0)
    
    def score_evidence(self, content: NormalizedContent) -> float:
        """Score content based on evidence quality."""
        evidence_score = 0.5  # Base score
        
        # Check for citations
        citation_patterns = [
            r'\[[\d,\s]+\]',  # [1, 2, 3]
            r'\([A-Za-z]+\s+et\s+al\.?\s+\d{4}\)',  # (Smith et al. 2023)
            r'\([A-Za-z]+\s+\d{4}\)',  # (Smith 2023)
            r'https?://[^\s]+',  # URLs
            r'doi:[^\s]+',  # DOI references
        ]
        
        text = f"{content.content} {content.summary}"
        citation_count = 0
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, text)
            citation_count += len(matches)
        
        # Evidence score based on citation count
        if citation_count >= 5:
            evidence_score = 0.9
        elif citation_count >= 3:
            evidence_score = 0.8
        elif citation_count >= 1:
            evidence_score = 0.7
        else:
            evidence_score = 0.4
        
        # Bonus for data/statistics
        data_patterns = [
            r'\d+%',  # Percentages
            r'\d+\.\d+',  # Decimals
            r'\b\d+\s*(?:accuracy|precision|recall|f1|score|rate)\b',  # Metrics
        ]
        
        data_count = sum(len(re.findall(pattern, text)) for pattern in data_patterns)
        if data_count >= 3:
            evidence_score += 0.1
        
        # Bonus for code snippets
        if '```' in text or 'def ' in text or 'class ' in text:
            evidence_score += 0.05
        
        return min(evidence_score, 1.0)
    
    def score_tech_depth(self, content: NormalizedContent) -> float:
        """Score technical depth of content."""
        text = f"{content.title} {content.content}".lower()
        
        # Technical depth indicators
        depth_indicators = {
            'high': ['algorithm', 'architecture', 'implementation', 'optimization', 'complexity', 'theorem', 'proof'],
            'medium': ['method', 'approach', 'technique', 'framework', 'model', 'system'],
            'low': ['tutorial', 'guide', 'introduction', 'overview', 'summary']
        }
        
        depth_score = 0.5  # Base score
        
        for level, indicators in depth_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in text)
            if level == 'high':
                depth_score += matches * 0.1
            elif level == 'medium':
                depth_score += matches * 0.05
            else:
                depth_score -= matches * 0.05
        
        # Bonus for mathematical content
        math_patterns = [
            r'\$[^$]+\$',  # LaTeX math
            r'\\[a-zA-Z]+',  # LaTeX commands
            r'[a-zA-Z]\s*=\s*[a-zA-Z0-9+\-*/()]+',  # Equations
        ]
        
        math_count = sum(len(re.findall(pattern, text)) for pattern in math_patterns)
        if math_count >= 2:
            depth_score += 0.1
        
        # Bonus for code content
        code_indicators = ['function', 'class', 'import', 'def', 'return', 'if', 'for', 'while']
        code_matches = sum(1 for indicator in code_indicators if indicator in text)
        if code_matches >= 3:
            depth_score += 0.05
        
        return min(max(depth_score, 0.0), 1.0)
    
    def score_recency(self, content: NormalizedContent) -> float:
        """Score content recency."""
        if not content.normalized_date:
            return 0.5  # Unknown date gets neutral score
        
        try:
            content_date = datetime.fromisoformat(content.normalized_date.replace('Z', '+00:00'))
            days_old = (datetime.now(content_date.tzinfo) - content_date).days
            
            # Recency scoring
            if days_old <= 1:
                return 1.0
            elif days_old <= 7:
                return 0.9
            elif days_old <= 30:
                return 0.8
            elif days_old <= 90:
                return 0.6
            elif days_old <= 365:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            log.warning(f"Failed to parse date for recency scoring: {e}")
            return 0.5
    
    def calculate_penalty(self, content: NormalizedContent) -> float:
        """Calculate penalty score for content issues."""
        penalty = 0.0
        
        # Penalty for very short content
        if content.word_count < 100:
            penalty += 0.3
        elif content.word_count < 200:
            penalty += 0.1
        
        # Penalty for clickbait titles
        clickbait_patterns = [
            r'you won\'t believe',
            r'shocking',
            r'amazing',
            r'incredible',
            r'mind-blowing',
            r'this will change everything',
            r'secret',
            r'hack'
        ]
        
        title_lower = content.title.lower()
        for pattern in clickbait_patterns:
            if re.search(pattern, title_lower):
                penalty += 0.2
                break
        
        # Penalty for missing author
        if not content.author:
            penalty += 0.1
        
        # Penalty for missing license
        if not content.license or content.license == "Unknown":
            penalty += 0.1
        
        return min(penalty, 0.5)  # Max 50% penalty
    
    def score_content(self, content: NormalizedContent, existing_content: List[NormalizedContent] = None) -> QualityScore:
        """Score content quality using all criteria."""
        # Calculate individual scores
        reputation_score = self.score_reputation(content)
        relevance_score = self.score_relevance(content)
        novelty_score = self.score_novelty(content, existing_content)
        evidence_score = self.score_evidence(content)
        tech_depth_score = self.score_tech_depth(content)
        recency_score = self.score_recency(content)
        penalty_score = self.calculate_penalty(content)
        
        # Calculate weighted overall score
        overall_score = (
            self.weights['reputation'] * reputation_score +
            self.weights['relevance'] * relevance_score +
            self.weights['novelty'] * novelty_score +
            self.weights['evidence'] * evidence_score +
            self.weights['tech_depth'] * tech_depth_score +
            self.weights['recency'] * recency_score
        ) - penalty_score
        
        # Ensure score is between 0 and 1
        overall_score = max(0.0, min(overall_score, 1.0))
        
        # Create breakdown
        breakdown = {
            'reputation': reputation_score,
            'relevance': relevance_score,
            'novelty': novelty_score,
            'evidence': evidence_score,
            'tech_depth': tech_depth_score,
            'recency': recency_score,
            'penalty': penalty_score
        }
        
        return QualityScore(
            overall_score=overall_score,
            reputation_score=reputation_score,
            relevance_score=relevance_score,
            novelty_score=novelty_score,
            evidence_score=evidence_score,
            tech_depth_score=tech_depth_score,
            recency_score=recency_score,
            penalty_score=penalty_score,
            breakdown=breakdown,
            confidence=0.8
        )
    
    def score_batch(self, contents: List[NormalizedContent]) -> List[QualityScore]:
        """Score a batch of content items."""
        scores = []
        
        for content in contents:
            try:
                # Use other content as existing content for novelty scoring
                other_content = [c for c in contents if c != content]
                score = self.score_content(content, other_content)
                scores.append(score)
            except Exception as e:
                log.error(f"Quality scoring failed for content: {e}")
                # Create a low-quality score for failed scoring
                scores.append(QualityScore(
                    overall_score=0.0,
                    reputation_score=0.0,
                    relevance_score=0.0,
                    novelty_score=0.0,
                    evidence_score=0.0,
                    tech_depth_score=0.0,
                    recency_score=0.0,
                    penalty_score=1.0,
                    breakdown={},
                    confidence=0.0
                ))
        
        # Log statistics
        avg_score = sum(s.overall_score for s in scores) / len(scores) if scores else 0.0
        high_quality_count = sum(1 for s in scores if s.overall_score >= 0.7)
        
        log.info(f"Quality scoring: avg={avg_score:.2f}, {high_quality_count}/{len(scores)} high-quality")
        
        return scores

def score_content_quality(content: NormalizedContent, 
                         existing_content: List[NormalizedContent] = None,
                         policy_file: str = "policies/learning_policy.yaml") -> QualityScore:
    """Convenience function to score a single content item."""
    scorer = QualityScorer(policy_file)
    return scorer.score_content(content, existing_content)

def score_content_quality_batch(contents: List[NormalizedContent],
                               policy_file: str = "policies/learning_policy.yaml") -> List[QualityScore]:
    """Convenience function to score a batch of content items."""
    scorer = QualityScorer(policy_file)
    return scorer.score_batch(contents)
