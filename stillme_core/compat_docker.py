#!/usr/bin/env python3
"""
🐳 DOCKER COMPATIBILITY LAYER
🐳 LỚP TƯƠNG THÍCH DOCKER

PURPOSE / MỤC ĐÍCH:
- Compatibility wrapper for Docker operations with fallback
- Lớp wrapper tương thích cho các thao tác Docker với fallback
- Provides fake implementation when Docker daemon is unavailable
- Cung cấp implementation giả khi Docker daemon không khả dụng

FUNCTIONALITY / CHỨC NĂNG:
- Detects Docker availability via try/except and environment variables
- Phát hiện khả năng sử dụng Docker qua try/except và biến môi trường
- Falls back to FakeSandboxDeployer when Docker is unavailable
- Chuyển sang FakeSandboxDeployer khi Docker không khả dụng
- Maintains same interface for both real and fake implementations
- Duy trì cùng interface cho cả implementation thật và giả
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from .common.logging import get_logger

logger = get_logger(__name__)


class FakeSandboxDeployer:
    """
    Fake sandbox deployer for when Docker is unavailable
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize fake deployer"""
        self.project_root = Path(project_root or os.getcwd())
        self.deployment_logs: List[Dict] = []
        logger.info(f"🚀 FakeSandboxDeployer initialized (Docker unavailable) for project: {self.project_root}")
    
    async def deploy_security_sandbox(
        self,
        name: str = "security-test",
        image: str = "fake-security-image",
        custom_dockerfile: Optional[str] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Fake deployment that always succeeds
        """
        result = {
            "engine": "fake",
            "status": "unavailable",
            "reason": "no_docker_daemon",
            "actions": [],
            "container_id": f"fake-{name}-12345",
            "image": image,
            "deployed_at": "2025-01-01T00:00:00Z"
        }
        
        self.deployment_logs.append({
            "action": "fake_deploy",
            "name": name,
            "image": image,
            "result": result
        })
        
        logger.info(f"🎭 Fake deployment completed for {name}")
        return True, f"Fake deployment successful for {name}", result
    
    async def cleanup(self, container_id: str) -> Tuple[bool, str]:
        """
        Fake cleanup that always succeeds
        """
        self.deployment_logs.append({
            "action": "fake_cleanup",
            "container_id": container_id
        })
        
        logger.info(f"🎭 Fake cleanup completed for {container_id}")
        return True, f"Fake cleanup successful for {container_id}"
    
    def get_logs(self) -> List[Dict]:
        """
        Get deployment logs
        """
        return self.deployment_logs.copy()


class RealDockerDeployer:
    """
    Real Docker-based sandbox deployer
    """
    
    def __init__(self, docker_client, project_root: Optional[str] = None):
        """Initialize real deployer with Docker client"""
        self.docker_client = docker_client
        self.project_root = Path(project_root or os.getcwd())
        self.deployment_logs: List[Dict] = []
        logger.info(f"🐳 RealDockerDeployer initialized for project: {self.project_root}")
    
    async def deploy_security_sandbox(
        self,
        name: str = "security-test",
        image: str = "alpine:latest",
        custom_dockerfile: Optional[str] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Real Docker deployment
        """
        try:
            # Pull image
            self.docker_client.images.pull(image)
            
            # Run container
            container = self.docker_client.containers.run(
                image,
                name=name,
                detach=True,
                remove=False,
                environment={"SANDBOX_MODE": "security_test"}
            )
            
            result = {
                "engine": "docker",
                "status": "running",
                "reason": "deployed_successfully",
                "actions": ["pull_image", "create_container", "start_container"],
                "container_id": container.id,
                "image": image,
                "deployed_at": "2025-01-01T00:00:00Z"
            }
            
            self.deployment_logs.append({
                "action": "real_deploy",
                "name": name,
                "image": image,
                "container_id": container.id,
                "result": result
            })
            
            logger.info(f"🐳 Real deployment completed for {name} (ID: {container.id})")
            return True, f"Real deployment successful for {name}", result
            
        except Exception as e:
            error_msg = f"Docker deployment failed: {e}"
            logger.error(error_msg)
            return False, error_msg, {"engine": "docker", "status": "failed", "error": str(e)}
    
    async def cleanup(self, container_id: str) -> Tuple[bool, str]:
        """
        Real Docker cleanup
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop()
            container.remove()
            
            self.deployment_logs.append({
                "action": "real_cleanup",
                "container_id": container_id
            })
            
            logger.info(f"🐳 Real cleanup completed for {container_id}")
            return True, f"Real cleanup successful for {container_id}"
            
        except Exception as e:
            error_msg = f"Docker cleanup failed: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_logs(self) -> List[Dict]:
        """
        Get deployment logs
        """
        return self.deployment_logs.copy()


def get_sandbox_deployer(project_root: Optional[str] = None):
    """
    Get appropriate sandbox deployer based on Docker availability
    
    Returns:
        RealDockerDeployer if Docker is available, FakeSandboxDeployer otherwise
    """
    # Check if Docker is explicitly disabled
    if os.getenv("DISABLE_DOCKER", "").lower() in ("1", "true", "yes"):
        logger.info("🐳 Docker disabled via DISABLE_DOCKER environment variable")
        return FakeSandboxDeployer(project_root)
    
    # Try to initialize Docker client
    try:
        import docker
        client = docker.from_env()
        # Test connection
        client.ping()
        logger.info("🐳 Docker daemon available, using RealDockerDeployer")
        return RealDockerDeployer(client, project_root)
    except Exception as e:
        logger.warning(f"🐳 Docker daemon unavailable ({e}), using FakeSandboxDeployer")
        return FakeSandboxDeployer(project_root)


__all__ = ['get_sandbox_deployer', 'FakeSandboxDeployer', 'RealDockerDeployer']
