"""
StillMe Risk Injection Scanner
Detects prompt injection and other security risks in content.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import yaml

from stillme_core.learning.parser.normalize import NormalizedContent

log = logging.getLogger(__name__)

@dataclass
class RiskAssessment:
    """Risk assessment result."""
    risk_score: float  # 0.0 to 1.0
    risk_level: str    # "low", "medium", "high", "critical"
    detected_patterns: List[str]
    risk_details: List[Dict]
    safe: bool
    confidence: float

class InjectionScanner:
    """Scans content for prompt injection and security risks."""
    
    def __init__(self, policy_file: str = "policies/learning_policy.yaml"):
        self.policy_file = Path(policy_file)
        self.policy = self._load_policy()
        self.injection_patterns = self._load_injection_patterns()
        self.high_risk_keywords = self._load_high_risk_keywords()
        self.pii_patterns = self._load_pii_patterns()
        
        log.info(f"Injection scanner initialized with {len(self.injection_patterns)} patterns")
    
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
            'risk_assessment': {
                'injection_patterns': [
                    'ignore previous instructions',
                    'system prompt',
                    'jailbreak',
                    'roleplay as',
                    'pretend to be',
                    'act as if'
                ],
                'high_risk_keywords': [
                    'hack', 'exploit', 'vulnerability', 'bypass', 'circumvent', 'unauthorized'
                ],
                'pii_patterns': [
                    'email', 'phone', 'address', 'ssn', 'credit card'
                ]
            }
        }
    
    def _load_injection_patterns(self) -> List[str]:
        """Load prompt injection patterns."""
        patterns = self.policy.get('risk_assessment', {}).get('injection_patterns', [])
        
        # Add additional common injection patterns
        additional_patterns = [
            r'ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?',
            r'system\s+prompt',
            r'jailbreak',
            r'roleplay\s+as',
            r'pretend\s+to\s+be',
            r'act\s+as\s+if',
            r'forget\s+(?:everything|all)',
            r'new\s+instructions?',
            r'override\s+(?:previous|prior)',
            r'disregard\s+(?:previous|prior)',
            r'you\s+are\s+now',
            r'from\s+now\s+on',
            r'change\s+(?:your\s+)?role',
            r'stop\s+being',
            r'become\s+(?:a\s+)?different',
            r'simulate\s+(?:being|a)',
            r'impersonate',
            r'pose\s+as',
            r'act\s+like',
            r'behave\s+as',
        ]
        
        return patterns + additional_patterns
    
    def _load_high_risk_keywords(self) -> List[str]:
        """Load high-risk keywords."""
        keywords = self.policy.get('risk_assessment', {}).get('high_risk_keywords', [])
        
        # Add additional high-risk keywords
        additional_keywords = [
            'hack', 'exploit', 'vulnerability', 'bypass', 'circumvent', 'unauthorized',
            'malware', 'virus', 'trojan', 'backdoor', 'rootkit',
            'phishing', 'scam', 'fraud', 'identity theft',
            'ddos', 'dos attack', 'brute force', 'sql injection',
            'xss', 'csrf', 'buffer overflow', 'privilege escalation',
            'social engineering', 'manipulation', 'deception',
            'illegal', 'criminal', 'terrorist', 'weapon',
            'drug', 'violence', 'harm', 'dangerous'
        ]
        
        return keywords + additional_keywords
    
    def _load_pii_patterns(self) -> List[str]:
        """Load PII detection patterns."""
        patterns = self.policy.get('risk_assessment', {}).get('pii_patterns', [])
        
        # Add regex patterns for PII
        additional_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-?\d{2}-?\d{4}\b',  # SSN
            r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',  # Phone
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',  # Credit card
            r'\b\d{1,5}\s+\w+\s+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|way|blvd|boulevard)\b',  # Address
        ]
        
        return patterns + additional_patterns
    
    def scan_injection_patterns(self, text: str) -> List[Dict]:
        """Scan for prompt injection patterns."""
        detected = []
        text_lower = text.lower()
        
        for pattern in self.injection_patterns:
            try:
                # Compile pattern as regex if it contains regex syntax
                if any(char in pattern for char in ['(', ')', '[', ']', '{', '}', '|', '*', '+', '?', '^', '$']):
                    matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                else:
                    # Simple string search
                    if pattern.lower() in text_lower:
                        matches = [re.Match()]
                    else:
                        matches = []
                
                for match in matches:
                    detected.append({
                        'type': 'injection_pattern',
                        'pattern': pattern,
                        'severity': 'high',
                        'confidence': 0.9,
                        'description': f'Potential prompt injection: "{pattern}"'
                    })
            except re.error:
                # Fallback to simple string search
                if pattern.lower() in text_lower:
                    detected.append({
                        'type': 'injection_pattern',
                        'pattern': pattern,
                        'severity': 'high',
                        'confidence': 0.8,
                        'description': f'Potential prompt injection: "{pattern}"'
                    })
        
        return detected
    
    def scan_high_risk_keywords(self, text: str) -> List[Dict]:
        """Scan for high-risk keywords."""
        detected = []
        text_lower = text.lower()
        
        for keyword in self.high_risk_keywords:
            if keyword.lower() in text_lower:
                # Count occurrences
                count = text_lower.count(keyword.lower())
                severity = 'medium' if count == 1 else 'high' if count <= 3 else 'critical'
                
                detected.append({
                    'type': 'high_risk_keyword',
                    'keyword': keyword,
                    'count': count,
                    'severity': severity,
                    'confidence': 0.7,
                    'description': f'High-risk keyword detected: "{keyword}" ({count} times)'
                })
        
        return detected
    
    def scan_pii_patterns(self, text: str) -> List[Dict]:
        """Scan for PII patterns."""
        detected = []
        
        for pattern in self.pii_patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Mask the actual PII in the description
                    masked_text = match.group()[:3] + '*' * (len(match.group()) - 3)
                    
                    detected.append({
                        'type': 'pii_pattern',
                        'pattern': pattern,
                        'severity': 'medium',
                        'confidence': 0.8,
                        'description': f'Potential PII detected: {masked_text}'
                    })
            except re.error:
                # Fallback to simple string search
                if pattern.lower() in text.lower():
                    detected.append({
                        'type': 'pii_pattern',
                        'pattern': pattern,
                        'severity': 'medium',
                        'confidence': 0.6,
                        'description': f'Potential PII pattern: "{pattern}"'
                    })
        
        return detected
    
    def assess_content_risk(self, content: NormalizedContent) -> RiskAssessment:
        """Assess risk for a content item."""
        all_detections = []
        
        # Combine all text for analysis
        full_text = f"{content.title} {content.content} {content.summary}"
        
        # Scan for different types of risks
        injection_detections = self.scan_injection_patterns(full_text)
        risk_keyword_detections = self.scan_high_risk_keywords(full_text)
        pii_detections = self.scan_pii_patterns(full_text)
        
        all_detections.extend(injection_detections)
        all_detections.extend(risk_keyword_detections)
        all_detections.extend(pii_detections)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(all_detections)
        risk_level = self._determine_risk_level(risk_score, all_detections)
        
        # Extract detected patterns
        detected_patterns = list(set(det['pattern'] if 'pattern' in det else det.get('keyword', '') for det in all_detections))
        
        # Determine if content is safe
        safe = risk_level in ['low', 'medium'] and risk_score < 0.5
        
        return RiskAssessment(
            risk_score=risk_score,
            risk_level=risk_level,
            detected_patterns=detected_patterns,
            risk_details=all_detections,
            safe=safe,
            confidence=0.8
        )
    
    def _calculate_risk_score(self, detections: List[Dict]) -> float:
        """Calculate overall risk score."""
        if not detections:
            return 0.0
        
        # Weight different types of detections
        weights = {
            'injection_pattern': 0.5,
            'high_risk_keyword': 0.3,
            'pii_pattern': 0.2
        }
        
        # Weight by severity
        severity_weights = {
            'low': 0.1,
            'medium': 0.3,
            'high': 0.6,
            'critical': 1.0
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for detection in detections:
            detection_type = detection.get('type', 'unknown')
            severity = detection.get('severity', 'medium')
            confidence = detection.get('confidence', 0.5)
            
            type_weight = weights.get(detection_type, 0.1)
            severity_weight = severity_weights.get(severity, 0.3)
            
            score = type_weight * severity_weight * confidence
            total_score += score
            total_weight += type_weight
        
        return min(total_score / total_weight if total_weight > 0 else 0.0, 1.0)
    
    def _determine_risk_level(self, risk_score: float, detections: List[Dict]) -> str:
        """Determine risk level based on score and detections."""
        # Check for critical detections
        critical_detections = [d for d in detections if d.get('severity') == 'critical']
        if critical_detections:
            return 'critical'
        
        # Check for high-severity detections
        high_detections = [d for d in detections if d.get('severity') == 'high']
        if len(high_detections) >= 3 or risk_score >= 0.8:
            return 'high'
        
        # Check for medium-severity detections
        medium_detections = [d for d in detections if d.get('severity') == 'medium']
        if len(medium_detections) >= 2 or risk_score >= 0.5:
            return 'medium'
        
        return 'low'
    
    def scan_batch(self, contents: List[NormalizedContent]) -> List[RiskAssessment]:
        """Scan a batch of content items."""
        assessments = []
        
        for content in contents:
            try:
                assessment = self.assess_content_risk(content)
                assessments.append(assessment)
            except Exception as e:
                log.error(f"Risk assessment failed for content: {e}")
                # Create a high-risk assessment for failed scans
                assessments.append(RiskAssessment(
                    risk_score=1.0,
                    risk_level='critical',
                    detected_patterns=['scan_error'],
                    risk_details=[{
                        'type': 'scan_error',
                        'severity': 'critical',
                        'confidence': 1.0,
                        'description': f'Risk scan failed: {str(e)}'
                    }],
                    safe=False,
                    confidence=1.0
                ))
        
        # Log statistics
        safe_count = sum(1 for a in assessments if a.safe)
        high_risk_count = sum(1 for a in assessments if a.risk_level in ['high', 'critical'])
        
        log.info(f"Risk scan: {safe_count}/{len(assessments)} items safe, {high_risk_count} high-risk")
        
        return assessments

def assess_content_risk(content: NormalizedContent, 
                       policy_file: str = "policies/learning_policy.yaml") -> RiskAssessment:
    """Convenience function to assess risk for a single content item."""
    scanner = InjectionScanner(policy_file)
    return scanner.assess_content_risk(content)

def assess_content_risks(contents: List[NormalizedContent],
                        policy_file: str = "policies/learning_policy.yaml") -> List[RiskAssessment]:
    """Convenience function to assess risk for a batch of content items."""
    scanner = InjectionScanner(policy_file)
    return scanner.scan_batch(contents)
