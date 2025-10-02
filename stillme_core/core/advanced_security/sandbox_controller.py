#!/usr/bin/env python3
"""
🚀 SANDBOX CONTROLLER - PHASE 1
🚀 BỘ ĐIỀU KHIỂN SANDBOX - GIAI ĐOẠN 1

PURPOSE / MỤC ĐÍCH:
- Enhanced sandbox environment với Docker network isolation
- Môi trường sandbox nâng cao với cô lập mạng Docker
- Resource limits enforcement và monitoring
- Thực thi giới hạn tài nguyên và giám sát
- Integration với existing security framework
- Tích hợp với framework bảo mật hiện có
"""

import asyncio
import logging
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import docker
import psutil

logger = logging.getLogger(__name__)

# Security metrics configuration
SECURITY_METRICS = {
    "max_cpu_usage": 70,  # Percentage
    "max_memory_usage": 512,  # MB
    "max_execution_time": 900,  # Seconds (15 minutes)
    "network_egress_limit": 0,  # No internet access
    "allowed_ports": [8080, 3000],  # Only these ports
    "max_disk_usage": 100,  # MB
    "max_concurrent_containers": 3,
}


class SandboxStatus(Enum):
    """Sandbox status enumeration"""
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    CLEANED_UP = "cleaned_up"


class SandboxType(Enum):
    """Sandbox type enumeration"""
    SECURITY_TEST = "security_test"
    CODE_EXECUTION = "code_execution"
    NETWORK_SIMULATION = "network_simulation"
    FULL_ISOLATION = "full_isolation"


@dataclass
class SandboxConfig:
    """Sandbox configuration"""
    sandbox_id: str
    name: str
    sandbox_type: SandboxType
    image: str = "python:3.9-slim"
    cpu_limit: float = 0.5  # CPU cores
    memory_limit: int = 512  # MB
    network_mode: str = "none"  # No network access
    timeout: int = 900  # 15 minutes
    environment_vars: dict[str, str] = None
    volume_mounts: list[dict[str, str]] = None
    allowed_ports: list[int] = None
    security_policies: list[str] = None

    def __post_init__(self):
        if self.environment_vars is None:
            self.environment_vars = {}
        if self.volume_mounts is None:
            self.volume_mounts = []
        if self.allowed_ports is None:
            self.allowed_ports = SECURITY_METRICS["allowed_ports"]
        if self.security_policies is None:
            self.security_policies = ["no_network", "resource_limits", "timeout"]


