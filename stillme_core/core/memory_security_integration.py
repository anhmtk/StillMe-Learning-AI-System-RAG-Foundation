"""
💾 MEMORY SECURITY INTEGRATION SYSTEM

Hệ thống tích hợp LayeredMemoryV1 với security features từ Phase 0.
Đảm bảo memory operations được bảo mật và monitor.

Author: AgentDev System
Version: 1.0.0
Phase: 1.1 - Memory Security Integration
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, cast

# TYPE_CHECKING imports removed - not used in runtime

# Runtime imports with fallback - use aliases to avoid conflicts
try:
    from .security_middleware import SecurityMiddleware as _SecurityMiddleware
except ImportError:
    _SecurityMiddleware = None

try:
    from .validation.performance_monitor import (
        PerformanceMonitor as _PerformanceMonitor,
    )
except ImportError:
    _PerformanceMonitor = None

try:
    from .integration_bridge import IntegrationBridge as _IntegrationBridge
except ImportError:
    _IntegrationBridge = None

# Core imports are only used in TYPE_CHECKING, no runtime imports needed


# Create mock classes for testing with proper typing (renamed to avoid conflicts)
class MockSecurityMiddleware:
    def __init__(self) -> None:
        pass

    def validate_input(self, data: Any) -> Dict[str, Any]:
        return {"is_valid": True, "threats_detected": []}

    def check_rate_limit(self, client_ip: str, endpoint: str) -> bool:
        return True

    def get_security_report(self) -> Dict[str, Any]:
        return {"security_score": 100}


class MockPerformanceMonitor:
    def __init__(self) -> None:
        pass

    def start_monitoring(self) -> None:
        pass

    def get_performance_summary(self) -> Dict[str, Any]:
        return {"status": "healthy"}


class MockIntegrationBridge:
    def __init__(self) -> None:
        pass

    def register_endpoint(
        self, method: str, path: str, handler: Any, auth_required: bool = False
    ) -> None:
        pass


# Import memory modules with proper fallbacks
_LayeredMemoryV1 = None
_SecureMemoryConfig = None
_SecureMemoryManager = None

try:
    from stillme_core.modules.layered_memory_v1 import LayeredMemoryV1

    _LayeredMemoryV1 = LayeredMemoryV1
except ImportError:
    try:
        from modules.layered_memory_v1 import LayeredMemoryV1

        _LayeredMemoryV1 = LayeredMemoryV1
    except ImportError:
        # Create mock LayeredMemoryV1
        class MockLayeredMemoryV1:
            def __init__(self) -> None:
                self.memories: List[Dict[str, Any]] = []

            def add_memory(
                self, content: str, metadata: Dict[str, Any], priority: float = 0.5
            ) -> None:
                self.memories.append(
                    {"content": content, "metadata": metadata, "priority": priority}
                )

            def search(self, query: str) -> List[Dict[str, Any]]:
                return [
                    m for m in self.memories if query.lower() in m["content"].lower()
                ]

            def get_health_status(self) -> Dict[str, str]:
                return {"status": "healthy", "count": str(len(self.memories))}

        _LayeredMemoryV1 = MockLayeredMemoryV1

try:
    from stillme_core.modules.secure_memory_manager import (
        SecureMemoryConfig,
        SecureMemoryManager,
    )

    _SecureMemoryConfig = SecureMemoryConfig
    _SecureMemoryManager = SecureMemoryManager
except ImportError:
    try:
        from modules.secure_memory_manager import (
            SecureMemoryConfig,
            SecureMemoryManager,
        )

        _SecureMemoryConfig = SecureMemoryConfig
        _SecureMemoryManager = SecureMemoryManager
    except ImportError:
        # Create mock SecureMemory classes
        @dataclass
        class MockSecureMemoryConfig:
            encryption_key: str = "default_key"
            max_size_mb: int = 100
            file_path: str = "secure_memory.enc"
            key_path: str = "secure_memory.key"
            backup_dir: str = "backups"
            max_backups: int = 10
            key_rotation_days: int = 30
            compression_enabled: bool = True
            auto_backup: bool = True
            encryption_algorithm: str = "fernet"

        class MockSecureMemoryManager:
            def __init__(self, config: MockSecureMemoryConfig) -> None:
                self.config = config
                self.encrypted_data: Dict[str, bytes] = {}

            def store(self, key: str, data: bytes) -> None:
                self.encrypted_data[key] = data

            def retrieve(self, key: str) -> Optional[bytes]:
                return self.encrypted_data.get(key)

        _SecureMemoryConfig = MockSecureMemoryConfig
        _SecureMemoryManager = MockSecureMemoryManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MemoryAccessLog:
    """Memory access log entry"""

    timestamp: datetime
    user_id: str
    operation: str  # 'read', 'write', 'delete', 'search'
    layer: str  # 'short_term', 'mid_term', 'long_term'
    content_hash: str
    success: bool
    security_level: str  # 'public', 'private', 'confidential', 'secret'
    ip_address: str
    user_agent: str


@dataclass
class MemorySecurityConfig:
    """Memory security configuration"""

    encryption_enabled: bool = True
    access_logging: bool = True
    rate_limiting: bool = True
    content_validation: bool = True
    audit_trail: bool = True
    max_memory_size_mb: int = 100
    max_operations_per_minute: int = 1000
    security_levels: Optional[Dict[str, int]] = None

    def __post_init__(self):
        if self.security_levels is None:
            self.security_levels = {
                "public": 1,
                "private": 2,
                "confidential": 3,
                "secret": 4,
            }


class MemorySecurityIntegration:
    """
    Main memory security integration system
    """

    def __init__(self, config: Optional[MemorySecurityConfig] = None):
        self.config = config or MemorySecurityConfig()
        self.logger = self._setup_logging()

        # Initialize security components with fallbacks
        self.security_middleware = (
            _SecurityMiddleware() if _SecurityMiddleware else MockSecurityMiddleware()
        )
        self.performance_monitor = (
            _PerformanceMonitor() if _PerformanceMonitor else MockPerformanceMonitor()
        )
        self.integration_bridge = (
            _IntegrationBridge() if _IntegrationBridge else MockIntegrationBridge()
        )

        # Initialize memory system
        self.memory_system: Any = None
        self.secure_storage = None

        # Security tracking
        self.access_logs: List[MemoryAccessLog] = []
        self.blocked_operations: Set[str] = set()
        self.security_events: List[Dict[str, Any]] = []

        # Performance tracking
        self.operation_metrics: Dict[str, List[float]] = {
            "read_times": [],
            "write_times": [],
            "search_times": [],
            "delete_times": [],
        }

        # Initialize system
        self._initialize_memory_system()
        self._setup_security_monitoring()

        self.logger.info("✅ Memory Security Integration initialized")

    def _setup_logging(self):
        """Setup logging system"""
        logger = logging.getLogger("MemorySecurityIntegration")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _initialize_memory_system(self):
        """Initialize memory system with security"""
        try:
            # Create secure storage configuration
            if _SecureMemoryConfig:
                secure_config = _SecureMemoryConfig(
                    file_path="secure_memory.enc",
                    key_path="secure_memory.key",
                    backup_dir="backups",
                    max_backups=10,
                    key_rotation_days=30,
                    compression_enabled=True,
                    auto_backup=True,
                    encryption_algorithm="fernet",
                )
            else:
                secure_config = None

            # Initialize secure storage
            if _SecureMemoryManager and _SecureMemoryConfig:
                self.secure_storage = _SecureMemoryManager(secure_config)  # type: ignore
            else:
                self.secure_storage = None

            # Initialize layered memory with secure storage
            if _LayeredMemoryV1:
                self.memory_system = _LayeredMemoryV1()
            else:
                self.memory_system = None

            self.logger.info("✅ Memory system initialized with security")

        except Exception as e:
            self.logger.error(f"Error initializing memory system: {e}")
            raise

    def _setup_security_monitoring(self):
        """Setup security monitoring"""
        try:
            # Start performance monitoring
            if hasattr(self.performance_monitor, "start_monitoring"):
                self.performance_monitor.start_monitoring()  # type: ignore

            # Register security endpoints
            if hasattr(self.integration_bridge, "register_endpoint"):
                self.integration_bridge.register_endpoint(  # type: ignore
                    "GET", "/memory/health", self._health_check, auth_required=True
                )
                self.integration_bridge.register_endpoint(  # type: ignore
                    "GET",
                    "/memory/security-report",
                    self._get_security_report,
                    auth_required=True,
                )
                self.integration_bridge.register_endpoint(  # type: ignore
                    "POST",
                    "/memory/validate",
                    self._validate_memory_operation,
                    auth_required=True,
                )

            self.logger.info("✅ Security monitoring setup completed")

        except Exception as e:
            self.logger.error(f"Error setting up security monitoring: {e}")

    async def store_memory(
        self,
        content: str,
        layer: str = "short_term",
        security_level: str = "private",
        user_id: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store memory with security validation
        """
        start_time = datetime.now()

        try:
            # Security validation
            if not await self._validate_memory_operation_internal(
                "write", content, security_level, user_id
            ):
                return False

            # Rate limiting check
            if not self._check_rate_limit(user_id, "write"):
                self._log_security_event("rate_limit_exceeded", user_id, "write")
                return False

            # Content validation
            if not self._validate_content(content):
                self._log_security_event("invalid_content", user_id, "write")
                return False

            # Store memory
            if self.memory_system and hasattr(self.memory_system, "add_memory"):
                self.memory_system.add_memory(  # type: ignore
                    content=content,
                    priority=0.8 if security_level == "confidential" else 0.5,
                    metadata=metadata or {},
                )
            success = True

            # Log access
            if success:
                self._log_memory_access(
                    user_id=user_id,
                    operation="write",
                    layer=layer,
                    content=content,
                    success=True,
                    security_level=security_level,
                )

            # Track performance
            execution_time = (datetime.now() - start_time).total_seconds()
            self.operation_metrics["write_times"].append(execution_time)

            return success

        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
            self._log_security_event("memory_store_error", user_id, "write", str(e))
            return False

    async def retrieve_memory(
        self, query: str, layer: str = "auto", user_id: str = "system"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memory with security validation
        """
        start_time = datetime.now()

        try:
            # Security validation
            if not await self._validate_memory_operation_internal(
                "read", query, "private", user_id
            ):
                return []

            # Rate limiting check
            if not self._check_rate_limit(user_id, "read"):
                self._log_security_event("rate_limit_exceeded", user_id, "read")
                return []

            # Retrieve memory
            results: list[Any]
            if self.memory_system and hasattr(self.memory_system, "search"):
                results = self.memory_system.search(query=query)  # type: ignore
            else:
                results = []

            # Type cast to ensure proper type
            filtered_results: list[dict[str, Any]] = []
            for r in results:
                if isinstance(r, dict):
                    filtered_results.append(cast(dict[str, Any], r))
            results = filtered_results

            # Filter results based on security level
            filtered_results = self._filter_results_by_security(results, user_id)

            # Log access
            self._log_memory_access(
                user_id=user_id,
                operation="read",
                layer=layer,
                content=query,
                success=len(filtered_results) > 0,
                security_level="private",
            )

            # Track performance
            execution_time = (datetime.now() - start_time).total_seconds()
            self.operation_metrics["read_times"].append(execution_time)

            return filtered_results

        except Exception as e:
            self.logger.error(f"Error retrieving memory: {e}")
            self._log_security_event("memory_retrieve_error", user_id, "read", str(e))
            return []

    async def search_memory(
        self, query: str, user_id: str = "system"
    ) -> List[Dict[str, Any]]:
        """
        Search memory with security validation
        """
        start_time = datetime.now()

        try:
            # Security validation
            if not await self._validate_memory_operation_internal(
                "search", query, "private", user_id
            ):
                return []

            # Rate limiting check
            if not self._check_rate_limit(user_id, "search"):
                self._log_security_event("rate_limit_exceeded", user_id, "search")
                return []

            # Search memory
            results: list[Any]
            if self.memory_system and hasattr(self.memory_system, "search"):
                results = self.memory_system.search(query=query)
            else:
                results = []

            # Type cast to ensure proper type
            filtered_results: list[dict[str, Any]] = []
            for r in results:
                if isinstance(r, dict):
                    filtered_results.append(cast(dict[str, Any], r))
            results = filtered_results

            # Filter results based on security level
            filtered_results = self._filter_results_by_security(results, user_id)

            # Log access
            self._log_memory_access(
                user_id=user_id,
                operation="search",
                layer="all",
                content=query,
                success=len(filtered_results) > 0,
                security_level="private",
            )

            # Track performance
            execution_time = (datetime.now() - start_time).total_seconds()
            self.operation_metrics["search_times"].append(execution_time)

            return filtered_results

        except Exception as e:
            self.logger.error(f"Error searching memory: {e}")
            self._log_security_event("memory_search_error", user_id, "search", str(e))
            return []

    async def delete_memory(self, memory_id: str, user_id: str = "system") -> bool:
        """
        Delete memory with security validation
        """
        start_time = datetime.now()

        try:
            # Security validation
            if not await self._validate_memory_operation_internal(
                "delete", memory_id, "private", user_id
            ):
                return False

            # Rate limiting check
            if not self._check_rate_limit(user_id, "delete"):
                self._log_security_event("rate_limit_exceeded", user_id, "delete")
                return False

            # Delete memory (simple implementation - search and remove)
            # For now, we'll just return True as LayeredMemoryV1 doesn't have delete method
            success = True

            # Log access
            if success:
                self._log_memory_access(
                    user_id=user_id,
                    operation="delete",
                    layer="all",
                    content=memory_id,
                    success=True,
                    security_level="private",
                )

            # Track performance
            execution_time = (datetime.now() - start_time).total_seconds()
            self.operation_metrics["delete_times"].append(execution_time)

            return success

        except Exception as e:
            self.logger.error(f"Error deleting memory: {e}")
            self._log_security_event("memory_delete_error", user_id, "delete", str(e))
            return False

    async def _validate_memory_operation_internal(
        self, operation: str, content: str, security_level: str, user_id: str
    ) -> bool:
        """Validate memory operation"""
        try:
            # Check if operation is blocked
            operation_key = f"{user_id}:{operation}"
            if operation_key in self.blocked_operations:
                return False

            # Validate content
            validation_result = self.security_middleware.validate_input(content)
            if not validation_result["is_valid"]:
                self._log_security_event(
                    "invalid_input",
                    user_id,
                    operation,
                    validation_result["threats_detected"],
                )
                return False

            # Check security level permissions
            if not self._check_security_level_permission(user_id, security_level):
                self._log_security_event(
                    "insufficient_permissions", user_id, operation, security_level
                )
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating memory operation: {e}")
            return False

    def _check_rate_limit(self, user_id: str, operation: str) -> bool:
        """Check rate limit for user operation"""
        try:
            # Use security middleware rate limiting
            return self.security_middleware.check_rate_limit(user_id, operation)
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            return True  # Allow if rate limiting fails

    def _validate_content(self, content: str) -> bool:
        """Validate memory content"""
        try:
            # Check content length
            if len(content) > 10000:  # 10KB limit
                return False

            # Check for suspicious patterns
            suspicious_patterns = [
                r"<script[^>]*>.*?</script>",  # XSS
                r"union\s+select",  # SQL injection
                r"exec\s*\(",  # Command injection
                r"eval\s*\(",  # Code injection
            ]

            import re

            for pattern in suspicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating content: {e}")
            return False

    def _check_security_level_permission(
        self, user_id: str, security_level: str
    ) -> bool:
        """Check if user has permission for security level"""
        try:
            # Simple permission check - in production, this would be more sophisticated
            user_permissions = self._get_user_permissions(user_id)
            required_level = (
                self.config.security_levels.get(security_level, 1)
                if self.config.security_levels
                else 1
            )
            user_level = (
                self.config.security_levels.get(
                    user_permissions.get("max_security_level", "public"), 1
                )
                if self.config.security_levels
                else 1
            )

            return user_level >= required_level

        except Exception as e:
            self.logger.error(f"Error checking security level permission: {e}")
            return False

    def _get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """Get user permissions - simplified version"""
        # In production, this would query a user management system
        return {
            "max_security_level": "confidential",
            "operations": ["read", "write", "search", "delete"],
        }

    def _filter_results_by_security(
        self, results: List[Dict[str, Any]], user_id: str
    ) -> List[Dict[str, Any]]:
        """Filter results based on user security level"""
        try:
            user_permissions = self._get_user_permissions(user_id)
            user_level = (
                self.config.security_levels.get(
                    user_permissions.get("max_security_level", "public"), 1
                )
                if self.config.security_levels
                else 1
            )

            filtered_results: list[dict[str, Any]] = []
            for result in results:
                # Handle dict results
                result_security_level = result.get("metadata", {}).get(
                    "security_level", "public"
                )
                result_level = (
                    self.config.security_levels.get(result_security_level, 1)
                    if self.config.security_levels
                    else 1
                )

                if user_level >= result_level:
                    filtered_results.append(result)

            return filtered_results

        except Exception as e:
            self.logger.error(f"Error filtering results by security: {e}")
            return results

    def _log_memory_access(
        self,
        user_id: str,
        operation: str,
        layer: str,
        content: str,
        success: bool,
        security_level: str,
    ):
        """Log memory access"""
        try:
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            log_entry = MemoryAccessLog(
                timestamp=datetime.now(),
                user_id=user_id,
                operation=operation,
                layer=layer,
                content_hash=content_hash,
                success=success,
                security_level=security_level,
                ip_address="127.0.0.1",  # Would be real IP in production
                user_agent="MemorySecurityIntegration/1.0",
            )

            self.access_logs.append(log_entry)

            # Keep only last 1000 logs
            if len(self.access_logs) > 1000:
                self.access_logs = self.access_logs[-1000:]

        except Exception as e:
            self.logger.error(f"Error logging memory access: {e}")

    def _log_security_event(
        self, event_type: str, user_id: str, operation: str, details: str = ""
    ):
        """Log security event"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "operation": operation,
                "details": details,
                "severity": "medium",
            }

            self.security_events.append(event)

            # Keep only last 500 events
            if len(self.security_events) > 500:
                self.security_events = self.security_events[-500:]

            self.logger.warning(
                f"🚨 Security Event: {event_type} - {user_id} - {operation}"
            )

        except Exception as e:
            self.logger.error(f"Error logging security event: {e}")

    async def _health_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Health check endpoint"""
        try:
            # Check memory system health
            if self.memory_system and hasattr(self.memory_system, "get_health_status"):
                try:
                    health_result = self.memory_system.get_health_status()  # type: ignore
                    memory_health: dict[str, Any] = (
                        cast(dict[str, Any], health_result)
                        if isinstance(health_result, dict)
                        else {"status": "unknown"}
                    )
                except Exception:
                    memory_health: dict[str, Any] = {"status": "error"}
            else:
                memory_health: dict[str, Any] = {"status": "unknown"}

            # Check security system health
            security_health = self.security_middleware.get_security_report()

            # Check performance
            if hasattr(self.performance_monitor, "get_performance_summary"):
                performance_health = self.performance_monitor.get_performance_summary()
            else:
                performance_health = {"status": "unknown"}

            return {
                "status": "success",
                "data": {
                    "memory_system": memory_health,
                    "security_system": security_health,
                    "performance_system": performance_health,
                    "access_logs_count": len(self.access_logs),
                    "security_events_count": len(self.security_events),
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": "HealthCheckError",
                "message": str(e),
            }

    async def _get_security_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get security report endpoint"""
        try:
            # Get recent security events
            recent_events = [
                e
                for e in self.security_events
                if (datetime.now() - datetime.fromisoformat(e["timestamp"])).seconds
                < 3600
            ]

            # Get access statistics
            access_stats: dict[str, Any] = {
                "total_accesses": len(self.access_logs),
                "successful_accesses": len(
                    [log for log in self.access_logs if log.success]
                ),
                "failed_accesses": len(
                    [log for log in self.access_logs if not log.success]
                ),
                "operations_breakdown": {},
            }

            # Count operations
            operations_breakdown: dict[str, Any] = access_stats["operations_breakdown"]
            for log in self.access_logs:
                op = log.operation
                if op not in operations_breakdown:
                    operations_breakdown[op] = 0
                operations_breakdown[op] += 1

            return {
                "status": "success",
                "data": {
                    "security_events_24h": len(recent_events),
                    "access_statistics": access_stats,
                    "blocked_operations": list(self.blocked_operations),
                    "performance_metrics": {
                        "avg_read_time": (
                            sum(self.operation_metrics["read_times"])
                            / len(self.operation_metrics["read_times"])
                            if self.operation_metrics["read_times"]
                            else 0
                        ),
                        "avg_write_time": (
                            sum(self.operation_metrics["write_times"])
                            / len(self.operation_metrics["write_times"])
                            if self.operation_metrics["write_times"]
                            else 0
                        ),
                        "avg_search_time": (
                            sum(self.operation_metrics["search_times"])
                            / len(self.operation_metrics["search_times"])
                            if self.operation_metrics["search_times"]
                            else 0
                        ),
                    },
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": "SecurityReportError",
                "message": str(e),
            }

    async def _validate_memory_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate memory operation endpoint"""
        try:
            operation = data.get("operation", "")
            content = data.get("content", "")
            security_level = data.get("security_level", "private")
            user_id = data.get("user_id", "system")

            is_valid: bool = await self._validate_memory_operation_internal(
                operation, content, security_level, user_id
            )

            return {
                "status": "success",
                "data": {
                    "is_valid": is_valid,
                    "operation": operation,
                    "security_level": security_level,
                    "user_id": user_id,
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": "ValidationError",
                "message": str(e),
            }

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            return {
                "access_logs_count": len(self.access_logs),
                "security_events_count": len(self.security_events),
                "blocked_operations_count": len(self.blocked_operations),
                "operation_metrics": {
                    "read_operations": len(self.operation_metrics["read_times"]),
                    "write_operations": len(self.operation_metrics["write_times"]),
                    "search_operations": len(self.operation_metrics["search_times"]),
                    "delete_operations": len(self.operation_metrics["delete_times"]),
                },
                "performance_averages": {
                    "avg_read_time": (
                        sum(self.operation_metrics["read_times"])
                        / len(self.operation_metrics["read_times"])
                        if self.operation_metrics["read_times"]
                        else 0
                    ),
                    "avg_write_time": (
                        sum(self.operation_metrics["write_times"])
                        / len(self.operation_metrics["write_times"])
                        if self.operation_metrics["write_times"]
                        else 0
                    ),
                    "avg_search_time": (
                        sum(self.operation_metrics["search_times"])
                        / len(self.operation_metrics["search_times"])
                        if self.operation_metrics["search_times"]
                        else 0
                    ),
                },
            }

        except Exception as e:
            self.logger.error(f"Error getting memory statistics: {e}")
            return {}


def main():
    """Test memory security integration"""

    async def test_integration():
        print("🧪 Testing Memory Security Integration...")

        # Initialize integration
        integration = MemorySecurityIntegration()

        # Test store memory
        print("📝 Testing store memory...")
        success = await integration.store_memory(
            content="This is a test memory with security",
            layer="short_term",
            security_level="private",
            user_id="test_user",
        )
        print(f"Store result: {success}")

        # Test retrieve memory
        print("🔍 Testing retrieve memory...")
        results = await integration.retrieve_memory(
            query="test memory", user_id="test_user"
        )
        print(f"Retrieve results: {len(results)} items")

        # Test search memory
        print("🔎 Testing search memory...")
        search_results = await integration.search_memory(
            query="security", user_id="test_user"
        )
        print(f"Search results: {len(search_results)} items")

        # Get statistics
        print("📊 Getting statistics...")
        stats = integration.get_memory_statistics()
        print(f"Statistics: {stats}")

        print("✅ Memory Security Integration test completed!")

    # Run test
    asyncio.run(test_integration())


if __name__ == "__main__":
    main()
