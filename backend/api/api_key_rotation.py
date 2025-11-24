"""
API Key Rotation Service
Manages API key rotation for enhanced security
"""

import os
import secrets
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class APIKeyRecord:
    """Record for an API key"""
    key_hash: str  # SHA-256 hash of the key
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    last_used: Optional[datetime]
    usage_count: int = 0


class APIKeyRotationService:
    """Service for managing API key rotation"""
    
    def __init__(self, rotation_interval_days: int = 90, max_keys: int = 3):
        """Initialize API key rotation service
        
        Args:
            rotation_interval_days: Days between key rotations (default: 90)
            max_keys: Maximum number of active keys to keep (default: 3)
        """
        self.rotation_interval_days = rotation_interval_days
        self.max_keys = max_keys
        self.keys: List[APIKeyRecord] = []
        logger.info(f"API Key Rotation Service initialized (rotation interval: {rotation_interval_days} days)")
    
    def _hash_key(self, key: str) -> str:
        """Hash API key for storage (SHA-256)"""
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()
    
    def add_key(self, key: str, expires_in_days: Optional[int] = None) -> str:
        """Add a new API key
        
        Args:
            key: API key string (will be hashed)
            expires_in_days: Days until expiration (None = no expiration)
            
        Returns:
            Key hash for reference
        """
        key_hash = self._hash_key(key)
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        record = APIKeyRecord(
            key_hash=key_hash,
            created_at=datetime.now(),
            expires_at=expires_at,
            is_active=True,
            last_used=None,
            usage_count=0
        )
        
        self.keys.append(record)
        
        # Keep only max_keys most recent active keys
        active_keys = [k for k in self.keys if k.is_active]
        if len(active_keys) > self.max_keys:
            # Deactivate oldest keys
            active_keys.sort(key=lambda x: x.created_at)
            for old_key in active_keys[:-self.max_keys]:
                old_key.is_active = False
                logger.info(f"Deactivated old API key (created: {old_key.created_at})")
        
        logger.info(f"Added new API key (expires: {expires_at})")
        return key_hash
    
    def verify_key(self, key: str) -> bool:
        """Verify API key and update usage stats
        
        Args:
            key: API key to verify
            
        Returns:
            True if key is valid and active, False otherwise
        """
        key_hash = self._hash_key(key)
        
        for record in self.keys:
            if record.key_hash == key_hash:
                # Check if expired
                if record.expires_at and datetime.now() > record.expires_at:
                    logger.warning(f"API key expired: {record.expires_at}")
                    record.is_active = False
                    return False
                
                # Check if active
                if not record.is_active:
                    logger.warning("API key is not active")
                    return False
                
                # Update usage stats
                record.last_used = datetime.now()
                record.usage_count += 1
                return True
        
        return False
    
    def rotate_key(self) -> str:
        """Generate a new API key and rotate
        
        Returns:
            New API key string
        """
        # Generate new key
        new_key = secrets.token_hex(32)
        
        # Add to rotation service
        self.add_key(new_key, expires_in_days=self.rotation_interval_days)
        
        logger.info("API key rotated successfully")
        return new_key
    
    def get_active_keys(self) -> List[Dict[str, any]]:
        """Get list of active API keys (metadata only, not the keys themselves)
        
        Returns:
            List of key metadata dictionaries
        """
        active_keys = [k for k in self.keys if k.is_active]
        return [
            {
                "created_at": k.created_at.isoformat(),
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "last_used": k.last_used.isoformat() if k.last_used else None,
                "usage_count": k.usage_count,
                "is_expired": k.expires_at and datetime.now() > k.expires_at if k.expires_at else False
            }
            for k in active_keys
        ]
    
    def deactivate_key(self, key_hash: str) -> bool:
        """Deactivate an API key
        
        Args:
            key_hash: Hash of the key to deactivate
            
        Returns:
            True if key was found and deactivated, False otherwise
        """
        for record in self.keys:
            if record.key_hash == key_hash:
                record.is_active = False
                logger.info(f"Deactivated API key (created: {record.created_at})")
                return True
        return False


# Global rotation service instance
_api_key_rotation_service: Optional[APIKeyRotationService] = None


def get_api_key_rotation_service() -> Optional[APIKeyRotationService]:
    """Get global API key rotation service instance"""
    global _api_key_rotation_service
    if _api_key_rotation_service is None:
        rotation_interval = int(os.getenv("API_KEY_ROTATION_INTERVAL_DAYS", "90"))
        _api_key_rotation_service = APIKeyRotationService(rotation_interval_days=rotation_interval)
    return _api_key_rotation_service