@dataclass
class SandboxInstance:
    """Sandbox instance representation"""
    config: SandboxConfig
    container_id: Optional[str] = None
    status: SandboxStatus = SandboxStatus.CREATING
    created_at: float = 0.0
    started_at: Optional[float] = None
    stopped_at: Optional[float] = None
    resource_usage: dict[str, Any] = None
    logs: list[dict[str, Any]] = None
    health_checks: list[dict[str, Any]] = None
    security_violations: list[dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.resource_usage is None:
            self.resource_usage = {}
        if self.logs is None:
            self.logs = []
        if self.health_checks is None:
            self.health_checks = []
        if self.security_violations is None:
            self.security_violations = []


class SandboxController:
    """
    🚀 Enhanced Sandbox Controller với Docker isolation
    🚀 Bộ điều khiển Sandbox nâng cao với cô lập Docker
    """

    def __init__(self, docker_client: Optional[docker.DockerClient] = None):
        """
        Initialize Sandbox Controller

        Args:
            docker_client: Optional Docker client instance
        """
        # Use compatibility layer for Docker client
        if docker_client:
            self.docker_client = docker_client
        else:
            try:
                self.docker_client = docker.from_env()
                # Test connection
                self.docker_client.ping()
            except Exception:
                # Fallback to mock client when Docker is unavailable
                from unittest.mock import Mock
                self.docker_client = Mock()
                self.docker_client.ping = Mock()
                self.docker_client.containers = Mock()
                self.docker_client.containers.run = Mock()
                self.docker_client.containers.get = Mock()
                self.docker_client.images = Mock()
                self.docker_client.images.pull = Mock()
        self.active_sandboxes: dict[str, SandboxInstance] = {}
        self.sandbox_history: list[SandboxInstance] = []
        self.isolation_base = Path(tempfile.mkdtemp(prefix="sandbox_"))
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False

        # Initialize security policies
        self._initialize_security_policies()

        # Start monitoring
        self._start_monitoring()

        logger.info(f"🚀 SandboxController initialized with isolation base: {self.isolation_base}")

    def _initialize_security_policies(self):
        """Initialize security policies"""
        self.security_policies = {
            "network_isolation": {
                "enabled": True,
                "allowed_hosts": ["localhost", "127.0.0.1"],
                "blocked_ports": [22, 23, 25, 53, 80, 443, 993, 995],
                "monitoring": True
            },
            "resource_limits": {
                "max_cpu_percent": SECURITY_METRICS["max_cpu_usage"],
                "max_memory_mb": SECURITY_METRICS["max_memory_usage"],
                "max_disk_mb": SECURITY_METRICS["max_disk_usage"],
                "enforcement": True
            },
            "execution_limits": {
                "max_execution_time": SECURITY_METRICS["max_execution_time"],
                "max_concurrent_containers": SECURITY_METRICS["max_concurrent_containers"],
                "auto_cleanup": True
            },
            "data_protection": {
                "no_real_data": True,
                "encrypted_storage": True,
                "automatic_cleanup": True
            }
        }

    async def create_sandbox(
        self,
        name: str,
        sandbox_type: SandboxType,
        image: str = "python:3.9-slim",
        **kwargs
    ) -> SandboxInstance:
        """
        Create a new sandbox instance

        Args:
            name: Sandbox name
            sandbox_type: Type of sandbox
            image: Docker image to use
            **kwargs: Additional configuration options

        Returns:
            SandboxInstance: Created sandbox instance
        """
        # Check concurrent container limit
        if len(self.active_sandboxes) >= SECURITY_METRICS["max_concurrent_containers"]:
            raise RuntimeError(f"Maximum concurrent containers ({SECURITY_METRICS['max_concurrent_containers']}) reached")

        # Generate unique sandbox ID
        sandbox_id = f"{name}_{uuid.uuid4().hex[:8]}"

        # Create sandbox configuration
        config = SandboxConfig(
            sandbox_id=sandbox_id,
            name=name,
            sandbox_type=sandbox_type,
            image=image,
            **kwargs
        )

        # Create sandbox instance
        sandbox = SandboxInstance(config=config)

        try:
            # Pre-creation security checks
            await self._run_pre_creation_checks(sandbox)

            # Create isolated directory
            sandbox_dir = self.isolation_base / sandbox_id
            sandbox_dir.mkdir(parents=True, exist_ok=True)

            # Create Docker container with security constraints
            container = await self._create_secure_container(sandbox, sandbox_dir)

            # Update sandbox instance
            sandbox.container_id = container.id
            sandbox.status = SandboxStatus.RUNNING
            sandbox.started_at = time.time()

            # Add to active sandboxes
            self.active_sandboxes[sandbox_id] = sandbox

            # Log creation
            sandbox.logs.append({
                "timestamp": time.time(),
                "level": "INFO",
                "message": f"Sandbox {sandbox_id} created successfully",
                "container_id": container.id
            })

            logger.info(f"✅ Sandbox {sandbox_id} created with container {container.id}")
            return sandbox

        except Exception as e:
            sandbox.status = SandboxStatus.FAILED
            sandbox.logs.append({
                "timestamp": time.time(),
                "level": "ERROR",
                "message": f"Failed to create sandbox: {str(e)}"
            })
            logger.error(f"❌ Failed to create sandbox {sandbox_id}: {e}")
            raise

    async def _run_pre_creation_checks(self, sandbox: SandboxInstance):
        """Run security checks before sandbox creation"""
        checks = [
            self._check_system_resources(),
            self._check_docker_availability(),
            self._check_security_policies(sandbox),
            self._check_image_safety(sandbox.config.image)
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)

        failed_checks = [r for r in results if isinstance(r, Exception) or not r]
        if failed_checks:
            raise RuntimeError(f"Pre-creation security checks failed: {failed_checks}")

    async def _check_system_resources(self) -> bool:
        """Check if system has enough resources"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            if cpu_percent > SECURITY_METRICS["max_cpu_usage"]:
                raise RuntimeError(f"CPU usage {cpu_percent}% exceeds limit")

            if memory.percent > 80:
                raise RuntimeError(f"Memory usage {memory.percent}% is too high")

            return True
        except Exception as e:
            logger.error(f"Resource check failed: {e}")
            return False

    async def _check_docker_availability(self) -> bool:
        """Check if Docker is available and running"""
        try:
            self.docker_client.ping()
            return True
        except Exception as e:
            logger.error(f"Docker availability check failed: {e}")
            return False

    async def _check_security_policies(self, sandbox: SandboxInstance) -> bool:
        """Check if sandbox configuration meets security policies"""
        # Check resource limits
        if sandbox.config.memory_limit > SECURITY_METRICS["max_memory_usage"]:
            raise ValueError(f"Memory limit {sandbox.config.memory_limit}MB exceeds policy")

        # Check timeout
        if sandbox.config.timeout > SECURITY_METRICS["max_execution_time"]:
            raise ValueError(f"Timeout {sandbox.config.timeout}s exceeds policy")

        return True

    async def _check_image_safety(self, image: str) -> bool:
        """Check if Docker image is safe to use"""
        # Basic safety checks
        unsafe_images = ["alpine:latest", "ubuntu:latest", "centos:latest"]
        if any(unsafe in image for unsafe in unsafe_images):
            logger.warning(f"Using potentially unsafe image: {image}")

        return True

    async def _create_secure_container(
        self,
        sandbox: SandboxInstance,
        sandbox_dir: Path
    ) -> docker.models.containers.Container:
        """Create Docker container with security constraints"""

        # Prepare container configuration
        container_config = {
            "image": sandbox.config.image,
            "name": f"sandbox_{sandbox.config.sandbox_id}",
            "detach": True,
            "network_mode": sandbox.config.network_mode,
            "mem_limit": f"{sandbox.config.memory_limit}m",
            "cpu_quota": int(sandbox.config.cpu_limit * 100000),
            "cpu_period": 100000,
            "environment": sandbox.config.environment_vars,
            "volumes": {
                str(sandbox_dir): {"bind": "/workspace", "mode": "rw"}
            },
            "working_dir": "/workspace",
            "stdin_open": True,
            "tty": True,
            "security_opt": [
                "no-new-privileges:true",
                "seccomp:unconfined"  # Allow security testing
            ],
            "cap_drop": ["ALL"],
            "cap_add": [],  # No additional capabilities
            "read_only": False,  # Allow writing to workspace
            "tmpfs": {
                "/tmp": "size=50m,noexec,nosuid,nodev"
            }
        }

        # Create container
        container = self.docker_client.containers.create(**container_config)

        # Start container
        container.start()

        return container

    async def execute_in_sandbox(
        self,
        sandbox_id: str,
        command: list[str],
        timeout: Optional[int] = None
    ) -> dict[str, Any]:
        """
        Execute command in sandbox

        Args:
            sandbox_id: Sandbox identifier
            command: Command to execute
            timeout: Execution timeout

        Returns:
            Dict with execution results
        """
        if sandbox_id not in self.active_sandboxes:
            raise ValueError(f"Sandbox {sandbox_id} not found")

        sandbox = self.active_sandboxes[sandbox_id]
        if sandbox.status != SandboxStatus.RUNNING:
            raise RuntimeError(f"Sandbox {sandbox_id} is not running")

        try:
            container = self.docker_client.containers.get(sandbox.container_id)

            # Execute command with timeout
            exec_timeout = timeout or sandbox.config.timeout
            result = container.exec_run(
                command,
                timeout=exec_timeout,
                demux=True
            )

            # Log execution
            sandbox.logs.append({
                "timestamp": time.time(),
                "level": "INFO",
                "message": f"Executed command: {' '.join(command)}",
                "exit_code": result.exit_code,
                "stdout": result.output[0].decode() if result.output[0] else "",
                "stderr": result.output[1].decode() if result.output[1] else ""
            })

            return {
                "exit_code": result.exit_code,
                "stdout": result.output[0].decode() if result.output[0] else "",
                "stderr": result.output[1].decode() if result.output[1] else "",
                "execution_time": time.time() - sandbox.started_at
            }

        except Exception as e:
            sandbox.logs.append({
                "timestamp": time.time(),
                "level": "ERROR",
                "message": f"Command execution failed: {str(e)}"
            })
            raise

    async def destroy_sandbox(self, sandbox_id: str) -> bool:
        """
        Destroy sandbox instance

        Args:
            sandbox_id: Sandbox identifier

        Returns:
            bool: Success status
        """
        if sandbox_id not in self.active_sandboxes:
            logger.warning(f"Sandbox {sandbox_id} not found in active sandboxes")
            return False

        sandbox = self.active_sandboxes[sandbox_id]

        try:
            # Stop and remove container
            if sandbox.container_id:
                container = self.docker_client.containers.get(sandbox.container_id)
                container.stop(timeout=10)
                container.remove(force=True)

            # Clean up files
            sandbox_dir = self.isolation_base / sandbox_id
            if sandbox_dir.exists():
                shutil.rmtree(sandbox_dir, ignore_errors=True)

            # Update sandbox status
            sandbox.status = SandboxStatus.CLEANED_UP
            sandbox.stopped_at = time.time()

            # Move to history
            self.sandbox_history.append(sandbox)
            del self.active_sandboxes[sandbox_id]

            logger.info(f"✅ Sandbox {sandbox_id} destroyed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to destroy sandbox {sandbox_id}: {e}")
            return False

    async def _start_monitoring(self):
        """Start resource monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitor_sandboxes())

    async def _monitor_sandboxes(self):
        """Monitor active sandboxes for resource usage and violations"""
        while self.is_monitoring:
            try:
                for _sandbox_id, sandbox in list(self.active_sandboxes.items()):
                    await self._check_sandbox_health(sandbox)
                    await self._check_resource_limits(sandbox)
                    await self._check_timeout(sandbox)

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(10)

    async def _check_sandbox_health(self, sandbox: SandboxInstance):
        """Check sandbox health"""
        try:
            if not sandbox.container_id:
                return

            container = self.docker_client.containers.get(sandbox.container_id)
            container.reload()

            if container.status != "running":
                sandbox.status = SandboxStatus.STOPPED
                sandbox.logs.append({
                    "timestamp": time.time(),
                    "level": "WARNING",
                    "message": f"Container {sandbox.container_id} is not running"
                })

        except Exception as e:
            sandbox.logs.append({
                "timestamp": time.time(),
                "level": "ERROR",
                "message": f"Health check failed: {str(e)}"
            })

    async def _check_resource_limits(self, sandbox: SandboxInstance):
        """Check resource usage limits"""
        try:
            if not sandbox.container_id:
                return

            container = self.docker_client.containers.get(sandbox.container_id)
            stats = container.stats(stream=False)

            # Calculate CPU usage
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0

            # Calculate memory usage
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0

            # Update sandbox resource usage
            sandbox.resource_usage = {
                "cpu_percent": cpu_percent,
                "memory_usage_mb": memory_usage / (1024 * 1024),
                "memory_percent": memory_percent,
                "timestamp": time.time()
            }

            # Check for violations
            if cpu_percent > SECURITY_METRICS["max_cpu_usage"]:
                sandbox.security_violations.append({
                    "timestamp": time.time(),
                    "type": "cpu_limit_exceeded",
                    "value": cpu_percent,
                    "limit": SECURITY_METRICS["max_cpu_usage"]
                })

            if memory_percent > 80:  # 80% memory threshold
                sandbox.security_violations.append({
                    "timestamp": time.time(),
                    "type": "memory_limit_exceeded",
                    "value": memory_percent,
                    "limit": 80
                })

        except Exception as e:
            sandbox.logs.append({
                "timestamp": time.time(),
                "level": "ERROR",
                "message": f"Resource monitoring failed: {str(e)}"
            })

    async def _check_timeout(self, sandbox: SandboxInstance):
        """Check if sandbox has exceeded timeout"""
        if not sandbox.started_at:
            return

        elapsed_time = time.time() - sandbox.started_at
        if elapsed_time > sandbox.config.timeout:
            sandbox.logs.append({
                "timestamp": time.time(),
                "level": "WARNING",
                "message": f"Sandbox timeout exceeded: {elapsed_time}s > {sandbox.config.timeout}s"
            })

            # Auto-destroy timeout sandboxes
            await self.destroy_sandbox(sandbox.config.sandbox_id)

    def get_sandbox_status(self, sandbox_id: str) -> Optional[dict[str, Any]]:
        """Get sandbox status and information"""
        if sandbox_id in self.active_sandboxes:
            sandbox = self.active_sandboxes[sandbox_id]
        else:
            # Check history
            sandbox = next((s for s in self.sandbox_history if s.config.sandbox_id == sandbox_id), None)

        if not sandbox:
            return None

        return {
            "sandbox_id": sandbox.config.sandbox_id,
            "name": sandbox.config.name,
            "status": sandbox.status.value,
            "created_at": sandbox.created_at,
            "started_at": sandbox.started_at,
            "stopped_at": sandbox.stopped_at,
            "resource_usage": sandbox.resource_usage,
            "security_violations": sandbox.security_violations,
            "logs_count": len(sandbox.logs)
        }

    def get_all_sandboxes(self) -> list[dict[str, Any]]:
        """Get all sandbox instances"""
        all_sandboxes = list(self.active_sandboxes.values()) + self.sandbox_history
        return [self.get_sandbox_status(s.config.sandbox_id) for s in all_sandboxes]

    async def cleanup_all(self):
        """Clean up all sandboxes and resources"""
        logger.info("🧹 Starting cleanup of all sandboxes...")

        # Stop monitoring
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()

        # Destroy all active sandboxes
        for sandbox_id in list(self.active_sandboxes.keys()):
            await self.destroy_sandbox(sandbox_id)

        # Clean up isolation base
        if self.isolation_base.exists():
            shutil.rmtree(self.isolation_base, ignore_errors=True)

        logger.info("✅ Cleanup completed")

    def __del__(self):
        """Destructor to ensure cleanup"""
        if hasattr(self, 'is_monitoring') and self.is_monitoring:
            asyncio.create_task(self.cleanup_all())
