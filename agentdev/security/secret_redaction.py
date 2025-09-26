import secrets
#!/usr/bin/env python3
"""
AgentDev Secret Redaction - SEAL-GRADE
Enterprise-grade secret detection and redaction
"""

import asyncio
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union, Tuple
import yaml
import hashlib
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecretType(Enum):
    """Types of secrets"""
    PASSWORD = "password"
    API_KEY = "api_key"
    TOKEN = "token"
    SECRET = "secret"
    PRIVATE_KEY = "private_key"
    CREDENTIAL = "credential"
    SESSION_ID = "session_id"
    COOKIE = "cookie"
    DATABASE_URL = "database_url"
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"

class RedactionLevel(Enum):
    """Redaction levels"""
    NONE = "none"           # No redaction
    PARTIAL = "partial"     # Partial redaction (show first/last chars)
    FULL = "full"          # Full redaction (show only type)
    HASH = "hash"          # Show hash of value

@dataclass
class SecretPattern:
    """Pattern for detecting secrets"""
    pattern_id: str
    secret_type: SecretType
    regex: str
    confidence: float  # 0.0 to 1.0
    description: str
    redaction_level: RedactionLevel = RedactionLevel.FULL

@dataclass
class DetectedSecret:
    """Detected secret information"""
    secret_id: str
    secret_type: SecretType
    value: str
    redacted_value: str
    position: Tuple[int, int]  # start, end
    confidence: float
    context: str  # surrounding text
    redaction_level: RedactionLevel

@dataclass
class RedactionResult:
    """Result of redaction process"""
    original_text: str
    redacted_text: str
    detected_secrets: List[DetectedSecret]
    redaction_count: int
    processing_time: float

