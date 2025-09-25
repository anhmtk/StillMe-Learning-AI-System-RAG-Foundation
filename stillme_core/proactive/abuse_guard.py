#!/usr/bin/env python3
"""
Proactive Suggestion Abuse Guard
================================

Bảo vệ hệ thống đề xuất chủ động khỏi spam/slang/keyword abuse

Author: StillMe Framework Team
Version: 1.0.0
"""

import re
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class AbuseGuardResult:
    """Kết quả kiểm tra abuse guard"""
    should_suggest: bool
    confidence: float
    abuse_score: float
    reasoning: str
    features: Dict[str, Any]
    latency_ms: float

class ProactiveAbuseGuard:
    """Guard bảo vệ hệ thống đề xuất chủ động khỏi abuse"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Thresholds
        self.suggestion_threshold = self.config.get("suggestion_threshold", 0.85)  # Balanced threshold
        self.abuse_threshold = self.config.get("abuse_threshold", 0.20)  # Balanced threshold
        self.rate_limit_window = self.config.get("rate_limit_window", 30)  # seconds
        self.max_suggestions_per_window = self.config.get("max_suggestions_per_window", 2)
        
        # Session tracking
        self.session_suggestions = defaultdict(list)  # session_id -> [timestamps]
        
        # Load heuristics
        self._load_slang_lexicon()
        self._load_stop_words()
        self._load_emoji_patterns()
        
        # Performance tracking
        self.stats = {
            "total_requests": 0,
            "suggestions_allowed": 0,
            "suggestions_blocked": 0,
            "rate_limits_hit": 0,
            "total_latency_ms": 0.0
        }
    
    def _load_slang_lexicon(self):
        """Load slang lexicon for detection"""
        self.slang_patterns = [
            # Internet slang
            r"\b(lol|lmao|rofl|wtf|omg|btw|fyi|imo|imho|tbh|nvm|idk|ikr|smh|tldr|afaik|asap|diy|aka)\b",
            r"\b(yo|pls|thx|np|brb|gg|gl|hf|irl|afk|fomo|yolo|swag|lit|dope|chill|squad|fam|bro|sis|dude|gal|guy|peeps|folks|y'all|af)\b",
            r"\b(can\s+u|u\s+can|u\s+help|help\s+me\s+out)\b",
            # Modern slang
            r"\b(sus|no\s+cap|bussin|mid|fire|lit|pop|slay|periodt|bet|fr|ngl|lowkey|highkey|stan|ship|flex|clout|cap)\b",
            r"\b(that's\s+funny\s+af|spill\s+the\s+tea|it's\s+giving|main\s+character\s+energy|that's\s+a\s+vibe|make\s+it\s+aesthetic)\b",
            # Additional slang patterns
            r"\b(btw\s+fyi|imo\s+this|tbh\s+this|nvm\s+then|idk\s+what|ikr\s+right|smh\s+my|tldr\s+version)\b",
            r"\b(yo\s+can|pls\s+help|thx\s+so|np\s+problem|brb\s+in|gg\s+wp|gl\s+hf|hf\s+gl)\b",
            r"\b(irl\s+life|afk\s+now|fomo\s+about|yolo\s+swag|swag\s+life|lit\s+af|dope\s+as|chill\s+out)\b",
            # Enhanced patterns for failed cases
            r"\b(lol|lmao|rofl)\s+(that's|this|it's)\b",  # "lol that's"
            r"\b(that's|this|it's)\s+(funny|good|bad|weird)\s+(af|lol|fr)\b",  # "that's funny af"
            r"\b(it's\s+giving|that's\s+giving)\b",  # "it's giving"
            r"\b(main\s+character\s+energy|main\s+character)\b",  # "main character energy"
            r"\b(that's\s+mid|it's\s+mid|this\s+is\s+mid)\b",  # "that's mid"
            # Context-aware patterns
            r"\b\w+\s+(af|fr|ngl|lowkey|highkey)\b",  # Word + slang suffix
            r"\b(it's|that's|this\s+is)\s+(giving|bussin|fire|lit|mid)\b",  # "it's giving X"
            # Vietnamese slang patterns
            r"\b(vl|phết|thật)\b",  # Vietnamese slang words
            r"\b\w+\s+(vl|phết)\b",  # Word + Vietnamese slang suffix
            r"\b(vl|phết)\s+\w+\b",  # Vietnamese slang + word
        ]
    
    def _load_stop_words(self):
        """Load stop words for density calculation"""
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "must", "can", "this", "that", "these", "those",
            "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her", "its", "our", "their"
        }
    
    def _load_emoji_patterns(self):
        """Load emoji patterns for spam detection"""
        self.emoji_patterns = [
            r"[\U0001F600-\U0001F64F]",  # Emoticons
            r"[\U0001F300-\U0001F5FF]",  # Misc Symbols and Pictographs
            r"[\U0001F680-\U0001F6FF]",  # Transport and Map
            r"[\U0001F1E0-\U0001F1FF]",  # Regional indicator symbols
            r"[\U00002600-\U000026FF]",  # Miscellaneous symbols
            r"[\U00002700-\U000027BF]",  # Dingbats
        ]
    
    def analyze(self, text: str, session_id: str = "default") -> AbuseGuardResult:
        """
        Phân tích text để quyết định có nên đề xuất hay không
        
        Args:
            text: Input text cần phân tích
            session_id: Session ID để rate limiting
            
        Returns:
            AbuseGuardResult với quyết định và lý do
        """
        start_time = time.time()
        
        # Update stats
        self.stats["total_requests"] += 1
        
        # Check rate limiting first
        if not self._check_rate_limit(session_id):
            latency = (time.time() - start_time) * 1000
            self.stats["rate_limits_hit"] += 1
            self.stats["total_latency_ms"] += latency
            
            return AbuseGuardResult(
                should_suggest=False,
                confidence=0.0,
                abuse_score=1.0,
                reasoning="Rate limit exceeded",
                features={"rate_limited": True},
                latency_ms=latency
            )
        
        # Calculate abuse score
        abuse_score = self._calculate_abuse_score(text)
        
        # Calculate confidence
        confidence = 1.0 - abuse_score
        
        # Determine if should suggest
        # Block if abuse score is too high OR if vague score is significant
        vague_score = self._calculate_vague_score(text.lower())
        should_suggest = (confidence >= self.suggestion_threshold and 
                         abuse_score < self.abuse_threshold and 
                         vague_score < 0.2)  # Block if vague score >= 0.2
        
        # Generate reasoning
        reasoning = self._generate_reasoning(abuse_score, confidence, should_suggest)
        
        # Extract features
        features = self._extract_features(text, abuse_score)
        
        # Update stats
        if should_suggest:
            self.stats["suggestions_allowed"] += 1
            # Record suggestion timestamp
            self.session_suggestions[session_id].append(time.time())
        else:
            self.stats["suggestions_blocked"] += 1
        
        latency = (time.time() - start_time) * 1000
        self.stats["total_latency_ms"] += latency
        
        return AbuseGuardResult(
            should_suggest=should_suggest,
            confidence=confidence,
            abuse_score=abuse_score,
            reasoning=reasoning,
            features=features,
            latency_ms=latency
        )
    
    def _check_rate_limit(self, session_id: str) -> bool:
        """Check if session has exceeded rate limit"""
        current_time = time.time()
        
        # Clean old timestamps
        self.session_suggestions[session_id] = [
            ts for ts in self.session_suggestions[session_id]
            if current_time - ts < self.rate_limit_window
        ]
        
        # Check if under limit
        return len(self.session_suggestions[session_id]) < self.max_suggestions_per_window
    
    def _calculate_abuse_score(self, text: str) -> float:
        """Calculate abuse score (0-1, higher = more abusive)"""
        text_lower = text.lower()
        
        # 1. N-gram repetition score
        ngram_score = self._calculate_ngram_repetition_score(text_lower)
        
        # 2. Slang lexicon score
        slang_score = self._calculate_slang_score(text_lower)
        
        # 3. Entropy check
        entropy_score = self._calculate_entropy_score(text_lower)
        
        # 4. Stop-word density
        stopword_score = self._calculate_stopword_density(text_lower)
        
        # 5. Emoji spam score
        emoji_score = self._calculate_emoji_spam_score(text)
        
        # 6. Keyword stuffing score
        keyword_score = self._calculate_keyword_stuffing_score(text_lower)
        
        # 7. Vague content score
        vague_score = self._calculate_vague_score(text_lower)
        
        # Weighted combination
        weights = {
            "ngram": 0.15,
            "slang": 0.30,      # Increased from 0.25
            "entropy": 0.10,
            "stopword": 0.15,   # Decreased from 0.20
            "emoji": 0.20,
            "keyword": 0.10,
            "vague": 0.20       # New weight for vague detection
        }
        
        abuse_score = (
            ngram_score * weights["ngram"] +
            slang_score * weights["slang"] +
            entropy_score * weights["entropy"] +
            stopword_score * weights["stopword"] +
            emoji_score * weights["emoji"] +
            keyword_score * weights["keyword"] +
            vague_score * weights["vague"]
        )
        
        return min(1.0, abuse_score)
    
    def _calculate_ngram_repetition_score(self, text: str) -> float:
        """Calculate n-gram repetition score"""
        words = text.split()
        if len(words) < 3:
            return 0.0
        
        # Calculate bigram repetition
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        bigram_counts = Counter(bigrams)
        
        # Calculate trigram repetition
        trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words)-2)]
        trigram_counts = Counter(trigrams)
        
        # Calculate repetition ratio
        total_bigrams = len(bigrams)
        total_trigrams = len(trigrams)
        
        if total_bigrams == 0 and total_trigrams == 0:
            return 0.0
        
        bigram_repetition = sum(count - 1 for count in bigram_counts.values() if count > 1) / max(total_bigrams, 1)
        trigram_repetition = sum(count - 1 for count in trigram_counts.values() if count > 1) / max(total_trigrams, 1)
        
        return min(1.0, (bigram_repetition + trigram_repetition) / 2)
    
    def _calculate_slang_score(self, text: str) -> float:
        """Calculate slang lexicon score"""
        slang_matches = 0
        total_words = len(text.split())
        
        if total_words == 0:
            return 0.0
        
        for pattern in self.slang_patterns:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            slang_matches += matches
        
        return min(1.0, slang_matches / total_words)
    
    def _calculate_entropy_score(self, text: str) -> float:
        """Calculate entropy score (lower entropy = more repetitive)"""
        if not text:
            return 0.0
        
        # Calculate character entropy
        char_counts = Counter(text)
        total_chars = len(text)
        
        entropy = 0.0
        for count in char_counts.values():
            probability = count / total_chars
            if probability > 0:
                import math
                entropy -= probability * math.log2(probability)
        
        # Normalize entropy (0-1, lower = more repetitive)
        import math
        max_entropy = math.log2(len(char_counts)) if len(char_counts) > 0 else 0
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        return 1.0 - normalized_entropy
    
    def _calculate_stopword_density(self, text: str) -> float:
        """Calculate stop-word density score"""
        words = text.split()
        if not words:
            return 0.0
        
        stopword_count = sum(1 for word in words if word.lower() in self.stop_words)
        stopword_density = stopword_count / len(words)
        
        # High stopword density indicates low content quality
        # Boost penalty for very high stopword density
        if stopword_density > 0.8:
            return 1.0
        elif stopword_density > 0.6:
            return stopword_density * 3
        else:
            return min(1.0, stopword_density * 2)
    
    def _calculate_emoji_spam_score(self, text: str) -> float:
        """Calculate emoji spam score"""
        total_chars = len(text)
        if total_chars == 0:
            return 0.0
        
        emoji_count = 0
        for pattern in self.emoji_patterns:
            emoji_count += len(re.findall(pattern, text))
        
        emoji_ratio = emoji_count / total_chars
        return min(1.0, emoji_ratio * 20)  # Scale up emoji ratio more aggressively
    
    def _calculate_keyword_stuffing_score(self, text: str) -> float:
        """Calculate keyword stuffing score"""
        words = text.split()
        if not words:
            return 0.0
        
        word_counts = Counter(words)
        total_words = len(words)
        
        # Find words that appear too frequently
        stuffing_score = 0.0
        for word, count in word_counts.items():
            if count > 1:  # Word appears more than once
                frequency = count / total_words
                if frequency > 0.3:  # More than 30% of text (lowered threshold)
                    stuffing_score += frequency * 2  # Boost penalty
        
        return min(1.0, stuffing_score)
    
    def _calculate_vague_score(self, text: str) -> float:
        """Calculate vague content score"""
        vague_patterns = [
            r"\b(make|fix|improve|change|update)\s+(it|this|that)\s+(better|good|nice|great)\b",
            r"\b(help|assist|support)\s+(me|us|with)\s+(this|that|it)\b",
            r"\b(do|can\s+you)\s+(something|anything|this|that)\b",
            r"\b(what|how|why|when|where)\s+(should|can|do)\s+(i|we|you)\s+(do|make|fix)\b",
            r"\b(make|fix|improve|change|update)\s+(it|this|that)\b",  # "make it better", "change it"
            r"\b(help\s+me|fix\s+this|do\s+something|what\s+should\s+i\s+do)\b",
            # Additional vague patterns
            r"\b(make|fix|improve|change|update)\s+(something|anything)\b",  # "change something"
            r"\b(what|how|why|when|where)\s+(is|are|was|were)\s+(wrong|the\s+problem|the\s+issue)\s+(with|about)\s+(this|that|it)\b",  # "what's wrong with this"
            r"\b(what|how)\s+(do\s+you|should\s+i)\s+(think|feel)\s+(about|of)\s+(this|that|it)\b",  # "what do you think about this"
            # Borderline vague patterns
            r"\b(improve|optimize|enhance)\s+(system|user|performance|experience|efficiency)\b",  # "improve system performance"
            r"\b(make|fix|improve|optimize)\s+(it|this|that|something|everything)\s+(faster|better|good|great|nice|efficient)\b",  # "make it faster"
            # Edge case patterns
            r"^\s*$",  # Empty or whitespace only
            r"^\.+$",  # Only dots
            r"^[!?]+$",  # Only exclamation/question marks
        ]
        
        vague_matches = 0
        for pattern in vague_patterns:
            vague_matches += len(re.findall(pattern, text.lower()))
        
        return min(1.0, vague_matches / max(len(text.split()), 1))
    
    def _generate_reasoning(self, abuse_score: float, confidence: float, should_suggest: bool) -> str:
        """Generate human-readable reasoning"""
        if should_suggest:
            return f"Text quality is good (confidence: {confidence:.2f}, abuse score: {abuse_score:.2f})"
        else:
            if abuse_score >= 0.8:
                return f"High abuse score detected ({abuse_score:.2f}) - likely spam or low-quality content"
            elif abuse_score >= 0.6:
                return f"Moderate abuse score ({abuse_score:.2f}) - content needs improvement"
            else:
                return f"Low confidence ({confidence:.2f}) - need more context for better suggestions"
    
    def _extract_features(self, text: str, abuse_score: float) -> Dict[str, Any]:
        """Extract features for analysis"""
        text_lower = text.lower()
        
        return {
            "text_length": len(text),
            "word_count": len(text.split()),
            "ngram_repetition": self._calculate_ngram_repetition_score(text_lower),
            "slang_score": self._calculate_slang_score(text_lower),
            "entropy_score": self._calculate_entropy_score(text_lower),
            "stopword_density": self._calculate_stopword_density(text_lower),
            "emoji_count": sum(len(re.findall(pattern, text)) for pattern in self.emoji_patterns),
            "keyword_stuffing": self._calculate_keyword_stuffing_score(text_lower),
            "vague_score": self._calculate_vague_score(text_lower),
            "abuse_score": abuse_score
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total_requests = self.stats["total_requests"]
        avg_latency = (
            self.stats["total_latency_ms"] / total_requests 
            if total_requests > 0 else 0.0
        )
        
        return {
            "total_requests": total_requests,
            "suggestions_allowed": self.stats["suggestions_allowed"],
            "suggestions_blocked": self.stats["suggestions_blocked"],
            "rate_limits_hit": self.stats["rate_limits_hit"],
            "average_latency_ms": avg_latency,
            "suggestion_rate": (
                self.stats["suggestions_allowed"] / total_requests 
                if total_requests > 0 else 0.0
            )
        }
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.stats = {
            "total_requests": 0,
            "suggestions_allowed": 0,
            "suggestions_blocked": 0,
            "rate_limits_hit": 0,
            "total_latency_ms": 0.0
        }
        self.session_suggestions.clear()
