"""
ReviewAdapter - Simulated Peer Review for Learning Proposals
Inspired by AlphaResearch's dual environment approach

Uses DeepSeek API + Prompt Engineering instead of training a reward model
to evaluate learning proposals with academic review standards.
"""

import os
import re
import hashlib
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Review threshold
REVIEW_THRESHOLD = 5.0  # Minimum score to accept (0-10 scale)

# Cache for review results (in-memory, can be upgraded to Redis later)
_review_cache: Dict[str, Dict[str, Any]] = {}


class ReviewAdapter:
    """
    Adapter that evaluates learning proposals using simulated peer review
    
    Uses DeepSeek API with structured prompt to evaluate proposals based on:
    - Novelty
    - Feasibility
    - Relevance
    - Clarity
    - Evidence Base
    """
    
    def __init__(self, api_key: Optional[str] = None, enable_cache: bool = True):
        """
        Initialize Review Adapter
        
        Args:
            api_key: DeepSeek API key (if None, uses DEEPSEEK_API_KEY env var)
            enable_cache: Enable caching of review results
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.enable_cache = enable_cache
        self.review_count = 0
        self.cache_hits = 0
        
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY not found - ReviewAdapter will be disabled")
        
        logger.info(f"ReviewAdapter initialized (cache={'enabled' if enable_cache else 'disabled'})")
    
    def evaluate_proposal(
        self, 
        proposal: str, 
        proposal_type: str = "learning_content",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a learning proposal using simulated peer review
        
        Args:
            proposal: The proposal text to evaluate (title, summary, or full content)
            proposal_type: Type of proposal ("learning_content", "learning_source", "user_proposal")
            context: Optional context (source, metadata, etc.)
            
        Returns:
            Dict with:
                - score: float (0-10)
                - passed: bool (score >= threshold)
                - reasons: List[str] (explanation of score)
                - cached: bool (whether result was from cache)
        """
        if not self.api_key:
            # If no API key, return neutral score (don't block)
            logger.warning("ReviewAdapter: No API key, returning neutral score")
            return {
                "score": 5.0,
                "passed": True,
                "reasons": ["review_disabled_no_api_key"],
                "cached": False
            }
        
        # Check cache
        cache_key = self._get_cache_key(proposal, proposal_type)
        if self.enable_cache and cache_key in _review_cache:
            self.cache_hits += 1
            cached_result = _review_cache[cache_key].copy()
            cached_result["cached"] = True
            logger.debug(f"ReviewAdapter: Cache hit for proposal")
            return cached_result
        
        # Call DeepSeek API for evaluation
        try:
            self.review_count += 1
            score, reasons = self._call_review_api(proposal, proposal_type, context)
            
            result = {
                "score": score,
                "passed": score >= REVIEW_THRESHOLD,
                "reasons": reasons,
                "cached": False,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache result
            if self.enable_cache:
                _review_cache[cache_key] = result.copy()
                # Limit cache size (keep last 1000 entries)
                if len(_review_cache) > 1000:
                    # Remove oldest entries (simple FIFO)
                    oldest_key = next(iter(_review_cache))
                    del _review_cache[oldest_key]
            
            logger.info(
                f"ReviewAdapter: Evaluated proposal (score={score:.1f}, "
                f"passed={result['passed']}, type={proposal_type})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"ReviewAdapter: Error evaluating proposal: {e}")
            # On error, return neutral score (don't block)
            return {
                "score": 5.0,
                "passed": True,
                "reasons": [f"review_error:{str(e)}"],
                "cached": False
            }
    
    def _call_review_api(
        self, 
        proposal: str, 
        proposal_type: str,
        context: Optional[Dict[str, Any]]
    ) -> Tuple[float, list]:
        """
        Call DeepSeek API to evaluate proposal
        
        Returns:
            Tuple of (score, reasons)
        """
        # Build review prompt
        prompt = self._build_review_prompt(proposal, proposal_type, context)
        
        # Call DeepSeek API (using sync HTTP client for simplicity)
        try:
            import httpx
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {
                                "role": "system",
                                "content": self._get_system_prompt()
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 500,
                        "temperature": 0.3  # Lower temperature for more consistent scoring
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        response_text = data["choices"][0]["message"]["content"]
                    else:
                        raise Exception("Unexpected response format")
                else:
                    raise Exception(f"API error: {response.status_code}")
            
            # Parse response
            score, reasons = self._parse_review_response(response_text)
            return score, reasons
            
        except Exception as e:
            logger.error(f"ReviewAdapter: API call error: {e}")
            # Return neutral score on error
            return 5.0, [f"api_error:{str(e)}"]
    
    def _build_review_prompt(
        self, 
        proposal: str, 
        proposal_type: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the review prompt for DeepSeek API"""
        
        context_info = ""
        if context:
            source = context.get("source", "")
            if source:
                context_info = f"\nSource: {source}"
        
        prompt = f"""Evaluate this learning proposal for StillMe (a transparent AI learning system):

PROPOSAL:
{proposal}
{context_info}

PROPOSAL TYPE: {proposal_type}

EVALUATION CRITERIA:
1. Novelty (0-10): Is this new knowledge or a new perspective?
2. Feasibility (0-10): Can StillMe learn this from available sources?
3. Relevance (0-10): Is this relevant to AI, transparency, ethics, or StillMe's mission?
4. Clarity (0-10): Is the proposal clear and well-structured?
5. Evidence Base (0-10): Is this supported by credible sources?

Please provide:
1. A score from 0.0 to 10.0 (weighted average of the 5 criteria)
2. Brief reasons for the score (2-3 sentences)

Format your response as JSON:
{{
    "score": <float 0.0-10.0>,
    "reasons": ["reason1", "reason2", "reason3"]
}}

Be strict but fair. Reject proposals that are:
- Not relevant to AI/tech/StillMe's mission
- Too vague or unclear
- Not feasible for StillMe to learn
- Lacking evidence or credibility
"""
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for reviewer persona"""
        return """You are an academic reviewer evaluating learning proposals for StillMe, a transparent AI learning system.

StillMe's mission:
- AI transparency and ethics
- Open source AI development
- Community governance
- Continuous learning from trusted sources (arXiv, Wikipedia, RSS feeds)

Your role:
- Evaluate proposals based on academic review standards
- Be strict but fair
- Prioritize relevance to AI, transparency, and ethics
- Consider feasibility for StillMe's RAG-based learning system

Provide objective, constructive evaluations."""
    
    def _parse_review_response(self, response_text: str) -> Tuple[float, list]:
        """
        Parse DeepSeek API response to extract score and reasons
        
        Returns:
            Tuple of (score, reasons)
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                score = float(data.get("score", 5.0))
                reasons = data.get("reasons", ["No reasons provided"])
                
                # Validate score range
                score = max(0.0, min(10.0, score))
                
                return score, reasons
            else:
                # Fallback: Try to extract score from text (multiple patterns)
                patterns = [
                    r'score["\']?\s*[:=]\s*([0-9.]+)',
                    r'score\s+is\s+([0-9.]+)',
                    r'score\s+of\s+([0-9.]+)',
                    r'([0-9.]+)\s+out\s+of\s+10',
                    r'([0-9.]+)/10',
                    r'rating["\']?\s*[:=]\s*([0-9.]+)'
                ]
                
                for pattern in patterns:
                    score_match = re.search(pattern, response_text, re.IGNORECASE)
                    if score_match:
                        try:
                            score = float(score_match.group(1))
                            score = max(0.0, min(10.0, score))
                            reasons = ["Score extracted from text response"]
                            return score, reasons
                        except ValueError:
                            continue
                
                # Last resort: neutral score
                logger.warning("ReviewAdapter: Could not parse response, using neutral score")
                return 5.0, ["Could not parse review response"]
                    
        except Exception as e:
            logger.error(f"ReviewAdapter: Error parsing response: {e}")
            return 5.0, [f"parse_error:{str(e)}"]
    
    def _get_cache_key(self, proposal: str, proposal_type: str) -> str:
        """Generate cache key for proposal"""
        # Use hash of proposal text + type for cache key
        key_string = f"{proposal_type}:{proposal}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about review adapter usage"""
        return {
            "reviews_performed": self.review_count,
            "cache_hits": self.cache_hits,
            "cache_size": len(_review_cache),
            "cache_hit_rate": (self.cache_hits / self.review_count * 100) if self.review_count > 0 else 0.0,
            "threshold": REVIEW_THRESHOLD
        }
    
    def clear_cache(self):
        """Clear the review cache"""
        _review_cache.clear()
        logger.info("ReviewAdapter: Cache cleared")

