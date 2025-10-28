"""
Ethical Content Safety Filter for StillMe V2
Comprehensive ethical filtering system for input and output content
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, List

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Safety assessment levels"""
    SAFE = "safe"
    WARNING = "warning"
    UNSAFE = "unsafe"


class EthicalPrinciple(Enum):
    """Ethical principles for content evaluation"""
    BENEFICENCE = "beneficence"
    NON_MALEFICENCE = "non_maleficence"
    AUTONOMY = "autonomy"
    JUSTICE = "justice"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"


class ViolationSeverity(Enum):
    """Severity levels for ethical violations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyResult:
    """Result of safety check"""
    is_safe: bool
    level: SafetyLevel
    reason: str
    confidence: float
    details: dict[str, Any]
    ethical_violations: List['EthicalViolation'] = None

    def __post_init__(self):
        if self.ethical_violations is None:
            self.ethical_violations = []


@dataclass
class EthicalViolation:
    """Ethical violation record"""
    violation_id: str
    principle: EthicalPrinciple
    severity: ViolationSeverity
    description: str
    context: str
    timestamp: datetime
    suggested_action: str
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EthicalContentSafetyFilter:
    """
    Comprehensive Ethical Content Safety Filter for StillMe V2
    Ensures safe, ethical, and appropriate content for learning
    """

    def __init__(self, ethics_level: str = "medium"):
        self.ethics_level = ethics_level
        self.blacklist_keywords = self._load_blacklist_keywords()
        self.unreliable_sources = self._load_unreliable_sources()
        self.min_content_length = 50
        self.toxicity_threshold = 0.8
        self.violations: List[EthicalViolation] = []
        self.principles = list(EthicalPrinciple)
        
        logger.info(f"✅ Ethical Content Safety Filter initialized with level: {self.ethics_level}")

    def _load_blacklist_keywords(self) -> List[str]:
        """Load comprehensive blacklist keywords for content filtering"""
        return [
            # Harmful content
            "fake news", "conspiracy", "misinformation", "disinformation",
            "hate speech", "discrimination", "racism", "sexism", "homophobia",
            "violence", "threat", "attack", "harm", "danger",
            "explicit content", "pornography", "adult content",
            "scam", "fraud", "malware", "virus", "hack tutorial",
            "weapon", "terrorist", "extremist", "bomb", "explosive",
            
            # Illegal activities
            "illegal", "criminal", "theft", "robbery", "murder",
            "drug trafficking", "human trafficking", "child abuse",
            
            # Spam and deceptive content
            "clickbait", "spam", "phishing", "pyramid scheme",
            "get rich quick", "miracle cure", "guaranteed profit",
            
            # Sensitive topics (configurable based on ethics level)
            "suicide", "self-harm", "eating disorder", "mental illness",
        ]

    def _load_unreliable_sources(self) -> List[str]:
        """Load list of unreliable source domains"""
        return [
            "fake-news", "conspiracy", "hoax", "scam", "clickbait",
            "satire", "parody", "unreliable", "questionable",
        ]

    def check_content_safety(
        self, content: str, source_url: str = None, context: str = ""
    ) -> SafetyResult:
        """
        Comprehensive safety check for content
        
        Args:
            content: Content to check
            source_url: Source URL (optional)
            context: Context information (optional)
            
        Returns:
            SafetyResult with detailed assessment
        """
        details = {}
        ethical_violations = []

        # Basic content validation
        if not content or len(content.strip()) < self.min_content_length:
            return SafetyResult(
                is_safe=False,
                level=SafetyLevel.UNSAFE,
                reason="Content too short or empty",
                confidence=1.0,
                details={"length": len(content) if content else 0},
                ethical_violations=[]
            )

        # Pre-filter using keyword matching
        pre_filter_result = self._pre_filter_content(content, source_url)
        if not pre_filter_result["is_safe"]:
            violation = EthicalViolation(
                violation_id=f"violation_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                principle=EthicalPrinciple.NON_MALEFICENCE,
                severity=ViolationSeverity.HIGH,
                description=f"Content contains harmful keywords: {pre_filter_result.get('matched_keyword', 'unknown')}",
                context=context,
                timestamp=datetime.now(),
                suggested_action="Remove or sanitize harmful content",
                metadata={"matched_keyword": pre_filter_result.get('matched_keyword')}
            )
            ethical_violations.append(violation)
            
            return SafetyResult(
                is_safe=False,
                level=SafetyLevel.UNSAFE,
                reason=pre_filter_result["reason"],
                confidence=pre_filter_result["confidence"],
                details=pre_filter_result,
                ethical_violations=ethical_violations
            )

        # Ethical compliance check
        ethical_violations = self._check_ethical_compliance(content, context)
        details["ethical_check"] = {
            "violations_count": len(ethical_violations),
            "principles_violated": [v.principle.value for v in ethical_violations]
        }

        # Quality and toxicity check
        quality_check = self._check_content_quality(content)
        details["quality_check"] = quality_check

        if quality_check["toxicity_score"] > self.toxicity_threshold:
            violation = EthicalViolation(
                violation_id=f"violation_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                principle=EthicalPrinciple.NON_MALEFICENCE,
                severity=ViolationSeverity.MEDIUM,
                description="High toxicity detected in content",
                context=context,
                timestamp=datetime.now(),
                suggested_action="Review content for toxicity and bias",
                metadata={"toxicity_score": quality_check["toxicity_score"]}
            )
            ethical_violations.append(violation)

        # Determine final safety level
        if ethical_violations:
            # Check severity of violations
            high_severity_violations = [v for v in ethical_violations if v.severity in [ViolationSeverity.HIGH, ViolationSeverity.CRITICAL]]
            
            if high_severity_violations:
                safety_level = SafetyLevel.UNSAFE
                reason = f"High severity ethical violations detected: {len(high_severity_violations)}"
                confidence = 0.9
            else:
                safety_level = SafetyLevel.WARNING
                reason = f"Ethical violations detected: {len(ethical_violations)}"
                confidence = 0.7
        else:
            safety_level = SafetyLevel.SAFE
            reason = "Content passed all safety and ethical checks"
            confidence = 0.9

        # Record violations
        for violation in ethical_violations:
            self.violations.append(violation)
            logger.warning(f"⚠️ Ethical violation detected: {violation.principle.value} - {violation.description}")

        return SafetyResult(
            is_safe=safety_level != SafetyLevel.UNSAFE,
            level=safety_level,
            reason=reason,
            confidence=confidence,
            details=details,
            ethical_violations=ethical_violations
        )

    def _pre_filter_content(self, content: str, source_url: str = None) -> dict[str, Any]:
        """Fast pre-filtering using keyword matching"""
        content_lower = content.lower()

        for keyword in self.blacklist_keywords:
            if keyword.lower() in content_lower:
                return {
                    "is_safe": False,
                    "reason": f"Blacklisted keyword detected: {keyword}",
                    "confidence": 1.0,
                    "matched_keyword": keyword,
                }

        if source_url:
            source_url_lower = source_url.lower()
            for unreliable in self.unreliable_sources:
                if unreliable in source_url_lower:
                    return {
                        "is_safe": False,
                        "reason": f"Unreliable source detected: {unreliable}",
                        "confidence": 0.9,
                        "matched_source": unreliable,
                    }

        return {
            "is_safe": True,
            "reason": "Pre-filter passed",
            "confidence": 0.8,
        }

    def _check_ethical_compliance(self, content: str, context: str = "") -> List[EthicalViolation]:
        """Check ethical compliance of content"""
        violations = []

        # Check for harmful content
        if self._contains_harmful_content(content):
            violation = EthicalViolation(
                violation_id=f"violation_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                principle=EthicalPrinciple.NON_MALEFICENCE,
                severity=ViolationSeverity.HIGH,
                description="Content contains potentially harmful material",
                context=context,
                timestamp=datetime.now(),
                suggested_action="Review and sanitize content",
                metadata={}
            )
            violations.append(violation)

        # Check for bias
        if self._contains_bias(content):
            violation = EthicalViolation(
                violation_id=f"violation_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                principle=EthicalPrinciple.JUSTICE,
                severity=ViolationSeverity.MEDIUM,
                description="Content may contain biased language",
                context=context,
                timestamp=datetime.now(),
                suggested_action="Review for bias and use inclusive language",
                metadata={}
            )
            violations.append(violation)

        # Check for privacy violations
        if self._contains_pii(content):
            violation = EthicalViolation(
                violation_id=f"violation_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                principle=EthicalPrinciple.AUTONOMY,
                severity=ViolationSeverity.HIGH,
                description="Content contains personally identifiable information",
                context=context,
                timestamp=datetime.now(),
                suggested_action="Remove or anonymize PII",
                metadata={}
            )
            violations.append(violation)

        return violations

    def _contains_harmful_content(self, content: str) -> bool:
        """Check if content contains harmful material"""
        harmful_keywords = [
            "violence", "harm", "danger", "threat", "attack",
            "illegal", "criminal", "fraud", "scam", "deception",
            "suicide", "self-harm", "murder", "kill", "death"
        ]

        content_lower = content.lower()
        return any(keyword in content_lower for keyword in harmful_keywords)

    def _contains_bias(self, content: str) -> bool:
        """Check if content contains biased language"""
        bias_keywords = [
            "always", "never", "all", "none", "everyone", "nobody",
            "typical", "normal", "abnormal", "weird", "strange",
            "obviously", "clearly", "undoubtedly", "certainly"
        ]

        content_lower = content.lower()
        return any(keyword in content_lower for keyword in bias_keywords)

    def _contains_pii(self, content: str) -> bool:
        """Check if content contains personally identifiable information"""
        # Email pattern
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        if re.search(email_pattern, content):
            return True

        # Phone pattern
        phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
        if re.search(phone_pattern, content):
            return True

        # SSN pattern
        ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
        if re.search(ssn_pattern, content):
            return True

        return False

    def _check_content_quality(self, content: str) -> dict[str, Any]:
        """Check content quality using heuristics"""
        content_lower = content.lower()

        sensitive_topics = [
            "politics", "religion", "adult", "gambling", "drugs",
            "medical advice", "financial advice", "legal advice"
        ]

        has_sensitive = any(topic in content_lower for topic in sensitive_topics)

        uppercase_ratio = sum(1 for c in content if c.isupper()) / len(content) if content else 0
        exclamation_count = content.count("!")
        question_count = content.count("?")

        toxicity_score = 0.0
        if uppercase_ratio > 0.3:
            toxicity_score += 0.2
        if exclamation_count > 5:
            toxicity_score += 0.1
        if question_count > 5:
            toxicity_score += 0.05

        spam_patterns = [
            r"click here", r"buy now", r"limited time", r"act now",
            r"free money", r"guaranteed", r"no risk", r"instant"
        ]

        is_spam = any(re.search(pattern, content_lower) for pattern in spam_patterns)
        if is_spam:
            toxicity_score += 0.3

        return {
            "toxicity_score": min(1.0, toxicity_score),
            "has_sensitive_topics": has_sensitive,
            "uppercase_ratio": uppercase_ratio,
            "exclamation_count": exclamation_count,
            "is_spam": is_spam,
        }

    def batch_check_content(self, contents: List[dict[str, Any]]) -> List[SafetyResult]:
        """Batch check multiple content items"""
        results = []

        for item in contents:
            content = item.get("content", "")
            source_url = item.get("source_url")
            context = item.get("context", "")

            result = self.check_content_safety(content, source_url, context)
            results.append(result)

        safe_count = sum(1 for r in results if r.is_safe)
        logger.info(f"🔍 Batch ethical safety check: {safe_count}/{len(results)} passed")

        return results

    def get_safety_stats(self) -> dict[str, Any]:
        """Get comprehensive safety filter statistics"""
        violations_by_principle = {}
        violations_by_severity = {}

        for violation in self.violations:
            principle_key = violation.principle.value
            violations_by_principle[principle_key] = violations_by_principle.get(principle_key, 0) + 1

            severity_key = violation.severity.value
            violations_by_severity[severity_key] = violations_by_severity.get(severity_key, 0) + 1

        return {
            "ethics_level": self.ethics_level,
            "blacklist_keywords_count": len(self.blacklist_keywords),
            "unreliable_sources_count": len(self.unreliable_sources),
            "min_content_length": self.min_content_length,
            "toxicity_threshold": self.toxicity_threshold,
            "total_violations": len(self.violations),
            "violations_by_principle": violations_by_principle,
            "violations_by_severity": violations_by_severity,
            "principles_monitored": [p.value for p in self.principles]
        }

    def get_ethical_summary(self) -> dict[str, Any]:
        """Get ethical compliance summary"""
        return {
            "total_violations": len(self.violations),
            "violations_by_principle": {
                principle.value: len([v for v in self.violations if v.principle == principle])
                for principle in EthicalPrinciple
            },
            "violations_by_severity": {
                severity.value: len([v for v in self.violations if v.severity == severity])
                for severity in ViolationSeverity
            },
            "timestamp": datetime.now().isoformat(),
        }

    def add_blacklist_keyword(self, keyword: str):
        """Add keyword to blacklist"""
        if keyword and keyword not in self.blacklist_keywords:
            self.blacklist_keywords.append(keyword)
            logger.info(f"➕ Added blacklist keyword: {keyword}")

    def add_unreliable_source(self, source: str):
        """Add source to unreliable list"""
        if source and source not in self.unreliable_sources:
            self.unreliable_sources.append(source)
            logger.info(f"➕ Added unreliable source: {source}")

    def remove_blacklist_keyword(self, keyword: str):
        """Remove keyword from blacklist"""
        if keyword in self.blacklist_keywords:
            self.blacklist_keywords.remove(keyword)
            logger.info(f"➖ Removed blacklist keyword: {keyword}")

    def is_url_safe(self, url: str) -> bool:
        """Quick check if URL is from safe source"""
        url_lower = url.lower()

        for unreliable in self.unreliable_sources:
            if unreliable in url_lower:
                return False

        safe_patterns = [
            "github.com", "wikipedia.org", "arxiv.org", "medium.com",
            "stackoverflow.com", "mozilla.org", "w3.org", "ietf.org"
        ]

        for pattern in safe_patterns:
            if pattern in url_lower:
                return True

        return True

    def clear_violations(self):
        """Clear all violations"""
        self.violations.clear()
        logger.info("🧹 All ethical violations cleared")


# Global instance
ethical_safety_filter = EthicalContentSafetyFilter()

