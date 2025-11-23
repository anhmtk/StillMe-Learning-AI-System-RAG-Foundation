"""
Source Consensus Validator - Detects contradictions between RAG context documents

This validator checks if retrieved context documents contradict each other on key facts
(dates, numbers, names, events). If contradictions are detected, it forces StillMe
to acknowledge uncertainty and report the contradiction transparently.

MVP Implementation:
- Only compares top-2 documents (to minimize cost)
- Only runs when ≥2 documents are available
- Timeout: 3s per comparison
- Only flags serious contradictions (dates, numbers, names)
"""

import logging
from typing import List, Optional, Dict, Any
from .base import ValidationResult
import os
import time

logger = logging.getLogger(__name__)


class SourceConsensusValidator:
    """
    Validator that detects contradictions between RAG context documents
    
    MVP Features:
    - Compares top-2 documents only
    - Detects contradictions in: dates, numbers, names, key facts
    - Forces uncertainty expression when contradictions found
    """
    
    def __init__(self, enabled: bool = True, timeout: float = 3.0):
        """
        Initialize source consensus validator
        
        Args:
            enabled: Whether validator is enabled (default: True)
            timeout: Timeout per comparison in seconds (default: 3.0)
        """
        self.enabled = enabled
        self.timeout = timeout
        logger.info(f"SourceConsensusValidator initialized (enabled={enabled}, timeout={timeout}s)")
    
    def _compare_documents(self, doc1: str, doc2: str, question: Optional[str] = None) -> Dict[str, Any]:
        """
        Compare two documents to detect contradictions
        
        Uses LLM to detect contradictions in:
        - Dates (e.g., "1954" vs "1955")
        - Numbers (e.g., "17th parallel" vs "16th parallel")
        - Names (e.g., "Keynes" vs "White")
        - Key facts (e.g., "Geneva Conference" vs "Paris Conference")
        
        Args:
            doc1: First document
            doc2: Second document
            question: Optional user question for context
            
        Returns:
            Dictionary with:
            - has_contradiction: bool
            - contradiction_type: str (e.g., "date", "number", "name", "fact")
            - details: str (description of contradiction)
            - confidence: float (0.0-1.0)
        """
        if not self.enabled:
            return {"has_contradiction": False, "confidence": 0.0}
        
        try:
            # Use LLM to detect contradictions
            # Try DeepSeek first, fallback to OpenAI
            api_key = os.getenv("DEEPSEEK_API_KEY")
            api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
            model = "deepseek-chat"
            
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
                api_base = "https://api.openai.com/v1"
                model = "gpt-3.5-turbo"
            
            if not api_key:
                logger.warning("No API key available for source consensus check, skipping")
                return {"has_contradiction": False, "confidence": 0.0}
            
            # Build comparison prompt
            comparison_prompt = f"""You are analyzing two documents to detect contradictions in key facts.

**User Question (for context):**
{question or "N/A"}

**Document 1:**
{doc1[:1000]}  # Truncate to save tokens

**Document 2:**
{doc2[:1000]}  # Truncate to save tokens

**Task:**
Compare these two documents and detect if they contradict each other on:
1. **Dates** (e.g., "1954" vs "1955", "July 20" vs "July 21")
2. **Numbers** (e.g., "17th parallel" vs "16th parallel", "35 USD" vs "40 USD")
3. **Names** (e.g., "Keynes" vs "White", "Ho Chi Minh" vs "Bao Dai")
4. **Key Facts** (e.g., "Geneva Conference" vs "Paris Conference", "IMF" vs "World Bank")

**Important:**
- Only flag SERIOUS contradictions (different dates, numbers, names, events)
- Do NOT flag different perspectives or interpretations (e.g., "Popper: falsification" vs "Kuhn: paradigm" is OK)
- Do NOT flag different wording for same fact (e.g., "Geneva 1954" vs "Geneva Conference 1954" is OK)

**Output Format (JSON):**
{{
    "has_contradiction": true/false,
    "contradiction_type": "date" | "number" | "name" | "fact" | "none",
    "details": "Brief description of contradiction",
    "confidence": 0.0-1.0
}}

**Examples:**
- Document 1: "Geneva Conference 1954" vs Document 2: "Geneva Conference 1955" → has_contradiction: true, type: "date"
- Document 1: "17th parallel" vs Document 2: "16th parallel" → has_contradiction: true, type: "number"
- Document 1: "Keynes" vs Document 2: "White" → has_contradiction: true, type: "name"
- Document 1: "Popper: falsification" vs Document 2: "Kuhn: paradigm" → has_contradiction: false (different perspectives, not contradiction)

Return ONLY valid JSON, no other text."""

            # Call LLM API using httpx (consistent with codebase)
            import httpx
            
            start_time = time.time()
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{api_base}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a fact-checking assistant. Analyze documents for contradictions and return JSON only."},
                            {"role": "user", "content": comparison_prompt}
                        ],
                        "temperature": 0.0,  # Deterministic
                        "max_tokens": 200
                    }
                )
                
                if response.status_code != 200:
                    logger.warning(f"LLM API error: {response.status_code} - {response.text[:200]}")
                    return {"has_contradiction": False, "confidence": 0.0}
                
                data = response.json()
                if "choices" not in data or len(data["choices"]) == 0:
                    logger.warning("LLM API returned unexpected response format")
                    return {"has_contradiction": False, "confidence": 0.0}
                
                result_text = data["choices"][0]["message"]["content"].strip()
            
            elapsed = time.time() - start_time
            
            # Parse JSON response
            import json
            try:
                # Remove markdown code blocks if present
                if result_text.startswith("```"):
                    result_text = result_text.split("```")[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]
                result_text = result_text.strip()
                
                result = json.loads(result_text)
                
                logger.debug(f"Source consensus check completed in {elapsed:.2f}s: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response as JSON: {result_text[:200]}, error: {e}")
                return {"has_contradiction": False, "confidence": 0.0}
        
        except Exception as e:
            logger.warning(f"Source consensus check failed: {e}, continuing without check")
            return {"has_contradiction": False, "confidence": 0.0}
    
    def run(self, answer: str, ctx_docs: List[str], user_question: Optional[str] = None) -> ValidationResult:
        """
        Check for contradictions between context documents
        
        MVP: Only compares top-2 documents
        
        Args:
            answer: The answer to validate (not used in MVP, but kept for interface consistency)
            ctx_docs: List of context documents from RAG
            user_question: Optional user question for context
            
        Returns:
            ValidationResult with contradiction status
        """
        if not self.enabled:
            return ValidationResult(passed=True)
        
        # MVP: Only check if we have ≥2 documents
        if len(ctx_docs) < 2:
            logger.debug("SourceConsensusValidator: <2 documents, skipping check")
            return ValidationResult(passed=True)
        
        # MVP: Only compare top-2 documents (to minimize cost)
        doc1 = ctx_docs[0]
        doc2 = ctx_docs[1]
        
        logger.debug(f"SourceConsensusValidator: Comparing top-2 documents (total: {len(ctx_docs)})")
        
        # Compare documents
        comparison_result = self._compare_documents(doc1, doc2, user_question)
        
        if comparison_result.get("has_contradiction", False):
            contradiction_type = comparison_result.get("contradiction_type", "unknown")
            details = comparison_result.get("details", "Contradiction detected between sources")
            confidence = comparison_result.get("confidence", 0.5)
            
            # Only flag if confidence is high enough (≥0.7)
            if confidence >= 0.7:
                logger.warning(
                    f"🔍 Source contradiction detected: type={contradiction_type}, "
                    f"confidence={confidence:.2f}, details={details[:100]}"
                )
                
                return ValidationResult(
                    passed=False,
                    reasons=[f"source_contradiction:{contradiction_type}:{details[:200]}"],
                    patched_answer=None  # Don't patch, let ConfidenceValidator handle uncertainty
                )
            else:
                logger.debug(f"Source contradiction detected but confidence too low ({confidence:.2f}), ignoring")
                return ValidationResult(passed=True)
        else:
            logger.debug("SourceConsensusValidator: No contradictions detected")
            return ValidationResult(passed=True)

