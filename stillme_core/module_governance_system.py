"""
🏛️ MODULE GOVERNANCE SYSTEM

Hệ thống quản lý toàn diện cho tất cả modules trong StillMe ecosystem.
Bao gồm lifecycle management, configuration management, monitoring & alerting, và security governance.

Author: AgentDev System
Version: 1.0.0
Phase: 1.2 - Module Governance System
"""

import os
import json
import logging
import asyncio
import threading
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import importlib
import inspect
import psutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import Phase 0 security modules
try:
    from .security_middleware import SecurityMiddleware
    from .performance_monitor import PerformanceMonitor
    from .integration_bridge import IntegrationBridge
    from .memory_security_integration import MemorySecurityIntegration
except ImportError:
    try:
        from stillme_core.security_middleware import SecurityMiddleware
        from stillme_core.performance_monitor import PerformanceMonitor
        from stillme_core.integration_bridge import IntegrationBridge
        from stillme_core.memory_security_integration import MemorySecurityIntegration
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
        
        class MemorySecurityIntegration:
            def __init__(self): pass
            def get_memory_statistics(self): return {"access_logs_count": 0}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModuleStatus(Enum):
    """Module status enumeration"""
    UNKNOWN = "unknown"
    DISCOVERED = "discovered"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"

class ModulePriority(Enum):
    """Module priority enumeration"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    OPTIONAL = 5

@dataclass
class ModuleInfo:
    """Module information structure"""
    name: str
    path: str
    version: str
    status: ModuleStatus
    priority: ModulePriority
    dependencies: List[str]
    dependents: List[str]
    health_score: float
    last_health_check: datetime
    startup_time: Optional[datetime]
    shutdown_time: Optional[datetime]
    error_count: int
    last_error: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class ModuleConfiguration:
    """Module configuration structure"""
    module_name: str
    config_version: str
    enabled: bool
    auto_start: bool
    restart_on_failure: bool
    max_restart_attempts: int
    health_check_interval: int
    timeout_seconds: int
    resource_limits: Dict[str, Any]
    environment_variables: Dict[str, str]
    custom_settings: Dict[str, Any]
    last_updated: datetime

@dataclass
class GovernanceMetrics:
    """Governance system metrics"""
    total_modules: int
    running_modules: int
    stopped_modules: int
    error_modules: int
    maintenance_modules: int
    avg_health_score: float
    total_restarts: int
    total_errors: int
    system_uptime: float
    last_governance_check: datetime

class ModuleGovernanceSystem:
    """
    Main Module Governance System
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = self._setup_logging()
        
        # Initialize governance components
        self.security_middleware = SecurityMiddleware()
        self.performance_monitor = PerformanceMonitor()
        self.integration_bridge = IntegrationBridge()
        self.memory_integration = MemorySecurityIntegration()
        
        # Module registry
        self.modules: Dict[str, ModuleInfo] = {}
        self.module_configs: Dict[str, ModuleConfiguration] = {}
        self.module_instances: Dict[str, Any] = {}
        
        # Governance state
        self.governance_metrics = GovernanceMetrics(
            total_modules=0,
            running_modules=0,
            stopped_modules=0,
            error_modules=0,
            maintenance_modules=0,
            avg_health_score=0.0,
            total_restarts=0,
            total_errors=0,
            system_uptime=0.0,
            last_governance_check=datetime.now()
        )
        
        # Monitoring and control
        self.monitoring_active = False
        self.governance_thread = None
        self.health_check_interval = 30  # seconds
        self.auto_recovery_enabled = True
        
        # Performance tracking
        self.performance_metrics: Dict[str, List[float]] = {
            'startup_times': [],
            'shutdown_times': [],
            'health_check_times': [],
            'restart_times': []
        }
        
        # Initialize system
        self._initialize_governance_system()
        self._setup_governance_monitoring()
        
        self.logger.info("✅ Module Governance System initialized")
    
    def _setup_logging(self):
        """Setup logging system"""
        logger = logging.getLogger("ModuleGovernanceSystem")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_governance_system(self):
        """Initialize governance system"""
        try:
            # Discover all modules
            self._discover_modules()
            
            # Load module configurations
            self._load_module_configurations()
            
            # Initialize governance monitoring
            self._start_governance_monitoring()
            
            self.logger.info("✅ Governance system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing governance system: {e}")
            raise
    
    def _discover_modules(self):
        """Discover all modules in the system"""
        try:
            self.logger.info("🔍 Discovering modules...")
            
            # Define module discovery paths
            discovery_paths = [
                "modules/",
                "stillme_core/",
                "api/",
                "utils/"
            ]
            
            discovered_count = 0
            
            for path in discovery_paths:
                if os.path.exists(path):
                    modules = self._scan_directory_for_modules(path)
                    for module_name, module_path in modules.items():
                        if module_name not in self.modules:
                            self.modules[module_name] = ModuleInfo(
                                name=module_name,
                                path=module_path,
                                version="1.0.0",
                                status=ModuleStatus.DISCOVERED,
                                priority=ModulePriority.MEDIUM,
                                dependencies=[],
                                dependents=[],
                                health_score=0.0,
                                last_health_check=datetime.now(),
                                startup_time=None,
                                shutdown_time=None,
                                error_count=0,
                                last_error=None,
                                metadata={}
                            )
                            discovered_count += 1
            
            self.governance_metrics.total_modules = len(self.modules)
            self.logger.info(f"✅ Discovered {discovered_count} modules")
            
        except Exception as e:
            self.logger.error(f"Error discovering modules: {e}")
    
    def _scan_directory_for_modules(self, directory: str) -> Dict[str, str]:
        """Scan directory for Python modules"""
        modules = {}
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        module_name = file[:-3]  # Remove .py extension
                        module_path = os.path.join(root, file)
                        modules[module_name] = module_path
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
        
        return modules
    
    def _load_module_configurations(self):
        """Load module configurations"""
        try:
            config_file = Path("config/module_governance_config.json")
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                for module_name, config in config_data.items():
                    self.module_configs[module_name] = ModuleConfiguration(
                        module_name=module_name,
                        config_version=config.get('version', '1.0.0'),
                        enabled=config.get('enabled', True),
                        auto_start=config.get('auto_start', True),
                        restart_on_failure=config.get('restart_on_failure', True),
                        max_restart_attempts=config.get('max_restart_attempts', 3),
                        health_check_interval=config.get('health_check_interval', 30),
                        timeout_seconds=config.get('timeout_seconds', 60),
                        resource_limits=config.get('resource_limits', {}),
                        environment_variables=config.get('environment_variables', {}),
                        custom_settings=config.get('custom_settings', {}),
                        last_updated=datetime.now()
                    )
            else:
                # Create default configurations
                self._create_default_configurations()
            
            self.logger.info(f"✅ Loaded configurations for {len(self.module_configs)} modules")
            
        except Exception as e:
            self.logger.error(f"Error loading module configurations: {e}")
    
    def _create_default_configurations(self):
        """Create default configurations for all modules"""
        try:
            for module_name in self.modules.keys():
                self.module_configs[module_name] = ModuleConfiguration(
                    module_name=module_name,
                    config_version="1.0.0",
                    enabled=True,
                    auto_start=True,
                    restart_on_failure=True,
                    max_restart_attempts=3,
                    health_check_interval=30,
                    timeout_seconds=60,
                    resource_limits={
                        'max_memory_mb': 512,
                        'max_cpu_percent': 80
                    },
                    environment_variables={},
                    custom_settings={},
                    last_updated=datetime.now()
                )
            
            # Save default configurations
            self._save_module_configurations()
            
        except Exception as e:
            self.logger.error(f"Error creating default configurations: {e}")
    
    def _save_module_configurations(self):
        """Save module configurations to file"""
        try:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            config_data = {}
            for module_name, config in self.module_configs.items():
                config_data[module_name] = {
                    'version': config.config_version,
                    'enabled': config.enabled,
                    'auto_start': config.auto_start,
                    'restart_on_failure': config.restart_on_failure,
                    'max_restart_attempts': config.max_restart_attempts,
                    'health_check_interval': config.health_check_interval,
                    'timeout_seconds': config.timeout_seconds,
                    'resource_limits': config.resource_limits,
                    'environment_variables': config.environment_variables,
                    'custom_settings': config.custom_settings
                }
            
            config_file = config_dir / "module_governance_config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info("✅ Module configurations saved")
            
        except Exception as e:
            self.logger.error(f"Error saving module configurations: {e}")
    
    def _setup_governance_monitoring(self):
        """Setup governance monitoring"""
        try:
            # Register governance endpoints
            self.integration_bridge.register_endpoint(
                "GET", "/governance/status", self._get_governance_status, auth_required=True
            )
            self.integration_bridge.register_endpoint(
                "GET", "/governance/modules", self._get_modules_status, auth_required=True
            )
            self.integration_bridge.register_endpoint(
                "POST", "/governance/module/start", self._start_module, auth_required=True
            )
            self.integration_bridge.register_endpoint(
                "POST", "/governance/module/stop", self._stop_module, auth_required=True
            )
            self.integration_bridge.register_endpoint(
                "POST", "/governance/module/restart", self._restart_module, auth_required=True
            )
            self.integration_bridge.register_endpoint(
                "GET", "/governance/health", self._get_governance_health, auth_required=True
            )
            
            self.logger.info("✅ Governance monitoring setup completed")
            
        except Exception as e:
            self.logger.error(f"Error setting up governance monitoring: {e}")
    
    def _start_governance_monitoring(self):
        """Start governance monitoring thread"""
        try:
            self.monitoring_active = True
            self.governance_thread = threading.Thread(
                target=self._governance_monitoring_loop,
                daemon=True
            )
            self.governance_thread.start()
            
            self.logger.info("✅ Governance monitoring started")
            
        except Exception as e:
            self.logger.error(f"Error starting governance monitoring: {e}")
    
    def _governance_monitoring_loop(self):
        """Main governance monitoring loop"""
        while self.monitoring_active:
            try:
                start_time = time.time()
                
                # Update governance metrics
                self._update_governance_metrics()
                
                # Health check all modules
                self._health_check_all_modules()
                
                # Auto-recovery for failed modules
                if self.auto_recovery_enabled:
                    self._auto_recovery_check()
                
                # Performance monitoring
                self._monitor_performance()
                
                # Update system uptime
                self.governance_metrics.system_uptime = time.time() - start_time
                self.governance_metrics.last_governance_check = datetime.now()
                
                # Sleep until next check
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in governance monitoring loop: {e}")
                time.sleep(5)  # Short sleep on error
    
    def _update_governance_metrics(self):
        """Update governance metrics"""
        try:
            running_count = 0
            stopped_count = 0
            error_count = 0
            maintenance_count = 0
            total_health_score = 0.0
            total_restarts = 0
            total_errors = 0
            
            for module in self.modules.values():
                if module.status == ModuleStatus.RUNNING:
                    running_count += 1
                elif module.status == ModuleStatus.STOPPED:
                    stopped_count += 1
                elif module.status == ModuleStatus.ERROR:
                    error_count += 1
                elif module.status == ModuleStatus.MAINTENANCE:
                    maintenance_count += 1
                
                total_health_score += module.health_score
                total_restarts += module.error_count
                total_errors += module.error_count
            
            self.governance_metrics.running_modules = running_count
            self.governance_metrics.stopped_modules = stopped_count
            self.governance_metrics.error_modules = error_count
            self.governance_metrics.maintenance_modules = maintenance_count
            self.governance_metrics.avg_health_score = total_health_score / len(self.modules) if self.modules else 0.0
            self.governance_metrics.total_restarts = total_restarts
            self.governance_metrics.total_errors = total_errors
            
        except Exception as e:
            self.logger.error(f"Error updating governance metrics: {e}")
    
    def _health_check_all_modules(self):
        """Perform health check on all modules"""
        try:
            for module_name, module in self.modules.items():
                if module.status == ModuleStatus.RUNNING:
                    start_time = time.time()
                    
                    # Perform health check
                    health_score = self._perform_module_health_check(module_name)
                    
                    # Update module health
                    module.health_score = health_score
                    module.last_health_check = datetime.now()
                    
                    # Track performance
                    health_check_time = time.time() - start_time
                    self.performance_metrics['health_check_times'].append(health_check_time)
                    
                    # Update status based on health score
                    if health_score < 0.5:
                        module.status = ModuleStatus.ERROR
                        module.error_count += 1
                        self.logger.warning(f"⚠️ Module {module_name} health score low: {health_score}")
                    
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
    
    def _perform_module_health_check(self, module_name: str) -> float:
        """Perform health check on a specific module"""
        try:
            health_score = 1.0
            
            # Check if module instance exists
            if module_name not in self.module_instances:
                return 0.0
            
            # Check module configuration
            if module_name in self.module_configs:
                config = self.module_configs[module_name]
                if not config.enabled:
                    return 0.0
            
            # Check resource usage
            try:
                process = psutil.Process()
                memory_percent = process.memory_percent()
                cpu_percent = process.cpu_percent()
                
                # Adjust health score based on resource usage
                if memory_percent > 80:
                    health_score -= 0.3
                if cpu_percent > 80:
                    health_score -= 0.2
                
            except Exception:
                pass  # Ignore resource check errors
            
            # Check for recent errors
            module = self.modules.get(module_name)
            if module and module.error_count > 0:
                health_score -= min(0.5, module.error_count * 0.1)
            
            return max(0.0, min(1.0, health_score))
            
        except Exception as e:
            self.logger.error(f"Error performing health check for {module_name}: {e}")
            return 0.0
    
    def _auto_recovery_check(self):
        """Check for modules that need auto-recovery"""
        try:
            for module_name, module in self.modules.items():
                if module.status == ModuleStatus.ERROR:
                    config = self.module_configs.get(module_name)
                    if config and config.restart_on_failure and config.enabled:
                        if module.error_count < config.max_restart_attempts:
                            self.logger.info(f"🔄 Auto-recovering module {module_name}")
                            self._restart_module_internal(module_name)
                        else:
                            self.logger.error(f"❌ Module {module_name} exceeded max restart attempts")
                            module.status = ModuleStatus.MAINTENANCE
            
        except Exception as e:
            self.logger.error(f"Error in auto-recovery check: {e}")
    
    def _monitor_performance(self):
        """Monitor system performance"""
        try:
            # Monitor memory usage
            memory_usage = psutil.virtual_memory()
            if memory_usage.percent > 90:
                self.logger.warning(f"⚠️ High memory usage: {memory_usage.percent}%")
            
            # Monitor CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage > 90:
                self.logger.warning(f"⚠️ High CPU usage: {cpu_usage}%")
            
            # Monitor disk usage
            disk_usage = psutil.disk_usage('/')
            if disk_usage.percent > 90:
                self.logger.warning(f"⚠️ High disk usage: {disk_usage.percent}%")
            
        except Exception as e:
            self.logger.error(f"Error monitoring performance: {e}")
    
    async def start_module(self, module_name: str) -> bool:
        """Start a module"""
        try:
            if module_name not in self.modules:
                self.logger.error(f"Module {module_name} not found")
                return False
            
            module = self.modules[module_name]
            config = self.module_configs.get(module_name)
            
            if not config or not config.enabled:
                self.logger.error(f"Module {module_name} is disabled")
                return False
            
            if module.status == ModuleStatus.RUNNING:
                self.logger.info(f"Module {module_name} is already running")
                return True
            
            start_time = time.time()
            
            # Start module
            success = await self._start_module_internal(module_name)
            
            if success:
                module.status = ModuleStatus.RUNNING
                module.startup_time = datetime.now()
                module.error_count = 0
                module.last_error = None
                
                # Track performance
                startup_time = time.time() - start_time
                self.performance_metrics['startup_times'].append(startup_time)
                
                self.logger.info(f"✅ Module {module_name} started successfully")
            else:
                module.status = ModuleStatus.ERROR
                module.error_count += 1
                module.last_error = "Failed to start"
                
                self.logger.error(f"❌ Failed to start module {module_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error starting module {module_name}: {e}")
            return False
    
    async def _start_module_internal(self, module_name: str) -> bool:
        """Internal method to start a module"""
        try:
            # This is a simplified implementation
            # In a real system, this would load and initialize the actual module
            
            # Simulate module startup
            await asyncio.sleep(0.1)
            
            # Mark module as started
            self.module_instances[module_name] = {
                'instance': f"MockInstance_{module_name}",
                'startup_time': datetime.now(),
                'status': 'running'
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in internal module start for {module_name}: {e}")
            return False
    
    async def stop_module(self, module_name: str) -> bool:
        """Stop a module"""
        try:
            if module_name not in self.modules:
                self.logger.error(f"Module {module_name} not found")
                return False
            
            module = self.modules[module_name]
            
            if module.status == ModuleStatus.STOPPED:
                self.logger.info(f"Module {module_name} is already stopped")
                return True
            
            start_time = time.time()
            
            # Stop module
            success = await self._stop_module_internal(module_name)
            
            if success:
                module.status = ModuleStatus.STOPPED
                module.shutdown_time = datetime.now()
                
                # Track performance
                shutdown_time = time.time() - start_time
                self.performance_metrics['shutdown_times'].append(shutdown_time)
                
                self.logger.info(f"✅ Module {module_name} stopped successfully")
            else:
                module.status = ModuleStatus.ERROR
                module.error_count += 1
                module.last_error = "Failed to stop"
                
                self.logger.error(f"❌ Failed to stop module {module_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error stopping module {module_name}: {e}")
            return False
    
    async def _stop_module_internal(self, module_name: str) -> bool:
        """Internal method to stop a module"""
        try:
            # Remove module instance
            if module_name in self.module_instances:
                del self.module_instances[module_name]
            
            # Simulate module shutdown
            await asyncio.sleep(0.1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in internal module stop for {module_name}: {e}")
            return False
    
    async def restart_module(self, module_name: str) -> bool:
        """Restart a module"""
        try:
            self.logger.info(f"🔄 Restarting module {module_name}")
            
            start_time = time.time()
            
            # Stop module first
            stop_success = await self.stop_module(module_name)
            if not stop_success:
                return False
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Start module
            start_success = await self.start_module(module_name)
            
            # Track performance
            restart_time = time.time() - start_time
            self.performance_metrics['restart_times'].append(restart_time)
            
            return start_success
            
        except Exception as e:
            self.logger.error(f"Error restarting module {module_name}: {e}")
            return False
    
    def _restart_module_internal(self, module_name: str):
        """Internal method to restart a module (synchronous)"""
        try:
            # This is called from the monitoring thread
            asyncio.create_task(self.restart_module(module_name))
        except Exception as e:
            self.logger.error(f"Error in internal module restart for {module_name}: {e}")
    
    def get_governance_status(self) -> Dict[str, Any]:
        """Get governance system status"""
        try:
            return {
                "status": "success",
                "data": {
                    "governance_metrics": asdict(self.governance_metrics),
                    "monitoring_active": self.monitoring_active,
                    "auto_recovery_enabled": self.auto_recovery_enabled,
                    "health_check_interval": self.health_check_interval,
                    "performance_metrics": {
                        "avg_startup_time": sum(self.performance_metrics['startup_times']) / len(self.performance_metrics['startup_times']) if self.performance_metrics['startup_times'] else 0,
                        "avg_shutdown_time": sum(self.performance_metrics['shutdown_times']) / len(self.performance_metrics['shutdown_times']) if self.performance_metrics['shutdown_times'] else 0,
                        "avg_health_check_time": sum(self.performance_metrics['health_check_times']) / len(self.performance_metrics['health_check_times']) if self.performance_metrics['health_check_times'] else 0,
                        "avg_restart_time": sum(self.performance_metrics['restart_times']) / len(self.performance_metrics['restart_times']) if self.performance_metrics['restart_times'] else 0
                    }
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "GovernanceStatusError",
                "message": str(e)
            }
    
    def get_modules_status(self) -> Dict[str, Any]:
        """Get status of all modules"""
        try:
            modules_data = {}
            for module_name, module in self.modules.items():
                modules_data[module_name] = {
                    "name": module.name,
                    "path": module.path,
                    "version": module.version,
                    "status": module.status.value,
                    "priority": module.priority.value,
                    "health_score": module.health_score,
                    "last_health_check": module.last_health_check.isoformat(),
                    "startup_time": module.startup_time.isoformat() if module.startup_time else None,
                    "shutdown_time": module.shutdown_time.isoformat() if module.shutdown_time else None,
                    "error_count": module.error_count,
                    "last_error": module.last_error,
                    "dependencies": module.dependencies,
                    "dependents": module.dependents
                }
            
            return {
                "status": "success",
                "data": {
                    "modules": modules_data,
                    "total_modules": len(self.modules),
                    "governance_metrics": asdict(self.governance_metrics)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "ModulesStatusError",
                "message": str(e)
            }
    
    async def _get_governance_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get governance status endpoint"""
        return self.get_governance_status()
    
    async def _get_modules_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get modules status endpoint"""
        return self.get_modules_status()
    
    async def _start_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Start module endpoint"""
        try:
            module_name = data.get('module_name', '')
            if not module_name:
                return {
                    "status": "error",
                    "error_type": "ValidationError",
                    "message": "module_name is required"
                }
            
            success = await self.start_module(module_name)
            
            return {
                "status": "success" if success else "error",
                "data": {
                    "module_name": module_name,
                    "started": success
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "StartModuleError",
                "message": str(e)
            }
    
    async def _stop_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stop module endpoint"""
        try:
            module_name = data.get('module_name', '')
            if not module_name:
                return {
                    "status": "error",
                    "error_type": "ValidationError",
                    "message": "module_name is required"
                }
            
            success = await self.stop_module(module_name)
            
            return {
                "status": "success" if success else "error",
                "data": {
                    "module_name": module_name,
                    "stopped": success
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "StopModuleError",
                "message": str(e)
            }
    
    async def _restart_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Restart module endpoint"""
        try:
            module_name = data.get('module_name', '')
            if not module_name:
                return {
                    "status": "error",
                    "error_type": "ValidationError",
                    "message": "module_name is required"
                }
            
            success = await self.restart_module(module_name)
            
            return {
                "status": "success" if success else "error",
                "data": {
                    "module_name": module_name,
                    "restarted": success
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "RestartModuleError",
                "message": str(e)
            }
    
    async def _get_governance_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get governance health endpoint"""
        try:
            # Get system health
            system_health = {
                "governance_system": "healthy",
                "monitoring_active": self.monitoring_active,
                "auto_recovery_enabled": self.auto_recovery_enabled,
                "avg_health_score": self.governance_metrics.avg_health_score,
                "total_modules": self.governance_metrics.total_modules,
                "running_modules": self.governance_metrics.running_modules,
                "error_modules": self.governance_metrics.error_modules
            }
            
            # Get memory integration health
            memory_stats = self.memory_integration.get_memory_statistics()
            
            # Get security system health
            security_report = self.security_middleware.get_security_report()
            
            # Get performance system health
            performance_summary = self.performance_monitor.get_performance_summary()
            
            return {
                "status": "success",
                "data": {
                    "system_health": system_health,
                    "memory_system": memory_stats,
                    "security_system": security_report,
                    "performance_system": performance_summary,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": "GovernanceHealthError",
                "message": str(e)
            }
    
    def shutdown(self):
        """Shutdown governance system"""
        try:
            self.logger.info("🔄 Shutting down governance system...")
            
            # Stop monitoring
            self.monitoring_active = False
            
            # Stop all modules
            for module_name in list(self.modules.keys()):
                if self.modules[module_name].status == ModuleStatus.RUNNING:
                    asyncio.create_task(self.stop_module(module_name))
            
            # Wait for governance thread to finish
            if self.governance_thread and self.governance_thread.is_alive():
                self.governance_thread.join(timeout=5)
            
            self.logger.info("✅ Governance system shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error shutting down governance system: {e}")

def main():
    """Test module governance system"""
    async def test_governance():
        print("🧪 Testing Module Governance System...")
        
        # Initialize governance system
        governance = ModuleGovernanceSystem()
        
        # Test governance status
        print("📊 Testing governance status...")
        status = governance.get_governance_status()
        print(f"Governance status: {status['status']}")
        
        # Test modules status
        print("📋 Testing modules status...")
        modules_status = governance.get_modules_status()
        print(f"Modules status: {modules_status['status']}")
        print(f"Total modules: {modules_status['data']['total_modules']}")
        
        # Test starting a module
        if modules_status['data']['modules']:
            module_name = list(modules_status['data']['modules'].keys())[0]
            print(f"🚀 Testing start module: {module_name}")
            success = await governance.start_module(module_name)
            print(f"Start result: {success}")
            
            # Test stopping the module
            print(f"🛑 Testing stop module: {module_name}")
            success = await governance.stop_module(module_name)
            print(f"Stop result: {success}")
        
        # Test restart
        if modules_status['data']['modules']:
            module_name = list(modules_status['data']['modules'].keys())[0]
            print(f"🔄 Testing restart module: {module_name}")
            success = await governance.restart_module(module_name)
            print(f"Restart result: {success}")
        
        # Get final status
        print("📊 Final governance status...")
        final_status = governance.get_governance_status()
        print(f"Final status: {final_status}")
        
        # Shutdown
        governance.shutdown()
        
        print("✅ Module Governance System test completed!")
    
    # Run test
    asyncio.run(test_governance())

if __name__ == "__main__":
    main()
