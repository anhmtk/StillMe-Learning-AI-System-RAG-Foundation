#!/usr/bin/env python3
"""
🚀 SANDBOX DEPLOY SCRIPT - PHASE 1
🚀 SCRIPT TRIỂN KHAI SANDBOX - GIAI ĐOẠN 1

PURPOSE / MỤC ĐÍCH:
- Automated sandbox deployment và verification
- Triển khai sandbox tự động và xác minh
- Docker image building và container management
- Xây dựng Docker image và quản lý container
- Health checks và integration testing
- Kiểm tra sức khỏe và test tích hợp
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import docker
import requests
from ...compat_docker import get_sandbox_deployer

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stillme_core.core.advanced_security.sandbox_controller import (
    SandboxController,
    SandboxStatus,
    SandboxType,
)

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_IMAGE = "python:3.9-slim"
CUSTOM_IMAGE_TAG = "stillme-security-test"
HEALTH_CHECK_TIMEOUT = 30
DEPLOYMENT_TIMEOUT = 300  # 5 minutes


class SandboxDeployer:
    """
    🚀 Automated Sandbox Deployment Manager
    🚀 Quản lý triển khai Sandbox tự động
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize Sandbox Deployer
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root or os.getcwd())
        
        # Use compatibility layer to get appropriate deployer
        self._deployer = get_sandbox_deployer(str(self.project_root))
        
        # Maintain backward compatibility by exposing the same interface
        if hasattr(self._deployer, 'docker_client'):
            self.docker_client = self._deployer.docker_client
            self.sandbox_controller = SandboxController(self.docker_client)
        else:
            # For fake deployer, create a mock sandbox controller
            self.docker_client = None
            # Create a mock sandbox controller that doesn't require Docker
            from unittest.mock import Mock
            self.sandbox_controller = Mock()
            self.sandbox_controller.create_sandbox = Mock()
            self.sandbox_controller.get_status = Mock(return_value={"status": "fake"})
            
        self.deployment_logs: List[Dict] = []

        logger.info(f"🚀 SandboxDeployer initialized for project: {self.project_root}")

    async def deploy_security_sandbox(
        self,
        name: str = "security-test",
        image: str = DEFAULT_IMAGE,
        custom_dockerfile: Optional[str] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Deploy a security testing sandbox
        
        Args:
            name: Sandbox name
            image: Base Docker image
            custom_dockerfile: Path to custom Dockerfile
            
        Returns:
            Tuple of (success, sandbox_id, deployment_info)
        """
        # Delegate to the appropriate deployer
        return await self._deployer.deploy_security_sandbox(name, image, custom_dockerfile)

    async def cleanup_deployment(self, sandbox_id: str) -> bool:
        """
        Clean up deployment
        
        Args:
            sandbox_id: ID of the sandbox to clean up
            
        Returns:
            True if cleanup successful, False otherwise
        """
        # Delegate to the appropriate deployer
        success, message = await self._deployer.cleanup(sandbox_id)
        return success

    def get_logs(self) -> List[Dict]:
        """
        Get deployment logs
        
        Returns:
            List of deployment log entries
        """
        return self._deployer.get_logs()

    def _log_deployment(self, level: str, message: str):
        """
        Log deployment event (for backward compatibility)
        
        Args:
            level: Log level (INFO, SUCCESS, ERROR, etc.)
            message: Log message
        """
        log_entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message
        }
        self.deployment_logs.append(log_entry)
        logger.info(f"[{level}] {message}")

    def get_deployment_report(self) -> Dict:
        """
        Get deployment report (for backward compatibility)
        
        Returns:
            Dictionary containing deployment report
        """
        return {
            "total_deployments": len(self.deployment_logs),
            "successful_deployments": len([log for log in self.deployment_logs if log.get("level") == "SUCCESS"]),
            "failed_deployments": len([log for log in self.deployment_logs if log.get("level") == "ERROR"]),
            "deployment_logs": self.deployment_logs,
            "logs": self.deployment_logs,  # Also include for backward compatibility
            "sandbox_status": "fake" if hasattr(self._deployer, '__class__') and "Fake" in self._deployer.__class__.__name__ else "active",
            "deployer_type": "fake" if hasattr(self._deployer, '__class__') and "Fake" in self._deployer.__class__.__name__ else "real"
        }


async def main():
    """Main deployment function"""
    logging.basicConfig(level=logging.INFO)

    deployer = SandboxDeployer()

    try:
        # Deploy security sandbox
        success, sandbox_id, info = await deployer.deploy_security_sandbox(
            name="security-test-deployment",
            image=DEFAULT_IMAGE
        )

        if success:
            print(f"✅ Deployment successful! Sandbox ID: {sandbox_id}")
            print(f"📊 Deployment info: {json.dumps(info, indent=2, default=str)}")
        else:
            print(f"❌ Deployment failed! Error: {info.get('error', 'Unknown error')}")

        # Get deployment report
        report = deployer.get_deployment_report()
        print(f"📈 Deployment report: {json.dumps(report, indent=2, default=str)}")

        # Cleanup after 30 seconds (for testing)
        await asyncio.sleep(30)
        await deployer.cleanup_deployment(sandbox_id)

    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
