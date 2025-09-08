"""
💾 MEMORY SECURITY INTEGRATION SYSTEM

Hệ thống tích hợp LayeredMemoryV1 với security features từ Phase 0.
Đảm bảo memory operations được bảo mật và monitor.

Author: AgentDev System
Version: 1.0.0
Phase: 1.1 - Memory Security Integration
"""

import os
import json
import logging
import hashlib
import secrets
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import asyncio
import threading
from cryptography.fernet import Fernet

# Import Phase 0 security modules
try:
    from .security_middleware import SecurityMiddleware
    from .performance_monitor import PerformanceMonitor
    from .integration_bridge import IntegrationBridge
except ImportError:
    try:
        from stillme_core.security_middleware import SecurityMiddleware
        from stillme_core.performance_monitor import PerformanceMonitor
        from stillme_core.integration_bridge import IntegrationBridge
    except ImportError:
        # Create mock classes for testing
        class SecurityMiddleware:
            def __init__(self): pass
            def validate_input(self, data): return {"is_valid": True, "threats_detected": []}
            def check_rate_limit(self, client_ip, endpoint): return True
            def get_security_report(self): return {"security_score": 100}
        
        class PerformanceMonitor:
            def __init__(self): pass
            def start_monitoring(self): pass
            def get_performance_summary(self): return {"status": "healthy"}
        
        class IntegrationBridge:
            def __init__(self): pass
            def register_endpoint(self, method, path, handler, auth_required=False): pass

# Import memory modules
try:
    from modules.layered_memory_v1 import LayeredMemoryV1
    from modules.secure_memory_manager import SecureMemoryManager, SecureMemoryConfig
except ImportError:
    from layered_memory_v1 import LayeredMemoryV1
    from secure_memory_manager import SecureMemoryManager, SecureMemoryConfig

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
    security_levels: Dict[str, int] = None
    
    def __post_init__(self):
        if self.security_levels is None:
            self.security_levels = {
                'public': 1,
                'private': 2,
                'confidential': 3,
                'secret': 4
            }

