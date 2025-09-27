"""
StillMe License Gate
Validates content licenses against policy requirements.
"""

import logging
import yaml
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from stillme_core.learning.parser.normalize import NormalizedContent

log = logging.getLogger(__name__)

@dataclass
class LicenseDecision:
    """License gate decision result."""
    allowed: bool
    license: Optional[str]
    reason: str
    confidence: float
    policy_violations: List[str] = None
    
    def __post_init__(self):
        if self.policy_violations is None:
            self.policy_violations = []

class LicenseGate:
    """Validates content licenses against policy."""
    
    def __init__(self, policy_file: str = "policies/learning_policy.yaml"):
        self.policy_file = Path(policy_file)
        self.policy = self._load_policy()
        self.allowed_licenses = set(self.policy.get('content_filters', {}).get('allowed_licenses', []))
        self.rejected_licenses = set(self.policy.get('content_filters', {}).get('rejected_licenses', []))
        
        log.info(f"License gate initialized with {len(self.allowed_licenses)} allowed licenses")
    
    def _load_policy(self) -> Dict:
        """Load learning policy."""
        try:
            if self.policy_file.exists():
                with open(self.policy_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                log.warning(f"Policy file not found: {self.policy_file}")
                return self._get_default_policy()
        except Exception as e:
            log.error(f"Failed to load policy: {e}")
            return self._get_default_policy()
    
    def _get_default_policy(self) -> Dict:
        """Get default policy if file loading fails."""
        return {
            'content_filters': {
                'allowed_licenses': ['CC-BY', 'CC-BY-SA', 'Apache-2.0', 'MIT', 'BSD-3-Clause'],
                'rejected_licenses': ['All Rights Reserved', 'Proprietary', 'Commercial']
            }
        }
    
    def validate_license(self, content: NormalizedContent) -> LicenseDecision:
        """Validate content license against policy."""
        license_info = content.license
        violations = []
        
        # Check if license is explicitly rejected
        if license_info in self.rejected_licenses:
            violations.append(f"License '{license_info}' is explicitly rejected by policy")
            return LicenseDecision(
                allowed=False,
                license=license_info,
                reason=f"License '{license_info}' is rejected by policy",
                confidence=1.0,
                policy_violations=violations
            )
        
        # Check if license is explicitly allowed
        if license_info in self.allowed_licenses:
            return LicenseDecision(
                allowed=True,
                license=license_info,
                reason=f"License '{license_info}' is allowed by policy",
                confidence=1.0,
                policy_violations=[]
            )
        
        # Handle unknown licenses
        if license_info is None or license_info == "Unknown":
            # Check domain-based exceptions
            domain_exceptions = self._check_domain_exceptions(content.domain)
            if domain_exceptions:
                return LicenseDecision(
                    allowed=True,
                    license=license_info,
                    reason=f"Domain '{content.domain}' has license exception",
                    confidence=0.8,
                    policy_violations=[]
                )
            
            violations.append("License is unknown and no domain exception applies")
            return LicenseDecision(
                allowed=False,
                license=license_info,
                reason="Unknown license - requires explicit approval",
                confidence=0.9,
                policy_violations=violations
            )
        
        # License not in allowed list but not explicitly rejected
        violations.append(f"License '{license_info}' not in allowed list")
        return LicenseDecision(
            allowed=False,
            license=license_info,
            reason=f"License '{license_info}' not explicitly allowed",
            confidence=0.7,
            policy_violations=violations
        )
    
    def _check_domain_exceptions(self, domain: str) -> bool:
        """Check if domain has license exceptions."""
        # Domain-specific license exceptions
        domain_exceptions = {
            'arxiv.org': True,  # arXiv papers are generally open
            'github.com': True,  # GitHub repos often have permissive licenses
        }
        
        return domain_exceptions.get(domain, False)
    
    def validate_batch(self, contents: List[NormalizedContent]) -> List[LicenseDecision]:
        """Validate a batch of content items."""
        decisions = []
        
        for content in contents:
            try:
                decision = self.validate_license(content)
                decisions.append(decision)
            except Exception as e:
                log.error(f"License validation failed for content: {e}")
                # Create a rejection decision for failed validations
                decisions.append(LicenseDecision(
                    allowed=False,
                    license=content.license,
                    reason=f"License validation failed: {str(e)}",
                    confidence=0.0,
                    policy_violations=["Validation error"]
                ))
        
        # Log statistics
        allowed_count = sum(1 for d in decisions if d.allowed)
        log.info(f"License gate: {allowed_count}/{len(decisions)} items allowed")
        
        return decisions
    
    def get_policy_summary(self) -> Dict:
        """Get license policy summary."""
        return {
            'allowed_licenses': list(self.allowed_licenses),
            'rejected_licenses': list(self.rejected_licenses),
            'policy_file': str(self.policy_file),
            'domain_exceptions': {
                'arxiv.org': True,
                'github.com': True
            }
        }
    
    def update_policy(self, new_policy: Dict) -> bool:
        """Update license policy."""
        try:
            # Validate new policy structure
            if 'content_filters' not in new_policy:
                log.error("Invalid policy structure: missing 'content_filters'")
                return False
            
            content_filters = new_policy['content_filters']
            if 'allowed_licenses' not in content_filters:
                log.error("Invalid policy structure: missing 'allowed_licenses'")
                return False
            
            # Update internal state
            self.policy = new_policy
            self.allowed_licenses = set(content_filters.get('allowed_licenses', []))
            self.rejected_licenses = set(content_filters.get('rejected_licenses', []))
            
            log.info("License policy updated successfully")
            return True
            
        except Exception as e:
            log.error(f"Failed to update policy: {e}")
            return False

def validate_content_license(content: NormalizedContent, 
                           policy_file: str = "policies/learning_policy.yaml") -> LicenseDecision:
    """Convenience function to validate a single content item."""
    gate = LicenseGate(policy_file)
    return gate.validate_license(content)

def validate_content_licenses(contents: List[NormalizedContent],
                            policy_file: str = "policies/learning_policy.yaml") -> List[LicenseDecision]:
    """Convenience function to validate a batch of content items."""
    gate = LicenseGate(policy_file)
    return gate.validate_batch(contents)
