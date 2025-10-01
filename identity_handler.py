"""Identity Handler for StillMe Framework"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class IdentityType(Enum):
    USER = "user"
    SYSTEM = "system"
    SERVICE = "service"
    ANONYMOUS = "anonymous"

class IdentityStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

@dataclass
class Identity:
    """Identity record"""
    id: str
    name: str
    identity_type: IdentityType
    status: IdentityStatus
    created_at: datetime
    last_accessed: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class IdentityHandler:
    """Identity handler for StillMe framework"""

    def __init__(self):
        self.logger = logger
        self.identities: List[Identity] = []
        self.logger.info("✅ IdentityHandler initialized")

    def create_identity(self,
                       name: str,
                       identity_type: IdentityType,
                       metadata: Dict[str, Any] = None) -> str:
        """Create a new identity"""
        try:
            identity_id = f"id_{len(self.identities) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            identity = Identity(
                id=identity_id,
                name=name,
                identity_type=identity_type,
                status=IdentityStatus.ACTIVE,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                metadata=metadata or {}
            )

            self.identities.append(identity)
            self.logger.info(f"👤 Identity created: {name} ({identity_type.value})")
            return identity_id

        except Exception as e:
            self.logger.error(f"❌ Failed to create identity: {e}")
            return ""

    def get_identity(self, identity_id: str) -> Optional[Identity]:
        """Get identity by ID"""
        for identity in self.identities:
            if identity.id == identity_id:
                return identity
        return None

    def update_identity_status(self, identity_id: str, status: IdentityStatus) -> bool:
        """Update identity status"""
        for identity in self.identities:
            if identity.id == identity_id:
                identity.status = status
                identity.last_accessed = datetime.now()
                self.logger.info(f"🔄 Identity {identity_id} status updated to {status.value}")
                return True
        return False

    def get_identities_by_type(self, identity_type: IdentityType) -> List[Identity]:
        """Get identities by type"""
        return [i for i in self.identities if i.identity_type == identity_type]

    def get_identities_by_status(self, status: IdentityStatus) -> List[Identity]:
        """Get identities by status"""
        return [i for i in self.identities if i.status == status]

    def get_identity_summary(self) -> Dict[str, Any]:
        """Get identity summary"""
        try:
            total_identities = len(self.identities)
            identities_by_type = {}
            identities_by_status = {}

            for identity in self.identities:
                # Count by type
                type_key = identity.identity_type.value
                identities_by_type[type_key] = identities_by_type.get(type_key, 0) + 1

                # Count by status
                status_key = identity.status.value
                identities_by_status[status_key] = identities_by_status.get(status_key, 0) + 1

            return {
                "total_identities": total_identities,
                "identities_by_type": identities_by_type,
                "identities_by_status": identities_by_status,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get identity summary: {e}")
            return {"error": str(e)}

    def clear_identities(self):
        """Clear all identities"""
        self.identities.clear()
        self.logger.info("🧹 All identities cleared")