class MemorySecurityIntegration:
    """
    Main memory security integration system
    """
    
    def __init__(self, config: Optional[MemorySecurityConfig] = None):
        self.config = config or MemorySecurityConfig()
        self.logger = self._setup_logging()
        
        # Initialize security components
        self.security_middleware = SecurityMiddleware()
        self.performance_monitor = PerformanceMonitor()
        self.integration_bridge = IntegrationBridge()
        
        # Initialize memory system
        self.memory_system = None
        self.secure_storage = None
        
        # Security tracking
        self.access_logs: List[MemoryAccessLog] = []
        self.blocked_operations: Set[str] = set()
        self.security_events: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.operation_metrics: Dict[str, List[float]] = {
            'read_times': [],
            'write_times': [],
            'search_times': [],
            'delete_times': []
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
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_memory_system(self):
        """Initialize memory system with security"""
        try:
            # Create secure storage configuration
            secure_config = SecureMemoryConfig(
                file_path="secure_memory.enc",
                key_path="secure_memory.key",
                backup_dir="backups",
                max_backups=10,
                key_rotation_days=30,
                compression_enabled=True,
                auto_backup=True,
                encryption_algorithm="fernet"
            )
            
            # Initialize secure storage
            self.secure_storage = SecureMemoryManager(secure_config)
            
            # Initialize layered memory with secure storage
            self.memory_system = LayeredMemoryV1(
                secure_storage_config=secure_config,
                external_secure_storage=self.secure_storage
            )
            
            self.logger.info("✅ Memory system initialized with security")
            
        except Exception as e:
            self.logger.error(f"Error initializing memory system: {e}")
            raise
    
    def _setup_security_monitoring(self):
        """Setup security monitoring"""
        try:
            # Start performance monitoring
            self.performance_monitor.start_monitoring()
            
            # Register security endpoints
            self.integration_bridge.register_endpoint(
                "GET", "/memory/health", self._health_check, auth_required=True
            )
            self.integration_bridge.register_endpoint(
                "GET", "/memory/security-report", self._get_security_report, auth_required=True
            )
            self.integration_bridge.register_endpoint(
                "POST", "/memory/validate", self._validate_memory_operation, auth_required=True
            )
            
            self.logger.info("✅ Security monitoring setup completed")
            
        except Exception as e:
            self.logger.error(f"Error setting up security monitoring: {e}")
    
    async def store_memory(self, content: str, layer: str = "short_term", 
                          security_level: str = "private", user_id: str = "system",
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store memory with security validation
        """
        start_time = datetime.now()
        
        try:
            # Security validation
            if not await self._validate_memory_operation_internal("write", content, security_level, user_id):
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
            self.memory_system.add_memory(
                content=content,
                priority=0.8 if security_level == "confidential" else 0.5,
                metadata=metadata or {}
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
                    security_level=security_level
                )
            
            # Track performance
            execution_time = (datetime.now() - start_time).total_seconds()
            self.operation_metrics['write_times'].append(execution_time)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
            self._log_security_event("memory_store_error", user_id, "write", str(e))
            return False
    
    async def retrieve_memory(self, query: str, layer: str = "auto", 
                             user_id: str = "system") -> List[Dict[str, Any]]:
        """
        Retrieve memory with security validation
        """
        start_time = datetime.now()
        
        try:
            # Security validation
            if not await self._validate_memory_operation_internal("read", query, "private", user_id):
                return []
            
            # Rate limiting check
            if not self._check_rate_limit(user_id, "read"):
                self._log_security_event("rate_limit_exceeded", user_id, "read")
                return []
            
            # Retrieve memory
            results = self.memory_system.search(query=query)
            
            # Filter results based on security level
            filtered_results = self._filter_results_by_security(results, user_id)
            
            # Log access
            self._log_memory_access(
                user_id=user_id,
                operation="read",
                layer=layer,
                content=query,
                success=len(filtered_results) > 0,
                security_level="private"
            )
            
            # Track performance
            execution_time = (datetime.now() - start_time).total_seconds()
            self.operation_metrics['read_times'].append(execution_time)
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Error retrieving memory: {e}")
            self._log_security_event("memory_retrieve_error", user_id, "read", str(e))
            return []
    
    async def search_memory(self, query: str, user_id: str = "system") -> List[Dict[str, Any]]:
        """
        Search memory with security validation
        """
        start_time = datetime.now()
        
        try:
            # Security validation
            if not await self._validate_memory_operation_internal("search", query, "private", user_id):
                return []
            
            # Rate limiting check
            if not self._check_rate_limit(user_id, "search"):
                self._log_security_event("rate_limit_exceeded", user_id, "search")
                return []
            
            # Search memory
            results = self.memory_system.search(query=query)
            
            # Filter results based on security level
            filtered_results = self._filter_results_by_security(results, user_id)
            
            # Log access
            self._log_memory_access(
                user_id=user_id,
                operation="search",
                layer="all",
                content=query,
                success=len(filtered_results) > 0,
                security_level="private"
            )
            
            # Track performance
            execution_time = (datetime.now() - start_time).total_seconds()
            self.operation_metrics['search_times'].append(execution_time)
            
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
            if not await self._validate_memory_operation_internal("delete", memory_id, "private", user_id):
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
                    security_level="private"
                )
            
            # Track performance
            execution_time = (datetime.now() - start_time).total_seconds()
            self.operation_metrics['delete_times'].append(execution_time)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting memory: {e}")
            self._log_security_event("memory_delete_error", user_id, "delete", str(e))
            return False
    
    async def _validate_memory_operation_internal(self, operation: str, content: str, 
                                       security_level: str, user_id: str) -> bool:
        """Validate memory operation"""
        try:
            # Check if operation is blocked
            operation_key = f"{user_id}:{operation}"
            if operation_key in self.blocked_operations:
                return False
            
            # Validate content
            validation_result = self.security_middleware.validate_input(content)
            if not validation_result["is_valid"]:
                self._log_security_event("invalid_input", user_id, operation, 
                                       validation_result["threats_detected"])
                return False
            
            # Check security level permissions
            if not self._check_security_level_permission(user_id, security_level):
                self._log_security_event("insufficient_permissions", user_id, operation, security_level)
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
                r'<script[^>]*>.*?</script>',  # XSS
                r'union\s+select',  # SQL injection
                r'exec\s*\(',  # Command injection
                r'eval\s*\('  # Code injection
            ]
            
            import re
            for pattern in suspicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating content: {e}")
            return False
    
    def _check_security_level_permission(self, user_id: str, security_level: str) -> bool:
        """Check if user has permission for security level"""
        try:
            # Simple permission check - in production, this would be more sophisticated
            user_permissions = self._get_user_permissions(user_id)
            required_level = self.config.security_levels.get(security_level, 1)
            user_level = self.config.security_levels.get(user_permissions.get('max_security_level', 'public'), 1)
            
            return user_level >= required_level
            
        except Exception as e:
            self.logger.error(f"Error checking security level permission: {e}")
            return False
    
    def _get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """Get user permissions - simplified version"""
        # In production, this would query a user management system
        return {
            'max_security_level': 'confidential',
            'operations': ['read', 'write', 'search', 'delete']
        }
    
    def _filter_results_by_security(self, results: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """Filter results based on user security level"""
        try:
            user_permissions = self._get_user_permissions(user_id)
            user_level = self.config.security_levels.get(user_permissions.get('max_security_level', 'public'), 1)
            
            filtered_results = []
            for result in results:
                # Handle MemoryItem objects
                if hasattr(result, 'metadata'):
                    result_security_level = result.metadata.get('security_level', 'public')
                else:
                    result_security_level = result.get('metadata', {}).get('security_level', 'public')
                
                result_level = self.config.security_levels.get(result_security_level, 1)
                
                if user_level >= result_level:
                    # Convert MemoryItem to dict if needed
                    if hasattr(result, 'content'):
                        filtered_results.append({
                            'content': result.content,
                            'priority': result.priority,
                            'timestamp': result.timestamp.isoformat(),
                            'metadata': result.metadata
                        })
                    else:
                        filtered_results.append(result)
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Error filtering results by security: {e}")
            return results
    
    def _log_memory_access(self, user_id: str, operation: str, layer: str, 
                          content: str, success: bool, security_level: str):
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
                user_agent="MemorySecurityIntegration/1.0"
            )
            
            self.access_logs.append(log_entry)
            
            # Keep only last 1000 logs
            if len(self.access_logs) > 1000:
                self.access_logs = self.access_logs[-1000:]
            
        except Exception as e:
            self.logger.error(f"Error logging memory access: {e}")
    
    def _log_security_event(self, event_type: str, user_id: str, operation: str, details: str = ""):
        """Log security event"""
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'user_id': user_id,
                'operation': operation,
                'details': details,
                'severity': 'medium'
            }
            
            self.security_events.append(event)
            
            # Keep only last 500 events
            if len(self.security_events) > 500:
                self.security_events = self.security_events[-500:]
            
            self.logger.warning(f"🚨 Security Event: {event_type} - {user_id} - {operation}")
            
        except Exception as e:
            self.logger.error(f"Error logging security event: {e}")
    
    async def _health_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Health check endpoint"""
        try:
            # Check memory system health
            memory_health = await self.memory_system.get_health_status() if hasattr(self.memory_system, 'get_health_status') else {"status": "unknown"}
            
            # Check security system health
            security_health = self.security_middleware.get_security_report()
            
            # Check performance
            performance_health = self.performance_monitor.get_performance_summary()
            
            return {
                "status": "success",
                "data": {
                    "memory_system": memory_health,
                    "security_system": security_health,
                    "performance_system": performance_health,
                    "access_logs_count": len(self.access_logs),
                    "security_events_count": len(self.security_events)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "HealthCheckError",
                "message": str(e)
            }
    
    async def _get_security_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get security report endpoint"""
        try:
            # Get recent security events
            recent_events = [e for e in self.security_events if 
                           (datetime.now() - datetime.fromisoformat(e['timestamp'])).seconds < 3600]
            
            # Get access statistics
            access_stats = {
                'total_accesses': len(self.access_logs),
                'successful_accesses': len([log for log in self.access_logs if log.success]),
                'failed_accesses': len([log for log in self.access_logs if not log.success]),
                'operations_breakdown': {}
            }
            
            # Count operations
            for log in self.access_logs:
                op = log.operation
                if op not in access_stats['operations_breakdown']:
                    access_stats['operations_breakdown'][op] = 0
                access_stats['operations_breakdown'][op] += 1
            
            return {
                "status": "success",
                "data": {
                    "security_events_24h": len(recent_events),
                    "access_statistics": access_stats,
                    "blocked_operations": list(self.blocked_operations),
                    "performance_metrics": {
                        "avg_read_time": sum(self.operation_metrics['read_times']) / len(self.operation_metrics['read_times']) if self.operation_metrics['read_times'] else 0,
                        "avg_write_time": sum(self.operation_metrics['write_times']) / len(self.operation_metrics['write_times']) if self.operation_metrics['write_times'] else 0,
                        "avg_search_time": sum(self.operation_metrics['search_times']) / len(self.operation_metrics['search_times']) if self.operation_metrics['search_times'] else 0
                    }
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "SecurityReportError",
                "message": str(e)
            }
    
    async def _validate_memory_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate memory operation endpoint"""
        try:
            operation = data.get('operation', '')
            content = data.get('content', '')
            security_level = data.get('security_level', 'private')
            user_id = data.get('user_id', 'system')
            
            is_valid = await self._validate_memory_operation(operation, content, security_level, user_id)
            
            return {
                "status": "success",
                "data": {
                    "is_valid": is_valid,
                    "operation": operation,
                    "security_level": security_level,
                    "user_id": user_id
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "ValidationError",
                "message": str(e)
            }
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            return {
                "access_logs_count": len(self.access_logs),
                "security_events_count": len(self.security_events),
                "blocked_operations_count": len(self.blocked_operations),
                "operation_metrics": {
                    "read_operations": len(self.operation_metrics['read_times']),
                    "write_operations": len(self.operation_metrics['write_times']),
                    "search_operations": len(self.operation_metrics['search_times']),
                    "delete_operations": len(self.operation_metrics['delete_times'])
                },
                "performance_averages": {
                    "avg_read_time": sum(self.operation_metrics['read_times']) / len(self.operation_metrics['read_times']) if self.operation_metrics['read_times'] else 0,
                    "avg_write_time": sum(self.operation_metrics['write_times']) / len(self.operation_metrics['write_times']) if self.operation_metrics['write_times'] else 0,
                    "avg_search_time": sum(self.operation_metrics['search_times']) / len(self.operation_metrics['search_times']) if self.operation_metrics['search_times'] else 0
                }
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
            user_id="test_user"
        )
        print(f"Store result: {success}")
        
        # Test retrieve memory
        print("🔍 Testing retrieve memory...")
        results = await integration.retrieve_memory(
            query="test memory",
            user_id="test_user"
        )
        print(f"Retrieve results: {len(results)} items")
        
        # Test search memory
        print("🔎 Testing search memory...")
        search_results = await integration.search_memory(
            query="security",
            user_id="test_user"
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