class SecretRedactor:
    """
    SEAL-GRADE Secret Redactor
    
    Detects and redacts sensitive information:
    - Password detection
    - API key detection
    - Token detection
    - Private key detection
    - Database URL detection
    - PII detection (email, phone, SSN)
    - Credit card detection
    - Custom pattern matching
    - Context-aware redaction
    - Audit logging
    """
    
    def __init__(self, policy_file: str = "agentdev/policy/redaction_policy.yaml"):
        self.policy_file = Path(policy_file)
        self.patterns: List[SecretPattern] = []
        self.redaction_history: List[RedactionResult] = []
        self.secret_hashes: Set[str] = set()  # Track redacted secrets
        
        # Load redaction policies
        self._load_policies()
        
        # Initialize default patterns
        self._initialize_default_patterns()
        
        logger.info("🔐 Secret Redactor initialized with SEAL-GRADE security")
    
    def _load_policies(self):
        """Load redaction policies from YAML file"""
        if not self.policy_file.exists():
            self._create_default_policies()
            return
        
        try:
            with open(self.policy_file, 'r', encoding='utf-8') as f:
                policy_data = yaml.safe_load(f)
            
            # Load custom patterns
            for pattern_config in policy_data.get('patterns', []):
                pattern = SecretPattern(
                    pattern_id=pattern_config['pattern_id'],
                    secret_type=SecretType(pattern_config['secret_type']),
                    regex=pattern_config['regex'],
                    confidence=pattern_config['confidence'],
                    description=pattern_config['description'],
                    redaction_level=RedactionLevel(pattern_config.get('redaction_level', 'full'))
                )
                self.patterns.append(pattern)
            
            logger.info(f"✅ Loaded {len(self.patterns)} redaction patterns")
            
        except Exception as e:
            logger.error(f"❌ Failed to load redaction policies: {e}")
            self._create_default_policies()
    
    def _create_default_policies(self):
        """Create default redaction policies"""
        policy_data = {
            'patterns': [
                {
                    'pattern_id': 'password_basic',
                    'secret_type': 'password',
                    'regex': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s]+)["\']?',
                    'confidence': 0.9,
                    'description': 'Basic password detection',
                    'redaction_level': 'full'
                },
                {
                    'pattern_id': 'api_key_basic',
                    'secret_type': 'api_key',
                    'regex': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
                    'confidence': 0.8,
                    'description': 'API key detection',
                    'redaction_level': 'partial'
                },
                {
                    'pattern_id': 'token_bearer',
                    'secret_type': 'token',
                    'regex': r'(?i)(bearer\s+)?token\s*[:=]\s*["\']?([a-zA-Z0-9._-]{20,})["\']?',
                    'confidence': 0.8,
                    'description': 'Bearer token detection',
                    'redaction_level': 'partial'
                },
                {
                    'pattern_id': 'private_key_rsa',
                    'secret_type': 'private_key',
                    'regex': r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----.*?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
                    'confidence': 0.95,
                    'description': 'RSA private key detection',
                    'redaction_level': 'full'
                },
                {
                    'pattern_id': 'database_url',
                    'secret_type': 'database_url',
                    'regex': r'(?i)(database[_-]?url|db[_-]?url)\s*[:=]\s*["\']?([^"\'\s]+)["\']?',
                    'confidence': 0.9,
                    'description': 'Database URL detection',
                    'redaction_level': 'full'
                },
                {
                    'pattern_id': 'email_address',
                    'secret_type': 'email',
                    'regex': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    'confidence': 0.7,
                    'description': 'Email address detection',
                    'redaction_level': 'partial'
                },
                {
                    'pattern_id': 'phone_number',
                    'secret_type': 'phone',
                    'regex': r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                    'confidence': 0.6,
                    'description': 'Phone number detection',
                    'redaction_level': 'partial'
                },
                {
                    'pattern_id': 'ssn',
                    'secret_type': 'ssn',
                    'regex': r'\b(?!000|666|9\d{2})\d{3}[-.\s]?(?!00)\d{2}[-.\s]?(?!0000)\d{4}\b',
                    'confidence': 0.8,
                    'description': 'SSN detection',
                    'redaction_level': 'full'
                },
                {
                    'pattern_id': 'credit_card',
                    'secret_type': 'credit_card',
                    'regex': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
                    'confidence': 0.7,
                    'description': 'Credit card detection',
                    'redaction_level': 'partial'
                }
            ]
        }
        
        with open(self.policy_file, 'w', encoding='utf-8') as f:
            yaml.dump(policy_data, f, default_flow_style=False, indent=2)
        
        logger.info("✅ Created default redaction policies")
    
    def _initialize_default_patterns(self):
        """Initialize default secret detection patterns"""
        # Load patterns from policy file
        self._load_policies()
    
    async def redact_text(self, text: str, redaction_level: RedactionLevel = RedactionLevel.FULL) -> RedactionResult:
        """
        Redact sensitive information from text
        
        SEAL-GRADE redaction includes:
        - Pattern matching
        - Context analysis
        - Confidence scoring
        - Multiple redaction levels
        - Audit logging
        """
        start_time = time.time()
        detected_secrets: List[DetectedSecret] = []
        redacted_text = text
        
        # Detect secrets using all patterns
        for pattern in self.patterns:
            matches = re.finditer(pattern.regex, text, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                # Extract the secret value (usually the second group)
                secret_value = match.group(2) if len(match.groups()) >= 2 else match.group(0)
                
                # Skip if confidence is too low
                if pattern.confidence < 0.5:
                    continue
                
                # Create detected secret
                secret_id = str(uuid.uuid4())
                redacted_value = self._redact_value(secret_value, pattern.redaction_level)
                
                detected_secret = DetectedSecret(
                    secret_id=secret_id,
                    secret_type=pattern.secret_type,
                    value=secret_value,
                    redacted_value=redacted_value,
                    position=(match.start(), match.end()),
                    confidence=pattern.confidence,
                    context=self._extract_context(text, match.start(), match.end()),
                    redaction_level=pattern.redaction_level
                )
                
                detected_secrets.append(detected_secret)
                
                # Replace in text
                redacted_text = redacted_text.replace(secret_value, redacted_value)
                
                # Track secret hash
                secret_hash = hashlib.sha256(secret_value.encode()).hexdigest()
                self.secret_hashes.add(secret_hash)
        
        # Sort secrets by position (reverse order for replacement)
        detected_secrets.sort(key=lambda x: x.position[0], reverse=True)
        
        # Apply redactions
        for secret in detected_secrets:
            start, end = secret.position
            redacted_text = redacted_text[:start] + secret.redacted_value + redacted_text[end:]
        
        processing_time = time.time() - start_time
        
        # Create result
        result = RedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            detected_secrets=detected_secrets,
            redaction_count=len(detected_secrets),
            processing_time=processing_time
        )
        
        # Record in history
        self.redaction_history.append(result)
        
        # Keep only last 1000 redactions
        if len(self.redaction_history) > 1000:
            self.redaction_history = self.redaction_history[-1000:]
        
        # Log redaction
        if detected_secrets:
            logger.warning(f"🔐 Redacted {len(detected_secrets)} secrets in {processing_time:.3f}s")
            for secret in detected_secrets:
                logger.warning(f"  - {secret.secret_type.value}: {secret.redacted_value}")
        
        return result
    
    def _redact_value(self, value: str, redaction_level: RedactionLevel) -> str:
        """Redact a secret value based on redaction level"""
        if redaction_level == RedactionLevel.NONE:
            return value
        elif redaction_level == RedactionLevel.PARTIAL:
            if len(value) <= 4:
                return "*" * len(value)
            else:
                return value[:2] + "*" * (len(value) - 4) + value[-2:]
        elif redaction_level == RedactionLevel.HASH:
            return f"[HASH:{hashlib.sha256(value.encode()).hexdigest()[:8]}]"
        else:  # FULL
            return "[REDACTED]"
    
    def _extract_context(self, text: str, start: int, end: int, context_size: int = 50) -> str:
        """Extract context around detected secret"""
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        return text[context_start:context_end]
    
    async def redact_dict(self, data: Dict[str, Any], 
                         sensitive_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Redact sensitive information from dictionary"""
        if sensitive_keys is None:
            sensitive_keys = {
                'password', 'passwd', 'pwd', 'secret', 'token', 'key', 'api_key',
                'private_key', 'database_url', 'db_url', 'email', 'phone', 'ssn'
            }
        
        redacted_data = {}
        
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                if isinstance(value, str):
                    # Force redaction for sensitive keys
                    redacted_data[key] = "[REDACTED]"
                else:
                    redacted_data[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted_data[key] = await self.redact_dict(value, sensitive_keys)
            elif isinstance(value, list):
                redacted_list = []
                for item in value:
                    if isinstance(item, dict):
                        redacted_list.append(await self.redact_dict(item, sensitive_keys))
                    elif isinstance(item, str):
                        result = await self.redact_text(item)
                        redacted_list.append(result.redacted_text)
                    else:
                        redacted_list.append(item)
                redacted_data[key] = redacted_list
            else:
                redacted_data[key] = value
        
        return redacted_data
    
    async def redact_json(self, json_text: str) -> str:
        """Redact sensitive information from JSON text"""
        try:
            data = json.loads(json_text)
            redacted_data = await self.redact_dict(data)
            return json.dumps(redacted_data, indent=2, default=str)
        except json.JSONDecodeError:
            # If not valid JSON, treat as plain text
            result = await self.redact_text(json_text)
            return result.redacted_text
    
    def get_redaction_stats(self) -> Dict[str, Any]:
        """Get redaction statistics"""
        total_redactions = len(self.redaction_history)
        total_secrets = sum(result.redaction_count for result in self.redaction_history)
        
        # Count by secret type
        secret_type_counts = {}
        for result in self.redaction_history:
            for secret in result.detected_secrets:
                secret_type = secret.secret_type.value
                secret_type_counts[secret_type] = secret_type_counts.get(secret_type, 0) + 1
        
        # Count by redaction level
        redaction_level_counts = {}
        for result in self.redaction_history:
            for secret in result.detected_secrets:
                level = secret.redaction_level.value
                redaction_level_counts[level] = redaction_level_counts.get(level, 0) + 1
        
        return {
            "total_redactions": total_redactions,
            "total_secrets_detected": total_secrets,
            "unique_secret_hashes": len(self.secret_hashes),
            "secrets_by_type": secret_type_counts,
            "redactions_by_level": redaction_level_counts,
            "active_patterns": len(self.patterns)
        }
    
    def get_redaction_history(self, limit: int = 100) -> List[RedactionResult]:
        """Get recent redaction history"""
        return self.redaction_history[-limit:]
    
    def add_pattern(self, pattern: SecretPattern):
        """Add new secret detection pattern"""
        self.patterns.append(pattern)
        self._save_policies()
        logger.info(f"✅ Added redaction pattern: {pattern.pattern_id}")
    
    def remove_pattern(self, pattern_id: str):
        """Remove secret detection pattern"""
        self.patterns = [p for p in self.patterns if p.pattern_id != pattern_id]
        self._save_policies()
        logger.info(f"✅ Removed redaction pattern: {pattern_id}")
    
    def _save_policies(self):
        """Save redaction policies to YAML file"""
        try:
            policy_data = {
                'patterns': [
                    {
                        'pattern_id': pattern.pattern_id,
                        'secret_type': pattern.secret_type.value,
                        'regex': pattern.regex,
                        'confidence': pattern.confidence,
                        'description': pattern.description,
                        'redaction_level': pattern.redaction_level.value
                    }
                    for pattern in self.patterns
                ]
            }
            
            with open(self.policy_file, 'w', encoding='utf-8') as f:
                yaml.dump(policy_data, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save redaction policies: {e}")

# Global secret redactor instance
secret_redactor = SecretRedactor()

# Convenience functions
async def redact_text(text: str, redaction_level: RedactionLevel = RedactionLevel.FULL) -> RedactionResult:
    """Redact sensitive information from text"""
    return await secret_redactor.redact_text(text, redaction_level)

async def redact_dict(data: Dict[str, Any], sensitive_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
    """Redact sensitive information from dictionary"""
    return await secret_redactor.redact_dict(data, sensitive_keys)

async def redact_json(json_text: str) -> str:
    """Redact sensitive information from JSON text"""
    return await secret_redactor.redact_json(json_text)

def get_redaction_stats() -> Dict[str, Any]:
    """Get redaction statistics"""
    return secret_redactor.get_redaction_stats()
